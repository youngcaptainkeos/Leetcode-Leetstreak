"""HTML templates for public Legal and Compliance pages (Privacy Policy, Terms of Service/EULA)."""

BASE_CSS = """
:root {
  --bg: #0b0f19;
  --card-bg: #131b2e;
  --card-border: #1e293b;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --accent: #f97316;
  --accent-glow: rgba(249, 115, 22, 0.15);
  --accent-light: #fb923c;
  --link: #38bdf8;
  --code-bg: #1e293b;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg);
  color: var(--text-main);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.65;
  font-size: 15px;
  -webkit-font-smoothing: antialiased;
}

.header-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(11, 15, 25, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--card-border);
  padding: 14px 24px;
}

.nav-container {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-main);
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.3px;
}

.brand-flame {
  font-size: 20px;
  filter: drop-shadow(0 0 8px rgba(249, 115, 22, 0.5));
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 18px;
}

.nav-link {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: color 0.15s;
}

.nav-link:hover, .nav-link.active {
  color: var(--accent-light);
}

.content-container {
  max-width: 860px;
  margin: 40px auto 60px auto;
  padding: 0 20px;
}

.legal-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 14px;
  padding: 40px 36px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

@media (max-width: 640px) {
  .legal-card {
    padding: 24px 18px;
  }
}

.badge-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  background: var(--accent-glow);
  color: var(--accent-light);
  border: 1px solid rgba(249, 115, 22, 0.3);
}

.effective-date {
  color: var(--text-dim);
  font-size: 12px;
}

h1 {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 12px;
  color: #ffffff;
}

.lead-p {
  color: var(--text-muted);
  font-size: 15px;
  margin-bottom: 28px;
  line-height: 1.6;
}

hr {
  border: 0;
  height: 1px;
  background: var(--card-border);
  margin: 32px 0;
}

h2 {
  font-size: 19px;
  font-weight: 700;
  color: #f1f5f9;
  margin-top: 30px;
  margin-bottom: 14px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

h3 {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  margin-top: 20px;
  margin-bottom: 8px;
}

p, ul, ol {
  color: var(--text-muted);
  margin-bottom: 16px;
}

ul, ol {
  padding-left: 24px;
}

li {
  margin-bottom: 8px;
}

strong {
  color: #f8fafc;
}

a {
  color: var(--link);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

.highlight-box {
  background: rgba(30, 41, 59, 0.7);
  border-left: 4px solid var(--accent);
  border-radius: 0 8px 8px 0;
  padding: 14px 18px;
  margin: 20px 0;
  color: #cbd5e1;
  font-size: 14px;
}

.footer {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--card-border);
  color: var(--text-dim);
  font-size: 12px;
  text-align: center;
  line-height: 1.6;
}
"""

PRIVACY_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Privacy Policy - LeetStreak</title>
  <meta name="description" content="Privacy Policy for LeetStreak Chrome Extension and cloud sync backend.">
  <style>{BASE_CSS}</style>
