"""HTML templates for public Legal and Compliance pages (Privacy Policy, Terms of Service/EULA)."""

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
:root { --bg:#111318; --card-bg:#181b22; --card-border:#363b47; --text-main:#f1f5f9; --text-muted:#9ca3af; --text-dim:#6b7280; --accent:#a78bfa; --accent-glow:rgba(167,139,250,.12); --accent-light:#c4b5fd; --link:#c4b5fd; --code-bg:#252934; }
* { box-sizing:border-box; margin:0; padding:0; }
html { scroll-behavior:smooth; }
body { background:var(--bg); color:var(--text-main); font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.7; font-size:14px; -webkit-font-smoothing:antialiased; }
.header-nav { position:sticky; top:0; z-index:50; background:rgba(17,19,24,.9); backdrop-filter:blur(12px); border-bottom:1px solid rgba(255,255,255,.07); padding:24px 40px; }
.nav-container { max-width:1104px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; gap:24px; }
.brand-link { display:flex; align-items:center; gap:9px; text-decoration:none; color:var(--text-main); font-family:Outfit,Inter,sans-serif; font-weight:700; font-size:24px; letter-spacing:-1px; white-space:nowrap; }
.brand-flame { display:block; width:34px; height:38px; object-fit:contain; }
.nav-links { display:flex; align-items:center; gap:28px; }
.nav-link { position:relative; color:var(--text-muted); text-decoration:none; font-size:12px; font-weight:500; transition:color .15s; }
.nav-link:hover,.nav-link.active { color:var(--text-main); }
.nav-link.active::after { content:""; position:absolute; left:0; right:0; bottom:-12px; height:2px; border-radius:2px; background:var(--accent); }
.content-container { max-width:1104px; margin:56px auto 80px; padding:0 40px; }
.legal-card { background:radial-gradient(ellipse at 10% 0,rgba(167,139,250,.08),transparent 34%),var(--card-bg); border:1px solid var(--card-border); border-radius:20px; padding:48px 52px; box-shadow:0 28px 80px rgba(0,0,0,.22); }
.badge-row { display:flex; align-items:center; gap:12px; margin-bottom:20px; }
.badge { display:inline-block; padding:5px 11px; border-radius:9999px; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.8px; background:var(--accent-glow); color:var(--accent-light); border:1px solid rgba(167,139,250,.25); }
.effective-date { color:var(--text-dim); font-size:11px; }
h1 { font-family:Outfit,Inter,sans-serif; font-size:36px; font-weight:600; letter-spacing:-1px; line-height:1.2; margin-bottom:16px; color:var(--text-main); }
.lead-p { color:var(--text-muted); font-size:14px; margin-bottom:18px; line-height:1.85; }
hr { border:0; height:1px; background:var(--card-border); margin:34px 0; }
h2 { font-family:Outfit,Inter,sans-serif; font-size:20px; font-weight:600; color:var(--text-main); margin-top:32px; margin-bottom:14px; padding-bottom:9px; border-bottom:1px solid rgba(255,255,255,.07); }
h3 { font-size:15px; font-weight:600; color:var(--text-main); margin-top:22px; margin-bottom:9px; }
p,ul,ol { color:var(--text-muted); margin-bottom:16px; }
ul,ol { padding-left:24px; }
li { margin-bottom:8px; }
strong { color:var(--text-main); }
a { color:var(--link); text-decoration:none; transition:color .15s; }
a:hover { color:var(--text-main); text-decoration:underline; }
code { border-radius:5px; padding:2px 5px; background:var(--code-bg); color:var(--accent-light); font-size:.9em; }
.highlight-box { background:var(--accent-glow); border:1px solid rgba(167,139,250,.2); border-left:3px solid var(--accent); border-radius:12px; padding:16px 20px; margin:20px 0; color:#d6d0e6; font-size:13px; }
.footer { margin-top:48px; padding-top:24px; border-top:1px solid var(--card-border); color:var(--text-dim); font-size:11px; text-align:center; line-height:1.8; }
::selection { color:#201732; background:var(--accent); }
@media(max-width:700px) { .header-nav { padding:20px 18px; } .nav-container { align-items:flex-start; gap:18px; flex-direction:column; } .nav-links { gap:18px; flex-wrap:wrap; } .content-container { margin:30px auto 48px; padding:0 18px; } .legal-card { padding:26px 20px; border-radius:16px; } .badge-row { align-items:flex-start; flex-direction:column; gap:8px; } h1 { font-size:28px; } h2 { font-size:18px; } }
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
        <img class="brand-flame" src="/web-assets/just_logo.png" alt="">
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
        <li><strong>Project:</strong> LeetStreak Open Source</li>
        <li><strong>Inquiries &amp; Support:</strong> <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak/issues" target="_blank" rel="noreferrer">GitHub Support &amp; Inquiries</a></li>
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
        <img class="brand-flame" src="/web-assets/just_logo.png" alt="">
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
        <li><strong>Project:</strong> LeetStreak Open Source</li>
        <li><strong>Inquiries &amp; Support:</strong> <a href="https://github.com/youngcaptainkeos/Leetcode-Leetstreak/issues" target="_blank" rel="noreferrer">GitHub Support &amp; Inquiries</a></li>
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
