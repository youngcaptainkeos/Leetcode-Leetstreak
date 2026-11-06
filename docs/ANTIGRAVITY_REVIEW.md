# Antigravity diff review

Original review boundary: `fd9b051..8e9a07c`. Follow-up repair commits are separate from this original diff.

**Status: incomplete.** The owner requested a review of every modified line. The earlier 25-minute repair limit remains in effect; unchecked files below are explicitly queued for the next review pass. Passing tests/builds do not establish line-by-line review coverage. No production release, public-history rewrite or installed-extension acceptance is claimed.

## Findings and follow-up

- Scoring/data findings and repairs: see `IMPLEMENTATION_PLAN.md`, REV-01 through REV-07. Repair `08e2158` preserves earned awards, protects legacy combined credit, rejects unverified dates, retains Codeforces repeat evidence, and reads stored breakdown components.
- Account identity guards were repaired and verified with the final 173-test backend suite: revalidate a confirmation after provider waits, reject a newly verified competing owner, discard stale LeetCode provider results and invalidate account generations on Codeforces replacement. These are targeted safeguards, not proof of the complete claim/recovery lifecycle.
- The extension bridge treats page events as unprivileged hints and keeps credentials in extension storage. Its DOM fallback can retrigger sync while an Accepted result remains visible and the page continues mutating; investigate edge-triggering and native browser behavior later.
- CI omitted the extension TypeScript check; the repair adds it. CI still omits the browser smoke test, which passed locally in this repair pass; adding it to CI remains a follow-up.
- Generated output and binary packages require reproducibility, reference checks and artifact inspection. Reading minified bundles is not a substitute for reviewing their source.

### Additional findings from the expanded review

- **REV-08 — release source metadata (deferred):** `release_metadata.py` falls back to a hardcoded old revision (`2fd7c77`) if its configured environment keys and a Git checkout are unavailable. Docker excludes `.git`; review the deployment commit-variable binding and report unknown rather than advertise an unrelated old revision. Also revalidate the minimum supported client version against the authentication compatibility break.
- **REV-09 — scoring dataset consistency (deferred):** the global refresh lease only updates the winning worker's in-memory `CONTEST_RATINGS` and local file. A simultaneous loser returns its own old memory without reloading a shared version. Workers/instances can consequently score with different dataset snapshots. Add a shared/versioned dataset publication and worker reload policy with multiprocess tests.
- **REV-06 detail:** `user_sync_lease` does not renew while its body runs; `renew_lease` is a read-then-update without a fencing condition. Long jobs and expired-owner writes require a dedicated concurrency repair and real process tests.

## Every changed file

Statuses: **diff read** means the complete original diff for that file was read, not that all runtime acceptance checks passed; **targeted** means only relevant sections were inspected; **tests executed** means the test file ran but its assertions still need a full semantic review; **generated** means build/package checks ran and source review remains relevant; **pending** means no complete line review is claimed.

