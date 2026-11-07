from collections import defaultdict
from sqlalchemy.orm import Session
from .models import DailyActivity, PlatformActivity, Solve


def daily_counts(db: Session, user_ids: list[int]) -> dict:
    from .models import User
    from .reconciliation import proved_date
    from .timekeeping import ist_date, utc_now
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts
    now = utc_now()
    for solve, user in db.query(Solve, User).join(User, User.id == Solve.user_id).filter(
            Solve.user_id.in_(user_ids), Solve.first_solve_verified.is_(True), Solve.first_solve_at.isnot(None)).all():
        instant = proved_date(user, solve)
        if instant is not None and instant <= now:
            counts[user.id][ist_date(instant)] += 1
    return counts


def solve_url(solve: Solve) -> str:
    return solve.problem_url or f"https://leetcode.com/problems/{solve.title_slug}/"


def streak_dates(db: Session, user_ids: list[int], *, today=None, verified_counts=None) -> dict:
    """Temporary display compatibility while first-solve history is incomplete.

    Calendar activity can include repeats/attempts. Use it only for the visible
    activity streak, never as unique-solve evidence or a scoring multiplier.
    Existing date rows are unioned, so overlapping sources add no extra days.
    """
    from .models import User, ProviderCalendar
    from .timekeeping import ist_today
    today = today or ist_today()
    active = defaultdict(set)
    if not user_ids:
        return active
    verified = verified_counts if verified_counts is not None else daily_counts(db, user_ids)
    for user_id, counts in verified.items():
        active[user_id].update(day for day, count in counts.items() if count > 0 and day <= today)
    # Undated legacy account attribution is usable only for the initial linked
    # account. Current handle replacement clears these rows as well.
    for user_id, day in db.query(DailyActivity.user_id, DailyActivity.date).join(
            User, User.id == DailyActivity.user_id).filter(
            User.id.in_(user_ids), User.leetcode_account_version == 0,
            DailyActivity.problems_solved > 0, DailyActivity.date <= today):
        active[user_id].add(day)
    for user_id, day in db.query(PlatformActivity.user_id, PlatformActivity.date).join(
            User, User.id == PlatformActivity.user_id).filter(
            User.id.in_(user_ids), User.codeforces_account_version == 0,
            User.codeforces_username.isnot(None), PlatformActivity.platform == "codeforces",
            PlatformActivity.problems_solved > 0, PlatformActivity.date <= today):
        active[user_id].add(day)
    for user_id, day in db.query(ProviderCalendar.user_id, ProviderCalendar.date).join(
            User, User.id == ProviderCalendar.user_id).filter(
            User.id.in_(user_ids), ProviderCalendar.platform == "leetcode",
            ProviderCalendar.account_version == User.leetcode_account_version,
            ProviderCalendar.source == "leetcode_submission_calendar",
            ProviderCalendar.submission_count > 0, ProviderCalendar.date <= today):
        active[user_id].add(day)
    return active


def activity_counts(db: Session, user_ids: list[int], *, today=None) -> dict:
    """Display-only activity, never unique-solve totals or scoring evidence.

    Overlapping sources use max per platform/day before summing platforms.
    Calendars can include attempts/repeats. Legacy rows belong only to the
    original account generation.
    """
    from .models import User, ProviderCalendar
    from .reconciliation import proved_date
    from .timekeeping import ist_date, ist_today, utc_now
    today = today or ist_today()
    now = utc_now()
    by_platform = defaultdict(lambda: defaultdict(int))
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts

    def merge(user_id, platform, day, count):
        if day <= today and count > 0:
            key = (platform, day)
            by_platform[user_id][key] = max(by_platform[user_id][key], count)

    verified = defaultdict(int)
    for solve, user in db.query(Solve, User).join(User, User.id == Solve.user_id).filter(
            Solve.user_id.in_(user_ids), Solve.first_solve_verified.is_(True), Solve.first_solve_at.isnot(None)).all():
        instant = proved_date(user, solve)
        if instant is not None and instant <= now:
            verified[(user.id, solve.platform, ist_date(instant))] += 1
    for (user_id, platform, day), count in verified.items():
        merge(user_id, platform, day, count)
    for user_id, day, count in db.query(DailyActivity.user_id, DailyActivity.date, DailyActivity.problems_solved).join(
            User, User.id == DailyActivity.user_id).filter(
            User.id.in_(user_ids), User.leetcode_account_version == 0, DailyActivity.date <= today):
        merge(user_id, "leetcode", day, count)
    for user_id, day, count in db.query(PlatformActivity.user_id, PlatformActivity.date, PlatformActivity.problems_solved).join(
            User, User.id == PlatformActivity.user_id).filter(
            User.id.in_(user_ids), User.codeforces_account_version == 0,
            User.codeforces_username.isnot(None), PlatformActivity.platform == "codeforces", PlatformActivity.date <= today):
        merge(user_id, "codeforces", day, count)
    for user_id, day, count in db.query(ProviderCalendar.user_id, ProviderCalendar.date, ProviderCalendar.submission_count).join(
            User, User.id == ProviderCalendar.user_id).filter(
            User.id.in_(user_ids), ProviderCalendar.platform == "leetcode",
            ProviderCalendar.account_version == User.leetcode_account_version,
            ProviderCalendar.source == "leetcode_submission_calendar", ProviderCalendar.date <= today):
        merge(user_id, "leetcode", day, count)
    for user_id, days in by_platform.items():
        for (_, day), count in days.items():
            counts[user_id][day] += count
    return counts
