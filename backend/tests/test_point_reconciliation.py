"""Tests for bounded, resumable all-user point reconciliation."""
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

os.environ.setdefault("JWT_SECRET", "synthetic-unit-test-key-" + "x" * 40)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User, Solve, JobCheckpoint
from app.point_calculator import recalculate_all_users_points


class PointReconciliationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed 5 users with solves
        for i in range(1, 6):
            user = User(
                id=i,
                name=f"User {i}",
                leetcode_username=f"coder_{i}",
                email=f"coder_{i}@example.com",
                points=0.0,
                easy_count=1,
            )
            self.db.add(user)
            solve = Solve(
                user_id=i,
                title_slug=f"problem-{i}",
                difficulty="Easy",
                points_earned=0.0,
                solved_at=datetime(2026, 1, i, 10, 0, tzinfo=timezone.utc),
            )
            self.db.add(solve)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    @patch("app.leetcode_client.fetch_today_daily_challenge_slug", new_callable=AsyncMock)
    async def test_batch_reconciliation_checkpoints_progress(self, mock_slug):
        mock_slug.return_value = None

        # Reconcile 5 users in batches of 2 -> 3 batches (2, 2, 1)
        res = await recalculate_all_users_points(
            self.db, batch_size=2, job_name="test-rec-1"
        )
        self.assertEqual(res["total_processed"], 5)
        self.assertEqual(res["batches"], 3)
        self.assertEqual(res["status"], "completed")

        # Verify all users received points
        users = self.db.query(User).order_by(User.id).all()
        for u in users:
            self.assertGreater(u.points, 0.0)

        # Verify checkpoint state
        cp = self.db.query(JobCheckpoint).filter_by(job_name="test-rec-1").first()
        self.assertIsNotNone(cp)
        self.assertEqual(cp.status, "completed")
        self.assertEqual(cp.last_processed_id, 5)
        self.assertEqual(cp.total_processed, 5)

    @patch("app.leetcode_client.fetch_today_daily_challenge_slug", new_callable=AsyncMock)
    async def test_reconciliation_already_completed_guard(self, mock_slug):
        mock_slug.return_value = None

        # First run completes
        await recalculate_all_users_points(self.db, batch_size=5, job_name="test-rec-2")

        # Second run without force should immediately return already_completed
        res = await recalculate_all_users_points(self.db, batch_size=5, job_name="test-rec-2")
        self.assertEqual(res["status"], "already_completed")
        self.assertEqual(res["batches"], 0)

        # Run with force=True restarts
        res_force = await recalculate_all_users_points(self.db, batch_size=5, job_name="test-rec-2", force=True)
        self.assertEqual(res_force["status"], "completed")
        self.assertEqual(res_force["batches"], 1)

    @patch("app.leetcode_client.fetch_today_daily_challenge_slug", new_callable=AsyncMock)
    async def test_interrupted_job_resumes_without_recalculating_prior_batches(self, mock_slug):
        mock_slug.return_value = None

        # Simulate a checkpoint interrupted after user 2
        cp = JobCheckpoint(
            job_name="test-rec-resume",
            last_processed_id=2,
            total_processed=2,
            batch_size=2,
            status="running",
        )
        self.db.add(cp)
        self.db.commit()

        # Resume with batch_size=2
        # Users remaining: 3, 4, 5 -> 2 batches (users 3,4 and user 5)
        res = await recalculate_all_users_points(
            self.db, batch_size=2, job_name="test-rec-resume", resume=True
        )
        self.assertEqual(res["status"], "completed")
        self.assertEqual(res["batches"], 2)
        self.assertEqual(res["total_processed"], 5)

        # Verify checkpoint
        self.db.refresh(cp)
        self.assertEqual(cp.status, "completed")
        self.assertEqual(cp.last_processed_id, 5)
        self.assertEqual(cp.total_processed, 5)


if __name__ == "__main__":
    unittest.main()
