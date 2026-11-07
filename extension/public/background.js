// Friend notifications are deferred. No demo identities or production test hooks.
const API_ORIGIN = "https://codestreak-api.onrender.com";

async function keepAlivePing() {
  try { await fetch(`${API_ORIGIN}/api/health`); } catch { /* Retry on the next alarm. */ }
}

function checkBackgroundUpdate() {
  if (!chrome.runtime.requestUpdateCheck) return;
  chrome.runtime.requestUpdateCheck(status => {
    if (chrome.runtime.lastError) return;
    if (status === "update_available") chrome.runtime.reload();
  });
}

function configureAlarms() {
  // Retire the old global-feed polling/demo notification path.
  chrome.alarms.clear("check_solves_alarm");
  chrome.alarms.create("keep_alive_alarm", { periodInMinutes: 10 });
  chrome.alarms.create("extension_update_alarm", { periodInMinutes: 60 });
  void keepAlivePing();
}
chrome.runtime.onInstalled.addListener(configureAlarms);
chrome.runtime.onStartup.addListener(configureAlarms);
chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === "keep_alive_alarm") void keepAlivePing();
  if (alarm.name === "extension_update_alarm") checkBackgroundUpdate();
});

// Only extension pages can hand off a manual sync. Content scripts cannot use
// this handler to submit arbitrary URLs, credentials, accounts or HTTP methods.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "leetstreak:start-sync") return;
  if (sender.id !== chrome.runtime.id || !sender.url?.startsWith(chrome.runtime.getURL(""))) {
    sendResponse({ ok: false, status: 403, message: "This Sync request is not allowed." });
    return;
  }
  void (async () => {
    const stored = await chrome.storage.local.get(["codestreak_user_id", "codestreak_access_token"]);
    const userId = Number(stored.codestreak_user_id);
    if (!Number.isSafeInteger(userId) || userId <= 0 || message.userId !== userId || !stored.codestreak_access_token) {
      return { ok: false, status: 401, message: "Please sign in again." };
    }
    // Only the quick enqueue request runs here. Long work belongs to the server.
    const response = await fetch(`${API_ORIGIN}/api/users/${userId}/sync-jobs`, {
      method: "POST", headers: { Authorization: `Bearer ${stored.codestreak_access_token}`, "Content-Type": "application/json" },
      signal: AbortSignal.timeout(20000),
    });
    const body = await response.json().catch(() => ({}));
    if (response.ok) return { ok: true, job: body.job };
    const raw = response.headers.get("Retry-After");
    const parsed = raw && /^\d+$/.test(raw.trim()) ? Number(raw) : raw ? Math.ceil((Date.parse(raw) - Date.now()) / 1000) : 60;
    const wait = Number.isFinite(parsed) ? Math.max(1, parsed) : 60;
    if (response.status === 429 || response.status === 503) {
      await chrome.storage.local.set({ [`codestreak_account_${userId}:sync_retry_at`]: String(Date.now() + wait * 1000) });
    }
    return { ok: false, status: response.status, retryAfterSeconds: response.status === 429 || response.status === 503 ? wait : 0,
      message: typeof body.detail === "string" ? body.detail : response.status === 429 ? `Requests are temporarily limited. Please try again in ${wait} seconds.` : "The server could not start Sync. Please try again shortly." };
  })().then(result => sendResponse(result)).catch(() => sendResponse({ ok: false, status: 0,
    message: "Could not confirm that Sync started. Its status will be checked when you reopen the extension." }));
  return true;
});
