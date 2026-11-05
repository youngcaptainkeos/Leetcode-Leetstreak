# LeetStreak Implementation Changes Log

This document records all changes made during the autonomous execution of the LeetStreak implementation plan on branch `pre-launch`.

---

## 2026-11-06 — Step: FEAT-06 / M6 Step 1: Weekly and Monthly Points Rankings

### Summary of Changes
Implemented weekly and monthly points rankings across the backend APIs, Chrome extension, and web application. Point totals can now be toggled between "All-time", "This Week", and "This Month". Rankings use strict IST Sunday-start week boundaries and calendar month boundaries, querying `PointAward` and `Solve` records within `[start_dt, end_dt)`. Undated legacy baseline credit is excluded from period views, eliminating historical point entrenchment while preserving lifetime leaderboards. Deterministic tie-breaking is enforced by `(points, combined_score, streak, -user_id)`. Both extension and web clients include period selectors in the leaderboard header, cache results per `boardKey(tab, sort, period)`, and update synchronously. Added automated test suite `backend/tests/test_period_rankings.py`.

### Detailed Changes
1. **API Schema & Query Support (`backend/app/schemas.py`, `backend/app/main.py`)**:
   - Updated `LeaderboardResponse` schema to include `period: str = "all"`, `period_start: Optional[date] = None`, `period_end: Optional[date] = None`.
   - Updated `_compute_leaderboard()` to accept `period: str = "all"` ("all", "week", "month").
   - When `period in ("week", "month")`, computes IST start and end instants via `period_bounds(period)`.
   - Aggregates `PointAward` sums where `earned_at >= start_dt` and `earned_at < end_dt` (falling back to period-bounded `Solve` rows if awards have not yet been generated).
   - Breaks down Codeforces count/points and LeetCode points specifically for the period.
   - Enforces deterministic tie-breaking by `-user.id`.
   - Updated `GET /api/leaderboard`, `GET /api/friends/leaderboard`, and `GET /api/groups/{group_id}/leaderboard` to accept `period: str = Query("all", pattern="^(all|week|month)$")`.

2. **Frontend Extension & Web Clients (`extension/src/`, `web/app/`)**:
   - Updated API client wrappers `leaderboard(period)`, `friendsLeaderboard(userId, period)`, and `groupLeaderboard(groupId, period)`.
   - Added period state (`"all" | "week" | "month"`) to both clients.
   - Extended caching key to `boardKey(tab, sort, period)` preventing cache collisions across periods.
   - Added interactive period toggle button group ("All-time", "This Week", "This Month") in the leaderboard header.
   - Rebuilt extension and website bundles; synchronized all 4 ZIP distribution copies.

3. **Automated Testing & Verification (`backend/tests/test_period_rankings.py`)**:
   - Added test suite with 5 test cases verifying:
     - Lifetime rankings use total `User.points`.
     - Week and month period rankings accurately filter awards within `[start_dt, end_dt)`.
     - Out-of-period awards and undated baseline credit are excluded from period points.
     - Codeforces and LeetCode period points breakdown.
     - Group and friends leaderboards support the `period` query parameter.
     - Deterministic tie-breaking by `-user.id`.
     - Fast validation rejection (HTTP 422) for invalid period values.

### Verification Evidence
- `backend/tests/test_period_rankings.py`: 5 tests passed.
- Full backend test suite: 140 unit and integration tests passed.
- All 4 extension ZIP files verified byte-synchronized.
- PostgreSQL migration check: 10 migrations passed with advisory locking.
- Headless Chrome browser smoke test: extension and web UI passed with 0 runtime errors.
- Full `./scripts/run_checks.sh` verification passed cleanly.

---

## 2026-11-06 — Step: OPS-03 / M5 Step 7: Incremental Challenge Archive Backfill & Resumable Bounded Point Reconciliation

### Summary of Changes
Completed the remaining operational requirements of OPS-03: incremental daily challenge backfill with month-level coverage checks, and bounded all-user point reconciliation with persistent progress checkpointing and restart recovery. Added migration `20261106-checkpoints-v1` introducing table `job_checkpoints`. Created `backend/app/challenge_archive.py` with `is_month_covered()` and `backfill_daily_challenges_archive(incremental=True)` committing per-month to prevent redundant fetches. Upgraded `backend/app/point_calculator.py` with batch-bounded user reconciliation (`batch_size=50`) checkpointing `last_processed_id` per batch. Built two explicit CLI operator tools: `scripts/backfill_challenges.py` and `scripts/reconcile_points.py`. Added unit test suites `backend/tests/test_challenge_archive.py` and `backend/tests/test_point_reconciliation.py`.

### Detailed Changes
1. **Database Migration `20261106-checkpoints-v1` (`backend/app/migrations.py` & `backend/app/models.py`)**:
   - Created `JobCheckpoint` model and table `job_checkpoints` (`job_name`, `last_processed_id`, `batch_size`, `total_processed`, `status`, `metadata_json`, `started_at`, `updated_at`, `completed_at`).
   - Added migration function `migrate_checkpoints` registered in `run_all_migrations`.
   - Updated migration tests in `backend/tests/test_migrations.py` and `backend/tests/test_postgres_migrations.py` to reflect 10 registered migrations under PostgreSQL advisory lock.

2. **Incremental Challenge Archive Backfill (`backend/app/challenge_archive.py` & `scripts/backfill_challenges.py`)**:
   - `is_month_covered()` checks if all expected challenge days for a past or current month are already stored in `daily_challenges`.
   - `backfill_daily_challenges_archive()` scans from `start_year` (default: 2024), skips covered months, fetches only missing months from LeetCode GraphQL, and commits per month so interrupted runs resume cleanly from the next missing month without re-fetching.
   - Created CLI script `scripts/backfill_challenges.py` supporting `--start-year`, `--dry-run`, and `--force`.

3. **Bounded All-User Point Reconciliation (`backend/app/point_calculator.py` & `scripts/reconcile_points.py`)**:
   - Upgraded `recalculate_all_users_points()` to process users in bounded batches (default: 50) using `last_processed_id` cursor pagination.
   - Commits each batch to database and updates checkpoint; an interrupted job resumes from `last_processed_id` without recalculating already-completed batches.
   - Returns `ReconciliationResult` with integer coercion for backwards compatibility.
   - Guard against duplicate runs (`status="already_completed"`) unless `--force` is specified.
   - Created CLI script `scripts/reconcile_points.py` supporting `--job-name`, `--batch-size`, `--force`, and `--status`.

