from collections import defaultdict
from sqlalchemy.orm import Session
from .models import DailyActivity, PlatformActivity, Solve


def daily_counts(db: Session, user_ids: list[int]) -> dict:
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts
    # Calendar activity and imported timestamps cannot establish first solves.
    from .timekeeping import ist_date
    rows = db.query(Solve).filter(Solve.user_id.in_(user_ids),
                                  Solve.first_solve_verified.is_(True),
                                  Solve.first_solve_at.isnot(None)).all()
    for row in rows:
        counts[row.user_id][ist_date(row.first_solve_at)] += 1
    return counts


def solve_url(solve: Solve) -> str:
    return solve.problem_url or f"https://leetcode.com/problems/{solve.title_slug}/"
