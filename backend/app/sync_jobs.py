"""Persist manual sync work before acknowledging it to a browser popup."""
import asyncio
import logging
import math
from datetime import timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import SessionLocal, get_db
from .models import User, UserSyncJob
from .sync_context import SyncAttempt, SyncOwnershipLost, LEASE_SECONDS
from .sync_report import SyncReport
from .security import current_user, require_self
from .timekeeping import utc_now
from .leetcode_client import LeetCodeError

router = APIRouter()
logger = logging.getLogger("codestreak.sync_jobs")
_worker_lock = asyncio.Lock()
_workers = set()
_kicks = set()
_stopping = False
MAX_ATTEMPTS = 3
SOFT_TIMEOUT = 300


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
        recent = db.query(UserSyncJob).filter_by(user_id=user_id).filter(
            UserSyncJob.created_at > utc_now() - timedelta(seconds=30)).order_by(UserSyncJob.created_at.desc()).first()
        if recent:
            remaining = max(1, math.ceil(30 - (utc_now() - recent.created_at).total_seconds()))
            db.rollback()
            raise HTTPException(429, f"Please wait {remaining} seconds before starting another Sync.",
                                headers={"Retry-After": str(remaining)})
    if existing is None:
        existing = UserSyncJob(id=str(uuid4()), user_id=user_id, state="queued",
            leetcode_account_version=user.leetcode_account_version,
            codeforces_account_version=user.codeforces_account_version,
            session_version=user.session_version)
        db.add(existing)
    db.commit()
    result = job_payload(existing)
    logger.info("Manual sync accepted for user %d: %s", user_id, result["state"])
    db.commit()  # Release the request connection before background processing.
    # Processing is independent of the popup; the scheduler also recovers queued jobs.
    background_tasks.add_task(process_sync_jobs)
    return {"job": result}


