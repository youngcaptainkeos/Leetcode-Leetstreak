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
    if (data.state === "SUCCESS" && data.status_code === 10) {
      if (typeof chrome !== "undefined" && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get(["codestreak_user"], (res) => {
          const user = res.codestreak_user;
          if (user && user.id) {
            const fetchFn = origFetch || window.fetch;
            fetchFn(`https://codestreak-api.onrender.com/api/users/${user.id}/sync`, {
              method: "POST"
            }).catch(() => {});
          }
        });
      }
    }
  }
})();
