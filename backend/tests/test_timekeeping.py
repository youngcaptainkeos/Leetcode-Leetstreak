import unittest
from datetime import date, datetime, timedelta, timezone

from app.timekeeping import IST, ist_date, ist_today, utc_storage, week_start, month_start, period_bounds, revision_due


class ProductTimeTests(unittest.TestCase):
    def test_ist_midnight_is_not_utc_midnight(self):
        self.assertEqual(ist_date(datetime(2026, 11, 5, 18, 29, 59)), date(2026, 11, 5))
        self.assertEqual(ist_date(datetime(2026, 11, 5, 18, 30)), date(2026, 11, 6))
        self.assertEqual(ist_today(datetime(2026, 11, 6, 0, 0, tzinfo=IST)), date(2026, 11, 6))

    def test_aware_and_naive_instants_agree(self):
        instant = datetime(2026, 11, 5, 18, 30)
        aware = datetime(2026, 11, 6, 0, 0, tzinfo=IST)
        self.assertEqual(utc_storage(aware), instant)
        self.assertEqual(ist_date(aware), ist_date(instant))

    def test_day_bounds_are_exclusive_at_next_midnight(self):
        self.assertEqual(period_bounds("today", date(2026, 1, 1)), (datetime(2025, 12, 31, 18, 30), datetime(2026, 1, 1, 18, 30)))

    def test_week_and_month_transitions(self):
        self.assertEqual(week_start(date(2026, 11, 8)), date(2026, 11, 8))
        self.assertEqual(week_start(date(2026, 11, 7)), date(2026, 11, 1))
        self.assertEqual(month_start(date(2026, 12, 31)), date(2026, 12, 1))
        start, end = period_bounds("month", date(2026, 12, 31))
        self.assertEqual((start, end), (datetime(2026, 11, 30, 18, 30), datetime(2026, 12, 31, 18, 30)))
        start, end = period_bounds("month", date(2028, 2, 29))
        self.assertEqual(end - start, timedelta(days=29))

    def test_revision_requires_seven_elapsed_days(self):
        anchor = datetime(2026, 1, 1, 18, 31)
        self.assertFalse(revision_due(anchor + timedelta(days=7, microseconds=-1), anchor))
        self.assertTrue(revision_due(anchor + timedelta(days=7), anchor))
        self.assertFalse(revision_due(anchor - timedelta(days=1), anchor))
        self.assertTrue(revision_due((anchor + timedelta(days=7)).replace(tzinfo=timezone.utc).astimezone(IST), anchor))

    def test_period_validation_and_all_time(self):
        self.assertEqual(period_bounds("all"), (None, None))
        with self.assertRaises(ValueError):
            period_bounds("unsupported")
