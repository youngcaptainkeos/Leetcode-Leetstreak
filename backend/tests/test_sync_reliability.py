"""Isolated sync regressions with synthetic accounts and mocked providers."""
import unittest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import test_ingestion as fixtures
from app import scheduler
from app.leetcode_client import LeetCodeError
from app.sync_report import SyncReport
from app import codeforces_sync
from app.codeforces_client import CodeforcesError
from app.models import Solve
from app.timekeeping import utc_now
from test_sync_ingestion import cf_history


class IndependentPlatformTests(unittest.IsolatedAsyncioTestCase):
    setUp = fixtures.IngestionTests.setUp
    tearDown = fixtures.IngestionTests.tearDown

    async def test_codeforces_runs_when_leetcode_fails(self):
        report = SyncReport()

        async def cf(*args, **kwargs):
            kwargs["report"].codeforces = "synced"
            return 3

        with patch.object(scheduler, "_poll_leetcode_user", new=AsyncMock(side_effect=LeetCodeError("unavailable"))), \
                patch.object(scheduler, "sync_codeforces_user", new=AsyncMock(side_effect=cf)) as sync:
            added = await scheduler.poll_user(self.db, self.user, raise_on_unavailable=True,
                force_codeforces=True, report=report)
        self.assertEqual(added, 3)
        self.assertTrue(sync.call_args.kwargs["force"])
        self.assertIn("Codeforces synced", report.message)
        self.assertIn("LeetCode is temporarily unavailable", report.message)

    async def test_leetcode_success_survives_codeforces_failure(self):
        report = SyncReport()
        with patch.object(scheduler, "_poll_leetcode_user", new=AsyncMock(return_value=2)), \
                patch.object(scheduler, "sync_codeforces_user", new=AsyncMock(side_effect=ValueError("invalid batch"))):
            self.assertEqual(await scheduler.poll_user(self.db, self.user,
                raise_on_unavailable=True, report=report), 2)
        self.assertIn("LeetCode synced", report.message)
        self.assertEqual(report.codeforces, "unavailable")

    async def test_both_fail_only_after_both_were_attempted(self):
        with patch.object(scheduler, "_poll_leetcode_user", new=AsyncMock(side_effect=LeetCodeError("unavailable"))), \
                patch.object(scheduler, "sync_codeforces_user", new=AsyncMock(side_effect=ValueError("invalid batch"))) as sync:
            with self.assertRaises(LeetCodeError):
                await scheduler.poll_user(self.db, self.user, raise_on_unavailable=True)
            sync.assert_awaited_once()


class CodeforcesProofTests(unittest.IsolatedAsyncioTestCase):
    setUp = fixtures.IngestionTests.setUp
    tearDown = fixtures.IngestionTests.tearDown

    async def test_unavailable_full_history_does_not_claim_recent_history_is_complete(self):
        before = utc_now() - timedelta(minutes=11)
        self.user.codeforces_last_sync = before
        self.user.codeforces_last_full_sync = utc_now()
        self.db.commit()
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(side_effect=[
                cf_history("cf-100-b"), CodeforcesError("full scan unavailable")])):
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 1)
        self.db.refresh(self.user)
        self.assertGreater(self.user.codeforces_last_sync, before)
        pending = self.db.query(Solve).filter_by(title_slug="cf-100-b").one()
        self.assertFalse(pending.first_solve_verified)
        self.assertIsNone(pending.first_solve_at)
        self.assertEqual(self.user.points, 55.3)
        self.assertIn("await full-history verification", self.user.codeforces_sync_error)

    async def test_manual_force_bypasses_recent_sync_skip(self):
        self.user.codeforces_last_sync = utc_now()
        self.db.commit()
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history())) as fetch, \
                patch.object(codeforces_sync, "recalculate_user_points"):
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
            fetch.assert_not_awaited()
            await codeforces_sync.sync_codeforces_user(self.db, self.user, force=True)
            fetch.assert_awaited_once()
        self.db.refresh(self.solve)
        self.assertTrue(self.solve.first_solve_verified)
