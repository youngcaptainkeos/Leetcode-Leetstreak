"""Isolated sync regressions with synthetic accounts and mocked providers."""
import unittest
from unittest.mock import AsyncMock, patch

import test_ingestion as fixtures
from app import scheduler
from app.leetcode_client import LeetCodeError
from app.sync_report import SyncReport


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
