import logging
from time import perf_counter
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date

IST = timezone(timedelta(hours=5, minutes=30))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from .config import POLL_INTERVAL_MINUTES
from .database import SessionLocal
from .models import User, Solve, DailyActivity, DailyChallenge, ProviderCalendar
from .leetcode_client import fetch_leetcode_user_data, fetch_today_daily_challenge_slug, fetch_monthly_daily_challenges, fetch_problem_info, LeetCodeError
from .point_calculator import recalculate_user_points
from .contest_ratings import refresh_zerotrac_dataset
from .codeforces_sync import sync_codeforces_user
from .tracking import ProviderAcceptance, capture_score_baseline, ingest_acceptances, validate_acceptances
from .timekeeping import utc_now, ist_date
from .sync_context import SyncOwnershipLost, lock_attempt, checkpoint

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


async def poll_user(db: Session, user: User, sync_codeforces: bool = True, *,
                    raise_on_unavailable: bool = False, report=None,
                    force_codeforces: bool = False, attempt=None) -> int:
    """Attempt each linked platform independently; preserve the integer API."""
    from .sync_report import SyncReport
    report = report if report is not None else SyncReport()
    added = 0
    try:
        added += await _poll_leetcode_user(db, user, attempt=attempt)
        report.leetcode = "synced"
    except SyncOwnershipLost:
        raise
    except Exception as error:
        db.rollback()
        report.leetcode = "unavailable"
        logger.warning("LeetCode sync could not finish for user %d (%s)", user.id, type(error).__name__)
    if sync_codeforces:
        db.refresh(user)
        if user.codeforces_username:
            try:
                added += await sync_codeforces_user(db, user, force=force_codeforces, report=report, attempt=attempt)
            except SyncOwnershipLost:
                raise
            except Exception as error:
                db.rollback()
                report.codeforces = "unavailable"
                logger.warning("Codeforces sync could not finish for user %d (%s)", user.id, type(error).__name__)
    if raise_on_unavailable and not report.any_success:
        raise LeetCodeError(report.message or "Sync could not finish. Please try again later.")
    return added


async def _poll_leetcode_user(db: Session, user: User, *, attempt=None) -> int:
    """Fetch accepted questions; absent stored questions count as database-first."""
    db.refresh(user)
    handle, user_id = user.leetcode_username, user.id
    account_version, previous_sync = user.leetcode_account_version, user.leetcode_last_sync
    sync_started = utc_now()
    started = perf_counter()
    db.commit()  # Release the connection before provider requests.
    try:
        data = await fetch_leetcode_user_data(handle)
        provider_finished = perf_counter()
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
        # Stored metadata survives restarts; avoid refetching known questions.
        slugs = {row.title_slug for row in evidence}
        problem_info = await asyncio.to_thread(_saved_problem_info, db.get_bind(),
                                             user_id, account_version, slugs)
        new_slugs = slugs - problem_info.keys()
        missing = [slug for slug in slugs if slug not in problem_info
                   or problem_info[slug]["difficulty"] not in {"Easy", "Medium", "Hard"}
                   or problem_info[slug]["ac_rate"] is None]
        async def load_metadata():
            values = await asyncio.gather(*(fetch_problem_info(slug) for slug in missing))
            return dict(zip(missing, values))
        fetched, daily_slug = await asyncio.gather(load_metadata(),
            fetch_today_daily_challenge_slug() if previous_sync is not None and new_slugs
            else asyncio.sleep(0, result=None))
        problem_info.update(fetched)
        metadata_finished = perf_counter()
    except (LeetCodeError, httpx.HTTPError, ValueError, OverflowError, OSError) as error:
        status = error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
        logger.warning("LeetCode accepted history unavailable for user %d: %s, HTTP %s", user_id, type(error).__name__, status)
        raise LeetCodeError("LeetCode is temporarily unavailable; its saved data is unchanged.") from None

    new_count = await asyncio.to_thread(_persist_leetcode_snapshot, db.get_bind(),
        user_id=user_id, handle=handle, account_version=account_version,
        previous_sync=previous_sync, sync_started=sync_started, data=data,
        submissions=submissions, evidence=evidence, problem_info=problem_info, attempt=attempt, daily_slug=daily_slug)
    # Sessions and ORM objects never cross threads. Refresh the caller's view
    # after the separate write transaction has committed.
    db.expire_all()
    if new_count is None:
        return 0
    db.refresh(user)
    logger.info("LeetCode sync timing user %d: provider=%.2fs metadata=%.2fs persist=%.2fs metadata_lookups=%d total=%.2fs",
                user_id, provider_finished - started, metadata_finished - provider_finished,
                perf_counter() - metadata_finished, len(missing), perf_counter() - started)
    return new_count


def _saved_problem_info(bind, user_id, account_version, slugs):
    if not slugs:
        return {}
    with Session(bind=bind) as db:
        rows = db.query(Solve.title_slug, Solve.difficulty, Solve.ac_rate).filter(
            Solve.user_id == user_id, Solve.platform == "leetcode",
            Solve.account_version == account_version, Solve.title_slug.in_(slugs)).all()
        return {slug: {"difficulty": difficulty, "ac_rate": ac_rate}
                for slug, difficulty, ac_rate in rows}