| File | Added | Deleted | Review coverage |
|---|---:|---:|---|
| `.dockerignore` | 3 | 0 | Diff read; runtime limitations noted above |
| `.github/workflows/ci.yml` | 124 | 0 | Diff read; runtime limitations noted above |
| `.gitignore` | 4 | 0 | Diff read; runtime limitations noted above |
| `CHANGES.md` | 906 | 0 | Pending |
| `PRIVACY.md` | 5 | 4 | Pending |
| `README.md` | 38 | 17 | Pending |
| `SECURITY.md` | 1 | 1 | Pending |
| `backend/app/challenge_archive.py` | 121 | 0 | Pending |
| `backend/app/codeforces_client.py` | 33 | 19 | Targeted; remaining lines pending |
| `backend/app/codeforces_sync.py` | 119 | 64 | Targeted; remaining lines pending |
| `backend/app/contest_ratings.py` | 10 | 0 | Diff read; follow-ups below remain open |
| `backend/app/leases.py` | 284 | 0 | Diff read; follow-ups below remain open |
| `backend/app/leetcode_client.py` | 10 | 0 | Diff read; follow-ups below remain open |
| `backend/app/leetstreak.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `backend/app/legal_pages.py` | 6 | 5 | Pending |
| `backend/app/main.py` | 1450 | 122 | Targeted; remaining lines pending |
| `backend/app/migrations.py` | 231 | 14 | Pending |
| `backend/app/models.py` | 97 | 0 | Targeted; remaining lines pending |
| `backend/app/platform_migration.py` | 2 | 17 | Pending |
| `backend/app/point_calculator.py` | 283 | 128 | Targeted; remaining lines pending |
| `backend/app/release_metadata.py` | 105 | 0 | Diff read; follow-ups below remain open |
| `backend/app/releases.py` | 14 | 0 | Diff read; follow-ups below remain open |
| `backend/app/scheduler.py` | 156 | 97 | Targeted; remaining lines pending |
| `backend/app/schemas.py` | 234 | 0 | Targeted; remaining lines pending |
| `backend/tests/test_auth.py` | 24 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_challenge_archive.py` | 95 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_coordination.py` | 163 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_friendships.py` | 235 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_history_and_exports.py` | 386 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_migrations.py` | 159 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_period_rankings.py` | 292 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_point_reconciliation.py` | 121 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_postgres_migrations.py` | 25 | 1 | Tests executed; complete line review pending |
| `backend/tests/test_progress_plans.py` | 182 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_release_metadata.py` | 155 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_score_reconciliation.py` | 142 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_tracking_sync.py` | 246 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_unlink.py` | 130 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_verification.py` | 219 | 0 | Tests executed; complete line review pending |
| `docs/ENVIRONMENT_SETUP.md` | 112 | 0 | Pending |
| `docs/IMPLEMENTATION_PLAN.md` | 372 | 350 | Targeted; remaining lines pending |
| `docs/KEY_MANAGEMENT.md` | 65 | 0 | Pending |
| `docs/MANUAL_VERIFICATION_CHECKLIST.md` | 39 | 0 | Targeted; remaining lines pending |
| `docs/RELEASE_PROCEDURE.md` | 114 | 0 | Pending |
| `docs/TESTING.md` | 110 | 0 | Pending |
| `extension/dist/assets/index-Bxqks-9B.css` | 0 | 1614 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/assets/index-D4eizpAd.css` | 0 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/assets/index-D4eizpAd.js` | 0 | 54 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/assets/index-main.css` | 0 | 1583 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/assets/index-main.js` | 0 | 26089 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/background.js` | 77 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/index-main.css` | 1 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/index-main.js` | 14 | 14 | Generated; rebuilt/package checks; source review pending |
| `extension/dist/manifest.json` | 21 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/index-main.css` | 1 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/index-main.js` | 14 | 14 | Generated; rebuilt/package checks; source review pending |
| `extension/leetstreak.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `extension/manifest.json` | 21 | 1 | Pending |
| `extension/package.json` | 3 | 2 | Diff read; runtime limitations noted above |
| `extension/public/background.js` | 77 | 1 | Diff read; runtime limitations noted above |
| `extension/public/index-main.css` | 1 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/public/index-main.js` | 14 | 14 | Generated; rebuilt/package checks; source review pending |
| `extension/public/leetcode-listener.js` | 43 | 34 | Diff read; runtime limitations noted above |
| `extension/public/leetcode-page-bridge.js` | 61 | 0 | Diff read; runtime limitations noted above |
| `extension/public/manifest.json` | 21 | 1 | Pending |
| `extension/src/App.css` | 284 | 0 | Pending |
| `extension/src/App.tsx` | 929 | 74 | Targeted; remaining lines pending |
| `extension/src/lib/api.ts` | 260 | 4 | Targeted; remaining lines pending |
| `extension/src/progress/Progress.tsx` | 163 | 22 | Pending |
| `extension/src/storage.ts` | 93 | 0 | Diff read; runtime limitations noted above |
| `extension/tests/ordering.test.mjs` | 100 | 0 | Tests executed; complete line review pending |
| `extension/tests/storage.test.mjs` | 127 | 0 | Tests executed; complete line review pending |
| `leetstreak.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `leetstreak_dist.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `render.yaml` | 6 | 0 | Diff read; runtime limitations noted above |
| `scripts/backfill_challenges.py` | 68 | 0 | Pending |
| `scripts/check_hygiene.py` | 148 | 0 | Pending |
| `scripts/reconcile_points.py` | 73 | 0 | Pending |
| `scripts/run_checks.sh` | 60 | 0 | Pending |
| `scripts/sync_release.py` | 201 | 0 | Pending |
| `web/app/App.css` | 726 | 0 | Pending |
| `web/app/App.tsx` | 834 | 45 | Targeted; remaining lines pending |
| `web/app/Progress.tsx` | 583 | 0 | Pending |
| `web/app/data/strivers-a2z.json` | 4180 | 0 | Pending |
| `web/app/data/study-plans.json` | 1655 | 0 | Pending |
| `web/app/lib/api.ts` | 261 | 4 | Targeted; remaining lines pending |
| `web/app/progressData.ts` | 256 | 0 | Pending |
| `web/main.tsx` | 1 | 0 | Pending |
| `web/package.json` | 1 | 1 | Pending |

## Next review order

1. Finish every modified route and helper in `backend/app/main.py`, then account ownership, migrations, leases and provider syncing. Review both additions and removed safeguards.
2. Review all changed client state, progress sync/outbox, ordering, settings and data-export flows against their backend contracts.
3. Review every new/changed test assertion for missing cases and mistaken expected behavior; green tests may encode the bug.
4. Review plan/data imports, operational scripts, CI, documentation and attribution.
5. Reproduce both builds in a clean checkout, inspect all generated assets/packages, complete installed-extension checks and the separate release/privacy gates.

Do not mark this document complete until each file has a final disposition and unresolved findings have tracking IDs.

Verification checkpoint: 173 backend tests including PostgreSQL passed; six new identity race-guard tests passed. Both type checks, 26 client tests, builds, browser session smoke tests, hygiene checks and package consistency passed during the bounded repair. Eleven manifest/HTML runtime references resolved inside the reviewed ZIP. These checks do not close pending line-review coverage.
