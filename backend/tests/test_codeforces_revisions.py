"""Public provider fixtures for Codeforces repeat evidence and live revision awards."""
import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import test_access as fixtures
from app.models import User, Solve, PointAward, AcceptedSubmission
from app.codeforces_client import fetch_accepted_history
from app.codeforces_sync import sync_codeforces_user
from app.timekeeping import utc_now


class CodeforcesRevisionTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown

    def row(self, when, submission=100):
        return dict(slug="cf-1-a", title="Synthetic CF", url="https://codeforces.com/contest/1/problem/A",
                    rating=800, timestamp=int(when.replace(tzinfo=timezone.utc).timestamp()), submission_id=submission)

    def test_provider_preserves_all_acceptances_but_one_question(self):
        now = int(utc_now().replace(tzinfo=timezone.utc).timestamp())
        def submission(identifier, timestamp):
            return dict(id=identifier, verdict="OK", testset="TESTS", creationTimeSeconds=timestamp,
                        author={"members": [{"handle": "demo_cf"}]},
                        problem={"contestId": 1, "index": "A", "name": "Synthetic CF", "rating": 800})
        rows = [submission(2, now), submission(1, now - 864000), submission(2, now)]
        with patch("app.codeforces_client.codeforces_request", new=AsyncMock(return_value=rows)):
            history = asyncio.run(fetch_accepted_history("demo_cf"))
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["submission_id"], 1)
        self.assertEqual([e["submission_id"] for e in history[0]["accepted_submissions"]], [1, 2])

    def test_live_cf_repeat_earns_revision_without_moving_first_solve_and_replay_is_safe(self):
        now = utc_now()
        user = self.db.get(User, 1)
        user.codeforces_username = "demo_cf"
        user.codeforces_last_sync = now - timedelta(minutes=12)
        user.codeforces_last_full_sync = now - timedelta(days=1)
        first = now - timedelta(days=20)
        solve = Solve(user_id=1, platform="codeforces", title_slug="cf-1-a", difficulty="Rated",
                      solved_at=first, first_solve_at=first, first_solve_verified=True, problem_rating=800)
        self.db.add(solve)
        self.db.commit()
        row = self.row(now - timedelta(minutes=5))
        with patch("app.codeforces_sync.fetch_accepted_history", new=AsyncMock(return_value=[row])):
            self.assertEqual(asyncio.run(sync_codeforces_user(self.db, user)), 0)
            user.codeforces_last_sync = now - timedelta(minutes=12)
            self.db.commit()
            asyncio.run(sync_codeforces_user(self.db, user))
        self.db.refresh(solve)
        self.assertEqual(solve.first_solve_at, first)
        self.assertEqual(self.db.query(Solve).count(), 1)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").count(), 1)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 1)
        self.assertGreater(solve.points_earned, 10)

    def test_initial_cf_history_import_never_awards_old_revisions(self):
        now = utc_now()
        user = self.db.get(User, 1)
        user.codeforces_username = "demo_cf"
        self.db.commit()
        row = self.row(now - timedelta(days=20), 1)
        row["accepted_submissions"] = [
            {"timestamp": row["timestamp"], "submission_id": 1},
            {"timestamp": int((now - timedelta(days=10)).replace(tzinfo=timezone.utc).timestamp()), "submission_id": 2},
        ]
        with patch("app.codeforces_sync.fetch_accepted_history", new=AsyncMock(return_value=[row])):
            asyncio.run(sync_codeforces_user(self.db, user))
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 2)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").count(), 0)
        self.assertEqual(self.db.query(Solve).count(), 1)

    def test_incremental_unknown_question_has_no_verified_first_date(self):
        now = utc_now()
        user = self.db.get(User, 1)
        user.codeforces_username = "demo_cf"
        user.codeforces_last_sync = now - timedelta(minutes=12)
        user.codeforces_last_full_sync = now - timedelta(days=1)
        self.db.commit()
        with patch("app.codeforces_sync.fetch_accepted_history", new=AsyncMock(return_value=[self.row(now - timedelta(minutes=5))])):
            asyncio.run(sync_codeforces_user(self.db, user))
        solve = self.db.query(Solve).one()
        self.assertIsNone(solve.first_solve_at)
        self.assertFalse(solve.first_solve_verified)
        self.assertEqual(solve.points_earned, 8)
