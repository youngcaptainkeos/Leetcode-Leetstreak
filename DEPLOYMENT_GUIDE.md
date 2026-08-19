# 🚀 CodeStreak 24/7 Hosting Guide (Render + UptimeRobot)

This guide walks you through deploying the CodeStreak backend to Render for free and keeping it active **24 hours a day with 0 downtime and 0 cold starts**.

---

## 1. Push Code to GitHub

1. Create a repository on GitHub (e.g. `codestreak`).
2. Run the following commands in your project folder to push:

```bash
git init
git add .
git commit -m "Add CodeStreak backend, extension, and deployment blueprint"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/codestreak.git
git push -u origin main
```

---

## 2. Deploy Backend on Render (Automated 1-Click Blueprint)

1. Go to [Render.com](https://render.com) and log in.
2. Click the **New +** button in the top right → Select **Blueprint**.
3. Connect your `codestreak` GitHub repository.
4. Render will automatically detect [`render.yaml`](file:///c:/PDocuments/leetcode%20tracker/codestreak/render.yaml) and create two services:
   - 🐘 **`codestreak-db`**: PostgreSQL Database
   - ⚡ **`codestreak-api`**: Python FastAPI Web Service
5. Click **Apply**.
6. Once deployed, Render will provide your public URL (e.g., `https://codestreak-api.onrender.com`).

Verify your live backend is running:
Open `https://codestreak-api.onrender.com/api/health` in your browser.
It will return: `{"status": "ok"}`

---

## 3. Keep it Active 24/7 (0 Downtime / No Sleeping)

Render's free tier goes to sleep after 15 minutes of inactivity. To keep it running **24 hours a day, 7 days a week**:

1. Go to [UptimeRobot.com](https://uptimerobot.com) (Free 24/7 monitoring).
2. Click **Add New Monitor**:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `CodeStreak 24/7 Ping`
   - **URL (or IP)**: `https://codestreak-api.onrender.com/api/health`
   - **Monitoring Interval**: `Every 5 minutes`
3. Click **Create Monitor**.

Now UptimeRobot will ping your backend every 5 minutes. Render will **never go to sleep**, giving you a 100% free, 24/7 hosted backend!

---

## 4. Point Chrome Extension to Live Backend

1. Open [`extension/src/lib/api.ts`](file:///c:/PDocuments/leetcode%20tracker/codestreak/extension/src/lib/api.ts) and set `API_BASE` to your live Render URL:

```typescript
export const API_BASE = "https://codestreak-api.onrender.com/api";
```

2. Rebuild the extension:
```bash
cd extension
npm run build
Copy-Item manifest.json dist/manifest.json
```

3. Share the built `extension/dist` folder with your friends or load it in Chrome (`chrome://extensions`).

Everyone in your friend group will now share the same live online database, create private groups, and build daily streaks 24/7!
