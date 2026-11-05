# LeetStreak implementation and public-release plan

Created: 2026-11-05  
Baseline: `progress-bar`, commit `693a20c`  
Scope: backend, extension, website, data correctness, operations, and public repository readiness.

Pre-scheduling decisions: [DECISIONS.md](DECISIONS.md) records accepted requirements, pending recommendations across M1–M6, and feasibility investigations. The owner's latest accepted rules below supersede earlier recommendations. Unanswered choices remain pending.

## 1. How we will use this document

This is the working checklist for the repository review. It covers every issue and proposed feature in that review, plus the requested cleanup for publishing clean public code. It describes future work; creating this document does not fix or verify the application.

- Check an item's master checkbox only after its implementation and acceptance criteria are satisfied.
- Mark intermediate progress in the item's task checkboxes. Use the completion log for commits, verification evidence, and release status.
- If implementation is finished but release or required verification is pending, leave the master checkbox open and record that distinction.
- Record a deliberately deferred item with its reason; do not mark it fixed.
- Keep personal details, real test addresses, account exports, credentials, and raw production logs out of this document and its completion evidence.
- Evidence should identify the check and outcome without including private payloads.

**Current state: 0 of 45 items completed; 3 notification items explicitly deferred.** DATA-09 tracks revision scoring and FEAT-10 tracks direct friendships without shared groups. Only checks explicitly recorded as passed have been performed locally; unchecked criteria and production release checks remain pending. This is a source-based plan, not proof of current production behavior or hosting configuration.

### Execution authorization and branch sequence — owner instruction

- The owner has authorized implementation on `pre-launch` with a clearly labeled commit/push and progress notification after every successful step. The integration merge/deployment to `main` completed at `269e06f`; production releases of milestone fixes remain separate checkpoints.
- The existing Codeforces/plan integration was merged and checked separately; it is not counted as completing any pre-launch checklist item.
- Branch `pre-launch` was created from updated `origin/main` (`269e06f`) for milestone work. Do not merge fixes into production without the agreed release checkpoint.
- On `pre-launch`, make a separate clearly labeled commit after each completed implementation step, not just one commit per milestone. Include milestone/task/step identifiers, for example `M2 DATA-09 step 1: add revision award ledger`. Notify the owner after each successful step through the agreed private notification destination; never record that destination or credentials in this public repository.
- Push each completed step's commit to `origin/pre-launch` and record the revision, checks, and status here. Follow dependencies when a step spans multiple tasks; do not label unfinished/unverified work as fixed.
- A push to `pre-launch` is not a production release. Production merges/deployments remain explicit release checkpoints.
- Chrome Web Store upload is deferred until all planned fixes and release checks are complete, as requested on 2026-11-05. Prepare the final reviewed ZIP, listing assets and privacy/permission disclosures at that checkpoint; do not upload the current development build.

### Priorities

| Priority | Meaning |
|---|---|
| P0 | Protect accounts and administrative actions before a broader release. |
| P1 | Fix incorrect results, privacy leaks, broken core behavior, and public-release blockers. |
| P2 | Improve reliability, maintainability, and essential product completeness. |
| P3 | Add useful capabilities after the foundations are reliable. |

### Working boundaries

1. Keep website and extension independently buildable. Website-only tasks must not change extension bundles or ZIPs. Cross-client tasks must explicitly list both clients.
2. Follow the branch sequence above: finish integration, merge to `main`, then create `pre-launch` for these fixes when instructed. Do not perform those actions during planning or rewrite shared history merely because a checklist item exists.
3. Use additive, versioned migrations where possible. Snapshot affected data privately before destructive reconciliation, then make changes reversible.
4. Preserve the existing dark charcoal/purple theme, Inter controls, Outfit headings, and 380px extension width.
5. Never use real users or production accounts as test fixtures. Never run scratch mutation scripts against production.
6. Keep actual secrets in environment settings. Public examples must contain clearly fictional values only.
7. Run acceptance checks in an isolated environment when that implementation task is undertaken and testing is authorized. Production checks must not send test messages or mutate user data.
8. For extension changes, build and synchronize the required distribution archives. For website changes, use its separate build. A branch push is not proof of a production deployment.

## 2. Master checklist

### Security and privacy

- [ ] **SEC-01 · P0:** Authenticate account actions and enforce permissions.
- [ ] **SEC-02 · P0:** Protect every administrative endpoint; remove the default admin secret.
- [ ] **SEC-03 · P1:** Harden password recovery, passwords, and session revocation.
- [ ] **SEC-04 · P1:** Separate Global leaderboard display preferences from participation; enforce profile and private-group access rules.
- [ ] **SEC-05 · P1:** Remove fabricated-profile behavior from production.

### Scoring and data correctness

- [x] **DATA-01 · P1:** Reconcile history when a LeetCode handle changes.
- [x] **DATA-02 · P1:** Keep one unique question entry and deduplicate all repeated submissions.
- [x] **DATA-03 · P1:** Separate submission activity from verified accepted solves.
- [x] **DATA-04 · P1:** Represent and reconcile incomplete LeetCode history.
- [x] **DATA-05 · P1:** Revalue historical base points fairly for all users while retaining earned daily bonuses.
- [x] **DATA-06 · P1:** Use IST for all product day/week/month/challenge boundaries; retain UTC timestamp storage.
- [x] **DATA-07 · P1:** Use one calculation for stored points and score breakdowns.
- [x] **DATA-08 · P2:** Retain earned daily awards separately and prevent retrospective daily bonuses on imported history.
- [x] **DATA-09 · P2:** Award 2 revision points for an accepted repeat after at least one week, without extending the streak or adding another question entry.

### Extension and website behavior

- [x] **UI-01 · P1:** Unify background/content-script account storage.
- [x] **UI-02 · P1:** Repair immediate accepted-submission detection.
- [ ] **UI-03 · P1 · Deferred:** Repair the friend notification page under Manifest V3 when the owner resumes that feature.
- [ ] **UI-04 · P2 · Deferred:** Correct friend notification selection, deduplication, and platform labels later.
- [x] **UI-05 · P1:** Prevent stale leaderboard responses and incorrect sorted caches.
- [x] **UI-06 · P2:** Distinguish friend lookup failures from empty activity.
- [x] **UI-07 · P2:** Keep the newest friend submission when merging activity sources.

### Reliability and maintenance

- [ ] **OPS-01 · P1:** Report email delivery failures honestly.
- [ ] **OPS-02 · P1:** Configure stable signing keys and predictable session behavior.
- [ ] **OPS-03 · P2:** Remove full archive imports and all-user recalculation from startup.
- [ ] **OPS-04 · P2:** Coordinate sync jobs and provider limits across processes.
- [ ] **OPS-05 · P1:** Make release versions and update metadata accurate.
- [ ] **OPS-06 · P1:** Add regression coverage and continuous checks.
- [ ] **OPS-07 · P2:** Remove tracked environments and simplify generated output management.

### Product features

- [x] **FEAT-01 · P2:** Save plans, external completion, and preferences to the account.
- [ ] **FEAT-02 · P2:** Add Progress to the website.
- [x] **FEAT-03 · P1:** Show reliable sync status and history completeness.
- [ ] **FEAT-04 · P2:** Add coding-account ownership verification and claim recovery.
- [ ] **FEAT-05 · P2:** Allow Codeforces unlinking.
- [ ] **FEAT-06 · P3:** Add weekly/monthly points rankings.
- [ ] **FEAT-07 · P2 · Deferred:** Add friend notification preferences and quiet hours when that feature is resumed.
- [ ] **FEAT-08 · P3:** Add searchable history, longer activity views, and exports.
- [x] **FEAT-09 · P2:** Explain the browser-session requirement for complete LeetCode plan sync.
- [ ] **FEAT-10 · P2:** Add direct friendships independently of group membership.

### Public repository readiness

- [ ] **PUB-01 · P1:** Remove real test identities and personal development details.
- [ ] **PUB-02 · P1:** Remove or curate scratch scripts and abandoned experiments.
- [ ] **PUB-03 · P1:** Audit configuration, secrets, logs, and screenshots.
- [ ] **PUB-04 · P1:** Assess and remediate historical exposure in Git and published assets.
- [ ] **PUB-05 · P1:** Publish clean extension packages and release artifacts.
- [ ] **PUB-06 · P2:** Rewrite public documentation around supported workflows.
- [ ] **PUB-07 · P1:** Complete a clean-clone and public-release review.

## 3. Implementation sequence and dependencies

| Milestone | Work | Exit condition |
|---|---|---|
| M1: Access and exposure | SEC-01–05, OPS-01–02, PUB-01–04; establish OPS-06 checks alongside fixes | Account boundaries enforced; administrative access fails closed; public exposure assessed. |
| M2: Accurate tracking | DATA-01–09, FEAT-03 | First-solve streaks, unique counts, revision awards, IST boundaries, base revaluation, and protected daily awards behave consistently. |
| M3: Reliable extension | UI-01–02, UI-05–07, FEAT-09 | Live sync, request ordering, inline daily reminders, and error states behave consistently. Friend notifications remain deferred. |
| M4: Account-backed progress and friendships | FEAT-01–02, FEAT-04–05, FEAT-10 | Plans follow the account; direct friendships work without groups; website parity and coding-account management are usable. |
| M5: Operations and release | OPS-03–07, PUB-05–07 | Repeatable release, migration, packaging, and recovery procedures exist. |
| M6: Product expansion | FEAT-06, FEAT-08 | Period rankings and history tools use verified, correctly scoped data. |

Public cleanup can proceed alongside security work after the execution hold is lifted. A public release must pass all applicable non-deferred P0/P1 gates; optional P3 features need not delay it. UI-03, UI-04, and FEAT-07 are backlog items, not current milestone blockers. Deferring alerts does not exempt packaged code from security/privacy cleanup; inert obsolete assets can be removed without rebuilding the feature. Put baseline regression checks and the versioned migration foundation in place during the early fixes, not only at M5. Milestones describe outcomes rather than fixed time estimates. Dependencies on a policy decision require that decision to be recorded, not that the entire related feature be finished.

### Accepted M1 product decisions

Confirmed by the owner on 2026-11-05. These decisions update the intended behavior; no application implementation is complete yet.

| Decision | Accepted behavior | Affected items |
|---|---|---|
| Global leaderboard participation | Every registered user participates in Global rankings regardless of the signup/settings toggle. Turning it off never hides the user from other people's rankings or removes their score. | SEC-04 |
| Global leaderboard display | The toggle controls whether the Global leaderboard appears on that user's homepage/dashboard. Label it “Show Global leaderboard”; explain that everyone still participates. Apply the same meaning in the extension and website. | SEC-04, FEAT-01 |
| Viewing profiles | A user who can access a clickable profile can view its coding stats, streak, points, activity, and recent solves. The target user's Global display preference must not block this. Private account settings, emails, credentials, and reset data are not profile content. | SEC-01, SEC-04 |
| Group permissions | Members may leave; owners may remove members and delete their group. An owner leaving must transfer ownership or delete the group. Private-group membership, codes, and group views require the appropriate membership/owner permission. | SEC-01, SEC-04 |
| Password reset | A successful reset invalidates existing sessions. Existing passwords continue working until changed; stronger rules apply to newly created/reset passwords. | SEC-03, OPS-02 |
| Test emails and announcements | Keep synthetic email tests local. Remove the production test-email endpoint; retain authenticated, protected release announcements. | SEC-02, OPS-01, PUB-01–03 |
| Old experiments and history | Clean current files, privately assess historical exposure, then review a concrete history-remediation strategy before rewriting shared history. | PUB-01–04 |

The earlier proposal to treat the signup toggle as a privacy opt-out is superseded. A user with this toggle off is not a hidden or “friends-only” account. Activity-feed inclusion also must not be filtered by this display preference. Notification scope remains governed by friend membership and notification preferences.

### Accepted scoring and workflow rules — owner evaluation

