"""Tests for incremental challenge archive backfill and coverage tracking."""
import os
import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

os.environ.setdefault("JWT_SECRET", "synthetic-unit-test-key-" + "x" * 40)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import DailyChallenge
from app.challenge_archive import is_month_covered, backfill_daily_challenges_archive


class ChallengeArchiveTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_is_month_covered_past_month(self):
        # February 2024 has 29 days (leap year)
        ref_date = date(2024, 6, 1)
        self.assertFalse(is_month_covered(self.db, 2024, 2, reference_date=ref_date))

        # Add 28 days -> still not covered (needs 29)
        for d in range(1, 29):
            self.db.add(DailyChallenge(date=date(2024, 2, d), title_slug=f"problem-{d}"))
        self.db.commit()
        self.assertFalse(is_month_covered(self.db, 2024, 2, reference_date=ref_date))

        # Add day 29 -> now covered
        self.db.add(DailyChallenge(date=date(2024, 2, 29), title_slug="problem-29"))
        self.db.commit()
        self.assertTrue(is_month_covered(self.db, 2024, 2, reference_date=ref_date))

    def test_is_month_covered_current_month(self):
        ref_date = date(2024, 4, 15)
        # Needs days 1..15
        for d in range(1, 15):
            self.db.add(DailyChallenge(date=date(2024, 4, d), title_slug=f"problem-{d}"))
        self.db.commit()
        self.assertFalse(is_month_covered(self.db, 2024, 4, reference_date=ref_date))

        self.db.add(DailyChallenge(date=date(2024, 4, 15), title_slug="problem-15"))
        self.db.commit()
        self.assertTrue(is_month_covered(self.db, 2024, 4, reference_date=ref_date))

    def test_is_month_covered_future_month(self):
        ref_date = date(2024, 4, 15)
        self.assertTrue(is_month_covered(self.db, 2024, 5, reference_date=ref_date))
        self.assertTrue(is_month_covered(self.db, 2025, 1, reference_date=ref_date))

    @patch("app.challenge_archive.fetch_monthly_daily_challenges", new_callable=AsyncMock)
    async def test_incremental_backfill_skips_covered_months(self, mock_fetch):
        mock_fetch.return_value = {
            "2024-01-01": "two-sum",
            "2024-01-02": "add-two-numbers",
        }
        ref_date = date(2024, 1, 2)

        # Run 1: month is missing -> fetches and inserts
        res1 = await backfill_daily_challenges_archive(
            self.db, start_year=2024, incremental=True, reference_date=ref_date
        )
        self.assertEqual(mock_fetch.await_count, 1)
        self.assertEqual(res1["added_records"], 2)
        self.assertIn("2024-01", res1["fetched_months"])

        # Run 2: month is now covered -> skipped, 0 fetches
        mock_fetch.reset_mock()
        res2 = await backfill_daily_challenges_archive(
            self.db, start_year=2024, incremental=True, reference_date=ref_date
        )
        self.assertEqual(mock_fetch.await_count, 0)
        self.assertEqual(res2["added_records"], 0)
        self.assertIn("2024-01", res2["skipped_months"])

        # Run 3: force=True -> fetches even though covered
        mock_fetch.reset_mock()
        res3 = await backfill_daily_challenges_archive(
            self.db, start_year=2024, incremental=False, force=True, reference_date=ref_date
        )
        self.assertEqual(mock_fetch.await_count, 1)
        self.assertIn("2024-01", res3["fetched_months"])


if __name__ == "__main__":
    unittest.main()
