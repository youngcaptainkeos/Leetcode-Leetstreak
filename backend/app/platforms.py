from collections import defaultdict
from sqlalchemy.orm import Session
from .models import DailyActivity, PlatformActivity, Solve


def daily_counts(db: Session, user_ids: list[int], platform: str = "all") -> dict:
    counts = defaultdict(lambda: defaultdict(int))
    if not user_ids:
        return counts
    models = (DailyActivity,) if platform == "leetcode" else (PlatformActivity,) if platform == "codeforces" else (DailyActivity, PlatformActivity)
    for model in models:
        query = db.query(model).filter(model.user_id.in_(user_ids), model.problems_solved > 0)
        if platform == "codeforces":
            query = query.filter(PlatformActivity.platform == "codeforces")
        for row in query.all():
            counts[row.user_id][row.date] += row.problems_solved
    return counts


def solve_url(solve: Solve) -> str:
    return solve.problem_url or f"https://leetcode.com/problems/{solve.title_slug}/"


def platform_metrics(db: Session, user, today, week_start, month_start):
    from datetime import timedelta
    from sqlalchemy import func
    from .streak import current_streak
    lc_days = daily_counts(db, [user.id], "leetcode")[user.id]
    cf_days = daily_counts(db, [user.id], "codeforces")[user.id]
    combined = {day: lc_days.get(day, 0) + cf_days.get(day, 0) for day in set(lc_days) | set(cf_days)}
    cf_count, cf_rated, cf_points = db.query(func.count(Solve.id), func.count(Solve.problem_rating), func.coalesce(func.sum(Solve.points_earned), 0)).filter(Solve.user_id == user.id, Solve.platform == "codeforces").one()
    cf_points = round(float(cf_points), 2)
    lc_total = (user.easy_count or 0) + (user.medium_count or 0) + (user.hard_count or 0)
    result = {}
    for platform, days in (("all", combined), ("leetcode", lc_days), ("codeforces", cf_days)):
        lc = platform != "codeforces"
        cf = platform != "leetcode"
        result[platform] = {
            "current_streak": current_streak({day for day, count in days.items() if count > 0}, today),
            "today_count": days.get(today, 0),
            "weekly_total": sum(count for day, count in days.items() if week_start <= day <= today),
            "monthly_total": sum(count for day, count in days.items() if month_start <= day <= today),
            "total_solved": (lc_total if lc else 0) + (cf_count if cf else 0),
            "points": round(float(user.points or 0), 2) if platform == "all" else cf_points if cf else round(float(user.points or 0) - cf_points, 2),
            "easy_count": (user.easy_count or 0) if lc else 0,
            "medium_count": (user.medium_count or 0) if lc else 0,
            "hard_count": (user.hard_count or 0) if lc else 0,
            "codeforces_count": cf_count if cf else 0,
            "rated_count": cf_rated if cf else 0, "unrated_count": cf_count - cf_rated if cf else 0,
            "last_7_days": [{"date": today - timedelta(days=i), "problems_solved": days.get(today - timedelta(days=i), 0)} for i in range(6, -1, -1)],
        }
    return result
