import asyncio
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from .codeforces_client import fetch_accepted_history, CodeforcesError
from .models import User, Solve, PlatformActivity, PointAward, AcceptedSubmission
from .point_calculator import recalculate_user_points
from .timekeeping import IST, ist_date
from .tracking import record_acceptance, capture_score_baseline, award_live_revision

from .leases import user_sync_lease, is_lease_active

logger = logging.getLogger("codestreak.codeforces")
IST = timezone(timedelta(hours=5, minutes=30))


class UserSyncLock:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self._ctx = None

    def locked(self) -> bool:
        return is_lease_active(f"sync:user:{self.user_id}")

    async def __aenter__(self):
        self._ctx = user_sync_lease(self.user_id, ttl_seconds=120.0, wait_timeout=30.0)
        lease = await self._ctx.__aenter__()
        if not lease:
            raise TimeoutError(f"Could not acquire sync lock for user {self.user_id}")
        return lease

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._ctx:
            await self._ctx.__aexit__(exc_type, exc_val, exc_tb)


def user_sync_lock(user_id: int) -> UserSyncLock:
    return UserSyncLock(user_id)


async def sync_codeforces_user(db: Session, user: User, already_leased: bool = False) -> int:
    if already_leased:
        return await _sync_codeforces_user_inner(db, user)
    async with user_sync_lease(user.id, ttl_seconds=120.0) as lease:
        if not lease:
            return 0
        return await _sync_codeforces_user_inner(db, user)


async def _sync_codeforces_user_inner(db: Session, user: User) -> int:
    db.refresh(user)
    handle, user_id = user.codeforces_username, user.id
    generation = user.codeforces_account_version
    previous_sync = user.codeforces_last_sync
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
    if user.codeforces_username != handle or user.codeforces_account_version != generation:
        return 0
    capture_score_baseline(db, user_id)
    existing = {s.title_slug: s for s in db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces").all()}
    incoming = {row["slug"]: row for row in history}
    added = 0
    for slug, solve in existing.items():
        if slug not in incoming and (full or solve.solved_at.replace(tzinfo=timezone.utc).timestamp() >= since):
            db.query(PointAward).filter_by(solve_id=solve.id).delete(synchronize_session=False)
            db.query(AcceptedSubmission).filter_by(solve_id=solve.id).delete(synchronize_session=False)
            db.delete(solve)
    for slug, row in incoming.items():
        solve = existing.get(slug)
        solved_at = datetime.fromtimestamp(row["timestamp"], timezone.utc).replace(tzinfo=None)
        if solve is None:
            solve = Solve(
                user_id=user_id,
                title_slug=slug,
                platform="codeforces",
                is_daily=False,
                scoring_version="cf-linear-v1",
                solved_at=solved_at,
                first_solve_at=solved_at if full else None,
                first_solve_verified=full,
                account_version=user.codeforces_account_version,
            )
            db.add(solve)
            db.flush()
            added += 1
        # Incremental windows cannot move an established first acceptance forward.
        if full or solved_at < solve.solved_at:
            solve.solved_at = solved_at
        if full:
            solve.first_solve_at = solved_at
            solve.first_solve_verified = True
        solve.title = row["title"]
        solve.account_version = user.codeforces_account_version
        solve.source_handle = handle
        solve.source_submission_id = row["submission_id"]
        solve.problem_rating = row["rating"]
        solve.problem_url = row["url"]
        solve.difficulty = "Rated" if row["rating"] is not None else "Unrated"
        for event_row in row.get("accepted_submissions", [row]):
            event_at = datetime.fromtimestamp(event_row["timestamp"], timezone.utc)
            event = record_acceptance(
                db, user_id, platform="codeforces", account_version=generation,
                submission_id=str(event_row["submission_id"]), title_slug=slug,
                accepted_at=event_at, evidence_kind="provider_full" if full else "provider_live",
                first_solve_verified=bool(full and event_at.replace(tzinfo=None) == solve.first_solve_at),
            )
            event.solve_id = solve.id
            award_live_revision(db, solve, event, previous_sync)
    db.flush()
    counts = Counter(ist_date(s.first_solve_at or s.solved_at) for s in db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces", Solve.first_solve_verified.is_(True), Solve.first_solve_at.isnot(None)).all())
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
