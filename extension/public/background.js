// LeetStreak Background Service Worker for Native Chrome Desktop Solve Notifications (MV3 Linux Compliant)

const DEFAULT_API_URL = "https://leetcode-leetstreak.onrender.com";

function openFloatingSolvePopup(userName, title, leetcodeUrl) {
  try {
    const query = `user=${encodeURIComponent(userName)}&title=${encodeURIComponent(title)}&url=${encodeURIComponent(leetcodeUrl)}`;
    chrome.windows.create(
      {
        url: `notification.html?${query}`,
        type: "popup",
        width: 380,
        height: 180,
        top: 140,
        left: 140,
        focused: true
      },
      (win) => {
        if (chrome.runtime.lastError) {
          console.error("Chrome Window Create Error:", chrome.runtime.lastError.message);
        } else {
          console.log("Floating Popup Window created successfully! ID:", win ? win.id : "unknown");
        }
      }
    );
  } catch (err) {
    console.error("Error creating floating solve popup:", err);
  }
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
        // 1. Update extension badge on toolbar icon
        if (chrome.action && chrome.action.setBadgeText) {
          chrome.action.setBadgeText({ text: "NEW" });
          chrome.action.setBadgeBackgroundColor({ color: "#FB923C" });
        }

        // 2. Native OS Desktop Notification (MV3 Promise API, relative iconUrl, priority: 0 for Linux DBus compatibility)
        chrome.notifications.create(`solve|${latestSolve.leetcode_url}|${Date.now()}`, {
          type: "basic",
          iconUrl: "icon48.png",
          title: "🔥 LeetStreak Solve Alert!",
          message: `${latestSolve.user_name} (@${latestSolve.user_handle}) just solved "${latestSolve.title}" on LeetCode!`
        }).then((id) => {
          console.log("Notification created successfully! ID:", id);
        }).catch((err) => {
          console.error("Chrome Notification Error:", err);
        });

        // 3. Mini Desktop Floating Window Popup (works even when main extension popup is closed!)
        openFloatingSolvePopup(latestSolve.user_name, latestSolve.title, latestSolve.leetcode_url);
      }

      await new Promise((resolve) => {
        chrome.storage.local.set({ last_notified_solve: currentSolveKey }, resolve);
      });
    }
  } catch (err) {
    console.error("LeetStreak background check error:", err);
  }
}

// Silent Background Extension Auto-Updater (No Notification Banners)
function checkBackgroundOtaUpdate() {
  if (chrome.runtime && chrome.runtime.requestUpdateCheck) {
    chrome.runtime.requestUpdateCheck((status) => {
      if (status === "update_available") {
        console.log("Silent OTA Update Available! Applying update and reloading extension...");
        chrome.runtime.reload();
      }
    });
  }
}

// Alarm Listener (runs every 1 minute)
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "check_solves_alarm") {
    checkNewSolves();
    checkBackgroundOtaUpdate();
  }
});

// Setup alarm on startup / install
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("check_solves_alarm", { periodInMinutes: 1 });
  checkNewSolves();
  checkBackgroundOtaUpdate();
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("check_solves_alarm", { periodInMinutes: 1 });
  checkNewSolves();
  checkBackgroundOtaUpdate();
});

// Runtime Message Listener (for testing & trigger from popup)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "TRIGGER_TEST_NOTIFICATION" || request.type === "TRIGGER_TEST_NOTIFICATION_DELAYED") {
    const delay = request.type === "TRIGGER_TEST_NOTIFICATION_DELAYED" ? 3000 : 0;

    setTimeout(() => {
      const testUser = "Sumukh Shandilya";
      const testTitle = "3Sum";
      const testUrl = "https://leetcode.com/problems/3sum";

      // 1. Update toolbar badge
      if (chrome.action && chrome.action.setBadgeText) {
        chrome.action.setBadgeText({ text: "NEW" });
        chrome.action.setBadgeBackgroundColor({ color: "#FB923C" });
      }

      // 2. Native Desktop OS Notification (MV3 Promise API with relative iconUrl and no unsupported priority)
      chrome.notifications.create(`solve|${testUrl}|${Date.now()}`, {
        type: "basic",
        iconUrl: "icon48.png",
        title: "🔥 LeetStreak Solve Alert!",
        message: `${testUser} (@Sumukh_Shandilya) just solved "${testTitle}" on LeetCode!`
      }).then((id) => {
        console.log("Test Notification created successfully with ID:", id);
      }).catch((err) => {
        console.error("Error creating native notification:", err);
      });

      // 3. Mini Desktop Floating Window Popup (works even when main extension popup is closed!)
      openFloatingSolvePopup(testUser, testTitle, testUrl);
    }, delay);

    sendResponse({ status: "scheduled", delay });
  }
  return true;
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
