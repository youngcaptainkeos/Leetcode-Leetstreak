"""Persist manual sync work before acknowledging it to a browser popup."""
import asyncio
import logging
from datetime import timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal, get_db
from .models import User, UserSyncJob
from .security import current_user, require_self
from .timekeeping import utc_now
from .leetcode_client import LeetCodeError

router = APIRouter()
logger = logging.getLogger("codestreak.sync_jobs")
_worker_lock = asyncio.Lock()


def job_payload(job):
    if job is None:
        return None
    return {"id": job.id, "state": job.state, "new_solves": job.new_solves,
            "message": job.message,
            "created_at": job.created_at.replace(tzinfo=timezone.utc),
            "finished_at": job.finished_at.replace(tzinfo=timezone.utc) if job.finished_at else None}


@router.post("/api/users/{user_id}/sync-jobs", status_code=202)
def enqueue_sync(user_id: int, background_tasks: BackgroundTasks,
                 db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    user = db.query(User).filter_by(id=user_id).populate_existing().with_for_update().one()
    existing = db.query(UserSyncJob).filter_by(user_id=user_id).filter(
        UserSyncJob.state.in_(["queued", "running"])).order_by(UserSyncJob.created_at.desc()).first()
    if existing is None:
        # A server-side cooldown also applies across devices and popup sessions.
        existing = db.query(UserSyncJob).filter_by(user_id=user_id).filter(
            UserSyncJob.created_at > utc_now() - timedelta(seconds=30)).order_by(UserSyncJob.created_at.desc()).first()
    if existing is None:
        existing = UserSyncJob(id=str(uuid4()), user_id=user_id, state="queued",
            leetcode_account_version=user.leetcode_account_version,
            codeforces_account_version=user.codeforces_account_version,
            session_version=user.session_version)
        db.add(existing)
    db.commit()
    result = job_payload(existing)
    db.commit()  # Release the request connection before background processing.
    # Processing is independent of the popup; the scheduler also recovers queued jobs.
    background_tasks.add_task(process_sync_jobs)
    return {"job": result}


@router.get("/api/users/{user_id}/sync-jobs/latest")
def latest_sync(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    job = db.query(UserSyncJob).filter_by(user_id=user_id).order_by(UserSyncJob.created_at.desc()).first()
    return {"job": job_payload(job)}


async def process_sync_jobs():
    from .scheduler import poll_user
    if _worker_lock.locked():
        return
    async with _worker_lock:
        db = SessionLocal()
        job_id = None
        try:
            now = utc_now()
            # A killed process cannot leave a permanent spinning state.
            db.query(UserSyncJob).filter(UserSyncJob.state == "running", UserSyncJob.lease_until < now).update(
                {UserSyncJob.state: "failed", UserSyncJob.finished_at: now,
                 UserSyncJob.message: "Sync was interrupted. Please try again."}, synchronize_session=False)
            db.commit()
            job = db.query(UserSyncJob).filter_by(state="queued").order_by(
                UserSyncJob.created_at).with_for_update(skip_locked=True).first()
            if job is None:
                return
            job_id = job.id
            job.state, job.started_at, job.lease_until = "running", now, now + timedelta(minutes=10)
            user_id = job.user_id
            expected = (job.leetcode_account_version, job.codeforces_account_version, job.session_version)
            db.commit()
            user = db.query(User).filter_by(id=user_id).first()
            if user is None or expected != (user.leetcode_account_version, user.codeforces_account_version, user.session_version):
                raise LeetCodeError("Your linked account or session changed. Please start Sync again.")
            added = await asyncio.wait_for(poll_user(db, user, raise_on_unavailable=True), timeout=300)
            db.refresh(user)
            if expected != (user.leetcode_account_version, user.codeforces_account_version, user.session_version):
                raise LeetCodeError("Your linked account or session changed. Please start Sync again.")
            message = "LeetCode synced; Codeforces is temporarily unavailable." if user.codeforces_username and user.codeforces_sync_error else None
            job = db.query(UserSyncJob).filter_by(id=job_id, state="running").with_for_update().first()
            if job:
                job.state, job.new_solves, job.message, job.finished_at = "succeeded", added, message, utc_now()
                job.lease_until = None
                db.commit()
        except Exception as error:
            db.rollback()
            logger.warning("Manual sync job failed (%s)", type(error).__name__)
            if job_id:
                job = db.query(UserSyncJob).filter_by(id=job_id, state="running").with_for_update().first()
                if job:
                    job.state, job.finished_at, job.lease_until = "failed", utc_now(), None
                    job.message = str(error)[:300] if isinstance(error, LeetCodeError) else "Sync could not finish. Please try again in a minute."
                    db.commit()
        finally:
            db.close()
