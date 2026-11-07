# Accepted-submission evidence — rebuild R2

## Implemented boundary

Both production sync functions now record provider acceptances in
`accepted_submissions`, separately from the one-question `solves` rows.
Codeforces retains every eligible individual, final accepted submission in the
scanned pages, including repeated acceptances and overlapping-page deduplication.
Failed, pending, pretest-only, team, ghost and other-account submissions do not
enter that evidence set. If a submission changes during page overlap, the scan
fails instead of being treated as a complete snapshot. Malformed/unsupported
problem identities also fail the scan rather than silently erasing saved history.

LeetCode recent-AC query availability is explicit. An unavailable response is
not successful empty history and does not advance the LC sync checkpoint.
Calendar activity is not accepted-event evidence.

Before writing a batch, sync validates the captured provider handle, account
generation and prior successful-sync checkpoint again under the account lock.
Handle changes increment the relevant generation, preventing an old request
from being accepted after a handle changes away and back. Metadata requests are
performed before acquiring the account write lock. This is not distributed job
coordination: OPS-04 still owns provider leases and shared rate limits.

Each event has a provider submission ID, platform, generation, observed instant
and accepted instant. Replay with conflicting identity/time is rejected. A batch
uses a savepoint inside the caller's transaction; failed batches and caller
rollbacks cannot retain partial events. Existing question rows are linked;
the evidence writer never creates another question row or awards points.
The immutable pre-reconciliation baseline is captured before runtime ingestion
changes existing account history.

## First-solve proof

- A completed public Codeforces history scan can establish the earliest final
  acceptance among the supported public submissions it returns. It is not a
  claim about inaccessible/private submissions or an immutable provider snapshot.
- An incremental CF window cannot establish a first date for a newly discovered
  question. A later full scan can improve the proof.
- LeetCode's recent accepted list proves acceptance only. It cannot establish a
  historical first solve, even for a question absent from LeetStreak's local rows.
- Replaying a recent window does not downgrade an existing full-scan proof.
- A full scan finding an earlier acceptance updates the first-date marker and
  leaves exactly one first-proof event for that question/generation.
- If CF rejudgement removes an unawarded question, its raw observations remain
  detached from the deleted question. Credited questions missing from the public scan remain as flagged, unproved
  history; absence alone does not prove a revoked acceptance. R3 continues
  syncing other questions and restores first-date proof if a full scan later
  returns the question.

## Revision awards — R3 integration

`revision_candidates` plans eligible rewards; runtime reconciliation applies
those proposals under the account lock using unique event-based award keys.
Amounts use `2 × streak multiplier`, never add a question or streak day, and
are retained exactly through later base revaluation. Imports without a prior
successful-sync boundary receive no retrospective revisions. Unrewarded attempts
do not restart the recurring seven-day cooldown. Unknown prior reward dates
block eligibility instead of guessing. Native PostgreSQL checks exercise
concurrent reconciliation of the same accepted event.

Both provider sync functions now call the same component reconciler. Score
breakdowns read stored components without provider requests or write side
effects. Both clients display base, daily, revision and protected legacy credit,
plus incomplete-history notices. Calendar attempts are stored separately in
`provider_calendar` with provider source and partial-coverage metadata. Streaks
and period solve counts derive only from proved unique first solves.

## Protected history and incomplete metadata

Base amounts revalue under the current formula. Explicit daily/revision awards
retain their credited amounts and dates. A legacy daily row without a reliable
component split keeps its combined total as protected credit and is flagged for
review, rather than reconstructing a +5 bonus. Unknown question metadata never
defaults to Medium. Existing credit is retained provisionally; once valid
metadata arrives, a temporary metadata credit can be replaced by its current
base. Protected uncertain daily totals remain protected.

`account_credits` records base-only historical estimates separately from question
awards, with inputs and unknown-date labels. Classified named questions consume
one slot from their category. Already-credited unclassified questions reserve
remaining slots conservatively (Hard, then Medium, then Easy), preventing the
confirmed aggregate/per-question overlap. A zero-credit unknown question can be
covered by an anonymous estimate until metadata resolves it. These estimates
never establish streak days, dated rankings or retrospective bonuses.

Different coding handles replace that platform's history, account credit,
evidence and awards; the other platform stays intact. Private immutable
transition snapshots are captured first, and generation checks reject stale
requests. Case-only changes retain history. Provider-backed proof of other
same-account renames remains FEAT-04 work; similarity is not identity proof.