| Area | Accepted requirement |
|---|---|
| Streak | Only the first accepted solve of a previously unsolved platform problem contributes to the streak. Repeats, revisions, failed attempts, sync/import time, and manual checkboxes do not extend it. A failed attempt followed by the first acceptance is still a first solve; “first” does not require acceptance on the first submission attempt. |
| Unique questions | Multiple submissions of the same platform question always produce one question entry and one lifetime unique-solve count. Repeat-event evidence may exist privately for award eligibility, not as duplicate solved-question entries. |
| Revision | An accepted repeat after at least one week can earn 2 extra revision points. It never adds another question entry or extends the streak. Record it as a separate award component. Owner confirmed recurring eligibility seven days after the first solve or last rewarded revision; unrewarded attempts do not restart the clock. Revision awards apply the streak multiplier to the 2-point base. A daily bonus can be earned on each different official daily question first solved that IST day; repeats receive revision awards only. |
| Time | All product boundaries and displayed activity dates follow IST, including daily, weekly, monthly, streak, revision eligibility, and LeetStreak daily awards. Timestamp storage can remain UTC. Do not silently retain a UTC-reset exception in product behavior. |
| Formula changes | Recalculate previous questions for all users under the same new base-point formula/version, rather than leaving older users on a frozen base scale. Preserve source inputs and revaluation history for audit/recovery. |
| Earned daily points | Retain existing earned daily award amounts separately from the base points being revalued. Do not try to reconstruct or overwrite earned bonuses from incomplete old challenge archives. |
| New-user history | Initial/imported historical questions receive base points only, with no retroactive daily bonuses. Owner confirmed new users can earn daily bonuses on future live solves. |
| Handle change | Recalculate for a genuinely different linked coding account; preserve history for a proven rename of the same account. A matching display name/avatar or similar history is not sufficient proof of identity. |
| Friend notifications | Known nonworking feature deferred until explicitly resumed. Preserve its backlog details without spending current milestone work on alert delivery or preference design. Inline daily reminders and friends activity remain in scope. |
| Git workflow | Finish current integration, merge it into `main`, then branch `pre-launch`. Commit and push each clearly labeled completed step on `pre-launch` once implementation is requested. No such action is authorized by this planning edit. |
| Backend plan sync | User plans must be saved and synced in the backend under the authenticated account. Library membership, imported definitions, follows/removals, and external completion must not exist only locally. Local storage is an offline cache/outbox; the backend is the durable account source across extension, website, browsers, and devices. |
| Direct friends | Users must be able to add friends without joining or creating a shared group. Persist friendships in the backend and support both clients. Existing groups remain a separate feature. Request/accept vs one-way follow behavior still needs an explicit product decision before implementation. |

### Remaining product decisions for later implementation

These are proposed defaults, not changes already made to user data or decisions accepted merely by approving the M1 behaviors above.

| Decision | Proposed default | Affected items |
|---|---|---|
| Revision arithmetic | Cooldown is confirmed: recurring seven days since first solve/last rewarded revision; unrewarded acceptances do not restart it. Owner confirmed the streak multiplier applies to the 2-point revision base. Repeated questions are revision-only; different first-time daily questions can each earn a daily bonus within one IST day. | DATA-09 |
| Revision arithmetic and display | Revision awards use 2 × the applicable streak multiplier. Repeated questions receive revision credit only, without a daily award; display the revision component inside the existing question entry. Repeats never count as new questions or streak days. | DATA-02, DATA-07–09 |
| Daily eligibility for new users | Accepted: imported history gets base points only; future live solves can earn daily bonuses. Daily bonuses apply to each different official daily question first solved that IST day; no retroactive daily or repeat-daily awards. | DATA-08 |
| IST daily question selection | Accepted: follow the current official challenge even if it changes within the IST day. Product day boundaries remain IST. Record challenge changes with observation timestamps rather than pinning one slug per day. | DATA-06, DATA-08 |
| Incomplete historical bases | Accepted fallback: apply current base-only credit for old LeetCode questions with unproved first-solve dates; mark history incomplete and exclude those dates from streak/period rankings. If an old daily bonus cannot be reliably separated from its stored combined score, preserve that credited total as protected legacy credit and flag reconciliation rather than guessing. | DATA-04–05 |
| Unlinking | Remove the disconnected platform's active contribution to scores/activity after explicit confirmation; preserve only the minimal private audit/recovery data allowed by the chosen retention policy. | FEAT-05 |
| Unverified ownership | Label existing self-declared accounts; do not silently lock legitimate users out or award verified status without evidence. | FEAT-04 |
| Plan conflicts | Merge unique plans and solve identities; resolve external check/uncheck conflicts through explicit revision/version rules. | FEAT-01 |
| Public history cleanup | Rotate exposed credentials first. Choose targeted history cleanup or a clean public release repository only after a private exposure inventory. | PUB-04 |

### M1 execution steps

Each row is a separate commit/push checkpoint. Local/branch completion is not production completion.

| Step | Scope | State / evidence |
|---|---|---|
| M1-01 | SEC-01 route inventory + OPS-02 key configuration/JWT validation foundation | Passed locally: 7 synthetic token/configuration tests; route map in `backend/ACCESS_CONTROL.md`. Branch commit: `M1 SEC-01 OPS-02 step 1: require stable keys and validate tokens`. Hosting configuration/release still pending. |
| M1-02 | SEC-01 account/group permissions + client session compatibility | Passed locally: 17 backend tests, 3 client session tests, 11 existing progress tests, both type checks/builds; archives synchronized. Owner transfer API added; UI work remains in M1-06. Branch commit: `M1 SEC-01 step 2: enforce account and group permissions`. Not deployed. |
| M1-03 | SEC-02 fail-closed administration | Passed locally: 22 backend tests; every admin route guarded, production test-email route removed, reviewed release previews and durable duplicate-job guards. Commit labeled `M1 SEC-02 step 3`. Awaiting release; interrupted mail jobs require operator review. |
| M1-04 | OPS-01 honest email outcomes | Passed locally: 28 backend tests, including mocked acceptance/rejection/failure/timeout, redacted logs, escaped templates, offloaded SMTP, and accepted-only release state updates. Commit labeled `M1 OPS-01 step 4`. No real messages sent; awaiting release. |
| M1-05 | SEC-03 recovery abuse limits, password policy, session revocation | Backend/local checks passed: 37 tests including recovery, revocation, and additive SQLite migration. Password/reset UI copy and client types updated; password-management settings UI follows M1-06. 3 client session checks, both type checks/builds passed; archives synchronized. Commit labeled `M1 SEC-03 step 5`. Production PostgreSQL migration/release remains pending. |
| M1-06 | SEC-04 Global display-only preference and group/profile behavior | Passed locally: 42 backend + 5 client session/preference tests, both type checks/builds; packages synchronized. Global preference migration, profile field restrictions, transfer/password/session controls implemented. Commit labeled `M1 SEC-04 step 6`; not deployed; full browser visual/release verification remains pending. |
| M1-07 | SEC-05 synthetic fixture isolation + PUB-01–03 current-source cleanup | Passed locally: 44 backend tests, extension build and package inspection. Removed fabricated provider responses, obsolete notification demonstrations/pages, five scratch scripts and tracked installed environment (local environment retained). Current-source scan reviewed reserved example addresses/provider sender and route-path false positives; packages synchronized and obsolete assets absent. Donation QR/controls explicitly approved public on 2026-11-05. Historical exposure and production fixture records remain separate pending work; not deployed. |
| M1-08 | PUB-04 private exposure inventory and concrete remediation proposal | Inventory/proposal prepared for owner review: 662 historical text blobs, 145 ZIP versions, five remote branches plus one tag, GitHub published collections and primary hosted artifact reviewed; private backup restored and integrity checked. Owner approved private rewrite preparation. Rehearsal prepared in isolated protected storage: six refs verified, 521 retained files compared, 869 reachable blobs scanned, approved donation/support assets retained, reviewed packages restored on rehearsal pre-launch and 44 backend tests passed. Local checkout restored after a tool invocation error; remote refs confirmed unchanged. Credential checkpoint closed based on owner confirmation: Supabase password changed and old Render credentials revoked. Final shared-history publication approval remains open. Secondary host timed out; wiki inaccessible; coverage limits recorded privately. No public history rewrite or production change. |
| M1-09 | OPS-06 local PostgreSQL and browser acceptance | Passed locally: 48 backend tests including four native PostgreSQL checks; six client session/preference tests and 11 progress checks; both type checks/builds. Browser login, persisted display preference, password change and revoked-session return to sign-in pass for website and popup preview with no runtime errors. Fixed concurrent migration-registry creation and website token-refresh storage. Synthetic screenshots visually reviewed; native extension acceptance follows M3. Production release and public-history publication remain separate checkpoints. |


### M2 execution steps

| Step | Scope | State / evidence |
|---|---|---|
| M2-01 | DATA-06 shared clock and period boundaries | Passed locally: 54 backend tests including six new boundary/cooldown checks and four PostgreSQL migration checks. Dashboard and streak helpers use one IST clock; shared UTC storage conversion, Sunday-start weeks, exclusive period ends and seven-day elapsed cooldown helpers added. Ingestion, award migration and client date conversion remain later steps; DATA-06 is not yet complete. |
| M2-02 | DATA-02/04/05/08 evidence and award storage | Passed locally: 63 backend tests, including concurrent PostgreSQL migration/event replay/baseline capture, old-point preservation, repeat-event idempotency, stale-account rejection, unique precise award identities and immutable baseline capture. Added account generations, explicit unknown first-solve state, accepted-event/award tables and private score snapshots. Migration does not revalue or reconstruct legacy daily awards. Account deletion/reset also clear private evidence. Runtime ingestion, scoring and UI integration remain later steps. |
| M2-03 | DATA-07/08/09 shared component arithmetic | Passed locally: 71 backend tests, including eight arithmetic checks covering exact component totals, retained credits, invalid metadata and existing base scales. Deterministic Decimal engine added for new ledger integration: existing LC and CF base formulas, capped streak multiplier, multiplied revision awards, explicit retained daily/revision components and four-place half-up rounding. Stored-component totals must match exactly. Runtime calculator migration and read-API integration remain separate steps; no legacy scores are revalued by this module. |
| M5-01 | OPS-03 versioned atomic schema migrations & safe startup lifecycle | Passed locally: 81 backend tests, including 9 migration/lifecycle tests and concurrent PostgreSQL advisory-locked execution. Unified migrations into versioned registry under PostgreSQL advisory lock / local RLock. Removed unconditional startup repairs, remote challenge fetches, immediate polling, and blanket recalculation. Startup fails closed on migration error; shutdown stops scheduler cleanly. Commit labeled 'M5 OPS-03 step 1: make schema initialization atomic, versioned, and safe during startup'. |
| M2-04 | DATA-02/03/04/09 runtime evidence ingestion, repeat deduplication & revision awards | Passed locally: 86 backend tests including 5 sync/deduplication/revision/streak tests. Ingests LeetCode and Codeforces AC submissions into AcceptedSubmission via record_acceptance. Dedupes repeated submissions to single Solve row, eliminates calendar-to-solve conversion, updates DailyActivity strictly from verified first solves, enforces first-solve streak qualification, and awards 2 * streak multiplier for revisions after 7 elapsed days without resetting cooldown on unrewarded attempts. Commit labeled 'M2 DATA-02/03/04/09 step 4: ingest accepted evidence, deduplicate repeat solves, and award revisions'. |
| M2-05 | DATA-01/05/07/08/09 score ledger reconciliation, point awards persistence & handle change recovery | Passed locally: 91 backend tests including 5 reconciliation and handle change tests. Captures protected ScoreSnapshot baseline before recalculation. Unifies point calculations and breakdowns with scoring.py Decimal engine, persisting exact PointAward rows (base, daily, revision) under version points-components-v2. Preserves earned daily bonuses, awards base-only credit for unlogged historical solves without streak inflation, and handles LeetCode handle change by resetting LeetCode solves while strictly preserving Codeforces history and tracking. Commit labeled 'M2 DATA-01/05/07/08/09 step 5: reconcile score ledger, persist point awards, and handle account changes'. |
| M2-06 | FEAT-03 provider sync status and history completeness across clients | Passed locally: 91 backend tests, 11 progress tests, 6 auth/session tests, web check/build and extension tsc/build. Returned leetcode_last_sync, leetcode_history_state, and leetcode_history_gap from backend get_dashboard API, updated web/app and extension App.tsx settings view with sync timestamps and history completeness indicators, and synchronized all 4 ZIP distribution packages. Commit labeled 'M2 FEAT-03 step 6: provide provider sync status and history completeness across clients'. |

