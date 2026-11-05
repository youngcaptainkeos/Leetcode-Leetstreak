import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date

IST = timezone(timedelta(hours=5, minutes=30))

from collections import Counter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from .config import POLL_INTERVAL_MINUTES
from .database import SessionLocal
from .models import User, Solve, DailyActivity, DailyChallenge, AcceptedSubmission, PointAward
from .leetcode_client import fetch_leetcode_user_data, fetch_today_daily_challenge_slug, fetch_monthly_daily_challenges, fetch_problem_info, LeetCodeError
from .point_calculator import recalculate_user_points
from .contest_ratings import refresh_zerotrac_dataset
from .codeforces_sync import sync_codeforces_user
from .timekeeping import IST, ist_date, ist_today, utc_storage, revision_due
from .tracking import record_acceptance
from .scoring import revision_points, SCORING_VERSION
from .platforms import daily_counts
from .streak import current_streak
from .leases import user_sync_lease, acquire_lease, release_lease

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


async def poll_user(db: Session, user: User, sync_codeforces: bool = True, already_leased: bool = False) -> int:
    """Fetch complete LeetCode profile, calendar history, and recent AC submissions for one user."""
    if not already_leased:
        async with user_sync_lease(user.id, ttl_seconds=120.0) as lease:
            if not lease:
                logger.info("User %s (ID %d) sync skipped: lease held by another process.", user.leetcode_username, user.id)
                return 0
            return await _poll_user_inner(db, user, sync_codeforces=sync_codeforces)
    else:
        return await _poll_user_inner(db, user, sync_codeforces=sync_codeforces)


