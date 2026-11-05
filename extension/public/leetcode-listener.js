// LeetStreak Content Script: Listens for page bridge events and forwards unprivileged hints to background
(function () {
  // Inject page bridge into the main world if not already present
  try {
    const s = document.createElement("script");
    s.src = chrome.runtime.getURL("leetcode-page-bridge.js");
    s.onload = () => s.remove();
    (document.head || document.documentElement).appendChild(s);
  } catch (_) {}

  // Listen for validated messages from the page bridge
  window.addEventListener("message", (event) => {
    if (event.origin !== "https://leetcode.com") return;
    if (event.data?.source !== "leetstreak-page-bridge") return;
    if (event.data?.type !== "LEETSTREAK_SUBMISSION_ACCEPTED") return;

    // Send a narrow, unprivileged hint message to background.js
    if (typeof chrome !== "undefined" && chrome.runtime?.sendMessage) {
      chrome.runtime.sendMessage({
        type: "LEETSTREAK_SUBMISSION_HINT",
        platform: "leetcode"
      }).catch(() => {});
    }
  });

  // DOM observer fallback for SPA / submission result modals
  let lastObservedSolve = 0;
  const observer = new MutationObserver(() => {
    const now = Date.now();
    if (now - lastObservedSolve < 15000) return; // 15s throttle
    const resultElem = document.querySelector('[data-e2e-locator="submission-result"]');
    if (resultElem && resultElem.textContent && resultElem.textContent.includes("Accepted")) {
      lastObservedSolve = now;
      if (typeof chrome !== "undefined" && chrome.runtime?.sendMessage) {
        chrome.runtime.sendMessage({
          type: "LEETSTREAK_SUBMISSION_HINT",
          platform: "leetcode"
        }).catch(() => {});
      }
    }
  });

  try {
    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true
    });
  } catch (_) {}
})();