### M3 execution steps

| Step | Scope | State / evidence |
|---|---|---|
| M3-01 | UI-01 shared account storage contract & UI-02 immediate accepted submission detection | Passed locally: 91 backend tests, 23 extension tests (6 auth, 6 storage, 11 progress), web check/build and extension tsc/build. Established versioned session storage contract (v2) with automatic legacy migration in extension/src/storage.ts. Added main-world submission bridge (leetcode-page-bridge.js) intercepting fetch/XHR LeetCode submission checks and isolated content-script listener relaying unprivileged hints to background.js. Background service worker handles authenticated sync debouncing and broadcasts sync completions to refresh UI. Rebuilt extension and synchronized all 4 ZIP archives. Commit labeled 'M3 UI-01 UI-02 step 1: shared account storage contract and immediate submission detection'. |
| M3-02 | UI-05 request ordering and sorted caches, UI-06 friend failure separation, UI-07 recency merge, and FEAT-09 session guidance | Passed locally: 91 backend tests, 26 extension tests (6 auth, 6 storage, 3 ordering, 11 progress), web check/build and extension tsc/build. Added request sequence ordering and combined cache keys (tab + sort + user) in extension and web App.tsx, eliminating stale response race conditions. Updated FriendsActivity in Progress.tsx to preserve valid results across platforms during partial failures, retain existing items across refreshes, and merge identical questions preserving the newest timestamp. Added explanatory session requirement messaging for study plan progress. Synchronized all 4 ZIP archives. Commit labeled 'M3 UI-05 UI-06 UI-07 FEAT-09 step 2: request ordering, friend activity merge, and session guidance'. |

### M4 execution steps

| Step | Scope | State / evidence |
|---|---|---|
| M4-01 | FEAT-01 account-backed study plans, playlists, library subscriptions & external completion | Passed locally: 90 backend tests including 7 progress/custom plan tests, 8 PostgreSQL tests, 26 extension tests, web check/build and extension tsc/build. Added UserProgress and UserCustomPlan models and 20261106-progress-v1 migration. Implemented authenticated progress and custom plan endpoints in backend/app/main.py. Integrated bidirectional account sync in extension/src/progress/Progress.tsx with local-first cache/outbox and transparent migration of existing local plans. Rebuilt extension and synchronized all 4 ZIP distribution packages. Commit labeled 'M4 FEAT-01 step 1: persist study plans and playlists to backend account profile'. |




## 4. Security and privacy plans

### SEC-01 — Authenticate account actions and enforce permissions

**Problem:** Most account, group, sync, and kudos routes accept client-supplied identities without validating the acting account. Group owner checks trust the supplied requester ID.

**Files:** `backend/app/main.py`, `auth.py`, `schemas.py`; both clients' API and session code.

**Depends on:** OPS-02 for stable keys; implement regression checks through OPS-06.

**Implementation**

- [x] Inventory every route: explicitly public, authenticated self-service, group-member, group-owner, or admin. Include dashboard/profile reads, solve history, sync, settings, deletion, group codes, and kudos.
- [ ] Add a shared authenticated-user dependency. Validate signature, required expiry/subject, supported algorithm, account existence, and session version; malformed tokens must return controlled errors.
- [x] Derive actor identity from the token. Retained legacy ID fields must match the actor and must never establish authorization.
- [x] Add reusable self/member/owner checks. Use transactions for group creation/membership changes and handle duplicate/racing requests.
- [ ] Update both clients and background requests. Clear invalid sessions and request sign-in rather than treating a cached numeric ID as authentication.
- [ ] Publish a coordinated compatibility change for old clients; do not retain unauthenticated writes as a fallback.

**Acceptance**

- [ ] Anonymous, expired-token, malformed-token, cross-account, and nonmember requests are rejected as appropriate.
- [ ] A normal member cannot impersonate an owner, remove another member, or edit another account.
- [ ] The authorized account/owner can still perform each supported action in both clients.

### SEC-02 — Protect administrative endpoints

**Problem:** Poll-all, broadcast email, and test email routes lack admin authentication. The configured admin secret has a public fallback, and an empty value disables the existing comparison.

**Files:** `backend/app/config.py`, `main.py`, deployment configuration, developer documentation.

**Depends on:** PUB-03–04 for exposure handling; OPS-01 for honest email results.

**Implementation**

- [x] Remove the fallback secret. Missing/empty configuration must disable administrative actions or prevent production startup, according to the documented deployment policy.
- [x] Apply one fail-closed admin dependency to every admin route, including test/broadcast/poll routes. Use constant-time secret comparison or an explicitly authorized admin identity.
- [x] Remove test-email endpoints from production, or limit them to an authenticated development/admin workflow with approved destinations.
- [x] Restrict broadcast inputs to a validated release record; validate HTTPS download destinations and bound input sizes.
- [x] Add limits and audit events for administrative jobs without logging secrets or recipient lists. Coalesce duplicate poll/broadcast jobs.

**Acceptance**

- [x] No admin route succeeds anonymously or with a missing, blank, invalid, or obsolete credential.
- [x] Unauthorized attempts send no email, mutate no records, and start no sync job.
- [x] Valid administration is auditable; errors do not expose configuration values.

### SEC-03 — Password recovery, passwords, and session revocation

**Problem:** Reset initiation reveals account existence and email addresses; OTP attempts are unrestricted; passwords can be four characters; old sessions survive password changes.

**Files:** `backend/app/auth.py`, `models.py`, `schemas.py`, `main.py`; both onboarding/settings clients.

**Depends on:** SEC-01, OPS-01–02; use versioned migration support from OPS-03.

**Implementation**

- [x] Return a generic initiation response and remove full-email disclosure. Make account lookup unambiguous; duplicate LeetCode handles must not reset an arbitrary account.
- [x] Add persisted request cooldowns, expiry, failed-attempt counters, and per-account/source abuse limits. Do not keep the only limiter in process memory.
- [x] Store an OTP verifier rather than plaintext; invalidate previous codes on resend and consume a valid code atomically once.
- [x] Define and enforce the same stronger password policy at registration and reset. Preserve existing users' login compatibility until they change passwords.
- [x] Add an account session version or equivalent revocation mechanism; password reset invalidates prior tokens.
- [x] Add authenticated password change and session-revocation UI where required to complete account management. Keep passwords/codes out of persisted drafts and logs.

**Acceptance**

- [x] Existing/nonexistent-account reset requests do not disclose private identity data.
- [x] Cooldown, attempt exhaustion, expiry, resend, and concurrent reuse behave correctly.
- [x] Old tokens fail after a successful reset; new credentials work in both clients.

### SEC-04 — Global display preference, profile access, and private groups

**Problem:** The existing flag is used as a Global participation/privacy filter, but the owner intends a display preference only. Existing code excludes users with the flag off from Global rankings and uses “friends-only” messaging. Separately, private-group information is readable without proving membership. The earlier review's suggestion to hide activity based on this flag is withdrawn under the clarified product requirement.

**Files:** `backend/app/main.py`, `schemas.py`, group/profile/feed UI in both clients, legal/help copy.

**Depends on:** SEC-01; apply the accepted M1 decisions in section 3.

**Implementation**

- [x] Inventory every use of `global_leaderboard_enabled` in backend queries, schemas, signup/settings, navigation, caches, documentation, and both clients. Separate ranking eligibility from display preferences.
- [x] Introduce an unambiguous preference such as `show_global_leaderboard`. Migrate each existing true/false value to the corresponding display choice while including every registered user in Global ranking calculations. Document/deprecate the old field for compatible clients; never reset every display preference to true.
- [x] Remove participation filters tied to this preference. Global rank, points, period rankings, and inclusion in other people's boards must not change when someone toggles their own Global view.
- [x] Hide/show the Global leaderboard navigation and section on that user's homepage/dashboard. When switching it off while Global is selected, move to Friends or another available view. When reopening either client, respect the persisted preference and ignore stale cached Global selection.
- [x] Rename signup/settings copy to “Show Global leaderboard,” with an explanation that all users still participate. Remove “hidden publicly,” “friends-only mode,” and equivalent privacy promises tied to this setting.
- [x] Write an endpoint-by-viewer permission matrix: public coding profile fields, authenticated account-only fields, group-member data, owner actions, and administrator actions. Accessible profile links must open complete coding stats/recent solves regardless of the profile owner's Global display setting. Keep credential, email, reset, and private settings data separate.
- [x] Restrict private-group membership, codes, and group views to authorized members/owners. Implement owner transfer or group deletion before an owner leaves; define safe behavior when the owner deletes their account.
- [x] Invalidate private caches after account/membership changes. Feed inclusion and profile access must not be suppressed by the Global display toggle. Friend notifications still follow membership and notification settings; exports still follow account authorization.

**Acceptance**

- [x] With Global display off, a user remains ranked and inspectable from another user's Global leaderboard; points/rank eligibility do not change because of the toggle.
- [x] The user's own homepage/dashboard hides the Global view in both clients, persists the choice, and does not reopen a stale Global tab. Re-enabling restores access to that view.
- [x] Clicking an accessible profile opens its coding stats, activity, points, and recent solves whether its owner has Global display on or off. Private account data remains inaccessible.
- [x] Nonmembers cannot read a private group's membership, code, or leaderboard.
- [x] Members retain intended access; leaving/removal takes effect on subsequent requests and cached UI. An owner cannot leave a group without completing the agreed ownership-transfer/deletion flow.
- [x] Signup/settings/help copy cannot be read as opting out of participation or hiding the account from other people.

### SEC-05 — Remove fabricated-profile production behavior

**Problem:** The LeetCode client fabricates totals for handles with testing prefixes, allowing fake profiles to reach real registration/scoring paths.

**Files:** `backend/app/leetcode_client.py`, isolated fixtures/tests, seed tooling if retained.

**Depends on:** PUB-01–02; DATA-05 for any approved score repair.

**Implementation**

- [ ] Remove prefix-based fake responses from production code.
- [ ] Move synthetic data into isolated test fixtures with explicit dependency injection and fictional identities.
- [ ] Privately inventory existing records that might originate from this shortcut. A prefix alone must not be treated as proof that a real account is fake.
- [ ] Prepare a reviewed, dry-run cleanup with backups and an audit of affected totals; do not auto-delete users during application startup.

**Acceptance**

- [ ] A nonexistent test-prefixed handle fails normal provider validation.
- [ ] Tests can still run with synthetic data without contacting or changing production.
- [ ] Any existing-data cleanup has a recorded decision and verified outcome, or remains explicitly pending.

## 5. Scoring and data correctness plans

### DATA-01 — Reconcile LeetCode handle changes

**Problem:** Updating the handle changes user metadata but retains old solves/activity. The resulting account can mix histories from different people.

**Files:** `backend/app/main.py`, `scheduler.py`, `models.py`, `point_calculator.py`; account settings in both clients; extension progress storage migration.

**Depends on:** SEC-01, DATA-04–06; FEAT-04 for verified rename handling.

**Implementation**

