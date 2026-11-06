"""Production sync/read paths against synthetic provider responses."""
import unittest
from datetime import datetime, timezone, date
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import test_ingestion as fixtures
from test_sync_ingestion import cf_history, lc_profile
from app import codeforces_sync, main, scheduler
from app.auth import create_access_token
from app.database import get_db
from app.models import AcceptedSubmission, DailyActivity, PointAward, ProviderCalendar, Solve, User
from app.platforms import daily_counts
from app.reconciliation import reconcile_user


class RuntimeScoringTests(unittest.IsolatedAsyncioTestCase):
    setUp = fixtures.IngestionTests.setUp
    tearDown = fixtures.IngestionTests.tearDown

    async def test_real_codeforces_sync_awards_live_revisions_once(self):
        history = cf_history()
        history[0]["accepted_submissions"] = history[0]["accepted_submissions"][:1]
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=history)), patch.object(codeforces_sync, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 1, 2, tzinfo=timezone.utc)
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").count(), 0)
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history())), patch.object(codeforces_sync, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 1, 9, tzinfo=timezone.utc)
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.assertEqual(self.user.points, 14.8427)
        for minute in (0, 11):
            history = cf_history()
            history[0]["accepted_submissions"].append({"submission_id": 102, "timestamp": int(datetime(2026, 1, 15, tzinfo=timezone.utc).timestamp())})
            with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=history)), patch.object(codeforces_sync, "datetime", wraps=datetime) as clock:
                clock.now.return_value = datetime(2026, 1, 16, 0, minute, tzinfo=timezone.utc)
                await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.assertEqual(self.user.points, 16.8427)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").count(), 2)
        self.assertEqual(self.db.query(Solve).count(), 1)
        self.assertEqual(dict(daily_counts(self.db, [1])[1]), {date(2026, 1, 1): 1})

    async def test_calendar_and_recent_repeats_do_not_become_verified_solve_days(self):
        data = lc_profile(submission_calendar={date(2026, 1, 8): 123})
        with patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(return_value=data)), patch.object(scheduler, "fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50})):
            await scheduler.poll_user(self.db, self.user, sync_codeforces=False)
        self.assertEqual(dict(daily_counts(self.db, [1])[1]), {})
        self.assertEqual(self.db.query(DailyActivity).count(), 0)
        calendar = self.db.query(ProviderCalendar).one()
        self.assertEqual(calendar.submission_count, 123)
        self.assertEqual(calendar.coverage, "provider_partial")
        self.assertEqual(self.db.query(PointAward).filter_by(kind="daily").count(), 0)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 2)

    async def test_read_api_does_not_fetch_providers_or_change_history(self):
        row = Solve(user_id=1, platform="leetcode", title_slug="synthetic-unknown", source_handle="demo_lc",
                    solved_at=datetime(2026, 1, 1), points_earned=17.1234)
        self.db.add(row)
        self.db.commit()
        headers = {"Authorization": "Bearer " + create_access_token(1)}
        with patch.dict(main.app.dependency_overrides, {get_db: lambda: self.db}), patch.object(main, "fetch_problem_info", new=AsyncMock()) as metadata, patch.object(main, "poll_user", new=AsyncMock()) as poll, patch.object(main, "fetch_today_daily_challenge_slug", new=AsyncMock()) as daily:
            client = TestClient(main.app)
            try:
                response = client.get("/api/users/1/recent-solves", headers=headers)
                self.assertEqual(response.status_code, 200)
                result = next(value for value in response.json() if value["platform"] == "leetcode")
                self.assertEqual(result["points_earned"], 17.1234)
                self.assertEqual(result["breakdown"]["legacy_credit"], 17.1234)
                self.assertEqual(result["breakdown"]["points_earned"], 17.1234)
                self.assertFalse(result["first_solve_verified"])
                self.assertEqual(result["breakdown"]["score_state"], "unreconciled")
                metadata.assert_not_awaited(); poll.assert_not_awaited(); daily.assert_not_awaited()
            finally:
                client.close()
        self.db.refresh(row)
        self.assertIsNone(row.difficulty)
        self.assertFalse(row.is_daily)
        self.assertEqual(row.points_earned, 17.1234)
        self.assertEqual(self.db.query(PointAward).count(), 0)

    async def test_dashboard_and_breakdown_report_the_same_credited_points(self):
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history())):
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        with patch.dict(main.app.dependency_overrides, {get_db: lambda: self.db}):
            client = TestClient(main.app)
            try:
                headers = {"Authorization": "Bearer " + create_access_token(1)}
                dash = client.get("/api/users/1/dashboard", headers=headers).json()
                recent = client.get("/api/users/1/recent-solves", headers=headers).json()[0]
                self.assertEqual(dash["points"], recent["points_earned"])
                self.assertEqual(recent["points_earned"], recent["breakdown"]["points_earned"])
                self.assertEqual(dash["codeforces_points"] + dash["leetcode_points"], dash["points"])
                self.assertTrue(dash["history_incomplete"])
            finally:
                client.close()

    async def test_rankings_keep_fractional_credit_when_sorting(self):
        self.user.points = 8.0034
        self.db.add(User(id=2, name="Another Demo", email="another@example.com", leetcode_username="another_demo", points=8.0044))
        self.db.commit()
        result = main._compute_leaderboard(self.db, self.db.query(User).all())
        self.assertEqual([entry.id for entry in result.entries], [2, 1])
        self.assertEqual([entry.points for entry in result.entries], [8.0044, 8.0034])

    async def test_leetcode_replacement_recalculates_only_that_platform(self):
        self.solve.problem_rating = 800
        self.user.easy_count = 1
        self.db.add(Solve(user_id=1, platform="leetcode", source_handle="demo_lc", title_slug="old-daily",
            solved_at=datetime(2026, 1, 1), is_daily=True, points_earned=17.5, difficulty="Easy"))
        self.db.add(PointAward(award_key="synthetic-cf-revision", user_id=1, solve_id=self.solve.id,
            kind="revision", points=2, earned_at=datetime(2026, 1, 8), scoring_version="synthetic-v1"))
        reconcile_user(self.user, self.db)
        self.db.commit()
        self.assertEqual(self.user.points, 27.5)
        profile = {"username": "another_demo", "difficulty_counts": {"Easy": 2}}
        with patch.dict(main.app.dependency_overrides, {get_db: lambda: self.db}), patch.object(main, "fetch_leetcode_user_data", new=AsyncMock(return_value=profile)), patch.object(main, "poll_user", new=AsyncMock(return_value=0)):
            client = TestClient(main.app)
            try:
                response = client.put("/api/users/1/leetcode-username", headers={"Authorization": "Bearer " + create_access_token(1)}, json={"leetcode_username": "another_demo"})
                self.assertEqual(response.status_code, 200, response.text)
            finally:
                client.close()
        self.db.refresh(self.user)
        self.assertEqual(self.user.leetcode_account_version, 1)
        self.assertEqual(self.user.points, 26)  # 16 new LC base estimate, plus unchanged 10 CF credit.
        self.assertEqual(self.db.query(Solve).filter_by(platform="leetcode").count(), 0)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").one().points, 2)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="legacy").count(), 0)

    async def test_case_only_leetcode_change_retains_protected_history(self):
        self.db.add(Solve(user_id=1, platform="leetcode", source_handle="demo_lc", title_slug="old-daily",
            solved_at=datetime(2026, 1, 1), is_daily=True, points_earned=17.5, difficulty="Easy"))
        reconcile_user(self.user, self.db)
        self.db.commit()
        before = self.user.points
        with patch.dict(main.app.dependency_overrides, {get_db: lambda: self.db}), patch.object(main, "fetch_leetcode_user_data", new=AsyncMock(return_value={"username": "demo_lc"})), patch.object(main, "poll_user", new=AsyncMock(return_value=0)):
            client = TestClient(main.app)
            try:
                response = client.put("/api/users/1/leetcode-username", headers={"Authorization": "Bearer " + create_access_token(1)}, json={"leetcode_username": "Demo_Lc"})
                self.assertEqual(response.status_code, 200, response.text)
            finally:
                client.close()
        self.db.refresh(self.user)
        self.assertEqual(self.user.leetcode_account_version, 0)
        self.assertEqual(self.user.points, before)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="legacy").one().points, 17.5)

    async def test_missing_credited_history_does_not_block_new_solves_and_can_recover(self):
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history())):
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.user.codeforces_last_sync = None
        self.user.codeforces_last_full_sync = None
        self.db.commit()
        missing_history = cf_history("cf-200-b")
        missing_history[0]["submission_id"] += 1000
        for event in missing_history[0]["accepted_submissions"]:
            event["submission_id"] += 1000
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=missing_history)):
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 1)
        old = self.db.query(Solve).filter_by(title_slug="cf-100-a").one()
        self.assertEqual(old.score_components_state, "history_review")
        self.assertFalse(old.first_solve_verified)
        self.assertIsNone(old.first_solve_at)
        self.assertGreater(old.points_earned, 0)
        self.assertEqual(sum(daily_counts(self.db, [1])[1].values()), 1)
        self.user.codeforces_last_sync = None
        self.user.codeforces_last_full_sync = None
        self.db.commit()
        history = cf_history() + cf_history("cf-200-b")
        history[1]["submission_id"] += 1000
        # Provider IDs are globally unique, even across different questions.
        for event in history[1]["accepted_submissions"]:
            event["submission_id"] += 1000
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=history)):
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.db.refresh(old)
        self.assertTrue(old.first_solve_verified)
        self.assertEqual(old.score_components_state, "verified")
