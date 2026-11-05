# Progress feature branch

Branch: `progress-bar` (Git branch names cannot contain spaces).

The extension now has **Leaderboards** and **Progress** menus. Progress includes
SQL 50, LeetCode 75, and Top Interview 150, with follow controls, completion bars,
search, completed/to-do filters, collapsed question lists with expand/collapse
controls, and a link to the next
unsolved problem. Public question lists were retrieved from LeetCode's
`studyPlanV2Detail` query on November 5, 2026 and are bundled for offline use:

- https://leetcode.com/studyplan/top-sql-50/
- https://leetcode.com/studyplan/leetcode-75/
- https://leetcode.com/studyplan/top-interview-150/

Recent public accepted submissions are checked when the popup opens, each minute
while it remains open, and after Sync or Refresh. Observed accepted questions are
remembered and count toward every plan containing them. Older questions outside
the public recent-submissions window can be checked off manually. Automatic
completion is never represented as a complete import of private LeetCode history.
Followed plans, observed solves, and manual checkmarks are stored locally for each
LeetStreak account and linked LeetCode handle. Removing a followed plan preserves
its progress. This local progress does not sync between browsers or devices.

## Add, remove, and restore plans

New users see SQL 50, LeetCode 75, and Top Interview 150. In **Progress → Add plan**,
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

Questions with a public LeetCode problem link are matched to observed accepted
LeetCode submissions. Other questions and lessons are completed manually. The
same LeetCode problem can complete multiple items if the source sheet references
it more than once. Questions open their LeetCode link where supplied, otherwise
the public takeUforward article or the source sheet.

The three LeetCode plans remain the only defaults; Striver's sheet is added only
when requested. Supported sources are explicitly validated. Additional external
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

These features call LeetCode's public GraphQL endpoint with `credentials: omit`,
using the extension's existing LeetCode host permission. They require no new
backend endpoints, database changes, credentials, or permissions. The website and
production service are unchanged by this branch.

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