- [ ] Distinguish a provider rename from linking a different account; disclose what changes before confirmation.
- [ ] Investigate provider-supported stable account identifiers or trusted ownership evidence for rename matching. Preserve old history only when the same underlying account is established; an ambiguous case needs confirmation/recovery rather than a guess.
- [ ] Stage replacement-account validation/import before publishing the new linked state. Keep the previous state intact if provider requests fail.
- [ ] In one controlled transaction, replace or reassign LeetCode-only history/activity, update provenance, and recompute totals. Preserve Codeforces data.
- [ ] Coordinate concurrent polling/link requests with an account lock or database job mechanism.
- [ ] Namespace client caches by account and linked-handle version; cancel old requests and prevent old progress from being saved under the new handle.

**Acceptance**

- [ ] Switching handles cannot combine their unique solves or retain stale counts.
- [ ] A failed import leaves the existing linked account usable and recoverable.
- [ ] Renames follow the selected identity policy; Codeforces history and unrelated preferences remain correct.

### DATA-02 — One question entry and repeat-submission deduplication

**Problem:** The scheduler increments per-day counts for each recent accepted submission, including duplicates of the same question.

**Files:** `backend/app/scheduler.py`, `models.py`, `platforms.py`, dashboard/ranking aggregations.

**Depends on:** DATA-03–04, DATA-06.

**Implementation**

- [ ] Key the user-visible solve ledger by account, provider identity, platform, and question identity. Repeated submissions never create another unique question entry or increase unique-question totals.
- [ ] Compute Today/This week/This month new-question counts and streak days from the first accepted event for each problem, using IST. Keep repeat/revision activity separately labeled; do not silently count it as newly solved work.
- [ ] Store only the bounded accepted-event evidence needed to verify first solves, daily awards, and DATA-09 cooldowns. Separate award records are not duplicate solved-question entries.
- [ ] Aggregate counters from these deduplicated identities rather than incrementing every submission or preserving an inflated maximum.
- [ ] Backfill only from trustworthy evidence; retain an explicit incomplete marker where the historical identities are unavailable.

**Acceptance**

- [ ] Multiple acceptances of one question, on the same or different days, produce one question entry and one lifetime unique count.
- [ ] A revision-only day does not increase newly solved counts or preserve the streak; two first-time solved questions count twice.
- [ ] Repeating imports does not change counts, and a truncated recent list does not erase established valid counts.
- [ ] Dashboard, profiles, and rankings agree about the same metric.

### DATA-03 — Submission activity vs verified accepted solves

**Problem:** Calendar activity currently becomes at least one solved question even when no accepted problem is known. Submission calendars alone do not establish acceptance.

**Files:** `backend/app/leetcode_client.py`, `scheduler.py`, `models.py`, `platforms.py`, `streak.py`; stats/help UI.

**Depends on:** The accepted first-solve-only streak rule; implement DATA-06 date helpers before migrating activity records.

**Implementation**

- [ ] Store provider calendar activity separately from verified accepted-question activity, with source and completeness metadata.
- [ ] Remove the “calendar activity means one solved question” conversion.
- [ ] Derive qualifying streak days only from first accepted solves of previously unsolved questions on either linked platform. Repeated acceptances, revision awards, and failed attempts never qualify.
- [ ] Keep calendar/recent-repeat activity separate from new-question streak evidence. A newly imported record uses its known accepted date, never its import date, and a repeat's timestamp must not be misrepresented as a first solve.
- [ ] Reconcile existing rows conservatively. Do not turn missing evidence into either a fabricated accepted solve or proof that someone did no work.

**Acceptance**

- [ ] A day with submissions but no accepted evidence is not presented as a verified solved-question count.
- [ ] Unknown historical accepted counts are distinguishable from zero.
- [ ] Streak, volume, and score definitions match the displayed explanations.
- [ ] Re-solving yesterday's question today cannot extend the streak, even when it earns a revision award. A first-time solved question on either platform does qualify.

### DATA-04 — Incomplete LeetCode history and reconciliation

**Problem:** Backend polling requests only 20 recent acceptances. Public profile totals and calendars do not provide a complete question-and-timestamp ledger. The extension's full solved-slug import also does not provide first-accepted timestamps.

**Files:** `backend/app/leetcode_client.py`, `scheduler.py`, `models.py`; `extension/src/progress/history.ts`, `data.ts`; future account-backed progress API.

**Depends on:** SEC-01, DATA-02–03; FEAT-03 exposes the result.

**Implementation**

- [ ] Track what is known separately: aggregate profile totals, observed accepted events, session-observed solved slugs, and historical coverage gaps.
- [ ] Persist reliable submission IDs/timestamps where available, use overlapping ingestion and idempotency, and detect rather than hide polling gaps.
- [ ] Check provider-supported retrieval options before claiming full historical event import. Do not assume a public endpoint can paginate all LeetCode acceptances.
- [ ] Keep automatic browser-session solved-slug import for plan completion, including identity checks, cancellation, and incomplete-response rejection.
- [ ] If client history is uploaded for cross-device progress, treat it as client-observed plan evidence, not independent proof of competitive score eligibility.
- [ ] State limitations in the API/UI. Never manufacture timestamps or silently replace missing history with exact-looking awards.

**Acceptance**

- [ ] Missing history is visible and cannot be mislabeled as a complete import.
- [ ] Re-imports and overlapping polls are idempotent; failed imports preserve valid saved data.
- [ ] Full plan completion can improve without inventing historical score events.

### DATA-05 — Fair base-point revaluation and preserved earned bonuses

**Problem:** Missing solves are proportionally estimated using difficulty totals and a current streak multiplier. Later syncs can change those estimates without new solves. Current recalculation also recomputes historical awards.

**Files:** `backend/app/point_calculator.py`, `models.py`, `contest_ratings.py`, score/ranking UI.

**Depends on:** DATA-03–04, DATA-06, and DATA-08 bonus preservation. Implement the shared arithmetic with DATA-07 before migrating awards.

**Implementation**

- [ ] Split total points into revaluable base awards, retained earned daily awards, revision awards, and clearly labeled historical estimates/corrections. Do not hide daily amounts inside one mutable total.
- [ ] Persist the scoring version and inputs used for an award: provider/problem identity, rating or fallback inputs, challenge bonus, streak date/value, and precision.
- [ ] Apply each approved base-formula change to previous questions for all users under the same scoring version. Do not freeze older users' base credit while newly imported users receive a different scale.
- [ ] Snapshot and retain each known earned daily award amount before base revaluation. Preserve any already-earned bonus component, including any historically applied bonus multiplier, as an explicit retained amount; do not rediscover it from old challenge archives.
- [ ] For new-user historical imports, calculate base points only and create no retroactive daily/revision awards. Do not use import-time/current streak to manufacture historical bonuses.
- [ ] Keep uncertainty in incomplete old history explicit. Compare feasible per-question reconstruction with a consistently applied documented fallback for missing inputs; obtain the remaining policy decision before claiming exact/fair historical totals.
- [ ] Decide how verified discoveries replace estimates without double counting and how rejudgements/rating corrections are recorded.
- [ ] Prepare a dry-run comparison for existing accounts, review significant changes privately, and migrate transactionally with rollback/recovery evidence.
- [ ] Keep the current CF scale documented as provisional. Calibration changes require a version and explicit revaluation policy.

**Acceptance**

- [ ] Repeating a recalculation under the same formula/inputs is idempotent; approved formula changes revalue all affected users' prior base points consistently.
- [ ] A formula migration changes base amounts without deleting, duplicating, or recomputing retained earned daily bonuses. New imported histories get no historical daily/revision credit.
- [ ] Every total can be explained as verified awards plus disclosed adjustments/estimates.
- [ ] Replacing estimates with known solves cannot award both credits for the same work.

### DATA-06 — Timestamp and day-boundary consistency

**Problem:** UTC timestamps, IST activity dates, server-local `date.today()`, and provider challenge dates are mixed.

**Files:** `backend/app/scheduler.py`, `point_calculator.py`, `main.py`, `streak.py`, `platforms.py`; extension daily reminder and date rendering.

**Depends on:** Activity/streak policy from DATA-03.

**Implementation**

- [ ] Establish shared helpers: UTC instant storage, but IST for all product day/week/month/streak/revision/daily-award boundaries and displayed activity dates. Compare a week-long revision cooldown using unambiguous IST-aware timestamps under the chosen cooldown rule.
- [ ] Map provider challenge identifiers/publication instants to an explicit LeetStreak IST-day challenge record. Resolve which question belongs to each IST day before coding this mapping; do not assume the provider resets at IST midnight or silently retain UTC product days.
- [ ] Return timezone-explicit timestamps and stop deriving challenge dates from the host machine's local timezone.
- [ ] Use the same date helpers in ingestion, score calculation, profiles, rankings, and notifications.
- [ ] Backfill date-derived aggregates from preserved timestamps where possible. Flag records with ambiguous origins rather than guessing.

**Acceptance**

- [ ] Boundary examples cover IST midnight, week/month/year transitions, seven-day revision eligibility, and an open popup crossing an IST daily reset. UTC midnight alone does not reset product counters or daily eligibility.
- [ ] Changing the server timezone does not alter a user's counts or awards.
- [ ] Both clients show the same challenge eligibility and activity totals for identical data.

### DATA-07 — One authoritative point calculation

**Problem:** The award and breakdown functions round streak multipliers differently; reads may combine newly calculated explanations with previously stored awards.

**Files:** `backend/app/point_calculator.py`, `main.py`, `schemas.py`; scoring modals in both clients.

**Depends on:** The recorded DATA-05 scoring policy and DATA-06 date helpers. Implement the shared calculation before DATA-05's award migration.

**Implementation**

- [ ] Return one structured calculation result for both storage and display, with explicit internal precision and display rounding.
- [ ] Use that result for LC and CF awards; avoid separate arithmetic paths for explanations.
- [ ] Render historical explanations from the active approved base-revaluation version plus separate retained daily/revision components. Keep prior input/version snapshots for audit; do not imply historical bases are permanently frozen.
- [ ] Make read endpoints observational; move metadata repair or point reconciliation into explicit sync/migration jobs.

**Acceptance**

- [ ] Breakdown fields reproduce the stored award under the documented rounding rules.
- [ ] The same solve does not receive different results from storage and display helpers.
- [ ] Reading a profile does not silently change its scored ledger.

### DATA-08 — Retained earned daily awards and base-only historical imports

**Problem:** Daily bonuses currently share mutable solve totals and may be reconstructed from incomplete old challenge archives. Base revaluation must retain already-earned daily points; a new user's imported history must not receive guessed past daily bonuses.

**Files:** `backend/app/models.py`, `scheduler.py`, `point_calculator.py`, challenge history; help and daily reminder UI.

**Depends on:** DATA-02, DATA-06–07; implement retained-bonus extraction before DATA-05 revaluation. Resolve future new-user/repeated-daily eligibility and IST challenge assignment before adding new awards.

**Implementation**

- [ ] Store earned daily award amounts in a dedicated component/event keyed by account/provider identity/platform/IST challenge date, with question, evidence, source, and rule version.
- [ ] Extract known already-earned daily amounts before altering bases; retain their exact awarded component. For rows where the old daily component cannot be established confidently, prepare a private impact report and seek a policy choice rather than silently losing or inventing points.
- [ ] Initial/imported historical questions receive base-only credit. Do not infer historical daily eligibility from a solved slug, archive match, current streak, or import time; a newly registered account must not gain retroactive daily points.
- [x] Set future/repeated daily eligibility: new users can earn live daily bonuses; each different official daily question first solved that IST day can earn one. There is no across-question daily cap. Repeats earn revision credit only. Implementation remains pending below.
- [ ] Once those decisions are made, record eligible live awards idempotently. A repeated daily never adds a second unique base award or extends the first-solve-only streak; any overlap with revision points follows the agreed stacking rule.
- [ ] Update help, breakdowns, reminders, and migrations to distinguish current base credit, retained earned daily points, revision credit, and unknown historical evidence.

