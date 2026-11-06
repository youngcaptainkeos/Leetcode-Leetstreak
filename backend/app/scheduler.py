import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date

IST = timezone(timedelta(hours=5, minutes=30))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from .config import POLL_INTERVAL_MINUTES
from .database import SessionLocal
from .models import User, Solve, DailyActivity, DailyChallenge
from .leetcode_client import fetch_leetcode_user_data, fetch_today_daily_challenge_slug, fetch_monthly_daily_challenges, fetch_problem_info, LeetCodeError
from .point_calculator import recalculate_user_points
from .contest_ratings import refresh_zerotrac_dataset
from .codeforces_sync import sync_codeforces_user
from .tracking import ProviderAcceptance, capture_score_baseline, ingest_acceptances, validate_acceptances
from .timekeeping import utc_now

logger = logging.getLogger("codestreak.scheduler")


async def backfill_daily_challenges_archive(db: Session):
    """Backfills daily challenges archive from LeetCode GraphQL for 2024 to current year/month."""
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    for year in range(2024, current_year + 1):
        max_m = current_month if year == current_year else 12
        for month in range(1, max_m + 1):
            try:
                m_map = await fetch_monthly_daily_challenges(year, month)
                for d_str, slug in m_map.items():
                    d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
                    existing = db.query(DailyChallenge).filter(DailyChallenge.date == d_obj).first()
                    if not existing:
                        db.add(DailyChallenge(date=d_obj, title_slug=slug))
            except Exception as e:
                logger.warning("Backfill failed for %d-%d: %s", year, month, e)
    db.commit()


