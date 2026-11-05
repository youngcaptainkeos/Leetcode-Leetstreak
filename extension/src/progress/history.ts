export interface SolvedHistory { slugs: string[]; syncedAt: number }

async function findSessionTab(): Promise<number | undefined> {
  if (typeof chrome === "undefined" || !chrome.tabs?.query || !chrome.tabs?.sendMessage) return undefined;
  const tabs = await new Promise<chrome.tabs.Tab[]>(resolve => {
    chrome.tabs.query({ url: "https://leetcode.com/*" }, result => { const error = chrome.runtime.lastError; resolve(error ? [] : result); });
  });
  for (const tab of tabs) {
    if (tab.id === undefined) continue;
    const ready = await new Promise<boolean>(resolve => {
      chrome.tabs.sendMessage(tab.id!, { type: "LEETSTREAK_HISTORY", kind: "ping" }, result => { const error = chrome.runtime.lastError; resolve(!error && result?.ready === true); });
    });
    if (ready) return tab.id;
  }
  return undefined;
}

async function tabQuery<T>(tabId: number, kind: "account" | "page", skip: number, signal: AbortSignal): Promise<T> {
  if (signal.aborted) throw new DOMException("History sync cancelled", "AbortError");
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (error?: Error, data?: T) => {
      if (settled) return;
      settled = true; clearTimeout(timeout); signal.removeEventListener("abort", cancel);
      if (error) reject(error); else resolve(data!);
    };
    const cancel = () => finish(new DOMException("History sync cancelled", "AbortError"));
    const timeout = setTimeout(() => finish(new Error("LeetCode took too long to respond. Refresh its tab, then sync again.")), 16000);
    signal.addEventListener("abort", cancel, { once: true });
    chrome.tabs.sendMessage(tabId, { type: "LEETSTREAK_HISTORY", kind, skip }, result => {
      const error = chrome.runtime.lastError;
      if (error || !result?.ok || !result.data) finish(new Error("Could not read your LeetCode session. Open or refresh LeetCode, then sync again."));
      else finish(undefined, result.data);
    });
  });
}

async function sessionQuery<T>(query: string, variables: Record<string, unknown>, signal: AbortSignal, tabId?: number): Promise<T> {
  if (tabId !== undefined) return tabQuery<T>(tabId, query.includes("extensionHistoryAccount") ? "account" : "page", Number(variables.skip || 0), signal);
  const request = new AbortController();
  const cancel = () => request.abort();
  signal.addEventListener("abort", cancel, { once: true });
  if (signal.aborted) request.abort();
  const timeout = setTimeout(cancel, 14000);
  try {
    // The browser attaches its existing LeetCode session only to LeetCode.
    // No cookie or session token is read, stored, or sent to our backend.
    const response = await fetch("https://leetcode.com/graphql/", {
      method: "POST", credentials: "include", signal: request.signal,
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, variables }),
    });
    if (!response.ok) throw new Error("LeetCode is unavailable. Your saved progress is unchanged.");
    const result = await response.json();
    if (result.errors || !result.data) throw new Error("LeetCode could not return solved history. Your saved progress is unchanged.");
    return result.data;
  } finally { clearTimeout(timeout); signal.removeEventListener("abort", cancel); }
}

async function verifyAccount(username: string, signal: AbortSignal, tabId?: number): Promise<void> {
  const result = await sessionQuery<{ userStatus: { isSignedIn: boolean; username: string | null } | null }>(
    "query extensionHistoryAccount { userStatus { isSignedIn username } }", {}, signal, tabId);
  const account = result.userStatus;
  if (!account?.isSignedIn || !account.username) throw new Error(`Sign in to LeetCode as @${username} in this browser to sync your complete solved history.`);
  if (account.username.toLowerCase() !== username.trim().toLowerCase()) {
    throw new Error(`Your LeetCode session belongs to another account. Switch to @${username} on LeetCode, then sync again.`);
  }
}

const PAGE_SIZE = 100;
interface SolvedPage { total: number; questions: { titleSlug: string; status: string }[] }
async function readPage(skip: number, signal: AbortSignal, tabId?: number): Promise<SolvedPage> {
  const result = await sessionQuery<{ problemsetQuestionList: SolvedPage | null }>(
    `query extensionSolvedHistory($limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(categorySlug: "", limit: $limit, skip: $skip, filters: $filters) {
        total: totalNum questions: data { titleSlug status }
      }
    }`, { limit: PAGE_SIZE, skip, filters: { status: "AC" } }, signal, tabId);
  const page = result.problemsetQuestionList;
  if (!page || !Number.isSafeInteger(page.total) || page.total < 0 || page.total > 10000 || !Array.isArray(page.questions) ||
    page.questions.some(q => !q || typeof q.titleSlug !== "string" || !/^[a-z0-9-]{1,200}$/.test(q.titleSlug) || q.status?.toLowerCase() !== "ac")) {
    throw new Error("LeetCode returned an invalid solved list. Your saved progress is unchanged.");
  }
  return page;
}

export async function fetchSolvedHistory(username: string, onProgress?: (loaded: number, total: number) => void, signal?: AbortSignal): Promise<SolvedHistory> {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal?.addEventListener("abort", cancel, { once: true });
  if (signal?.aborted) controller.abort();
  try {
    const tabId = await findSessionTab();
    await verifyAccount(username, controller.signal, tabId);
    const first = await readPage(0, controller.signal, tabId);
    const solved = new Set(first.questions.map(q => q.titleSlug));
    onProgress?.(solved.size, first.total);
    // At most four concurrent page requests. Validate every page and reject a
    // changing or truncated result rather than saving it as complete history.
    const offsets = Array.from({ length: Math.max(0, Math.ceil(first.total / PAGE_SIZE) - 1) }, (_, i) => (i + 1) * PAGE_SIZE);
    for (let start = 0; start < offsets.length; start += 4) {
      const batch = await Promise.all(offsets.slice(start, start + 4).map(skip => readPage(skip, controller.signal, tabId)));
      for (const page of batch) {
        if (page.total !== first.total) throw new Error("Your solved list changed during sync. Retry to finish importing it.");
        page.questions.forEach(q => solved.add(q.titleSlug));
      }
      onProgress?.(solved.size, first.total);
    }
    if (solved.size !== first.total) throw new Error("LeetCode returned an incomplete solved list. Retry; your saved progress is unchanged.");
    await verifyAccount(username, controller.signal, tabId);
    if (controller.signal.aborted) throw new DOMException("History sync cancelled", "AbortError");
    return { slugs: [...solved], syncedAt: Date.now() };
  } finally { controller.abort(); signal?.removeEventListener("abort", cancel); }
}
