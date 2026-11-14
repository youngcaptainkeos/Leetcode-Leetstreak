"""Forward-only multiplier policy; existing PointAward rows stay immutable."""
from datetime import datetime

from .streak import current_streak
from .timekeeping import ist_date, utc_storage


# Owner-approved cutover: 14 November 2026, 16:42:59 IST. Use the
# acceptance/earning time, so a delayed historical import cannot gain a bonus.
SHARED_STREAK_START = datetime(2026, 11, 14, 11, 12, 59)


class AwardStreak:
    """Reuse the profile's cross-platform day set for newly earned rewards."""

    def __init__(self, db, user, first_dates):
        self.db = db
        self.user = user
        self.first_dates = first_dates
        self.activity_dates = None

    @staticmethod
    def basis_at(earned_at):
        return ("shared_profile_v1" if utc_storage(earned_at) >= SHARED_STREAK_START
                else "recorded_first_solves_v1")

    def days_at(self, earned_at):
        instant = utc_storage(earned_at)
        day = ist_date(instant)
        if instant < SHARED_STREAK_START:
            return current_streak({date for first, date in self.first_dates
                                   if utc_storage(first) <= instant}, day)
        if self.activity_dates is None:
            # Local import avoids a module cycle through daily_counts. This is
            # exactly the shared LC/CF date source used by profiles/rankings.
            from .platforms import streak_dates
            self.activity_dates = streak_dates(self.db, [self.user.id])[self.user.id]
        return current_streak({date for date in self.activity_dates if date <= day}, day)
