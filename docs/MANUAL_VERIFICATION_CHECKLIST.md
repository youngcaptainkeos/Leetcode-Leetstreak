# Manual Extension Verification Checklist

This checklist covers browser-specific and UI behaviors that cannot be fully exercised inside automated headless CI environments. Perform these manual verification steps before publishing or distributing unpacked extension builds.

---

## 1. Unpacked Installation & Reload
- [ ] **Load Unpacked**: Open `chrome://extensions`, enable **Developer mode**, click **Load unpacked**, and select the folder containing `manifest.json`.
- [ ] **Manifest & Icon Verification**: Verify the extension title is **LeetStreak**, version displays **1.1.0**, and the icon displays sharply in the toolbar.
- [ ] **Reload Card**: Click the reload button (🔄) on the LeetStreak card in `chrome://extensions`; confirm the extension reloads instantly without errors.

---

## 2. Popup UI & Responsive Layout
- [ ] **Popup Launch**: Click the pinned LeetStreak icon in the browser toolbar; confirm popup opens smoothly without clipping.
- [ ] **Theme & Typography**: Confirm dark mode theme colors, typography, buttons, and badges match the existing charcoal/violet theme and Inter/Outfit typography.
- [ ] **Points Help Modal**: Click **❓ Help** in the header; confirm the Points Rulebook modal displays base points, ZeroTrac contest ratings, and streak multiplier formulas correctly.
- [ ] **Update Banner & Guide**: When an update is detected, verify the update banner displays honest reload steps and the toggleable **How to update?** guide opens with clear instructions.

---

## 3. Authentication & Session Lifecycles
- [ ] **New Registration**: Register a test account; verify dashboard immediately renders with active streak, difficulty stats, and empty friends leaderboard.
- [ ] **Popup Reopen (Persistence)**: Close the extension popup and reopen it; confirm the authenticated dashboard renders immediately without flashing the login view.
- [ ] **Password Change & Revocation**: Change password from settings; verify existing sessions are revoked and prompt for sign-in.
- [ ] **Clean Logout**: Click Logout; confirm tokens and caches are cleared and onboarding view appears.

---

## 4. Multi-Platform & Progress Features
- [ ] **Codeforces Handle Link & Verify**: Enter a Codeforces handle; confirm the verification token challenge is presented with clear instructions.
- [ ] **Study Plan Library**: Navigate to the **Progress** tab; confirm default starter plans (Striver’s A2Z, SQL 50, Top Interview 150) render with progress bars and question search.
- [ ] **Direct Friends Search**: Open the **👥 Friends** modal, search for a username; confirm action buttons (Add Friend, Pending, Friends) reflect accurate state.

---

## 5. LeetCode In-Page Content Script
- [ ] **DOM Injection**: Open any problem on LeetCode (e.g. `https://leetcode.com/problems/two-sum/`).
- [ ] **Console Inspection**: Open DevTools Console; confirm `leetcode-listener.js` and `leetcode-page-bridge.js` initialize cleanly with zero CSP (Content Security Policy) errors.
