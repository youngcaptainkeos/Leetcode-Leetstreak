from datetime import date, timedelta


def current_streak(active_dates: set[date], today: date | None = None) -> int:
    """
    Consecutive-day activity streak ending today or yesterday.
    Grace period: if the user hasn't solved anything YET today, the streak
    isn't broken until tomorrow (they still have time today).
    """
    today = today or date.today()

    cursor = today
    if cursor not in active_dates:
        cursor = today - timedelta(days=1)
        if cursor not in active_dates:
            return 0

    streak = 0
    while cursor in active_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
