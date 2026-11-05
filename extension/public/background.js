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