@router.get("/api/users/{user_id}/sync-jobs/latest")
def latest_sync(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    job = db.query(UserSyncJob).filter_by(user_id=user_id).order_by(UserSyncJob.created_at.desc()).first()
    return {"job": job_payload(job)}


def _claim_job():
    with SessionLocal() as db:
        now = utc_now()
        expired = db.query(UserSyncJob).filter(UserSyncJob.state == "running",
            UserSyncJob.lease_until < now).with_for_update(skip_locked=True).limit(20).all()
        for job in expired:
            job.worker_token, job.lease_until = None, None
            if job.attempts >= MAX_ATTEMPTS:
                job.state, job.finished_at = "failed", now
                job.message = "Sync was interrupted repeatedly. Your credited points are safe; please try again."
            else:
                job.state, job.finished_at = "queued", None
                job.message = "Resuming an interrupted Sync…"
        db.flush()
        job = db.query(UserSyncJob).filter_by(state="queued").order_by(
            UserSyncJob.created_at).with_for_update(skip_locked=True).first()
        if job is None:
            db.commit()
            return None
        job.state, job.started_at = "running", now
        job.worker_token = str(uuid4())
        job.attempts = (job.attempts or 0) + 1
        job.lease_until = now + timedelta(seconds=LEASE_SECONDS)
        result = (job.id, job.user_id, job.worker_token)
        db.commit()
        return result


def _renew_job(attempt):
    with SessionLocal() as db:
        count = db.query(UserSyncJob).filter_by(id=attempt.job_id,
            worker_token=attempt.token, state="running").update(
                {UserSyncJob.lease_until: utc_now() + timedelta(seconds=LEASE_SECONDS)},
                synchronize_session=False)
        db.commit()
        return bool(count)


async def _heartbeat(attempt):
    while True:
        await asyncio.sleep(10)
        try:
            if not await asyncio.to_thread(_renew_job, attempt):
                return
        except Exception as error:
            # A later writer must still pass the database ownership check.
            logger.warning("Sync heartbeat unavailable (%s)", type(error).__name__)


def _finish_job(attempt, user_id, *, added=0, message=None, error=False):
    with SessionLocal() as db:
        # Writers use the same User -> job lock order.
        user = db.query(User).filter_by(id=user_id).with_for_update().first()
        job = db.query(UserSyncJob).filter_by(id=attempt.job_id, state="running",
            worker_token=attempt.token).with_for_update().first()
        if job is None:
            return
        if user is None or (job.leetcode_account_version, job.codeforces_account_version, job.session_version) != (
                user.leetcode_account_version, user.codeforces_account_version, user.session_version):
            error, message = True, "Your linked account or session changed. Please start Sync again."
        job.state = "failed" if error else "succeeded"
        job.message, job.finished_at = message, utc_now()
        # Per-platform commits checkpoint progress, including across restarts.
        job.new_solves = max(job.new_solves or 0, added)
        job.lease_until, job.worker_token = None, None
        state, count = job.state, job.new_solves
        db.commit()
        logger.info("Manual sync %s for user %d: %d new question entries",
                    state, user_id, count)


def _release_job(attempt):
    with SessionLocal() as db:
        job = db.query(UserSyncJob).filter_by(id=attempt.job_id, state="running",
            worker_token=attempt.token).with_for_update(skip_locked=True).first()
        if job is None:
            # A database writer may still hold this row. It will commit/rollback
            # before the expired-lease recovery can safely reclaim the attempt.
            return
        job.worker_token, job.lease_until = None, None
        if job.attempts >= MAX_ATTEMPTS:
            job.state, job.finished_at = "failed", utc_now()
            job.message = "Sync was interrupted repeatedly. Your credited points are safe; please try again."
        else:
            job.state = "queued"
            job.message = "Resuming an interrupted Sync…"
        db.commit()


async def _perform_job(user_id, attempt, report):
    from .scheduler import poll_user
    with SessionLocal() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if user is None:
            raise SyncOwnershipLost()
        return await poll_user(db, user, raise_on_unavailable=True, report=report,
                               force_codeforces=True, attempt=attempt)


async def process_sync_jobs():
    if _stopping or _worker_lock.locked():
        return
    async with _worker_lock:
        owner = asyncio.current_task()
        _workers.add(owner)
        attempt = work = heartbeat = None
        try:
            claimed = await asyncio.to_thread(_claim_job)
            if claimed is None:
                return
            job_id, user_id, token = claimed
            attempt = SyncAttempt(job_id, token)
            report = SyncReport()
            heartbeat = asyncio.create_task(_heartbeat(attempt))
            work = asyncio.create_task(_perform_job(user_id, attempt, report))
            logger.info("Manual sync processing user %d", user_id)
            try:
                added = await asyncio.wait_for(asyncio.shield(work), timeout=SOFT_TIMEOUT)
            except asyncio.TimeoutError:
                # Cancelling to_thread cannot stop its transaction. Keep the
                # heartbeat and await completion instead of falsely failing it.
                logger.info("Manual sync user %d is finishing saved work", user_id)
                added = await asyncio.shield(work)
            await asyncio.to_thread(_finish_job, attempt, user_id, added=added, message=report.message)
        except SyncOwnershipLost:
            logger.info("Discarded a superseded manual sync attempt")
        except asyncio.CancelledError:
            if work is not None:
                work.cancel()
                await asyncio.gather(work, return_exceptions=True)
            if attempt is not None:
                await asyncio.to_thread(_release_job, attempt)
            raise
        except Exception as error:
            logger.warning("Manual sync job failed (%s)", type(error).__name__)
            if attempt is not None:
                message = str(error)[:300] if isinstance(error, LeetCodeError) else "Sync could not finish. Please try again in a minute."
                await asyncio.to_thread(_finish_job, attempt, user_id, message=message, error=True)
        finally:
            if heartbeat is not None:
                heartbeat.cancel()
                await asyncio.gather(heartbeat, return_exceptions=True)
            _workers.discard(owner)


def resume_sync_jobs():
    global _stopping
    _stopping = False


async def stop_sync_jobs():
    global _stopping
    _stopping = True
    tasks = [task for task in _workers | _kicks if task is not asyncio.current_task() and not task.done()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.wait(tasks, timeout=5)


def _read_job(job_id):
    with SessionLocal() as db:
        return job_payload(db.query(UserSyncJob).filter_by(id=job_id).first())


async def legacy_sync(user_id, background_tasks, db, actor):
    """Preserve 1.0.0's synchronous response using the same durable job queue."""
    result = enqueue_sync(user_id, background_tasks, db, actor)
    job_id = result["job"]["id"]
    db.rollback()  # Do not hold the HTTP request's connection while waiting.
    task = asyncio.create_task(process_sync_jobs())
    _kicks.add(task)
    task.add_done_callback(_kicks.discard)
    deadline = asyncio.get_running_loop().time() + 180
    while asyncio.get_running_loop().time() < deadline:
        job = await asyncio.to_thread(_read_job, job_id)
        if job is None:
            raise HTTPException(409, "This account or Sync job changed. Please sign in again.")
        if job["state"] == "succeeded":
            return {"status": "synced", "user_id": user_id,
                    "new_solves": job["new_solves"], "message": job["message"]}
        if job["state"] == "failed":
            raise HTTPException(503, job["message"], headers={"Retry-After": "60"})
        await asyncio.sleep(1)
    raise HTTPException(503, "Sync is still running on the server. Reopen the extension later; your credited points are safe.",
                        headers={"Retry-After": "30"})
