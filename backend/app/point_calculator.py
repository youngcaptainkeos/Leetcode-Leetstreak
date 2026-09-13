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
    Computes exact float points for a single problem solve.
    """
    rating = get_contest_rating(title_slug)

    if rating is not None and rating > 0:
        # Option 1: Rating / 100 (e.g. 1550 rating -> 15.5 pts)
        base_points = rating / 100.0
    else:
        # Option 3 Fallback
        diff_str = (difficulty or "Medium").capitalize()
        category_bases = {"Easy": 10.0, "Medium": 25.0, "Hard": 45.0}
        cat_base = category_bases.get(diff_str, 25.0)

        rate = ac_rate if (ac_rate is not None and 0.0 <= ac_rate <= 100.0) else 45.0
        ac_multiplier = 1.0 + ((50.0 - rate) / 100.0)
        base_points = cat_base * max(0.2, ac_multiplier)

    # Additive bonuses
    daily_bonus = 10.0 if is_daily else 0.0
    first_try_bonus = 5.0 if is_first_try else 0.0

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
    processed_slugs = set()

    for solve in solves:
        slug = solve.title_slug or ""
        processed_slugs.add(slug)
        # Calculate points for each recorded solve
        pts = compute_solve_points(
            title_slug=slug,
            difficulty=None,  # Will fallback or lookup rating
            ac_rate=None,
            is_daily=False,
            is_first_try=True,  # Logged solves default to accepted first try
            streak_days=user_streak,
        )
        solve.points_earned = pts
        total_points += pts

    # Handle remaining problem counts not explicitly logged in solves table
    easy_remaining = max(0, (user.easy_count or 0) - len([s for s in solves if False]))
    medium_remaining = max(0, (user.medium_count or 0) - len([s for s in solves if False]))
    hard_remaining = max(0, (user.hard_count or 0) - len([s for s in solves if False]))

    # For legacy/historical solve counts not in `solves` table, apply standard difficulty fallback points
    legacy_pts = 0.0
    # Apply streak multiplier to legacy solves as well
    streak_mult = 1.0 + (0.25 * (min(30, max(0, user_streak)) / 30.0))

    if easy_remaining > 0:
        base_easy = compute_solve_points(difficulty="Easy", streak_days=0)
        legacy_pts += easy_remaining * base_easy * streak_mult
    if medium_remaining > 0:
        base_med = compute_solve_points(difficulty="Medium", streak_days=0)
        legacy_pts += medium_remaining * base_med * streak_mult
    if hard_remaining > 0:
        base_hard = compute_solve_points(difficulty="Hard", streak_days=0)
        legacy_pts += hard_remaining * base_hard * streak_mult

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
