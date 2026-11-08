"""Database ownership checks for a durable manual sync attempt."""
from dataclasses import dataclass
from datetime import timedelta

from .models import UserSyncJob
from .timekeeping import utc_now

LEASE_SECONDS = 45


class SyncOwnershipLost(Exception):
    """This attempt no longer owns the job/account and must not write."""


@dataclass(frozen=True)
class SyncAttempt:
    job_id: str
    token: str


def lock_attempt(db, user, attempt):
    """Call after locking User; hold both locks through the provider commit.

    Recovery skips locked job rows. Thus a live database transaction cannot be
    reclaimed underneath a writer, even if its heartbeat is briefly delayed.
    """
    if attempt is None:
        return None
    job = db.query(UserSyncJob).filter_by(id=attempt.job_id).populate_existing().with_for_update().first()
    if (job is None or job.state != "running" or job.worker_token != attempt.token
            or job.user_id != user.id
            or (job.leetcode_account_version, job.codeforces_account_version, job.session_version)
            != (user.leetcode_account_version, user.codeforces_account_version, user.session_version)):
        raise SyncOwnershipLost()
    return job


def checkpoint(job, added=0):
    if job is not None:
        job.new_solves = (job.new_solves or 0) + added
        job.lease_until = utc_now() + timedelta(seconds=LEASE_SECONDS)