</head>
<body>
  <header class="header-nav">
    <div class="nav-container">
      <a href="/" class="brand-link">
        <span class="brand-flame">🔥</span>
        <span>LeetStreak</span>
      </a>
      <nav class="nav-links">
        <a href="/privacy" class="nav-link active">Privacy Policy</a>
        <a href="/terms" class="nav-link">Terms & EULA</a>
        <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak" target="_blank" rel="noreferrer" class="nav-link">GitHub ↗</a>
      </nav>
    </div>
  </header>

  <main class="content-container">
    <article class="legal-card">
      <div class="badge-row">
        <span class="badge">Compliance & Privacy</span>
        <span class="effective-date">Effective: October 11, 2026 • Last Updated: October 11, 2026</span>
      </div>

      <h1>Privacy Policy for LeetStreak</h1>
      <p class="lead-p">
        LeetStreak (&ldquo;we&rdquo;, &ldquo;our&rdquo;, or &ldquo;us&rdquo;) provides a browser extension and cloud synchronization service designed to help competitive programming enthusiasts track daily practice consistency, maintain streaks, and engage on leaderboards with friends.
      </p>

      <p class="lead-p">
        This Privacy Policy explains how we collect, use, store, and safeguard your information when you use the LeetStreak Chrome Extension and associated backend API services (<code>codestreak-api.onrender.com</code>).
      </p>

      <hr>

      <h2>1. Single Purpose Statement</h2>
      <p>
        LeetStreak exists solely to track public LeetCode problem-solving activity, calculate consistency streaks and weighted skill points, and display comparative leaderboards for friends and public participants. We collect only the minimum data strictly required to achieve this core functionality.
      </p>

      <h2>2. Information We Collect</h2>

      <h3>A. Information You Provide Directly</h3>
      <ul>
        <li><strong>Display Name:</strong> Used to identify your profile within groups and leaderboard rankings.</li>
        <li><strong>Email Address:</strong> Used for account authentication, password recovery (via 6-digit verification codes), and optional critical update notices.</li>
        <li><strong>Account Password:</strong> Stored exclusively in irreversibly hashed form using strong cryptographic hashing (PBKDF2/Bcrypt). We cannot read your plaintext password.</li>
        <li><strong>LeetCode Public Username:</strong> Used to query public problem submission histories from LeetCode. <strong>We never ask for, collect, or store your LeetCode password or session cookies.</strong></li>
      </ul>

      <h3>B. Information Synchronized Automatically</h3>
      <ul>
        <li><strong>Public Solve Records:</strong> Problem titles, difficulty levels (Easy, Medium, Hard), acceptance rates, and submission timestamps retrieved from LeetCode's public GraphQL endpoints.</li>
        <li><strong>Leaderboard Preferences:</strong> Whether you have opted into the public Global Leaderboard or chosen private friends-only mode.</li>
        <li><strong>Social Interactions:</strong> Kudos counts sent and received across 24-hour cycles.</li>
      </ul>

      <h3>C. Information We DO NOT Collect</h3>
      <ul>
        <li>We do <strong>not</strong> collect your browsing history, cookies, personal tabs, IP locations, device hardware IDs, or biometric data.</li>
        <li>We do <strong>not</strong> collect payment or financial information.</li>
        <li>We do <strong>not</strong> monitor your activity on any website other than public LeetCode submission records requested explicitly for synchronization.</li>
      </ul>

      <hr>

      <h2>3. How We Use Your Information</h2>
      <ul>
        <li>To compute daily streaks, weekly totals, and contest-rating-weighted point scores.</li>
        <li>To render private friend squad leaderboards and the optional platform Global Leaderboard.</li>
        <li>To deliver password reset emails when requested.</li>
        <li>To cache leaderboard state locally in Chrome storage for instantaneous offline responsiveness.</li>
      </ul>

      <h2>4. Data Sharing and Transfer</h2>
      <div class="highlight-box">
        <strong>Strict Privacy Commitment:</strong> We do not sell, rent, monetize, or trade your personal data or activity logs to third parties, advertising brokers, or data aggregators.
      </div>
      <ul>
        <li><strong>No Third-Party Advertising:</strong> LeetStreak does not display third-party advertisements or tracking pixels.</li>
        <li><strong>Infrastructure Service Providers:</strong> Your data is processed securely through standard cloud hosting providers (Render, PostgreSQL, transactional email delivery) strictly to operate the service.</li>
      </ul>

      <h2>5. Data Retention &amp; Your Right to Deletion</h2>
      <ul>
        <li><strong>Self-Service Account Deletion:</strong> You have complete autonomy over your data. You can permanently delete your account, solve history, squad memberships, and points at any time directly inside the extension by navigating to <strong>Settings (⚙️) &rarr; Danger Zone &rarr; Delete Account</strong>.</li>
        <li><strong>Immediate Purge:</strong> Upon deletion, your account and all associated records are permanently erased from our active database.</li>
      </ul>

      <h2>6. Security Safeguards</h2>
      <ul>
        <li>All communication between the Chrome Extension and backend servers is encrypted in transit using Transport Layer Security (HTTPS/TLS).</li>
        <li>Passwords are salted and cryptographically hashed.</li>
        <li>Password reset tokens are short-lived 6-digit numeric codes that expire after 10 minutes.</li>
      </ul>

      <h2>7. Third-Party Disclaimer (LeetCode LLC)</h2>
      <p>
        LeetStreak is an independent open-source project and is <strong>not affiliated, associated, authorized, endorsed by, or in any way officially connected with LeetCode LLC</strong> or any of its subsidiaries or affiliates. The name &ldquo;LeetCode&rdquo; as well as related names, marks, emblems, and images are registered trademarks of their respective owners.
      </p>

      <h2>8. Changes to This Privacy Policy</h2>
      <p>
        We may periodically update this Privacy Policy to reflect feature additions or regulatory requirements. Any modifications will be posted here with an updated &ldquo;Last Updated&rdquo; date.
      </p>

      <h2>9. Contact Us</h2>
      <p>
        If you have questions, concerns, or requests regarding this Privacy Policy or your personal data, please contact:
      </p>
      <ul>
        <li><strong>Project Maintainer:</strong> Shashank</li>
        <li><strong>Email:</strong> <a href="mailto:support@leetstreak.com">support@leetstreak.com</a> / <a href="mailto:shashu2804@gmail.com">shashu2804@gmail.com</a></li>
        <li><strong>GitHub Repository:</strong> <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak" target="_blank" rel="noreferrer">github.com/youngcaptainkeos/Leetcode-Leetstreak</a></li>
      </ul>

      <footer class="footer">
        LeetStreak &copy; 2026. Licensed under the MIT License.<br>
        LeetCode is a trademark of LeetCode LLC. LeetStreak is an independent open-source tool.
      </footer>
    </article>
  </main>