async def poll_user(db: Session, user: User, sync_codeforces: bool = True) -> int:
    """Fetch public profile and recent ACs; recent history is never first-solve proof."""
    db.refresh(user)
    handle, user_id = user.leetcode_username, user.id
    account_version, previous_sync = user.leetcode_account_version, user.leetcode_last_sync
    sync_started = utc_now()
    db.commit()  # Release the connection before provider requests.
    try:
        data = await fetch_leetcode_user_data(handle)
        provider_handle = data.get("username")
        if not isinstance(provider_handle, str) or provider_handle.casefold() != handle.casefold():
            raise LeetCodeError("Provider account identity did not match")
        if not data.get("recent_submissions_available", False):
            raise LeetCodeError("Recent accepted history is unavailable")
        submissions = data.get("recent_submissions")
        if not isinstance(submissions, list):
            raise LeetCodeError("Invalid recent accepted history")
        evidence = []
        for sub in submissions:
            if (not isinstance(sub, dict) or not isinstance(sub.get("id"), (str, int))
                    or isinstance(sub.get("id"), bool)
                    or not isinstance(sub.get("timestamp"), (str, int))
                    or isinstance(sub.get("timestamp"), bool)
                    or not str(sub["timestamp"]).isascii() or not str(sub["timestamp"]).isdigit()):
                raise LeetCodeError("Invalid accepted submission evidence")
            evidence.append(ProviderAcceptance(str(sub["id"]), sub.get("titleSlug"),
                datetime.fromtimestamp(int(sub["timestamp"]), timezone.utc).replace(tzinfo=None)))
        validate_acceptances(evidence, "leetcode")
        # All slow metadata calls happen before acquiring the account write lock.
        problem_info = {slug: await fetch_problem_info(slug) for slug in {row.title_slug for row in evidence}}
        today_daily_slug = await fetch_today_daily_challenge_slug()
    except (LeetCodeError, ValueError, OverflowError, OSError):
        logger.warning("LeetCode accepted history unavailable for user %d", user_id)
        return await sync_codeforces_user(db, user) if sync_codeforces and user.codeforces_username else 0

    db.refresh(user, with_for_update=True)
    if (user.leetcode_username != handle or user.leetcode_account_version != account_version
            or user.leetcode_last_sync != previous_sync):
        db.rollback()
        return 0
    capture_score_baseline(db, user_id)

    # 1. Update user metadata & difficulty totals
    if data.get("avatar_url"):
        user.avatar_url = data["avatar_url"]
    diffs = data.get("difficulty_counts") or {}
    user.easy_count = diffs.get("Easy", 0)
    user.medium_count = diffs.get("Medium", 0)
    user.hard_count = diffs.get("Hard", 0)
    user.official_streak = data.get("official_streak", 0)

    # 2. Sync full submission calendar into DailyActivity (active days default to 1 solve)
    cal_map = data.get("submission_calendar") or {}
    existing_daily = {
        r.date: r for r in db.query(DailyActivity).filter(DailyActivity.user_id == user.id).all()
    }

    for day, solve_count in cal_map.items():
        if solve_count > 0:
            if day in existing_daily:
                # If currently 0 or bloated submission count (>1 without solves ledger match), normalize
                if existing_daily[day].problems_solved == 0:
                    existing_daily[day].problems_solved = 1
            else:
                new_row = DailyActivity(user_id=user.id, date=day, problems_solved=1)
                db.add(new_row)
                existing_daily[day] = new_row

    # 3. Dedup recent AC submissions into Solves ledger & update daily count from actual AC solves
    new_count = 0
    
    existing_solves = {
        r[0] for r in db.query(Solve.title_slug).filter(Solve.user_id == user.id, Solve.platform == "leetcode").all()
    }
    solves_by_date = {}

    for sub in sorted(submissions, key=lambda row: (int(row["timestamp"]), int(row["id"]))):
        title_slug = sub["titleSlug"]
        solved_at = datetime.fromtimestamp(int(sub["timestamp"]), tz=timezone.utc).replace(tzinfo=None)
        day = datetime.fromtimestamp(int(sub["timestamp"]), tz=IST).date()

        if title_slug not in existing_solves:
            existing_solves.add(title_slug)
            prob_info = problem_info[title_slug]

            is_daily_solve = bool(
                today_daily_slug
                and title_slug.lower() == today_daily_slug.lower()
                and day == date.today()
            )

            new_solve = Solve(
                user_id=user.id,
                platform="leetcode", source_handle=handle, account_version=account_version,
                problem_url=f"https://leetcode.com/problems/{title_slug}/",
                title_slug=title_slug,
                title=sub.get("title"),
                difficulty=prob_info.get("difficulty"),
                ac_rate=prob_info.get("ac_rate"),
                solved_at=solved_at,
                is_daily=is_daily_solve,
            )
            db.add(new_solve)
            new_count += 1

        solves_by_date[day] = solves_by_date.get(day, 0) + 1

    for day, ac_count in solves_by_date.items():
        if day in existing_daily:
            existing_daily[day].problems_solved = max(existing_daily[day].problems_solved, ac_count)
        else:
            new_row = DailyActivity(user_id=user.id, date=day, problems_solved=ac_count)
            db.add(new_row)
            existing_daily[day] = new_row

    db.flush()
    ingest_acceptances(db, user_id, platform="leetcode", account_version=account_version,
                       expected_handle=handle, submissions=evidence)
    user.leetcode_last_sync = sync_started
    recalculate_user_points(user, db, today_daily_slug=today_daily_slug)
    db.commit()
    if sync_codeforces and user.codeforces_username:
        new_count += await sync_codeforces_user(db, user)
    return new_count


import asyncio

async def poll_all_users() -> dict:
    """Concurrently poll all users with a max concurrency limit (Semaphore=5) and separate DB sessions."""
    db = SessionLocal()
    users = []
    try:
        users = db.query(User.id, User.leetcode_username).all()
    finally:
        db.close()

    semaphore = asyncio.Semaphore(5)
    results = {}

    async def _safe_poll(user_id: int, username: str):
        async with semaphore:
            user_db = SessionLocal()
            try:
                u = user_db.query(User).filter(User.id == user_id).first()
                if u:
                    solves = await poll_user(user_db, u)
                    results[username] = solves
            except Exception as e:
                logger.error("Error polling user %s (ID %s): %s", username, user_id, e)
                results[username] = 0
            finally:
                user_db.close()

    tasks = [_safe_poll(u.id, u.leetcode_username) for u in users]
    if tasks:
        await asyncio.gather(*tasks)

    logger.info("Poll complete for %d users: %s", len(users), results)
    return results


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_all_users,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="poll_all_users",
    )
    scheduler.add_job(
        refresh_zerotrac_dataset,
        "interval",
        weeks=1,
        id="refresh_zerotrac_dataset",
    )
    scheduler.start()
    return scheduler
