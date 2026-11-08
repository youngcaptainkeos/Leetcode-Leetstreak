import asyncio
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from .codeforces_client import fetch_accepted_history, CodeforcesError
from .models import User, Solve, PlatformActivity, AcceptedSubmission, PointAward
from .point_calculator import recalculate_user_points
from .sync_context import lock_attempt, checkpoint
from .tracking import ProviderAcceptance, capture_score_baseline, ingest_acceptances, validate_acceptances

logger = logging.getLogger("codestreak.codeforces")
IST = timezone(timedelta(hours=5, minutes=30))
_locks = {}


def user_sync_lock(user_id):
    return _locks.setdefault(user_id, asyncio.Lock())


async def sync_codeforces_user(db: Session, user: User, *, force=False, report=None, attempt=None) -> int:
    lock = user_sync_lock(user.id)
    if lock.locked():
        if report is not None:
            report.codeforces = "running"
        return 0
    async with lock:
        db.refresh(user)
        handle, user_id = user.codeforces_username, user.id
        account_version = user.codeforces_account_version
        previous_sync = user.codeforces_last_sync
        if not handle:
            return 0
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not force and user.codeforces_last_sync and now - user.codeforces_last_sync < timedelta(minutes=10):
            if report is not None:
                report.codeforces = "recent"
            return 0
        full = not user.codeforces_last_full_sync or now - user.codeforces_last_full_sync > timedelta(days=7)
        since = None if full else int((user.codeforces_last_sync.replace(tzinfo=timezone.utc) - timedelta(days=2)).timestamp())
        proof_unavailable = False
        db.commit()  # Do not hold a database connection during remote requests.
        try:
            history = await fetch_accepted_history(handle, since)
            if not full:
                proved = {row.title_slug: row.first_solve_at for row in db.query(Solve).filter_by(
                    user_id=user_id, platform="codeforces", account_version=account_version,
                    first_solve_verified=True).all() if row.first_solve_at is not None
                    and row.source_handle and row.source_handle.casefold() == handle.casefold()}
                # A recent window cannot establish the earliest AC for a newly
                # discovered problem. Fetch complete public history instead of
                # guessing, or delaying its streak eligibility for seven days.
                needs_full = any(row["slug"] not in proved or row["timestamp"] <
                    proved[row["slug"]].replace(tzinfo=timezone.utc).timestamp() for row in history)
                db.commit()
                if needs_full:
                    try:
                        complete = await fetch_accepted_history(handle, None)
                    except CodeforcesError:
                        # Keep valid recent solves/unique points available. A
                        # failed proof refresh must not invent first-solve dates.
                        proof_unavailable = True
                    else:
                        history, full, since = complete, True, None
        except CodeforcesError as error:
            if report is not None:
                report.codeforces = "unavailable"
            db.refresh(user, with_for_update=True)
            if user.codeforces_username == handle and user.codeforces_account_version == account_version and user.codeforces_last_sync == previous_sync:
                job = lock_attempt(db, user, attempt)
                user.codeforces_sync_error = str(error)[:300]
                checkpoint(job)
                db.commit()
            else:
                db.rollback()
            logger.warning("Codeforces sync unavailable for user %d", user_id)
            return 0
        added = await asyncio.to_thread(_persist_codeforces_history, db.get_bind(),
            user_id=user_id, handle=handle, account_version=account_version,
            previous_sync=previous_sync, now=now, full=full, since=since, history=history,
            proof_unavailable=proof_unavailable, attempt=attempt)
        db.expire_all()
        if report is not None:
            report.codeforces = "incomplete" if proof_unavailable else "synced"
        return added


def _persist_codeforces_history(bind, *, user_id, handle, account_version,
                               previous_sync, now, full, since, history, proof_unavailable=False, attempt=None):
    """Keep synchronous history/score persistence off the HTTP event loop."""
    with Session(bind=bind, autoflush=False) as db:
        user = db.query(User).filter_by(id=user_id).populate_existing().with_for_update().first()
        if user is None:
            return 0
        if (user.codeforces_username != handle or user.codeforces_account_version != account_version
                or user.codeforces_last_sync != previous_sync):
            db.rollback()
            return 0
        job = lock_attempt(db, user, attempt)
        evidence = [ProviderAcceptance(str(event["submission_id"]), row["slug"],
                    datetime.fromtimestamp(event["timestamp"], timezone.utc).replace(tzinfo=None))
                    for row in history for event in row["accepted_submissions"]]
        validate_acceptances(evidence, "codeforces")
        capture_score_baseline(db, user_id)
        existing = {s.title_slug: s for s in db.query(Solve).filter(Solve.user_id == user_id, Solve.platform == "codeforces").all()}
        incoming = {row["slug"]: row for row in history}
        added = 0
        for slug, solve in existing.items():
            if slug not in incoming and (full or solve.solved_at.replace(tzinfo=timezone.utc).timestamp() >= since):
                # Keep raw provider observations after a rejudgement. Revaluing
                # explicit awards needs R3, not an implicit cascade deletion.
                if db.query(PointAward.id).filter_by(solve_id=solve.id).first():
                    # Absence from public history is not proof of a revoked AC
                    # (e.g. a Gym can become unavailable). Retain credit, flag
                    # the gap, and keep syncing other questions.
                    solve.first_solve_verified = False
                    solve.first_solve_at = None
                    solve.score_components_state = "history_review"
                    db.query(AcceptedSubmission).filter_by(solve_id=solve.id).update(
                        {AcceptedSubmission.first_solve_verified: False}, synchronize_session="fetch")
                    continue
                db.query(AcceptedSubmission).filter_by(solve_id=solve.id).update(
                    {AcceptedSubmission.solve_id: None, AcceptedSubmission.first_solve_verified: False}, synchronize_session="fetch")
                db.delete(solve)
        for slug, row in incoming.items():
            solve = existing.get(slug)
            solved_at = datetime.fromtimestamp(row["timestamp"], timezone.utc).replace(tzinfo=None)
            if solve is None:
                solve = Solve(user_id=user_id, title_slug=slug, platform="codeforces", account_version=account_version, is_daily=False, scoring_version="cf-linear-v1", solved_at=solved_at)
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
        ingest_acceptances(db, user_id, platform="codeforces", account_version=account_version,
                           expected_handle=handle, submissions=evidence, complete_history=full)
        user.codeforces_last_sync = now
        if full:
            user.codeforces_last_full_sync = now
        user.codeforces_sync_error = ("Solves synced; some first-solve dates await full-history verification."
                                     if proof_unavailable else None)
        recalculate_user_points(user, db, revision_windows={"codeforces": previous_sync})
        checkpoint(job, added)
        db.commit()
        logger.info("Codeforces saved for user %d: %d new question entries", user_id, added)
        return added


async def background_codeforces_sync(user_id: int):
    from .database import SessionLocal
    db = SessionLocal()
    expected_account = None
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            expected_account = (user.codeforces_username, user.codeforces_account_version)
            await sync_codeforces_user(db, user)
    except Exception:
        db.rollback()
        logger.exception("Codeforces background sync failed for user %d", user_id)
        user = db.query(User).filter(User.id == user_id).populate_existing().with_for_update().first()
        if user and expected_account == (user.codeforces_username, user.codeforces_account_version):
            user.codeforces_sync_error = "Sync interrupted. Automatic syncing will retry later."
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()
