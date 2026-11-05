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

---

## 2026-11-06 — Step: M2-04 / DATA-02/03/04/09: Accepted Evidence Ingestion, Repeat Deduplication & Revision Awards

### Summary of Changes
Connected runtime syncing (`backend/app/scheduler.py` and `backend/app/codeforces_sync.py`) to the evidence and tracking pipeline. Ingested all AC submissions into `AcceptedSubmission`, eliminated the invalid calendar-to-solve conversion (DATA-03), deduplicated repeated submissions of the same problem into a single `Solve` ledger entry, enforced first-solve-only streaks in IST, and implemented revision awards (2 × streak multiplier after 7 elapsed days from first solve or last rewarded revision, with unrewarded attempts leaving the cooldown anchor intact). Clarified FEAT-01 in the implementation plan to ensure study plan playlists added by link are persisted directly to the backend profile rather than merely kept in local browser storage.

### Detailed Changes
1. **`backend/app/scheduler.py` (`poll_user`)**:
   - Switched day boundaries to `ist_date` and `ist_today()`.
   - Removed the blanket `submission_calendar` to `DailyActivity` population that falsely marked active calendar days as solved questions (DATA-03).
   - Ingests each AC submission via `record_acceptance` with `evidence_kind="public_recent"`, `account_version=user.leetcode_account_version`.
   - First-time solves create the unique `Solve` row with `first_solve_at = utc_storage(accepted_at)`, `first_solve_verified = True`, `account_version = user.leetcode_account_version`.
   - Repeat acceptances of already solved questions link their `AcceptedSubmission.solve_id` without creating duplicate `Solve` entries or inflating new-question counts.
   - Evaluates repeat acceptances for 7-day revision eligibility (`revision_due(accepted_at, anchor_time)`). When >= 7 elapsed days, records a `PointAward` of `kind="revision"` with `points = revision_points(streak_on_date)` (DATA-09). Unrewarded attempts do not reset the anchor.
   - Updates `DailyActivity` strictly from verified first solves of distinct LeetCode problems on each IST date.

2. **`backend/app/codeforces_sync.py` (`sync_codeforces_user`)**:
   - Ingests each Codeforces AC submission via `record_acceptance` with `evidence_kind="provider_full"`, `first_solve_verified=True`.
   - Sets `solve.first_solve_at = solved_at`, `solve.first_solve_verified = True`, `solve.account_version = user.codeforces_account_version`.
   - Synchronizes `PlatformActivity` based on IST first solve dates.

3. **`docs/IMPLEMENTATION_PLAN.md`**:
   - Explicitly updated FEAT-01 implementation details to specify adding custom study plans/playlists via URL link or catalog into Progress, persisting user library choices and item completion directly to their authenticated backend account profile so that study plans and playlists are never just locally saved in browser storage.
   - Added M2-04 verification entry to the implementation step sequence table.

4. **`backend/tests/test_tracking_sync.py`**:
   - Added 5 new tests covering:
     1. First solve creation, evidence recording, and IST daily count population.
     2. Repeat submission deduplication (does not add duplicate solve or extend streak).
     3. Calendar activity alone without verified accepts does not create solved question counts (DATA-03).
     4. 7-day revision eligibility, cooldown anchor preservation across unrewarded attempts, and recurring awards (DATA-09).
     5. Codeforces sync evidence recording and first solve metadata.

### Verification Evidence
- 86 backend tests passed with zero failures (`backend/tests`).
- Regression verified against both SQLite and local PostgreSQL test instances.

---

## 2026-11-06 — Step: M2-05 / DATA-01/05/07/08/09: Score Ledger Reconciliation, Point Awards Persistence & Handle Change Recovery

### Summary of Changes
Connected the deterministic `scoring.py` Decimal calculation engine to runtime score reconciliation in `backend/app/point_calculator.py`. Every calculation captures a protected immutable `ScoreSnapshot` baseline before altering any score. Persisted exact `PointAward` rows for base, daily, and revision awards under version `points-components-v2`. Preserved existing earned daily bonuses without retroactive loss or double-counting. Awarded base-only credit for unlogged historical solves without streak inflation or daily bonuses. Unified breakdown helpers with the stored award formula to eliminate calculation/display discrepancies. Implemented handle-change reconciliation in `update_leetcode_username` (DATA-01) by capturing a baseline snapshot, bumping `leetcode_account_version`, and clearing old LeetCode solves while strictly preserving Codeforces history and tracking.

### Detailed Changes
1. **`backend/app/point_calculator.py`**:
   - `compute_solve_points`, `compute_solve_points_breakdown`, and `compute_codeforces_points_breakdown` now delegate directly to `scoring.calculate_points`, eliminating differences between stored awards and display breakdown calculations (DATA-07).
   - `recalculate_user_points`:
     - Calls `capture_score_baseline(db, user.id)` before any score modification.
     - Computes base and daily awards using `calculate_points` for LeetCode (rated or category base * ac_rate) and Codeforces (linear scale).
     - Records and persists exact `PointAward` rows (`kind="base"`, `kind="daily"`) with `scoring_version="points-components-v2"`.
     - Preserves existing earned daily bonuses without recomputing or overwriting them.
     - Adds existing revision awards from `point_awards` to solve totals.
     - Unlogged historical LeetCode solves are awarded base credit only (`multiplier = 1.0`, no daily bonus, no streak inflation), protecting against artificial score boosts.
     - Flushes all awards and updates `user.points` with exact 4-place rounded precision.

2. **`backend/app/main.py` (`update_leetcode_username`)**:
   - When switching to a different LeetCode username:
     - Captures a baseline `ScoreSnapshot` for recovery.
     - Increments `user.leetcode_account_version += 1`, invalidating any stale in-flight operations.
     - Calls `clear_tracking(db, user_id, "leetcode")` and deletes previous LeetCode `Solve` and `DailyActivity` rows.
     - Resets LeetCode difficulty totals and streak while strictly keeping Codeforces history, solves, and preferences intact (DATA-01).
     - Polls and repopulates the new handle from scratch.

3. **`backend/tests/test_score_reconciliation.py`**:
   - Added 5 new tests covering:
     1. Exact `PointAward` persistence and baseline snapshot capture across LeetCode and Codeforces solves.
     2. Reconciliation idempotency (running twice produces identical scores without duplicate awards).
     3. Unlogged historical solves receiving base-only credit.
     4. Handle change reconciliation: LeetCode solves cleanly replaced, account version bumped, Codeforces history preserved.
     5. Breakdown helpers matching stored calculation results exactly.

### Verification Evidence
- 91 backend tests passed with zero failures (`backend/tests`).
- Verified against both SQLite and local native PostgreSQL 16 instances.
