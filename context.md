# 🧠 LeetStreak — Developer & Agent Context Guide

This document provides complete architectural, operational, and development context for AI agents and developers working on the **LeetStreak** project.

---

## 1. Project Overview & Mission

**LeetStreak** is a cross-platform browser extension (Chrome, Edge, Brave, Firefox, Safari) and companion cloud backend designed to help coders build and maintain daily LeetCode consistency.

### Key Value Props:
- **Daily Streak Tracking**: Automatically tracks active coding days with an automated 1-day grace period.
- **Fair Elo-Weighted Scoring**: Solves are scored using official ZeroTrac contest ratings, problem difficulty, acceptance rate adjustments, daily challenge bonuses (+5 pts), and streak multipliers (up to +10%).
- **Social Competition**: Real-time Global Leaderboards and custom Private Groups with 6-character invite codes.
- **Zero Privacy Friction**: Users only provide their public LeetCode handle; no passwords or session cookies required.

---

## 2. Repository Structure

```
codestreak/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entrypoint & API routes
│   │   ├── models.py                # SQLAlchemy DB models (User, Group, Solve, etc.)
│   │   ├── schemas.py               # Pydantic schemas for request/response validation
│   │   ├── auth.py                  # Password hashing & JWT authentication
│   │   ├── database.py              # Engine, SessionLocal, Base setup
│   │   ├── leetcode_client.py       # LeetCode GraphQL client for public submissions
│   │   ├── point_calculator.py      # Elo & acceptance rating scoring algorithms
│   │   ├── contest_ratings.py       # ZeroTrac rating lookup loader
│   │   ├── zerotrac_ratings.json    # Static dataset of LeetCode contest problem ratings
│   │   ├── scheduler.py             # APScheduler periodic sync job (every 15 mins)
│   │   ├── email_service.py         # Resend API email delivery (OTPs, updates)
│   │   ├── legal_pages.py           # HTML rendering for Terms and Privacy policies
│   │   └── leetstreak.zip           # Served directly by /downloads/leetstreak.zip
│   ├── Dockerfile                   # Production container definition for Render
│   ├── requirements.txt             # Python dependencies
│   └── codestreak.db                # Local development SQLite database
├── extension/
│   ├── src/
│   │   ├── App.tsx                  # Main React extension UI (tabs, modals, state)
│   │   ├── App.css                  # Core CSS design system & Material Design 3 tokens
│   │   └── main.tsx                 # React DOM mount point
│   ├── public/                      # Static extension assets (icons, images, manifest)
│   ├── dist/                        # Built production bundle folder (loaded unpacked)
│   ├── manifest.json                # Chrome Manifest V3 configuration
│   ├── package.json                 # Build scripts & node dependencies
│   └── leetcode_username_guide.png  # Guide screenshot for username helper modal
├── leetstreak.zip                   # Root distribution zip package
├── leetstreak_dist.zip              # Secondary distribution archive
├── render.yaml                      # Render Blueprint deployment configuration
├── README.md                        # User documentation & installation guide
├── PRIVACY.md / TERMS.md            # Legal and compliance documentation
└── context.md                       # This file
```

---

## 3. Standard Build, Package, & Release Workflow

When making modifications to the extension, **always** follow this complete release checklist:

### Step 1: Compile the Extension
```bash
npm --prefix extension run build
```
*What this script does (`extension/package.json`):*
1. Bundles `src/main.tsx` into `public/index-main.js` and `public/index-main.css` via esbuild.
2. Copies `manifest.json`, `index.html`, and bundled assets into `extension/dist/`.

### Step 2: Repackage Distribution Archives
All three zip file locations **must** be synchronized so that downloads from the web, the backend endpoint, and the repo are identical:
```bash
# 1. Zip the dist folder contents directly from inside extension/dist
(cd extension/dist && zip -FS -qr ../../leetstreak.zip .)

# 2. Mirror the archive to leetstreak_dist.zip and backend/app/leetstreak.zip
cp leetstreak.zip leetstreak_dist.zip
cp leetstreak.zip backend/app/leetstreak.zip
```
> ⚠️ **Critical Archive Requirement**: `manifest.json` must exist at the **root** of `leetstreak.zip`. Do not create a nested folder structure inside the zip.

### Step 3: Git Commit and Push
```bash
git add -u
git commit -m "your descriptive commit message"
git push origin main
```
> 💡 *Note: `extension/dist/` is listed in `.gitignore`, but tracked output files (`index-main.js`, `index-main.css`, and the `.zip` packages) will be staged via `git add -u`.*

### Step 4: Automatic Render Cloud Deployment
- Pushing to `origin/main` automatically triggers a Docker rebuild on Render for the `leetstreak-api` service.
- Live Base URL: `https://codestreak-api.onrender.com`
- Verify live health: `curl -s https://codestreak-api.onrender.com/api/health`
- Verify live version: `curl -s https://codestreak-api.onrender.com/api/extension/version`
- Verify package download: `curl -s -o /dev/null -w "%{http_code}\n" https://codestreak-api.onrender.com/downloads/leetstreak.zip`

