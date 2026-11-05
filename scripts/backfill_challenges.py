#!/usr/bin/env python3
"""
CLI tool for incremental LeetCode daily challenge archive backfill.

Usage:
    python3 scripts/backfill_challenges.py [--start-year 2024] [--force] [--dry-run]
"""
import argparse
import asyncio
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, engine
from app.migrations import run_all_migrations
from app.challenge_archive import backfill_daily_challenges_archive, is_month_covered


async def main():
    parser = argparse.ArgumentParser(description="Incremental LeetCode Daily Challenges Backfill")
    parser.add_argument("--start-year", type=int, default=2024, help="Starting year (default: 2024)")
    parser.add_argument("--force", action="store_true", help="Force refetch even for covered months")
    parser.add_argument("--dry-run", action="store_true", help="Report missing months without fetching")
    args = parser.parse_args()

    run_all_migrations(engine)
    db = SessionLocal()
    try:
        if args.dry_run:
            from datetime import date
            now = date.today()
            missing = []
            covered = []
            for y in range(args.start_year, now.year + 1):
                max_m = now.month if y == now.year else 12
                for m in range(1, max_m + 1):
                    key = f"{y}-{m:02d}"
                    if is_month_covered(db, y, m, reference_date=now):
                        covered.append(key)
                    else:
                        missing.append(key)
            print(f"[Dry Run] Covered months ({len(covered)}): {', '.join(covered) or 'None'}")
            print(f"[Dry Run] Missing months ({len(missing)}): {', '.join(missing) or 'None'}")
            return

        print(f"Starting incremental challenge backfill from {args.start_year} (force={args.force})...")
        summary = await backfill_daily_challenges_archive(
            db,
            start_year=args.start_year,
            incremental=not args.force,
            force=args.force,
        )
        print("\n--- Daily Challenge Archive Summary ---")
        print(f"Total months scanned : {summary['scanned_months']}")
        print(f"Skipped (covered)    : {len(summary['skipped_months'])} ({', '.join(summary['skipped_months']) if summary['skipped_months'] else 'None'})")
        print(f"Fetched              : {len(summary['fetched_months'])} ({', '.join(summary['fetched_months']) if summary['fetched_months'] else 'None'})")
        print(f"Failed               : {len(summary['failed_months'])} ({', '.join(summary['failed_months']) if summary['failed_months'] else 'None'})")
        print(f"Records added        : {summary['added_records']}")
        print(f"Records updated      : {summary['updated_records']}")
        print("Done!")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
