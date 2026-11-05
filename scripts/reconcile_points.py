#!/usr/bin/env python3
"""
CLI tool for bounded, resumable all-user point reconciliation.

Usage:
    python3 scripts/reconcile_points.py [--job-name reconcile-points-v2] [--batch-size 50] [--force] [--status]
"""
import argparse
import asyncio
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal, engine
from app.migrations import run_all_migrations
from app.models import JobCheckpoint, User
from app.point_calculator import recalculate_all_users_points


async def main():
    parser = argparse.ArgumentParser(description="Resumable All-User Point Reconciliation")
    parser.add_argument("--job-name", type=str, default="reconcile-points-v2", help="Versioned job name")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size per transaction (default: 50)")
    parser.add_argument("--force", action="store_true", help="Restart from ID 0 even if checkpoint exists")
    parser.add_argument("--status", action="store_true", help="Check current checkpoint status without running")
    args = parser.parse_args()

    run_all_migrations(engine)
    db = SessionLocal()
    try:
        checkpoint = db.query(JobCheckpoint).filter(JobCheckpoint.job_name == args.job_name).first()
        if args.status:
            total_users = db.query(User.id).count()
            print(f"=== Checkpoint Status for Job: {args.job_name} ===")
            print(f"Total Users in DB  : {total_users}")
            if not checkpoint:
                print("No checkpoint found (job has not been started).")
            else:
                print(f"Status             : {checkpoint.status}")
                print(f"Last Processed ID  : {checkpoint.last_processed_id}")
                print(f"Total Processed    : {checkpoint.total_processed}")
                print(f"Batch Size         : {checkpoint.batch_size}")
                print(f"Started At         : {checkpoint.started_at}")
                print(f"Updated At         : {checkpoint.updated_at}")
                print(f"Completed At       : {checkpoint.completed_at}")
            return

        def progress_callback(processed: int, total: int, last_id: int):
            percent = (processed / total * 100.0) if total > 0 else 100.0
            print(f"  [Progress] {processed}/{total} users ({percent:.1f}%) reconciled (Last User ID: {last_id})")

        print(f"Starting point reconciliation job '{args.job_name}' (batch_size={args.batch_size}, force={args.force})...")
        result = await recalculate_all_users_points(
            db,
            batch_size=args.batch_size,
            job_name=args.job_name,
            force=args.force,
            on_progress=progress_callback,
        )

        print("\n=== Point Reconciliation Complete ===")
        print(f"Job Name        : {result['job_name']}")
        print(f"Status          : {result['status']}")
        print(f"Total Processed : {result['total_processed']}")
        print(f"Batches Run     : {result['batches']}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
