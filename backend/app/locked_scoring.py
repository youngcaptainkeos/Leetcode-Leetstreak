"""Account-scoped opening balances plus immutable, deduplicated new awards.

The caller holds the User row lock and owns the transaction. Recovery snapshots
are private evidence, never client input. Changing a linked account clears its
AccountCredit rows; another platform's opening balance is unaffected.
"""
from decimal import Decimal

from .models import AccountCredit
from .scoring import number, rounded

POLICY = "points-locked-v1"


def credit_total(credit):
    state = credit.input_snapshot
    return rounded(number(credit.points)
                   + sum(map(Decimal, state["paid"].values()), Decimal(0))
                   + sum(map(Decimal, state["reward_credit"].values()), Decimal(0)))


def snapshot_matches(user, payload, platform):
    account = payload.get("accounts", {}).get(platform, {})
    return (account.get("version") == getattr(user, platform + "_account_version")
            and (account.get("handle") or "").casefold()
            == (getattr(user, platform + "_username") or "").casefold())


def reward_totals(solves, awards_by_solve):
    return {solve.title_slug: rounded(sum((number(a.points) for a in awards_by_solve[solve.id]
                                          if a.kind in {"daily", "revision"}), Decimal(0)))
            for solve in solves}


def locked_total(user, db, baseline_record, solves, awards_by_solve, estimate):
    """Lock a historical opening once, then add each new question/reward once.

    A newly recorded LC question earns its base once under database-first-v1.
    The initial aggregate history is credited once; named questions already in
    the database at the policy cutover are covered without being paid again.
    CF has a named full-history ledger and needs no anonymous-question budget.
    """
    snapshot = baseline_record.payload
    credits = {row.platform: row for row in db.query(AccountCredit).filter_by(
        user_id=user.id, kind="locked_balance").all()
        if row.account_version == getattr(user, row.platform + "_account_version")}
    had_credit = bool(credits)
    total = Decimal(0)
    active = {}
    for platform in ("leetcode", "codeforces"):
        if not getattr(user, platform + "_username"):
            continue
        rows = [row for row in solves if row.platform == platform]
        rewards = reward_totals(rows, awards_by_solve)
        credit = credits.get(platform)
        # A CF-only sync must not finalize an empty LC import before the first
        # successful LC provider response (signup can succeed during an outage).
        if (credit is None and platform == "leetcode" and user.leetcode_last_sync is None
                and not rows and not any(getattr(user, kind + "_count") for kind in ("easy", "medium", "hard"))
                and not number(snapshot.get("points") or 0)):
            continue
        if credit is None:
            old_rows = [row for row in snapshot["solves"] if row["platform"] == platform]
            recover = snapshot_matches(user, snapshot, platform) and number(snapshot.get("points") or 0) > 0
            if recover:
                cf_old = sum((number(row.get("points_earned") or 0) for row in snapshot["solves"]
                              if row["platform"] == "codeforces"), Decimal(0))
                opening = number(snapshot["points"]) - cf_old if platform == "leetcode" else cf_old
                if opening < 0:
                    raise ValueError("Inconsistent historical opening balance")
                covered = {row["title_slug"] for row in old_rows}
                by_id = {row["id"]: row["title_slug"] for row in old_rows}
                included_rewards = {}
                for award in snapshot.get("awards", []):
                    slug = by_id.get(award["solve_id"])
                    if slug and award["kind"] in {"daily", "revision"}:
                        included_rewards[slug] = included_rewards.get(slug, Decimal(0)) + Decimal(award["points"])
                initial_count = sum(snapshot.get("difficulty_counts", {}).get(kind, 0) or 0
                                    for kind in ("easy", "medium", "hard")) if platform == "leetcode" else len(old_rows)
                source = "tracking-v1"
            else:
                # A new user/account gets one initial historical calculation.
                opening = sum((number(row.points_earned or 0) for row in rows), Decimal(0))
                if platform == "leetcode":
                    opening += estimate
                covered = {row.title_slug for row in rows}
                included_rewards = rewards
                initial_count = sum(getattr(user, kind + "_count") or 0 for kind in ("easy", "medium", "hard")) if platform == "leetcode" else len(rows)
                source = "initial-import"
            credit = AccountCredit(user_id=user.id, platform=platform,
                account_version=getattr(user, platform + "_account_version"), kind="locked_balance",
                points=rounded(opening), scoring_version=POLICY,
                input_snapshot={"policy": POLICY, "source": source, "covered": sorted(covered),
                    "first_policy": "database-first-v1",
                    "initial_count": initial_count, "paid": {}, "reward_credit": {},
                    "included_rewards": {slug: str(value) for slug, value in included_rewards.items()}})
            db.add(credit)
        state = dict(credit.input_snapshot)
        covered = set(state["covered"])
        paid = dict(state["paid"])
        reward_credit = dict(state["reward_credit"])
        capacity = len(rows)
        # Each newly recorded question is paid once; covered/paid identities
        # persist in the locked balance across subsequent syncs.
        for solve in sorted(rows, key=lambda row: (row.solved_at, row.id), reverse=True):
            slug = solve.title_slug
            has_base = any(award.kind in {"base", "legacy"} for award in awards_by_solve[solve.id])
            if slug not in covered and slug not in paid and capacity > 0 and has_base:
                paid[slug] = str(rounded(number(solve.points_earned or 0) - rewards[slug]))
                capacity -= 1
            included = Decimal(state["included_rewards"].get(slug, "0"))
            reward_credit[slug] = str(max(Decimal(reward_credit.get(slug, "0")), rewards[slug] - included, Decimal(0)))
        state["paid"], state["reward_credit"] = paid, reward_credit
        credit.input_snapshot = state  # JSON changes must be assigned, not mutated in place.
        contribution = credit_total(credit)
        active[platform] = credit
        total += contribution
    # Preserve any more recent credited balance not represented in the old
    # recovery snapshot. Never carry it across an account replacement.
    if not had_credit and all(snapshot_matches(user, snapshot, p) for p in ("leetcode", "codeforces")):
        retained = max(Decimal(0), number(user.points or 0) - total)
        if retained and "leetcode" in active:
            credit = active["leetcode"]
            credit.points = rounded(number(credit.points) + retained)
            credit.input_snapshot = {**credit.input_snapshot, "additional_retained_credit": str(retained)}
            total += retained
    return rounded(total)
