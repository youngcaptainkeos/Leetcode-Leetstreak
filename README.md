# LeetStreak

A Chrome extension + backend that tracks a friend group's LeetCode
consistency: daily streaks, a weekly leaderboard, and a "who's showing up"
score instead of just raw problem counts.

```
leetstreak/
  backend/     FastAPI + PostgreSQL API, polls LeetCode on a schedule
  extension/   React + TypeScript Chrome extension (Manifest V3)
```

---

## 1. Backend setup

### Prerequisites
- Python 3.10+
- Docker (for Postgres) — or a local Postgres install if you'd rather not use Docker

### 1a. Start the database

```bash
cd backend
docker compose up -d
```

This starts Postgres on `localhost:5432` with user/password/db all set to
`codestreak` (see `docker-compose.yml`). Data persists in a Docker volume
across restarts.

> No Docker? Install Postgres locally, create a database and user matching
> `.env.example`, or edit `DATABASE_URL` to match whatever you create.

### 1b. Install and run the API

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # defaults already match docker-compose.yml

uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on first startup (`Base.metadata.create_all`
in `app/main.py`) — no separate migration step for this MVP.

Check it's alive:

```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

A background job polls every registered user's recent LeetCode activity
every 15 minutes (configurable via `POLL_INTERVAL_MINUTES` in `.env`), and
also runs once immediately on startup. You can also trigger it manually:

```bash
curl -X POST http://localhost:8000/api/admin/poll-now
```

Interactive API docs: http://localhost:8000/docs

---

## 2. Extension setup

### Prerequisites
- Node 18+

```bash
cd extension
npm install
npm run build
cp manifest.json dist/manifest.json
```

Then load it in Chrome:

1. Go to `chrome://extensions`
2. Turn on **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/dist` folder

Click the CodeStreak icon (you may need to pin it from the puzzle-piece
menu) to open the popup.

### Using it

1. Enter your name and your **public** LeetCode username, click Connect.
   The backend validates the username exists and immediately backfills
   your last ~20 accepted submissions so the dashboard isn't empty.
2. Have each friend do the same, on their own machine, pointed at the same
   backend (see below for running this on a real network instead of just
   `localhost`).
3. Hit **Sync now** in the popup any time to poll immediately instead of
   waiting for the 15-minute background job.

### Running it for a real friend group (not just your own machine)

Right now `API_BASE` in `extension/src/lib/api.ts` points at
`http://localhost:8000/api`, which only works for the person running the
backend. For friends on other machines to see the same leaderboard, deploy
the backend somewhere reachable (Render, Railway, Fly.io, a VPS — all have
free/cheap tiers that work fine for this), then:

1. Update `API_BASE` in `extension/src/lib/api.ts` to your deployed URL.
2. Update `host_permissions` in `extension/manifest.json` to match.
3. Rebuild (`npm run build`) and reload the unpacked extension.
4. Share the built `dist` folder (or publish to the Chrome Web Store) with
   your friends.

---

## 3. How the data pipeline works

LeetCode has no official API. The backend calls the same unofficial public
GraphQL endpoint the leetcode.com website itself uses
(`recentAcSubmissionList`), which returns each user's ~20 most recent
accepted submissions with timestamps — no auth needed for public profiles.

Because it's only the *recent* list, not full history:
- Streak/activity data only starts accumulating from whenever a user
  registers (plus whatever's in their last ~20 solves at that moment).
- The poller dedupes against a `solves` table so re-submitting an already-
  solved problem never double-counts it.
- This is an unofficial endpoint — it could change or start rate-limiting
  without notice. Fine for a friend-group tool, not something to build a
  product on top of.

---

## 4. Limitations & next steps

Deliberately left out of this MVP, in rough priority order for a v2:

- **Auth** — anyone who knows the backend URL can register any LeetCode
  username. Fine for a trusted friend group; add real login (e.g. Google
  OAuth) before opening this up further.
- **Multiple groups / invite codes** — everyone registered is on one
  shared leaderboard right now.
- **Difficulty breakdown, monthly heatmap, weekly challenges, nudges** —
  the original feature list; straightforward to add once the core loop
  (register → poll → streak → leaderboard) is working.
- **Anti-gaming checks** — no guard yet against someone dumping a backlog
  of old solves at once and spiking the board.
