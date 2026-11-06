# Antigravity diff review

**Archived evidence:** this report describes `fd9b051..8e9a07c` and follow-up repairs through `69c6a6c`. On 2026-11-06 the owner approved restarting from `fd9b051` on `pre-launch-rebuild`. Findings, line references and test results below refer to the preserved old branch; they are regression requirements for the rebuild, not claims about the current checkout.

Original review boundary: `fd9b051..8e9a07c`. Follow-up repair commits are separate from this original diff.

**Status: incomplete.** The owner requested a review of every modified line. The owner extended the read-only review through 07:10 IST on 2026-11-06. Unchecked files below remain queued rather than being marked reviewed because tests pass. Passing tests/builds do not establish line-by-line review coverage. No production release, public-history rewrite or installed-extension acceptance is claimed.

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

## Expanded review findings — 2026-11-06, through 07:10 IST

This pass changes review documents only. Reproductions use temporary synthetic databases and mocked providers; no production accounts, emails or databases were touched. **Confirmed** below means the isolated reproduction demonstrated the bug; **static** means a concrete code path was inspected without claiming a browser or concurrent-process reproduction.

| ID | Priority / evidence | Finding and required repair |
|---|---|---|
| REV-10 | P1 / confirmed | **Account deletion fails with direct friendships.** `backend/app/main.py:759` deletes the User, while `models.py:272` creates non-null friendship FKs with ORM backrefs that default to nullifying related rows. Synthetic deletion after removing the owned group raises `IntegrityError` on the friendship FK. Explicitly delete incoming/outgoing relationships or configure tested passive DB cascades; cover self-service and admin deletion. |
| REV-11 | P1 / confirmed | **Ownership claim mixes coding accounts.** In `main.py` confirmation, the previous owner is cleared but the claimant's existing platform history/generation/sync boundaries are not replaced. A synthetic CF claim returned 200, changed to the new handle and retained one solve with the old CF source handle. Reconcile the receiving and displaced accounts atomically while preserving the other platform. Retain the newly added token/owner guards; they do not fix this lifecycle bug. |
| REV-12 | P1 / confirmed + static clients | **Progress versioning/outbox is incomplete.** `ProgressUpdateRequest.base_version` is accepted but ignored by `main.py:797`; two writes with the same base version both returned 200 and the second erased the first. Clients swallow failed writes without a durable operation queue. Extension boot reuploads locally cached custom plans absent on the server and unions manual completions, resurrecting deleted plans/unchecked items. Add conditional version updates, tombstones and an acknowledged retry queue; test two devices and offline edits. |
| REV-13 | P1 / static | **Website completion uses only 50 recent solves.** `web/app/Progress.tsx:72` populates observed LeetCode slugs from `recentSolves(userId,50)`. Complete extension-synced solved slugs are absent from the backend progress contract. A different browser/device therefore cannot show full historical plan progress. Persist/provider-validate canonical completion sets and have both clients consume them with completeness metadata. |
| REV-14 | P1 / static | **Leaderboard ordering protection is incomplete.** Both App files have separate `fullLoadReqRef` and `leaderboardReqRef`; a late full refresh can overwrite the board selected by the newer tab/sort/period request. `handleKudosAll` still uses legacy tab-only cache keys, calls rankings without period (defaults all-time), and writes results unconditionally. Use one view generation/key for every board writer and retain the selected period. The copied-algorithm ordering unit tests do not exercise these production paths. |
| REV-15 | P2 / confirmed | **History date filters use UTC midnight instead of IST.** `main.py:2200` builds naive `datetime.combine` bounds. A solve at 2026-01-01 19:00 UTC (January 2, 00:30 IST) is missing from a January 2-only search. Convert IST start/end boundaries to UTC storage bounds and test both edges. |
| REV-16 | P1 / confirmed scanner gap | **Hygiene validation cannot support its claims.** `scripts/check_hygiene.py` misses a fictional credential-bearing Supabase pooler URL in the same hostname/port format involved in the original exposure. It has no test-identity/email detector, skips hidden directories, checks ZIP entry names without scanning decoded contents, and checks ignore-file substrings rather than tracked Git files/history. Implement a tracked-file and archive-content audit with reviewed allowlists; retain independent private history remediation. This finding does not assert that a new live credential was found. |
| REV-17 | P2 / static | **Incomplete dates are labeled zero activity and exported as definite solve dates.** Heatmap observation starts at registration/oldest observed solve; missing days thereafter become `zero` even when history is partial. Search/CSV/JSON omit first-solve proof and component-state flags, so observed timestamps can look like confirmed first solves. Add explicit coverage intervals and provenance fields throughout the UI/export. |
| REV-18 | P2 / static | **FEAT-08 UI is unfinished.** Neither App calls `api.searchSolves` or `api.activityHeatmap`; the new search box filters the existing last-10 profile list, and no longer heatmap is rendered. Backend endpoints alone do not satisfy full-history search/activity views. Implement pagination/filters and uncertainty-aware heatmap rendering in both clients. |
| REV-19 | P2 / confirmed + static | **Import validation differs from save validation.** A 1,001-question plan was accepted by `/plans/import`, while normal save rejects it. Import list lengths, manual/followed item limits and question URL/slug/kind validation are incomplete; duplicate plan slugs can also cause uniqueness failures. Centralize constraints in schemas and apply limits after merging. `sourceUrl` is propagated into direct anchor URLs without the question-link HTTPS guard; reject unsupported schemes. No browser exploit is claimed. |
| REV-20 | P2 / static | **Friend requests lack unordered-pair uniqueness and abuse bounds.** The model uniquely constrains directional `(user_id,friend_id)` only, while the route checks both directions before inserting. Truly concurrent crossed requests can create two pending relationships. There is no persisted request quota or list pagination; ambiguous exact display names use `.first()`. Add a canonical pair key/transactional transitions, stable IDs and bounded discovery/request behavior. |
| REV-21 | P2 / static | **Maintenance modes can mutate unexpectedly and misreport work.** Both CLI `--status`/`--dry-run` paths run schema migrations before their read mode. Batch size is unbounded/unvalidated: zero can mark reconciliation complete without processing accounts; negative can remove the intended bound. Checkpoints lack exclusive job ownership and failure-state updates. Archive defaults use host `date.today()` rather than IST. Validate inputs, use explicit targets, keep read modes read-only and test interruption/concurrency. |
| REV-22 | P2 / static docs | **Public documentation contradicts implementation.** README states LC bases 10/20/30, CF rating/100 and a 10-day multiplier ramp; the engine uses 8/15/24, 8+0.012*(rating-800), and 30-day ramp. Environment docs claim an automatically generated admin secret, while admin actions actually fail closed without one. Testing docs list nonexistent client test files and overstate multi-process/browser coverage. Correct docs and release claims from verified behavior. |
| REV-23 | P1 / confirmed, repair regression | **Missing metadata can double-count historical credit.** This is in repair `08e2158`, not solely the original Antigravity code: a synthetic user with one Easy total and one undated unclassified solve already credited 10 receives total 18 because the unknown solve keeps its credit and the difficulty estimate adds another 8. Avoid overlapping identity-less aggregate credit and preserved per-question credit; cover missing metadata and later enrichment before running reconciliation. |
| REV-24 | P1 / confirmed | **Actual Striver starter removal is not persisted.** Bundled slug is `strivers-a2z-dsa-sheet`, but backend `STARTER_PLANS` uses `strivers-a2z`. Deleting the real slug returned success but backend hidden plans stayed empty; reopening can restore it. Derive starter IDs from one canonical catalog and update tests to use shipped IDs. |
| REV-25 | P2 / static | **Website import silently substitutes the wrong Striver plan.** `fetchBundledOrCatalogPlan` returns A2Z for any input containing `takeuforward.org`, including another Striver sheet. The placeholder alias `strivers-a2z` also differs from the actual bundled slug. Resolve known URLs exactly; show an explicit unsupported-source fallback rather than change the requested plan. |
| REV-26 | P2 / static | **Friend activity failure/recency gaps remain.** Website friends activity suppresses lookup failures as empty arrays and only fetches the first ten friends. Extension's final refresh replacement drops prior valid items on partial failures. CF recent-solves reads question first-solve timestamps rather than latest accepted-event timestamps, hiding rewarded repeats. Preserve partial results, expose failures and source activity from accepted events. |
| REV-27 | P2 / static migration | **Legacy registration dates can still be invented.** `migrate_core` adds a missing `created_at` column with `DEFAULT CURRENT_TIMESTAMP`, assigning migration time to legacy accounts. Preserve unknown registration dates explicitly; do not let them establish heatmap observation coverage. |