async def _poll_user_inner(db: Session, user: User, sync_codeforces: bool = True) -> int:
    try:
        data = await fetch_leetcode_user_data(user.leetcode_username)
    except LeetCodeError as e:
        logger.warning("LeetCode fetch failed for %s: %s", user.leetcode_username, e)
        return await sync_codeforces_user(db, user, already_leased=True) if sync_codeforces and user.codeforces_username else 0

    today_daily_slug = await fetch_today_daily_challenge_slug()
    if today_daily_slug:
        today_date = ist_today()
        existing_dc = db.query(DailyChallenge).filter(DailyChallenge.date == today_date).first()
        if not existing_dc:
            db.add(DailyChallenge(date=today_date, title_slug=today_daily_slug))
            db.commit()

    db.refresh(user, with_for_update=True)

    # 1. Update user metadata & difficulty totals
    if data.get("avatar_url"):
        user.avatar_url = data["avatar_url"]
    diffs = data.get("difficulty_counts") or {}
    user.easy_count = diffs.get("Easy", 0)
    user.medium_count = diffs.get("Medium", 0)
    user.hard_count = diffs.get("Hard", 0)
    user.official_streak = data.get("official_streak", 0)

    # 2. Ingest recent AC submissions: record evidence, deduplicate question entries, reward eligible revisions
    new_count = 0
    submissions = data.get("recent_submissions") or []
    submissions = sorted(submissions, key=lambda s: int(s.get("timestamp", 0)))

    existing_solves = {
        s.title_slug: s for s in db.query(Solve).filter(
            Solve.user_id == user.id,
            Solve.platform == "leetcode"
        ).all()
    }

    for sub in submissions:
        title_slug = sub["titleSlug"]
        raw_ts = int(sub["timestamp"])
        accepted_at = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
        day = ist_date(accepted_at)
        sub_id = str(sub.get("id") or raw_ts)

        acc_event = record_acceptance(
            db,
            user.id,
            platform="leetcode",
            account_version=user.leetcode_account_version,
            submission_id=sub_id,
            title_slug=title_slug,
            accepted_at=accepted_at,
            evidence_kind="public_recent",
            first_solve_verified=False,
        )

        if title_slug not in existing_solves:
            prob_info = await fetch_problem_info(title_slug)
            is_daily_solve = bool(
                today_daily_slug
                and title_slug.lower() == today_daily_slug.lower()
                and day == ist_today()
            )
            new_solve = Solve(
                user_id=user.id,
                platform="leetcode",
                source_handle=user.leetcode_username,
                problem_url=f"https://leetcode.com/problems/{title_slug}/",
                title_slug=title_slug,
                title=sub.get("title"),
                difficulty=prob_info.get("difficulty"),
                ac_rate=prob_info.get("ac_rate"),
                solved_at=utc_storage(accepted_at),
                first_solve_at=utc_storage(accepted_at),
                first_solve_verified=True,
                is_daily=is_daily_solve,
                account_version=user.leetcode_account_version,
                score_components_state="points-components-v2",
            )
            db.add(new_solve)
            db.flush()
            existing_solves[title_slug] = new_solve
            acc_event.solve_id = new_solve.id
            new_count += 1
        else:
            solve = existing_solves[title_slug]
            acc_event.solve_id = solve.id

            # DATA-09: check 7-day revision eligibility from first solve or last rewarded revision
            latest_revision = (
                db.query(PointAward)
                .filter(PointAward.solve_id == solve.id, PointAward.kind == "revision")
                .order_by(PointAward.earned_at.desc())
                .first()
            )
            anchor_time = latest_revision.earned_at if latest_revision else (solve.first_solve_at or solve.solved_at)
            if anchor_time and revision_due(accepted_at, anchor_time):
                award_key = f"revision:{solve.id}:{acc_event.id}"
                if not db.query(PointAward.id).filter(PointAward.award_key == award_key).first():
                    active_dates = set(daily_counts(db, [user.id])[user.id])
                    streak_on_date = current_streak(active_dates, day)
                    rev_pts = revision_points(streak_on_date)
                    db.add(PointAward(
                        award_key=award_key,
                        user_id=user.id,
                        solve_id=solve.id,
                        submission_id=acc_event.id,
                        kind="revision",
                        points=rev_pts,
                        earned_at=utc_storage(accepted_at),
                        scoring_version=SCORING_VERSION,
                        input_snapshot={
                            "streak_days": streak_on_date,
                            "anchor_time": anchor_time.isoformat(),
                            "accepted_at": utc_storage(accepted_at).isoformat(),
                        },
                    ))
                    db.flush()

    # 3. Update DailyActivity strictly from verified first solves of distinct LeetCode problems
    lc_solves = db.query(Solve).filter(
        Solve.user_id == user.id,
        Solve.platform == "leetcode",
    ).all()
    counts_by_day = Counter(
        ist_date(s.first_solve_at or s.solved_at)
        for s in lc_solves
        if (s.first_solve_verified or s.first_solve_at is not None or s.solved_at is not None)
    )
    db.query(DailyActivity).filter(DailyActivity.user_id == user.id).delete()
    for day, count in counts_by_day.items():
        db.add(DailyActivity(user_id=user.id, date=day, problems_solved=count))
    db.flush()

    user.leetcode_last_sync = datetime.now(timezone.utc).replace(tzinfo=None)
    total_known = (user.easy_count or 0) + (user.medium_count or 0) + (user.hard_count or 0)
    user.leetcode_history_gap = total_known > len(lc_solves)
    user.leetcode_history_state = "partial" if user.leetcode_history_gap else "complete"

    recalculate_user_points(user, db, today_daily_slug=today_daily_slug)
    db.commit()
    if sync_codeforces and user.codeforces_username:
        new_count += await sync_codeforces_user(db, user, already_leased=True)
    return new_count


import asyncio

async def poll_all_users() -> dict:
    """Concurrently poll all users with a max concurrency limit (Semaphore=5) and separate DB sessions.
    Coordinates across worker processes using distributed job lease 'scheduler:job:poll_all_users'.
    """
    lease_owner = acquire_lease("scheduler:job:poll_all_users", ttl_seconds=300.0)
    if not lease_owner:
        logger.info("poll_all_users skipped: already running in another worker/process.")
        return {}

    try:
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
    finally:
        release_lease("scheduler:job:poll_all_users", lease_owner)


def start_scheduler(immediate: bool = False) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    job_kwargs = {"next_run_time": datetime.now()} if immediate else {}
    scheduler.add_job(
        poll_all_users,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="poll_all_users",
        **job_kwargs,
    )
    scheduler.add_job(
        refresh_zerotrac_dataset,
        "interval",
        weeks=1,
        id="refresh_zerotrac_dataset",
        **job_kwargs,
    )
    scheduler.start()
    return scheduler
