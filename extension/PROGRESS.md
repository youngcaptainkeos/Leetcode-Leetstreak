# Progress feature branch

Branch: `progress-bar` (Git branch names cannot contain spaces).

The extension now has **Leaderboards** and **Progress** menus. Progress includes
Striver's A2Z, SQL 50, and Top Interview 150 by default, with follow controls, completion bars,
search, completed/to-do filters, collapsed question lists with expand/collapse
controls, and a link to the next
unsolved problem. Public question lists were retrieved from LeetCode's
`studyPlanV2Detail` query on November 5, 2026 and are bundled for offline use:

- https://leetcode.com/studyplan/top-sql-50/
- https://leetcode.com/studyplan/leetcode-75/
- https://leetcode.com/studyplan/top-interview-150/

LeetCode-linked items use automatic completion, with no editable checkboxes.
Complete solved history is imported from the matching LeetCode account signed in
within the same browser. The extension checks account identity before and after
fetching all accepted-question pages and only saves a complete, valid result.
History sync runs on opening (cached for 15 minutes), and retries automatically each minute while open, when the window regains focus,
and after reconnecting. Adding or following a plan also requests a sync. Saved solves
immediately apply to every plan, including newly added plans.

Recent public accepted submissions are also checked on opening, every minute
while open, and after Sync or Refresh. Failed full-history imports keep saved
progress and offer an actionable retry rather than treating recent activity as
complete history. Older manual checkmarks on LeetCode-linked items no longer
count as verified solves.

Followed plans, verified solve slugs, full-sync timestamps, and external-item
checkmarks are stored locally for each LeetStreak account and linked LeetCode
handle. This progress does not sync between browsers or devices.

## Add, remove, and restore plans

New and existing users receive Striver's A2Z, SQL 50, and Top Interview 150, in that
order. Existing local state migrates once to the new defaults while preserving
solve history and added plans. LeetCode 75 is retained if it was explicitly
followed or imported; otherwise it can be added again by link. Later removals and
an empty library remain respected after migration.

In **Progress → Add plan**,
paste a public LeetCode study-plan URL (or its slug), then choose **Add & follow**.
For example, `https://leetcode.com/studyplan/30-days-of-javascript/` loads its
current public question list directly from LeetCode. Re-adding an existing plan
selects and follows it without creating duplicates. Imported lists are saved
locally and remain available offline. Invalid links, unavailable plans, malformed
responses, and cancelled imports leave existing plans intact.

Every selected plan has a **Remove plan** button. Starter plans are hidden when
removed; imported lists are removed from the library. Solved history is retained.
When every plan has been removed, the UI shows a compact empty state with **Add a
plan** and **Restore starter plans** actions. An empty library survives reopening
the extension. Restoration or re-importing restores progress rather than resetting
it.

### External provider: Striver's A2Z

The importer also accepts:
`https://takeuforward.org/prep-hub/strivers-a2z-dsa-sheet?open=none`

This provider uses a bundled public metadata snapshot dated November 5, 2026:
495 items across 84 sections, including practice problems and lessons. Only public
item names, categories, difficulty labels, and links are included; no solutions,
paid lesson content, login state, cookies, or user progress are imported.
The snapshot date and source link appear on the plan. Future sheet changes require
updating this snapshot in an extension release.

Questions with a public LeetCode problem link are matched to saved, verified
LeetCode solves. The remaining external questions and lessons have completion
checkboxes and external links; their checkmarks persist independently of syncing. The
same LeetCode problem can complete multiple items if the source sheet references
it more than once. Questions open their LeetCode link where supplied, otherwise
the public takeUforward article or the source sheet.

Striver's A2Z is one of the three default plans. Supported sources are explicitly validated. Additional external
sites require a provider adapter rather than fetching arbitrary pasted URLs.
Striver import works offline from its bundled snapshot and needs no new host
permissions or backend changes.

**What are my friends up to?**, above the playlists, uses members of your existing LeetStreak groups,
excluding yourself and deduplicating shared members. It retrieves each friend's
three most recent public accepted submissions, shows the latest 15 across the
selected friends, and opens each question on LeetCode. Requests use at most four
concurrent connections and show individual profile failures. A friend filter and
Refresh control are included. Friend activity is fetched when Progress opens.

The daily challenge banner appears just below the LeetStreak header in normal page
flow. It uses the official challenge date, checks for an accepted submission of
that exact problem on that UTC date, and disappears after completion or dismissal.
Dismissal lasts for that challenge date. A completed challenge is remembered for
the day even if it falls out of the public recent-submissions window. If the public
check fails, a retry message is shown rather than claiming the question is unsolved.

## Startup preference

In **Account Settings → Preferences → Startup tab**, choose **Progress**,
**Leaderboards**, or **Last used**. The choice is saved per LeetStreak account
and applies when reopening the extension.

## Browser session and privacy

Public activity and plan metadata use `credentials: omit`. Complete historical
progress uses the browser's existing LeetCode session, sent only to LeetCode's
read-only GraphQL endpoint. A small content-script bridge on an open LeetCode tab
supports browsers that block cross-site session requests; otherwise the extension
tries the request directly. After updating the extension, refresh an existing
LeetCode tab to load the bridge. Sign in there using the linked handle, then reopen the extension.
History syncing starts automatically; no separate sync button is needed.

No cookies or session tokens are read, stored, or sent to the LeetStreak backend.
Only question slugs and the sync time are saved locally. No new host permissions,
backend endpoints, or database changes are required. The website and production
service are unchanged by this branch.

## Build and try it

```bash
npm --prefix extension ci
npm --prefix extension run test:progress
extension/node_modules/.bin/tsc --noEmit -p extension/tsconfig.json
npm --prefix extension run build
```

Open `chrome://extensions`, enable Developer mode, and load `extension/dist` as an
unpacked extension, or reload your existing unpacked installation pointing there.
The root `leetstreak.zip`, `leetstreak_dist.zip`, and
`backend/app/leetstreak.zip` are synchronized copies for distribution. This branch
does not update the production download until it is merged and deployed.
