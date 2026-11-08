# LeetStreak 1.0.3 — remembered group leaderboard

- Restore the last selected group before requesting its leaderboard.
- Keep cached data scoped to the account, leaderboard and sort order.
- Ignore responses from earlier selections and competing startup requests.
- Stop using old generic caches that could display Global results under a group.
- Keep whole-number points and existing permissions. Backend scoring is unchanged.

Upload the ZIP to the existing Chrome Web Store item. Installed store copies get
the fix after review/publication and Chrome update delivery. For an unpacked copy,
replace its files with this package and reload it at chrome://extensions.

Extension build and TypeScript checks passed. Runtime manifest/archive inspection
passed. Automated tests and browser reopen checks were not run.
