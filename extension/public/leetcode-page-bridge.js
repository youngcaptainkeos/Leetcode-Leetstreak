// LeetStreak Main-World Page Bridge: monitors page-level submission check requests
(function () {
  if (window.__leetstreak_bridge_active) return;
  window.__leetstreak_bridge_active = true;

  function notifyAccepted(submissionId) {
    try {
      window.postMessage(
        {
          source: "leetstreak-page-bridge",
          type: "LEETSTREAK_SUBMISSION_ACCEPTED",
          submissionId: submissionId || null
        },
        "https://leetcode.com"
      );
    } catch (_) {}
  }

  // Intercept fetch
  const origFetch = window.fetch;
  if (origFetch) {
    window.fetch = async function (...args) {
      const response = await origFetch.apply(this, args);
      try {
        const url = typeof args[0] === "string" ? args[0] : (args[0] && args[0].url) || "";
        if (url.includes("/submissions/detail/") && url.includes("/check/")) {
          const clone = response.clone();
          clone.json().then((data) => {
            if (data && data.state === "SUCCESS" && (data.status_code === 10 || data.status_msg === "Accepted")) {
              notifyAccepted(data.submission_id);
            }
          }).catch(() => {});
        }
      } catch (_) {}
      return response;
    };
  }

  // Intercept XMLHttpRequest
  const origOpen = XMLHttpRequest.prototype.open;
  const origSend = XMLHttpRequest.prototype.send;
  if (origOpen && origSend) {
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
      this._ls_url = typeof url === "string" ? url : "";
      return origOpen.call(this, method, url, ...rest);
    };
    XMLHttpRequest.prototype.send = function (...args) {
      this.addEventListener("load", function () {
        try {
          if (this._ls_url && this._ls_url.includes("/submissions/detail/") && this._ls_url.includes("/check/")) {
            const data = JSON.parse(this.responseText);
            if (data && data.state === "SUCCESS" && (data.status_code === 10 || data.status_msg === "Accepted")) {
              notifyAccepted(data.submission_id);
            }
          }
        } catch (_) {}
      });
      return origSend.apply(this, args);
    };
  }
})();
