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
from .models import User, Solve, DailyActivity
from .streak import current_streak

logger = logging.getLogger("codestreak.points")


def compute_solve_points(
    title_slug: str = "",
    difficulty: Optional[str] = None,
    ac_rate: Optional[float] = None,
    is_daily: bool = False,
    is_first_try: bool = True,
    streak_days: int = 0,
) -> float:
    """
    Computes exact float points for a single problem solve based on Rulebook scale.
    """
    rating = get_contest_rating(title_slug)

    if rating is not None and rating > 0:
        # Option 1: Rating / 100 (e.g. 1550 rating -> 15.5 pts, 2400 -> 24.0 pts)
        base_points = rating / 100.0
    else:
        # Option 3 Fallback (Easy: 8, Medium: 15, Hard: 24)
        diff_str = (difficulty or "Medium").capitalize()
        category_bases = {"Easy": 8.0, "Medium": 15.0, "Hard": 24.0}
        cat_base = category_bases.get(diff_str, 15.0)

        if ac_rate is not None and 0.0 <= ac_rate <= 100.0:
            ac_multiplier = 1.0 + ((50.0 - ac_rate) / 100.0)
            base_points = cat_base * max(0.2, ac_multiplier)
        else:
            base_points = cat_base

    # Additive bonuses (Daily: +5.0, First-Try: +3.0)
    daily_bonus = 5.0 if is_daily else 0.0
    first_try_bonus = 3.0 if is_first_try else 0.0

    subtotal = base_points + daily_bonus + first_try_bonus

    # Streak Multiplier (1.0x to 1.10x max capped at 30 days)
    streak_capped = min(30, max(0, streak_days))
    streak_multiplier = 1.0 + (0.10 * (streak_capped / 30.0))

    final_points = subtotal * streak_multiplier
    return round(final_points, 4)


def compute_solve_points_breakdown(
    title_slug: str = "",
    difficulty: Optional[str] = None,
    ac_rate: Optional[float] = None,
    is_daily: bool = False,
    is_first_try: bool = True,
    streak_days: int = 0,
) -> dict:
    """Returns detailed breakdown components for a solve."""
    rating = get_contest_rating(title_slug)

    diff_str = (difficulty or "Medium").capitalize()
    category_bases = {"Easy": 8.0, "Medium": 15.0, "Hard": 24.0}
    cat_base = category_bases.get(diff_str, 15.0)

    if rating is not None and rating > 0:
        raw_base_points = round(rating / 100.0, 2)
        ac_multiplier = 1.0
        ac_adjustment = 0.0
        base_points = raw_base_points
    else:
        raw_base_points = cat_base
        if ac_rate is not None and 0.0 <= ac_rate <= 100.0:
            ac_mult_raw = max(0.2, 1.0 + ((50.0 - ac_rate) / 100.0))
            ac_multiplier = round(ac_mult_raw, 2)
            base_points = round(cat_base * ac_mult_raw, 2)
            ac_adjustment = round(base_points - cat_base, 2)
        else:
            ac_multiplier = 1.0
            ac_adjustment = 0.0
            base_points = cat_base

    daily_bonus = 5.0 if is_daily else 0.0
    first_try_bonus = 3.0 if is_first_try else 0.0

    subtotal = round(base_points + daily_bonus + first_try_bonus, 2)

    streak_capped = min(30, max(0, streak_days))
    streak_multiplier = round(1.0 + (0.10 * (streak_capped / 30.0)), 2)

    total_float = subtotal * streak_multiplier
    points_earned = int(round(total_float))

    return {
        "difficulty": diff_str,
        "raw_base_points": raw_base_points,
        "ac_rate": ac_rate,
        "ac_multiplier": ac_multiplier,
        "ac_adjustment": ac_adjustment,
        "base_points": base_points,
        "contest_rating": rating,
        "is_daily": is_daily,
        "daily_bonus": daily_bonus,
        "is_first_try": is_first_try,
        "first_try_bonus": first_try_bonus,
        "subtotal": subtotal,
        "streak_days": streak_days,
        "streak_multiplier": streak_multiplier,
        "points_earned": points_earned,
    }


def recalculate_user_points(
    user: User,
    db: Session,
    today_daily_slug: Optional[str] = None,
    attempts_map: Optional[dict] = None,
) -> float:
    """
    Recalculates a single user's total points based on their solves ledger
    and total difficulty counts, accounting for daily challenge bonus and attempt tracking.
    Uses the exact streak active on the date each problem was solved.
    """
    solves = db.query(Solve).filter(Solve.user_id == user.id).all()
    user_streak = user.official_streak or 0

    active_dates = {
        r.date for r in db.query(DailyActivity.date).filter(
            DailyActivity.user_id == user.id,
            DailyActivity.problems_solved > 0
        ).all()
    }

    total_points = 0.0
    for solve in solves:
        slug = solve.title_slug or ""
        is_daily = bool(today_daily_slug and slug.lower() == today_daily_slug.lower())

        is_first_try = True
        if attempts_map and isinstance(attempts_map, dict) and slug in attempts_map:
            is_first_try = bool(attempts_map[slug].get("is_first_try", True))

        solve_date = solve.solved_at.date() if hasattr(solve.solved_at, "date") else solve.solved_at
        streak_on_date = current_streak(active_dates, solve_date)

        pts = compute_solve_points(
            title_slug=slug,
            difficulty=solve.difficulty,
            ac_rate=solve.ac_rate,
            is_daily=is_daily,
            is_first_try=is_first_try,
            streak_days=streak_on_date,
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

        streak_mult = 1.0 + (0.10 * (min(30, max(0, user_streak)) / 30.0))
        legacy_pts += unlogged_easy * compute_solve_points(difficulty="Easy", streak_days=0) * streak_mult
        legacy_pts += unlogged_med * compute_solve_points(difficulty="Medium", streak_days=0) * streak_mult
        legacy_pts += unlogged_hard * compute_solve_points(difficulty="Hard", streak_days=0) * streak_mult

    final_total = round(total_points + legacy_pts, 2)
    user.points = final_total
    return final_total


async def recalculate_all_users_points(db: Session) -> int:
    """
    Updates total points for all users in the database.
    """
    from .leetcode_client import fetch_today_daily_challenge_slug
    today_daily_slug = await fetch_today_daily_challenge_slug()
    users = db.query(User).all()
    count = 0
    for u in users:
        recalculate_user_points(u, db, today_daily_slug=today_daily_slug)
        count += 1
    db.commit()
    logger.info("Recalculated points for %d users.", count)
    return count