**Acceptance**

- [ ] Existing earned daily points survive an approved base-formula migration unchanged and are never awarded twice.
- [ ] New-user historical imports generate no past daily bonus, even if a question appears in an old daily archive.
- [ ] Accepted live daily eligibility, repeat handling, and IST-day mapping are explicitly decided and verified before completion; pending choices keep this item open.

### DATA-09 — Revision points after at least one week

**Requirement:** An accepted repeat of an already solved question after at least one week can earn 2 extra revision points. It does not produce another question entry, another base award, or a streak day.

**Files:** `backend/app/models.py`, provider ingestion/sync clients, `point_calculator.py`, score schemas; question/profile/help displays in both clients.

**Depends on:** DATA-02–04, DATA-06–07, OPS-03 migration infrastructure. Use the confirmed recurring seven-day first-solve/last-reward anchor; owner confirmed the streak multiplier applies and repeats do not earn daily bonuses.

**Implementation**

- [ ] Record the original accepted problem identity and sufficient subsequent accepted-event timestamps/IDs to prove eligible revisions. Rewards recur at least seven days after the first solve or last rewarded revision. Unrewarded attempts do not restart the clock.
- [ ] Record a separate revision award for 2 points linked to the original question entry; never duplicate the solve row, increment new-question counts, or extend the streak.
- [x] Confirm revision arithmetic: multiply the 2-point base by the applicable streak multiplier. Repeated questions do not also earn a daily bonus.
- [ ] Add transactional uniqueness/idempotency so repeated polls, concurrent syncs, and replayed submissions cannot reward the same revision twice. Define which event wins when several eligible acceptances arrive in one batch.
- [ ] Do not award historical revisions from initial imported history without an explicitly approved backfill policy. Missing repeated-acceptance data means incomplete evidence, not permission to synthesize events.
- [ ] Show any revision credit within the existing question entry and score breakdown, with clear separation from base/daily points. Document cooldown behavior in help and website scoring.

**Acceptance**

- [ ] A repeat before seven days does not earn revision credit; an evidence-backed repeat at/after the agreed boundary can earn the agreed 2-point award.
- [ ] Replays/concurrent requests do not duplicate credit; subsequent revisions follow the explicitly chosen recurrence rule.
- [ ] Revision-only days do not extend the streak or create duplicate question entries/counts; base/daily components remain separately auditable.
- [ ] Both clients and total/profile/ranking displays agree with the revision ledger under IST boundaries.

## 6. Extension and website behavior plans

### UI-01 — Shared account storage contract

**Problem:** The popup stores an account ID/token, while the background worker and old listener expect different user objects.

**Files:** `extension/src/storage.ts`, `src/App.tsx`, `src/lib/api.ts`, `public/background.js`, `public/leetcode-listener.js`.

**Depends on:** SEC-01, OPS-02.

**Implementation**

- [x] Define one versioned session storage contract and an explicit migration from legacy keys.
- [x] Let the background worker handle authenticated backend requests; content scripts should send narrow messages rather than read credentials.
- [x] Observe storage changes for login/logout/account switching. Clear account-specific pending alerts and invalidate stale caches.
- [x] Handle storage failures and expired sessions explicitly; retain only intentionally persistent preferences.

**Acceptance**

- [x] Fresh login, existing installation migration, restart, logout, and account switching work across popup/background paths.
- [x] Logout stops account-scoped background actions and clears credentials.
- [x] No content script needs access to the backend bearer token.

### UI-02 — Immediate accepted-submission detection

**Problem:** Patching `window.fetch` in the isolated content-script world does not intercept LeetCode page fetches.

**Files:** `extension/manifest.json`, `public/leetcode-listener.js`, `public/background.js`; progress refresh events.

**Depends on:** UI-01, SEC-01, DATA-02.

**Implementation**

- [x] Choose a narrow supported detection mechanism: a validated page-world bridge or a robust provider-specific observer. Keep extension credentials outside page context.
- [x] If using a page bridge, package it locally and validate message origin, shape, sender, and expected event type. Treat page messages as hints only.
- [x] Debounce accepted hints in the worker; fetch trusted provider data before awarding points. A forged hint may request a bounded sync, not create a solve.
- [x] Cover fetch/XHR differences and SPA navigation where applicable. Preserve scheduled sync as the fallback.

**Acceptance**

- [x] An actual accepted result triggers one bounded authenticated sync and refreshes open UI.
- [x] Failed/pending submissions and duplicate events do not create awards or repeated jobs.
- [x] Untrusted page messages cannot claim another user's identity or arbitrary points.

### UI-03 — Manifest V3 notification page

**Status: Deferred by the owner.** Keep as a future friend-notification repair; do not schedule delivery work now. Security cleanup of packaged assets remains applicable. The inline daily challenge reminder is a separate in-scope feature.

**Problem:** `notification.html` uses an inline script that the default extension policy blocks. It also inserts external strings through `innerHTML`.

**Files:** `extension/public/notification.html`, a packaged notification script, manifest if necessary.

**Depends on:** None; coordinate with UI-04.

**Implementation**

- [ ] Move behavior into a local external script; retain the restrictive extension policy.
- [ ] Build message content using text nodes/text content, not interpolated HTML.
- [ ] Validate outgoing problem URLs against supported HTTPS platform domains.
- [ ] Implement close/open/timeout behavior and a meaningful missing-data state within the available window size.

**Acceptance**

- [ ] The packaged notification initializes without a policy violation; all controls work.
- [ ] Names/titles containing markup render as plain text.
- [ ] Invalid destinations cannot become executable or unrelated links.

### UI-04 — Notification selection and delivery semantics

**Status: Deferred by the owner.** No current alert-delivery implementation or notification product decisions are required. Retain the following as backlog notes for when this feature is explicitly resumed.

**Problem:** Notifications consider only the newest global item, lack friend filtering, label all platforms LeetCode, and open a focused window.

**Files:** `extension/public/background.js`; authenticated friend activity endpoint; notification renderer.

**Depends on:** SEC-04, UI-01–03, FEAT-07.

**Implementation**

- [ ] Fetch authorized friend activity through a stable cursor, including all eligible new events rather than only `feed[0]`.
- [ ] Persist a per-account cursor and bounded delivered-event identities. On first setup, establish a baseline without replaying old history.
- [ ] Label/link the actual platform, exclude self events, and honor group membership, quiet hours, and notification preferences. The Global leaderboard display toggle must not control notification eligibility.
- [ ] Default to a non-focus-stealing alert. Make floating windows explicitly optional; group bursts rather than opening many windows.
- [ ] Define cursor behavior after offline periods and errors so recovery neither loses all events nor floods the user.

**Acceptance**

- [ ] Multiple new friend events are handled once; unrelated/nonfriend users do not trigger friend alerts. Friends remain eligible regardless of their own Global leaderboard display choice.
- [ ] LC and CF alerts use correct names/links, including after worker restarts.
- [ ] First install, offline recovery, logout, and account switching do not replay another account's alerts.

### UI-05 — Request ordering and sorted caches

**Problem:** A slow response for a previous tab/sort can overwrite the selected leaderboard; cache keys omit sort mode.

**Files:** `extension/src/App.tsx`, `web/app/App.tsx`, both API clients and account cache helpers.

**Depends on:** SEC-01/04 for correct cache scoping.

**Implementation**

- [x] Key data by account, board/group, and sort mode, plus any future period/filter.
- [x] Cancel superseded requests or ignore responses whose request generation/key is stale.
- [x] Scope loading/error state to the active request; discard private caches after membership or account changes.
- [x] Distinguish cached data from fresh results without showing a different board under the current label.

**Acceptance**

- [x] Deliberately reversed response order cannot replace the selected tab/sort.
- [x] Sort changes and account switches do not reuse incompatible cached boards.
- [x] A failed obsolete request does not clear the current result or its loading state.

### UI-06 — Friend activity failures vs empty results

**Problem:** A failed public LeetCode lookup is converted to an empty array, hiding the difference between no activity and a provider failure.

**Files:** `extension/src/progress/Progress.tsx`; future friend activity API and website equivalent.

**Depends on:** FEAT-03; SEC-04 for viewer scope.

**Implementation**

- [x] Represent loading, success-empty, partial success, stale data, and error separately, including per-platform outcomes.
- [x] Keep previously loaded valid activity while a refresh is pending or fails.
- [x] Use bounded retries/backoff and an actionable retry state; avoid clearing/reloading the entire list on every refresh.
- [x] Do not suppress a friend's valid LC results solely because their CF lookup failed, or vice versa.

**Acceptance**

- [x] A provider failure cannot display as a verified “no recent solves” result.
- [x] Partial results remain usable with a clear error indication.
- [x] Repeated refreshes do not create flicker, unbounded requests, or misleading success states.

### UI-07 — Merge friend activity without losing recency

**Problem:** Deduplication can let an older backend ledger entry replace a more recent public acceptance of the same question.

**Files:** `extension/src/progress/Progress.tsx`, shared activity normalization if introduced.

**Depends on:** DATA-02/06; coordinate with UI-06.

**Implementation**

- [x] Define whether this view represents accepted events or latest activity per problem. Keep first-accepted scoring distinct from most-recent activity.
- [x] Normalize all timestamps and platform/problem identities before merging.
- [x] For a latest-per-problem view, explicitly choose the maximum valid timestamp; merge useful metadata without changing the event's date.
- [x] Apply deterministic tie-breaking and ensure link/platform labels come from the selected record.

**Acceptance**

- [x] Older ledger entries cannot move a recent acceptance backward in the feed.
- [x] Input order does not change merged results.
- [x] A problem on two platforms remains distinguishable; activity recency does not rewrite first-accepted points.

## 7. Reliability and maintenance plans

### OPS-01 — Honest email delivery results

**Problem:** The dispatcher returns success even when providers fail or no sender is configured. Some provider rejection responses are also treated as success.

**Files:** `backend/app/email_service.py`, password recovery/admin handlers in `main.py`.

**Depends on:** Coordinate with SEC-02–03.

**Implementation**

- [x] Return structured dispatch outcomes: accepted by provider, unavailable, rejected, or failed. Do not claim inbox delivery merely because a provider accepted a request.
- [x] Restrict no-send/log-only transport to explicit development mode; never log OTPs or private message bodies.
- [x] Keep public reset responses generic while recording private delivery failure for operations/retry. Mark update delivery only after genuine provider acceptance.
- [x] Bound retries and make broadcasts idempotent. Sanitize interpolated content and avoid blocking the async server with synchronous SMTP work.

**Acceptance**

- [x] Missing configuration, rejection, timeout, and failed fallback cannot produce a successful delivery record.
- [x] Provider acceptance produces the expected state without duplicate sends on retries.
- [x] Error logs contain actionable status without credentials, OTPs, or recipient dumps.

### OPS-02 — Stable signing keys and sessions

**Problem:** Without configured `JWT_SECRET`, each process generates a new secret. Restarted or multi-process services therefore reject otherwise valid tokens.

**Files:** `backend/app/config.py`, `auth.py`, `render.yaml`, safe environment examples and setup documentation.

**Depends on:** SEC-01/03; PUB-03 for configuration hygiene.

**Implementation**

- [ ] Require a stable, strong production key through hosting secrets; allow an explicit development-only ephemeral mode with clear behavior.
- [ ] Declare the required variable without committing a value and validate configuration at startup.
- [ ] Document safe rotation, planned sign-out effects, and deployment verification. Verify actual hosting configuration privately rather than assuming YAML reflects it.
- [ ] Ensure client session handling distinguishes unauthorized/expired access from network/provider failures.

**Acceptance**

- [ ] A restart with the same key preserves valid sessions; key rotation/revocation rejects them as intended.
- [ ] Production cannot silently start with an ephemeral or missing key.
- [ ] No real key appears in code, examples, logs, archives, or history added by this work.

### OPS-03 — Startup, migrations, and expensive reconciliation