## Remaining release gates

- Public LC recent acceptances still cannot prove a historical or live first
  solve. Stronger LC first-solve evidence and future live daily issuance remain
  open DATA-03/04/08 work. Imported history receives no daily bonus; existing
  earned credit is retained. No retrospective archive-based bonus is inferred.
- The all-account, bounded/resumable reconciliation job and release-wide formula
  rollout remain OPS-03/DATA-05 gates. Runtime sync revalues one account at a time;
  startup and profile reads do not silently rewrite all accounts.
- More complete history coverage/status, provider ownership/rename proof,
  backend plan persistence and distributed job coordination remain their planned
  milestones. An omitted public CF question is flagged, not declared definitely
  unsolved or automatically stripped of retained awards.
- Browser checks cover the local website and popup preview, not a natively
  installed extension or production deployment. Build/package checks are local.

All provider checks use mocked responses and database checks use synthetic
accounts in disposable local databases. No real provider account or production
database is mutated by the rebuild checkpoints.

## Deployed streak compatibility recovery — 2026-11-07

`platforms.streak_dates` now supplies dashboard/profile and all leaderboard
display streaks separately from `daily_counts`. The owner approved restoring
the historical activity-based display while complete first-solve verification
is unavailable. Legacy rows are used only for initial linked generations;
provider calendars must match the current account generation. Dates are
unioned, positive activity is required, and future dates are ignored. The
existing IST today/yesterday grace rule remains.

No historical solve is promoted to verified, and no rows, point awards or
scoring multipliers are rewritten. Verified question counts remain strict.
Activity calendars can contain repeats/failed attempts, so this is temporary
display compatibility, not completion of the intended first-solve streak
policy. Updating the submitted extension's strict-streak Help wording is a
follow-up client release task; the backend repair requires no extension ZIP.


### Profile activity chart recovery — 2026-11-07

- Removed profile history/reconciliation notices from extension and website overview; detailed explanations remain in Help.
- Dashboard `last_7_days` is display activity: verified first solves, original-generation legacy activity and matching-generation LeetCode calendar observations. Overlapping sources use the maximum per platform/day; platforms are summed. Calendar activity may include repeats/attempts.
- Today/Week/Month counters still use verified first solves. No score components or scoring streak evidence are changed.
- Rebuilt extension and website bundles. No test suite run for this UI request.


### Sync failure handling — 2026-11-07

- Catch LeetCode transport/HTTP failures before sync mutation; manual sync returns a safe 503 with a 60-second Retry-After instead of an unhandled 500 or an incorrect up-to-date message. Background polling keeps its existing failure fallback. Logs record exception class and upstream status without provider response bodies.
- Clients respect 429 Retry-After and show a countdown; Sync 503 errors retain the server's safe explanation. No automatic POST retries.
- Render wake-up errors were independently observed; an earlier user-reported 500/429 has not yet been matched to an application request log. Do not call the incident resolved solely because deployment is live.


### Friends activity and popup-independent manual Sync — 2026-11-07

- Friends activity displays at most five entries after filtering. It reads the same backend recent-acceptance history as profile Recent Solves, rather than mixing live LeetCode responses with saved profile data. The panel refreshes its saved view once per minute while open; provider freshness still depends on users' own syncs and scheduled polling.
- Recent Solves orders each unique question by its latest recorded acceptance, including repeats. First-solve dates, question counts and scoring components are unchanged.
- New clients enqueue a private, account-owned sync job. A short worker request survives closing the popup; provider work executes on the server. Status is restored on reopen. No automatic POST replay after an ambiguous response. Legacy synchronous Sync remains available to already submitted clients.
- Jobs are transactionally recorded before acknowledgement, deduplicated under the user lock, claimed with row locks and processed by a scheduler recovery path. A five-minute processing timeout and ten-minute lease prevent permanently running jobs after interruption; expired jobs report failure and need a deliberate retry. Account generation/session checks reject outdated requests.
- Added an additive schema migration for the private jobs table, with RLS and public Data API grants revoked. No browser credentials are stored in jobs.
- Help describes 2 revision points and 5 daily bonus points first, explaining the up-to-10% points adjustment separately. Daily live verification remains unavailable; retained credits are preserved.
- Validation: frontend builds/type checks, backend syntax and background-script syntax. No test suite run. Production behavior still requires confirmation after deployment and loading the rebuilt extension.
