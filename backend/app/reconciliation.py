"""Component reconciliation; caller owns commit/rollback. No provider requests."""
from collections import Counter
from decimal import Decimal

from sqlalchemy.orm import Session

from .contest_ratings import get_contest_rating
from .models import AccountCredit, PointAward, Solve, User
from .scoring import SCORING_VERSION, calculate_points, number, rounded
from .streak import current_streak
from .timekeeping import ist_date
from .tracking import capture_score_baseline, revision_candidates


def current_account(user: User, solve: Solve) -> bool:
    handle = getattr(user, solve.platform + "_username", None)
    generation = getattr(user, solve.platform + "_account_version", None)
    return bool(handle and solve.account_version == generation and (
        (solve.source_handle and solve.source_handle.casefold() == handle.casefold())
        or (not solve.source_handle and generation == 0)))


def proved_date(user: User, solve: Solve):
    return solve.first_solve_at if (current_account(user, solve) and solve.source_handle
        and solve.first_solve_verified and solve.first_solve_at is not None) else None


def json_inputs(values):
    return {key: str(value) if isinstance(value, Decimal) else value for key, value in values.items()}


def store_award(db, solve, kind, points, *, earned_at=None, inputs=None, key=None):
    key = key or f"components:{solve.id}:{kind}"
    award = db.query(PointAward).filter_by(award_key=key).first()
    if award:
        if (award.user_id, award.solve_id, award.kind) != (solve.user_id, solve.id, kind):
            raise ValueError("Conflicting award identity")
        return award
    award = PointAward(award_key=key, user_id=solve.user_id, solve_id=solve.id,
        kind=kind, points=rounded(number(points)), earned_at=earned_at,
        scoring_version=SCORING_VERSION, input_snapshot=inputs or {})
    db.add(award)
    db.flush()
    return award


