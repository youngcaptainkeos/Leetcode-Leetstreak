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

---

## 2026-11-06 — Step: M2-06 / FEAT-03: Provider Sync Status and History Completeness Across Clients

### Summary of Changes
Exposed authenticated provider sync status and history completeness across the backend API and client applications (`extension` and `web`). The backend dashboard endpoint now returns `leetcode_last_sync`, `leetcode_history_state`, and `leetcode_history_gap` alongside existing Codeforces sync status. In the scheduler, `leetcode_last_sync` is updated on every poll, and `leetcode_history_gap` is evaluated by comparing total known solves (from difficulty counts) with recorded solve evidence. If a gap exists, history state is labeled as `partial` (older solves receive base credit only); otherwise, `complete`. The Settings UI in both the browser extension and website renders the last sync timestamp and honest history coverage information. Rebuilt the extension and synchronized all four ZIP packages (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`). This completes Milestone M2.

### Detailed Changes
1. **`backend/app/schemas.py` & `backend/app/main.py`**:
   - Added `leetcode_last_sync: Optional[datetime] = None`, `leetcode_history_state: Optional[str] = "partial"`, and `leetcode_history_gap: Optional[bool] = True` to `DashboardResponse`.
   - `get_dashboard` serializes `user.leetcode_last_sync` (in UTC timezone), `user.leetcode_history_state`, and `user.leetcode_history_gap`.

2. **`backend/app/scheduler.py`**:
   - In `poll_user`, updates `user.leetcode_last_sync = datetime.now(timezone.utc).replace(tzinfo=None)`.
   - Compares total known solved problems (`easy + medium + hard`) to recorded LeetCode solves to compute `user.leetcode_history_gap` and sets `user.leetcode_history_state = "partial"` or `"complete"`.

3. **`extension/src/lib/api.ts` & `web/app/lib/api.ts`**:
   - Added `leetcode_last_sync?: string`, `leetcode_history_state?: string`, and `leetcode_history_gap?: boolean` to the `DashboardResponse` interface.

4. **`extension/src/App.tsx` & `web/app/App.tsx`**:
   - Updated the LeetCode settings card input hint to render `Last synced <timestamp>` when available and clearly state `History coverage: partial (older historical solves have base points only)` or `History coverage: complete`.

5. **Distribution Packages**:
   - Built the extension bundle via `npm run build`.
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- Ran `tsc --noEmit` on both `extension` and `web` with 0 errors.
- Ran extension unit tests: 11/11 tests passed (`progress.test.mjs`), 6/6 tests passed (`auth.test.mjs`).
- Ran backend test suite: 91/91 tests passed (`backend/tests`).
- Built web application cleanly (`npm run build` -> `backend/web`).

---

## 2026-11-06 — Step: M3-01 / UI-01 & UI-02: Shared Account Storage Contract and Immediate Accepted-Submission Detection

### Summary of Changes
Unified the extension session storage contract under version 2 (`codestreak_session_v2`), providing seamless fallback and automatic migration from legacy storage keys (`codestreak_user_id`, `codestreak_access_token`, and `codestreak_user`). Implemented a main-world page bridge script (`extension/public/leetcode-page-bridge.js`) that monitors fetch and XMLHttpRequest responses for LeetCode submission checks. Rewrote `leetcode-listener.js` to run in the isolated world, inject the bridge into LeetCode pages, validate origin and message payloads, and relay unprivileged hint messages to `background.js` without accessing user tokens or credentials. Updated `background.js` to debounce incoming hints (10-second window), load the authenticated session, trigger an authorized backend sync, and broadcast `LEETSTREAK_SYNC_COMPLETED` to refresh open extension views immediately.

### Detailed Changes
1. **`extension/src/storage.ts`**:
   - Defined `SESSION_STORAGE_KEY = "codestreak_session_v2"` and `StoredSession` interface (`{ version: 2, userId: number, accessToken: string }`).
   - Implemented `getStoredSession()`: reads `SESSION_STORAGE_KEY` and falls back to validating and migrating legacy `codestreak_user_id` / `codestreak_access_token` or `codestreak_user`.
   - Implemented `setStoredSession(session)`: persists the versioned session and synchronizes individual keys for backward compatibility.
   - Implemented `clearStoredSession()`: cleanly invalidates the session, individual keys, legacy user objects, and all account-scoped cache keys (`cached_dash`, `cached_board`, `active_tab`, menu and startup tab keys).

2. **`extension/public/leetcode-page-bridge.js`**:
   - Created a main-world script intercepting both `window.fetch` and `XMLHttpRequest.prototype.open/send`.
   - Detects LeetCode submission checks matching `/submissions/detail/.../check/` that succeed with status code 10 or "Accepted".
   - Dispatches a validated `window.postMessage` with source `"leetstreak-page-bridge"` and type `"LEETSTREAK_SUBMISSION_ACCEPTED"`.

3. **`extension/public/leetcode-listener.js`**:
   - Injects `leetcode-page-bridge.js` into LeetCode pages.
   - Listens for `window.onmessage`, verifying origin `https://leetcode.com` and matching bridge signatures.
   - Includes a fallback `MutationObserver` on the page DOM for `"Accepted"` submission result modals.
   - Dispatches narrow, unprivileged `{ type: "LEETSTREAK_SUBMISSION_HINT", platform: "leetcode" }` hints to `background.js` via `chrome.runtime.sendMessage`.
   - Removed all token access from content scripts.

4. **`extension/manifest.json`**:
   - Registered `leetcode-page-bridge.js` under `content_scripts` with `"world": "MAIN"` and `"run_at": "document_start"`.
   - Added `leetcode-page-bridge.js` to `web_accessible_resources`.

5. **`extension/public/background.js`**:
   - Added `chrome.storage.onChanged` listener to invalidate worker sync timestamps on logout.
   - Added message handler for `LEETSTREAK_SUBMISSION_HINT`: validates sender runtime ID, debounces sync requests (10s cooldown), fetches the active session from storage, issues an authorized `POST /api/users/{userId}/sync` request, and broadcasts `LEETSTREAK_SYNC_COMPLETED` to active extension popups.

6. **`extension/src/App.tsx`**:
   - Switched initialization, login, registration, password reset, and password change to use `getStoredSession` and `setStoredSession`.
   - Added listener for `LEETSTREAK_SYNC_COMPLETED` to refresh dashboard and practice data in real time when a solve is detected.

7. **`extension/tests/storage.test.mjs`**:
   - Added 6 unit tests verifying versioned session contract, legacy key migration, legacy user object migration, synchronized setting, cache invalidation on logout, and sensitive draft clearing.

8. **Distribution Packages**:
   - Built the extension bundle via `npm run build`.
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- Ran `tsc --noEmit` on `extension` with 0 errors.
- Ran all 23 extension unit tests (6 auth tests, 6 storage tests, 11 progress tests) — 23 passed, 0 failed.
- Ran backend test suite: 91/91 tests passed (`backend/tests`).
- Built web application cleanly (`npm run build` -> `backend/web`).


