import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from .config import POLL_INTERVAL_MINUTES
from .database import SessionLocal
from .models import User, Solve, DailyActivity
from .leetcode_client import fetch_leetcode_user_data, LeetCodeError

logger = logging.getLogger("codestreak.scheduler")


async def poll_user(db: Session, user: User) -> int:
    """Fetch complete LeetCode profile, calendar history, and recent AC submissions for one user."""
    try:
        data = await fetch_leetcode_user_data(user.leetcode_username)
    except LeetCodeError as e:
        logger.warning("LeetCode fetch failed for %s: %s", user.leetcode_username, e)
        return 0

    # 1. Update user metadata & difficulty totals
    if data.get("avatar_url"):
        user.avatar_url = data["avatar_url"]
    diffs = data.get("difficulty_counts") or {}
    user.easy_count = diffs.get("Easy", 0)
    user.medium_count = diffs.get("Medium", 0)
    user.hard_count = diffs.get("Hard", 0)
    user.official_streak = data.get("official_streak", 0)

    # 2. Sync full submission calendar into DailyActivity
    cal_map = data.get("submission_calendar") or {}
    existing_daily = {
        r.date: r for r in db.query(DailyActivity).filter(DailyActivity.user_id == user.id).all()
    }

    for day, solve_count in cal_map.items():
        if day in existing_daily:
            existing_daily[day].problems_solved = max(existing_daily[day].problems_solved, solve_count)
        else:
            new_row = DailyActivity(user_id=user.id, date=day, problems_solved=solve_count)
            db.add(new_row)
            existing_daily[day] = new_row

    # 3. Dedup recent AC submissions into Solves ledger
    new_count = 0
    submissions = data.get("recent_submissions") or []
    existing_solves = {
        r[0] for r in db.query(Solve.title_slug).filter(Solve.user_id == user.id).all()
    }

    for sub in submissions:
        title_slug = sub["titleSlug"]
        if title_slug in existing_solves:
            continue

        existing_solves.add(title_slug)
        solved_at = datetime.fromtimestamp(int(sub["timestamp"]), tz=timezone.utc)
        db.add(Solve(
            user_id=user.id,
            title_slug=title_slug,
            title=sub.get("title"),
            solved_at=solved_at,
        ))

        day = solved_at.date()
        if day in existing_daily:
            existing_daily[day].problems_solved = max(existing_daily[day].problems_solved, 1)
        else:
            new_row = DailyActivity(user_id=user.id, date=day, problems_solved=1)
            db.add(new_row)
            existing_daily[day] = new_row

        new_count += 1

    db.commit()
    return new_count


async def poll_all_users() -> dict:
    db = SessionLocal()
    results = {}
    try:
        users = db.query(User).all()
        for user in users:
            results[user.leetcode_username] = await poll_user(db, user)
    finally:
        db.close()
    logger.info("Poll complete: %s", results)
    return results


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_all_users,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="poll_all_users",
        next_run_time=datetime.now(),  # run once immediately on startup
    )
    scheduler.start()
    return scheduler
