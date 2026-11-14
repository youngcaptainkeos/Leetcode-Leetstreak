# LeetStreak 1.0.5 — LeetCode problem lists and public playlists

Support for importing public LeetCode problem lists (e.g. `https://leetcode.com/problem-list/009101pc/` or shorthand `leetcode.com/problem-list/009101pc` and list slugs).

Problem lists are fetched directly from LeetCode's public GraphQL endpoint via `favoriteDetailV2` and `favoriteQuestionList`. Question titles, slugs, and difficulties are preserved, and questions auto-sync with the user's solved LeetCode history.

The original workspace extension/dist contains 1.0.5. Reload an unpacked install
from that folder. Upload the ZIP to the existing Web Store item for store users;
their copy updates after review/publication. No permissions were added.

Extension build, TypeScript, and automated unit tests passed.
