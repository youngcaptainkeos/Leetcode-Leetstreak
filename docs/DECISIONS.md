# LeetStreak decisions before implementation scheduling

Date: 2026-11-05  
Companion tracker: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)

## Status and purpose

The accepted M1 decisions in the implementation plan remain authoritative: everyone participates in Global rankings; the toggle only shows/hides that view on their own homepage; accessible profiles expose coding stats; group ownership is enforced; password reset revokes sessions; production test-email functionality is removed; shared-history remediation requires review of a concrete plan first.

D05–D11, D13, D16, and D23 now contain the owner's accepted rules or explicitly identified remaining details. Other recommendations remain pending unless already accepted in M1. D30 records additional revision-rule clarifications still needed. Accepting a rule does not authorize implementation during this documentation-only turn.

**Execution status:** The integration merge and deployment completed at `269e06f`. The owner has now authorized starting milestone implementation on `pre-launch`, with checks, a clearly labeled commit/push, and a progress notification after each successful step. Production deployment of milestone fixes remains a separate checkpoint. Outstanding product decisions are not inferred from permission to start independent work; shared-history rewriting still requires a concrete reviewed proposal.

The purpose is to settle product behavior and execution constraints across all milestones. Technical details such as schema/index design, request cancellation, safe escaping, transactional writes, and cache keys can be resolved during implementation against these decisions. No milestone is marked complete by accepting its design.

## M1 — Access, security, and public exposure

| ID | Decision | Accepted rule / recommendation | Effect / tradeoff | Related tasks |
|---|---|---|---|---|
| D01 | Existing sessions after the security release | Require one fresh sign-in for sessions that cannot satisfy the new authenticated API. Preserve account data, plans, and preferences. Valid compatible tokens can continue. | Old extension versions may require updating. No permanent insecure compatibility fallback. | SEC-01, OPS-02, OPS-05 |
| D02 | Who may view coding profiles? | Signed-in users may view coding profiles reachable from authorized rankings/activity; no new anonymous public profile pages in this release. Global display off never hides an account or profile. | Coding stats are social; email, account settings, credentials, reset data, and private-group internals remain restricted. If anonymous profile links are wanted, specify that separately. | SEC-01, SEC-04 |
| D03 | Owner deletes their account while still owning groups | Offer ownership transfer or group deletion before account deletion. Do not silently leave ownerless groups. | Requires a short extra step for owners; ordinary members can delete their accounts normally. | SEC-01, SEC-04 |
| D04 | Intentional public identity/contact assets | Remove personal development/test details by default. The owner explicitly approved keeping the donation QR/payment asset, donation controls and existing public support contacts public on 2026-11-05. Retain only owner-approved public support/contact/donation information; replace screenshots with synthetic accounts where needed. | A genuine product contact address is different from a private test inbox. No personal information is pasted into this public document to make the decision. | PUB-01, PUB-03 |

**Already agreed:** stronger rules apply to newly created/reset passwords; existing passwords still work until changed. Implementation will select and document concrete validation/abuse limits against current primary guidance. Administrative operations need authentication, not a new admin dashboard. Historical Git cleanup is assessed before any destructive action. On 2026-11-05 the owner approved preparing a targeted rewrite privately. Publication remains held until exposed database credentials are confirmed revoked/rotated or their accounts deleted, and the final ref changes are reviewed.

## M2 — What activity and points mean

