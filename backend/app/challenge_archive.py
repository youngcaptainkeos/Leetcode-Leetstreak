"""
LeetCode Daily Challenges Archive Manager.

Provides incremental backfill and coverage tracking for historical and live daily challenges.
Avoids redundant remote GraphQL fetches for already-stored months and commits per-month
to ensure interrupted backfills resume without duplicate work or lost coverage.
"""
import calendar
import logging
from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import DailyChallenge
from .leetcode_client import fetch_monthly_daily_challenges

logger = logging.getLogger("codestreak.challenge_archive")


def is_month_covered(db: Session, year: int, month: int, reference_date: Optional[date] = None) -> bool:
    """
    Checks if all expected daily challenge dates for (year, month) are stored in the database.
    - Past months require all days of the month (e.g. 31, 30, 28/29).
    - The current month requires challenges up through reference_date.
    - Future months return True (future challenges do not exist yet).
    """
    ref = reference_date or date.today()
    if year > ref.year or (year == ref.year and month > ref.month):
        return True

    _, days_in_month = calendar.monthrange(year, month)
    start_date = date(year, month, 1)

    if year == ref.year and month == ref.month:
        end_date = ref
        expected_days = ref.day
    else:
        end_date = date(year, month, days_in_month)
        expected_days = days_in_month

    count = (
        db.query(func.count(DailyChallenge.date))
        .filter(DailyChallenge.date >= start_date, DailyChallenge.date <= end_date)
        .scalar()
        or 0
    )
    return count >= expected_days


async def backfill_daily_challenges_archive(
    db: Session,
    start_year: int = 2024,
    incremental: bool = True,
    force: bool = False,
    reference_date: Optional[date] = None,
) -> Dict[str, object]:
    """
    Backfills daily challenges archive from LeetCode GraphQL from start_year to current date.
    
    When incremental=True (default), skips any month that is already fully covered in the database.
    Commits after each month so interrupted runs resume cleanly from the next missing month.
    """
    ref = reference_date or date.today()
    scanned = 0
    skipped_months: List[str] = []
    fetched_months: List[str] = []
    failed_months: List[str] = []
    added_records = 0
    updated_records = 0

    for year in range(start_year, ref.year + 1):
        max_m = ref.month if year == ref.year else 12
        for month in range(1, max_m + 1):
            scanned += 1
            month_key = f"{year}-{month:02d}"

            if incremental and not force:
                if is_month_covered(db, year, month, reference_date=ref):
                    skipped_months.append(month_key)
                    continue

            logger.info("Backfilling daily challenges for month %s...", month_key)
            try:
                m_map = await fetch_monthly_daily_challenges(year, month)
                month_added = 0
                month_updated = 0
                for d_str, slug in m_map.items():
                    d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
                    existing = db.query(DailyChallenge).filter(DailyChallenge.date == d_obj).first()
                    if not existing:
                        db.add(DailyChallenge(date=d_obj, title_slug=slug))
                        month_added += 1
                    elif existing.title_slug != slug:
                        existing.title_slug = slug
                        month_updated += 1
                db.commit()
                fetched_months.append(month_key)
                added_records += month_added
                updated_records += month_updated
                logger.info(
                    "Month %s backfilled: %d added, %d updated.",
                    month_key,
                    month_added,
                    month_updated,
                )
            except Exception as e:
                db.rollback()
                logger.warning("Backfill failed for %s: %s", month_key, e)
                failed_months.append(month_key)

    summary = {
        "scanned_months": scanned,
        "skipped_months": skipped_months,
        "fetched_months": fetched_months,
        "failed_months": failed_months,
        "added_records": added_records,
        "updated_records": updated_records,
    }
    logger.info("Daily challenges backfill completed: %s", summary)
    return summary
