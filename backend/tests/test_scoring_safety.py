"""Regression checks for the scoring blockers found in the pre-launch review."""
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, AsyncMock

import test_access as fixtures
from app.models import User, Solve, PointAward, DailyChallenge, DailyActivity
from app.point_calculator import recalculate_user_points
from app.platforms import daily_counts
from app.timekeeping import ist_date, period_bounds
from app.tracking import capture_score_baseline


class ScoringSafetyTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def solve(self, **kwargs):
        values = dict(user_id=1, platform="leetcode", title_slug="synthetic-safety",
                      difficulty="Easy", ac_rate=50, solved_at=datetime(2026, 1, 1),
                      points_earned=0)
        values.update(kwargs)
        row = Solve(**values)
        self.db.add(row)
        self.db.flush()
        return row

    def award(self, solve, kind, points, earned_at=None):
        row = PointAward(user_id=1, solve_id=solve.id, kind=kind, points=Decimal(points),
                         award_key=f"{kind}:{solve.id}", scoring_version="points-components-v2",
                         earned_at=earned_at, input_snapshot={})
        self.db.add(row)
        self.db.flush()
        return row

    def recalc(self):
        with patch("app.point_calculator.get_contest_rating", return_value=None):
            return recalculate_user_points(self.db.get(User, 1), self.db)

    def test_archive_and_current_slug_do_not_mint_historical_daily_bonus(self):
        solve = self.solve(is_daily=True)
        self.db.add(DailyChallenge(date=ist_date(solve.solved_at), title_slug=solve.title_slug))
        self.assertEqual(self.recalc(), 8)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="daily").count(), 0)
        base = self.db.query(PointAward).filter_by(kind="base").one()
        self.assertIsNone(base.earned_at)
        self.assertEqual(solve.score_components_state, "base_only_history")

    def test_earned_daily_and_revision_amounts_survive_base_changes(self):
        solve = self.solve(is_daily=True, first_solve_verified=True, first_solve_at=datetime(2026, 1, 1))
        daily = self.award(solve, "daily", "5.4321", datetime(2026, 1, 1))
        revision = self.award(solve, "revision", "2.1234", datetime(2026, 1, 9))
        self.assertAlmostEqual(self.recalc(), 8.0267 + 5.4321 + 2.1234, places=4)
        solve.difficulty = "Hard"
        self.assertAlmostEqual(self.recalc(), 24.08 + 5.4321 + 2.1234, places=4)
        self.assertEqual(daily.points, Decimal("5.4321"))
        self.assertEqual(revision.points, Decimal("2.1234"))

    def test_uncertain_legacy_daily_combined_total_is_protected(self):
        solve = self.solve(is_daily=True, points_earned=37.25)
        self.assertEqual(self.recalc(), 37.25)
        solve.difficulty = "Hard"
        self.assertEqual(self.recalc(), 37.25)
        legacy = self.db.query(PointAward).filter_by(kind="legacy").one()
        self.assertIsNone(legacy.earned_at)
        self.assertTrue(legacy.input_snapshot["needs_reconciliation"])
        self.assertEqual(solve.score_components_state, "protected_legacy")
        self.assertEqual(self.db.query(PointAward).count(), 1)

    def test_original_snapshot_recovers_previously_overwritten_legacy_total(self):
        solve = self.solve(is_daily=True, points_earned=31.75)
        capture_score_baseline(self.db, 1)
        solve.points_earned = 13
        solve.scoring_version = "points-components-v2"
        self.award(solve, "base", "8")
        self.award(solve, "daily", "5")
        self.assertEqual(self.recalc(), 31.75)
        self.assertEqual(self.db.query(PointAward).count(), 1)

    def test_unverified_dates_and_calendar_counts_do_not_extend_streak(self):
        self.solve(first_solve_at=datetime(2026, 1, 1), first_solve_verified=False)
        self.db.add(DailyActivity(user_id=1, date=ist_date(datetime(2026, 1, 1)), problems_solved=50))
        self.db.flush()
        self.assertEqual(dict(daily_counts(self.db, [1])[1]), {})
        self.assertEqual(self.recalc(), 8)

    def test_unverified_history_is_excluded_from_period_points_even_with_old_award_dates(self):
        start, _ = period_bounds("week")
        solve = self.solve(solved_at=start + timedelta(hours=1), first_solve_at=None, points_earned=100)
        self.award(solve, "base", "100", start + timedelta(hours=1))
        response = self.client.get("/api/leaderboard?period=week", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        entry = next(row for row in response.json()["entries"] if row["id"] == 1)
        self.assertEqual(entry["points"], 0)

    def test_codeforces_revision_is_included_in_total_during_reconciliation(self):
        solve = self.solve(platform="codeforces", title_slug="cf-1-a", problem_rating=800,
                           first_solve_verified=True, first_solve_at=datetime(2026, 1, 1))
        self.award(solve, "revision", "2.1", datetime(2026, 1, 9))
        self.assertAlmostEqual(self.recalc(), float(Decimal("8.0267") + Decimal("2.1")), places=4)

    def test_missing_historical_credit_uses_actual_remaining_difficulties(self):
        user = self.db.get(User, 1)
        user.easy_count, user.hard_count = 1, 1
        self.solve(difficulty="Hard")
        self.assertEqual(self.recalc(), 32)  # known Hard 24 + remaining Easy 8

    def test_recent_solve_read_does_not_infer_or_write_daily_eligibility(self):
        solve = self.solve(is_daily=False, points_earned=8)
        self.db.add(DailyChallenge(date=ist_date(solve.solved_at), title_slug=solve.title_slug))
        self.db.commit()
        with patch("app.main.fetch_today_daily_challenge_slug", new=AsyncMock()) as daily:
            response = self.client.get("/api/users/1/recent-solves", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        daily.assert_not_called()
        self.db.refresh(solve)
        self.assertFalse(solve.is_daily)
        self.assertEqual(solve.points_earned, 8)
