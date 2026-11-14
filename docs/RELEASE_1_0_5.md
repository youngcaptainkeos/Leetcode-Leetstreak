# LeetStreak 1.0.5 — LeetCode problem lists and public playlists

Support for importing public LeetCode problem lists (e.g. `https://leetcode.com/problem-list/009101pc/` or shorthand `leetcode.com/problem-list/009101pc` and list slugs).

Problem lists are fetched directly from LeetCode's public GraphQL endpoint via `favoriteDetailV2` and `favoriteQuestionList`. Question titles, slugs, and difficulties are preserved, and questions auto-sync with the user's solved LeetCode history.

The original workspace extension/dist contains 1.0.5. Reload an unpacked install
from that folder. Upload the ZIP to the existing Web Store item for store users;
their copy updates after review/publication. No permissions were added.

Extension build, TypeScript, and automated unit tests passed.

## UI and saved release assets

- Dynamic points breakdowns show only the saved scoring path and earned rewards.
- Recent Solves in extension profiles uses a thin violet scrollbar on a charcoal
  track, with rounded corners and a matching hover color.
- The current extension/dist and all four repository ZIP copies contain the same
  1.0.5 runtime. A copy is available locally in Downloads/leetstreak-1.0.5.zip.
- Saved the three Web Store screenshots with clearly labeled illustrative data.
- This does not publish a new Chrome Web Store version automatically.

The progress suite passed all 12 tests during the preceding review. Final
TypeScript, build, archive-content and whitespace checks passed; a Chrome visual
check was not performed for the scrollbar. Public-list import was also checked
against a live 100-question list. Known limitation: the list importer does not
follow additional pages if LeetCode returns a partial question list.
