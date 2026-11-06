"""Synthetic component reconciliation; no providers or production databases."""
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import test_access as fixtures
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import AccountCredit, PointAward, ScoreSnapshot, Solve, User
from app.reconciliation import reconcile_user, stored_breakdown
from app.tracking import ProviderAcceptance, ingest_acceptances


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="leetstreak-reconciliation-")
        self.engine = create_engine("sqlite:///" + self.directory.name + "/test.db")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(id=1, name="Demo", email="demo@example.com", leetcode_username="demo_lc", codeforces_username="demo_cf")
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.directory.cleanup()

    def solve(self, **changes):
        args = dict(user_id=1, title_slug="synthetic-question", source_handle="demo_lc", platform="leetcode",
                    solved_at=datetime(2026, 1, 1), difficulty="Easy", ac_rate=50, points_earned=8)
        row = Solve(**{**args, **changes})
        self.db.add(row)
        self.db.flush()
        return row

    def test_unknown_daily_combined_credit_is_preserved_without_guessing(self):
        row = self.solve(is_daily=True, points_earned=17.1234)
        self.user.easy_count = 1
        self.assertEqual(reconcile_user(self.user, self.db), 17.1234)
        with patch("app.reconciliation.get_contest_rating", return_value=2500):
            self.assertEqual(reconcile_user(self.user, self.db), 17.1234)
        self.assertEqual(self.db.query(PointAward).count(), 1)
        self.assertEqual(row.score_components_state, "legacy_protected")
        self.assertEqual(stored_breakdown(self.db, row)["legacy_credit"], Decimal("17.1234"))

    def test_stored_daily_and_revision_amounts_survive_base_revaluation_exactly(self):
        row = self.solve()
        for kind, amount in (("daily", "5.1234"), ("revision", "2.2000")):
            self.db.add(PointAward(award_key=f"synthetic-{kind}", user_id=1, solve_id=row.id, kind=kind,
                                  points=Decimal(amount), scoring_version="synthetic-v1"))
        self.db.flush()
        self.assertEqual(reconcile_user(self.user, self.db), 15.3234)
        with patch("app.reconciliation.get_contest_rating", return_value=2000):
            self.assertEqual(reconcile_user(self.user, self.db), 27.3234)
        breakdown = stored_breakdown(self.db, row)
        self.assertEqual(breakdown["daily_award"], Decimal("5.1234"))
        self.assertEqual(breakdown["revision_award"], Decimal("2.2000"))
        self.assertEqual(breakdown["points_earned"], sum(breakdown[key] for key in ("base_award", "daily_award", "revision_award", "legacy_credit")))

    def test_no_retrospective_daily_award_for_a_new_import(self):
        row = self.solve(is_daily=False)
        self.assertEqual(reconcile_user(self.user, self.db), 8)
        self.assertFalse(row.is_daily)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="daily").count(), 0)
        self.assertIsNone(self.db.query(PointAward).one().earned_at)

    def test_unclassified_preserved_question_does_not_overlap_the_aggregate_pool(self):
        row = self.solve(difficulty=None, ac_rate=None, points_earned=10)
        self.user.easy_count = 1
        self.assertEqual(reconcile_user(self.user, self.db), 10)
        self.assertEqual(self.db.query(AccountCredit).one().points, 0)
        row.difficulty = "Easy"
        row.ac_rate = 50
        self.assertEqual(reconcile_user(self.user, self.db), 8)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="legacy").count(), 0)
        self.assertEqual(self.db.query(AccountCredit).one().points, 0)

    def test_zero_credit_unclassified_question_can_receive_anonymous_base_estimate(self):
        self.solve(difficulty=None, ac_rate=None, points_earned=0)
        self.user.easy_count = 1
        self.assertEqual(reconcile_user(self.user, self.db), 8)
        credit = self.db.query(AccountCredit).one()
        self.assertEqual(credit.points, 8)
        self.assertTrue(credit.input_snapshot["estimated"])

    def test_remaining_history_uses_category_bases_without_official_streak(self):
        self.user.easy_count, self.user.medium_count, self.user.hard_count = 2, 1, 1
        self.user.official_streak = 100
        row = self.solve()
        self.assertEqual(reconcile_user(self.user, self.db), 55)
        self.assertEqual(self.db.query(AccountCredit).one().points, 47)
        self.assertEqual(row.points_earned, 8)
        self.assertIsNone(self.db.query(PointAward).one().earned_at)

    def test_metadata_loss_keeps_the_existing_base_until_valid_evidence_returns(self):
        row = self.solve()
        reconcile_user(self.user, self.db)
        row.difficulty = None
        row.ac_rate = None
        self.assertEqual(reconcile_user(self.user, self.db), 8)
        self.assertEqual(row.score_components_state, "metadata_missing")
        self.assertEqual(self.db.query(PointAward).count(), 1)

    def test_baseline_is_immutable_and_reconciliation_rolls_back_with_caller(self):
        row = self.solve(is_daily=True, points_earned=17.5)
        self.db.commit()
        reconcile_user(self.user, self.db)
        original = self.db.query(ScoreSnapshot).one().payload
        self.db.commit()
        self.assertEqual(reconcile_user(self.user, self.db), 17.5)
        self.assertEqual(self.db.query(ScoreSnapshot).one().payload, original)
        self.db.rollback()
        self.assertEqual(self.db.query(PointAward).count(), 1)

    def test_revisions_are_replay_safe_and_never_add_questions_or_daily_awards(self):
        row = self.solve(platform="codeforces", source_handle="demo_cf", title_slug="cf-100-a", problem_rating=800)
        ingest_acceptances(self.db, 1, platform="codeforces", account_version=0, expected_handle="demo_cf", complete_history=True,
            submissions=[ProviderAcceptance(str(100 + day), row.title_slug, datetime(2026, 1, day)) for day in (1, 8, 15)])
        reconcile_user(self.user, self.db)  # Initial import earns no revisions.
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").count(), 0)
        for _ in range(2):
            reconcile_user(self.user, self.db, revision_windows={"codeforces": datetime(2026, 1, 2)})
        self.assertEqual(self.db.query(PointAward).filter_by(kind="revision").count(), 2)
        self.assertEqual(self.db.query(Solve).count(), 1)
        self.assertEqual(self.db.query(PointAward).filter_by(kind="daily").count(), 0)
        self.assertEqual(row.points_earned, 12.0267)  # 8 × first-day multiplier, plus 2 + 2.

    def test_stale_generation_history_cannot_add_points_or_reserve_estimate_slots(self):
        self.solve(account_version=1, points_earned=500)
        self.user.easy_count = 1
        self.assertEqual(reconcile_user(self.user, self.db), 8)
        self.assertEqual(self.db.query(PointAward).count(), 0)

    def test_reused_solve_id_after_replacement_cannot_inherit_a_legacy_bonus(self):
        old = self.solve(is_daily=True, points_earned=50)
        reconcile_user(self.user, self.db)
        self.db.query(PointAward).delete()
        self.db.delete(old)
        self.db.flush()
        self.user.leetcode_account_version = 1
        self.user.leetcode_username = "another_demo"
        row = self.solve(account_version=1, source_handle="another_demo", is_daily=False)
        self.assertEqual(reconcile_user(self.user, self.db), 8)
        self.assertEqual(row.score_components_state, "base_only")