| ID | Decision | Recommended default | Effect / tradeoff | Related tasks |
|---|---|---|---|---|
| D05 | What maintains the streak? | **Accepted:** Only the first accepted solve of a previously unsolved question on either platform contributes. Failed attempts, repeats, revisions, manual checks, and import time do not. | “First” means first accepted solve, not that the first submission attempt must succeed. Unknown historical first-solve dates cannot be fabricated. | DATA-02–03, DATA-06 |
| D06 | Re-solving and question entries | **Accepted:** Every platform question has one LeetStreak question entry regardless of submissions. An accepted repeat after at least one week can earn 2 extra revision points, but never another base award, unique question, or streak day. | Separate revision evidence/awards from the unique-question ledger. Recurring eligibility is seven days since first solve/last rewarded revision, with the streak multiplier applied to the 2-point base. Daily limits/stacking remain under D30. | DATA-02–03, DATA-09 |
| D07 | Time boundaries | **Accepted:** All product boundaries and displayed activity dates use IST: daily, weekly, monthly, streak, revision, and daily awards. UTC can remain the internal instant format. | Sunday remains the earlier week-start recommendation, not a new confirmed choice. Provider publication must map to a defined IST-day question; its UTC reset must not silently control LeetStreak days. | DATA-06, FEAT-06 |
| D08 | Historical score fairness | **Accepted:** Approved base-formula changes also recalculate past questions for all users. Existing users must not stay on a frozen base scale while new users receive a different one. Retain earned daily award amounts separately. | Missing old question identities/inputs still need a consistent disclosed reconstruction/fallback policy. Do not guess old daily completions or erase retained bonuses. | DATA-04–05, DATA-08 |
| D09 | Daily bonus retention and new-user history | **Accepted:** Preserve previously earned daily points through base recalculation. New-user imported questions receive base-only credit, never retrospective daily bonuses. | **Accepted clarification:** New users may earn daily bonuses on future live solves. Repeated-daily eligibility and within-day award limits remain pending. | DATA-08, DATA-07/09 |
| D10 | Formula changes and award components | **Accepted:** Version/audit formula changes and apply new bases consistently across all prior questions/users while retaining earned daily components. Add revision credit separately. | No base calibration change is requested by this plan edit. Base, retained daily, and revision points must be separable; old acceptance/rating evidence may be incomplete. | DATA-05–09 |
| D11 | Replacing or renaming a coding account | **Accepted:** A completely different/wrong linked account must be recalculated for the new account. A proven rename of the same account retains history. Preserve the other platform. | Investigate stable provider identity/ownership proof. Do not treat a similar name/avatar as proof or destructively replace history when identity is ambiguous. | DATA-01, FEAT-04–05 |

**Important doubts:** solved-question lists do not establish every historical first-accepted timestamp or repeated acceptance. Investigate evidence for new-solve streaks, fair historical base reconstruction, and revision eligibility. Keep stored earned daily components intact; do not rely on complete past daily archives to recreate them. Resolve the future new-user daily rule and which provider question is assigned to each IST day before implementing bonuses.

| ID | Clarification | Known rule | Remaining choices | Related tasks |
|---|---|---|---|---|
| D30 | Revision reward details | Accepted repeat after at least one week can earn 2 extra points; one question entry; no streak extension. | Confirmed: recurring cooldown of seven days since first solve or last rewarded revision; unrewarded attempts do not reset it. Confirmed: the streak multiplier applies to the 2-point revision base. Pending: whether a revision can stack with a daily bonus and the daily award limit. | DATA-09 |

## M3 — Notifications and everyday extension behavior

| ID | Decision | Recommended default | Effect / tradeoff | Related tasks |
|---|---|---|---|---|
| D12 | Daily reminder | Keep the inline reminder below the extension name/header. It pushes content down, can be dismissed for that IST challenge day, and stays dismissed after reopening. | Automatic checking remains; no intrusive modal or required manual sync-history button. Separate this feature from deferred friend notifications; resolve IST question assignment in D07 first. | DATA-06/08, FEAT-09 |
| D13 | Friend solve notifications | **Deferred by owner:** The feature has never worked reliably; keep repair/preferences in the backlog for later. | Do not spend current work deciding delivery modes, quiet hours, sound, or popup behavior. UI-03/UI-04/FEAT-07 are deferred. Inline daily reminders and friends activity remain in scope. | UI-03–04, FEAT-07 |
| D14 | Friends activity meaning | Pending recommendation: show the latest accepted activity within one entry per friend/platform/question, updating that entry's timestamp rather than duplicating a question for every submission. | Any revision label must be backed by DATA-09 evidence. Feed activity and revision points do not extend first-solve-only streaks. | UI-06–07 |
| D15 | Offline/provider failure behavior | Preserve the last successful data with a clear stale/partial/error state, then retry automatically with backoff. Never describe a failed lookup as no solves or a successful sync. | Old data stays useful, but its age is visible. Sync timing is a best-effort target subject to provider availability. | UI-05–07, FEAT-03 |

**Already required:** friends activity stays above playlists; question visibility and expanded sections persist; all plans can be collapsed; the existing typography/theme stays consistent. D13 defers friend alerts only, not D12's inline daily reminder.

