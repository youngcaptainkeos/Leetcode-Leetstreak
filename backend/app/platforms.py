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
