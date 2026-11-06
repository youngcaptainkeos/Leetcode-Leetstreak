import unittest
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
import test_access as fixtures
from app.models import AcceptedSubmission, PointAward, ScoreSnapshot, Solve, User
from app.tracking import capture_score_baseline, record_acceptance


class TrackingEvidenceTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def event(self, **changes):
        values = dict(platform="leetcode", account_version=0, submission_id="100", title_slug="synthetic-question",
                      accepted_at=datetime(2026, 1, 1, tzinfo=timezone.utc), evidence_kind="public_recent")
        return record_acceptance(self.db, 1, **{**values, **changes})

    def test_overlapping_provider_pages_are_idempotent(self):
        first = self.event()
        self.assertEqual(self.event().id, first.id)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 1)
        self.assertEqual(self.db.query(Solve).count(), 0)
        self.assertEqual(self.db.query(PointAward).count(), 0)

    def test_repeat_acceptances_are_events_not_duplicate_questions(self):
        self.event()
        self.event(submission_id="101", accepted_at=datetime(2026, 1, 8))
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 2)
        self.assertTrue(all(not row.first_solve_verified for row in self.db.query(AcceptedSubmission)))
        self.assertEqual(self.db.query(Solve).count(), 0)

    def test_conflicting_and_stale_account_evidence_is_rejected(self):
        self.event()
        with self.assertRaises(ValueError):
            self.event(title_slug="different-question")
        self.db.query(User).filter_by(id=1).update({User.leetcode_account_version: 1})
        with self.assertRaises(ValueError):
            self.event(submission_id="102")
        with self.assertRaises(ValueError):
            self.event(account_version=1, evidence_kind="manual_checkbox")
        with self.assertRaises(ValueError):
            self.event(account_version=1, first_solve_verified=True)

    def test_legacy_snapshot_retains_totals_and_daily_marks_without_reconstruction(self):
        self.db.query(User).filter_by(id=1).update({User.points: 31.2345})
        self.db.add(Solve(user_id=1, title_slug="synthetic-daily", platform="leetcode", solved_at=datetime(2026, 1, 1), is_daily=True, points_earned=21.2345))
        self.db.flush()
        snapshot = capture_score_baseline(self.db, 1)
        self.assertEqual(snapshot.payload["points"], 31.2345)
        self.assertEqual(snapshot.payload["solves"][0]["points_earned"], 21.2345)
        self.assertIs(snapshot.payload["solves"][0]["is_daily"], True)
        self.assertNotIn("email", snapshot.payload)
        self.assertNotIn("password_hash", snapshot.payload)
        self.db.query(User).filter_by(id=1).update({User.points: 99})
        self.assertEqual(capture_score_baseline(self.db, 1).id, snapshot.id)
        self.assertEqual(snapshot.payload["points"], 31.2345)
        self.assertEqual(self.db.query(ScoreSnapshot).count(), 1)

    def test_awards_have_exact_components_and_unique_replay_keys(self):
        solve = Solve(user_id=1, title_slug="synthetic-award", platform="leetcode", solved_at=datetime(2026, 1, 1))
        self.db.add(solve); self.db.flush()
        award = PointAward(award_key="synthetic-base:1", user_id=1, solve_id=solve.id, kind="base", points=Decimal("8.0267"), scoring_version="synthetic-v1", input_snapshot={"streak_days": 1})
        self.db.add(award); self.db.commit(); self.db.refresh(award)
        self.assertEqual(award.points, Decimal("8.0267"))
        with self.assertRaises(IntegrityError):
            with self.db.begin_nested():
                self.db.add(PointAward(award_key="synthetic-base:1", user_id=1, solve_id=solve.id, kind="base", points=1, scoring_version="synthetic-v1", input_snapshot={}))
                self.db.flush()

    def test_account_deletion_removes_private_tracking_evidence(self):
        solve = Solve(user_id=3, title_slug="synthetic-delete", platform="leetcode", solved_at=datetime(2026, 1, 1))
        self.db.add(solve); self.db.flush()
        record_acceptance(self.db, 3, platform="leetcode", account_version=0, submission_id="200",
                          title_slug=solve.title_slug, accepted_at=solve.solved_at, evidence_kind="public_recent")
        self.db.add(PointAward(award_key="synthetic-delete:3", user_id=3, solve_id=solve.id, kind="base", points=8, scoring_version="synthetic-v1", input_snapshot={}))
        capture_score_baseline(self.db, 3); self.db.commit()
        response = self.client.post("/api/users/3/delete-account", headers=self.headers(3), json={"password": "synthetic-password"})
        self.assertEqual(response.status_code, 200)
        for model in (PointAward, AcceptedSubmission, ScoreSnapshot):
            self.assertEqual(self.db.query(model).filter_by(user_id=3).count(), 0)
