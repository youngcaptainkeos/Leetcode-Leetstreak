import asyncio
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from .codeforces_client import fetch_accepted_history, CodeforcesError
from .models import User, Solve, PlatformActivity
from .point_calculator import recalculate_user_points

logger = logging.getLogger("codestreak.codeforces")
IST = timezone(timedelta(hours=5, minutes=30))
_locks = {}


def user_sync_lock(user_id):
    return _locks.setdefault(user_id, asyncio.Lock())


async def sync_codeforces_user(db: Session, user: User) -> int:
    lock = user_sync_lock(user.id)
    if lock.locked():
        return 0
    async with lock:
        db.refresh(user)
        handle, user_id = user.codeforces_username, user.id
        if not handle:
            return 0
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if user.codeforces_last_sync and now - user.codeforces_last_sync < timedelta(minutes=10):
            return 0
        full = not user.codeforces_last_full_sync or now - user.codeforces_last_full_sync > timedelta(days=7)
        since = None if full else int((user.codeforces_last_sync.replace(tzinfo=timezone.utc) - timedelta(days=2)).timestamp())
        db.commit()  # Do not hold a database connection during remote requests.
        try:
            history = await fetch_accepted_history(handle, since)
        except CodeforcesError as error:
            db.refresh(user)
            user.codeforces_sync_error = str(error)[:300]
            db.commit()
            logger.warning("Codeforces sync unavailable for user %d", user_id)
            return 0
        db.refresh(user, with_for_update=True)
        if user.codeforces_username != handle:
            return 0
        existing = {s.title_slug: s for s in db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces").all()}
        incoming = {row["slug"]: row for row in history}
        added = 0
        for slug, solve in existing.items():
            if slug not in incoming and (full or solve.solved_at.replace(tzinfo=timezone.utc).timestamp() >= since):
                db.delete(solve)
        for slug, row in incoming.items():
            solve = existing.get(slug)
            solved_at = datetime.fromtimestamp(row["timestamp"], timezone.utc).replace(tzinfo=None)
            if solve is None:
                solve = Solve(user_id=user_id, title_slug=slug, platform="codeforces", is_daily=False, scoring_version="cf-linear-v1", solved_at=solved_at)
                db.add(solve)
                added += 1
            elif not full and solve.solved_at < solved_at:
                # An older first AC is outside this incremental scan's window.
                if row["rating"] is not None:
                    solve.problem_rating = row["rating"]
                continue
            solve.title = row["title"]
            solve.solved_at = solved_at
            solve.source_handle = handle
            solve.source_submission_id = row["submission_id"]
            solve.problem_rating = row["rating"]
            solve.problem_url = row["url"]
            solve.difficulty = "Rated" if row["rating"] is not None else "Unrated"
        db.flush()
        counts = Counter(s.solved_at.replace(tzinfo=timezone.utc).astimezone(IST).date() for s in db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces").all())
        db.query(PlatformActivity).filter(PlatformActivity.user_id == user_id, PlatformActivity.platform == "codeforces").delete()
        for day, count in counts.items():
            db.add(PlatformActivity(user_id=user_id, platform="codeforces", date=day, problems_solved=count))
        db.flush()
        user.codeforces_last_sync = now
        if full:
            user.codeforces_last_full_sync = now
        user.codeforces_sync_error = None
        recalculate_user_points(user, db)
        db.commit()
        return added


async def background_codeforces_sync(user_id: int):
    from .database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            await sync_codeforces_user(db, user)
    except Exception:
        db.rollback()
        logger.exception("Codeforces background sync failed for user %d", user_id)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.codeforces_sync_error = "Sync interrupted. Automatic syncing will retry later."
            db.commit()
    finally:
        db.close()
