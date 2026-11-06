"""Internal evidence storage. Client plan checks are never score evidence."""
import math
from datetime import datetime
from sqlalchemy.orm import Session

from .models import AcceptedSubmission, DailyActivity, PlatformActivity, ScoreSnapshot, Solve, User, PointAward
from .timekeeping import utc_storage, utc_now


def safe_number(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {"invalid_numeric": str(value)}
    return value


def clear_tracking(db: Session, user_id: int | None = None, platform: str | None = None):
    """Use before deleting solve/account rows, including on local SQLite."""
    if platform is not None and platform not in {"leetcode", "codeforces"}:
        raise ValueError("Invalid platform")
    awards = db.query(PointAward)
    events = db.query(AcceptedSubmission)
    snapshots = db.query(ScoreSnapshot)
    solves = db.query(Solve.id)
    if user_id is not None:
        awards = awards.filter(PointAward.user_id == user_id)
        events = events.filter(AcceptedSubmission.user_id == user_id)
        snapshots = snapshots.filter(ScoreSnapshot.user_id == user_id)
        solves = solves.filter(Solve.user_id == user_id)
    if platform is not None:
        awards = awards.filter(PointAward.solve_id.in_(solves.filter(Solve.platform == platform)))
        events = events.filter(AcceptedSubmission.platform == platform)
    awards.delete(synchronize_session=False)
    events.delete(synchronize_session=False)
    if platform is None:
        snapshots.delete(synchronize_session=False)


def capture_score_baseline(db: Session, user_id: int) -> ScoreSnapshot:
    """Call before reconciliation, in the caller's transaction; never overwrite."""
    user = db.query(User).filter(User.id == user_id).populate_existing().with_for_update().one()
    key = f"tracking-v1:{user.id}"
    existing = db.query(ScoreSnapshot).filter_by(snapshot_key=key).first()
    if existing:
        return existing
    solves = db.query(Solve).filter_by(user_id=user.id).order_by(Solve.id).all()
    snapshot = ScoreSnapshot(snapshot_key=key, user_id=user.id, reason="tracking-v1", payload={
        "format_version": 1,
        "points": safe_number(user.points),
        "difficulty_counts": {"easy": user.easy_count, "medium": user.medium_count, "hard": user.hard_count},
        "official_streak": user.official_streak,
        "solves": [{
            "id": solve.id, "platform": solve.platform, "title_slug": solve.title_slug,
            "account_version": solve.account_version,
            "source_handle": solve.source_handle, "scoring_version": solve.scoring_version,
            "solved_at": solve.solved_at.isoformat(), "is_daily": solve.is_daily,
            "points_earned": safe_number(solve.points_earned), "difficulty": solve.difficulty,
            "ac_rate": safe_number(solve.ac_rate), "problem_rating": safe_number(solve.problem_rating),
        } for solve in solves],
        "calendar_activity": [{"date": row.date.isoformat(), "count": row.problems_solved}
                              for row in db.query(DailyActivity).filter_by(user_id=user.id).order_by(DailyActivity.date).all()],
        "platform_activity": [{"platform": row.platform, "date": row.date.isoformat(), "count": row.problems_solved}
                              for row in db.query(PlatformActivity).filter_by(user_id=user.id).order_by(PlatformActivity.platform, PlatformActivity.date).all()],
    })
    db.add(snapshot)
    db.flush()
    return snapshot


def record_acceptance(db: Session, user_id: int, *, platform: str, account_version: int,
                      submission_id: str, title_slug: str, accepted_at: datetime,
                      evidence_kind: str, first_solve_verified: bool = False) -> AcceptedSubmission:
    """Record a provider-verified acceptance once, without awarding any points."""
    if platform not in {"leetcode", "codeforces"} or not isinstance(submission_id, str) or not submission_id or len(submission_id) > 80:
        raise ValueError("Invalid accepted submission identity")
    if not isinstance(title_slug, str) or not title_slug or len(title_slug) > 200:
        raise ValueError("Invalid problem identity")
    if evidence_kind not in {"public_recent", "provider_full", "provider_live"}:
        raise ValueError("Only provider evidence may enter the scoring ledger")
    if type(account_version) is not int or account_version < 0 or not isinstance(accepted_at, datetime):
        raise ValueError("Invalid accepted submission evidence")
    if first_solve_verified and evidence_kind == "public_recent":
        raise ValueError("Recent submissions alone cannot prove a first solve")
    user = db.query(User).filter_by(id=user_id).populate_existing().with_for_update().one()
    if getattr(user, platform + "_account_version") != account_version:
        raise ValueError("The linked coding account changed during sync")
    accepted_at = utc_storage(accepted_at)
    existing = db.query(AcceptedSubmission).filter_by(user_id=user_id, platform=platform,
                 account_version=account_version, submission_id=submission_id).first()
    if existing:
        if existing.title_slug != title_slug or existing.accepted_at != accepted_at:
            raise ValueError("Conflicting provider submission evidence")
        return existing
    event = AcceptedSubmission(user_id=user_id, platform=platform, account_version=account_version,
             submission_id=submission_id, title_slug=title_slug, accepted_at=accepted_at,
             observed_at=utc_now(), evidence_kind=evidence_kind,
             first_solve_verified=first_solve_verified)
    db.add(event)
    db.flush()
    return event


def award_live_revision(db: Session, solve: Solve, event: AcceptedSubmission, live_since: datetime | None):
    """Reward only newly observed live repeats; history imports never mint revisions."""
    from .timekeeping import revision_due, ist_date
    from .platforms import daily_counts
    from .streak import current_streak
    from .scoring import revision_points, SCORING_VERSION
    if live_since is None or event.accepted_at < utc_storage(live_since).replace(microsecond=0):
        return None
    latest = db.query(PointAward).filter_by(solve_id=solve.id, kind="revision").order_by(PointAward.earned_at.desc()).first()
    anchor = latest.earned_at if latest else (solve.first_solve_at or solve.solved_at)
    if anchor is None or not revision_due(event.accepted_at, anchor):
        return None
    key = f"revision:{solve.id}:{event.id}"
    existing = db.query(PointAward).filter_by(award_key=key).first()
    if existing:
        return existing
    streak = current_streak(set(daily_counts(db, [solve.user_id])[solve.user_id]), ist_date(event.accepted_at))
    award = PointAward(award_key=key, user_id=solve.user_id, solve_id=solve.id,
                       submission_id=event.id, kind="revision", points=revision_points(streak),
                       earned_at=event.accepted_at, scoring_version=SCORING_VERSION,
                       input_snapshot={"streak_days": streak, "anchor_time": anchor.isoformat(),
                                       "accepted_at": event.accepted_at.isoformat()})
    db.add(award)
    db.flush()
    return award
