from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy import Date, cast, func, or_
from sqlalchemy.orm import Session
from .models import DailyActivity, PlatformActivity, Solve


def verified_daily_counts(db: Session, user_ids: list[int]) -> dict:
    """Transfer daily totals, not full solves and repeated User records.

    Keep exact Python casefold account matching after aggregation: SQL lower()
    does not have the same Unicode semantics as the existing identity policy.
    """
    from .models import User
    from .first_solves import current_account
    from .timekeeping import utc_now
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts
    users = {row.id: row for row in db.query(
        User.id, User.leetcode_username, User.codeforces_username,
        User.leetcode_account_version, User.codeforces_account_version,
    ).filter(User.id.in_(user_ids))}
    if db.get_bind().dialect.name == "sqlite":
        day = func.date(Solve.first_solve_at, "+330 minutes")
    else:
        # first_solve_at is a naive UTC timestamp, independent of DB session TZ.
        day = cast(Solve.first_solve_at + timedelta(hours=5, minutes=30), Date)
    rows = db.query(
        Solve.user_id, Solve.platform, Solve.account_version, Solve.source_handle,
        day.label("day"), func.count(Solve.id).label("solve_count"),
    ).filter(
        Solve.user_id.in_(user_ids), Solve.first_solve_at <= utc_now(),
        Solve.source_handle.isnot(None), Solve.source_handle != "",
        or_(Solve.first_solve_verified.is_(True),
            (Solve.platform == "leetcode") & (Solve.first_solve_basis == "database_first")),
    ).group_by(Solve.user_id, Solve.platform, Solve.account_version, Solve.source_handle, day)
    for row in rows:
        user = users.get(row.user_id)
        if user is not None and current_account(user, row):
            solved_day = date.fromisoformat(row.day) if isinstance(row.day, str) else row.day
            counts[row.user_id][(row.platform, solved_day)] += row.solve_count
    return counts


def daily_counts(db: Session, user_ids: list[int], *, verified=None) -> dict:
    counts = defaultdict(lambda: defaultdict(int))
    verified = verified_daily_counts(db, user_ids) if verified is None else verified
    for user_id, days in verified.items():
        for (_, day), count in days.items():
            counts[user_id][day] += count
    return counts


def solve_url(solve: Solve) -> str:
    return solve.problem_url or f"https://leetcode.com/problems/{solve.title_slug}/"


def streak_dates(db: Session, user_ids: list[int], *, today=None, verified_counts=None) -> dict:
    """Temporary display compatibility while first-solve history is incomplete.

    Calendar activity can include repeats/attempts. It is never unique-solve
    evidence. From the November 14 policy cutover, new award multipliers use
    this same profile streak; reward eligibility still requires accepted solves.
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


def activity_counts(db: Session, user_ids: list[int], *, today=None, verified=None, since=None) -> dict:
    """Display-only activity, never unique-solve totals or scoring evidence.

    Overlapping sources use max per platform/day before summing platforms.
    Calendars can include attempts/repeats. Legacy rows belong only to the
    original account generation.
    """
    from .models import User, ProviderCalendar
    from .timekeeping import ist_today
    today = today or ist_today()
    by_platform = defaultdict(lambda: defaultdict(int))
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts

    def merge(user_id, platform, day, count):
        if day <= today and (since is None or day >= since) and count > 0:
            key = (platform, day)
            by_platform[user_id][key] = max(by_platform[user_id][key], count)

    verified = verified_daily_counts(db, user_ids) if verified is None else verified
    for user_id, days in verified.items():
        for (platform, day), count in days.items():
            merge(user_id, platform, day, count)
    for user_id, day, count in db.query(DailyActivity.user_id, DailyActivity.date, DailyActivity.problems_solved).join(
            User, User.id == DailyActivity.user_id).filter(
            User.id.in_(user_ids), User.leetcode_account_version == 0, DailyActivity.date <= today,
            *([DailyActivity.date >= since] if since is not None else [])):
        merge(user_id, "leetcode", day, count)
    for user_id, day, count in db.query(PlatformActivity.user_id, PlatformActivity.date, PlatformActivity.problems_solved).join(
            User, User.id == PlatformActivity.user_id).filter(
            User.id.in_(user_ids), User.codeforces_account_version == 0,
            User.codeforces_username.isnot(None), PlatformActivity.platform == "codeforces", PlatformActivity.date <= today,
            *([PlatformActivity.date >= since] if since is not None else [])):
        merge(user_id, "codeforces", day, count)
    for user_id, day, count in db.query(ProviderCalendar.user_id, ProviderCalendar.date, ProviderCalendar.submission_count).join(
            User, User.id == ProviderCalendar.user_id).filter(
            User.id.in_(user_ids), ProviderCalendar.platform == "leetcode",
            ProviderCalendar.account_version == User.leetcode_account_version,
            ProviderCalendar.source == "leetcode_submission_calendar", ProviderCalendar.date <= today,
            *([ProviderCalendar.date >= since] if since is not None else [])):
        merge(user_id, "leetcode", day, count)
    for user_id, days in by_platform.items():
        for (_, day), count in days.items():
            counts[user_id][day] += count
    return counts