### Isolated reproduction results

- Friendship-linked account deletion: `IntegrityError`; non-null friendship FK failure confirmed.
- Two progress writes using the same base version: `200`, `200`; only the second followed-plan list remained.
- January 2 IST search for the 00:30 IST solve: zero results.
- CF claim with existing old-account solves: `200`; new handle linked while old source-handle solve remained.
- Fictional pooler credential URL: scanner did not detect it.
- Preserved 10-point unclassified solve plus one Easy aggregate: recalculation produced 18 points.
- Delete the actual bundled Striver slug: hidden flag absent afterward.
- Import 1,001 questions: `200` despite the direct-save 1,000 limit.

### Dataset inspection

Both added website JSON datasets are byte-identical to their pre-existing extension counterparts. Parsed every record: Striver A2Z contains 495 unique question IDs; study-plan catalog has 3 plans / 275 questions, no duplicate IDs within a plan and no non-HTTPS explicit question URLs. This is structured validation of all records, not verification of every external problem mapping, copyright/attribution or provider snapshot freshness.

## Every changed file

Statuses: **diff read** means the complete original diff for that file was read, not that all runtime acceptance checks passed; **targeted** means only relevant sections were inspected; **tests executed** means the test file ran but its assertions still need a full semantic review; **generated** means build/package checks ran and source review remains relevant; **pending** means no complete line review is claimed.

