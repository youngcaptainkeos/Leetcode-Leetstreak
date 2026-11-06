"""Provider evidence and revision proposals; no real accounts or remote requests."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import test_access as fixtures
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import User, Solve, AcceptedSubmission, PointAward, DailyActivity
from app.tracking import ProviderAcceptance, ingest_acceptances, revision_candidates


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="leetstreak-ingestion-")
        self.engine = create_engine("sqlite:///" + self.directory.name + "/test.db")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(id=1, name="Demo", email="demo@example.com", leetcode_username="demo_lc",
                         codeforces_username="demo_cf", points=42.5)
        self.solve = Solve(id=1, user_id=1, platform="codeforces", source_handle="demo_cf",
                           title_slug="cf-100-a", solved_at=datetime(2026, 1, 1), points_earned=8)
        self.db.add_all([self.user, self.solve])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        self.directory.cleanup()

    def event(self, number=100, day=1, slug="cf-100-a", **kwargs):
        return ProviderAcceptance(str(number), slug, datetime(2026, 1, day, **kwargs))

    def ingest(self, rows, complete=True, **changes):
        args = dict(platform="codeforces", account_version=0, expected_handle="demo_cf",
                    submissions=rows, complete_history=complete)
        return ingest_acceptances(self.db, 1, **{**args, **changes})

    def test_full_import_keeps_repeats_with_one_question_and_no_rewards(self):
        events = [self.event(103, 15), self.event(), self.event(102, 8), self.event()]
        self.ingest(events)
        self.ingest(events)
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 3)
        self.assertEqual(self.db.query(Solve).count(), 1)
        self.db.refresh(self.solve)
        self.assertEqual(self.solve.first_solve_at, datetime(2026, 1, 1))
        self.assertTrue(self.solve.first_solve_verified)
        self.assertEqual(self.db.query(AcceptedSubmission).filter_by(first_solve_verified=True).count(), 1)
        self.assertEqual(revision_candidates(self.db, self.solve, live_after=None), [])
        self.assertEqual(self.db.query(PointAward).count(), 0)
        self.assertEqual(self.user.points, 42.5)

    def test_incremental_history_cannot_prove_first_solve_or_downgrade_full_proof(self):
        self.ingest([self.event(102, 8)], complete=False)
        self.assertFalse(self.solve.first_solve_verified)
        self.ingest([self.event(102, 8), self.event()], complete=True)
        self.db.refresh(self.solve)
        self.assertEqual(self.solve.first_solve_at, datetime(2026, 1, 1))
        self.ingest([self.event(103, 15)], complete=False)
        self.assertTrue(self.solve.first_solve_verified)
        self.assertEqual(self.solve.first_solve_at, datetime(2026, 1, 1))

    def test_later_full_history_corrects_earliest_proof_and_event_flags(self):
        self.ingest([self.event(102, 8)])
        self.ingest([self.event(), self.event(102, 8)])
        self.db.refresh(self.solve)
        self.assertEqual(self.solve.first_solve_at, datetime(2026, 1, 1))
        proof = self.db.query(AcceptedSubmission).filter_by(first_solve_verified=True).one()
        self.assertEqual(proof.submission_id, "100")

    def test_leetcode_recent_acceptances_never_prove_a_first_solve(self):
        solve = Solve(user_id=1, platform="leetcode", source_handle="demo_lc", title_slug="synthetic-question",
                      solved_at=datetime(2026, 1, 8))
        self.db.add(solve)
        self.db.flush()
        rows = [self.event(100, 1, "synthetic-question"), self.event(101, 8, "synthetic-question")]
        self.ingest(rows, complete=False, platform="leetcode", expected_handle="demo_lc")
        self.assertIsNone(solve.first_solve_at)
        self.assertFalse(solve.first_solve_verified)
        self.assertEqual(revision_candidates(self.db, solve, live_after=datetime(2026, 1, 2)), [])
        with self.assertRaises(ValueError):
            self.ingest(rows, platform="leetcode", expected_handle="demo_lc")

    def test_invalid_batch_does_not_store_a_valid_prefix(self):
        for bad in [self.event(0), self.event(100, slug="javascript:invalid"),
                    ProviderAcceptance("101", "cf-100-a", datetime(2099, 1, 1))]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.ingest([self.event(), bad])
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 0)

    def test_conflicting_replay_rolls_back_only_the_batch(self):
        self.ingest([self.event(101, 8)])
        with self.assertRaises(ValueError):
            self.ingest([self.event(), self.event(101, 9)])
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 1)
        self.db.refresh(self.solve)
        self.assertEqual(self.solve.first_solve_at, datetime(2026, 1, 8))

    def test_caller_rollback_undoes_a_successful_batch(self):
        self.ingest([self.event()])
        self.db.rollback()
        self.assertEqual(self.db.query(AcceptedSubmission).count(), 0)
        self.db.refresh(self.solve)
        self.assertFalse(self.solve.first_solve_verified)

    def test_handle_generation_and_source_mismatch_never_attach_evidence(self):
        for changes in [{"account_version": 1}, {"expected_handle": "someone_else"}, {"account_version": False}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.ingest([self.event()], **changes)
        self.solve.source_handle = "another_account"
        events = self.ingest([self.event()])
        self.assertIsNone(events[0].solve_id)
        self.assertFalse(self.solve.first_solve_verified)
        self.assertEqual(self.db.query(Solve).count(), 1)

    def test_exact_cooldown_recurs_without_unrewarded_attempts_resetting_it(self):
        self.ingest([self.event(), self.event(101, 7, hour=23, minute=59, second=59),
                     self.event(102, 8), self.event(103, 14), self.event(104, 15)])
        proposals = revision_candidates(self.db, self.solve, live_after=datetime(2026, 1, 2))
        self.assertEqual([row.accepted_at.day for row in proposals], [8, 15])
        self.assertEqual([row.points for row in proposals], [Decimal("2.0000"), Decimal("2.0000")])
        self.assertEqual(self.db.query(PointAward).count(), 0)
        self.assertEqual(self.db.query(Solve).count(), 1)

    def test_only_live_events_after_the_successful_sync_boundary_are_proposed(self):
        self.ingest([self.event(), self.event(101, 8), self.event(102, 15)])
        proposals = revision_candidates(self.db, self.solve, live_after=datetime(2026, 1, 8))
        self.assertEqual([row.accepted_at.day for row in proposals], [15])

    def test_rewarded_revision_is_the_recurring_anchor_and_is_not_proposed_again(self):
        self.ingest([self.event(), self.event(101, 8), self.event(102, 9), self.event(103, 15)])
        first = revision_candidates(self.db, self.solve, live_after=datetime(2026, 1, 2))[0]
        self.db.add(PointAward(award_key="synthetic-revision", user_id=1, solve_id=1,
            submission_id=first.event_id, kind="revision", points=first.points, earned_at=first.accepted_at,
            scoring_version="synthetic-v1"))
        self.db.flush()
        self.assertEqual([row.accepted_at.day for row in revision_candidates(
            self.db, self.solve, live_after=datetime(2026, 1, 2))], [15])

    def test_revisions_use_only_verified_first_solve_streaks_at_the_event_in_ist(self):
        self.ingest([self.event(), self.event(101, 8, hour=19)])  # January 9 IST
        for day in (7, 8, 9):
            instant = datetime(2026, 1, day, 0)
            self.db.add(Solve(user_id=1, platform="leetcode", source_handle="demo_lc", title_slug=f"synthetic-{day}",
                solved_at=instant, first_solve_at=instant, first_solve_verified=True))
        # The January 9 first solve is still in the future at the revision instant.
        self.db.add_all([DailyActivity(user_id=1, date=datetime(2026, 1, day).date(), problems_solved=100) for day in range(1, 10)])
        self.db.flush()
        proposal = revision_candidates(self.db, self.solve, live_after=datetime(2026, 1, 2))[0]
        self.assertEqual(proposal.streak_days, 2)  # Jan 7–8; Jan 9 still has yesterday's grace.
        self.assertEqual(proposal.points, Decimal("2.0133"))

    def test_unknown_reward_date_and_replaced_account_block_revision_proposals(self):
        self.ingest([self.event(), self.event(101, 8)])
        reward = PointAward(award_key="synthetic-unknown", user_id=1, solve_id=1,
            kind="revision", points=2, earned_at=None, scoring_version="synthetic-v1")
        self.db.add(reward)
        self.db.flush()
        self.assertEqual(revision_candidates(self.db, self.solve, live_after=datetime(2026, 1, 2)), [])
        self.db.delete(reward)
        self.user.codeforces_account_version += 1
        self.db.flush()
        self.assertEqual(revision_candidates(self.db, self.solve, live_after=datetime(2026, 1, 2)), [])
