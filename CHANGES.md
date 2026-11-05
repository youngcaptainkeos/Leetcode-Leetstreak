# LeetStreak Implementation Changes Log

This document records all changes made during the autonomous execution of the LeetStreak implementation plan on branch `pre-launch`.

---

## 2026-11-06 — Step: OPS-03 / M5 Step 1: Versioned Atomic Migrations & Safe Startup Lifecycle

### Summary of Changes
Addressed the critical OPS-03 startup/migration prerequisite before activating the new scoring pipeline. Removed expensive and unsafe operations from server startup, unified database migrations into an atomic, versioned registry with advisory locking, and added shutdown lifecycle handling.

### Detailed Changes
1. **`backend/app/migrations.py`**:
   - Upgraded `migration_connection(target)` to accept either an `Engine` or an active `Connection`.
   - On PostgreSQL, acquires transaction-scoped advisory lock `72635001` (`SELECT pg_advisory_xact_lock(72635001)`).
   - On non-PostgreSQL (e.g. SQLite), uses an in-process `threading.RLock()` to prevent self-deadlocks during nested migration calls.
   - Added `migrate_core(target)` (version `20261105-core-v1`): creates core tables and ensures columns and indices on legacy schemas.
   - Added `migrate_platforms(target)` (version `20261105-platforms-v1`): versions multi-platform columns/indices so they run once rather than querying and updating repeatedly on every startup.
   - Updated `migrate_auth`, `migrate_display_preference`, `migrate_tracking` to accept `target` (Engine or Connection).
   - Added `run_all_migrations(target)`: runs all migrations sequentially within a single atomic transaction.

2. **`backend/app/platform_migration.py`**:
   - Replaced duplicate migration logic with a delegation export to `migrate_platforms` in `migrations.py`.

3. **`backend/app/main.py`**:
   - Removed import-time `Base.metadata.create_all(bind=engine)` and raw `ALTER TABLE` DDL blocks.
   - Cleaned `on_startup`: removed hardcoded `image-overlap` daily fix, `created_at` timestamp mutation, `DailyActivity` row bloat normalization, `backfill_daily_challenges_archive(db)` GraphQL queries, and `recalculate_all_users_points(db)`. Now calls `run_all_migrations(engine)` and starts the scheduler.
   - Fails startup cleanly if any migration fails (fail-closed).
   - Added `on_shutdown`: cleanly shuts down `_scheduler` if running.

4. **`backend/app/scheduler.py`**:
   - Updated `start_scheduler(immediate: bool = False)`: removed unconditional `next_run_time=datetime.now()`, avoiding startup polling of all users and immediate zerotrac dataset refresh.

5. **`backend/tests/test_migrations.py` & `backend/tests/test_postgres_migrations.py`**:
   - Added 9 unit tests in `test_migrations.py` testing fresh DB migration, idempotency, engine/connection polymorphism, failure rollback, platform versioning, engine concurrency, startup/shutdown lifecycle, and fail-closed startup.
   - Added `test_run_all_migrations_concurrently_under_advisory_lock` in `test_postgres_migrations.py` testing 4 concurrent threads against native PostgreSQL 16.

### Verification Evidence
- 81 backend tests passed with zero failures (`backend/tests`), covering both SQLite and native PostgreSQL 16.
- Concurrent migrations verified under thread pool execution against PostgreSQL advisory locks.
