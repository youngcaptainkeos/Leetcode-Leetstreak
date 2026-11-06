# Account study-plan sync

The authenticated backend stores an account's imported plan definitions and
source URLs, followed plans, removals (including custom-plan tombstones), and
external-item completion. LeetCode completion is a separate client-observed
progress cache. It never grants competitive points, awards or streak days.
Codeforces completion continues to come from the existing solve API.

`GET /api/users/{user_id}/progress` restores the authoritative library.
`POST` to the same path applies one operation with `base_version` and a unique
`operation_id`. Operations are initialize, add, remove, follow, manual,
restore and observe. Follow/check changes assign a boolean instead of toggling
the server's previous value. Account ownership is derived from the token;
another account cannot read or mutate the document.

The account row lock and conditional version update serialize writes. A stale
revision returns 409. The client reloads and reapplies that individual intent,
preserving unrelated changes from other devices. For the same item, the last
successfully synchronized explicit change wins. The most recent 256 operation
IDs suppress lost-response duplicates; ordinary assignments remain idempotent
beyond that receipt window. A follow for a removed plan is rejected rather
than silently restoring it. Explicit Add can restore a removed plan.

Limits: 50 custom plans, 1,000 questions per plan, 200 sections per plan,
2 MB document/payload, 20,000 completion identities and 120 writes per account
per 15 minutes. Definitions are validated as data; URLs must be public HTTPS
links without embedded credentials. The backend never fetches imported URLs.
The existing browser importer and its permission checks still perform imports.

The first successful account initialization imports that device's existing
plans, follows, removals and external checkmarks. Once initialized, account
state takes precedence over other devices' old snapshots. Before replacing a
legacy cache, the client retains a local recovery copy under the account's
`_before_account_sync` key. Old caches do not carry provider account-generation
proof, so LeetCode completion refreshes automatically instead of importing old
completion as verified history. Other devices' pre-existing local-only plans
can be re-added explicitly; they are not blindly merged back into the library.

Local storage is a cache and an operation outbox. Pending edits are persisted
before upload and retried on reopen, reconnection, focus and periodic refresh.
Unsynced work can be lost if device storage is erased; server-confirmed changes
recover after reinstall/sign-in. Pending and confirmed states have distinct
UI messages. Rejected size/validation changes are retained locally under
`_rejected_change` and visibly rolled back; other valid edits can still sync.
Browser request deadlines are 20 seconds. Sign-out/account switches stop the
client; outboxes are scoped to account ID and linked LeetCode handle.

LeetCode completion observations include the linked account generation. Old
observations cannot populate a replacement account, even when its handle later
changes back. Plans and external checkmarks survive a coding-handle change.
Account deletion removes the private progress document in both self-service
and admin deletion paths. The migration enables PostgreSQL RLS without public
policies and revokes PUBLIC/anon/authenticated table privileges. Access is
through the custom-auth backend's private database role.

The website has API methods but its Progress screen remains FEAT-02. Plan
selection, expanded question lists and startup-tab preferences remain device
settings in this step. No milestone or full release completion is claimed.
