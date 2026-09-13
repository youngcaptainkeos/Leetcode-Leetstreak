"""
Dynamic LeetCode Point Calculation Engine.

Rules:
1. Base Points:
   - Primary (Option 1): If problem has contest rating (800..3500), Base = Rating / 100
   - Fallback (Option 3): Category Base (Easy: 10, Medium: 25, Hard: 45) * (1 + (50 - AC_Rate) / 100)
2. Additive Bonuses:
   - LeetCode Daily Bonus: +10.0 pts
   - First-Try Bonus (0 failed submissions): +5.0 pts
3. Multipliers:
   - Streak Multiplier: 1.0 + (0.25 * min(1.0, max(0.0, streak_days) / 30.0)) (Capped at 1.25x for 30+ days)
4. Final Score = (Base + Bonuses) * StreakMultiplier
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from .contest_ratings import get_contest_rating
from .models import User, Solve

logger = logging.getLogger("codestreak.points")


def compute_solve_points(
    title_slug: str = "",
    difficulty: Optional[str] = None,
    ac_rate: Optional[float] = None,
    is_daily: bool = False,
    is_first_try: bool = False,
    streak_days: int = 0,
) -> float:
    """
    Computes exact float points for a single problem solve (scaled down ~10x).
    """
    rating = get_contest_rating(title_slug)

    if rating is not None and rating > 0:
        # Option 1: Rating / 1000 (e.g. 1550 rating -> 1.55 pts, 2400 -> 2.4 pts)
        base_points = rating / 1000.0
    else:
        # Option 3 Fallback (Easy: 1.0, Medium: 2.5, Hard: 4.5)
        diff_str = (difficulty or "Medium").capitalize()
        category_bases = {"Easy": 1.0, "Medium": 2.5, "Hard": 4.5}
        cat_base = category_bases.get(diff_str, 2.5)

        rate = ac_rate if (ac_rate is not None and 0.0 <= ac_rate <= 100.0) else 45.0
        ac_multiplier = 1.0 + ((50.0 - rate) / 100.0)
        base_points = cat_base * max(0.2, ac_multiplier)

    # Additive bonuses
    daily_bonus = 1.0 if is_daily else 0.0
    first_try_bonus = 0.5 if is_first_try else 0.0

    subtotal = base_points + daily_bonus + first_try_bonus

    # Streak Multiplier (1.0x to 1.25x capped at 30 days)
    streak_capped = min(30, max(0, streak_days))
    streak_multiplier = 1.0 + (0.25 * (streak_capped / 30.0))

    final_points = subtotal * streak_multiplier
    return round(final_points, 4)


def recalculate_user_points(user: User, db: Session) -> float:
    """
    Recalculates a single user's total points based on their solves ledger
    and total difficulty counts.
    """
    solves = db.query(Solve).filter(Solve.user_id == user.id).all()
    user_streak = user.official_streak or 0

    total_points = 0.0
    for solve in solves:
        slug = solve.title_slug or ""
        pts = compute_solve_points(
            title_slug=slug,
            difficulty=None,
            ac_rate=None,
            is_daily=False,
            is_first_try=True,
            streak_days=user_streak,
        )
        solve.points_earned = pts
        total_points += pts

    # Handle remaining problem counts not explicitly logged in solves table
    # Base fallback if solves ledger has fewer items than total count
    num_solves_logged = len(solves)
    total_known_solves = (user.easy_count or 0) + (user.medium_count or 0) + (user.hard_count or 0)

    legacy_pts = 0.0
    if total_known_solves > num_solves_logged and total_known_solves > 0:
        # Ratio of unlogged solves
        unlogged_ratio = (total_known_solves - num_solves_logged) / float(total_known_solves)
        unlogged_easy = (user.easy_count or 0) * unlogged_ratio
        unlogged_med = (user.medium_count or 0) * unlogged_ratio
        unlogged_hard = (user.hard_count or 0) * unlogged_ratio

        streak_mult = 1.0 + (0.25 * (min(30, max(0, user_streak)) / 30.0))
        legacy_pts += unlogged_easy * compute_solve_points(difficulty="Easy", streak_days=0) * streak_mult
        legacy_pts += unlogged_med * compute_solve_points(difficulty="Medium", streak_days=0) * streak_mult
        legacy_pts += unlogged_hard * compute_solve_points(difficulty="Hard", streak_days=0) * streak_mult

    final_total = round(total_points + legacy_pts, 2)
    user.points = final_total
    return final_total


def recalculate_all_users_points(db: Session) -> int:
    """
    Updates total points for all users in the database.
    """
    users = db.query(User).all()
    count = 0
    for u in users:
        recalculate_user_points(u, db)
        count += 1
    db.commit()
    logger.info("Recalculated points for %d users.", count)
    return count
