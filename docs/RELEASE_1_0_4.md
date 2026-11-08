# LeetStreak 1.0.4 — cached leaderboard navigation

Visited Global, Friends and group leaderboards are cached separately by account
and sort mode. Saved results survive popup closure. Fresh cached results are
reused for one minute without another board request; older cached rows stay
visible during background refresh. The first visit to an uncached view still
needs a server response. Concurrent identical requests share one fetch.

Group navigation metadata also restores from cache. Late responses populate
the correct cache without switching the active board. Sync and coding-account,
kudos and membership changes invalidate freshness; responses from before an
invalidation cannot replace newer cached data.

Pending Sync status polls every two seconds. The backend batches new accepted
submissions and first-date lookups under the existing account transaction.
Scoring rules, precision, cooldowns, ownership and deduplication remain.

The original workspace extension/dist contains 1.0.4. Reload an unpacked install
from that folder. Upload the ZIP to the existing Web Store item for store users;
their copy updates after review/publication. No permissions were added.

Extension build, TypeScript, Python parsing and archive inspection passed.
Automated tests and browser navigation/reopen checks were not run. Broad
before/after sync performance gains are not claimed without paired measurements.
