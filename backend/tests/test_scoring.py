import unittest
from decimal import Decimal

from app.scoring import calculate_points, revision_points, streak_multiplier


class ComponentScoringTests(unittest.TestCase):
    def test_existing_category_and_acceptance_formulas(self):
        for difficulty, base in [("Easy", 8), ("Medium", 15), ("Hard", 24)]:
            self.assertEqual(calculate_points(platform="leetcode", difficulty=difficulty, ac_rate=50)["base_points"], base)
        self.assertEqual(calculate_points(platform="leetcode", difficulty="Easy", ac_rate=0)["base_points"], 12)
        self.assertEqual(calculate_points(platform="leetcode", difficulty="Easy", ac_rate=100)["base_points"], 4)

    def test_rated_leetcode_uses_rating_before_acceptance_adjustment(self):
        result = calculate_points(platform="leetcode", rating=1823, ac_rate=10)
        self.assertEqual(result["base_points"], Decimal("18.2300"))
        self.assertEqual(result["ac_multiplier"], 1)

    def test_codeforces_keeps_calibrated_linear_scale(self):
        for rating, expected in [(800, "8"), (1400, "15.2"), (1800, "20"), (2200, "24.8")]:
            self.assertEqual(calculate_points(platform="codeforces", rating=rating)["base_points"], Decimal(expected))
        self.assertEqual(calculate_points(platform="codeforces")["points_earned"], 0)

    def test_daily_and_revision_awards_use_the_same_capped_multiplier(self):
        result = calculate_points(platform="leetcode", difficulty="Easy", daily_eligible=True, streak_days=30)
        self.assertEqual(result["base_award"], Decimal("8.8000"))
        self.assertEqual(result["daily_award"], Decimal("5.5000"))
        self.assertEqual(revision_points(1), Decimal("2.0067"))
        self.assertEqual(revision_points(30), Decimal("2.2000"))
        self.assertEqual(revision_points(100), revision_points(30))
        self.assertEqual(streak_multiplier(-1), 1)

    def test_retained_components_are_never_multiplied_again(self):
        result = calculate_points(platform="leetcode", difficulty="Easy", streak_days=30,
                                  retained_daily_points=Decimal("5.1234"), retained_revision_points=Decimal("2.0067"))
        self.assertEqual(result["daily_award"], Decimal("5.1234"))
        self.assertEqual(result["revision_award"], Decimal("2.0067"))
        self.assertEqual(result["points_earned"], Decimal("15.9301"))

    def test_totals_reproduce_the_stored_components_exactly(self):
        for days in range(45):
            for rate in [0, 12.345, 50, 100]:
                result = calculate_points(platform="leetcode", difficulty="Medium", ac_rate=rate, streak_days=days, daily_eligible=True)
                self.assertEqual(result["points_earned"], sum(result[key] for key in ["base_award", "daily_award", "revision_award"]))

    def test_invalid_or_missing_evidence_is_not_silently_scored_as_medium(self):
        invalid = [dict(platform="leetcode"), dict(platform="leetcode", rating=float("nan")),
                   dict(platform="leetcode", difficulty="Easy", ac_rate=101), dict(platform="leetcode", rating=0),
                   dict(platform="codeforces", rating=float("inf")), dict(platform="external"),
                   dict(platform="leetcode", difficulty="Easy", streak_days=True),
                   dict(platform="leetcode", difficulty="Easy", daily_eligible="yes"),
                   dict(platform="leetcode", rating=1e300)]
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                calculate_points(**arguments)

    def test_retained_daily_cannot_be_awarded_twice_or_applied_to_codeforces(self):
        invalid = [dict(platform="leetcode", difficulty="Easy", daily_eligible=True, retained_daily_points=5),
                   dict(platform="codeforces", rating=1400, daily_eligible=True),
                   dict(platform="leetcode", difficulty="Easy", retained_daily_points=-1)]
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                calculate_points(**arguments)
