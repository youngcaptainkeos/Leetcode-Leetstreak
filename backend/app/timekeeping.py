"""Product dates use IST; database timestamps are naive UTC instants."""
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def utc_instant(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def utc_storage(value: datetime) -> datetime:
    return utc_instant(value).replace(tzinfo=None)


def ist_date(value: datetime) -> date:
    return utc_instant(value).astimezone(IST).date()


def ist_today(now: datetime | None = None) -> date:
    return ist_date(now or datetime.now(UTC))


def week_start(day: date) -> date:
    """Retain the product's Sunday-start week, at 00:00 IST."""
    return day - timedelta(days=(day.weekday() + 1) % 7)


def month_start(day: date) -> date:
    return day.replace(day=1)


def period_bounds(period: Literal["all", "today", "week", "month"], day: date | None = None) -> tuple[datetime | None, datetime | None]:
    """Return inclusive start/exclusive end as UTC database timestamps."""
    day = day or ist_today()
    if period == "all":
        return None, None
    if period == "today":
        start, end = day, day + timedelta(days=1)
    elif period == "week":
        start = week_start(day)
        end = start + timedelta(days=7)
    elif period == "month":
        start = month_start(day)
        end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)
    else:
        raise ValueError("Unknown ranking period")
    return tuple(utc_storage(datetime.combine(value, time.min, IST)) for value in (start, end))


def revision_due(accepted_at: datetime, first_or_rewarded_at: datetime) -> bool:
    """Unrewarded attempts never change the supplied eligibility anchor."""
    return utc_instant(accepted_at) - utc_instant(first_or_rewarded_at) >= timedelta(days=7)
