// LeetStreak Content Script: Live LeetCode Submission Listener & Attempt Verifier
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

  async function handleSubmissionCheck(data) {
    if (!data || !data.state) return;
    if (data.state === "SUCCESS") {
      const titleSlug = parseSlugFromUrl();
      if (!titleSlug) return;
      await verifyProblemAttempts(titleSlug);
      setTimeout(syncAllRecentSolves, 1000);
    }
  }

  async function verifyProblemAttempts(titleSlug) {
    if (!titleSlug) return null;
    try {
      const fetchFn = origFetch || window.fetch;
      const res = await fetchFn("https://leetcode.com/graphql", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: `
            query submissionList($offset: Int!, $limit: Int!, $questionSlug: String!) {
              submissionList(offset: $offset, limit: $limit, questionSlug: $questionSlug) {
                submissions {
                  id
                  statusDisplay
                  timestamp
                }
              }
            }
          `,
          variables: { offset: 0, limit: 20, questionSlug: titleSlug }
        })
      });

      const data = await res.json();
      const subs = data?.data?.submissionList?.submissions;
      if (Array.isArray(subs) && subs.length > 0) {
        // Sort chronologically (oldest submission first)
        const sorted = [...subs].sort((a, b) => parseInt(a.timestamp) - parseInt(b.timestamp));
        const firstSub = sorted[0];
        const isFirstTry = (firstSub.statusDisplay === "Accepted" || firstSub.statusDisplay === "AC");
        return isFirstTry;
      }
    } catch (e) {
      console.warn("[LeetStreak] Error verifying submission list for", titleSlug, e);
    }
    return null;
  }

  async function syncAllRecentSolves() {
    if (typeof chrome === "undefined" || !chrome.storage || !chrome.storage.local) return;

    chrome.storage.local.get(["codestreak_user", "codestreak_attempts_map"], async (res) => {
      const user = res.codestreak_user;
      if (!user || !user.id) return;

      const attemptsMap = res.codestreak_attempts_map || {};
      const fetchFn = origFetch || window.fetch;

      try {
        const solvesResp = await fetchFn(`https://codestreak-api.onrender.com/api/users/${user.id}/recent-solves?limit=15`);
        if (!solvesResp.ok) return;
        const solves = await solvesResp.json();

        let mapChanged = false;
        for (const solve of solves) {
          const slug = solve.title_slug;
          if (!slug) continue;

          const isFirstTry = await verifyProblemAttempts(slug);
          if (isFirstTry !== null) {
            if (!attemptsMap[slug] || attemptsMap[slug].is_first_try !== isFirstTry) {
              attemptsMap[slug] = {
                is_first_try: isFirstTry,
                timestamp: Date.now(),
              };
              mapChanged = true;
            }
          }
        }

        if (mapChanged) {
          chrome.storage.local.set({ codestreak_attempts_map: attemptsMap }, () => {
            fetchFn(`https://codestreak-api.onrender.com/api/users/${user.id}/sync`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ attempts_map: attemptsMap })
            }).catch(() => {});
          });
        }
      } catch (e) {
        console.warn("[LeetStreak] Auto-sync recent solves attempts failed", e);
      }
    });
  }

  function parseSlugFromUrl() {
    const parts = window.location.pathname.split("/");
    const pIdx = parts.indexOf("problems");
    if (pIdx !== -1 && parts.length > pIdx + 1) {
      return parts[pIdx + 1];
    }
    return null;
  }

  // Auto-verify all recent solves when landing on any LeetCode page
  setTimeout(() => {
    syncAllRecentSolves();
  }, 1500);
})();
