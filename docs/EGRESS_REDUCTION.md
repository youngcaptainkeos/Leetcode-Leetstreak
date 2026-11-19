# Database egress reduction — November 19, 2026

## Implemented: dashboard reads and leaderboard aggregation

- `platforms.verified_daily_counts` groups eligible first solves in the database
  by account identity, platform and IST date. Results contain counts and identity
  fields rather than full Solve and User records repeated for every question.
- Account generation and exact Python casefold matching remain in place. Future
  dates, missing source handles and ineligible first-solve evidence remain excluded.
- Dashboards reuse those totals for period counts, streak input and activity chart.
  The incomplete-history flag uses a limited ID lookup instead of loading all solves.
- Legacy calendar queries for the dashboard activity chart are limited to seven days.
- Leaderboards automatically use the same grouped daily totals.
- No schema migration, score recalculation, balance write, provider request change,
  cache, or sync-schedule change is introduced by this patch.

## Validation and limits

Python compilation and `git diff --check` passed. No automated test suite or live
database comparison was run for this change. Correctness review covered IST date
conversion, account replacement, casefold matching, first-solve eligibility, and
the existing max-per-platform/day activity merge. Runtime parity and actual
egress savings are not yet measured.

The screenshot showed organization-wide usage across all projects; it cannot
attribute traffic to LeetStreak. Filter the Supabase usage report to this database
and inspect Shared Pooler Egress. Compare complete days after deployment, allowing
for the report's refresh delay. Do not infer a percentage reduction from code alone.

## Remaining work

- Measure which queries dominate traffic before selecting further changes.
- Consider short, correctly scoped server caches with mutation invalidation.
- Reduce routine sync reads of unchanged calendars, scoring snapshots and ledgers.
  Preserve immutable awards and recovery evidence; do not reprice historical scores.
- Firefox packaging work is separate and does not need to be released for these
  backend changes to benefit installed extensions.