4. **Testing & Verification (`backend/tests/test_challenge_archive.py` & `backend/tests/test_point_reconciliation.py`)**:
   - Added 4 unit tests in `test_challenge_archive.py` covering past, current, and future month coverage, incremental skipping, and forced refetches.
   - Added 3 unit tests in `test_point_reconciliation.py` covering batch checkpointing, `already_completed` guard, and simulated interruption/resumption without re-running prior batches.

### Verification Evidence
- `backend/tests/test_challenge_archive.py`: 4 tests passed.
- `backend/tests/test_point_reconciliation.py`: 3 tests passed.
- `backend/tests/test_migrations.py`: 10 migrations verified.
- `backend/tests/test_postgres_migrations.py`: 10 migrations verified on PostgreSQL.
- Full 7-stage verification suite `./scripts/run_checks.sh` passed cleanly with 0 errors.

---

## 2026-11-06 — Step: OPS-02 / M5 Step 6: Stable Signing Keys, Session Predictability & Key Management

### Summary of Changes
Completed full operational key management, session stability, and rotation policies. Declared `JWT_SECRET` with `generateValue: true`, `ADMIN_SECRET` with `sync: false`, and `APP_ENV=production` in `render.yaml`. Published comprehensive operator documentation in `docs/KEY_MANAGEMENT.md` detailing key generation, rotation procedures, planned sign-out effects across extension and web clients, per-user targeted session version revocation, and hosting verification. Added automated unit tests in `backend/tests/test_auth.py` verifying HMAC-SHA256 signature rejection on key rotation, session version claims, and strict minimum 32-byte secret validation.

### Detailed Changes
1. **Hosting Blueprint Configuration (`render.yaml`)**:
   - Declared `JWT_SECRET` with `generateValue: true` to ensure Render automatically provisions and retains a persistent, cryptographically secure 256-bit signing key across deployments.
   - Declared `ADMIN_SECRET` with `sync: false` to require dashboard management without committing secrets to repository files.
   - Declared `APP_ENV: production` to prevent accidental ephemeral fallback.

2. **Key Management & Rotation Guide (`docs/KEY_MANAGEMENT.md`)**:
   - Specified cryptographic entropy requirements (at least 32 bytes / 256 bits).
   - Documented step-by-step fleet-wide key rotation procedure and its client impact (HTTP 401 Unauthorized returned on old tokens; extension and web clients cleanly clear cached credentials, show actionable session expired messages, and prompt for re-authentication).
   - Documented targeted per-user session revocation via `User.session_version` without disturbing other active users.
   - Detailed Render dashboard configuration verification.

3. **Automated Key & Session Tests (`backend/tests/test_auth.py`)**:
   - `test_key_rotation_invalidates_prior_tokens`: Verifies that rotating `JWT_SECRET` causes existing tokens to fail signature validation with `Invalid token signature`, while restoring the secret restores token validity.
   - `test_session_version_claim`: Validates that tokens carry and decode explicit session versions (`ver`).
   - `test_key_length_boundaries`: Validates fail-closed behavior on secrets below 32 bytes (31 bytes raises `RuntimeError`, 32 bytes succeeds).

### Verification Evidence
- `backend/tests/test_auth.py` passed with 10 unit tests in 0.004s.
- `scripts/check_hygiene.py` passed with 0 secret leaks and clean artifacts.
- `./scripts/run_checks.sh` full 7-stage suite passed.

---

## 2026-11-06 — Step: OPS-07 / M5 Step 5: Untracked Environments, Clean Staging & Automated Packaging

### Summary of Changes
Cleaned up repository virtual environments and generated build outputs. Verified that `test_env/`, `venv/`, and `linux_venv/` are completely untracked and enforced through comprehensive ignore rules in `.gitignore` and `.dockerignore`. Removed 5 abandoned historical build artifacts from `extension/dist/assets/` (reducing extension release ZIP archive size from 9.68 MB to 9.42 MB), automated `rm -rf dist` clean staging in `extension/package.json`, published the reproducible environment setup guide `docs/ENVIRONMENT_SETUP.md`, and ensured `scripts/sync_release.py` automates byte-identical mirroring and checksum verification across all 4 release ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Detailed Changes
1. **Virtual Environment Ignore Rules (`.gitignore` & `.dockerignore`)**:
   - Enhanced `.gitignore` to comprehensively ignore `venv/`, `linux_venv/`, `*venv*/`, `test_env/`, `*.pyd`, and local database files.
   - Enhanced `.dockerignore` to ignore `test_env`, `**/linux_venv`, `**/*venv*`, and `private-audit`.
   - Verified that `git ls-files test_env` and other venvs report zero tracked files.

2. **Clean Staging & Removal of Abandoned Assets**:
   - Removed obsolete tracked hash bundles in `extension/dist/assets/` (`index-Bxqks-9B.css`, `index-D4eizpAd.css`, `index-D4eizpAd.js`, `index-main.css`, `index-main.js`) using `git rm -r`.
   - Updated `extension/package.json` build script to wipe staging directory (`rm -rf dist && mkdir -p dist`) before copying active assets, preventing accumulation of stale build artifacts.
   - Package archive size optimized from 9,680,827 bytes to 9,429,382 bytes.

3. **Reproducible Environment Documentation (`docs/ENVIRONMENT_SETUP.md` & `README.md`)**:
   - Published `docs/ENVIRONMENT_SETUP.md` documenting prerequisite versions (Python 3.12+, Node 20+), step-by-step virtual environment creation and dependency installation (`pip install -r backend/requirements.txt -r backend/requirements-test.txt`), frontend package setup (`npm ci`), building, running the development server, and environment variable reference.
   - Linked setup and testing guides in `README.md`.

