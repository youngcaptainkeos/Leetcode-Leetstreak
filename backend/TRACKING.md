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
  detached from the deleted question. Explicitly awarded history fails closed
  until R3 reconciliation can treat its components safely.

## Revision proposals, not rewards yet

`revision_candidates` returns proposals only. It does not write awards or change
displayed totals. Eligibility requires a proved first-solve date, matching
current account identity/generation, and an accepted repeat after the supplied
last-successful-sync boundary. Initial import has no boundary and earns no
retrospective revisions.

The first proposal is due after seven elapsed days from the first solve or last
rewarded revision. Each subsequent proposal assumes the preceding one will be
awarded, then advances that seven-day anchor. Unrewarded attempts do not restart
the cooldown. A previous reward with an unknown date blocks proposals rather
than guessing. Each proposal uses the existing `2 × streak multiplier` formula;
the streak is calculated from proved unique first solves on either platform,
as of the acceptance instant in IST. Calendar days, repeats and later solves
cannot inflate that multiplier.

R3 must apply eligible proposals under the account lock, use unique replay-safe
award keys, preserve their actual amounts and publish consistent totals to both
clients. A caller must not treat proposals themselves as paid rewards.

## Release blockers still open

The runtime calculator and legacy activity tables remain in use. They still
require R3's protected-credit reconciliation, no-retrospective-daily enforcement,
verified-only streak/count integration and matching read-API breakdowns. Proven
LC live first solves/daily eligibility need stronger history evidence. The full
handle-replacement/rename lifecycle is DATA-01 work: generation guards prevent
stale writes but do not clear/reconcile a replaced LC account's old history.
Backend plan persistence is also a later milestone.

This branch must not be released as complete scoring or account-replacement
support on the strength of R2's evidence tests. All provider tests are mocked,
and database tests use synthetic accounts in disposable local databases. No
real provider account, production database, client bundle or hosted deployment
is changed by this checkpoint.