</body>
</html>
"""

TERMS_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Terms of Service & EULA - LeetStreak</title>
  <meta name="description" content="Terms of Service and End User License Agreement for LeetStreak.">
  <style>{BASE_CSS}</style>
</head>
<body>
  <header class="header-nav">
    <div class="nav-container">
      <a href="/" class="brand-link">
        <span class="brand-flame">🔥</span>
        <span>LeetStreak</span>
      </a>
      <nav class="nav-links">
        <a href="/privacy" class="nav-link">Privacy Policy</a>
        <a href="/terms" class="nav-link active">Terms & EULA</a>
        <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak" target="_blank" rel="noreferrer" class="nav-link">GitHub ↗</a>
      </nav>
    </div>
  </header>

  <main class="content-container">
    <article class="legal-card">
      <div class="badge-row">
        <span class="badge">Legal Agreement</span>
        <span class="effective-date">Effective: October 11, 2026 • Last Updated: October 11, 2026</span>
      </div>

      <h1>Terms of Service &amp; End User License Agreement (EULA)</h1>
      <p class="lead-p">
        Please read these Terms of Service and End User License Agreement (&ldquo;Agreement&rdquo;, &ldquo;Terms&rdquo;) carefully before installing or using the <strong>LeetStreak</strong> browser extension or associated backend application services (&ldquo;Service&rdquo;, &ldquo;Software&rdquo;).
      </p>

      <p class="lead-p">
        By creating an account, installing the extension, or accessing the Service, you agree to be bound by these Terms. If you do not agree to these Terms, do not install or use the Service.
      </p>

      <hr>

      <h2>1. License Grant</h2>
      <p>
        Subject to these Terms, LeetStreak grants you a personal, non-exclusive, non-transferable, revocable license to download, install, and use the extension for personal, non-commercial educational and competitive tracking purposes. The source code is licensed under the permissive <strong>MIT License</strong>, subject to the conditions outlined in the repository's <code>LICENSE</code> file.
      </p>

      <h2>2. Permitted Use and Community Conduct</h2>
      <p>You agree to use LeetStreak responsibly and in good faith:</p>
      <ul>
        <li><strong>Authentic Handles:</strong> You agree to link only your own LeetCode account handle or handles you have legitimate permission to track.</li>
        <li><strong>No Abuse or Botting:</strong> You shall not attempt to artificially manipulate points, spam kudos requests, launch denial-of-service attacks, or bypass API security controls.</li>
        <li><strong>Respectful Groups:</strong> You agree not to create groups, handles, or display names containing abusive, harassing, defamatory, or unlawful language.</li>
      </ul>
      <p>We reserve the right to suspend, reset, or terminate any account or group found violating these guidelines.</p>

      <h2>3. Intellectual Property &amp; Third-Party Trademark Notice</h2>
      <ul>
        <li><strong>LeetStreak Assets:</strong> The LeetStreak brand, original interface designs, custom icons, and codebase are the intellectual property of the project maintainers and contributors.</li>
        <li><strong>LeetCode Disclaimer:</strong> <strong>LeetStreak is an independent open-source tool and is not affiliated, associated, authorized, endorsed by, or in any official way connected with LeetCode LLC</strong> or any of its subsidiaries. All references to &ldquo;LeetCode&rdquo;, problem slugs, and logos are for descriptive and nominative identification purposes only.</li>
      </ul>

      <h2>4. Availability &amp; &ldquo;As-Is&rdquo; Warranty</h2>
      <div class="highlight-box">
        The Service is provided <strong>&ldquo;AS IS&rdquo;</strong> and <strong>&ldquo;AS AVAILABLE&rdquo;</strong>, without warranty of any kind, express or implied.
      </div>
      <ul>
        <li>We do not guarantee uninterrupted uptime, error-free operation, or compatibility with future updates to LeetCode's public APIs or browser updates.</li>
        <li>We are not responsible for any streak loss, missed synchronization windows, or scoring discrepancies resulting from upstream LeetCode downtime or network interruption.</li>
      </ul>

      <h2>5. Limitation of Liability</h2>
      <p>
        To the maximum extent permitted by applicable law, in no event shall the authors, maintainers, or contributors of LeetStreak be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, loss of data, loss of goodwill, or service interruption) arising out of or in connection with the use or inability to use the Software.
      </p>

      <h2>6. Account Deletion and Termination</h2>
      <ul>
        <li>You may terminate your agreement with LeetStreak at any time by deleting your account via the in-app Settings menu (<strong>Settings &rarr; Danger Zone &rarr; Delete Account</strong>) and uninstalling the extension.</li>
        <li>We reserve the right to terminate or restrict access to any user whose activity threatens the stability or security of the Service.</li>
      </ul>

      <h2>7. Governing Law and Severability</h2>
      <p>
        These Terms shall be interpreted in accordance with applicable laws without regard to conflict of law principles. If any provision of these Terms is deemed invalid or unenforceable, that provision will be limited or eliminated to the minimum extent necessary, and the remaining provisions will remain in full force.
      </p>

      <h2>8. Contact &amp; Inquiries</h2>
      <p>For questions regarding these Terms or the EULA, please reach out to:</p>
      <ul>
        <li><strong>Maintainer:</strong> Shashank</li>
        <li><strong>Email:</strong> <a href="mailto:support@leetstreak.com">support@leetstreak.com</a> / <a href="mailto:shashu2804@gmail.com">shashu2804@gmail.com</a></li>
        <li><strong>GitHub Repository:</strong> <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak" target="_blank" rel="noreferrer">github.com/youngcaptainkeos/Leetcode-Leetstreak</a></li>
      </ul>

      <footer class="footer">
        LeetStreak &copy; 2026. Licensed under the MIT License.<br>
        LeetCode is a trademark of LeetCode LLC. LeetStreak is an independent open-source tool.
      </footer>
    </article>
  </main>
</body>
</html>
"""
