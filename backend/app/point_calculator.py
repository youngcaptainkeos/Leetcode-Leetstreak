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
from typing import Callable
from sqlalchemy import func
from .models import User, Solve, DailyActivity, DailyChallenge, PointAward, JobCheckpoint
from .streak import current_streak, IST
from .tracking import capture_score_baseline
from .scoring import calculate_points, rounded, SCORING_VERSION
from .timekeeping import ist_date, ist_today, utc_now

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
    baseline = capture_score_baseline(db, user.id)
    original = {row["id"]: row for row in baseline.payload.get("solves", [])}
    solves = db.query(Solve).filter(Solve.user_id == user.id).all()
    from .platforms import daily_counts
    active_dates = set(daily_counts(db, [user.id])[user.id])
    total_points = Decimal("0")
    leetcode_solves = [s for s in solves if s.platform == "leetcode"]

    for solve in solves:
        awards = {row.kind: row for row in db.query(PointAward).filter_by(solve_id=solve.id).all()
                  if row.kind != "revision"}
        revisions = db.query(PointAward).filter_by(solve_id=solve.id, kind="revision").all()
        revision_total = sum((row.points for row in revisions), Decimal("0"))
        verified = bool(solve.first_solve_verified and solve.first_solve_at is not None)
        earned_at = solve.first_solve_at if verified else None
        streak_days = current_streak(active_dates, ist_date(earned_at)) if verified else 0
        old = original.get(solve.id, {})
        # Old combined daily totals cannot safely be split into base and bonus.
        # Preserve the original total instead of guessing a bonus during revaluation.
        protected = awards.get("legacy")
        old_total = old.get("points_earned")
        same_identity = (old.get("title_slug") == solve.title_slug and old.get("platform") == solve.platform
                         and old.get("account_version", 0) == solve.account_version)
        protect_original = (same_identity and old.get("is_daily") and old.get("scoring_version") != SCORING_VERSION
                            and isinstance(old_total, (int, float)) and old_total > 0)
        if protected or protect_original:
            if not protected:
                protected = PointAward(
                    award_key=f"legacy:{solve.id}", user_id=user.id, solve_id=solve.id,
                    kind="legacy", points=rounded(Decimal(str(old_total))), earned_at=None,
                    scoring_version=SCORING_VERSION,
                    input_snapshot={"state": "protected_legacy", "needs_reconciliation": True,
                                    "source": "tracking-v1"},
                )
                db.add(protected)
                # A previous reconciliation may have guessed these components.
                for kind in ("base", "daily"):
                    if kind in awards:
                        db.delete(awards[kind])
            solve.score_components_state = "protected_legacy"
            solve.points_earned = float(protected.points + revision_total)
            total_points += protected.points + revision_total
            continue

        rating = solve.problem_rating if solve.platform == "codeforces" else get_contest_rating(solve.title_slug)
        raw_diff = solve.difficulty.capitalize() if isinstance(solve.difficulty, str) else None
        # Metadata gaps receive no invented Medium classification. Keep old credit
        # until provider metadata is available, with no dated ranking award.
        if solve.platform == "leetcode" and rating is None and raw_diff not in {"Easy", "Medium", "Hard"}:
            solve.score_components_state = "metadata_incomplete"
            if "base" in awards:
                awards["base"].earned_at = None
            total_points += Decimal(str(solve.points_earned or 0))
            continue
        calc = calculate_points(platform=solve.platform, difficulty=raw_diff,
                                rating=rating, ac_rate=solve.ac_rate if solve.platform == "leetcode" else None,
                                streak_days=streak_days)
        base = awards.get("base")
        if base is None:
            base = PointAward(award_key=f"base:{solve.id}", user_id=user.id, solve_id=solve.id,
                              kind="base", points=calc["base_award"], earned_at=earned_at,
                              scoring_version=SCORING_VERSION, input_snapshot={})
            db.add(base)
        base.points = calc["base_award"]
        base.earned_at = earned_at
        base.scoring_version = SCORING_VERSION
        base.input_snapshot = {"difficulty": raw_diff, "rating": rating,
                               "ac_rate": solve.ac_rate, "streak_days": streak_days}
        # Existing earned daily/revision amounts are immutable. Reconciliation
        # never infers eligibility from a challenge archive or today's slug.
        daily = awards.get("daily")
        daily_total = daily.points if daily is not None else Decimal("0")
        solve.points_earned = float(base.points + daily_total + revision_total)
        solve.scoring_version = SCORING_VERSION
        solve.score_components_state = SCORING_VERSION if verified else "base_only_history"
        total_points += base.points + daily_total + revision_total

    # Subtract the known questions per difficulty, rather than spreading an
    # unknown fraction across all categories and changing their base credit.
    legacy_pts = Decimal("0")
    for category, field, base in (("Easy", "easy_count", 8), ("Medium", "medium_count", 15), ("Hard", "hard_count", 24)):
        logged = sum(1 for row in leetcode_solves if (row.difficulty or "").lower() == category.lower())
        missing = max(0, (getattr(user, field) or 0) - logged)
        legacy_pts += Decimal(missing * base)
    user.points = float(rounded(total_points + legacy_pts))
    db.flush()
    return user.points


