# Codeforces integration (progress-bar)

## Connect and sync

Existing LeetStreak users can add their public Codeforces handle in Account
Settings. Signup also offers the same optional handle: omitting it or leaving it
blank uses the existing LeetCode-only flow. A supplied handle is validated before
account creation; its history sync runs in the background after signup. The LeetCode username help button opens the same guide used at signup
on both clients. Connecting Codeforces validates its public profile, then starts
an automatic background import. No Codeforces password, API key, session cookie,
or submitted source code is requested or stored. Handles are self-declared,
like the existing LeetCode integration; profile existence does not prove ownership.
A case-insensitive unique index prevents two LeetStreak users claiming the same
Codeforces handle. Adding a handle does not create a new LeetStreak account.
Codeforces-only signup is outside this change.

The link endpoint requires the current user's signed LeetStreak access token.
Clients now retain the token returned by login/registration and clear it on
logout. Configure JWT_SECRET in the hosting environment for stable sessions;
without it the server creates an ephemeral signing key on each process start,
rather than using a signing secret published in the repository. Sessions created before this update must sign in again before linking.

Initial history imports paginate public user.status results. Incremental imports
recheck the last two days, and a full reconciliation runs at least weekly while
the scheduler is active. The default 15-minute scheduler polls both platforms;
a 10-minute cache avoids redundant CF imports. Profile and submission API calls
share a process-wide limiter of one request per 2.1 seconds. This assumes the
existing single-process service; multiple API replicas require a shared limiter
and job coordination before scaling the service.

Only solo, non-ghost, public submissions with verdict OK and final TESTS are
eligible. Team submissions, pretests, private data, and unresolved verdicts are
excluded. Earliest accepted timestamps determine the first solve. Repeated
acceptances earn no extra points or unique-solve activity. History reconciliation
removes solves that are no longer eligible. A failed or truncated API import
leaves the saved ledger untouched and exposes an automatic-retry status.

Updating to a different handle replaces that user's Codeforces solves/activity,
without deleting LeetCode history. Solve timestamps are stored in UTC and returned with explicit timezone offsets.
Daily counts use IST calendar days to match existing LeetStreak activity. The combined dashboard, group/global/friend
leaderboards, recent-solves feed, and extension friend activity include both
platforms, with correct question URLs and visible source labels.

## Points

For a rated Codeforces problem:

    base = 8 + 0.012 * (problem_rating - 800)
    multiplier = 1 + 0.10 * min(30, max(0, streak_days)) / 30
    earned = round(base * multiplier, 4)

Examples before streak bonuses: 800 -> 8, 1400 -> 15.2, 1800 -> 20,
2200 -> 24.8. No LeetCode daily bonus or acceptance-rate multiplier applies to
Codeforces. Unrated problems contribute activity and plan completion but award
zero points; a later supplied rating is picked up on reconciliation.

This is provisional calibration from similar Codeforces/LeetCode problems,
strongest in the 1500-2100 CF range. It is not a certified rating conversion.
The help modals and public website's Scoring section explain the formula.

Legacy LeetCode totals use only the LC ledger when estimating unlogged solves.
LeetCode solves before CF linking retain their LC-only scoring streak. New LC
solves and CF solves can use the combined activity streak. The visible streak
uses the union of activity days. Reads report stored awards and never replace
them with rounded display scores.

## Data provenance and migration

The additive, idempotent migration runs before request handling/startup polling.
Existing solves default to platform=leetcode; their source_handle is backfilled
from the user's currently linked LC handle (earlier handle changes cannot be
reconstructed). New solves store the handle observed at import.

Additional solves columns:

- platform: leetcode or codeforces (indexed).
- source_handle: account used for the import.
- source_submission_id: Codeforces submission ID, where available.
- problem_rating and problem_url: provider rating and exact exercise link.
- scoring_version: leetcode-v1 or cf-linear-v1.

The legacy unique(user_id, title_slug) constraint is retained. CF IDs are
namespaced as cf-<contestId>-<lowercase index> to prevent platform collisions.
platform_activity holds separate CF daily counts; existing daily_activity stays
LC-only, so LC calendar refreshes cannot overwrite CF activity. Account deletion
also removes additional platform activity. User columns expose the CF handle,
first-link time, successful sync/full-sync times, and last sync error.

API changes are additive. Recent solves/feed return platform, problem_url,
source_handle, submission ID, problem_rating, and scoring_version. The legacy
leetcode_url field remains an alias to the actual exercise URL for older clients.
Dashboard/leaderboard data provide separate CF counts and point contributions.
The extension uses the backend's verified CF ledger to complete matching playlist
questions automatically once a handle is linked; unlinked/external exercises keep
manual checkboxes. Clients never award competitive points from checkboxes.

## Rollout

This branch needs the backend and clients released together. Building or pushing
progress-bar does not deploy the production backend. Apply through the existing
Render release flow when this feature is merged; do not manually edit a user's
production account or import scores on their behalf. All changes are additive
except replacing CF history when its owner updates their linked CF handle.

## Platform-specific metrics

Dashboard responses include platform_stats for all, leetcode, and codeforces.
Each provides source-specific earned points, streak, today/week/month counts,
lifetime total, and a seven-day calendar. CF reports rated/unrated counts rather
than assigning LC difficulty categories to CF ratings. LC category counts remain
LC-only; combined lifetime totals add CF unique solves. Point filters show the
actual platform contribution without recalculating awarded streak bonuses.

Both clients use the same compact metrics panel for the owner and inspected
profiles. A profile request always uses that profile's user ID, clears stale data,
and ignores responses after closing or switching profiles. Failed requests show
an unavailable state instead of invented counts. Recent-solves accepts
platform=all|leetcode|codeforces and applies the filter before its limit. This
avoids omitting CF solves just because newer LC solves filled the combined list.
The selector controls the stats card and inspected profile.