## M4 — Plans, website parity, and linked accounts

| ID | Decision | Recommended default | Effect / tradeoff | Related tasks |
|---|---|---|---|---|
| D16 | Backend account plan storage | **Accepted:** User plans must be persisted/synced in the backend, not only locally. Persist imported definitions, library membership, follows/removals, and external completion by authenticated account. Local storage is cache/outbox only. | Cache clearing/reinstall must recover server-confirmed plans. Website/extension sessions use the same account data. View/startup preference sync remains the proposed extension to this requirement; friend-alert preference work is deferred. | FEAT-01–02 |
| D17 | Defaults and empty libraries | Keep Striver's A2Z, SQL 50, and Interview 150 as the three starters. Respect intentional removals, including zero plans. Offer restoration without automatically re-adding them. | Preserves accepted behavior for new and existing users; imports/removals must not reset solved history. | FEAT-01–02 |
| D18 | Plan import scope for the website | Website supports curated/provider-backed plans and pasted question links first. Retain extension public-page scanning where supported. Do not add unrestricted server scraping in the first parity release. | Website parity cannot include every extension-only host-permission capability immediately. Unsupported pages get clear alternatives. | FEAT-02 |
| D19 | Conflicting offline edits | Merge different plans/items. A stale conflicting edit to the same item's completion or plan removal must be detected and resolved rather than silently resurrecting removed plans or overwriting newer edits. | Most syncing is automatic; a rare explicit conflict choice is preferable to losing progress. Technical revision handling can be selected during implementation. | FEAT-01 |
| D20 | Coding-account ownership verification | Keep linking/signup usable while verification is optional initially. All users continue participating in Global rankings. Label verified/self-declared ownership honestly; add a recovery path for incorrectly claimed handles. | Verification must not create an unapproved participation exclusion or retroactively lock out existing users. Proof mechanisms require provider feasibility research. | FEAT-04 |
| D21 | Disconnect Codeforces | After confirmation, remove its contribution from the active account's points, activity, and automatic plan completion; preserve LeetCode and external manual items. Cancel pending imports and release the handle claim. | The warning must explain possible streak/score changes. No second base credit on relinking; backend reconciliation determines the correct current contribution. | FEAT-05 |

**Technical work to resolve:** account-scoped cache migration, bounded plan storage, revision conflict handling, deletion/unlink retention, and separating client-observed progress from trusted score evidence. Choose minimal private audit retention only after documenting its purpose and deletion behavior; never put retained personal data in the repository.

## M5 — Releases, operations, and clean public code

| ID | Decision | Recommended default | Effect / tradeoff | Related tasks |
|---|---|---|---|---|
| D22 | Verification during implementation | Authorize isolated automated tests, type checks, builds, and synthetic browser checks for each milestone. No real test-email sends or production-account mutations. | Makes “complete” evidence-based and permits regression coverage while fixing each issue. This is pending the user's approval; checks are not authorized solely by writing this proposal. | OPS-06, PUB-07 |
| D23 | Branch and per-step commit workflow | **Accepted:** Integration is merged into `main`; milestone implementation is authorized on `pre-launch` created from `269e06f`. Commit each completed step with milestone/task/step labels and push to `origin/pre-launch`. | The owner now authorizes pre-launch work and step-by-step progress notifications. Production merges/deployments remain explicit checkpoints. Record commits/evidence in the tracker. | All milestones, OPS-05 |
| D24 | Public repository history | Audit first. Prefer preserving a sanitized history if practical; if exposure/clutter warrants a clean public repository, present that option with consequences before choosing. Rotate exposed secrets regardless. | Ordinary deletion does not clean past commits. Shared history rewrites and replacement repositories still require concrete approval. | PUB-01–04 |
| D25 | Browser distribution and operating cost | Keep the current Chrome-compatible manually installed ZIP channel and existing hosting budget initially. Make release/version/update messaging truthful. Propose store publishing, new paid services, or additional infrastructure separately. | No unsupported automatic-update claim or promise of tested Safari/Firefox parity. Scaling work should fit existing resources where feasible; infrastructure needs may affect estimates. | OPS-03–05/07, PUB-05–07 |

