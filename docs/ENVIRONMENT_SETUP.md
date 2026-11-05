# Reproducible Environment Setup Guide

This guide provides step-by-step instructions for developers and contributors to set up a clean, reproducible local development and testing environment from maintained dependency manifests.

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
- **Python**: Version 3.12 or newer (`python3 --version`)
- **Node.js**: Version 20.x or newer (`node -v`)
- **npm**: Version 10.x or newer (`npm -v`)
- **Git**: (`git --version`)
- **Optional**: PostgreSQL 16 (recommended for native migration testing; SQLite is supported out of the box for standard development and unit tests).

---

## 2. Step-by-Step Installation

### Step A: Clone the Repository
```bash
git clone https://github.com/youngcaptainkeos/Leetcode-Leetstreak.git
cd Leetcode-Leetstreak
```

### Step B: Set Up Python Virtual Environment
Create a clean virtual environment and install backend and testing dependencies:

```bash
# 1. Create a virtual environment named test_env (ignored by Git)
python3 -m venv test_env

# 2. Activate the virtual environment
source test_env/bin/activate  # On Linux/macOS
# On Windows: test_env\Scripts\activate

# 3. Upgrade pip and install maintained dependency manifests
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r backend/requirements-test.txt
```

### Step C: Install Frontend & Extension Dependencies
Install clean npm packages for both the web app and extension:

```bash
npm --prefix web ci
npm --prefix extension ci
```

---

## 3. Building & Packaging

### Build the Web Application
```bash
npm --prefix web run check
npm --prefix web run build
```
*Generated assets are compiled to `backend/web/` and are automatically ignored by Git.*

### Build and Package the Browser Extension
```bash
python3 scripts/sync_release.py --package
```
*This compiles `extension/src/`, bundles it into `extension/dist/`, generates the root `leetstreak.zip`, and synchronizes all 4 mirrored ZIP copies.*

### Verify Build and Release Consistency
```bash
python3 scripts/sync_release.py --verify
```

---

## 4. Running the Local Backend Server

Copy the example configuration and start the FastAPI server:

```bash
# 1. Ensure JWT_SECRET is set (at least 32 characters for security)
export PYTHONPATH="backend"
export JWT_SECRET="local-development-secret-key-minimum-32-chars-long"

# 2. Run with uvicorn on port 8000
python3 -m uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` in your browser. The backend serves both the web interface and API endpoints locally.

---

## 5. Configuration & Environment Variables

| Variable | Description | Default / Local Dev Value |
|---|---|---|
| `JWT_SECRET` | Signing secret for session tokens (HMAC-SHA256). | Required; set to random string >= 32 chars. |
| `DATABASE_URL` | SQLAlchemy database connection string. | `sqlite:///backend/codestreak.db` if omitted. |
| `ADMIN_SECRET` | Header secret for administrative endpoints (`X-Admin-Secret`). | Randomly generated on startup if omitted. |
| `PORT` | Listening port for the application server. | `8000` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins. | Includes localhost, Render domain, and extensions. |
| `LEETSTREAK_TEST_POSTGRES_URL` | Optional PostgreSQL URL for native migration testing. | None (skipped if unset). |
| `LEETSTREAK_CHROME_EXECUTABLE` | Optional path to Chrome binary for Playwright smoke test. | `/opt/google/chrome/chrome` if available. |

---

## 6. Running Continuous Checks

To verify your installation and all regression tests locally:

```bash
./scripts/run_checks.sh
```