4. **Automated Package Mirroring & Equality Verification**:
   - Automated extension package generation and mirroring in `scripts/sync_release.py` and `npm --prefix extension run package`.
   - Verified byte-identity across all 4 ZIP locations (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`) with identical SHA-256 and MD5 hashes (`8790b066b41c6e89a0a9dd811ba18a72`).

### Verification Evidence
- `git ls-files test_env` returns empty (no tracked environment files in git).
- `scripts/check_hygiene.py` passed: 0 exposed secrets, valid gitignore rules, clean package archive.
- `scripts/sync_release.py --verify` passed: all 4 ZIP copies match with 0 divergence.
- Full verification suite `./scripts/run_checks.sh` passed: 125 backend tests, 8 PostgreSQL tests, 26 extension tests, and browser smoke test (0 runtime errors).

---

## 2026-11-06 — Step: OPS-06 / M5 Step 4: Regression Coverage, Continuous Integration & Hygiene Checks

### Summary of Changes
Established full continuous regression checks and automated quality gates across backend services, client packages, database migrations, and repository hygiene. Added GitHub Actions CI configuration (`.github/workflows/ci.yml`) with pinned permissions and native PostgreSQL service container, created a comprehensive local verification runner (`scripts/run_checks.sh`), built an automated secret and package hygiene scanner (`scripts/check_hygiene.py`), and published testing and contributor guidance (`docs/TESTING.md`) alongside a manual extension verification checklist (`docs/MANUAL_VERIFICATION_CHECKLIST.md`).

### Detailed Changes
1. **`.github/workflows/ci.yml`**:
   - Pinned deliberate minimal permissions (`contents: read`).
   - `backend-checks` job: runs 125 backend tests in Python 3.12 with SQLite & synthetic fixtures, and spins up a native PostgreSQL 16 service container to run concurrent multi-threaded advisory lock migration checks with `LEETSTREAK_TEST_POSTGRES_URL`.
   - `frontend-checks` job: runs TypeScript type check (`npm --prefix web run check`), 26 client unit tests (`node --test extension/tests/*.test.mjs`), website build (`npm --prefix web run build`), extension packaging (`scripts/sync_release.py --package`), and release archive consistency & checksum validation (`scripts/sync_release.py --verify`).
   - `hygiene-checks` job: executes repository secret and release artifact cleanliness checks (`scripts/check_hygiene.py`).

2. **`scripts/check_hygiene.py`**:
   - Automated validator scanning all tracked source files for private cryptographic keys, live API tokens, production credentials, and forbidden file names (`.env.production`, `.env.local`, SSH keys).
   - Validates release package `leetstreak.zip` to ensure it contains no `.git`, `.env`, `node_modules`, `.DS_Store`, or `__pycache__` artifacts.
   - Verifies `.gitignore` properly excludes virtual environments (`test_env`), `node_modules`, `.env`, and local `.db` files.

3. **`scripts/run_checks.sh`**:
   - One-command local runner executing the entire 7-stage verification suite:
     1. Secret and artifact hygiene scanner
     2. Website TypeScript type check
     3. Client unit tests (26 tests)
     4. Web build and extension packaging
     5. Release consistency and byte-identical ZIP checks
     6. Backend unit tests (125 tests)
     7. Native PostgreSQL migration and concurrency checks
     - Optional bonus: Headless Chrome browser smoke test (extension popup & web dashboard).

4. **`docs/TESTING.md`**:
   - Comprehensive testing and contributor documentation explaining synthetic fixtures (fictional identities, `@example.com` email addresses, mocked external providers), deterministic isolation, test module mapping, and local verification instructions.

5. **`docs/MANUAL_VERIFICATION_CHECKLIST.md`**:
   - Explicit manual checklist for browser-only behaviors: Developer Mode unpacked loading, popup dimensions and Material Design theme, points rulebook modal, update banner and manual reload guide, session persistence across popup closes, password revocation, Codeforces verification challenge, study plan playlists, direct friends search, and LeetCode in-page content script DOM injection without CSP violations.

### Verification Evidence
- `./scripts/run_checks.sh` executed cleanly and passed 100% of all stages:
  - Hygiene scan: 0 secrets, clean release package, valid gitignore.
  - TypeScript check: 0 errors (`tsc --noEmit`).
  - Client unit tests: 26 tests passed in 306ms.
  - Build & packaging: website and extension built, 4 ZIP copies mirrored and verified.
  - Release consistency: canonical version 1.1.0 verified across metadata and archives.
  - Backend tests: 125 tests passed in 43s.
  - Native PostgreSQL tests: 8 tests passed in 1.3s against PostgreSQL 16.
  - Headless Chrome browser smoke test: extension and website tested with 0 console runtime errors.

---

## 2026-11-06 — Step: OPS-05 / M5 Step 3: Authoritative Release Metadata, Version Consistency & Update Truthfulness

### Summary of Changes
Established a single authoritative source of truth for release metadata in `backend/app/release_metadata.py`, upgraded canonical semantic versioning across the project from `1.0.0` to `1.1.0` (reflecting all M1-M4 multi-platform, study plan, and friendship features), retired dead Omaha XML / fictitious `.crx` endpoints with HTTP 410 Gone, differentiated mandatory vs recommended updates, provided clear step-by-step reload guides for unpacked extension installations, synchronized and checksummed all 4 ZIP copies, and published `docs/RELEASE_PROCEDURE.md` and automated release validation tooling `scripts/sync_release.py`.

### Detailed Changes
1. **`backend/app/release_metadata.py`**:
   - Single authoritative source of truth defining `SEMANTIC_VERSION = "1.1.0"`, `MIN_SUPPORTED_VERSION = "1.0.0"`, `RELEASE_TAG = "v1.1.0"`, recorded Git commit revision, release notes, download URL, update channel, and update instructions.
   - Dynamically computes SHA-256 and MD5 checksums and byte size of the served `leetstreak.zip` package.
   - Provides `get_release_metadata()` returning comprehensive release metadata dictionary.

2. **`backend/app/releases.py`**:
   - Integrated with `release_metadata.py` while preserving existing `"integration-2026-11-05"` notice for test compatibility and adding `"v1.1.0"`.

3. **`backend/app/main.py`**:
   - Updated `/api/extension/version` to serve canonical `get_release_metadata()`, including artifact checksums and truthful update instructions.
   - Retired legacy `/api/extension/updates.xml` endpoint with HTTP 410 Gone and explicit deprecation reason ("CRX auto-update manifest has been retired. LeetStreak distributes via manual unpacked ZIP or official browser store releases.").
   - Updated `/api/config/app` dynamic config version to `SEMANTIC_VERSION` ("1.1.0").

4. **Package & Manifest Version Alignment**:
   - `extension/manifest.json`: version bumped to `"1.1.0"`.
   - `extension/package.json`: version bumped to `"1.1.0"`, added `"package"` script to automate building and byte-identical mirroring across all 4 locations.
   - `web/package.json`: version bumped to `"1.1.0"`.

5. **Client Update Banner & Instructions**:
   - `extension/src/App.tsx`: updated fallback version to `"1.1.0"`. Added comparison against `min_supported_version` to render `⚠️ Required Update: v{latest_version}` if client is unsupported, and `🚀 Update v{latest_version} Available` if newer. Added toggleable step-by-step instructions explaining how to update unpacked installations (download ZIP, extract, click reload in `chrome://extensions`).
   - `extension/src/lib/api.ts` & `web/app/lib/api.ts`: updated `VersionCheckResponse` to include `channel`, `update_instructions`, and `checksums`, and made `crx_url` optional.
   - `README.md`: added "How to Update an Existing Installation" section clearly separating unpacked ZIP reload procedures from automatic store-managed updates.

6. **Release Tooling & Procedure**:
   - `scripts/sync_release.py`: automated CLI utility to synchronize versions across metadata, manifests, and package files (`--sync`), package and mirror zip archives (`--package`), and verify that all versions and all 4 zip archives are byte-identical (`--verify`).
   - `docs/RELEASE_PROCEDURE.md`: comprehensive guide detailing authoritative metadata, development vs production branching rules, rollback-compatible deployment order (additive DB migrations -> deploy API -> verify metadata -> build clients -> distribute), artifact verification, and distribution channels.

7. **`backend/tests/test_release_metadata.py`**:
   - Added 7 unit tests covering canonical metadata endpoint, config version, 410 Gone for retired XML, valid zip download with root manifest inspection, release notice registry, byte-identical mirror verification across all 4 locations, and client-side version comparison logic (older client, current client, unsupported client, future client).

### Verification Evidence
- `scripts/sync_release.py --verify` passed: canonical version 1.1.0 verified across metadata, `extension/manifest.json`, `extension/package.json`, `web/package.json`, and all 4 ZIP archives confirmed byte-identical (MD5: `2a67b5c41d77362697bc036aa7c36153`, 9,680,827 bytes).
- 125 backend tests passed with zero failures (`backend/tests`), including all 7 release metadata tests.
- 8 native PostgreSQL tests passed in `test_postgres_migrations.py`.
- 26 extension unit tests passed (`extension/tests/*.test.mjs`).
- Browser smoke test (Playwright in headless Chrome) passed on both extension and website with 0 runtime errors.

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

---

## 2026-11-06 — Step: M3-02 / UI-05, UI-06, UI-07, FEAT-09: Request Ordering, Friend Activity Merge Recency, and Session Guidance

### Summary of Changes
Resolved race conditions in leaderboard switching and caching (UI-05), corrected friend activity lookup failure masking and empty state reporting (UI-06), fixed activity deduplication to preserve the most recent solve timestamp across multiple sources (UI-07), and added clear in-app guidance on browser session requirements for study-plan progress (FEAT-09). In `extension/src/App.tsx` and `web/app/App.tsx`, implemented generation counters (`fullLoadReqRef` and `leaderboardReqRef`) that automatically drop superseded, out-of-order network responses, and keyed in-memory and persistent leaderboard caches by account ID, tab, and sort mode (`points` vs `streak`). In `extension/src/progress/Progress.tsx`, rewrote `FriendsActivity` so partial failures on one platform (LeetCode vs Codeforces) do not discard successful data from the other, preserved existing items across refreshes, and merged duplicate problem entries preserving the newest solve timestamp. Added explanatory copy detailing public profile sync versus complete browser-session plan history. This completes Milestone M3 (with deferred alert items UI-03, UI-04, FEAT-07 untouched as agreed).

### Detailed Changes
1. **`extension/src/App.tsx` & `web/app/App.tsx` (UI-05)**:
   - Added `leaderboardReqRef = useRef(0)` and `fullLoadReqRef = useRef(0)` to track active request IDs.
   - Dropped obsolete responses in both `loadData` and `fetchLeaderboardOnly` when `reqId !== activeReqRef.current`.
   - Combined cache keys to include sort mode: `boardKey = (tab, sort) => `${String(tab)}_${sort}``.
   - Scoped persistent cache keys by user ID: `codestreak_cached_board_${userId}_${key}` and `codestreak_cached_dash_${userId}`.
   - Updated `changeTab` and initial restore to use combined keys.

2. **`extension/src/progress/Progress.tsx` (UI-06 & UI-07 & FEAT-09)**:
   - Isolated LeetCode and Codeforces lookups per friend in `FriendsActivity`: failures on one platform no longer suppress valid results from the other.
   - Recorded `failures++` honestly so network/lookup failures are distinguishable from empty activity ("0 solves").
   - Maintained previously loaded activity during refreshes instead of wiping to an empty screen.
   - When deduplicating solves across public submissions and database ledger rows for the same problem, compared `Number(solve.timestamp) > Number(existing.timestamp)` and retained the latest timestamp.
   - Added session requirements explanatory note: "Public solves sync automatically via public profile. Complete study-plan completion requires signing in to @{username} on LeetCode in this browser."

3. **`extension/tests/ordering.test.mjs`**:
   - Added 3 unit tests verifying:
     1. UI-07 solve deduplication preserving the latest timestamp.
     2. UI-06 partial lookup failure preserving successful platform results.
     3. UI-05 request sequence counters invalidating stale superseded responses.

4. **Distribution Packages**:
   - Rebuilt extension bundle via `npm run build`.
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- Ran `tsc --noEmit` on both `extension` and `web` with 0 errors.
- Ran all 26 extension unit tests (6 auth tests, 6 storage tests, 3 ordering tests, 11 progress tests) — 26 passed, 0 failed.
- Ran backend test suite: 91/91 tests passed (`backend/tests`).
- Built web application cleanly (`npm run build` -> `backend/web`).

---

## 2026-11-06 — Step: M4-01 / FEAT-01: Account-Backed Study Plans & Playlists Persistence

### Summary of Changes
Implemented durable, account-backed persistence and bidirectional sync for user study plans, custom playlists (imported via URL links or pasted links), library subscriptions (followed plans), exclusions (hidden/removed starter plans), and external item completion (manual checkboxes). Previously, custom study plans and external completion lived strictly in local browser storage (`localStorage`), meaning that switching browsers, clearing caches, or signing in from another machine lost all custom plans and completion. Now, the backend database is the authoritative store for user progress and custom plans, while local storage serves as a fast offline cache and outbox. Existing local custom plans and progress are seamlessly uploaded and migrated to the backend account on first load with zero data loss.

### Detailed Changes
1. **`backend/app/models.py`**:
   - Added `UserProgress` model (`user_progress` table):
     - `user_id`: PK (Integer, FK `users.id` with `ondelete="CASCADE"`).
     - `followed_plans`: JSON array of followed plan slugs.
     - `hidden_plans`: JSON array of hidden/removed plan slugs.
     - `manual_solves`: JSON array of externally checked problem slugs.
     - `version`: Integer optimistic concurrency counter (default 1).
     - `updated_at`: DateTime UTC timestamp.
   - Added `UserCustomPlan` model (`user_custom_plans` table):
     - `id`: PK (Integer).
     - `user_id`: Integer, FK `users.id` with index.
     - `slug`: String(120), index.
     - `name`: String(200).
     - `source`: String(40) (e.g. `leetcode`, `takeuforward`, `codeforces`, `external`).
     - `source_url`: String(1000).
     - `plan_json`: JSON structure containing all `planSubGroups` and questions.
     - `created_at` & `updated_at`: DateTime UTC timestamps.
     - Unique constraint on `(user_id, slug)`.
   - Linked `user_progress` (uselist=False) and `custom_plans` (list) relationships to `User`.

2. **`backend/app/migrations.py`**:
   - Added `migrate_progress(target)` (version `20261106-progress-v1`): creates `user_progress` and `user_custom_plans` tables idempotently under advisory lock.
   - Registered `migrate_progress` in `run_all_migrations`.

3. **`backend/app/schemas.py`**:
   - Added `StudyQuestionSchema`, `StudyPlanSubGroupSchema`, `StudyPlanPayload`, `ProgressUpdateRequest`, and `ProgressResponse`.
   - Enforced input bounds: max 50 custom plans per user, max 200 subgroups per plan, max 1000 questions per plan, max 1000 followed/hidden slugs, max 10,000 manual solves.

4. **`backend/app/main.py`**:
   - Added authenticated endpoints (all requiring `actor.id == user_id`):
     - `GET /api/users/{user_id}/progress`: returns user followed, hidden, manual solves, custom plans, and version.
     - `PUT /api/users/{user_id}/progress`: updates followed, hidden, and/or manual solves, bumping version and timestamp.
     - `POST /api/users/{user_id}/plans`: saves/upserts a custom study plan or playlist, automatically adds to followed and removes from hidden.
     - `DELETE /api/users/{user_id}/plans/{slug}`: deletes custom plan, removes from followed; if starter plan, records in hidden.
     - `POST /api/users/{user_id}/plans/restore-starters`: unhides default starter plans.
   - Updated `delete_user_account` to clean up `UserProgress` and `UserCustomPlan`.

5. **`extension/src/lib/api.ts` & `web/app/lib/api.ts`**:
   - Added `BackendProgressResponse` interface and `getProgress`, `updateProgress`, `saveCustomPlan`, `deleteCustomPlan`, and `restoreStarters` client methods.

6. **`extension/src/progress/Progress.tsx`**:
   - On load: loads local storage immediately for zero-latency rendering, then calls `api.getProgress(userId)`. Merges server-confirmed custom plans and progress; automatically uploads any local custom plans or manual solves not yet on the server, migrating existing users seamlessly.
   - On add plan: persists locally and calls `api.saveCustomPlan(userId, imported)`.
   - On remove plan: removes locally and calls `api.deleteCustomPlan(userId, plan.slug)`.
   - On restore starter plans: restores locally and calls `api.restoreStarters(userId)`.
   - On toggle follow: updates locally and calls `api.updateProgress(userId, { followed })`.
   - On toggle external item checkmark: updates locally and calls `api.updateProgress(userId, { manual })`.

7. **`backend/tests/test_progress_plans.py`**:
   - Added 7 comprehensive isolated tests covering auth/ownership enforcement, empty initialization, update persistence, custom plan saving and auto-following, plan deletion, starter plan hiding/restoration, and plan bounds limit checks.
   - Updated migration tests in `test_migrations.py` and `test_postgres_migrations.py` for version `20261106-progress-v1` and 6 total migrations.

8. **Distribution Packages**:
   - Built extension (`npm --prefix extension run build`).
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).
   - Built web application cleanly (`npm --prefix web run check && npm --prefix web run build`).

### Verification Evidence
- 90 backend tests passed with zero failures (`backend/tests`).
- 8 native PostgreSQL tests passed in `test_postgres_migrations.py`.
- 26 extension unit tests passed (`extension/tests/*.test.mjs`).
- `tsc --noEmit` on both `extension` and `web` passed cleanly with 0 errors.
- Verified byte-identical ZIP copies (9,669,812 bytes).

---

## 2026-11-06 — Step: M4-02 / FEAT-02: Website Progress Section with Study Plans, Playlists & Friends Activity

### Summary of Changes
Added the full Progress experience to the web application (`web/app/Progress.tsx`), bringing complete feature parity with the browser extension while using the account-backed persistence layer built in FEAT-01. Previously, the website lacked study plans, custom playlists, and question-level completion tracking altogether. Now, authenticated web users can browse their account-backed study plans, follow/unfollow curated sheets, create custom playlists by pasting question links or choosing catalog slugs, search and filter problems by completion status or difficulty, expand/collapse subgroups, toggle manual checkboxes for external items, and view live friends activity above playlists. All state changes synchronize bidirectionally with the backend and extension.

### Detailed Changes
1. **`web/app/progressData.ts`**:
   - Extracted pure plan data models (`StudyPlan`, `StudyQuestion`, `ProgressState`).
   - Copied bundled catalog sheets (`strivers-a2z.json` and `study-plans.json`) to `web/app/data/`.
   - Provided pure helpers: `parsePlanSlug`, `publicUrl`, `importedPlanSlug`, `leetcodeSlug`, `questionUrl`, `questionSolved`, `planCounts`, `visiblePlans`, `planFromLinks`, and `fetchBundledOrCatalogPlan`.
   - Handled web environment CORS constraints: bundled catalog plans load instantly offline, pasted question links are parsed locally via `planFromLinks`, and uncataloged external link scans provide a clear actionable fallback explaining that links can be pasted directly or scanned via the extension.

2. **`web/app/Progress.tsx`**:
   - Built the `WebsiteProgress` component rendering:
     - Friends activity feed ("What are my friends up to?") with recent friend solves, platform tags, and relative timestamps.
     - Study plans header with "+ Add Plan" modal and "Restore Starters" action when default plans are hidden.
     - Add plan form supporting catalog slugs and pasted question links.
     - Horizontal grid of plan cards with progress bar, solved count, completion percentage, and active selection.
     - Active plan detail panel with Next-up recommendation, Follow/Unfollow toggle, and Remove plan action.
     - Search and filter bar (All, Solved, To Do, External).
     - Subgroup sections with collapsible headers and solved badges.
     - Question rows with problem links, difficulty tags, and interactive checkboxes for external items.

3. **`web/app/App.tsx` & `web/main.tsx`**:
   - Mounted `WebsiteProgress` under `<section className="section workspace-progress-section" id="progress">`.
   - Added `◉ Study plans` navigation item in `web/main.tsx` workspace sidebar.

4. **`web/app/lib/api.ts`**:
   - Added `codeforcesSolves` endpoint method and verified full parity with extension API client.

5. **`web/app/App.css`**:
   - Added responsive styling matching the dark charcoal/purple theme, Outfit headings, Inter controls, collapsible cards, and mobile-friendly layout.

### Verification Evidence
- Built website cleanly (`npm --prefix web run check && npm --prefix web run build`).
- `tsc --noEmit` on `web` passed cleanly with 0 errors.
- Ran browser smoke tests (`backend/tests/browser_smoke.py` in headless Chrome via Playwright) across both extension (380px) and website (1366px): both passed with 0 runtime errors.
- 90 backend tests and 26 extension tests passed.

---

## 2026-11-06 — Step: M4-03 / FEAT-04: Coding-Account Ownership Verification & Claim Recovery

### Summary of Changes
Implemented cryptographic one-time token verification for LeetCode and Codeforces coding accounts, solving the account-takeover and preclaimed handle squatter vulnerability. Previously, anyone could enter any public LeetCode or Codeforces handle during signup or in settings without proving ownership, blocking legitimate owners from claiming their own handles on Codeforces (where handles are unique across LeetStreak accounts) and receiving unearned leaderboard standing.

Because neither platform provides OAuth for third-party extensions, ownership is proven via a zero-credential, expiring one-time challenge token (`codestreak-verify-<hex>`). Users place this code temporarily in their public profile bio (`aboutMe` or `realName` on LeetCode; `organization`, name, or city on Codeforces). Once verified by the backend server, the account receives a verified badge (✓) on leaderboards and profile cards. If an unverified user previously preclaimed a handle, the true owner who proves ownership through the challenge reclaims the handle, clearing the unverified squatter's solves and points.

### Detailed Changes
1. **`backend/app/models.py`**:
   - Added verification tracking columns to `User`:
     - `leetcode_verified_at`, `leetcode_verification_token`, `leetcode_verification_expires_at`, `leetcode_pending_handle`
     - `codeforces_verified_at`, `codeforces_verification_token`, `codeforces_verification_expires_at`, `codeforces_pending_handle`

2. **`backend/app/migrations.py`**:
   - Added migration `migrate_verification` (version `20261106-verification-v1`).
   - Included in `run_all_migrations` registry under PostgreSQL advisory lock / local RLock.
   - Updated migration count in `test_migrations.py` and `test_postgres_migrations.py` to 7 versioned migrations.

3. **`backend/app/leetcode_client.py` & `backend/app/codeforces_client.py`**:
   - Added `check_leetcode_profile_verification(username, token)`: checks LeetCode GraphQL public profile (`aboutMe` and `realName`).
   - Added `check_codeforces_profile_verification(handle, token)`: checks Codeforces API `user.info` public fields (`organization`, `firstName`, `lastName`, `city`).

4. **`backend/app/schemas.py`**:
   - Added `InitiateVerificationRequest`, `InitiateVerificationResponse`, `ConfirmVerificationRequest`, `ConfirmVerificationResponse`, `VerificationStatusResponse`, and `PlatformVerificationStatus`.
   - Added `leetcode_verified: bool` and `codeforces_verified: bool` to `DashboardResponse`, `RegisterResponse`, `LeaderboardEntry`, and `GroupMemberSchema`.

5. **`backend/app/main.py`**:
   - Added endpoints:
     - `POST /api/users/{user_id}/verify-handle/initiate`: generates an expiring 15-minute challenge token, bound to the user ID and requested handle.
     - `POST /api/users/{user_id}/verify-handle/confirm`: queries the provider's public profile, validates token presence, marks the handle verified with timestamp, and executes preclaim dispute recovery if the handle was held by an unverified account.
     - `GET /api/users/{user_id}/verify-handle/status`: returns verification status, pending handles, tokens, and expiry for both platforms.
   - Handle modifications in settings reset verification state to prevent handle-swap inheritance.

6. **Client UI & APIs (`extension` & `web`)**:
   - Updated `api.ts` in both clients with `initiateVerification`, `confirmVerification`, and `verificationStatus`.
   - Added verification badges (✓) with distinct tooltips on user cards, leaderboards, and profile modals.
   - Added interactive Verification Challenge modal in Settings of both extension and website, complete with one-click token copying, direct deep-links to provider profile settings, and instantaneous confirmation feedback.

7. **Distribution Packages**:
   - Built web application (`npm --prefix web run check && npm --prefix web run build`).
   - Built extension (`npm --prefix extension run build`).
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- 99 backend tests passed with zero failures (`backend/tests`), including 9 isolated verification tests in `backend/tests/test_verification.py`.
- 8 native PostgreSQL tests passed in `test_postgres_migrations.py`.
- 26 extension unit tests passed (`extension/tests/*.test.mjs`).
- Browser smoke test (Playwright in headless Chrome) passed on both extension and website with 0 runtime errors.
- Verified byte-identical ZIP copies across all 4 locations.

---

## 2026-11-06 — Step: M4-04 / FEAT-05: Allow Codeforces Unlinking & Score Reconciliation

### Summary of Changes
Enabled users to disconnect a previously connected Codeforces handle from their account in both the browser extension and web application. Previously, once a Codeforces handle was connected, users could replace it with another handle but had no mechanism to disconnect it or clear its associated data, locking the handle claim indefinitely and leaving users with no way to remove unwanted Codeforces solves or points.

Disconnecting now cleanly and atomically detaches the handle, bumps `codeforces_account_version` to immediately invalidate and discard any running or queued sync jobs, removes all associated Codeforces `Solve` records, `PlatformActivity` rows, and `PointAward` rows, resets verification state, releases the unique handle claim for other accounts to claim or verify, and recalculates the user's score based strictly on remaining LeetCode solves without affecting LeetCode history, streaks, or account integrity.

### Detailed Changes
1. **`backend/app/schemas.py`**:
   - Added `UnlinkCodeforcesResponse` schema (`status: str`, `message: str`, `points: float`).

2. **`backend/app/main.py`**:
   - Added `DELETE /api/users/{user_id}/codeforces` and alias `DELETE /api/users/{user_id}/codeforces-username`.
   - Requires authenticated user self-authorization (`require_self`).
   - Validates that a Codeforces account is linked (400 if none).
   - Under `user_sync_lock`:
     - Clears `codeforces_username`, `codeforces_verified_at`, `codeforces_verification_token`, `codeforces_verification_expires_at`, `codeforces_pending_handle`, `codeforces_last_sync`, `codeforces_last_full_sync`, `codeforces_linked_at`, and `codeforces_sync_error`.
     - Increments `codeforces_account_version += 1` to cancel in-flight jobs.
     - Calls `clear_tracking(db, user_id, "codeforces")` and deletes `Solve` and `PlatformActivity` rows for `codeforces`.
     - Calls `recalculate_user_points(user, db)`.

3. **`backend/tests/test_unlink.py`**:
   - Created 4 unit tests covering unauthenticated (401), cross-user forbidden (403), no connected account (400), and successful unlink (200).
   - Verifies complete removal of CF solves and platform activity, bump of `codeforces_account_version`, preservation of LeetCode solves, and exact point recalculation.

4. **Client API & UI (`web` & `extension`)**:
   - Added `unlinkCodeforces(userId: number)` in `web/app/lib/api.ts` and `extension/src/lib/api.ts`.
   - Added `Disconnect Codeforces` button in the Codeforces settings card when a handle is connected.
   - Added a confirmation modal explaining exact impact (removal of CF solves and rating points, preservation of LeetCode streak and solves, release of the handle).
   - Added `.danger-text-btn` styling in `web/app/App.css` and `extension/src/App.css`.

5. **Distribution Packages**:
   - Built web application (`npm --prefix web run check && npm --prefix web run build`).
   - Built extension (`npm --prefix extension run build`).
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- 103 backend tests passed with zero failures (`backend/tests`), including 4 tests in `backend/tests/test_unlink.py`.
- 8 native PostgreSQL tests passed in `test_postgres_migrations.py`.
- 26 extension unit tests passed (`extension/tests/*.test.mjs`).
- Browser smoke test (Playwright in headless Chrome) passed on both extension and website with 0 runtime errors.
- Verified byte-identical ZIP copies across all 4 locations.

---

## 2026-11-06 — Step: M4-05 / FEAT-10: Direct Friendships Without Groups

### Summary of Changes
Implemented owner-requested backend-persisted direct friendships independently of groups. Previously, the friends leaderboard and "What are my friends up to?" activity feed strictly aggregated members of shared groups, meaning users could not connect as friends or follow each other's progress without first creating and joining a shared private group.

Direct friendships are now first-class, account-backed relationships that persist across website and extension sessions. Users can search for peers by public name, LeetCode handle, or Codeforces handle without exposing private account details (emails, passwords, reset OTPs, or group codes). A full mutual friendship flow is provided (send request, crossed-request auto-acceptance, accept, decline, cancel outgoing, and remove friend). The friends leaderboard and activity feed merge and deduplicate connections from both direct friendships and shared groups.

### Detailed Changes
1. **`backend/app/models.py`**:
   - Added `Friendship` model with `user_id`, `friend_id`, `status` ("pending" | "accepted"), `action_user_id`, `created_at`, `updated_at`.
   - Includes unique constraint on `(user_id, friend_id)` ensuring normalized ordering (`user_id < friend_id`) and preventing duplicate relationship records.

2. **`backend/app/migrations.py`**:
   - Added `migrate_friendships(target)` (version `20261106-friendships-v1`): creates `friendships` table and indices (`idx_friendships_user`, `idx_friendships_friend`, `idx_friendships_status`).
   - Integrated into `run_all_migrations` (now 8 atomic migrations).
   - Updated migration count and version list in `test_migrations.py` and `test_postgres_migrations.py`.

3. **`backend/app/schemas.py`**:
   - Added `FriendSummary`, `FriendRequestItem`, `FriendsListResponse`, `SendFriendRequest`, `UserSearchResult`, and `FriendshipActionResponse`.

4. **`backend/app/main.py`**:
   - Added `GET /api/users/search`: safe public search filtering out the caller and returning relationship status (`friends`, `pending_sent`, `pending_received`, or `null`).
   - Added `GET /api/users/{user_id}/friends`: returns direct friends with streak/points, incoming requests, and outgoing requests.
   - Added `POST /api/users/{user_id}/friends/request`: creates pending request or auto-accepts crossed request.
   - Added `POST /api/users/{user_id}/friends/{request_id}/accept`: accepts incoming request.
   - Added `POST /api/users/{user_id}/friends/{request_id}/decline`: declines incoming request.
   - Added `POST /api/users/{user_id}/friends/{request_id}/cancel`: cancels outgoing request.
   - Added `DELETE /api/users/{user_id}/friends/{target_user_id}`: removes friendship.
   - Updated `GET /api/friends/leaderboard` to combine shared-group members and direct accepted friends with deduplication.

5. **`backend/tests/test_friendships.py`**:
   - Added 8 unit tests covering user search, friend request creation, crossed-request promotion, request cancellation, request decline, friend removal, friends leaderboard inclusion without groups, and deduplication when a user is both a group member and a direct friend.

6. **Web & Extension Frontend (`web` & `extension`)**:
   - Added client methods in `web/app/lib/api.ts` and `extension/src/lib/api.ts`: `searchUsers`, `getFriends`, `sendFriendRequest`, `acceptFriendRequest`, `declineFriendRequest`, `cancelFriendRequest`, `removeFriend`.
   - Updated `web/app/Progress.tsx` and `extension/src/progress/Progress.tsx` to include direct friends in "What are my friends up to?".
   - Added `FriendsModal` with 3 tabs: "Friends", "Requests" (with incoming/outgoing subsections and pending badge count), and "Find Friends" (live search with status badges and action buttons).
   - Added `👥 Friends` button in the leaderboard sort bar with pending request counter badge.
   - Added direct friends summary banner when on the "My Friends" leaderboard tab.
   - Added styling in `web/app/App.css` and `extension/src/App.css`.

7. **Distribution Packages**:
   - Built web application (`npm --prefix web run check && npm --prefix web run build`).
   - Built extension (`npm --prefix extension run build`).
   - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- 111 backend tests passed with zero failures (`backend/tests`), including all 8 friendship tests in `backend/tests/test_friendships.py`.
- 8 native PostgreSQL tests passed in `test_postgres_migrations.py`.
- 26 extension unit tests passed (`extension/tests/*.test.mjs`).
- Browser smoke test (Playwright in headless Chrome) passed on both extension and website with 0 runtime errors, successfully fetching and verifying friends endpoints.
- Verified byte-identical ZIP copies across all 4 locations.

---

## 2026-11-06 — Step: M5-02 / OPS-04: Multi-Process Sync Coordination, Scheduler Leases & Shared Provider Rate Limits

### Summary of Changes
Resolved process-local scheduling, sync concurrency, and rate-limiting limitations across multi-worker deployments. Previously, scheduler jobs, per-user sync locks, and Codeforces request spacing were held solely in process memory via `asyncio.Lock()`. If multiple worker processes or service instances were deployed, overlapping scheduler runs (`poll_all_users`, `refresh_zerotrac_dataset`) would fire concurrently, multiple processes could sync the same user simultaneously with competing row updates, and Codeforces requests from different workers could violate the 2-second rate limit, triggering HTTP 429 Too Many Requests.

Introduced durable, distributed job leases and rate-limiting coordination in `backend/app/leases.py` backed by atomic transactions against a new `job_leases` table. Short, sub-millisecond database transactions acquire and release leases without holding open database row locks or connections across slow remote network requests. Dead worker leases automatically expire after their TTL and are cleanly reclaimed. Coordinated per-account sync leases return 409 Conflict when a sync is already in progress, background scheduled jobs skip execution when a distributed job lease is active, and provider rate limits (such as Codeforces 2-second spacing) are enforced deployment-wide across all worker processes.

### Detailed Changes
1. **`backend/app/models.py`**:
   - Added `JobLease` model with `resource_key` (primary key), `owner_id`, `acquired_at`, and `expires_at` (indexed).

2. **`backend/app/migrations.py`**:
   - Added `migrate_leases(target)` (version `20261106-leases-v1`): creates `job_leases` table and index on `(resource_key, expires_at)`.
   - Updated `run_all_migrations` (now 9 atomic migrations).
   - Updated migration counts and expected versions in `test_migrations.py` and `test_postgres_migrations.py`.

3. **`backend/app/leases.py`**:
   - Implemented `acquire_lease(resource_key, ttl_seconds, owner_id, db)`: atomic acquisition and renewal using immediate transactions without holding long-lived DB connections.
   - Implemented `release_lease(resource_key, owner_id, db)`: atomic release.
   - Implemented `renew_lease(resource_key, owner_id, extension_seconds, db)` and `is_lease_active(resource_key, db)`.
   - Implemented `user_sync_lease(user_id, ttl_seconds, wait_timeout)`: async context manager combining fast in-memory locking with distributed database leasing.
   - Implemented `acquire_provider_rate_limit(provider, min_interval, max_wait)`: multi-process distributed rate limiter enforcing minimum spacing between calls across all workers.

4. **`backend/app/codeforces_client.py`**:
   - In `codeforces_request`, integrated `acquire_provider_rate_limit("codeforces", min_interval=2.1)` to ensure all outgoing requests across all worker processes strictly respect Codeforces' rate limits.

5. **`backend/app/codeforces_sync.py`**:
   - Replaced process-local `_locks` dictionary with `UserSyncLock` delegating to `user_sync_lease` and `is_lease_active`.
   - Updated `sync_codeforces_user` to coordinate under `user_sync_lease` and support `already_leased=True` flag for re-entrant callers.

6. **`backend/app/scheduler.py`**:
   - Updated `poll_all_users` to acquire distributed lease `scheduler:job:poll_all_users` (300s TTL), gracefully skipping overlapping runs across worker processes.
   - Updated `poll_user` to coordinate under `user_sync_lease(user.id, ttl_seconds=120.0)` and pass `already_leased=True` to downstream Codeforces sync.

7. **`backend/app/contest_ratings.py`**:
   - Updated `refresh_zerotrac_dataset` to acquire distributed lease `scheduler:job:refresh_zerotrac_dataset` (600s TTL), preventing concurrent dataset downloads across workers.

8. **`backend/app/main.py`**:
   - In `POST /api/users/{user_id}/sync`, coordinated under `user_sync_lease(user_id, wait_timeout=0.0)`. Returns HTTP 409 Conflict ("A sync is already in progress for this user.") if a sync is already running.

9. **`backend/tests/test_coordination.py`**:
   - Added 7 unit tests covering lease acquisition, mutual exclusion, owner renewal, dead-worker expiry recovery, context manager cleanup, scheduler job skipping, cross-process provider rate limiting spacing, and sync endpoint 409 conflict handling.

10. **Distribution Packages**:
    - Built web application (`npm --prefix web run check && npm --prefix web run build`).
    - Built extension (`npm --prefix extension run build`).
    - Synchronized all 4 ZIP copies (`./leetstreak.zip`, `./leetstreak_dist.zip`, `./extension/leetstreak.zip`, `./backend/app/leetstreak.zip`).

### Verification Evidence
- 118 backend tests passed with zero failures (`backend/tests`), including all 7 coordination tests in `backend/tests/test_coordination.py` and 9 migration tests.
- 8 native PostgreSQL tests passed in `test_postgres_migrations.py`.
- 26 extension unit tests passed (`extension/tests/*.test.mjs`).
- Browser smoke test (Playwright in headless Chrome) passed on both extension and website with 0 runtime errors.
- Verified byte-identical ZIP copies across all 4 locations.