**Already agreed:** remove personal testing details and obsolete attempts; use synthetic fixtures; retain protected release announcements; remove production test-email functionality. Current-tree cleanup and historical cleanup remain distinct tasks. Installed virtual environments do not belong in the tracked public tree.

## M6 — Period rankings and history tools

| ID | Decision | Recommended default | Effect / tradeoff | Related tasks |
|---|---|---|---|---|
| D26 | Ranking periods/default | Offer All time, This week, and This month in Global, Friends, and groups. Keep All time as the initial default and remember the user's last selection. | New users get meaningful short-period comparisons without replacing the existing lifetime view. The Global display choice still affects only their own UI. | FEAT-06 |
| D27 | Period score eligibility | Pending recommendation: use IST accepted/award dates, not import time. Attribute revalued base points to their original known first-solve period; retain daily/revision awards on their own earned dates. Exclude undated estimates from period rankings. | Linking history cannot create a false new-work spike. All eligible users' historical bases change under the same approved formula, with earned daily components retained under D08–D10. | DATA-05–09, FEAT-06 |
| D28 | History/export scope | Searchable, paginated history and longer activity views on the website, with compact extension entry points. Export own history as CSV and plans/progress as versioned JSON. No arbitrary full-account restore/import in the initial release. | Explicitly label incomplete older history; exports exclude private credentials and other users' account data. | FEAT-08 |
| D29 | Completion and scheduling scope | Tracker now has 45 items including DATA-09 and direct friendships FEAT-10. UI-03, UI-04, and FEAT-07 remain deferred. Plan the remaining 42 items after integration/main/pre-launch prerequisites and unresolved policy choices. | Keep deferred items unchecked and distinguish integration release work from planned milestone fixes. | All milestones |

## Additional accepted requirement — direct friends

Users must be able to add friends without a shared group, with backend persistence and website/extension support. This adds FEAT-10 to M4; groups remain separately usable. Friend notifications stay deferred.

| ID | Decision | Recommendation / confirmed scope | Remaining choice | Related tasks |
|---|---|---|---|---|
| D31 | Direct friendship flow | Group-independent friendships are accepted. Recommend mutual requests with accept/decline/cancel/remove, discovery by public coding handle/name, and deduplicated Friends views across direct/group sources. | Request/accept vs one-way follow, discovery fields, and abuse/blocking details need confirmation. Do not silently declare the recommended workflow accepted. | FEAT-10, SEC-01/04, UI-06–07 |

## Investigations before committing to a final schedule

These are not questions the owner needs to guess. Resolve them through read-only investigation or isolated experiments once that work is authorized. Do not paste findings containing private values into public docs.

| Investigation | Why it matters | Scheduling outcome |
|---|---|---|
| Provider history coverage | Determine retrievable LC accepted identities/timestamps, repeated-acceptance evidence, pagination/gaps, retained daily award amounts, and data already retained. | Bound first-solve/revision evidence and fair all-user base revaluation without inventing old daily bonuses; scope DATA-02–09. |
| Existing-data impact | Privately inspect schema/version/aggregate completeness and prepare representative synthetic migrations; production data access is a separate authorization boundary. | Identify migration/repair effort without testing on real users. |
| Ownership proof and rename identity | Check supported LC/CF proof options, stable identifiers, and rename behavior before selecting an ownership/rename flow. | Preserve history for proven same-account renames and recalculate genuinely different accounts without guessing identity. |
| IST challenge mapping | Establish provider publication behavior and propose a stable question assignment for each LeetStreak IST day. | All product boundaries remain IST; no unapproved UTC reset exception. |
| Hosting configuration and compatibility | Check configuration names/presence without exposing values, deployed API compatibility, supported client versions, and recoverable backups where access is authorized. | Establish safe release ordering, required sign-in/update behavior, and whether any hosting change is necessary. |
| Public exposure inventory | Inspect current/history/artifacts for personal test data, genuine credentials, abandoned files, and owned release copies. | Choose ordinary cleanup vs approved history work; keep external clone/cache limitations explicit. |
| Reproducible build/distribution | Confirm what source/assets are required, ZIP consumers, install path, and supported browser behavior. | Scope cleanup and release automation; avoid deleting active runtime files. |

## Suggested decision process

