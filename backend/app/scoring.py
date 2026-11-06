"""Deterministic component arithmetic for the new award ledger.

Each stored component is rounded to four decimal places, half up. Totals are
the sum of those stored components. Revaluation never multiplies retained
daily/revision awards again. Provider lookups and eligibility stay outside.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

SCORING_VERSION = "points-components-v2"
PRECISION = Decimal("0.0001")


def number(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError("Scoring inputs must be finite numbers")
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise ValueError("Scoring inputs must be finite numbers")
        return result
    except InvalidOperation as error:
        raise ValueError("Invalid scoring input") from error


def rounded(value: Decimal) -> Decimal:
    try:
        result = value.quantize(PRECISION, rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ValueError("Score exceeds stored precision") from error
    if abs(result) > Decimal("99999999999999.9999"):
        raise ValueError("Score exceeds stored precision")
    return result


def streak_multiplier(days: int) -> Decimal:
    if type(days) is not int:
        raise ValueError("Streak days must be an integer")
    return (Decimal(1) + Decimal(min(30, max(0, days))) / Decimal(300)).quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_UP)


def revision_points(streak_days: int) -> Decimal:
    return rounded(Decimal(2) * streak_multiplier(streak_days))


def calculate_points(*, platform: str, difficulty: str | None = None,
                     rating: int | float | Decimal | None = None,
                     ac_rate: int | float | Decimal | None = None,
                     streak_days: int = 0, daily_eligible: bool = False,
                     retained_daily_points: int | float | Decimal | None = None,
                     retained_revision_points: int | float | Decimal = 0) -> dict:
    if type(daily_eligible) is not bool:
        raise ValueError("Daily eligibility requires verified boolean evidence")
    multiplier = streak_multiplier(streak_days)
    rating_value = number(rating) if rating is not None else None
    ac_value = number(ac_rate) if ac_rate is not None else None
    if ac_value is not None and not Decimal(0) <= ac_value <= Decimal(100):
        raise ValueError("Acceptance rate must be between zero and 100")
    ac_multiplier = Decimal(1)
    if platform == "leetcode":
        if rating_value is not None:
            if rating_value <= 0:
                raise ValueError("LeetCode rating must be positive")
            raw_base = rating_value / Decimal(100)
        else:
            categories = {"Easy": Decimal(8), "Medium": Decimal(15), "Hard": Decimal(24)}
            if difficulty not in categories:
                raise ValueError("Verified difficulty or rating is required")
            raw_base = categories[difficulty]
            if ac_value is not None:
                ac_multiplier = Decimal(1) + (Decimal(50) - ac_value) / Decimal(100)
    elif platform == "codeforces":
        if daily_eligible or retained_daily_points not in (None, 0):
            raise ValueError("Codeforces does not earn LeetCode daily bonuses")
        raw_base = Decimal(0) if rating_value is None or rating_value < 800 else Decimal(8) + Decimal("0.012") * (rating_value - 800)
    else:
        raise ValueError("Unknown scoring platform")
    if daily_eligible and retained_daily_points is not None:
        raise ValueError("A retained daily award cannot be awarded again")
    base = rounded(raw_base * ac_multiplier)
    base_award = rounded(base * multiplier)
    daily_award = rounded(number(retained_daily_points)) if retained_daily_points is not None else rounded(Decimal(5) * multiplier if daily_eligible else Decimal(0))
    revisions = rounded(number(retained_revision_points))
    if daily_award < 0 or revisions < 0:
        raise ValueError("Retained awards cannot be negative")
    return {
        "scoring_version": SCORING_VERSION, "platform": platform,
        "difficulty": difficulty, "contest_rating": rating_value, "ac_rate": ac_value,
        "raw_base_points": rounded(raw_base), "ac_multiplier": ac_multiplier,
        "base_points": base, "streak_days": streak_days, "streak_multiplier": multiplier,
        "base_award": base_award, "daily_award": daily_award, "revision_award": revisions,
        "points_earned": rounded(base_award + daily_award + revisions),
    }
