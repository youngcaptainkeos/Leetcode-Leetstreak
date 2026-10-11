# Privacy Policy for LeetStreak

**Effective Date:** October 11, 2026  
**Last Updated:** October 11, 2026  

LeetStreak ("we", "our", or "us") provides a browser extension and accompanying cloud synchronization service to help competitive programming enthusiasts track daily practice consistency, maintain streaks, and engage on leaderboards with friends.

This Privacy Policy explains how we collect, use, store, and protect your information when you use the LeetStreak Chrome Extension and associated backend API services (`codestreak-api.onrender.com`).

---

## 1. Single Purpose Statement
LeetStreak exists solely to track public LeetCode problem-solving activity, calculate streaks and weighted skill points, and display comparative leaderboards for friends and public participants. We collect only the minimum data strictly required to achieve this core functionality.

---

## 2. Information We Collect

### A. Information You Provide Directly
* **Display Name:** Used to identify your profile within groups and leaderboard rankings.
* **Email Address:** Used for account authentication, password recovery (via 6-digit verification codes), and optional critical update notices.
* **Account Password:** Stored exclusively in irreversibly hashed form using strong cryptographic hashing (PBKDF2/Bcrypt). We cannot read your plaintext password.
* **LeetCode Public Username:** Used to query public problem submission histories from LeetCode. **We never ask for, collect, or store your LeetCode password or session cookies.**

### B. Information Synchronized Automatically
* **Public Solve Records:** Problem titles, difficulty levels (Easy, Medium, Hard), acceptance rates, and submission timestamps retrieved from LeetCode’s public GraphQL endpoints.
* **Leaderboard Preferences:** Whether you have opted into the public Global Leaderboard or chosen private friends-only mode.
* **Social Interactions:** Kudos counts sent and received across 24-hour cycles.

### C. Information We DO NOT Collect
* We do **not** collect your browsing history, cookies, personal tabs, IP locations, device hardware IDs, or biometric data.
* We do **not** collect payment or financial information.
* We do **not** monitor your activity on any website other than public LeetCode submission records requested explicitly for synchronization.

---

## 3. How We Use Your Information
* To compute daily streaks, weekly totals, and contest-rating-weighted point scores.
* To render private friend squad leaderboards and the optional platform Global Leaderboard.
* To deliver password reset emails when requested.
* To cache leaderboard state locally in Chrome storage for instantaneous offline responsiveness.

---

## 4. Data Sharing and Transfer
* **No Sale of Data:** We do not sell, rent, monetize, or trade your personal data or activity logs to third parties, advertising brokers, or data aggregators.
* **No Third-Party Advertising:** LeetStreak does not display third-party advertisements or tracking pixels.
* **Infrastructure Service Providers:** Your data is processed securely through standard cloud hosting providers (Render, PostgreSQL, Brevo/SendGrid for transactional email delivery) strictly to operate the service.

---

## 5. Data Retention & Your Right to Deletion
* **Account Deletion:** You have complete autonomy over your data. You can permanently delete your account, solve history, squad memberships, and points at any time directly inside the extension by going to **Settings (⚙️) &rarr; Danger Zone &rarr; Delete Account**.
* **Immediate Purge:** Upon deletion, your account and all associated records are permanently erased from our active database.

---

## 6. Security Measures
We implement industry-standard safeguards to protect your personal information:
* All communication between the Chrome Extension and backend servers is encrypted in transit using Transport Layer Security (HTTPS/TLS).
* Passwords are encrypted using cryptographic salt and hash functions.
* Password reset tokens are short-lived 6-digit numeric codes that expire after 10 minutes.

---

## 7. Third-Party Disclaimer (LeetCode LLC)
LeetStreak is an independent open-source project and is **not affiliated, associated, authorized, endorsed by, or in any way officially connected with LeetCode LLC** or any of its subsidiaries or affiliates. The name "LeetCode" as well as related names, marks, emblems, and images are registered trademarks of their respective owners.

---

## 8. Changes to This Privacy Policy
We may periodically update this Privacy Policy to reflect feature additions or regulatory requirements. Any modifications will be posted here with an updated "Last Updated" date.

---

## 9. Contact Us
If you have any questions, concerns, or requests regarding this Privacy Policy or your personal data, please contact:
* **Project Maintainer:** Shashank
* **Email:** [shashu2804@gmail.com](mailto:shashu2804@gmail.com)
* **GitHub Repository:** [https://github.com/youngcaptainkeos/Leetcode-Leetstreak](https://github.com/youngcaptainkeos/Leetcode-Leetstreak)