**Problem:** Startup performs historical remote archive fetches and all-user scoring. Schema changes are scattered through import/startup code, with warnings that can hide partial failure.

**Files:** `backend/app/main.py`, `scheduler.py`, `platform_migration.py`, database migration/job tooling, deployment instructions.

**Depends on:** DATA-05–07; coordinate migration framework with SEC-03 and FEAT-01.

**Implementation**

- [x] Move schema changes into ordered, versioned, repeatable migrations with explicit failure behavior and backup/recovery instructions.
- [ ] Backfill challenge archives incrementally using stored coverage/checkpoints; fetch missing months only.
- [ ] Run all-user point reconciliation as an explicit versioned job, in bounded batches with progress and restart recovery.
- [x] Separate basic liveness from readiness. Startup should validate local configuration/schema and avoid waiting on years of provider requests.
- [x] Remove unconditional historical repair statements from normal startup after migrating their intended data safely.

**Acceptance**

- [x] Restarting does not refetch the full archive or revalue all accounts.
- [x] Migration failure is visible and cannot leave a falsely healthy incompatible service.
- [ ] Interrupted backfills resume without duplicate awards or lost coverage.

### OPS-04 — Cross-process job coordination

**Problem:** Scheduler jobs, per-user locks, and CF request limits are process-local. The current model assumes one service process.

**Files:** `backend/app/scheduler.py`, `codeforces_sync.py`, `codeforces_client.py`, sync routes; job-state schema/deployment configuration.

**Depends on:** SEC-01–02, OPS-03; FEAT-03 for job status.

**Implementation**

- [ ] Document and enforce the current single-scheduler constraint until shared coordination is implemented.
- [ ] Introduce durable per-account job ownership/leases with expiry, atomic acquisition, retries, and idempotent writes. Do not hold database row locks across slow provider requests.
- [ ] Use one shared provider rate limiter/worker ownership model across processes; select database coordination or a queue/cache only after estimating expected volume.
- [ ] Coalesce manual sync, background polling, and linking jobs. Bound concurrency, batch size, retries, and queue length.
- [ ] Handle worker shutdown, lease expiry, and rejected provider requests without corrupting committed history.

**Acceptance**

- [ ] Two processes requesting the same account do not perform conflicting imports.
- [ ] Rate limits apply across the deployment, not separately per worker.
- [ ] A crashed worker's job is recoverable; clients can see a truthful queued/running/failed state.

### OPS-05 — Release metadata and update behavior

**Problem:** Manifest/version metadata and release notes remain at an old version; declared silent update paths are incomplete for manually loaded ZIP installations.

**Files:** `extension/manifest.json`, package metadata, `backend/app/main.py`, build/package scripts, installation documentation.

**Depends on:** PUB-05; coordinate backend/client compatibility after SEC-01.

**Implementation**

- [ ] Establish one release metadata source: semantic version, minimum backend/client compatibility, source revision, release notes, and artifact checksums.
- [ ] Generate the manifest/API update response from the release record and ensure the served archive matches it.
- [ ] Separate manual ZIP reload instructions from genuine browser/store-managed automatic updates. Remove or repair unsupported CRX/update references; do not promise automatic updating of unpacked installs.
- [ ] Add a release procedure for branch builds vs public stable builds and a rollback-compatible backend/client order.

**Acceptance**

- [ ] Downloaded package version, API metadata, source revision, and release notes agree.
- [ ] Older clients see the appropriate update/compatibility message; current clients do not see a false update.
- [ ] Installation/update instructions work for the distribution channel actually offered.

### OPS-06 — Regression coverage and continuous checks

**Problem:** Existing progress tests do not cover the main security, scoring, migration, and integration risks.

**Files:** isolated backend/client test directories, `.github/workflows/`, package scripts, contributor documentation.

**Depends on:** Build incrementally alongside each fix, starting with SEC-01–03 and DATA-02/06–07.

**Implementation**

- [ ] Add deterministic auth/permission, OTP, privacy, counts, streak boundary, scoring, rejudgement, and idempotent-ingestion cases.
- [ ] Add database migration checks for supported database targets, transactions, uniqueness, and concurrent jobs.
- [ ] Add client cases for reversed request order, cache identity, account switching, storage migration, plan defaults/removal/empty state, import cancellation, and provider failures.
- [ ] Use fictional fixtures and mocked providers; normal CI must require no real accounts, email delivery, or production secrets.
- [ ] Run type checks, relevant tests, builds, and artifact validation in CI. Keep a short explicit manual extension verification checklist for browser-only behaviors.
- [ ] Add secret/artifact hygiene checks from PUB-03/05 and pin/configure workflow permissions deliberately.

**Acceptance**

- [ ] A clean checkout can run documented checks with synthetic data.
- [ ] A regression in a fixed P0/P1 path fails its corresponding check.
- [ ] CI cannot contact production, send real test emails, or publish private fixtures by default.

### OPS-07 — Tracked environments and generated outputs

**Problem:** Thousands of virtual-environment files are tracked, and several copies of generated bundles/archives require manual synchronization.

**Files:** `test_env/`, `.gitignore`, `.dockerignore`, build/package tooling, generated artifact locations.

**Depends on:** PUB-02 and PUB-05; preserve compatibility with the current download endpoint.

**Implementation**

- [ ] Remove `test_env/` from Git tracking without deleting a developer's working environment unnecessarily; add an effective ignore rule.
- [ ] Document reproducible environment installation from maintained dependency files.
- [ ] Identify authoritative source vs required release output. Remove abandoned generated copies only after confirming all references and consumers.
- [ ] Automate any ZIP copies that remain necessary; prefer one built artifact copied to the required locations, with checksums proving equality.

**Acceptance**

- [ ] A fresh clone contains no tracked installed environment or dependency tree.
- [ ] Developers can recreate the environment from documentation.
- [ ] Builds/downloads still work and required package copies are identical.

## 8. Product feature plans

### FEAT-01 — Account-backed plans and preferences

**Gap:** Followed/custom plans, external completion, and view preferences live locally, so they do not follow the same account across browsers/devices.

**Owner requirement:** Backend persistence and account sync are mandatory. The server holds durable plan/progress state; a local-only implementation does not satisfy this task. This is an accepted requirement, not an optional future enhancement.

**Files:** new backend plan/progress models and authenticated API; `extension/src/progress/`, storage/session code; website integration later.

**Depends on:** SEC-01/04, DATA-04, OPS-03; FEAT-04 distinguishes identity assurance.

**Implementation**

- [x] Model a plan's provider identity/version, account library membership, removal tombstones, external-item completion, and relevant preferences. Keep solved identities separate from a specific plan.
- [x] Support adding custom study plans/playlists via URL link or catalog into Progress; persist user-added plan definitions, followed playlists, hidden/removed starters, and item completion directly to the user's backend account profile so that progress and playlists are never just locally saved in browser storage.
- [x] Add authenticated bounded CRUD/sync endpoints with revision conflict handling. Handle check and uncheck/removal operations, not just set union.
- [x] Migrate existing local data once per account with preview/recovery where needed. Preserve the three starter plans and a deliberately empty library.
- [x] Keep a local offline cache/outbox; merge on reconnection and prevent old account writes after sign-out/switching.
- [x] Load authoritative account state from the backend on sign-in/open/reconnection. Distinguish locally pending changes from server-confirmed saves, handle failures without falsely claiming sync, and reconcile revisions across devices.
- [x] Separate client-observed LC progress from server-verified competitive score evidence. External checkmarks never award competitive points.
- [x] Keep routine history sync automatic; do not add a required Sync History button.

**Acceptance**

- [x] Plans and external completion appear correctly in a second session/device.
- [x] Clearing local cache or reinstalling the extension recovers all server-confirmed plans, follows/removals, and external completion after sign-in. Loss of unsynced offline work is clearly distinguished from loss of synced data.
- [x] An authenticated backend response/database inspection confirms persistent plan records; two clients do not merely reuse the same browser storage. One account cannot read or alter another's plans.
- [x] Conflicting edits, offline removals, no plans, duplicate imports, and logout have deterministic outcomes.
- [x] Re-importing a plan retains valid solved progress without restoring intentionally removed plans unexpectedly.


### FEAT-02 — Website Progress section

**Gap:** The website has no equivalent of the extension's plan library and progress experience.

**Files:** `web/main.tsx`, `web/app/`, `web/web.css`; shared pure plan logic only if extracted safely.

**Depends on:** FEAT-01, FEAT-03, SEC-04.

**Implementation**

- [ ] Add website Progress navigation, friends activity above playlists, plan cards, search/filter, next question, and persistent question-list/section expansion.
- [ ] Use account-backed data and responsive page layout in the established theme.
- [ ] Support plan add/remove, preview, starter restoration, loading/errors, and the zero-plan state.
- [ ] Account for browser CORS/permission differences: the website cannot simply reuse extension host-permission scanning or its authenticated LeetCode bridge. Start with supported server/catalog metadata and pasted links; evaluate any server scraper separately with network access controls.
- [ ] Preserve independent extension builds and sources. Extract pure logic intentionally rather than copying another entire application.

**Acceptance**

- [ ] Website edits sync to the extension and vice versa after reconnection.
- [ ] Desktop/mobile layouts preserve usable controls and accessible navigation.
- [ ] Unsupported imports clearly offer an alternative rather than claiming universal compatibility.

### FEAT-03 — Sync status and history completeness

**Gap:** Users cannot reliably distinguish up to date, importing, partial history, provider failure, and stale cached data.

**Files:** backend sync state/API; both client dashboards/settings/progress views.

**Depends on:** DATA-04; coordinate with OPS-04.

**Implementation**

- [x] Store separate status per platform: queued/running/idle/failed, last attempt/success, next retry, coverage/completeness, and sanitized error category.
- [x] Expose an authenticated status response; avoid relying solely on a timestamp or the absence of an error string.
- [x] Show a compact status line and accessible detail view in both clients; distinguish provider history completeness from local plan sync completeness.
- [x] Poll only while needed, back off after failures, and preserve previous successful data. Refresh automatically after accepted activity and account changes.

**Acceptance**

- [x] A failed/partial import cannot be displayed as fully up to date.
- [x] Users can understand which platform is delayed without seeing private diagnostics.
- [x] Status settles after success/failure and does not leave an infinite loading indicator.

### FEAT-04 — Coding-account ownership verification

**Gap:** Linking validates that a public profile exists, not that the LeetStreak user owns it. A unique CF claim can therefore block the real owner.

**Files:** account-link models/API, provider clients, signup/settings and verification UI.

**Depends on:** SEC-01–03, OPS-03; data treatment from DATA-01/05.

**Implementation**

- [ ] Investigate provider-supported ownership proof before promising a method. Prefer official authorization if available; otherwise evaluate an expiring one-time public-profile challenge only where feasible.
- [ ] For a proof challenge, generate a random account/provider-bound token, verify through a trusted server fetch, expire it, and prevent replay. Never ask for provider passwords/cookies.
- [ ] Track unverified/pending/verified/disputed state, proof time, and verified provider identity where available.
- [ ] Define the ranking eligibility policy for unverified accounts and a recovery process for preclaimed handles/provider renames. Retain existing users without falsely marking them verified.
- [ ] Keep signup's CF field optional and allow onboarding before CF verification.

**Acceptance**

- [ ] Knowing a handle alone cannot produce verified ownership.
- [ ] Expired/reused/wrong-account challenges fail, and claims have an auditable recovery path.
- [ ] Existing legitimate accounts can migrate without handing credentials to LeetStreak.

### FEAT-05 — Unlink Codeforces

**Gap:** Settings allows connecting/replacing a handle but not disconnecting it.

**Files:** authenticated backend link API, sync jobs, `models.py`, settings in both clients, extension plan state.

**Depends on:** SEC-01, DATA-05, OPS-04; record the unlink retention/scoring policy.

**Implementation**

