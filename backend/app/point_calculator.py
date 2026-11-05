"""
Dynamic LeetCode Point Calculation Engine.

Rules:
1. Base Points:
   - Primary (Option 1): If problem has contest rating (800..3500), Base = Rating / 100
   - Fallback (Option 3): Category Base (Easy: 8, Medium: 15, Hard: 24) * (1 + (50 - AC_Rate) / 100)
2. Additive Bonuses:
   - LeetCode Daily Bonus: +5.0 pts
3. Multipliers:
   - Streak Multiplier: 1.0 + (0.10 * min(1.0, max(0.0, streak_days) / 30.0)) (Capped at 1.10x for 30+ days)
4. Final Score = (Base + Bonuses) * StreakMultiplier
"""

import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from .contest_ratings import get_contest_rating
from datetime import date, timezone
from .models import User, Solve, DailyActivity, DailyChallenge, PointAward
from .streak import current_streak, IST
from .tracking import capture_score_baseline
from .scoring import calculate_points, rounded, SCORING_VERSION
from .timekeeping import ist_date, ist_today

logger = logging.getLogger("codestreak.points")


def compute_solve_points(
    title_slug: str = "",
    difficulty: Optional[str] = None,
    ac_rate: Optional[float] = None,
    is_daily: bool = False,
    streak_days: int = 0,
    platform: str = "leetcode",
    rating: Optional[float] = None,
) -> float:
    """
    Computes exact float points for a single problem solve based on Rulebook scale.
    """
    if platform == "leetcode":
        if rating is None:
            rating = get_contest_rating(title_slug)
        raw_diff = difficulty.capitalize() if isinstance(difficulty, str) else None
        diff = raw_diff if raw_diff in {"Easy", "Medium", "Hard"} else ("Medium" if rating is None else None)
        res = calculate_points(
            platform="leetcode",
            difficulty=diff,
            rating=rating,
            ac_rate=ac_rate,
            streak_days=streak_days,
            daily_eligible=is_daily,
        )
    elif platform == "codeforces":
        res = calculate_points(
            platform="codeforces",
            rating=rating,
            streak_days=streak_days,
        )
    else:
        raise ValueError("Unknown scoring platform")
    return float(res["points_earned"])


def compute_solve_points_breakdown(
    title_slug: str = "",
    difficulty: Optional[str] = None,
    ac_rate: Optional[float] = None,
    is_daily: bool = False,
    streak_days: int = 0,
    platform: str = "leetcode",
    rating: Optional[float] = None,
) -> dict:
    """Returns detailed breakdown components for a solve."""
    if platform == "leetcode":
        if rating is None:
            rating = get_contest_rating(title_slug)
        raw_diff = difficulty.capitalize() if isinstance(difficulty, str) else None
        diff = raw_diff if raw_diff in {"Easy", "Medium", "Hard"} else ("Medium" if rating is None else None)
        res = calculate_points(
            platform="leetcode",
            difficulty=diff,
            rating=rating,
            ac_rate=ac_rate,
            streak_days=streak_days,
            daily_eligible=is_daily,
        )
    elif platform == "codeforces":
        res = calculate_points(
            platform="codeforces",
            rating=rating,
            streak_days=streak_days,
        )
    else:
        raise ValueError("Unknown scoring platform")

    raw_base = float(res["raw_base_points"])
    base = float(res["base_points"])
    ac_adj = round(base - raw_base, 4)
    multiplier = float(res["streak_multiplier"])
    daily_bonus = float(res["daily_award"])
    subtotal = round(base + (5.0 if is_daily else 0.0), 4)

    return {
        "difficulty": difficulty or ("Rated" if rating is not None else "Medium"),
        "raw_base_points": raw_base,
        "ac_rate": float(res["ac_rate"]) if res["ac_rate"] is not None else None,
        "ac_multiplier": float(res["ac_multiplier"]),
        "ac_adjustment": ac_adj,
        "base_points": base,
        "contest_rating": float(res["contest_rating"]) if res["contest_rating"] is not None else None,
        "is_daily": is_daily,
        "daily_bonus": daily_bonus,
        "subtotal": subtotal,
        "streak_days": streak_days,
        "streak_multiplier": multiplier,
        "points_earned": float(res["points_earned"]),
    }


def compute_codeforces_points_breakdown(rating: Optional[float], streak_days: int = 0) -> dict:
    """Version cf-linear-v1: calibrated base + existing capped streak multiplier."""
    res = calculate_points(platform="codeforces", rating=rating, streak_days=streak_days)
    base = float(res["base_points"])
    multiplier = float(res["streak_multiplier"])
    return {
        "difficulty": "Rated" if rating is not None else "Unrated",
        "raw_base_points": base,
        "ac_rate": None,
        "ac_multiplier": 1.0,
        "ac_adjustment": 0.0,
        "base_points": base,
        "contest_rating": rating,
        "is_daily": False,
        "daily_bonus": 0.0,
        "subtotal": base,
        "streak_days": streak_days,
        "streak_multiplier": multiplier,
        "points_earned": float(res["points_earned"]),
    }


