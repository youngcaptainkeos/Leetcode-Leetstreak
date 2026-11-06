# API access and session contract

This is the target access contract for pre-launch M1. The route-protection step
must enforce it; inventorying a route does not itself secure the route.

| Routes | Access |
|---|---|
| Website, legal pages, static assets, health, version, downloads, app config | Public; no account secrets |
| Register, login, initiate/verify password recovery | Public; bounded abuse controls |
| Global rankings/feed, coding profile/dashboard, recent solves, CF solve identities | Signed-in coding-profile reads; never passwords, email, or reset details |
| Sync, change LC/CF handle, settings, delete account, account session/preferences | Authenticated self only; body/path IDs must match token |
| My groups, friends rankings | Authenticated self only |
| Create/join group, kudos | Authenticated actor from token; retained legacy actor fields must match |
| Group rankings/member list/invite code | Authenticated group member |
| Remove a group member | Owner, or a member leaving themselves; owner must transfer/delete first |
| Delete/transfer group | Authenticated owner; transfer target must be a member |
| Poll all, broadcast release, debug/repair/delete/reset administration | Fail-closed administrator credential; no public test-email route |

The Global display preference is not an opt-out from participation or coding
profile visibility. Every user remains ranked. Private group access is separate.
Direct friendships are a later milestone; this does not implement them.

`show_global_leaderboard` is the canonical account preference. Migration
`20261105-global-display-v1` preserves the old true/false choice once; the old
`global_leaderboard_enabled` request field remains a deprecated display-only
alias for transitional clients. No ranking/feed query filters participation by
either preference. Other users' coding profiles omit these account preferences
and private sync diagnostics. Owners can transfer to an existing member before
leaving; account deletion refuses unresolved owned groups.

## Signing key configuration

Set a stable `JWT_SECRET` of at least 32 bytes using the hosting secret store.
Generate a random value locally with `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`.
Do not paste the result into source, issues, logs, screenshots, or test fixtures.
Production refuses missing/short keys. Keep the same value across restarts and
instances. Rotating it deliberately invalidates existing tokens; coordinate the
client update and sign-in requirement before deployment.

For local-only development, set `APP_ENV=development` and
`ALLOW_EPHEMERAL_JWT=true` to explicitly accept sign-out on restart. This flag
cannot enable temporary signing keys in production. Prefer a stable local secret
in an ignored environment file. Token tests use fictional keys only.

Tokens require the expected HS256/JWT header, positive consistent subject/account
identity, issued-at time, and unexpired expiry. Malformed input must be a controlled
authentication error, not a server error. Session revocation/account existence
checks are added by the route/session implementation steps.

Password recovery now returns the same generic response for a known, missing, or
ambiguous handle, without exposing its email. Use the registered email when a
LeetCode handle is shared. Codes expire after 15 minutes, allow five incorrect
attempts, and are stored as account/request-bound keyed verifiers. A resend
invalidates the old code; a 60-second resend cooldown prevents repeated sends.
Persisted HMAC-keyed counters also limit per-account/per-peer requests and login
attempts. They do not trust a raw client-supplied forwarding header.

New/reset passwords allow 15–100 characters with no required symbol/capital
recipe and reject a small baseline list of common values. This is not a claim of
complete compromised-password screening. Existing short passwords remain usable
until changed. Session versions revoke old tokens after reset/change or explicit
sign-out-all. Authenticated password change issues a replacement current-session
token; the other sessions are invalidated. Migration `20261105-auth-v1` adds only
authentication fields and invalidates old plaintext reset codes; solve history
and points are not changed. Local migration checks cover SQLite; production
PostgreSQL migration validation remains a release prerequisite.

## Local verification

Administrative requests require a separately generated `ADMIN_SECRET` of at least
32 bytes in `X-Admin-Secret`. Missing/blank/short configuration always denies
access. Ordinary account tokens do not grant administration. There is no
production test-email endpoint. Date repair uses POST, not a mutating GET.

Announcements accept a reviewed `release_id` from `app/releases.py`, with
`dry_run=true` by default. Preview returns counts only; sending requires an
explicit `dry_run=false`. Operators cannot supply arbitrary links or HTML.
Stored job guards reject duplicate broadcasts and overlapping/repeated all-user
polls. Interrupted/failed broadcasts require private operator review before
retrying; do not reset the guard blindly because provider acceptance can be
ambiguous. This is bounded protection, not a claim of exactly-once email delivery.

Email dispatch selects one configured provider (`EMAIL_BACKEND=auto` chooses the
first configured Brevo, SendGrid, Resend, or SMTP transport). A provider's accepted
request is recorded as accepted, not inbox-delivered. Missing configuration,
rejection, failure, and unknown timeout outcomes never count as successful sends.
Unknown outcomes require review, not automatic cross-provider resending. SMTP
work runs outside the async event loop. Development tests mock all transports;
no log-only mode prints reset codes, recipient addresses, or mail bodies.

Run `PYTHONPATH=backend test_env/bin/python -m unittest discover -s backend/tests -v`
in the current development checkout, or use a separately created local virtual
environment with `backend/requirements.txt`. No production database or provider
credentials should be required. Tests must select isolated temporary databases.

### PostgreSQL and browser acceptance

Install `backend/requirements-test.txt` into a local virtual environment for the
optional browser checks. Build both clients first. Run
`python backend/tests/browser_smoke.py` with Playwright Chromium installed, or
set `LEETSTREAK_CHROME_EXECUTABLE` to a local Chrome/Chromium executable.
`LEETSTREAK_BROWSER_EVIDENCE_DIR` optionally selects a private output directory;
otherwise evidence goes into a temporary directory. The script uses synthetic
accounts, isolated SQLite, mocked providers and intercepted API requests. It
checks the popup in browser-preview mode and the website; native extension
background/content-script acceptance is a separate M3 check.

To exercise PostgreSQL migrations, supply `LEETSTREAK_TEST_POSTGRES_URL` when
running the backend tests. The test refuses non-loopback hosts or database names
without the `leetstreak_test_` prefix. It uses a temporary schema per check and
verifies additive changes, retained solve awards/preferences, concurrent registry
creation, transaction rollback and safe retry. Never point it at production.

## Release checkpoint

These changes are developed on `pre-launch`. Do not deploy until the production
key is securely configured, authenticated clients are packaged, migrations are
verified, and the owner approves the coordinated release. No hosting secret is
changed by this document or by the local configuration checks.