- [ ] Add a clear disconnect action with an impact summary and explicit confirmation, including effects on score, activity, streak, and plan completion.
- [ ] Cancel/invalidate in-flight work using a linked-account version. Atomically detach the handle and reconcile its active data according to the selected policy.
- [ ] Recompute affected totals without deleting LeetCode data. Release the handle claim and clear stale CF plan observations.
- [ ] Define relinking behavior and recovery/retention limits without exposing old data to a subsequent claimant.

**Acceptance**

- [ ] Disconnect updates both clients and all affected aggregates consistently.
- [ ] A late sync response cannot recreate disconnected data.
- [ ] Reconnecting is idempotent and never doubles points.

### FEAT-06 — Weekly/monthly points rankings

**Gap:** Current point sorting is based on lifetime totals, giving established histories a lasting advantage.

**Files:** backend ranking query/schema/indexes; ranking controls/cache keys in both clients.

**Depends on:** DATA-02, DATA-04–07, UI-05, SEC-04.

**Implementation**

- [ ] Add explicit lifetime/week/month periods using the selected activity timezone and documented week start.
- [ ] Sum eligible awarded events within the period; exclude undated estimates from period rankings unless a separate explicit policy permits them.
- [ ] Apply the same period rules to global/friends/group views, tie-breaking, and own-rank pinning. Everyone remains eligible for Global rankings; the Global display preference only controls the viewer's own homepage section. Enforce private-group access separately.
- [ ] Include period in cache keys and support efficient indexed queries rather than loading all historical events per viewer.

**Acceptance**

- [ ] Known fixtures produce correct totals/ranks across week/month boundaries.
- [ ] Undated legacy credit does not leak into this week's score.
- [ ] Period labels, user rank, and displayed points stay aligned when switching rapidly.

### FEAT-07 — Notification preferences

**Status: Deferred by the owner with friend notifications.** Do not add or redesign friend-alert settings now. Existing inline daily-reminder dismissal remains in scope independently.

**Gap:** Users lack clear controls for friend alerts, floating windows, sound, quiet hours, and notification frequency.

**Files:** account preferences API/settings; extension storage/background/reminder code.

**Depends on:** FEAT-01, UI-01/04, DATA-06.

**Implementation**

- [ ] Add compact settings for enabled alerts, friend-only scope, delivery mode, optional sound where supported, quiet hours/timezone, and burst grouping.
- [ ] Preserve the existing daily reminder's per-day dismissal. Clarify that daily reminders and friend alerts are separate preferences.
- [ ] Decide which preferences follow the account vs device/browser capability; honor browser/OS permission denial without repeatedly prompting.
- [ ] Enforce preferences in the background delivery path, including after restart, not only in visible UI.

**Acceptance**

- [ ] Muted/quiet-hours alerts produce no focused window or sound.
- [ ] Reminder dismissal survives closing/reopening for that challenge date.
- [ ] Preferences persist and unsupported capabilities degrade gracefully.

### FEAT-08 — History, activity views, and exports

**Gap:** Users have limited history exploration and cannot export their custom plans/external completion through a supported flow.

**Files:** authenticated history/export API, query indexes, website history views, compact extension entry points.

**Depends on:** SEC-01/04, DATA-02–07, FEAT-01/03.

**Implementation**

- [ ] Add paginated searchable solve history with date/platform/difficulty filters and clear known-history coverage.
- [ ] Add longer activity views/heatmap with unknown/incomplete days distinguished from verified zero days.
- [ ] Export only the authenticated account's data as documented JSON/CSV. Include plan versions, external completion, and provenance without tokens, password hashes, reset data, or other users' private records.
- [ ] Protect CSV consumers from formula injection; bound export jobs/size and use authenticated expiring downloads if needed.
- [ ] Provide a versioned plan/progress export format; add import only with strict validation, preview, and explicit conflict handling.

**Acceptance**

- [ ] Pagination/search does not omit or duplicate records within its documented snapshot rules.
- [ ] Exports contain only permitted account data and remain usable with non-ASCII/problem-title edge cases.
- [ ] History views do not imply that unobserved historical dates are confirmed empty.

### FEAT-09 — Explain LeetCode session requirements

**Gap:** Complete plan completion requires the matching LeetCode account signed in within the same browser, unlike the public-profile backend sync. This can surprise users.

**Files:** extension onboarding/progress/help, website explanatory copy and installation documentation.

**Depends on:** DATA-04, FEAT-03.

**Implementation**

- [x] Explain public profile sync versus complete browser-session plan history in concise product language.
- [x] Detect missing/mismatched LeetCode sessions and show an account-specific instruction/link; never request passwords or copy session cookies to the backend.
- [x] Resume automatic syncing when conditions become valid, preserving saved progress and avoiding repeated disruptive prompts.
- [x] Explain website limitations and how extension-synced account progress becomes available on the website after FEAT-01.

**Acceptance**

- [x] Signed-out and wrong-account users receive useful instructions rather than apparent zero progress.
- [x] A correct session triggers automatic sync without a manual checkbox or required history-sync button.
- [x] Messaging accurately states what is read and what remains local/account-backed.

### FEAT-10 — Direct friendships without groups

**Owner requirement:** Adding a friend must not require a group. Direct friendships belong to the authenticated account and persist in the backend across website/extension sessions.

**Files:** backend friendship models/migrations, schemas, authenticated friendship/search APIs, friends ranking/activity queries; friends UI and API clients in the extension and website.

**Depends on:** SEC-01/04, OPS-03 migration infrastructure, UI-05–07 for reliable friend views. Friend notifications remain deferred.

**Product decision pending:** Recommend mutual friend requests with accept/decline/cancel/remove actions, rather than silently adding another user to a mutual relationship. Decide this flow, discovery fields, and abuse/blocking behavior before implementation; the requirement for group-independent friends is already accepted.

**Implementation**

- [ ] Model direct friendship/request state with unique normalized account pairs, timestamps, actor identity, and transactional handling. Reject self-requests and handle duplicate/crossed requests idempotently.
- [ ] Provide authenticated discovery by public display name/coding handle without exposing emails, credentials, reset data, or private group membership. Bound/paginate searches and prevent request spam.
- [ ] Add the approved add/request, accept/decline, cancel, and remove flows in both clients, with pending/empty/error states and account-backed persistence. Do not require or silently create a group.
- [ ] Update Friends rankings and “What are my friends up to?” to include accepted direct friends. During migration, retain existing shared-group friends as a separately identified source unless the owner chooses to replace that behavior. Deduplicate users who are both direct and group friends.
- [ ] Keep direct friendship permissions separate from group membership: adding a friend never exposes a group's invite code, membership list, or private leaderboard. Profiles follow the accepted coding-profile rules; Global display preference does not alter friendship eligibility.
- [ ] Handle removal/account deletion and refresh/invalidate caches in both clients. One relationship source disappearing must not accidentally remove a remaining direct/shared-group relationship.
- [ ] Keep future alert eligibility hooks as backlog only; implementing friendship does not resume deferred friend notifications.

**Acceptance**

- [ ] Two registered users with no shared group can establish the approved direct relationship, then see each other in Friends rankings/activity.
- [ ] Relationships and pending state survive cache clearing and another device's sign-in; another account cannot approve/remove a relationship on their behalf.
- [ ] Shared-group plus direct friends appear once; removing a group membership leaves an independent direct friendship intact.
- [ ] Duplicate/crossed/self requests, decline/cancel/remove, search failures, and account deletion follow the approved flow without leaking private information.

## 9. Public repository cleanup and release plans

The public repository should present supported product code and reproducible development workflows. It should not expose personal testing details, abandoned attempts, private operations, or installed environments. Keep useful synthetic tests; remove personal data and obsolete experiments rather than hiding defects by deleting coverage.

Do not paste discovered sensitive values or identities into public issues, this plan, screenshots, PR descriptions, or commit messages. Use a private inventory with categories, affected locations, and remediation status. Removing current files does not remove historical copies.

### PUB-01 — Real test identities and personal details

**Problem:** Development notification code and scratch fixtures include personal names/handles, and scripts include machine-specific absolute paths. Other test emails/details may exist and require an inventory; their presence has not been exhaustively established.

**Files:** tracked source/docs/tests, `extension/public/background.js`, scratch files, fixtures, images, generated bundles.

**Depends on:** SEC-05; PUB-04 handles old commits.

**Implementation**

- [ ] Privately inventory test addresses, personal names/handles, local paths, phone/payment details, screenshots, user exports, and hardcoded sample accounts in tracked/releasable files.
- [ ] Replace examples with clearly fictional identities such as `Demo Coder` and `coder@example.com`. Use reserved example addresses, never a real inbox disguised as test data.
- [ ] Remove hardcoded personal notification demonstrations; use safe synthetic fixtures in isolated tests or a development-only preview.
- [x] Distinguish intentional public product contact/donation details from accidental personal data. Owner explicitly approved the donation QR/payment assets and controls remaining public on 2026-11-05; the illustrated username guide is synthetic.
- [ ] Check assets and generated output as well as readable source. Rebuild affected artifacts after cleanup.

**Acceptance**

- [ ] Current public source, documentation, fixtures, screenshots, and packages contain no unapproved real testing identities or private machine paths.
- [ ] Synthetic examples work without sending to a real inbox or accessing a friend's account.
- [ ] Historical locations are handed to PUB-04 without copying sensitive content into the public tracker.

### PUB-02 — Scratch scripts and abandoned experiments

**Problem:** Tracked `scratch/` scripts include one-off migration/notification attempts, and legacy assets/scripts may no longer belong to a supported workflow.

**Files:** `scratch/`, legacy entry points such as `extension/public/app.js`, old migration helpers, duplicate assets; references in docs/build tooling.

**Depends on:** OPS-07; coordinate with current migrations before removing helpers.

**Implementation**

- [ ] Classify each candidate as active product, supported operational tool, useful synthetic test, or obsolete experiment. Search references before removal.
- [ ] Move genuinely needed operational commands into a documented tooling directory with explicit environment selection, safe defaults, dry-run support where applicable, and no embedded identities/connection strings.
- [ ] Remove abandoned scripts and unreferenced assets from the public working tree. If preservation is useful, keep a private archive outside the public repository and release artifacts.
- [ ] Replace hardcoded machine paths with documented arguments/configuration in retained tools.
- [ ] Remove instructions that encourage manually inserting fake solves or mutating production users for demonstrations.

**Acceptance**

- [ ] Every retained script has an explained purpose and safe supported entry point.
- [ ] Clean builds and operational docs do not reference removed experiments.
- [ ] No unsupported attempt is accidentally shipped by wildcard asset-copying rules.

### PUB-03 — Secrets, configuration, logs, and screenshots

**Problem:** Public-source readiness requires checking more than `.env` ignore rules. Default admin credentials, debug output, screenshots, archives, and operational files can expose sensitive material.

**Files:** current tracked tree, configuration examples, CI workflows/logging, Docker context, documentation and assets.

**Depends on:** SEC-02–03, OPS-01–02, PUB-01.

**Implementation**

- [ ] Scan current tracked/releasable content for credentials, tokens, connection strings, private addresses, personal fixtures, database exports, and sensitive screenshots. Review findings privately; a scanner is not proof of absence.
- [ ] Keep an accurate `.env.example` with variable names and fictional local placeholders only. Include required production settings and explicit development flags without usable production defaults.
- [ ] Review logging/redaction, error responses, email provider errors, and export/debug routes. Do not log passwords, OTPs, authorization headers, or message/recipient dumps.
- [ ] Confirm ignore rules and Docker/package allowlists exclude actual environment files, local databases, installed environments, private exports, and debug assets.
- [ ] Rotate any exposed real credential through its provider before treating source deletion as remediation. Do not reproduce the credential in a cleanup commit.

**Acceptance**

- [ ] Reviewed findings have a disposition; exposed real credentials are rotated/revoked.
- [ ] Examples support setup without containing private account data.
- [ ] Logs, error output, build contexts, and packages pass the same privacy review as source.

