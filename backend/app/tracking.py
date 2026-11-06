"""Internal evidence storage. Client plan checks are never score evidence."""
import math
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from .models import AcceptedSubmission, AccountCredit, ProviderCalendar, DailyActivity, PlatformActivity, ScoreSnapshot, Solve, User, PointAward
from .timekeeping import utc_storage, utc_now, ist_date, revision_due
from .scoring import revision_points
from .streak import current_streak


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
    credits = db.query(AccountCredit)
    calendars = db.query(ProviderCalendar)
    solves = db.query(Solve.id)
    if user_id is not None:
        awards = awards.filter(PointAward.user_id == user_id)
        events = events.filter(AcceptedSubmission.user_id == user_id)
        snapshots = snapshots.filter(ScoreSnapshot.user_id == user_id)
        credits = credits.filter(AccountCredit.user_id == user_id)
        calendars = calendars.filter(ProviderCalendar.user_id == user_id)
        solves = solves.filter(Solve.user_id == user_id)
    if platform is not None:
        awards = awards.filter(PointAward.solve_id.in_(solves.filter(Solve.platform == platform)))
        events = events.filter(AcceptedSubmission.platform == platform)
        credits = credits.filter(AccountCredit.platform == platform)
        calendars = calendars.filter(ProviderCalendar.platform == platform)
    calendars.delete(synchronize_session=False)
    credits.delete(synchronize_session=False)
    awards.delete(synchronize_session=False)
    events.delete(synchronize_session=False)
    if platform is None:
        snapshots.delete(synchronize_session=False)


