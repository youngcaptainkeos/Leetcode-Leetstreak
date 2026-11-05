import os
import tempfile
import asyncio
import time
import unittest
from datetime import datetime, timedelta, timezone

import test_access as fixtures

from fastapi.testclient import TestClient
from app.database import Base, SessionLocal, engine
from app.leases import (
    acquire_lease,
    release_lease,
    renew_lease,
    is_lease_active,
    user_sync_lease,
    acquire_provider_rate_limit,
)
from app.main import app
from app.migrations import run_all_migrations
from app.models import User, JobLease
from app.scheduler import poll_all_users


class JobLeaseCoordinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_all_migrations(engine)

    def setUp(self):
        self.db = SessionLocal()
        # Clean leases between tests
        self.db.query(JobLease).delete()
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            self.db.add(User(id=1, name="Demo 1", email="demo1@example.com", leetcode_username="demo_1"))
        self.db.commit()

    def tearDown(self):
        self.db.query(JobLease).delete()
        self.db.commit()
        self.db.close()

    def test_acquire_and_release_lease(self):
        key = "test:resource:1"
        owner_a = "worker_a_123"
        owner_b = "worker_b_456"

        # Worker A acquires lease
        acquired = acquire_lease(key, ttl_seconds=60.0, owner_id=owner_a)
        self.assertEqual(acquired, owner_a)
        self.assertTrue(is_lease_active(key))

        # Worker B attempts to acquire same active lease -> must fail
        acquired_b = acquire_lease(key, ttl_seconds=60.0, owner_id=owner_b)
        self.assertIsNone(acquired_b)

        # Worker A can re-acquire / renew its own lease
        renewed = acquire_lease(key, ttl_seconds=60.0, owner_id=owner_a)
        self.assertEqual(renewed, owner_a)

        # Worker A releases lease
        released = release_lease(key, owner_a)
        self.assertTrue(released)
        self.assertFalse(is_lease_active(key))

        # Worker B can now acquire it
        acquired_b = acquire_lease(key, ttl_seconds=60.0, owner_id=owner_b)
        self.assertEqual(acquired_b, owner_b)
        self.assertTrue(is_lease_active(key))

    def test_lease_expiry_and_dead_worker_recovery(self):
        key = "test:resource:crashed_worker"
        dead_owner = "crashed_worker_dead"
        new_owner = "live_worker_recovery"

        # Dead worker acquired lease that expired
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expired_at = now - timedelta(seconds=10)
        self.db.add(JobLease(resource_key=key, owner_id=dead_owner, acquired_at=now - timedelta(seconds=30), expires_at=expired_at))
        self.db.commit()

        self.assertFalse(is_lease_active(key))

        # Live worker must be able to claim expired lease atomically
        recovered = acquire_lease(key, ttl_seconds=60.0, owner_id=new_owner)
        self.assertEqual(recovered, new_owner)
        self.assertTrue(is_lease_active(key))

    def test_renew_lease(self):
        key = "test:resource:renew"
        owner = "worker_renew"

        self.assertFalse(renew_lease(key, owner, extension_seconds=120.0))

        acquire_lease(key, ttl_seconds=30.0, owner_id=owner)
        self.assertTrue(renew_lease(key, owner, extension_seconds=120.0))

        # Wrong owner cannot renew
        self.assertFalse(renew_lease(key, "wrong_owner", extension_seconds=120.0))

    def test_async_user_sync_lease_exclusivity(self):
        async def run_test():
            user_id = 42

            async with user_sync_lease(user_id, ttl_seconds=60.0, wait_timeout=0.0) as lease_1:
                self.assertIsNotNone(lease_1)
                self.assertTrue(is_lease_active(f"sync:user:{user_id}"))

                # Concurrent acquisition for same user without wait must fail immediately
                async with user_sync_lease(user_id, ttl_seconds=60.0, wait_timeout=0.0) as lease_2:
                    self.assertIsNone(lease_2)

            # After exiting block, lease is released
            self.assertFalse(is_lease_active(f"sync:user:{user_id}"))

        asyncio.run(run_test())

    def test_scheduler_job_coordination_skips_when_active(self):
        async def run_test():
            lease_key = "scheduler:job:poll_all_users"
            # Simulate another process already running poll_all_users
            other_owner = acquire_lease(lease_key, ttl_seconds=120.0, owner_id="remote_worker_1")
            self.assertIsNotNone(other_owner)

            # Running poll_all_users must skip and return empty dict without crashing
            res = await poll_all_users()
            self.assertEqual(res, {})

            release_lease(lease_key, other_owner)

        asyncio.run(run_test())

    def test_provider_rate_limit_spacing(self):
        async def run_test():
            start = time.monotonic()
            await acquire_provider_rate_limit("test_provider", min_interval=0.3)
            # Second call must wait for interval
            await acquire_provider_rate_limit("test_provider", min_interval=0.3)
            elapsed = time.monotonic() - start
            self.assertGreaterEqual(elapsed, 0.25)

        asyncio.run(run_test())

    def test_sync_endpoint_returns_409_when_sync_in_progress(self):
        client = TestClient(app)
        user = self.db.query(User).filter(User.id == 1).first()
        token = fixtures.create_access_token(user.id, user.session_version)
        headers = {"Authorization": f"Bearer {token}"}

        # Acquire sync lease for user 1 simulating background poll or another worker
        lease_key = f"sync:user:{user.id}"
        owner = acquire_lease(lease_key, ttl_seconds=60.0, owner_id="external_sync_job")
        self.assertIsNotNone(owner)

        try:
            # Calling sync route during active sync must return 409 Conflict
            res = client.post(f"/api/users/{user.id}/sync", headers=headers)
            self.assertEqual(res.status_code, 409)
            self.assertIn("already in progress", res.json()["detail"])
        finally:
            release_lease(lease_key, owner)
