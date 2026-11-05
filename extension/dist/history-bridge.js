// First-party LeetCode requests also work when cross-site session cookies are blocked.
// Only the extension can request these two fixed, read-only queries.
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (sender.id !== chrome.runtime.id || message?.type !== "LEETSTREAK_HISTORY") return;
  if (message.kind === "ping") { respond({ ready: true }); return; }
  if (message.kind !== "account" && message.kind !== "page") return;
  if (message.kind === "page" && (!Number.isSafeInteger(message.skip) || message.skip < 0 || message.skip > 9900)) {
    respond({ ok: false, error: "Invalid solved-history page." }); return;
  }
  const query = message.kind === "account"
    ? "query extensionHistoryAccount { userStatus { isSignedIn username } }"
    : 'query extensionSolvedHistory($limit: Int, $skip: Int, $filters: QuestionListFilterInput) { problemsetQuestionList: questionList(categorySlug: "", limit: $limit, skip: $skip, filters: $filters) { total: totalNum questions: data { titleSlug status } } }';
  const variables = message.kind === "account" ? {} : { limit: 100, skip: message.skip, filters: { status: "AC" } };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 14000);
  fetch("https://leetcode.com/graphql/", { method: "POST", credentials: "include", signal: controller.signal, headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, variables }) })
    .then(async response => {
      if (!response.ok) throw new Error("LeetCode is unavailable.");
      const result = await response.json();
      if (result.errors || !result.data) throw new Error("LeetCode could not return solved history.");
      respond({ ok: true, data: result.data });
    })
    .catch(() => respond({ ok: false, error: "Could not read your LeetCode session. Refresh LeetCode, then retry syncing." }))
    .finally(() => clearTimeout(timeout));
  return true;
});
