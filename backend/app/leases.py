import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import JobLease

logger = logging.getLogger("codestreak.leases")

_local_user_locks = {}
_provider_locks = {}


def generate_owner_id() -> str:
    """Generate a unique owner identifier for the current process and task."""
    return f"{os.getpid()}_{uuid.uuid4().hex[:12]}"


def _get_local_user_lock(user_id: int) -> asyncio.Lock:
    return _local_user_locks.setdefault(user_id, asyncio.Lock())


def acquire_lease(
    resource_key: str,
    ttl_seconds: float = 60.0,
    owner_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> Optional[str]:
    """
    Atomically acquire a lease for `resource_key` across processes.
    Returns `owner_id` on success, or `None` if lease is currently held by another owner.
    Does not hold open database connections or long-lived locks across network requests.
    """
    if not owner_id:
        owner_id = generate_owner_id()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = now + timedelta(seconds=ttl_seconds)

    owns_session = db is None
    session = db if db is not None else SessionLocal()

    try:
        query = session.query(JobLease).filter(JobLease.resource_key == resource_key)
        # Use row-level lock on dialects that support it (e.g. PostgreSQL)
        if session.bind and session.bind.dialect.name == "postgresql":
            query = query.with_for_update()

        lease = query.first()

        if lease is not None:
            if lease.expires_at > now and lease.owner_id != owner_id:
                # Active lease held by someone else
                return None
            # Expired lease (recoverable from crashed worker) or re-entrant acquisition
            lease.owner_id = owner_id
            lease.acquired_at = now
            lease.expires_at = expires
        else:
            session.add(
                JobLease(
                    resource_key=resource_key,
                    owner_id=owner_id,
                    acquired_at=now,
                    expires_at=expires,
                )
            )

        session.commit()
        return owner_id
    except Exception as e:
        session.rollback()
        logger.warning("Failed to acquire lease for %s: %s", resource_key, e)
        return None
    finally:
        if owns_session:
            session.close()


def release_lease(
    resource_key: str,
    owner_id: str,
    db: Optional[Session] = None,
) -> bool:
    """
    Atomically release a lease if owned by `owner_id`.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()

    try:
        deleted = (
            session.query(JobLease)
            .filter(
                JobLease.resource_key == resource_key,
                JobLease.owner_id == owner_id,
            )
            .delete()
        )
        session.commit()
        return deleted > 0
    except Exception as e:
        session.rollback()
        logger.warning("Failed to release lease for %s: %s", resource_key, e)
        return False
    finally:
        if owns_session:
            session.close()


def renew_lease(
    resource_key: str,
    owner_id: str,
    extension_seconds: float = 60.0,
    db: Optional[Session] = None,
) -> bool:
    """
    Extend expiry of an active lease if owned by `owner_id`.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires = now + timedelta(seconds=extension_seconds)

    try:
        lease = (
            session.query(JobLease)
            .filter(
                JobLease.resource_key == resource_key,
                JobLease.owner_id == owner_id,
            )
            .first()
        )
        if not lease or lease.expires_at <= now:
            return False
        lease.expires_at = expires
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.warning("Failed to renew lease for %s: %s", resource_key, e)
        return False
    finally:
        if owns_session:
            session.close()


def is_lease_active(
    resource_key: str,
    db: Optional[Session] = None,
) -> bool:
    """
    Check if a lease is currently active without modifying it.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        lease = (
            session.query(JobLease)
            .filter(
                JobLease.resource_key == resource_key,
                JobLease.expires_at > now,
            )
            .first()
        )
        return lease is not None
    finally:
        if owns_session:
            session.close()


@asynccontextmanager
async def user_sync_lease(user_id: int, ttl_seconds: float = 120.0, wait_timeout: float = 0.0):
    """
    Coordinated context manager for syncing a user account.
    Prevents overlapping sync jobs across both local asyncio tasks and multi-worker processes.
    If already locked and wait_timeout <= 0, yields None immediately.
    If wait_timeout > 0, waits up to wait_timeout seconds for lease availability.
    """
    key = f"sync:user:{user_id}"
    owner_id = generate_owner_id()
    local_lock = _get_local_user_lock(user_id)
    acquired_local = False
    acquired_db = False
    start_time = time.monotonic()

    try:
        if wait_timeout > 0:
            try:
                await asyncio.wait_for(local_lock.acquire(), timeout=wait_timeout)
                acquired_local = True
            except asyncio.TimeoutError:
                yield None
                return
        else:
            if local_lock.locked():
                yield None
                return
            await local_lock.acquire()
            acquired_local = True

        remaining_wait = wait_timeout - (time.monotonic() - start_time) if wait_timeout > 0 else 0.0
        while True:
            res = acquire_lease(key, ttl_seconds=ttl_seconds, owner_id=owner_id)
            if res:
                acquired_db = True
                break
            if remaining_wait <= 0 or (time.monotonic() - start_time) >= wait_timeout:
                break
            await asyncio.sleep(0.15)

        if not acquired_db:
            yield None
        else:
            yield owner_id
    finally:
        if acquired_db:
            release_lease(key, owner_id)
        if acquired_local:
            local_lock.release()


async def acquire_provider_rate_limit(
    provider: str = "codeforces",
    min_interval: float = 2.0,
    max_wait: float = 30.0,
):
    """
    Coordinates external provider rate limits across processes.
    Ensures that calls to `provider` are spaced by at least `min_interval` seconds deployment-wide.
    """
    key = f"provider:{provider}:rate_limit"
    owner_id = generate_owner_id()
    start = time.monotonic()

    local_lock = _provider_locks.setdefault(provider, asyncio.Lock())
    async with local_lock:
        while True:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            session = SessionLocal()
            try:
                query = session.query(JobLease).filter(JobLease.resource_key == key)
                if session.bind and session.bind.dialect.name == "postgresql":
                    query = query.with_for_update()

                lease = query.first()
                if lease is None or lease.expires_at <= now:
                    expires = now + timedelta(seconds=min_interval)
                    if lease is None:
                        session.add(
                            JobLease(
                                resource_key=key,
                                owner_id=owner_id,
                                acquired_at=now,
                                expires_at=expires,
                            )
                        )
                    else:
                        lease.owner_id = owner_id
                        lease.acquired_at = now
                        lease.expires_at = expires
                    session.commit()
                    return
                wait_seconds = (lease.expires_at - now).total_seconds()
            except Exception as e:
                session.rollback()
                logger.warning("Error in provider rate limiter for %s: %s", provider, e)
                wait_seconds = min_interval
            finally:
                session.close()

            if time.monotonic() - start + wait_seconds > max_wait:
                raise TimeoutError(f"Timed out waiting for {provider} rate limit slot")

            sleep_duration = max(0.1, min(wait_seconds, min_interval))
            await asyncio.sleep(sleep_duration)