### PUB-04 — Historical exposure and public Git history

**Problem:** Deleting today's test data does not remove it from prior commits, branches, tags, releases, PRs, or downloaded archives. Existing public copies may remain outside the owner's control.

**Files/surfaces:** Git history and refs, remote branches/tags, releases/assets, hosted downloads, CI artifacts, issues/PR attachments where accessible.

**Depends on:** PUB-01/03 inventory; credential rotation must precede publication cleanup.

**Implementation**

- [ ] Privately inspect reachable history/refs and published surfaces for the categories identified in PUB-01/03. Report locations and exposure classes, not raw sensitive values.
- [ ] Choose the least disruptive sufficient approach: ordinary cleanup for harmless clutter, targeted history sanitization for sensitive content, or a clean public release repository while retaining the original privately where appropriate.
- [x] Prepare a concrete history-remediation plan, private backup, affected refs, collaborator instructions, and verification procedure. Prepared privately; backup restoration/integrity verified.
- [ ] Obtain explicit approval of the reviewed proposal before rewriting shared history, force-pushing, removing public releases, or replacing a repository.
- [ ] Remove/update owned exposed release artifacts and request provider/cache remediation where applicable. Document that forks, clones, and third-party caches cannot be guaranteed erased.
- [ ] Re-scan the intended public refs/artifacts and record the outcome privately. Avoid promising that all historical traces are gone.

**Acceptance**

- [ ] The owner has reviewed the exposure inventory and selected the public-history strategy.
- [ ] Required credential rotations and owned-surface remediation are complete, with remaining external-copy limitations stated.
- [ ] The intended public refs/assets contain no known unresolved disallowed material; collaborators have safe migration instructions if history changed.

### PUB-05 — Clean extension packages and release artifacts

**Problem:** Builds copy public files broadly, and multiple ZIP copies can preserve obsolete code, test messages, or unnecessary assets even after source cleanup.

**Files:** extension build/package scripts, `public/`, generated bundle directories, all served ZIP copies, backend download routing.

**Depends on:** PUB-01–03, OPS-05/07. UI-03 is deferred; packaging must exclude or secure obsolete unsafe notification assets without requiring the friend-alert feature to be rebuilt.

**Implementation**

- [ ] Build into a clean staging directory from an explicit release asset list. Do not include every historical public file by default.
- [ ] Exclude scratch tools, personal demonstrations, environment files, databases, debug pages, unintended source maps, and duplicate obsolete assets.
- [ ] Verify `manifest.json` is at the ZIP root, all manifest/HTML references resolve, and version/compatibility metadata matches the release record.
- [ ] Produce one archive and mirror it to required destinations; record/check hashes. Inspect archive entries and decoded text as well as source files.
- [ ] Confirm that the hosted download points to the reviewed artifact during an authorized release; replace/remove obsolete owned artifacts through the approved release process.

**Acceptance**

- [ ] Archive contents contain only intended runtime assets and no unapproved identity/configuration data.
- [ ] Required ZIP copies are byte-identical, installable, and correspond to the recorded source/version.
- [ ] When released, the downloaded public artifact matches the reviewed checksum.

### PUB-06 — Public documentation and contributor experience

**Problem:** Current docs combine product descriptions, historical assumptions, and development/release notes; some claims no longer match implementation.

**Files:** `README.md`, `context.md`, `SECURITY.md`, `PRIVACY.md`, `TERMS.md`, extension/backend feature docs, contribution/environment setup docs.

**Depends on:** Relevant fixed behavior, OPS-05/07, PUB-01–03.

**Implementation**

- [ ] Write a concise architecture/setup guide and clearly separate user installation, local development, testing, migrations, and release procedures.
- [ ] State supported browsers/distribution channels and actual automatic-update behavior; remove unsupported claims.
- [ ] Update scoring bases/formulas, data provenance, history limitations, plan storage, browser-session requirements, visibility, and retention descriptions to match the implemented product.
- [ ] Replace personal walkthroughs and obsolete attempts with fictional examples and reproducible commands using arguments/configuration.
- [ ] Review the existing license, third-party dataset/asset attribution, contribution instructions, and private security-reporting path. Keep intentional public contact details distinct from private test addresses.
- [ ] Add a link to this tracker without claiming pending work is complete. Retain an accurate changelog rather than publishing raw personal experiments.

**Acceptance**

- [ ] A new contributor can understand and set up the supported product without private context or credentials.
- [ ] Public claims match actual features, limits, and release behavior.
- [ ] No private operational details or personal testing instructions are required to follow the docs.

### PUB-07 — Final clean-clone and public-release gate

**Problem:** A clean working tree alone does not establish that the public repository and shipped product are clean and reproducible.

**Files/surfaces:** intended public repository/ref, CI, release artifacts, deployment metadata and documentation.

**Depends on:** PUB-01–06, applicable P0/P1 fixes, OPS-06. Optional product enhancements may remain visibly deferred.

**Implementation**

- [ ] Start from a fresh clone/export of the intended public ref, without local databases, cached build output, private environment settings, or a preinstalled virtual environment.
- [ ] Follow public setup instructions, run the authorized checks/builds with synthetic data, and inspect the resulting source/package/Docker contexts.
- [ ] Confirm public refs/history decisions, required attribution, release versions, secret hygiene, and absence of personal test material.
- [ ] Record remaining known limitations, deferred features, backend/client compatibility, rollback procedure, and the final reviewed revision/checksums.
- [ ] Complete the separately authorized release. Verify status and public read-only flows without opening the Render debugger or sending test emails to real recipients.

**Acceptance**

- [ ] Clean-clone setup and relevant checks succeed using only documented dependencies and fictional/local configuration.
- [ ] The source and generated deliverables meet the public privacy/cleanup checklist.
- [ ] Release state is recorded accurately as local-only, branch-pushed, or deployed-and-verified; unresolved blockers remain unchecked.

## 10. Verification and completion record

For each item, record the following when work begins/completes. Do not place real secrets, test addresses, or production payloads in this log.

| Item | State | Implementation commit/PR | Verification evidence | Release state | Remaining work |
|---|---|---|---|---|---|
| M1-01 | Awaiting release | `f90fb47` | 7 synthetic auth/configuration tests passed | pre-launch | Production key configuration and coordinated release pending |
| M1-02 | Passed locally; awaiting release | `f200400` | 17 backend + 3 client session + 11 progress tests; type checks/builds passed | pre-launch | Session revocation follows M1-05; owner-transfer UI follows M1-06 |

### Shared definition of done

- The item's implementation and acceptance checkboxes are satisfied, or any deliberate scope change is recorded and approved where necessary.
- Applicable regression coverage and authorized verification results are recorded.
- Data/schema changes have a migration, recovery path, and evidence that unrelated platform/account data is preserved.
- Both affected clients handle API compatibility, loading, empty, offline, and failure states.
- Source, logs, fixtures, screenshots, packages, and documentation contain no unapproved private/test identities or secrets.
- Extension packages or website output are rebuilt only when their corresponding application changes require it.
- Required deployment verification is complete, or the item remains explicitly awaiting release.
- The master checkbox is updated, and any new follow-up has a distinct ID rather than being silently forgotten.

M1-03 (`f9f07a3`) evidence: 22 backend tests passed using synthetic users and a temporary database; no emails or production jobs were sent. Administrative configuration/release remains pending.

## 11. Coverage map back to the review

| Review finding or request | Tracking IDs |
|---|---|
| Client-supplied identities and group permissions | SEC-01 |
| Exposed admin actions and default/bypassable admin secret | SEC-02 |
| Password/OTP abuse, identity disclosure, old sessions | SEC-03 |
| Clarified Global display-only setting, accessible coding profiles, and private-group permissions | SEC-04 |
| Fabricated test profiles | SEC-05 |
| Old history retained after LeetCode handle change | DATA-01 |
| Repeated accepted submissions inflate counts | DATA-02 |
| Submission calendars treated as solved questions | DATA-03 |
| Only 20 recent backend acceptances; missing older evidence | DATA-04 |
| Estimated historical points and mutable awards | DATA-05 |
| UTC/IST/challenge-date mismatch | DATA-06 |
| Calculation/breakdown rounding mismatch | DATA-07 |
| Previously solved daily challenges | DATA-08 |
| First-solve-only streak, no duplicate question entries, and 2-point revision eligibility after a week | DATA-02–03, DATA-09 |
| Three incompatible account storage keys | UI-01 |
| Isolated-world fetch interception | UI-02 |
| Inline notification script blocked | UI-03 |
| Latest-global-only alerts, friend scope, wrong platform label | UI-04 |
| Stale requests and missing sort cache keys | UI-05 |
| Failed friend requests appear empty | UI-06 |
| Old ledger entries overwrite newer friend activity | UI-07 |
| Email claims success when unsent | OPS-01 |
| Ephemeral signing keys | OPS-02 |
| Expensive startup and scattered migration work | OPS-03 |
| Process-local scheduling/locking/rate limits | OPS-04 |
| Stale versions and incomplete update flow | OPS-05 |
| Narrow automated coverage | OPS-06 |
| Tracked environments and duplicated generated outputs | OPS-07 |
| Cross-device plans/preferences | FEAT-01 |
| Website Progress | FEAT-02 |
| Clear provider sync/completeness status | FEAT-03 |
| Coding-account ownership/claim recovery | FEAT-04 |
| Disconnect Codeforces | FEAT-05 |
| Weekly/monthly points rankings | FEAT-06 |
| Notification controls | FEAT-07 |
| Searchable history, activity views, exports | FEAT-08 |
| Explain full-history browser-session requirement | FEAT-09 |
| Add friends without requiring shared groups | FEAT-10 |
| Clean public source without personal testing details/attempts | PUB-01–07, SEC-05, OPS-07 |

## 12. Plan change log

| Date | Change |
|---|---|
| 2026-11-05 | Created the 43-item implementation tracker from the repository review. Added the requested public-source cleanup, historical-exposure assessment, artifact inspection, and final public-release gate. No application fixes performed by this document change. |
| 2026-11-05 | Owner clarified that everyone participates in Global rankings; the signup/settings toggle only shows/hides Global on their own homepage/dashboard. Accessible profiles expose coding stats regardless of this toggle. Replaced the earlier privacy-opt-out proposal throughout SEC-04 and related notification/ranking tasks. Recorded acceptance of the other M1 decisions on groups, password reset, test emails, and history cleanup. No application code changed. |
| 2026-11-05 | Recorded owner evaluation: first-time accepted questions alone qualify for streaks; one entry per question; revision repeats after at least a week may earn 2 points; all product boundaries use IST; formula changes revalue past base awards for everyone while retaining earned daily amounts; imported new-user history gets base points only; proven renames retain history and different accounts are recalculated. Added DATA-09 (44 total items), deferred UI-03/UI-04/FEAT-07, and recorded the main-then-pre-launch branch sequence with labeled per-step commits/pushes. Ambiguous cooldown/daily details remain open. Documentation only. |
| 2026-11-05 | Confirmed mandatory backend persistence/sync for user plans, follows/removals, imported definitions, and external completion; local storage serves only as cache/outbox. Added cache-clear/reinstall and cross-account acceptance checks. No application or Git branch operations performed. |
| 2026-11-05 | Added owner-requested FEAT-10 for backend-persisted direct friendships independent of groups (45 total items). Mutual-request/discovery details remain pending. Owner separately authorized merging progress-bar into main and testing the Codeforces integration; pre-launch milestone implementation remains on hold. |

M1-09 local acceptance: isolated PostgreSQL 16 exercised migration concurrency and transactional recovery. Browser checks exposed and now cover a website password-change bug where a session token was written through account-scoped dashboard storage. Both client flows pass with intercepted local APIs and mocked providers; no production accounts or emails were used. Credential invalidation is owner-confirmed, not tested using exposed passwords.