def reconcile_user(user: User, db: Session, *, revision_windows=None) -> float:
    """Revalue bases, retain awards and estimate only disjoint historical slots.

    Unknown old daily totals are protected whole, not reverse-engineered into a
    guessed +5. First imported history never receives retrospective bonuses.
    Revision windows come from successful provider syncs, never API request data.
    """
    db.flush()
    user = db.query(User).filter_by(id=user.id).populate_existing().with_for_update().one()
    snapshot = capture_score_baseline(db, user.id).payload
    baseline = {row["id"]: row for row in snapshot["solves"]}
    baseline_revisions = Counter()
    baseline_components = Counter()
    for row in snapshot.get("awards", []):
        if row["kind"] == "revision":
            baseline_revisions[row["solve_id"]] += number(Decimal(row["points"]))
        if row["kind"] in {"daily", "revision"}:
            baseline_components[row["solve_id"]] += number(Decimal(row["points"]))
    solves = [row for row in db.query(Solve).filter_by(user_id=user.id).all() if current_account(user, row)]
    dates = [(proved_date(user, row), ist_date(row.first_solve_at)) for row in solves if proved_date(user, row)]
    total = Decimal(0)
    classified = Counter()
    unclassified_paid = 0
    for solve in solves:
        awards = db.query(PointAward).filter_by(solve_id=solve.id).all()
        bases = [row for row in awards if row.kind == "base"]
        if len(bases) > 1:
            raise ValueError("Ambiguous base components require explicit repair")
        old = baseline.get(solve.id)
        if old and (old["title_slug"] != solve.title_slug or old["platform"] != solve.platform
                    or old.get("account_version", 0) != solve.account_version
                    or (old.get("source_handle") or "").casefold() != (solve.source_handle or "").casefold()):
            old = None
        old_points = number(old.get("points_earned") or 0) if old else Decimal(0)
        if old_points < 0:
            raise ValueError("Invalid historical credit")
        if old and old.get("is_daily") and old_points > 0 and not bases and not any(row.kind == "daily" for row in awards):
            # Explicit revisions already inside the baseline total must not be paid twice.
            protected = rounded(old_points - baseline_revisions[solve.id])
            if protected < 0:
                raise ValueError("Inconsistent protected historical credit")
            store_award(db, solve, "legacy", protected, inputs={"protection": "combined_daily", "needs_reconciliation": True})
            awards = db.query(PointAward).filter_by(solve_id=solve.id).all()
        combined = any(row.kind == "legacy" and row.input_snapshot.get("protection") == "combined_daily" for row in awards)
        first = proved_date(user, solve)
        streak = current_streak({day for instant, day in dates if instant <= first}, ist_date(first)) if first else 0
        result = None
        if not combined:
            try:
                result = calculate_points(platform=solve.platform, difficulty=solve.difficulty,
                    rating=get_contest_rating(solve.title_slug) if solve.platform == "leetcode" else solve.problem_rating,
                    ac_rate=solve.ac_rate if solve.platform == "leetcode" else None, streak_days=streak)
            except ValueError:
                # Missing/invalid metadata is not evidence that the question was Medium.
                result = None
            if result is not None:
                for row in awards:
                    if row.kind == "legacy" and row.input_snapshot.get("protection") == "metadata_missing":
                        db.delete(row)
                base = bases[0] if bases else store_award(db, solve, "base", result["base_award"])
                base.points = result["base_award"]
                base.earned_at = first
                base.scoring_version = SCORING_VERSION
                base.input_snapshot = json_inputs(result)
            elif not bases and old_points > 0:
                protected = rounded(old_points - baseline_components[solve.id])
                if protected < 0:
                    raise ValueError("Inconsistent historical components")
                store_award(db, solve, "legacy", protected, inputs={"protection": "metadata_missing", "needs_reconciliation": True})
        db.flush()
        if revision_windows and solve.platform in revision_windows:
            for proposal in revision_candidates(db, solve, live_after=revision_windows[solve.platform]):
                award = store_award(db, solve, "revision", proposal.points, earned_at=proposal.accepted_at,
                    key=f"revision:{solve.id}:{proposal.event_id}", inputs={"streak_days": proposal.streak_days, "base": 2})
                award.submission_id = proposal.event_id
        db.flush()
        awards = db.query(PointAward).filter_by(solve_id=solve.id).all()
        if any(row.kind not in {"base", "daily", "revision", "legacy"} for row in awards):
            raise ValueError("Unknown award component")
        if any(number(row.points) < 0 for row in awards):
            raise ValueError("Negative score components")
        points = rounded(sum((number(row.points) for row in awards), Decimal(0)))
        if points < 0:
            raise ValueError("Negative score components")
        solve.points_earned = float(points)
        solve.scoring_version = SCORING_VERSION
        solve.is_daily = combined or any(row.kind == "daily" and row.points > 0 for row in awards)
        solve.score_components_state = "legacy_protected" if combined else ("metadata_missing" if result is None else ("verified" if first else "base_only"))
        total += points
        if solve.platform == "leetcode":
            if solve.difficulty in {"Easy", "Medium", "Hard"}:
                classified[solve.difficulty] += 1
            elif points > 0:
                unclassified_paid += 1
    counts = {}
    for difficulty, attr in (("Easy", "easy_count"), ("Medium", "medium_count"), ("Hard", "hard_count")):
        count = getattr(user, attr) or 0
        if type(count) is not int or count < 0:
            raise ValueError("Invalid aggregate question count")
        counts[difficulty] = max(0, count - classified[difficulty])
    # Reserve anonymous slots for already credited, unclassified questions.
    # Highest-category reservation is conservative until metadata proves a match.
    reserved = unclassified_paid
    for difficulty in ("Hard", "Medium", "Easy"):
        used = min(reserved, counts[difficulty])
        counts[difficulty] -= used
        reserved -= used
    estimate = rounded(sum((calculate_points(platform="leetcode", difficulty=kind)["base_award"] * count
                            for kind, count in counts.items()), Decimal(0)))
    credit = db.query(AccountCredit).filter_by(user_id=user.id, platform="leetcode",
        account_version=user.leetcode_account_version, kind="historical_base").first()
    if credit is None:
        credit = AccountCredit(user_id=user.id, platform="leetcode", account_version=user.leetcode_account_version, kind="historical_base")
        db.add(credit)
    credit.points = estimate
    credit.scoring_version = SCORING_VERSION
    credit.input_snapshot = {"counts": counts, "reserved_unclassified": unclassified_paid - reserved,
                             "estimated": True, "dates_known": False}
    total = rounded(total + estimate)
    user.points = float(total)
    db.flush()
    return user.points


def stored_breakdown(db: Session, solve: Solve) -> dict:
    """Read stored components; never fetch a provider or reconstruct a bonus."""
    awards = db.query(PointAward).filter_by(solve_id=solve.id).all()
    components = {kind: rounded(sum((number(row.points) for row in awards if row.kind == kind), Decimal(0)))
                  for kind in ("base", "daily", "revision", "legacy")}
    base = next((row for row in awards if row.kind == "base"), None)
    inputs = base.input_snapshot if base else {}
    return {**inputs, "difficulty": solve.difficulty, "is_daily": solve.is_daily,
        "base_award": components["base"], "daily_award": components["daily"],
        "daily_bonus": components["daily"], "revision_award": components["revision"],
        "legacy_credit": components["legacy"], "score_state": solve.score_components_state,
        "points_earned": rounded(sum(components.values())) if awards else number(solve.points_earned or 0)}
