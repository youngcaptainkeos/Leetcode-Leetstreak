"""Tests for score ledger reconciliation, point awards persistence, and handle change reconciliation."""
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import test_access as fixtures
from app.models import User, Solve, DailyActivity, PlatformActivity, AcceptedSubmission, PointAward, ScoreSnapshot
from app.point_calculator import recalculate_user_points, compute_solve_points_breakdown, compute_codeforces_points_breakdown
from app.scoring import SCORING_VERSION


class ScoreReconciliationTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def test_recalculate_persists_exact_point_awards_and_baseline(self):
        user = self.db.query(User).filter_by(id=1).one()
        # Add a LeetCode solve and a Codeforces solve
        solve1 = Solve(
            user_id=1, platform="leetcode", title_slug="synthetic-p1",
            difficulty="Easy", ac_rate=50.0, solved_at=datetime(2026, 1, 1),
            is_daily=True,
        )
        solve2 = Solve(
            user_id=1, platform="codeforces", title_slug="cf-100-a",
            problem_rating=1200, solved_at=datetime(2026, 1, 2),
        )
        self.db.add_all([solve1, solve2])
        self.db.commit()

        total = recalculate_user_points(user, self.db)
        self.assertGreater(total, 0)

        # Baseline snapshot exists
        snapshot = self.db.query(ScoreSnapshot).filter_by(user_id=1).first()
        self.assertIsNotNone(snapshot)

        # Base and daily awards recorded in PointAward table
        awards = self.db.query(PointAward).filter_by(user_id=1).all()
        award_kinds = {a.kind for a in awards}
        self.assertIn("base", award_kinds)
        self.assertNotIn("daily", award_kinds)  # An old daily flag is not an earned award.

        # Scoring version matches SCORING_VERSION
        for a in awards:
            self.assertEqual(a.scoring_version, SCORING_VERSION)

        # Solves updated with components state
        for s in [solve1, solve2]:
            self.db.refresh(s)
            self.assertEqual(s.score_components_state, "base_only_history")
            self.assertGreater(s.points_earned, 0)

    def test_reconciliation_is_idempotent(self):
        user = self.db.query(User).filter_by(id=1).one()
        solve = Solve(
            user_id=1, platform="leetcode", title_slug="synthetic-idem",
            difficulty="Medium", ac_rate=50.0, solved_at=datetime(2026, 1, 1),
        )
        self.db.add(solve)
        self.db.commit()

        total1 = recalculate_user_points(user, self.db)
        award_count1 = self.db.query(PointAward).filter_by(user_id=1).count()

        total2 = recalculate_user_points(user, self.db)
        award_count2 = self.db.query(PointAward).filter_by(user_id=1).count()

        self.assertEqual(total1, total2)
        self.assertEqual(award_count1, award_count2)

    def test_unlogged_historical_solves_get_base_credit_only(self):
        user = self.db.query(User).filter_by(id=1).one()
        user.easy_count = 10
        user.medium_count = 0
        user.hard_count = 0
        # No logged solves in solves table
        self.db.commit()

        total = recalculate_user_points(user, self.db)
        # 10 unlogged Easy problems * 8.0 base points * 1.0 (multiplier=1, no daily bonus) = 80.0
        self.assertEqual(total, 80.0)

    def test_handle_change_reconciles_platform_history(self):
        user = self.db.query(User).filter_by(id=1).one()
        # User has a LeetCode solve and a Codeforces solve
        lc_solve = Solve(
            user_id=1, platform="leetcode", title_slug="old-lc-prob",
            difficulty="Easy", ac_rate=50.0, solved_at=datetime(2026, 1, 1),
        )
        cf_solve = Solve(
            user_id=1, platform="codeforces", title_slug="cf-100-b",
            problem_rating=1000, solved_at=datetime(2026, 1, 2),
        )
        self.db.add_all([lc_solve, cf_solve])
        self.db.commit()

        old_account_version = user.leetcode_account_version

        # Change LeetCode handle to new account
        new_data = {
            "avatar_url": "https://example.com/new_avatar.png",
            "difficulty_counts": {"Easy": 2, "Medium": 0, "Hard": 0},
            "official_streak": 0,
            "submission_calendar": {},
            "recent_submissions": [{
                "id": "9901", "title": "New Problem", "titleSlug": "new-problem",
                "timestamp": str(int(datetime(2026, 1, 15, tzinfo=timezone.utc).timestamp())),
            }],
        }
        with patch("app.main.fetch_leetcode_user_data", new=AsyncMock(return_value=new_data)), \
             patch("app.scheduler.fetch_leetcode_user_data", new=AsyncMock(return_value=new_data)), \
             patch("app.scheduler.fetch_today_daily_challenge_slug", new=AsyncMock(return_value=None)), \
             patch("app.scheduler.fetch_problem_info", new=AsyncMock(return_value={"difficulty": "Easy", "ac_rate": 50.0})):
            res = self.client.put("/api/users/1/leetcode-username", headers=self.headers(1), json={"leetcode_username": "new_handle_xyz"})

        self.assertEqual(res.status_code, 200)
        self.db.refresh(user)
        self.assertEqual(user.leetcode_username, "new_handle_xyz")
        # Account version bumped
        self.assertEqual(user.leetcode_account_version, old_account_version + 1)

        # Old LeetCode solve was removed, new LeetCode solve exists
        self.assertEqual(self.db.query(Solve).filter_by(user_id=1, title_slug="old-lc-prob").count(), 0)
        self.assertEqual(self.db.query(Solve).filter_by(user_id=1, title_slug="new-problem").count(), 1)

        # Codeforces solve is completely preserved!
        self.assertEqual(self.db.query(Solve).filter_by(user_id=1, title_slug="cf-100-b").count(), 1)

    def test_breakdown_helpers_match_calculated_points(self):
        # LeetCode breakdown
        bd_lc = compute_solve_points_breakdown(difficulty="Easy", ac_rate=50.0, streak_days=10, is_daily=True)
        self.assertAlmostEqual(bd_lc["points_earned"], (8.0 + 5.0) * (1.0 + 10 / 300), places=3)
        self.assertEqual(bd_lc["base_points"], 8.0)

        # Codeforces breakdown
        bd_cf = compute_codeforces_points_breakdown(rating=1400, streak_days=10)
        # Base for 1400: 8 + 0.012*(1400 - 800) = 8 + 7.2 = 15.2
        self.assertEqual(bd_cf["base_points"], 15.2)
        self.assertAlmostEqual(bd_cf["points_earned"], 15.2 * (1.0 + 10 / 300), places=3)
