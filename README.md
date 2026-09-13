# 🔥 LeetStreak

Track your LeetCode consistency, build active daily streaks, and compete on live leaderboards with your friends!

![LeetStreak Banner](https://raw.githubusercontent.com/youngcaptainkeos/Leetcode-Leetstreak/main/extension/public/icon128.png)

---

## 🚀 Quick Setup Guide for Users

Follow these simple steps to install **LeetStreak** on Google Chrome, Microsoft Edge, Brave, or any Chromium-based browser in under 1 minute!

### Step 1: Download the Extension
1. Download the latest `leetstreak.zip` release from the [GitHub Releases Page](https://github.com/youngcaptainkeos/Leetcode-Leetstreak/releases).
2. Unzip `leetstreak.zip` to any folder on your computer.

### Step 2: Load into Chrome / Edge / Brave
1. Open your browser and go to the extensions page:
   - **Chrome**: Type `chrome://extensions` in the address bar.
   - **Edge**: Type `edge://extensions` in the address bar.
   - **Brave**: Type `brave://extensions` in the address bar.
2. Toggle ON **Developer mode** (switch located in the top right corner).
3. Click the **Load unpacked** button (located in the top left).
4. **IMPORTANT**: Select the unzipped folder (or the `dist` folder if building from source) that **directly contains `manifest.json`**.
   > 💡 *Note: Make sure `manifest.json` is located right inside the folder you select! Do not select nested empty subdirectories.*

### Step 3: Pin & Open LeetStreak
1. Click the **Puzzle Piece icon** (🧩) in your top-right browser toolbar.
2. Click the **Pin icon** (📌) next to **LeetStreak** to keep it accessible.
3. Click the **LeetStreak icon** to launch!

---

### 🦊 Firefox Setup Guide

Follow these simple steps to install **LeetStreak** on Mozilla Firefox:

1. **Download & Extract**:
   - Download `leetstreak.zip` from [GitHub Releases](https://github.com/youngcaptainkeos/Leetcode-Leetstreak/releases).
   - Unzip `leetstreak.zip` to a folder on your computer.

2. **Open Firefox Debugging**:
   - Open Mozilla Firefox.
   - Type `about:debugging#/runtime/this-firefox` in the address bar and press **Enter**.

3. **Load the Extension**:
   - Click **Load Temporary Add-on...** (located near the top right).
   - Select the `manifest.json` file inside your unzipped folder (or `dist` directory).

4. **Pin & Launch**:
   - Click the **Puzzle Piece (🧩)** icon in Firefox's top-right toolbar and click **Pin to Toolbar** next to **LeetStreak**.

---

## 🎯 How Points & Scoring System Work

LeetStreak uses an advanced, fair scoring system based on actual problem difficulty, ZeroTrac contest ratings, acceptance ratios, and consistency bonuses:

### 1. Base Points Calculation
- **Contest Problems (Elo Rating Available)**:
  - Uses official **ZeroTrac Contest Rating** dataset.
  - Formula: `Points = Contest Elo Rating / 100` (e.g. Rating `1750` = `17.5 pts`, Rating `2200` = `22.0 pts`).
- **Non-Contest Problems**:
  - **Easy**: `10.0 pts` base.
  - **Medium**: `20.0 pts` base.
  - **Hard**: `30.0 pts` base.
  - **Acceptance Rate Adjustment**: Harder problems with lower acceptance rates reward bonus points (up to `+20 pts`), while higher acceptance problems adjust proportionally (`Adjustment = +20 × (1 - (2 × AcceptanceRate - 0.5))`).

### 2. Consistency & Performance Bonuses
- 🌅 **Daily First Solve Bonus**: `+5 pts` for your very first problem solved each day!
- 🎯 **First Try Bonus**: `+3 pts` for solving a problem on your first attempt without failed submissions.
- 🔥 **Active Streak Multiplier**: Up to **+10% boost** (`+1%` extra per active streak day up to 10 days) applied to all your daily solve points!

---

## ✨ Features

- 🔥 **Active Daily Streak Tracking**: Keeps track of your daily coding streak with an automatic 1-day grace period.
- 📝 **Live Solves & Points Breakdown**: Click any recent solve to open the **Points Breakdown Modal** and view exact base points, contest Elo ratings, acceptance deltas, and streak multipliers!
- 📊 **Global & Group Leaderboards**: Compare your streak, submissions, and points against all coders or private friends.
- 👥 **Private Friend Groups**: Create custom private groups or join your friends' groups using a unique 6-character invite code!

---

## 📱 How to Use LeetStreak

1. **Sign Up**:
   - Open the extension and click **Sign Up**.
   - Enter your Name, LeetCode Username, Email, and Password.
2. **Dashboard**:
   - View your active streak, submissions count, weighted points, and difficulty breakdown.
   - Click **Sync now** anytime to instantly refresh your latest LeetCode solves.
3. **Join or Create Groups**:
   - Navigate to the **Groups** tab.
   - Click **Create Group** to start a private leaderboard for your study group or class.
   - Share the **6-character Group Code** with your friends so they can join!
4. **Leaderboards**:
   - Check the **Global** or **Group Leaderboards** to see who's staying consistent!

---

## ❓ Frequently Asked Questions

<details>
<summary><b>Which folder do I select when clicking "Load unpacked"?</b></summary>
<br />
Select the unzipped folder (or `dist` folder if building from source) that directly contains the <code>manifest.json</code> file.
</details>

<details>
<summary><b>Does LeetStreak require my LeetCode password?</b></summary>
<br />
<b>No!</b> LeetStreak only asks for your public LeetCode username. It fetches your public submission calendar safely using public GraphQL endpoints.
</details>

<details>
<summary><b>Forgot your password?</b></summary>
<br />
Click <b>Forgot password?</b> on the login tab. Enter your email to receive a 6-digit verification code to reset your password instantly.
</details>

<details>
<summary><b>How often does my streak sync?</b></summary>
<br />
The backend automatically syncs every user's progress every 15 minutes. You can also click the <b>Sync now</b> button inside the extension anytime to refresh immediately!
</details>

---

<p align="center">
  Built with ❤️ for coders keeping their streak alive! 🔥
</p>