def recalculate_user_points(
    user: User,
    db: Session,
    today_daily_slug: Optional[str] = None,
) -> float:
    """
    Recalculates a single user's total points based on their solves ledger,
    capturing a protected baseline, persisting exact PointAward rows,
    preserving earned daily bonuses, and computing unlogged historical solves
    as base-only credit.
    """
    db.flush()
    db.query(User.id).filter(User.id == user.id).with_for_update().one()

    capture_score_baseline(db, user.id)

    solves = db.query(Solve).filter(Solve.user_id == user.id).all()
    user_streak = user.official_streak or 0

    daily_slugs_by_date = {
        r.date: r.title_slug.lower()
        for r in db.query(DailyChallenge).all()
    }

    from .platforms import daily_counts

    active_dates = set(daily_counts(db, [user.id])[user.id])
    total_points = Decimal("0")
    leetcode_solves = [s for s in solves if s.platform == "leetcode"]

    for solve in solves:
        solve_date = ist_date(solve.first_solve_at or solve.solved_at)
        streak_on_date = current_streak(active_dates, solve_date)

        if solve.platform == "codeforces":
            calc = calculate_points(platform="codeforces", rating=solve.problem_rating, streak_days=streak_on_date)
            base_award = calc["base_award"]
            solve.points_earned = float(base_award)
            solve.scoring_version = calc["scoring_version"]
            solve.score_components_state = "points-components-v2"

            award_key = f"base:{solve.id}"
            award = db.query(PointAward).filter_by(award_key=award_key).first()
            if not award:
                award = PointAward(
                    award_key=award_key,
                    user_id=user.id,
                    solve_id=solve.id,
                    kind="base",
                    points=base_award,
                    earned_at=solve.first_solve_at or solve.solved_at,
                    scoring_version=calc["scoring_version"],
                    input_snapshot={"rating": solve.problem_rating, "streak_days": streak_on_date},
                )
                db.add(award)
            else:
                award.points = base_award
                award.scoring_version = calc["scoring_version"]
            total_points += base_award
            continue

        slug = (solve.title_slug or "").lower()
        is_daily = (
            bool(getattr(solve, "is_daily", False))
            or bool(today_daily_slug and solve_date == ist_today() and slug == today_daily_slug.lower())
            or bool(solve_date in daily_slugs_by_date and slug == daily_slugs_by_date[solve_date])
        )
        if is_daily and not getattr(solve, "is_daily", False):
            solve.is_daily = True

        rating = get_contest_rating(solve.title_slug)
        raw_diff = solve.difficulty.capitalize() if isinstance(solve.difficulty, str) else None
        diff = raw_diff if raw_diff in {"Easy", "Medium", "Hard"} else ("Medium" if rating is None else None)

        calc = calculate_points(
            platform="leetcode",
            difficulty=diff,
            rating=rating,
            ac_rate=solve.ac_rate,
            streak_days=streak_on_date,
            daily_eligible=is_daily,
        )

        base_award = calc["base_award"]
        daily_award = calc["daily_award"]

        base_key = f"base:{solve.id}"
        base_row = db.query(PointAward).filter_by(award_key=base_key).first()
        if not base_row:
            base_row = PointAward(
                award_key=base_key,
                user_id=user.id,
                solve_id=solve.id,
                kind="base",
                points=base_award,
                earned_at=solve.first_solve_at or solve.solved_at,
                scoring_version=calc["scoring_version"],
                input_snapshot={"difficulty": diff, "rating": rating, "ac_rate": solve.ac_rate, "streak_days": streak_on_date},
            )
            db.add(base_row)
        else:
            base_row.points = base_award
            base_row.scoring_version = calc["scoring_version"]

        if daily_award > Decimal("0"):
            daily_key = f"daily:{solve.id}"
            daily_row = db.query(PointAward).filter_by(award_key=daily_key).first()
            if not daily_row:
                daily_row = PointAward(
                    award_key=daily_key,
                    user_id=user.id,
                    solve_id=solve.id,
                    kind="daily",
                    points=daily_award,
                    earned_at=solve.first_solve_at or solve.solved_at,
                    scoring_version=calc["scoring_version"],
                    input_snapshot={"challenge_date": str(solve_date), "streak_days": streak_on_date},
                )
                db.add(daily_row)
            else:
                daily_row.points = daily_award
                daily_row.scoring_version = calc["scoring_version"]

        rev_awards = db.query(PointAward).filter_by(solve_id=solve.id, kind="revision").all()
        rev_total = sum((a.points for a in rev_awards), Decimal("0"))

        solve_pts = base_award + daily_award + rev_total
        solve.points_earned = float(solve_pts)
        solve.scoring_version = calc["scoring_version"]
        solve.score_components_state = "points-components-v2"
        total_points += solve_pts

    # Unlogged historical LeetCode solves (base credit only: multiplier 1.0, no daily)
    num_solves_logged = len(leetcode_solves)
    total_known_solves = (user.easy_count or 0) + (user.medium_count or 0) + (user.hard_count or 0)
    legacy_pts = Decimal("0")
    if total_known_solves > num_solves_logged and total_known_solves > 0:
        unlogged_ratio = Decimal(str(total_known_solves - num_solves_logged)) / Decimal(str(total_known_solves))
        unlogged_easy = Decimal(str(user.easy_count or 0)) * unlogged_ratio
        unlogged_med = Decimal(str(user.medium_count or 0)) * unlogged_ratio
        unlogged_hard = Decimal(str(user.hard_count or 0)) * unlogged_ratio
        legacy_pts = rounded(unlogged_easy * Decimal(8) + unlogged_med * Decimal(15) + unlogged_hard * Decimal(24))

    final_total = float(rounded(total_points + legacy_pts))
    user.points = final_total
    db.flush()
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

