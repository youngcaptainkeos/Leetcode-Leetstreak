# LeetStreak Verification & Testing Guide

This document describes the testing architecture, synthetic fixtures, continuous integration checks, and local verification procedures for the LeetStreak codebase.

---

## 1. Principles & Safety Guarantees

1. **Strictly Synthetic Data**:
   - Tests never use real user accounts, production database connections, real email inboxes, or active external API mutations.
   - All email fixtures use the reserved domain `@example.com` (RFC 2606).
   - Upstream providers (LeetCode GraphQL and Codeforces API) are mocked with deterministic fixtures or mock servers.
2. **Deterministic & Isolated**:
   - Backend unit tests run with in-memory SQLite transactions or isolated per-test database schemas.
   - Migrations and advisory locks are tested concurrently against isolated test databases.
   - Client tests run in Node.js using isolated mock storage.
3. **Fail-Closed Security**:
   - Authentication, password validation, OTP limits, and admin endpoints fail closed whenever invalid, empty, or unconfigured credentials are provided.

---

## 2. Test Suites Overview

### A. Backend Unit & Integration Tests (`backend/tests/`)
Over 125 deterministic tests covering all core system components:

| Test Module | Coverage Scope |
|---|---|
| `test_access.py` | Role-based access control, friend leaderboards, and endpoint route authorization. |
| `test_auth.py` | Password complexity, PBKDF2 hashing, rate limits, and token issuance. |
| `test_admin.py` | Admin secret validation, idempotent release broadcasts, and administrative actions. |
| `test_preferences.py` | Global leaderboard visibility toggle and display preference persistence. |
| `test_timekeeping.py` | IST day boundaries, weekly/monthly period starts, and time zone normalization. |
| `test_scoring.py` | ZeroTrac contest ratings, acceptance rate adjustments, streak multipliers, and decimal score calculation. |
| `test_tracking.py` | Idempotent submission ingestion, repeat deduplication, and 7-day revision awards. |
| `test_tracking_sync.py` | Historical sync completeness labeling (`complete` vs `partial`). |
| `test_coordination.py` | Distributed leases, 409 Conflict handling, and multi-process provider rate limits. |
| `test_release_metadata.py` | SemVer v1.1.0 metadata, artifact checksums, retired XML 410 Gone, and client version comparison. |
| `test_migrations.py` | Atomic versioned migrations across core, platform, auth, display, tracking, and lease schemas. |
| `test_postgres_migrations.py` | Native PostgreSQL advisory lock concurrency and multi-threaded schema migrations. |
| `test_verification.py` | Platform handle challenge verification and profile ownership recovery. |
| `test_unlink.py` | Codeforces unlinking and ledger score reconciliation. |
| `test_friendships.py` | Safe user search, friend requests, and direct friendships without groups. |
| `test_progress_plans.py` | Study plan playlists, custom sheets, and starter restoration. |
| `test_email.py` | Honest email delivery reporting, SMTP error handling, and XSS sanitization. |
| `test_recovery.py` | Forgot password OTP verification, password changes, and session token revocation. |

### B. Client Test Suite (`extension/tests/`)
26 Node.js unit tests validating client-side business logic:
- `auth.test.mjs`: Session publishing, token persistence, and same-account refresh.
- `api.test.mjs`: Authenticated API requests, cache preference, and expired session detection.
- `ordering.test.mjs`: Solves deduplication across sources retaining the latest timestamp (UI-07).
- `isolation.test.mjs`: Partial platform failure isolation (UI-06).
- `concurrency.test.mjs`: Request sequence counters invalidating stale superseded responses (UI-05).
- `progress.test.mjs`: Study plan imports (LeetCode, Codeforces, Striver sheet), starter defaults, and offline recovery.
- `storage.test.mjs`: Versioned session contract migration (v2) and sensitive draft rejection.

### C. Browser Smoke Test (`backend/tests/browser_smoke.py`)
Playwright-driven headless Chrome test verifying real DOM rendering in both the extension popup and website:
- Full onboarding, registration, login, and dashboard navigation.
- Password change token revocation and expired session redirect.
- Asserts zero uncaught JavaScript errors in console.

### D. Hygiene & Release Validation Tools
- `scripts/check_hygiene.py`: Scans for exposed private keys, production credentials, unapproved test emails, and package cleanliness.
- `scripts/sync_release.py`: Validates version alignment and byte-identity across all 4 release ZIP copies.

---

## 3. Running Checks Locally

To execute the entire verification suite locally in one step:

```bash
./scripts/run_checks.sh
```

### Running Individual Test Suites:

```bash
# 1. Backend Unit Tests
PYTHONPATH=backend:backend/tests JWT_SECRET="test-secret-value-for-ci-and-testing-only-12345" python3 -m unittest discover -s backend/tests -p "test_*.py"

# 2. Native PostgreSQL Migration Tests (Requires local test PostgreSQL instance)
LEETSTREAK_TEST_POSTGRES_URL="postgresql+psycopg2://user:pass@127.0.0.1:5432/leetstreak_test" python3 -m unittest backend/tests/test_postgres_migrations.py

# 3. Client Unit Tests
node --test extension/tests/*.test.mjs

# 4. TypeScript & Web Build
npm --prefix web run check
npm --prefix web run build

# 5. Extension Packaging & Artifact Verification
python3 scripts/sync_release.py --package
python3 scripts/sync_release.py --verify

# 6. Hygiene Scan
python3 scripts/check_hygiene.py
```

---

## 4. Continuous Integration (CI)

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically on push and pull requests to `main` and `pre-launch`:
- Permissions are strictly pinned to `contents: read`.
- A dedicated PostgreSQL 16 service container runs native migration and advisory lock checks.
- All client tests, type checks, builds, and package verifications run concurrently.
- No network requests are made to live production services.
