# Privacy Policy for LeetStreak

**Effective Date:** October 11, 2026  
**Last Updated:** November 7, 2026

LeetStreak ("we", "our", or "us") provides a browser extension and accompanying cloud synchronization service to help competitive programming enthusiasts track daily practice consistency, maintain streaks, and engage on leaderboards with friends.

This Privacy Policy explains how we collect, use, store, and protect your information when you use the LeetStreak Chrome Extension and associated backend API services (`codestreak-api.onrender.com`).

---

## 1. Single Purpose Statement
LeetStreak exists solely to track LeetCode and optionally linked Codeforces problem-solving activity, calculate streaks and weighted skill points, and display comparative leaderboards for friends and public participants. We collect only the minimum data strictly required to achieve this core functionality.

---

## 2. Information We Collect

### A. Information You Provide Directly
* **Display Name:** Used to identify your profile within groups and leaderboard rankings.
* **Email Address:** Used for account authentication, password recovery (via 6-digit verification codes), and optional critical update notices.
* **Account Password:** Received over HTTPS for registration and authentication. Only a salted PBKDF2 password hash is stored; passwords are not intentionally logged.
* **LeetCode Public Username:** Used to query public problem submission histories from LeetCode. **We never ask for, collect, or store your LeetCode password or session cookies.**

* **Optional Codeforces Username:** Used to retrieve public profile and accepted-submission records for the linked handle. We do not request your Codeforces password.

### B. Information Synchronized Automatically
* **Public Solve Records:** Problem titles, difficulty levels (Easy, Medium, Hard), acceptance rates, problem ratings, provider identities and submission timestamps retrieved from LeetCode and Codeforces. For complete LeetCode plan progress, the browser uses the matching signed-in LeetCode session to read solved-question identities. Session cookies stay between your browser and LeetCode; they are not sent to our backend.
* **Leaderboard Display Preference:** Whether the Global leaderboard is shown on your own home page. All registered users participate in Global rankings regardless of this preference. Other signed-in users can view coding profiles and statistics; private group membership and invite codes require appropriate group access.
* **Social Interactions:** Kudos counts sent and received across 24-hour cycles.

* **Study Plans and Progress:** Imported plan definitions and source links, followed/removed plans, external-item checkmarks and observed solved-question identities are saved privately to your account for recovery and sync across devices. Browser storage holds an offline cache and pending changes. External checkmarks never grant competitive points.

* **Security and Request Metadata:** The backend processes network/IP information for request handling and abuse prevention. Application rate-limit buckets store keyed hashes of account/source identifiers. Hosting providers may retain request logs. We do not use this to determine your precise physical location.

### C. Information We DO NOT Collect
* We do **not** collect general browsing history, GPS location, device hardware IDs, biometric data, or unrelated tabs. The extension may locate an open LeetCode tab to read solved history; it does not collect your LeetCode or Codeforces passwords or export their session cookies.
* We do **not** collect payment or financial information.
* Activity processing is limited to coding submissions, practice progress and interactions needed for the service. When you explicitly import a study-plan link and grant website access, the extension reads that selected page to identify question titles and links. We do not collect general keystroke, mouse-position or browsing analytics.

---

## 3. How We Use Your Information
* To compute daily streaks, weekly totals, and contest-rating-weighted point scores.
* To render private group and Global leaderboards. All registered accounts participate; showing Global on your own home page is optional.
* To deliver password reset emails when requested.
* To cache leaderboard state locally in Chrome storage for instantaneous offline responsiveness.

---

## 4. Data Sharing and Transfer
* **No Sale of Data:** We do not sell, rent, monetize, or trade your personal data or activity logs to third parties, advertising brokers, or data aggregators.
* **No Third-Party Advertising:** LeetStreak does not display third-party advertisements or tracking pixels.
* **Infrastructure Service Providers:** Render and the configured PostgreSQL/Supabase database process service data. Configured transactional email providers (such as Brevo, Resend, SendGrid or SMTP) process recipient addresses and email content for delivery. Google Fonts may receive network metadata when the extension requests fonts. These requests do not include your LeetStreak authentication token or private plan library.

---

## 5. Data Retention & Your Right to Deletion
* **Account Deletion:** You can request deletion of your account, solve history, saved plans, squad memberships and points directly inside the extension by going to **Settings (⚙️) &rarr; Danger Zone &rarr; Delete Account**.
* **Deletion Scope:** Successful account deletion removes associated account data from the active application database. Transfer or delete groups you own first. Security rate-limit records and infrastructure logs/backups may be retained separately for operational purposes; deletion is not a promise of immediate erasure from provider backups or every browser cache.

---

## 6. Security Measures
We implement industry-standard safeguards to protect your personal information:
* All communication between the Chrome Extension and backend servers is encrypted in transit using Transport Layer Security (HTTPS/TLS).
* Passwords are salted and cryptographically hashed.
* Password reset tokens are short-lived 6-digit numeric codes that expire after 15 minutes. Resending invalidates the previous code, a 60-second resend cooldown applies, and each code permits at most five incorrect verification attempts. Request and verification rate limits also apply.

---

## 7. Third-Party Disclaimer (LeetCode LLC)
LeetStreak is an independent open-source project and is **not affiliated, associated, authorized, endorsed by, or in any way officially connected with LeetCode LLC** or any of its subsidiaries or affiliates. The name "LeetCode" as well as related names, marks, emblems, and images are registered trademarks of their respective owners.

---

## 8. Changes to This Privacy Policy
We may periodically update this Privacy Policy to reflect feature additions or regulatory requirements. Any modifications will be posted here with an updated "Last Updated" date.

---

## 9. Contact Us
If you have any questions, concerns, or requests regarding this Privacy Policy or your personal data, please contact:
* **Project:** LeetStreak Open Source
* **GitHub Repository:** [https://github.com/youngcaptainkeos/Leetcode-Leetstreak](https://github.com/youngcaptainkeos/Leetcode-Leetstreak)
* **Support & Inquiries:** [GitHub Issues](https://github.com/youngcaptainkeos/Leetcode-Leetstreak/issues)
