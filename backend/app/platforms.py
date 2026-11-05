from collections import defaultdict
from sqlalchemy.orm import Session
from .models import DailyActivity, PlatformActivity, Solve


def daily_counts(db: Session, user_ids: list[int]) -> dict:
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts
    for model in (DailyActivity, PlatformActivity):
        for row in db.query(model).filter(model.user_id.in_(user_ids), model.problems_solved > 0).all():
            counts[row.user_id][row.date] += row.problems_solved
    return counts


def solve_url(solve: Solve) -> str:
    return solve.problem_url or f"https://leetcode.com/problems/{solve.title_slug}/"
