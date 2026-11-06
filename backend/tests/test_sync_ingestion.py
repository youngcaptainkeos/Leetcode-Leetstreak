"""Exercise the production sync functions with mocked provider responses."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy.orm import Session
import test_ingestion as ingestion_fixtures
import test_access as access_fixtures
from app import scheduler, codeforces_sync
from app.codeforces_client import CodeforcesError
from app.models import AcceptedSubmission, ScoreSnapshot, Solve, User, PointAward
from app.timekeeping import utc_now


def timestamp(day):
    return int(datetime(2026, 1, day, tzinfo=timezone.utc).timestamp())


def cf_history(slug="cf-100-a"):
    return [{"slug": slug, "title": "Synthetic problem", "url": "https://codeforces.com/contest/100/problem/A",
             "rating": 1200, "timestamp": timestamp(1), "submission_id": 100,
             "accepted_submissions": [{"submission_id": 100, "timestamp": timestamp(1)},
                                      {"submission_id": 101, "timestamp": timestamp(8)}]}]


def lc_profile(**changes):
    return {"username": "demo_lc", "difficulty_counts": {"Easy": 1}, "official_streak": 0,
            "submission_calendar": {}, "recent_submissions_available": True,
            "recent_submissions": [{"id": "100", "timestamp": str(timestamp(1)), "titleSlug": "synthetic-question", "title": "Synthetic question"},
                                   {"id": "101", "timestamp": str(timestamp(8)), "titleSlug": "synthetic-question", "title": "Synthetic question"}], **changes}


class SyncIngestionTests(unittest.IsolatedAsyncioTestCase):
    setUp = ingestion_fixtures.IngestionTests.setUp
    tearDown = ingestion_fixtures.IngestionTests.tearDown

    async def test_codeforces_full_then_incremental_sync_keeps_repeats_and_is_idempotent(self):
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history())), patch.object(codeforces_sync, "recalculate_user_points"):
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 0)
            self.user.codeforces_last_sync = utc_now() - timedelta(minutes=11)
            self.db.commit()
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 0)
        self.assertEqual(self.db.query(Solve).count(), 1)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 2)
        self.assertEqual(self.db.query(PointAward).count(), 0)
        self.db.refresh(self.solve)
        self.assertEqual(self.solve.first_solve_at, datetime(2026, 1, 1))
        self.assertTrue(self.solve.first_solve_verified)
        self.assertEqual(self.db.query(ScoreSnapshot).one().payload["points"], 42.5)

    async def test_incrementally_discovered_problem_does_not_get_a_proved_first_solve_date(self):
        self.user.codeforces_last_sync = utc_now() - timedelta(minutes=11)
        self.user.codeforces_last_full_sync = utc_now()
        self.db.commit()
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history("cf-100-b"))), patch.object(codeforces_sync, "recalculate_user_points"):
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 1)
        new = self.db.query(Solve).filter_by(title_slug="cf-100-b").one()
        self.assertIsNone(new.first_solve_at)
        self.assertFalse(new.first_solve_verified)

    async def test_codeforces_stale_same_handle_generation_discards_success_and_error(self):
        async def replace_then_return(*args):
            with Session(self.engine) as other:
                other.query(User).filter_by(id=1).update({User.codeforces_account_version: User.codeforces_account_version + 1})
                other.commit()
            return cf_history()

        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(side_effect=replace_then_return)), patch.object(codeforces_sync, "recalculate_user_points") as score:
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 0)
            score.assert_not_called()
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 0)

        async def replace_then_error(*args):
            await replace_then_return()
            raise CodeforcesError("synthetic provider error")

        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(side_effect=replace_then_error)):
            self.assertEqual(await codeforces_sync.sync_codeforces_user(self.db, self.user), 0)
        self.db.refresh(self.user)
        self.assertIsNone(self.user.codeforces_sync_error)

        self.assertIsNone(self.user.codeforces_last_sync)

    async def test_rejudgement_preserves_raw_acceptance_evidence(self):
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=cf_history())), patch.object(codeforces_sync, "recalculate_user_points"):
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.user.codeforces_last_sync = utc_now() - timedelta(minutes=11)
        self.user.codeforces_last_full_sync = None
        self.db.commit()
        with patch.object(codeforces_sync, "fetch_accepted_history", new=AsyncMock(return_value=[])), patch.object(codeforces_sync, "recalculate_user_points"):
            await codeforces_sync.sync_codeforces_user(self.db, self.user)
        self.assertEqual(self.db.query(Solve).count(), 0)
        events = self.db.query(AcceptedSubmission).all()
        self.assertEqual(len(events), 2)
        self.assertTrue(all(row.solve_id is None and not row.first_solve_verified for row in events))

    async def test_leetcode_sync_stores_both_acceptances_and_one_unproved_question(self):
        with patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(return_value=lc_profile())), patch.object(scheduler, "fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50})), patch.object(scheduler, "fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), patch.object(scheduler, "recalculate_user_points"):
            self.assertEqual(await scheduler.poll_user(self.db, self.user, sync_codeforces=False), 1)
            self.assertEqual(await scheduler.poll_user(self.db, self.user, sync_codeforces=False), 0)
        solve = self.db.query(Solve).filter_by(platform="leetcode").one()
        self.assertFalse(solve.first_solve_verified)
        self.assertIsNone(solve.first_solve_at)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 2)
        self.assertIsNotNone(self.user.leetcode_last_sync)

    async def test_leetcode_partial_or_invalid_batch_does_not_advance_sync(self):
        for data in [lc_profile(recent_submissions_available=False), lc_profile(recent_submissions=[{"id": True}]), lc_profile(username="someone_else"), lc_profile(username=None)]:
            with self.subTest(data=data), patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(return_value=data)), patch.object(scheduler, "fetch_problem_info", new=AsyncMock()) as metadata:
                self.assertEqual(await scheduler.poll_user(self.db, self.user, sync_codeforces=False), 0)
                metadata.assert_not_awaited()
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 0)
        self.assertEqual(self.db.query(ScoreSnapshot).count(), 0)
        self.assertIsNone(self.user.leetcode_last_sync)

    async def test_leetcode_generation_change_during_metadata_fetch_discards_batch(self):
        async def replace_during_metadata(*args):
            with Session(self.engine) as other:
                other.query(User).filter_by(id=1).update({User.leetcode_account_version: 1})
                other.commit()
            return {"difficulty": "Easy", "ac_rate": 50}

        with patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(return_value=lc_profile())), patch.object(scheduler, "fetch_problem_info", new=AsyncMock(side_effect=replace_during_metadata)), patch.object(scheduler, "fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), patch.object(scheduler, "recalculate_user_points") as score:
            self.assertEqual(await scheduler.poll_user(self.db, self.user, sync_codeforces=False), 0)
            score.assert_not_called()
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 0)
        self.assertEqual(self.db.query(Solve).filter_by(platform="leetcode").count(), 0)

    async def test_later_sync_winning_during_request_cannot_be_overwritten(self):
        newer = utc_now()

        async def newer_sync(*args):
            with Session(self.engine) as other:
                other.query(User).filter_by(id=1).update({User.leetcode_last_sync: newer})
                other.commit()
            return lc_profile()

        with patch.object(scheduler, "fetch_leetcode_user_data", new=AsyncMock(side_effect=newer_sync)), patch.object(scheduler, "fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy"})), patch.object(scheduler, "fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)):
            self.assertEqual(await scheduler.poll_user(self.db, self.user, sync_codeforces=False), 0)
        self.db.refresh(self.user)
        self.assertEqual(self.user.leetcode_last_sync, newer)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 0)

    async def test_background_failure_does_not_mark_a_replaced_account_as_failed(self):
        background_db = Session(self.engine)

        async def replaced_then_failed(*args):
            with Session(self.engine) as other:
                other.query(User).filter_by(id=1).update({User.codeforces_account_version: 1})
                other.commit()
            raise RuntimeError("synthetic failed old-account job")

        with patch("app.database.SessionLocal", return_value=background_db), patch.object(codeforces_sync, "sync_codeforces_user", new=AsyncMock(side_effect=replaced_then_failed)):
            await codeforces_sync.background_codeforces_sync(1)
        self.db.expire_all()
        self.assertEqual(self.user.codeforces_account_version, 1)
        self.assertIsNone(self.user.codeforces_sync_error)

class HandleGenerationTests(unittest.TestCase):
    setUp = access_fixtures.AccessTests.setUp
    tearDown = access_fixtures.AccessTests.tearDown
    headers = access_fixtures.AccessTests.headers

    def test_leetcode_replacement_advances_generation_but_case_change_does_not(self):
        with patch("app.main.fetch_leetcode_user_data", new=AsyncMock(return_value={"username": "another_demo"})), patch("app.main.poll_user", new=AsyncMock(return_value=0)):
            response = self.client.put("/api/users/2/leetcode-username", headers=self.headers(2), json={"leetcode_username": "another_demo"})
            self.assertEqual(response.status_code, 200)
            self.db.expire_all()
            self.assertEqual(self.db.get(User, 2).leetcode_account_version, 1)
            response = self.client.put("/api/users/2/leetcode-username", headers=self.headers(2), json={"leetcode_username": "Another_Demo"})
            self.assertEqual(response.status_code, 200)
            self.db.expire_all()
            self.assertEqual(self.db.get(User, 2).leetcode_account_version, 1)

    def test_codeforces_replacement_advances_generation_but_case_change_does_not(self):
        with patch("app.main.fetch_profile", new=AsyncMock(return_value={"handle": "demo_cf"})), patch("app.main.background_codeforces_sync", new=AsyncMock()), patch("app.main.recalculate_user_points"):
            response = self.client.put("/api/users/2/codeforces-username", headers=self.headers(2), json={"codeforces_username": "demo_cf"})
            self.assertEqual(response.status_code, 200)
            self.db.expire_all()
            self.assertEqual(self.db.get(User, 2).codeforces_account_version, 1)
            response = self.client.put("/api/users/2/codeforces-username", headers=self.headers(2), json={"codeforces_username": "Demo_Cf"})
            self.assertEqual(response.status_code, 200)
            self.db.expire_all()
            self.assertEqual(self.db.get(User, 2).codeforces_account_version, 1)