1. Preserve the accepted D05–D11 rules; resolve D30, future new-user/repeated-daily eligibility, IST challenge assignment, and incomplete-history fallback before scheduling their implementation.
2. Review D01–D04 and D12–D21 for access, notifications, and account/plan behavior.
3. Review D22–D29 for authorized checks, release checkpoints, distribution, and final scope.
4. Record answers below and mirror accepted changes into the implementation tracker. No inferred approval from silence.
5. Keep the execution hold: current integration first, then authorized merge to `main`, then `pre-launch`. Once requested, complete bounded investigations and estimate the non-deferred work with contingency. Friend-alert work remains backlog.

Approval shorthand is fine: “Approve the recommendations except Dxx: …”. It accepts the stated defaults only; the explicit restrictions on production mutations, spending, deployment checkpoints, and shared-history rewriting still apply.

## Decision log

| IDs | State | User decision / clarification | Date |
|---|---|---|---|
| D05–D06 | Accepted core rules | First accepted unique questions alone maintain streaks; all submissions share one question entry; eligible repeats after at least a week may earn 2 revision points. D30 details remain open. | 2026-11-05 |
| D07 | Accepted timezone | All product boundaries use IST. Week-start choice and IST question assignment need explicit treatment before implementation. | 2026-11-05 |
| D08–D10 | Accepted core rules; partial clarification pending | Revalue prior base points for all users when the formula changes; preserve earned daily awards; historical new-user imports get base-only credit. Future new-user daily eligibility is confirmed; repeated daily awards remain open. | 2026-11-05 |
| D11 | Accepted | Recalculate for different accounts; preserve history for proven same-account renames. Proof feasibility needs investigation. | 2026-11-05 |
| D13 | Deferred | Friend notifications and their preferences are retained as backlog, not current implementation. | 2026-11-05 |
| D16 | Accepted backend requirement | Persist/sync user plans in the backend; local-only storage is insufficient. Related optional view/preference details remain pending. | 2026-11-05 |
| D23 | Accepted workflow; not executed | Current integration to main first, then pre-launch; labeled commit/push after each completed step when implementation starts. | 2026-11-05 |
| D30 | Cooldown accepted; arithmetic clarification pending | Recurring seven-day first-solve/last-reward cooldown; unrewarded attempts do not reset it. Multiplier and daily stacking remain open. | 2026-11-05 |
| Other recommendations | Pending unless previously accepted in M1 | No blanket approval inferred; retain the earlier accepted M1 rules. | 2026-11-05 |
| D31 | Requirement accepted; flow pending | Direct friends must not require a shared group. Detailed relationship/discovery workflow remains a proposal. | 2026-11-05 |

## Change log

| Date | Change |
|---|---|
| 2026-11-05 | Prepared decisions across all six milestones, separated existing accepted M1 requirements from pending proposals, and listed feasibility investigations needed for responsible scheduling. No application code changed. |
| 2026-11-05 | Replaced superseded M2 recommendations with the owner's first-solve streak, revision, IST, base-revaluation, daily-retention, and rename requirements. Deferred friend alerts, recorded the main-then-pre-launch workflow, and added D30 for unresolved revision details. Added mandatory backend plan persistence after owner clarification. Documentation only; no implementation/branch/commit/push/deployment performed. |
| 2026-11-05 | Added FEAT-10/D31 for group-independent direct friendships. Recorded new authorization to merge current integration into main and test Codeforces; later pre-launch fixes remain on hold. |

| 2026-11-05 | Owner authorized milestone implementation on pre-launch with a labeled commit/push and notification after every successful step. M1-01 passed seven synthetic authentication/configuration checks; no production changes. |

| 2026-11-05 | Owner confirmed recurring revision rewards seven days after first solve/last rewarded revision; unrewarded attempts do not restart the clock. No M2 scoring implementation performed yet. |

### Additional owner confirmations — 2026-11-05

- New users may earn daily bonuses on future live solves; imported historical solves receive base points only.
- Eligible recurring revisions apply the streak multiplier to their 2-point base. Revision/daily stacking remains open.
- Daily reminders and eligibility follow the current official challenge even if it changes within an IST day; product day boundaries remain IST.
- Owner confirmed the exposed legacy Render credentials revoked; Supabase password was regenerated and the primary service database reads passed after redeployment. The old passwords were not probed. Public history publication and production release checkpoints remain separate.