---

## 4. Architecture & Key Systems

### A. Frontend (Chrome Manifest V3 Extension)
- **Framework**: React 18 with TypeScript.
- **Popup Dimensions**: Fixed at **380px** (`width: 380px; min-width: 380px; max-width: 380px;`). Standard Chrome popup height is typically capped around 600px.
- **Design Language**: Material Design 3 inspired dark aesthetic:
  - Background: `#111318`
  - Surfaces: `--surface-low: #181B22`, `--surface: #1D2028`, `--surface-highest: #2D313D`
  - Accent / Primary: `#A78BFA` (brand purple), container `#3B2D63`
  - Borders: `#363B47` or `rgba(255, 255, 255, 0.08)`
  - Typography: **Inter** (`--md-ref-typeface-plain`) for UI controls; **Outfit** (`--md-ref-typeface-brand`) for headings.

#### ⚠️ Crucial Frontend Styling Caveats:
1. **`.auth-form` Global Overrides**:
   In `extension/src/App.css`, `.auth-form label` has `display: flex !important; flex-direction: column !important; width: 100% !important;` and `.auth-form label span` has `text-transform: uppercase !important; letter-spacing: 0.6px !important;`.
   - **Rule**: Never nest custom toggles, switches, or checkbox cards inside a `<label>` in `.auth-form`.
   - Always use `<div>` containers (such as `.auth-leaderboard-card`) with pure CSS track/thumb switches (`.auth-toggle-track` and `.auth-toggle-thumb`) to prevent layout and font distortion.
2. **Username Guide Helper Modal**:
   - Modal component: `LeetcodeUsernameHelpModal` in `extension/src/App.tsx`.
   - Displays 2 numbered steps, a screenshot of the LeetCode profile card, and a Do's & Don'ts card (`✓ Enter Handle` vs `✕ Not Display Name`).
   - Width: `352px !important`, padded and centered.

### B. Backend (FastAPI + SQLAlchemy)
- **Runtime**: Python 3.11 in Docker container.
- **Databases**:
  - Production (Render): PostgreSQL (via `DATABASE_URL` environment variable).
  - Local Dev: SQLite (`codestreak.db`).
- **Background Tasks & Scheduler**:
  - `scheduler.py` uses APScheduler to trigger problem syncs for all registered users every 15 minutes.
- **Scoring Engine (`point_calculator.py`)**:
  - Contest problems: Base points = `ZeroTrac Elo / 100`.
  - Non-contest: Easy = 10, Medium = 20, Hard = 30 + acceptance rate adjustment formula.
  - Bonus multipliers: Daily problem (+5 pts), active streak booster (+1% per streak day up to +10%).
- **Email Service (`email_service.py`)**:
  - Powered by the Resend API (`RESEND_API_KEY`).
  - Supports 6-digit password reset OTPs and extension update broadcast notifications (`/api/admin/broadcast-update-email`).

---

## 5. Key API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status check |
| `POST` | `/api/auth/register` | Create user account (`name`, `username`, `email`, `password`, `enable_global_leaderboard`) |
| `POST` | `/api/auth/login` | Authenticate user and return access token |
| `POST` | `/api/auth/forgot-password/initiate` | Send 6-digit password reset code via Resend |
| `POST` | `/api/auth/forgot-password/verify` | Reset password using 6-digit OTP |
| `GET` | `/api/dashboard/{user_id}` | Fetch user streak, solve statistics, points, and breakdown |
| `POST` | `/api/sync/{user_id}` | On-demand LeetCode sync trigger |
| `GET` | `/api/groups/{user_id}` | Retrieve user squads and group leaderboards |
| `POST` | `/api/groups/create` | Create a new private group with a 6-character code |
| `POST` | `/api/groups/join` | Join an existing group using invite code |
| `PUT` | `/api/settings/{user_id}` | Update settings (e.g. toggle `global_leaderboard_enabled`) |
| `GET` | `/api/extension/version` | Serves current extension version, latest commit, and release notes |
| `GET` | `/downloads/leetstreak.zip` | Download the packaged extension `.zip` archive |
| `POST` | `/api/admin/broadcast-update-email` | Admin endpoint to notify users of new releases |

---

## 6. Development Rules & Operational Best Practices

1. **Zero Secret Leaks**:
   - Never commit API keys, personal emails, passwords, or production database credentials to git.
   - Use environment variables (`.env`) for `DATABASE_URL`, `SECRET_KEY`, and `RESEND_API_KEY`.
2. **Keep Distribution in Sync**:
   - Whenever editing frontend code in `extension/src/`, **always build and package** (`leetstreak.zip`, `leetstreak_dist.zip`, `backend/app/leetstreak.zip`) before pushing to `origin/main`.
3. **Preserve Extension Usability**:
   - Respect the 380px extension popup width. Test spacing and text wrapping to ensure elements do not overflow or cause unwanted horizontal scrollbars.
4. **Git Branching**:
   - The primary branch is `main`. All live production deployments deploy automatically from `origin/main`.
