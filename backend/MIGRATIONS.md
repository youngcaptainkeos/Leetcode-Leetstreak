# Startup schema and maintenance boundaries

## Startup behavior

Importing `app.main` creates the application and a lazy database engine. It does
not connect to the database, run DDL, fetch providers or repair account data.
FastAPI startup calls `run_migrations` before starting the scheduler or accepting
requests. A schema error propagates and startup fails; do not suppress that error
to make the service appear healthy.

The runner uses one transaction for the registry, new tables and all pending
steps. PostgreSQL serializes runners with a transaction-scoped advisory lock.
SQLite uses `BEGIN IMMEDIATE`, including for DDL. Supported databases are
PostgreSQL and SQLite; do not assume another dialect has equivalent semantics.

Versions, in execution order:

| Version | Purpose |
|---|---|
| `20261106-bootstrap-v1` | Create missing tables on a new or legacy installation |
| `20261106-core-v1` | Consolidate old import/startup column and handle-index changes |
| `20261106-platforms-v1` | Add platform columns/indexes and missing legacy source handles |
| `20261105-auth-v1` | Existing authentication upgrade and plaintext reset-code invalidation |
| `20261105-global-display-v1` | Preserve the old display preference once |
| `20261105-tracking-v1` | Existing evidence/award storage foundation |
| `20261106-credits-v1` | Explicit account-level historical base estimates; no automatic revaluation |
| `20261106-provider-calendar-v1` | Unverified provider calendars separate from qualifying solve activity |
| `20261106-credit-privacy-v1` | Deny-by-default Data API access to new credit/calendar tables using PostgreSQL RLS |

New credit/calendar tables enable PostgreSQL RLS without public policies and
revoke table privileges from PUBLIC and existing `anon`/`authenticated` roles.
The custom-auth API accesses these through its private database connection,
using the table owner or an appropriately privileged backend role. Do not expose
these tables directly with end-user database credentials. Native tests check
RLS/policy metadata; no live hosted Data API audit is claimed. See the
[Supabase RLS guidance](https://supabase.com/docs/guides/database/postgres/row-level-security)
for the distinction between grants and row policies.

Execution order is explicit, not sorted by version name. Previously applied
versions keep their identities and are skipped. After the steps run, every
model table must contain its expected columns. This check detects missing
columns; it is not a complete constraint, data-type or data-integrity audit.

Existing points, daily flags, activity counts and unknown registration dates
are preserved. Missing legacy `created_at` values remain NULL. Future user
inserts receive dates without assigning a fictional date to older accounts.
Plaintext reset-code invalidation and the one-time source-handle attribution
remain intentional parts of the earlier upgrades.

SQLite's old inline UNIQUE constraint on `leetcode_username` requires an
explicit table-rebuild migration; this runner refuses that unsupported legacy
shape instead of silently retaining incompatible behavior. PostgreSQL's known
legacy constraint and the old standalone unique lookup index are handled.

## Readiness and scheduled work

- `/api/health` is process liveness only.
- `/api/ready` returns 200 only after successful startup and a database probe.
  It returns 503 before startup, after shutdown or when the probe fails, without
  exposing driver diagnostics. Use this endpoint for a deployment readiness
  check when the release configuration is reviewed; no live hosting settings
  have been changed by this implementation.
- Polling starts after its configured interval. Rating refresh starts after its
  weekly interval and uses the bundled local dataset until then. Neither runs
  immediately just because the service restarted.
- The scheduler is shut down when the application stops. Cross-process provider
  job ownership remains OPS-04; run a single application worker/instance until
  that work is completed. Migration locking does not coordinate provider jobs.

Full archive imports, the hardcoded historical daily patch, calendar-count
cleanup and all-user score recalculation no longer run at startup. Bounded,
resumable maintenance commands remain unfinished OPS-03 work. Do not invoke
the old unbounded helper functions as an operational substitute. R3 per-account sync uses component reconciliation. Bounded all-account rollout,
stronger LC first-solve evidence and live daily issuance remain release gates;
startup and profile reads do not perform historical score repair.

## Before release and recovery

1. Back up the target database privately and verify restoration into an isolated
   database. Do not commit dumps, connection strings or raw account records.
2. Exercise the upgrade against that isolated copy and review pending versions
   and preservation checks. Tests in this repository use synthetic data only.
3. Keep the current single-worker constraint and review the readiness probe.
   Production release is a separate owner checkpoint.
4. If startup migration fails, leave the service unavailable. The transaction
   rolls back pending schema changes and their version markers. Review the
   failure privately, repair the cause and retry; do not insert success markers
   manually or delete existing migration records to force a run.
5. For a failure discovered after a successful committed upgrade, stop writes
   and assess a forward repair or a verified backup restore. Switching source
   branches does not undo committed database migrations. Never restore over
   live writes without a separately reviewed recovery decision.

## Local checks

With backend runtime and test dependencies installed in a local environment:

```sh
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

Default API/migration tests select disposable SQLite databases. Native Postgres
checks additionally require `LEETSTREAK_TEST_POSTGRES_URL`, restricted by the
test harness to loopback hosts and a database name beginning
`leetstreak_test_`. These checks create/drop unique temporary schemas and
include separate-process startup migration contention. Never use a production
database URL for testing.