def _persist_leetcode_snapshot(bind, *, user_id, handle, account_version,
                                previous_sync, sync_started, data, submissions,
                                evidence, problem_info, attempt=None, daily_slug=None):
    """Synchronous database work owns a worker-thread session, not the API loop."""
    with Session(bind=bind, autoflush=False) as db:
        user = db.query(User).filter_by(id=user_id).populate_existing().with_for_update().first()
        if user is None:
            return None
        if (user.leetcode_username != handle or user.leetcode_account_version != account_version
                or user.leetcode_last_sync != previous_sync):
            db.rollback()
            return None
        job = lock_attempt(db, user, attempt)
        capture_score_baseline(db, user_id)

        # 1. Update user metadata & difficulty totals
        if data.get("avatar_url"):
            user.avatar_url = data["avatar_url"]
        diffs = data.get("difficulty_counts") or {}
        user.easy_count = diffs.get("Easy", 0)
        user.medium_count = diffs.get("Medium", 0)
        user.hard_count = diffs.get("Hard", 0)
        user.official_streak = data.get("official_streak", 0)

        # Provider calendars count attempts, not unique accepted questions.
        calendars = {row.date: row for row in db.query(ProviderCalendar).filter_by(
            user_id=user_id, platform="leetcode", account_version=account_version).all()}
        for day, count in (data.get("submission_calendar") or {}).items():
            if type(day) is not date or type(count) is not int or count < 0:
                continue
            row = calendars.get(day)
            if row is None:
                row = ProviderCalendar(user_id=user_id, platform="leetcode", account_version=account_version, date=day)
                db.add(row)
            row.submission_count = count
            row.source = "leetcode_submission_calendar"
            row.coverage = "provider_partial"
            row.observed_at = sync_started

        # Dedup accepted questions; ingestion records one first date per question.
        new_count = 0
        live_daily_solves = []

        existing_solves = {
            r[0] for r in db.query(Solve.title_slug).filter(Solve.user_id == user.id, Solve.platform == "leetcode").all()
        }

        for sub in sorted(submissions, key=lambda row: (int(row["timestamp"]), int(row["id"]))):
            title_slug = sub["titleSlug"]
            solved_at = datetime.fromtimestamp(int(sub["timestamp"]), tz=timezone.utc).replace(tzinfo=None)
            day = datetime.fromtimestamp(int(sub["timestamp"]), tz=IST).date()

            if title_slug not in existing_solves:
                existing_solves.add(title_slug)
                prob_info = problem_info[title_slug]

                is_daily_solve = False  # Daily rewards require a separate live check.

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
                if (daily_slug == title_slug and previous_sync is not None
                        and solved_at > previous_sync and user.created_at is not None
                        and solved_at >= user.created_at and ist_date(solved_at) == ist_date(sync_started)):
                    live_daily_solves.append(new_solve)
                new_count += 1

        db.flush()
        ingest_acceptances(db, user_id, platform="leetcode", account_version=account_version,
                           expected_handle=handle, submissions=evidence)
        # Retry genuinely missing metadata without changing previously locked
        # awards. Questions whose metadata was unavailable can then earn once.
        for solve in db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "leetcode",
                Solve.account_version == account_version, Solve.title_slug.in_(problem_info)).all():
            info = problem_info[solve.title_slug]
            if solve.difficulty not in {"Easy", "Medium", "Hard"} and info.get("difficulty") in {"Easy", "Medium", "Hard"}:
                solve.difficulty = info["difficulty"]
            if solve.ac_rate is None and info.get("ac_rate") is not None:
                solve.ac_rate = info["ac_rate"]
        user.leetcode_last_sync = sync_started
        recalculate_user_points(user, db, revision_windows={"leetcode": previous_sync},
                               daily_solve_ids={solve.id for solve in live_daily_solves})
        checkpoint(job, new_count)
        db.commit()
        logger.info("LeetCode saved for user %d: %d new question entries", user_id, new_count)
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

    logger.info("All-user poll started: %d accounts", len(users))
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

    logger.info("All-user poll finished: %d accounts checked, %d new question entries", len(results), sum(results.values()))
    return results


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_all_users,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        # Anchor to a fixed clock rather than restarting a full interval after
        # every deployment. With 15 minutes, ticks are :00/:15/:30/:45.
        start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
        coalesce=True,
        max_instances=1,
        id="poll_all_users",
    )
    scheduler.add_job(
        refresh_zerotrac_dataset,
        "interval",
        weeks=1,
        id="refresh_zerotrac_dataset",
    )
    from .sync_jobs import process_sync_jobs
    scheduler.add_job(process_sync_jobs, "interval", seconds=5, id="manual_sync_jobs", max_instances=1)
    scheduler.start()
    return scheduler
