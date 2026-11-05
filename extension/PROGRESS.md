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