class ReconciliationResult(dict):
    """Result dictionary that also evaluates as an integer for backwards compatibility."""
    def __int__(self):
        return int(self.get("total_processed", 0))

    def __index__(self):
        return int(self.get("total_processed", 0))


async def recalculate_all_users_points(
    db: Session,
    batch_size: int = 50,
    job_name: str = "reconcile-points-v2",
    resume: bool = True,
    force: bool = False,
    on_progress: Optional[Callable[[int, int, int], None]] = None,
) -> ReconciliationResult:
    """
    Updates total points for all users in bounded batches with progress checkpoints and restart recovery.
    """
    from .leetcode_client import fetch_today_daily_challenge_slug

    checkpoint = db.query(JobCheckpoint).filter(JobCheckpoint.job_name == job_name).first()
    if checkpoint:
        if checkpoint.status == "completed" and not force:
            logger.info("Reconciliation job %s already completed (%d users).", job_name, checkpoint.total_processed)
            return ReconciliationResult({
                "job_name": job_name,
                "status": "already_completed",
                "total_processed": checkpoint.total_processed,
                "batches": 0,
            })
        if force:
            checkpoint.last_processed_id = 0
            checkpoint.total_processed = 0
            checkpoint.status = "running"
            checkpoint.batch_size = batch_size
            checkpoint.started_at = utc_now()
            checkpoint.completed_at = None
            db.commit()
        elif resume and checkpoint.status in ("running", "failed", "pending"):
            checkpoint.status = "running"
            checkpoint.batch_size = batch_size
            db.commit()
    else:
        checkpoint = JobCheckpoint(
            job_name=job_name,
            last_processed_id=0,
            batch_size=batch_size,
            total_processed=0,
            status="running",
            started_at=utc_now(),
        )
        db.add(checkpoint)
        db.commit()

    total_users = db.query(func.count(User.id)).scalar() or 0
    today_daily_slug = await fetch_today_daily_challenge_slug()

    batches_count = 0
    while True:
        batch = (
            db.query(User)
            .filter(User.id > checkpoint.last_processed_id)
            .order_by(User.id)
            .limit(batch_size)
            .all()
        )
        if not batch:
            checkpoint.status = "completed"
            checkpoint.completed_at = utc_now()
            db.commit()
            break

        for u in batch:
            recalculate_user_points(u, db, today_daily_slug=today_daily_slug)

        checkpoint.last_processed_id = batch[-1].id
        checkpoint.total_processed += len(batch)
        checkpoint.updated_at = utc_now()
        db.commit()
        batches_count += 1

        if on_progress:
            on_progress(checkpoint.total_processed, total_users, batch[-1].id)

    logger.info("Reconciliation complete for %s: %d users processed in %d batches.", job_name, checkpoint.total_processed, batches_count)
    return ReconciliationResult({
        "job_name": job_name,
        "status": checkpoint.status,
        "total_processed": checkpoint.total_processed,
        "batches": batches_count,
    })