def capture_score_baseline(db: Session, user_id: int, *, snapshot_key: str | None = None, reason: str = "tracking-v1") -> ScoreSnapshot:
    """Call before reconciliation, in the caller's transaction; never overwrite."""
    user = db.query(User).filter(User.id == user_id).populate_existing().with_for_update().one()
    key = snapshot_key or f"tracking-v1:{user.id}"
    existing = db.query(ScoreSnapshot).filter_by(snapshot_key=key).first()
    if existing:
        return existing
    solves = db.query(Solve).filter_by(user_id=user.id).order_by(Solve.id).all()
    snapshot = ScoreSnapshot(snapshot_key=key, user_id=user.id, reason=reason, payload={
        "format_version": 2,
        "accounts": {platform: {"handle": getattr(user, platform + "_username"),
                                  "version": getattr(user, platform + "_account_version")}
                     for platform in ("leetcode", "codeforces")},
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
        "awards": [{"solve_id": row.solve_id, "kind": row.kind, "points": str(row.points)}
                   for row in db.query(PointAward).filter_by(user_id=user.id).all()],
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
    if type(first_solve_verified) is not bool:
        raise ValueError("First-solve proof must be explicit")
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


@dataclass(frozen=True)
class ProviderAcceptance:
    submission_id: str
    title_slug: str
    accepted_at: datetime


def validate_acceptances(submissions: list[ProviderAcceptance], platform: str):
    """Validate the entire provider batch before any account writes."""
    if platform not in {"leetcode", "codeforces"}:
        raise ValueError("Invalid platform")
    if not isinstance(submissions, list):
        raise ValueError("Invalid acceptance batch")
    identities = {}
    now = utc_now()
    for row in submissions:
        if (not isinstance(row, ProviderAcceptance) or not isinstance(row.submission_id, str)
                or not re.fullmatch(r"[1-9][0-9]{0,79}", row.submission_id)
                or not isinstance(row.title_slug, str) or len(row.title_slug) > 200
                or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", row.title_slug)
                or (platform == "codeforces" and not re.fullmatch(r"cf-[1-9][0-9]*-[a-z0-9]+", row.title_slug))
                or not isinstance(row.accepted_at, datetime)):
            raise ValueError("Invalid provider acceptance")
        instant = utc_storage(row.accepted_at)
        if instant > now:
            raise ValueError("A future timestamp is not accepted-solve evidence")
        evidence = (row.title_slug, instant)
        if row.submission_id in identities and identities[row.submission_id] != evidence:
            raise ValueError("Conflicting provider submission evidence")
        identities[row.submission_id] = evidence


def ingest_acceptances(db: Session, user_id: int, *, platform: str,
                       account_version: int, expected_handle: str,
                       submissions: list[ProviderAcceptance], complete_history: bool = False):
    """Store a batch atomically in the caller's transaction; never award points.

    Only a completed Codeforces scan can establish a first accepted timestamp
    here. LeetCode recent ACs prove acceptance, not historical first solves.
    Existing unique-question rows are linked, never duplicated by this writer.
    """
    validate_acceptances(submissions, platform)
    if type(complete_history) is not bool or (complete_history and platform != "codeforces"):
        raise ValueError("Unsupported complete-history proof")
    if not isinstance(expected_handle, str) or not expected_handle:
        raise ValueError("Missing provider account identity")
    if type(account_version) is not int or account_version < 0:
        raise ValueError("Invalid account generation")
    connection = db.connection()
    if connection.dialect.name == "sqlite" and not connection.connection.driver_connection.in_transaction:
        # A first SAVEPOINT in sqlite3 legacy mode otherwise commits on release,
        # even if the caller later rolls back its outer SQLAlchemy transaction.
        connection.exec_driver_sql("BEGIN")
    # A conflicting replay halfway through must not leave a partly stored batch.
    with db.begin_nested():
        user = db.query(User).filter_by(id=user_id).populate_existing().with_for_update().one()
        if (getattr(user, platform + "_account_version") != account_version
                or (getattr(user, platform + "_username") or "").casefold() != expected_handle.casefold()):
            raise ValueError("The linked coding account changed during sync")
        solves = {solve.title_slug: solve for solve in db.query(Solve).filter_by(
            user_id=user_id, platform=platform, account_version=account_version).all()
            if not solve.source_handle or solve.source_handle.casefold() == expected_handle.casefold()}
        earliest = {}
        events = []
        for row in sorted(submissions, key=lambda row: (utc_storage(row.accepted_at), int(row.submission_id))):
            event = record_acceptance(db, user_id, platform=platform, account_version=account_version,
                submission_id=row.submission_id, title_slug=row.title_slug, accepted_at=row.accepted_at,
                evidence_kind="provider_full" if complete_history else "public_recent")
            solve = solves.get(row.title_slug)
            if solve:
                event.solve_id = solve.id
            earliest.setdefault(row.title_slug, event)
            events.append(event)
        if complete_history:
            for slug, first in earliest.items():
                # A later full scan can expose an earlier acceptance. Do not leave
                # two events marked as the first solve or downgrade on recent scans.
                db.query(AcceptedSubmission).filter_by(user_id=user_id, platform=platform,
                    account_version=account_version, title_slug=slug).update(
                    {AcceptedSubmission.first_solve_verified: False}, synchronize_session="fetch")
                first.first_solve_verified = True
                first.evidence_kind = "provider_full"
                solve = solves.get(slug)
                if solve:
                    solve.first_solve_at = first.accepted_at
                    solve.first_solve_verified = True
                    if solve.score_components_state == "history_review":
                        solve.score_components_state = "base_only"
        db.flush()
        return events


@dataclass(frozen=True)
class RevisionCandidate:
    event_id: int
    accepted_at: datetime
    streak_days: int
    points: Decimal


def revision_candidates(db: Session, solve: Solve, *, live_after: datetime | None) -> list[RevisionCandidate]:
    """Plan recurring rewards; this function does not grant them or change totals.

    The caller supplies the last successful sync boundary captured before its
    provider request. No boundary means initial import: no retrospective reward.
    R3 must persist proposals under the account lock with unique award keys.
    """
    if live_after is None or not solve.first_solve_verified or solve.first_solve_at is None:
        return []
    user = db.query(User).filter_by(id=solve.user_id).one()
    if (solve.account_version != getattr(user, solve.platform + "_account_version")
            or not solve.source_handle
            or solve.source_handle.casefold() != (getattr(user, solve.platform + "_username") or "").casefold()):
        return []
    rewards = db.query(PointAward).filter_by(solve_id=solve.id, kind="revision").all()
    if any(reward.earned_at is None for reward in rewards):
        return []  # An unknown prior reward date cannot establish a safe cooldown.
    anchor = max([utc_storage(solve.first_solve_at)] + [utc_storage(reward.earned_at) for reward in rewards])
    rewarded_events = {reward.submission_id for reward in rewards}
    events = db.query(AcceptedSubmission).filter(
        AcceptedSubmission.user_id == solve.user_id, AcceptedSubmission.platform == solve.platform,
        AcceptedSubmission.account_version == solve.account_version, AcceptedSubmission.solve_id == solve.id,
        AcceptedSubmission.accepted_at > utc_storage(live_after)).order_by(
            AcceptedSubmission.accepted_at, AcceptedSubmission.id).all()
    first_solves = db.query(Solve).filter_by(user_id=solve.user_id, first_solve_verified=True).all()
    verified_dates = [(row.first_solve_at, ist_date(row.first_solve_at)) for row in first_solves
        if row.first_solve_at is not None and row.account_version == getattr(user, row.platform + "_account_version")
        and row.source_handle and row.source_handle.casefold() == (getattr(user, row.platform + "_username") or "").casefold()]
    result = []
    for event in events:
        if event.id in rewarded_events or event.first_solve_verified or not revision_due(event.accepted_at, anchor):
            continue
        days = current_streak({day for instant, day in verified_dates if instant <= event.accepted_at}, ist_date(event.accepted_at))
        result.append(RevisionCandidate(event.id, event.accepted_at, days, revision_points(days)))
        anchor = event.accepted_at  # Next proposal assumes this one is awarded.
    return result
