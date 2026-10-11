# Chrome Web Store Submission Guide for LeetStreak

This guide provides the exact text, assets, and questionnaire answers required to publish **LeetStreak** to the **Google Chrome Web Store** without rejection.

---

## 1. Store Listing Metadata

### Extension Name (Title)
> **LeetStreak - LeetCode Streaks & Leaderboards**

### Short Description (Max 132 Characters)
> **Track daily LeetCode consistency, build streaks, earn weighted contest points, and compete on private squad leaderboards with friends.**

### Category
* **Primary Category:** `Developer Tools`
* **Secondary Category:** `Social & Communication` (or `Productivity`)

### Language
* `English`

---

## 2. Detailed Description (Copy & Paste into Chrome Web Store)

```markdown
Level up your LeetCode consistency with LeetStreak 🔥

Practicing data structures and algorithms (DSA) for tech interviews or college placements is tough when you do it alone. LeetStreak brings friendly accountability right into your browser popup.

Track your active daily streaks, earn weighted skill points, and compete with friends in private squads without ever leaving your active tab.

KEY FEATURES:

🔥 LIVE STREAK TRACKING
- Automatic daily flame counter and activity badges.
- Weekly and monthly solve breakdowns at a glance.
- In-app celebration toasts when squad members solve questions.

⭐ FAIR & WEIGHTED PROBLEM SCORING
- Contest-Rating Based: Harder problems reward more points (calculated via ZeroTrac contest difficulty ratings). No more spamming easy two-sum clones to game the leaderboard!
- Acceptance Rate Scaling: Real difficulty evaluated inversely against acceptance percentages.
- Daily Challenge Bonuses: +5 bonus points for tackling the official LeetCode Problem of the Day.
- Streak Multipliers: Maintain your streak to earn up to +10% bonus on all points earned.

👥 PRIVATE SQUADS & GLOBAL LEADERBOARDS
- Form private friend groups with 6-character invite codes (e.g., college placement groups, study clubs).
- Toggle between Private Squads, "My Friends", and the platform-wide Global Leaderboard.
- Full privacy control: disable the Global Leaderboard in 1 click if you only want to compare with friends.

👏 ONE-CLICK KUDOS & SOCIAL MOTIVATION
- Celebrate your friends' problem solves with daily thumbs-up Kudos.
- Hit "Kudos All" to hype up your entire leaderboard in a single click.
- Inspect friend profiles to view their recent solve ledger, difficulty spread, and points calculation.

🔒 PRIVACY-FIRST & ZERO PASSWORDS
- No LeetCode passwords or session cookies needed! LeetStreak syncs purely from your public LeetCode username.
- Instant in-app account deletion anytime you want.
- Fast, lightweight Manifest V3 architecture with offline caching.

Start your streak today and make your coding interview prep consistent and fun! 🚀

---
DISCLAIMER:
LeetStreak is an independent open-source project and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with LeetCode LLC. All problem titles and trademarks belong to their respective owners.
```

---

## 3. Privacy Practices Questionnaire (Developer Console)

During submission, Google requires you to complete the **Privacy tab**:

### A. Single Purpose Description (Paste this exact text):
> *"LeetStreak tracks the user's public LeetCode problem-solving activity, computes daily consistency streaks and weighted skill points, and displays comparative leaderboards among friends and peers directly in a browser extension popup."*

### B. Permission Justifications (Paste these exact answers):

1. **`storage`**:
   > *"Required to store the user's authentication token and cache dashboard/leaderboard responses locally for instant 0ms offline rendering."*

2. **`alarms`**:
   > *"Required to run periodic background synchronization alarms that check for new public LeetCode submissions and update daily streak status."*

3. **`host_permissions` (`https://leetcode.com/*` & `https://codestreak-api.onrender.com/*`)**:
   > *"Required to query LeetCode's public GraphQL endpoints for user submission history, and to synchronize points, streaks, and squad leaderboards with the LeetStreak cloud backend."*

### C. Data Usage Declarations:
* **Personally Identifiable Information (PII):** Check **Yes** for *Name* and *Email* (used for login and password recovery).
* **Website Content / User Activity:** Check **Yes** for *User Activity* (specifically public LeetCode solve records).
* **Certifications (Check all three):**
  - [x] I do not sell user data to third parties.
  - [x] I do not use or transfer user data for purposes unrelated to the item's single purpose.
  - [x] I do not use or transfer user data to determine creditworthiness or for lending purposes.

### D. Privacy Policy URL:
> `https://codestreak-api.onrender.com/privacy`

---

## 4. Visual Assets (Ready in `chrome_store_assets/`)

All required branding assets have been generated and packaged in the [`chrome_store_assets/`](chrome_store_assets/) folder:

1. **Store Icon (Required):**
   * File: `chrome_store_assets/store_icon_128x128.png`
   * Dimensions: `128 × 128` PNG

2. **Small Promo Tile (Required for Store Recommendations & Search):**
   * File: `chrome_store_assets/small_promo_tile_440x280.png`
   * Dimensions: `440 × 280` PNG (Optimized dark-mode glow canvas with high-res LeetStreak logo)

3. **Marquee Promo Tile (Optional / Recommended for Home Banner):**
   * File: `chrome_store_assets/marquee_promo_tile_1400x560.png`
   * Dimensions: `1400 × 560` PNG

4. **Screenshots (User Action Needed):**
   * Resolution: **1280 × 800** PNG or JPEG (Alternative: 640 × 400).
   * Quantity: Minimum 1 required, 3–5 recommended.
   * Suggested Screen Captures:
     * **Screenshot 1 (Hero Streak):** Popup Dashboard showing the Hero Flame card with today/weekly/monthly metrics and sync button.
     * **Screenshot 2 (Squad Leaderboard):** Squads tab with rankings, avatars, weighted score tags, and "Kudos All" button.
     * **Screenshot 3 (Solve Breakdown):** Inspecting a problem solve showing ZeroTrac Elo rating, acceptance delta, and streak multiplier bonuses.
     * **Screenshot 4 (Clean Settings):** Settings modal displaying the Global Leaderboard toggle, handle updating, and legal links.

---

## 5. Zip Package to Upload

Upload the production-optimized zip file:
* File: **`leetstreak_dist.zip`** (located at repository root)
* File structure: Directly contains `manifest.json`, `index.html`, bundled scripts, and icons at the root level without nested wrapping directories.

---

## 6. Official Submission Steps (Summary Checklist)

1. Log into the [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole).
2. Click **+ Add new item** and drag-and-drop `leetstreak_dist.zip`.
3. In the **Store listing** tab:
   * Title: `LeetStreak - LeetCode Streaks & Leaderboards`
   * Short description: Paste the short description from Section 1.
   * Detailed description: Paste the formatted description from Section 2.
   * Upload `chrome_store_assets/store_icon_128x128.png`.
   * Upload your `1280x800` screenshots.
   * Upload `chrome_store_assets/small_promo_tile_440x280.png`.
   * Category: **Developer Tools** (Secondary: **Social & Communication**).
4. In the **Privacy** tab:
   * Single Purpose: Paste text from Section 3A.
   * Permission justifications: Paste justifications for `storage`, `alarms`, and `host_permissions` from Section 3B.
   * Data usage: Declare Name, Email, and User Activity (public solve records).
   * Check all 3 compliance certifications (no selling data).
   * Privacy policy URL: `https://codestreak-api.onrender.com/privacy`
5. Click **Submit for review**!
