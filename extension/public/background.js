// LeetStreak Background Service Worker for Native Chrome Desktop Solve Notifications

const DEFAULT_API_URL = "https://leetcode-leetstreak.onrender.com";

async function getApiBaseUrl() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["api_url"], (result) => {
      resolve(result.api_url || DEFAULT_API_URL);
    });
  });
}

async function checkNewSolves() {
  try {
    const storageData = await new Promise((resolve) => {
      chrome.storage.local.get(["user", "api_url", "last_notified_solve"], resolve);
    });

    const currentUser = storageData.user;
    if (!currentUser) return; // User not logged in

    const baseUrl = storageData.api_url || DEFAULT_API_URL;
    const response = await fetch(`${baseUrl}/api/feed/recent-solves?limit=10`);
    if (!response.ok) return;

    const feed = await response.json();
    if (!feed || !Array.isArray(feed) || feed.length === 0) return;

    const latestSolve = feed[0];
    const currentSolveKey = `${latestSolve.user_handle}-${latestSolve.title_slug}-${latestSolve.solved_at}`;
    const lastNotifiedKey = storageData.last_notified_solve;

    if (lastNotifiedKey !== currentSolveKey) {
      // Trigger notification if solve is from a friend / another user
      if (latestSolve.user_id !== currentUser.id) {
        chrome.notifications.create(
          `solve|${latestSolve.leetcode_url}|${Date.now()}`,
          {
            type: "basic",
            iconUrl: "icon48.png",
            title: "🔥 LeetStreak Solve Alert!",
            message: `${latestSolve.user_name} (@${latestSolve.user_handle}) just solved "${latestSolve.title}" on LeetCode!`,
            priority: 2
          }
        );
      }
      await new Promise((resolve) => {
        chrome.storage.local.set({ last_notified_solve: currentSolveKey }, resolve);
      });
    }
  } catch (err) {
    console.error("LeetStreak background check error:", err);
  }
}

// Alarm Listener (runs every 1 minute)
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "check_solves_alarm") {
    checkNewSolves();
  }
});

// Setup alarm on startup / install
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("check_solves_alarm", { periodInMinutes: 1 });
  checkNewSolves();
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("check_solves_alarm", { periodInMinutes: 1 });
  checkNewSolves();
});

// Handle Notification Click to open problem on LeetCode
chrome.notifications.onClicked.addListener((notificationId) => {
  if (notificationId.startsWith("solve|")) {
    const parts = notificationId.split("|");
    const leetcodeUrl = parts[1];
    if (leetcodeUrl) {
      chrome.tabs.create({ url: leetcodeUrl });
    }
  }
});
