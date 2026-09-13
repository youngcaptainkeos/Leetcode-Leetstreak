// LeetStreak Content Script: Live LeetCode Submission Listener
(function () {
  console.log("[LeetStreak] Live LeetCode submission attempt listener active.");

  const origFetch = window.fetch;
  if (origFetch) {
    window.fetch = async function (...args) {
      const response = await origFetch.apply(this, args);
      try {
        const url = typeof args[0] === "string" ? args[0] : (args[0] && args[0].url) || "";
        if (url.includes("/submissions/detail/") && url.includes("/check/")) {
          const clone = response.clone();
          clone.json().then((data) => {
            handleSubmissionCheck(data);
          }).catch(() => {});
        }
      } catch (e) {
        console.warn("[LeetStreak] Error parsing fetch response", e);
      }
      return response;
    };
  }

  function handleSubmissionCheck(data) {
    if (!data || !data.state) return;
    if (data.state === "SUCCESS") {
      const statusCode = data.status_code; // 10 = Accepted
      const titleSlug = parseSlugFromUrl();
      if (!titleSlug) return;

      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(["codestreak_attempts_map"], (result) => {
          const attemptsMap = result.codestreak_attempts_map || {};
          if (!attemptsMap[titleSlug]) {
            // Attempt #1
            const isFirstTry = (statusCode === 10);
            attemptsMap[titleSlug] = {
              is_first_try: isFirstTry,
              timestamp: Date.now(),
            };
            chrome.storage.local.set({ codestreak_attempts_map: attemptsMap });
            console.log(`[LeetStreak] Tracked 1st attempt for ${titleSlug}: ${isFirstTry ? "SUCCESS (+3 pts)" : "FAILED"}`);
          }
        });
      }
    }
  }

  function parseSlugFromUrl() {
    const parts = window.location.pathname.split("/");
    const pIdx = parts.indexOf("problems");
    if (pIdx !== -1 && parts.length > pIdx + 1) {
      return parts[pIdx + 1];
    }
    return null;
  }
})();
