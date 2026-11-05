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

## Local verification

Run `PYTHONPATH=backend test_env/bin/python -m unittest discover -s backend/tests -v`
in the current development checkout, or use a separately created local virtual
environment with `backend/requirements.txt`. No production database or provider
credentials should be required. Tests must select isolated temporary databases.

## Release checkpoint

These changes are developed on `pre-launch`. Do not deploy until the production
key is securely configured, authenticated clients are packaged, migrations are
verified, and the owner approves the coordinated release. No hosting secret is
changed by this document or by the local configuration checks.