| File | Added | Deleted | Review coverage |
|---|---:|---:|---|
| `.dockerignore` | 3 | 0 | Diff read; runtime limitations noted above |
| `.github/workflows/ci.yml` | 124 | 0 | Diff read; runtime limitations noted above |
| `.gitignore` | 4 | 0 | Diff read; runtime limitations noted above |
| `CHANGES.md` | 906 | 0 | Pending |
| `PRIVACY.md` | 5 | 4 | Source/diff read; findings/acceptance limits recorded |
| `README.md` | 38 | 17 | Pending |
| `SECURITY.md` | 1 | 1 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/challenge_archive.py` | 121 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/codeforces_client.py` | 33 | 19 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/codeforces_sync.py` | 119 | 64 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/contest_ratings.py` | 10 | 0 | Diff read; follow-ups below remain open |
| `backend/app/leases.py` | 284 | 0 | Diff read; follow-ups below remain open |
| `backend/app/leetcode_client.py` | 10 | 0 | Diff read; follow-ups below remain open |
| `backend/app/leetstreak.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `backend/app/legal_pages.py` | 6 | 5 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/main.py` | 1450 | 122 | Targeted; remaining lines pending |
| `backend/app/migrations.py` | 231 | 14 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/models.py` | 97 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/platform_migration.py` | 2 | 17 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/point_calculator.py` | 283 | 128 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/release_metadata.py` | 105 | 0 | Diff read; follow-ups below remain open |
| `backend/app/releases.py` | 14 | 0 | Diff read; follow-ups below remain open |
| `backend/app/scheduler.py` | 156 | 97 | Source/diff read; findings/acceptance limits recorded |
| `backend/app/schemas.py` | 234 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/tests/test_auth.py` | 24 | 0 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_challenge_archive.py` | 95 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/tests/test_coordination.py` | 163 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/tests/test_friendships.py` | 235 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/tests/test_history_and_exports.py` | 386 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_migrations.py` | 159 | 0 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_period_rankings.py` | 292 | 0 | Tests executed; complete line review pending |
| `backend/tests/test_point_reconciliation.py` | 121 | 0 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_postgres_migrations.py` | 25 | 1 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_progress_plans.py` | 182 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/tests/test_release_metadata.py` | 155 | 0 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_score_reconciliation.py` | 142 | 0 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_tracking_sync.py` | 246 | 0 | Diff/assertions read; coverage gaps remain as recorded |
| `backend/tests/test_unlink.py` | 130 | 0 | Source/diff read; findings/acceptance limits recorded |
| `backend/tests/test_verification.py` | 219 | 0 | Source/diff read; findings/acceptance limits recorded |
| `docs/ENVIRONMENT_SETUP.md` | 112 | 0 | Source/diff read; findings/acceptance limits recorded |
| `docs/IMPLEMENTATION_PLAN.md` | 372 | 350 | Targeted; remaining lines pending |
| `docs/KEY_MANAGEMENT.md` | 65 | 0 | Source/diff read; findings/acceptance limits recorded |
| `docs/MANUAL_VERIFICATION_CHECKLIST.md` | 39 | 0 | Targeted; remaining lines pending |
| `docs/RELEASE_PROCEDURE.md` | 114 | 0 | Source/diff read; findings/acceptance limits recorded |
| `docs/TESTING.md` | 110 | 0 | Source/diff read; findings/acceptance limits recorded |
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
| `extension/manifest.json` | 21 | 1 | Source/diff read; findings/acceptance limits recorded |
| `extension/package.json` | 3 | 2 | Diff read; runtime limitations noted above |
| `extension/public/background.js` | 77 | 1 | Diff read; runtime limitations noted above |
| `extension/public/index-main.css` | 1 | 1 | Generated; rebuilt/package checks; source review pending |
| `extension/public/index-main.js` | 14 | 14 | Generated; rebuilt/package checks; source review pending |
| `extension/public/leetcode-listener.js` | 43 | 34 | Diff read; runtime limitations noted above |
| `extension/public/leetcode-page-bridge.js` | 61 | 0 | Diff read; runtime limitations noted above |
| `extension/public/manifest.json` | 21 | 1 | Source/diff read; findings/acceptance limits recorded |
| `extension/src/App.css` | 284 | 0 | Source/diff read; findings/acceptance limits recorded |
| `extension/src/App.tsx` | 929 | 74 | Targeted; remaining lines pending |
| `extension/src/lib/api.ts` | 260 | 4 | Targeted; remaining lines pending |
| `extension/src/progress/Progress.tsx` | 163 | 22 | Source/diff read; findings/acceptance limits recorded |
| `extension/src/storage.ts` | 93 | 0 | Diff read; runtime limitations noted above |
| `extension/tests/ordering.test.mjs` | 100 | 0 | Source/diff read; findings/acceptance limits recorded |
| `extension/tests/storage.test.mjs` | 127 | 0 | Source/diff read; findings/acceptance limits recorded |
| `leetstreak.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `leetstreak_dist.zip` | - | - | Generated; rebuilt/package checks; source review pending |
| `render.yaml` | 6 | 0 | Diff read; runtime limitations noted above |
| `scripts/backfill_challenges.py` | 68 | 0 | Source/diff read; findings/acceptance limits recorded |
| `scripts/check_hygiene.py` | 148 | 0 | Source/diff read; findings/acceptance limits recorded |
| `scripts/reconcile_points.py` | 73 | 0 | Source/diff read; findings/acceptance limits recorded |
| `scripts/run_checks.sh` | 60 | 0 | Source/diff read; findings/acceptance limits recorded |
| `scripts/sync_release.py` | 201 | 0 | Source/diff read; findings/acceptance limits recorded |
| `web/app/App.css` | 726 | 0 | Pending |
| `web/app/App.tsx` | 834 | 45 | Targeted; remaining lines pending |
| `web/app/Progress.tsx` | 583 | 0 | Source/diff read; findings/acceptance limits recorded |
| `web/app/data/strivers-a2z.json` | 4180 | 0 | All records structurally checked; identical to extension data; external mapping review pending |
| `web/app/data/study-plans.json` | 1655 | 0 | All records structurally checked; identical to extension data; external mapping review pending |
| `web/app/lib/api.ts` | 261 | 4 | Targeted; remaining lines pending |
| `web/app/progressData.ts` | 256 | 0 | Source/diff read; findings/acceptance limits recorded |
| `web/main.tsx` | 1 | 0 | Source/diff read; findings/acceptance limits recorded |
| `web/package.json` | 1 | 1 | Source/diff read; findings/acceptance limits recorded |

## Next review order

1. Finish every modified route and helper in `backend/app/main.py`, then account ownership, migrations, leases and provider syncing. Review both additions and removed safeguards.
2. Review all changed client state, progress sync/outbox, ordering, settings and data-export flows against their backend contracts.
3. Review every new/changed test assertion for missing cases and mistaken expected behavior; green tests may encode the bug.
4. Review plan/data imports, operational scripts, CI, documentation and attribution.
5. Reproduce both builds in a clean checkout, inspect all generated assets/packages, complete installed-extension checks and the separate release/privacy gates.

Do not mark this document complete until each file has a final disposition and unresolved findings have tracking IDs.

Verification checkpoint: 173 backend tests including PostgreSQL passed; six new identity race-guard tests passed. Both type checks, 26 client tests, builds, browser session smoke tests, hygiene checks and package consistency passed during the bounded repair. Eleven manifest/HTML runtime references resolved inside the reviewed ZIP. These checks do not close pending line-review coverage.

### Extended review checkpoint

Original inventory: 89 files. Coverage categories: source/diff read: 58, targeted or pending: 12, generated checks: 17, structured data: 2. These categories distinguish inspection from correctness; open findings still block release. Remaining targeted/pending files retain their explicit statuses. No application source, packages or production state changed during this review pass.
