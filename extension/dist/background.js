// LeetStreak Background Service Worker: session-aware background jobs and sync coordination.
// Friend notifications are deferred. No demo identities or production test hooks.
const API_ORIGIN = "https://codestreak-api.onrender.com";

let lastSyncTimestamp = 0;
const SYNC_DEBOUNCE_MS = 10000;

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
  // Retire old unauthenticated polling alarms
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

// Observe session changes to invalidate worker state on logout
chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local") return;
  if (changes.codestreak_session_v2 || changes.codestreak_access_token) {
    const newValue = changes.codestreak_session_v2?.newValue || changes.codestreak_access_token?.newValue;
    if (!newValue) {
      lastSyncTimestamp = 0;
    }
  }
});

// Coordinate authenticated sync upon receiving unprivileged submission hints from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id) return;

  if (message?.type === "LEETSTREAK_SUBMISSION_HINT") {
    const now = Date.now();
    if (now - lastSyncTimestamp < SYNC_DEBOUNCE_MS) {
      sendResponse({ status: "debounced" });
      return;
    }
    lastSyncTimestamp = now;

    chrome.storage.local.get(["codestreak_session_v2", "codestreak_user_id", "codestreak_access_token"], async (items) => {
      let userId = null;
      let token = null;

      if (items.codestreak_session_v2) {
        try {
          const parsed = JSON.parse(items.codestreak_session_v2);
          if (parsed && parsed.version === 2 && parsed.userId && parsed.accessToken) {
            userId = parsed.userId;
            token = parsed.accessToken;
          }
        } catch (_) {}
      }

      if (!userId && items.codestreak_user_id && items.codestreak_access_token) {
        userId = parseInt(items.codestreak_user_id, 10);
        token = items.codestreak_access_token;
      }

      if (!userId || !token) {
        sendResponse({ status: "unauthenticated" });
        return;
      }

      try {
        const res = await fetch(`${API_ORIGIN}/api/users/${userId}/sync`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
        if (res.ok) {
          chrome.runtime.sendMessage({
            type: "LEETSTREAK_SYNC_COMPLETED",
            userId: userId
          }).catch(() => {});
          sendResponse({ status: "synced" });
        } else {
          sendResponse({ status: "error", code: res.status });
        }
      } catch (err) {
        sendResponse({ status: "network_error" });
      }
    });
    return true; // async sendResponse
  }
});
