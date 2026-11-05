import plans from "../data/study-plans.json";

// Public studyPlanV2Detail snapshots from LeetCode, retrieved 2026-11-05.
// Bundled so the complete question lists remain available offline.
export const STUDY_PLANS = plans;
export const PRACTICE_REFRESH = "leetstreak:practice-refresh";
export interface Submission { title: string; titleSlug: string; timestamp: string }
export interface PracticeSnapshot {
  daily: { date: string; title: string; slug: string };
  submissions: Submission[];
  checkedAt: number;
}
export interface ProgressState { followed: string[]; manual: string[]; observed: string[] }
export const emptyProgress = (): ProgressState => ({ followed: [], manual: [], observed: [] });

export function readProgress(raw: string | null): ProgressState {
  try {
    const parsed = JSON.parse(raw || "{}");
    const strings = (value: unknown): string[] => Array.isArray(value)
      ? [...new Set(value.filter((s): s is string => typeof s === "string"))] : [];
    return { followed: strings(parsed.followed).filter(slug => plans.some(p => p.slug === slug)), manual: strings(parsed.manual), observed: strings(parsed.observed) };
  } catch { return emptyProgress(); }
}

export function progressKey(userId: number, username: string) {
  return `codestreak_progress_v1_${userId}_${username.toLowerCase()}`;
}

export function dailySolved(snapshot: PracticeSnapshot): boolean {
  return snapshot.submissions.some(s => {
    const timestamp = Number(s.timestamp) * 1000;
    return s.titleSlug === snapshot.daily.slug && Number.isFinite(timestamp) &&
      new Date(timestamp).toISOString().slice(0, 10) === snapshot.daily.date;
  });
}

function validSubmissions(rows: Submission[]): Submission[] {
  return rows.filter(s => typeof s?.title === "string" && typeof s.titleSlug === "string" &&
    /^[a-z0-9-]+$/.test(s.titleSlug) && Number.isFinite(Number(s.timestamp)) &&
    Number(s.timestamp) > 0 && Number(s.timestamp) * 1000 < 8640000000000000);
}

export function planCounts(plan: typeof plans[number], state: ProgressState) {
  const solved = new Set([...state.observed, ...state.manual]);
  const questions = [...new Map(plan.planSubGroups.flatMap(g => g.questions).map(q => [q.titleSlug, q])).values()];
  const done = questions.filter(q => solved.has(q.titleSlug)).length;
  return { done, total: questions.length, percent: Math.round(done / questions.length * 100), next: questions.find(q => !solved.has(q.titleSlug)) };
}

async function graphql<T>(query: string, variables: Record<string, unknown>): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 14000);
  try {
    // Public profile data only. Never attach LeetCode cookies or session tokens.
    const response = await fetch("https://leetcode.com/graphql/", {
      method: "POST", credentials: "omit", signal: controller.signal,
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query, variables }),
    });
    if (!response.ok) throw new Error("LeetCode is unavailable. Try refreshing in a moment.");
    const body = await response.json();
    if (body.errors || !body.data) throw new Error("LeetCode could not return public activity. Try again shortly.");
    return body.data;
  } finally { clearTimeout(timeout); }
}

const snapshots = new Map<string, PracticeSnapshot>();
const pending = new Map<string, Promise<PracticeSnapshot>>();
export async function fetchPractice(username: string, force = false): Promise<PracticeSnapshot> {
  const key = username.toLowerCase();
  const cached = snapshots.get(key);
  const today = new Date().toISOString().slice(0, 10);
  if (!force && cached && cached.daily.date === today && Date.now() - cached.checkedAt < 15000) return cached;
  const existing = pending.get(key);
  if (existing) return existing;
  const task = (async () => {
    const result = await graphql<{
      activeDailyCodingChallengeQuestion: { date: string; question: { title: string; titleSlug: string } };
      recentAcSubmissionList: Submission[] | null;
    }>(`query practiceSnapshot($username: String!) {
      activeDailyCodingChallengeQuestion { date question { title titleSlug } }
      recentAcSubmissionList(username: $username, limit: 100) { title titleSlug timestamp }
    }`, { username });
    const daily = result.activeDailyCodingChallengeQuestion;
    if (!daily?.question?.titleSlug || !daily.date || !Array.isArray(result.recentAcSubmissionList)) {
      throw new Error("Public practice data is unavailable for this profile.");
    }
    const value = { daily: { date: daily.date, title: daily.question.title, slug: daily.question.titleSlug }, submissions: validSubmissions(result.recentAcSubmissionList), checkedAt: Date.now() };
    snapshots.set(key, value);
    return value;
  })();
  pending.set(key, task);
  try { return await task; } finally { pending.delete(key); }
}

export async function fetchFriendSubmissions(username: string): Promise<Submission[]> {
  const result = await graphql<{ recentAcSubmissionList: Submission[] | null }>(
    `query friendPractice($username: String!) { recentAcSubmissionList(username: $username, limit: 3) { title titleSlug timestamp } }`, { username });
  if (!Array.isArray(result.recentAcSubmissionList)) throw new Error("This public profile is unavailable.");
  return validSubmissions(result.recentAcSubmissionList);
}
