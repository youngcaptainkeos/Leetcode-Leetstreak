"""Tests for accepted submission evidence ingestion, deduplication, streak qualifying rules, and revision awards."""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from decimal import Decimal

import test_access as fixtures
from app.models import User, Solve, DailyActivity, PlatformActivity, AcceptedSubmission, PointAward, DailyChallenge
from app.scheduler import poll_user
from app.codeforces_sync import sync_codeforces_user
from app.streak import current_streak
from app.platforms import daily_counts
from app.timekeeping import IST, ist_date, ist_today, utc_storage


class TrackingSyncTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def test_recent_acceptance_does_not_prove_first_solve(self):
        user = self.db.query(User).filter_by(id=1).one()
        now_ts = int(datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc).timestamp())
        mock_data = {
            "avatar_url": "https://example.com/avatar.png",
            "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0},
            "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [{
                "id": "1001",
                "title": "Two Sum",
                "titleSlug": "two-sum",
                "timestamp": str(now_ts),
            }],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=mock_data)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            new_count = asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        self.assertEqual(new_count, 1)
        self.assertEqual(self.db.query(Solve).filter_by(user_id=1, title_slug="two-sum").count(), 1)
        solve = self.db.query(Solve).filter_by(user_id=1, title_slug="two-sum").one()
        self.assertFalse(solve.first_solve_verified)
        self.assertIsNone(solve.first_solve_at)

        # Evidence record exists
        acc = self.db.query(AcceptedSubmission).filter_by(user_id=1, submission_id="1001").one()
        self.assertEqual(acc.solve_id, solve.id)
        self.assertEqual(acc.title_slug, "two-sum")

        # DailyActivity exists for that IST date
        day = ist_date(datetime.fromtimestamp(now_ts, tz=timezone.utc))
        self.assertEqual(self.db.query(DailyActivity).filter_by(user_id=1, date=day).count(), 0)
        self.assertTrue(user.leetcode_history_gap)

    def test_repeat_submission_does_not_duplicate_solve_or_streak(self):
        user = self.db.query(User).filter_by(id=1).one()
        t1 = int(datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc).timestamp())
        t2 = int(datetime(2026, 1, 11, 10, 0, tzinfo=timezone.utc).timestamp())

        # First poll with Two Sum on day 1
        data1 = {
            "avatar_url": None, "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0}, "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [{
                "id": "1001", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": str(t1),
            }],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=data1)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        self.assertEqual(self.db.query(Solve).filter_by(user_id=1, title_slug="two-sum").count(), 1)
        self.assertEqual(self.db.query(AcceptedSubmission).filter_by(user_id=1).count(), 1)

        # Second poll on day 2 with same problem repeated
        data2 = {
            "avatar_url": None, "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0}, "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [
                {"id": "1001", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": str(t1)},
                {"id": "1002", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": str(t2)},
            ],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=data2)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            new_count2 = asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        # No new solve added
        self.assertEqual(new_count2, 0)
        self.assertEqual(self.db.query(Solve).filter_by(user_id=1, title_slug="two-sum").count(), 1)
        # But evidence is recorded for both submissions
        self.assertEqual(self.db.query(AcceptedSubmission).filter_by(user_id=1).count(), 2)

        # Day 2 has NO DailyActivity row because no first solves occurred on day 2
        day2 = ist_date(datetime.fromtimestamp(t2, tz=timezone.utc))
        self.assertEqual(self.db.query(DailyActivity).filter_by(user_id=1, date=day2).count(), 0)

        # Streak on day 2 is 0 or 1 (grace period for yesterday), not 2
        active_dates = set(daily_counts(self.db, [user.id])[user.id])
        self.assertNotIn(day2, active_dates)
        self.assertEqual(current_streak(active_dates, today=day2), 0)

    def test_calendar_activity_alone_does_not_create_solved_question_counts(self):
        user = self.db.query(User).filter_by(id=1).one()
        # Data has submission calendar entries but no accepted submissions
        mock_data = {
            "avatar_url": None,
            "difficulty_counts": {"Easy": 0, "Medium": 0, "Hard": 0},
            "official_streak": 5,
            "submission_calendar": {
                "2026-01-01": 3,
                "2026-01-02": 4,
                "2026-01-03": 2,
            },
            "recent_submissions": [],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=mock_data)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)):
            import asyncio
            new_count = asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        self.assertEqual(new_count, 0)
        self.assertEqual(self.db.query(Solve).filter_by(user_id=1).count(), 0)
        # No DailyActivity rows with problems_solved > 0
        self.assertEqual(self.db.query(DailyActivity).filter_by(user_id=1).count(), 0)
        active_dates = set(daily_counts(self.db, [user.id])[user.id])
        self.assertEqual(len(active_dates), 0)

    def test_revision_award_after_seven_elapsed_days(self):
        user = self.db.query(User).filter_by(id=1).one()
        base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        t1 = int(base_time.timestamp())
        # First solve on Jan 1
        data1 = {
            "avatar_url": None, "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0}, "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [{"id": "2001", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t1)}],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=data1)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        # Solve exists, 0 revision awards
        self.assertEqual(self.db.query(PointAward).filter_by(user_id=1, kind="revision").count(), 0)

        # Repeat on Day 4 (Jan 4, 3 days later: < 7 days) -> No revision award
        t2 = int((base_time + timedelta(days=3)).timestamp())
        data2 = {
            "avatar_url": None, "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0}, "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [
                {"id": "2001", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t1)},
                {"id": "2002", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t2)},
            ],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=data2)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        self.assertEqual(self.db.query(PointAward).filter_by(user_id=1, kind="revision").count(), 0)

        # Repeat on Day 9 (Jan 9, 8 days later: >= 7 days) -> Revision award earned!
        t3 = int((base_time + timedelta(days=8)).timestamp())
        data3 = {
            "avatar_url": None, "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0}, "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [
                {"id": "2001", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t1)},
                {"id": "2002", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t2)},
                {"id": "2003", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t3)},
            ],
        }
        user.leetcode_last_sync = utc_storage(base_time + timedelta(days=7))
        self.db.commit()
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=data3)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        revisions = self.db.query(PointAward).filter_by(user_id=1, kind="revision").all()
        self.assertEqual(len(revisions), 1)
        self.assertGreater(revisions[0].points, Decimal("0"))
        # Revision points = 2 * streak multiplier (streak at least 0 -> at least 2.0)
        self.assertGreaterEqual(revisions[0].points, Decimal("2.0"))

        # Repeat on Day 12 (Jan 12, 3 days after rewarded revision -> < 7 days from Jan 9) -> No new award
        t4 = int((base_time + timedelta(days=11)).timestamp())
        data4 = {
            "avatar_url": None, "difficulty_counts": {"Easy": 1, "Medium": 0, "Hard": 0}, "official_streak": 1,
            "submission_calendar": {},
            "recent_submissions": [
                {"id": "2001", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t1)},
                {"id": "2002", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t2)},
                {"id": "2003", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t3)},
                {"id": "2004", "title": "Problem A", "titleSlug": "prob-a", "timestamp": str(t4)},
            ],
        }
        with patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=data4)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            import asyncio
            asyncio.run(poll_user(self.db, user, sync_codeforces=False))

        self.assertEqual(self.db.query(PointAward).filter_by(user_id=1, kind="revision").count(), 1)

    def test_codeforces_sync_records_acceptance_and_first_solve_metadata(self):
        user = self.db.query(User).filter_by(id=1).one()
        user.codeforces_username = "synthetic_cf_user"
        self.db.commit()

        cf_history = [{
            "slug": "cf-1000-a",
            "title": "Theatre Square",
            "url": "https://codeforces.com/contest/1000/problem/A",
            "rating": 1000,
            "timestamp": int(datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc).timestamp()),
            "submission_id": 50001,
        }]
        with patch("app.codeforces_sync.fetch_accepted_history", new=AsyncMock(return_value=cf_history)):
            import asyncio
            added = asyncio.run(sync_codeforces_user(self.db, user))

        self.assertEqual(added, 1)
        solve = self.db.query(Solve).filter_by(user_id=1, platform="codeforces", title_slug="cf-1000-a").one()
        self.assertTrue(solve.first_solve_verified)
        self.assertIsNotNone(solve.first_solve_at)

        # AcceptedSubmission evidence exists
        acc = self.db.query(AcceptedSubmission).filter_by(user_id=1, platform="codeforces", submission_id="50001").one()
        self.assertEqual(acc.solve_id, solve.id)
        self.assertTrue(acc.first_solve_verified)

        # PlatformActivity exists for Codeforces
        day = ist_date(solve.first_solve_at)
        pa = self.db.query(PlatformActivity).filter_by(user_id=1, platform="codeforces", date=day).one()
        self.assertEqual(pa.problems_solved, 1)
