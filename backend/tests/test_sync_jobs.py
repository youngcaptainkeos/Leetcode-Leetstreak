"""Durable job recovery in temporary databases; no production writes."""
import asyncio
from datetime import timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from sqlalchemy.orm import Session
import test_ingestion as fixtures
from test_sync_ingestion import lc_profile
from app import scheduler, sync_jobs
from app.models import UserSyncJob, Solve
from app.sync_context import SyncAttempt, SyncOwnershipLost
from app.timekeeping import utc_now


class SyncJobTests(IsolatedAsyncioTestCase):
    def setUp(self):
        fixtures.IngestionTests.setUp(self)
        self.sessions = patch.object(sync_jobs, "SessionLocal", lambda: Session(self.engine))
        self.sessions.start()
        sync_jobs.resume_sync_jobs()
        self.db.add(UserSyncJob(id="synthetic-job", user_id=1, state="queued",
            leetcode_account_version=0, codeforces_account_version=0, session_version=0))
        self.db.commit()

    def tearDown(self):
        self.sessions.stop()
        fixtures.IngestionTests.tearDown(self)

    def claim(self):
        job_id, user_id, token = sync_jobs._claim_job()
        return SyncAttempt(job_id, token)

    def read(self):
        self.db.expire_all()
        return self.db.query(UserSyncJob).one()

    def expire(self):
        job = self.read()
        job.lease_until = utc_now() - timedelta(seconds=1)
        self.db.commit()

    async def test_expired_attempt_is_reclaimed_with_a_different_owner(self):
        old = self.claim()
        self.expire()
        new = self.claim()
        self.assertNotEqual(old.token, new.token)
        self.assertEqual(self.read().attempts, 2)
        self.assertFalse(sync_jobs._renew_job(old))
        self.assertTrue(sync_jobs._renew_job(new))
        sync_jobs._finish_job(old, 1, added=99)
        self.assertEqual(self.read().state, "running")
        self.assertEqual(self.read().new_solves, 0)

    async def test_superseded_writer_cannot_save_questions_or_scores(self):
        old = self.claim()
        self.expire()
        self.claim()
        with patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(return_value=lc_profile())), \
                patch.object(scheduler, "fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50})):
            with self.assertRaises(SyncOwnershipLost):
                await scheduler._poll_leetcode_user(self.db, self.user, attempt=old)
        self.db.expire_all()
        self.assertEqual(self.db.query(Solve).filter_by(platform="leetcode").count(), 0)
        self.assertEqual(self.user.points, 42.5)

    async def test_committed_progress_survives_restart_without_duplicate_credit(self):
        first = self.claim()
        with patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(return_value=lc_profile())), \
                patch.object(scheduler, "fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50})):
            self.assertEqual(await scheduler._poll_leetcode_user(self.db, self.user, attempt=first), 1)
            self.db.refresh(self.user)
            points = self.user.points
            self.assertEqual(self.read().new_solves, 1)
            sync_jobs._release_job(first)
            second = self.claim()
            self.assertEqual(await scheduler._poll_leetcode_user(self.db, self.user, attempt=second), 0)
            self.db.refresh(self.user)
            self.assertEqual(self.user.points, points)
        sync_jobs._finish_job(second, 1, added=0)
        self.assertEqual(self.read().new_solves, 1)
        self.assertEqual(self.read().state, "succeeded")

    async def test_soft_timeout_waits_for_actual_completion(self):
        async def work(*args):
            await asyncio.sleep(0.04)
            return 2
        with patch.object(sync_jobs, "SOFT_TIMEOUT", 0.01), \
                patch.object(sync_jobs, "_perform_job", new=AsyncMock(side_effect=work)):
            await sync_jobs.process_sync_jobs()
        self.assertEqual(self.read().state, "succeeded")
        self.assertEqual(self.read().new_solves, 2)

    async def test_cancelled_worker_requeues_its_attempt(self):
        started = asyncio.Event()

        async def work(*args):
            started.set()
            await asyncio.Event().wait()

        with patch.object(sync_jobs, "_perform_job", new=AsyncMock(side_effect=work)):
            task = asyncio.create_task(sync_jobs.process_sync_jobs())
            await asyncio.wait_for(started.wait(), timeout=5)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual(self.read().state, "queued")
        self.assertIsNone(self.read().worker_token)

    async def test_interruption_retries_are_bounded(self):
        for _ in range(sync_jobs.MAX_ATTEMPTS):
            self.claim()
            self.expire()
        self.assertIsNone(sync_jobs._claim_job())
        self.assertEqual(self.read().state, "failed")
