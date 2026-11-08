# LeetStreak 1.0.1

## Included

- Durable Sync status that survives closing/reopening the popup.
- Independent LeetCode and Codeforces backend syncing with partial-success messages.
- Verified public Codeforces first solves and evidence-gated revisions.
- Restart recovery and preservation of locked point balances.
- Updated Help copy; existing extension permissions unchanged.

## Publish the extension update

1. Open the existing LeetStreak item in Chrome Web Store Developer Dashboard.
2. Choose **Package → Upload new package**.
3. Upload `leetstreak_dist.zip` (manifest version **1.0.1**).
4. Review the draft and submit it for review, then publish when approved.

Use the same store item to retain its extension ID, users and extension storage.
Existing store installations receive published updates automatically. Unpacked
installations require replacing the unpacked files and reloading the extension.

Server changes deploy independently and support the published 1.0.0 client.
The server's published-version announcement remains at 1.0.0 until the store
update is actually published; the minimum supported version is unchanged.
No reviewer/test account is included in this package. If the previous reviewer
account was removed, replace its confidential Web Store test instructions before
submitting the update. Do not commit reviewer credentials to the public repo.
