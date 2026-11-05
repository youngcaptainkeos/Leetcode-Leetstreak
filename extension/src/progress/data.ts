import plans from "../data/study-plans.json";
import strivers from "../data/strivers-a2z.json";
import { publicUrl, importedPlanSlug, fetchPublicPlan } from "./importer";

// Public studyPlanV2Detail snapshots from LeetCode, retrieved 2026-11-05.
// Bundled so the complete question lists remain available offline.
export const BUNDLED_PLANS: StudyPlan[] = plans;
export const STUDY_PLANS: StudyPlan[] = [
  strivers as StudyPlan,
  plans.find(plan => plan.slug === "top-sql-50")!,
  plans.find(plan => plan.slug === "top-interview-150")!,
];
const DEFAULTS_VERSION = 2;
export interface StudyQuestion { title: string; titleSlug: string; difficulty: string; url?: string; leetcodeSlug?: string; kind?: "learning" | "practice" }
export interface StudyPlan { name: string; slug: string; planSubGroups: { name: string; questions: StudyQuestion[] }[]; source?: "leetcode" | "takeuforward" | "codeforces" | "external"; sourceUrl?: string; snapshotDate?: string }
export const PRACTICE_REFRESH = "leetstreak:practice-refresh";
export interface Submission { title: string; titleSlug: string; timestamp: string }
export interface PracticeSnapshot {
  daily: { date: string; title: string; slug: string };
  submissions: Submission[];
  checkedAt: number;
}
export interface ProgressState { followed: string[]; manual: string[]; observed: string[]; customPlans: StudyPlan[]; hiddenPlans: string[]; defaultsVersion: number; lastFullSyncAt: number | null; codeforcesObserved: string[]; codeforcesHandle: string | null; codeforcesSyncedAt: string | null }
export const emptyProgress = (): ProgressState => ({ followed: [], manual: [], observed: [], customPlans: [], hiddenPlans: [], defaultsVersion: DEFAULTS_VERSION, lastFullSyncAt: null, codeforcesObserved: [], codeforcesHandle: null, codeforcesSyncedAt: null });

export function parsePlanSlug(input: string): string {
  let slug = input.trim();
  if (/^(?:www\.)?leetcode\.com\//i.test(slug)) slug = `https://${slug}`;
  if (slug.startsWith("https://")) {
    const url = new URL(slug);
    if (!["leetcode.com", "www.leetcode.com"].includes(url.hostname) || url.port || url.username || url.password) {
      throw new Error("Paste a study-plan link from leetcode.com.");
    }
    const match = url.pathname.match(/^\/studyplan\/([^/]+)\/?$/);
    if (!match) throw new Error("Use a link like https://leetcode.com/studyplan/30-days-of-javascript/.");
    slug = match[1];
  }
  if (slug.length > 100 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw new Error("Enter a LeetCode study-plan link or its slug, such as 30-days-of-javascript.");
  }
  return slug;
}

export function parsePlanInput(input: string): { source: "leetcode" | "takeuforward" | "codeforces" | "external"; slug: string; url?: string } {
  let raw = input.trim();
  if (raw === strivers.slug) return { source: "takeuforward", slug: strivers.slug };
  if (/^(?:www\.)?(?:takeuforward\.org|codeforces\.com)\//i.test(raw)) raw = `https://${raw}`;
  if (raw.startsWith("https://")) {
    const url = publicUrl(raw);
    if (["takeuforward.org", "www.takeuforward.org"].includes(url.hostname)) {
      const slug = url.pathname.match(/^\/prep-hub\/([a-z0-9-]+)\/?$/)?.[1];
      if (!slug) throw new Error("Use a takeUforward prep-hub sheet link.");
      return { source: "takeuforward", slug, url: url.href };
    }
    if (!["leetcode.com", "www.leetcode.com"].includes(url.hostname)) {
      return { source: /^(www\.)?codeforces\.com$/.test(url.hostname) ? "codeforces" : "external", slug: importedPlanSlug(url), url: url.href };
    }
  }
  return { source: "leetcode", slug: parsePlanSlug(raw) };
}

function isSafeSourceUrl(value: unknown): value is string {
  if (typeof value !== "string" || value.length > 1000) return false;
  try { publicUrl(value); return true; } catch { return false; }
}

export function questionUrl(question: StudyQuestion): string {
  return question.url && isSafeSourceUrl(question.url) ? question.url : `https://leetcode.com/problems/${question.titleSlug}/`;
}

export function questionLeetcodeSlug(question: StudyQuestion): string | null {
  if (question.kind === "learning") return null;
  if (question.leetcodeSlug) return question.leetcodeSlug;
  if (question.url) {
    const url = new URL(question.url);
    return ["leetcode.com", "www.leetcode.com"].includes(url.hostname) ? url.pathname.match(/^\/problems\/([a-z0-9-]+)\/?$/)?.[1] || null : null;
  }
  return question.titleSlug.startsWith("tuf-") ? null : question.titleSlug;
}

export function questionCodeforcesSlug(question: StudyQuestion): string | null {
  if (!question.url) return null;
  try {
    const url = new URL(question.url);
    if (!/^(www\.)?codeforces\.com$/.test(url.hostname)) return null;
    const match = url.pathname.match(/^\/problemset\/problem\/(\d+)\/([A-Za-z0-9]+)\/?$/) || url.pathname.match(/\/(?:contest|gym)\/(\d+)\/problem\/([A-Za-z0-9]+)\/?$/);
    return match ? `cf-${match[1]}-${match[2].toLowerCase()}` : null;
  } catch { return null; }
}
export function automaticQuestion(question: StudyQuestion, state: Pick<ProgressState, "codeforcesHandle">): boolean {
  return Boolean(questionLeetcodeSlug(question) || state.codeforcesHandle && questionCodeforcesSlug(question));
}

export function questionSolved(question: StudyQuestion, state: Pick<ProgressState, "manual" | "observed"> & Partial<Pick<ProgressState, "codeforcesHandle" | "codeforcesObserved">>): boolean {
  const slug = questionLeetcodeSlug(question);
  if (slug !== null) return state.observed.includes(slug);
  const cf = questionCodeforcesSlug(question);
  if (cf && state.codeforcesHandle) return Boolean(state.codeforcesObserved?.includes(cf));
  return state.manual.includes(question.titleSlug);
}

export function mergeSolvedHistory(state: ProgressState, slugs: string[], syncedAt: number): ProgressState {
  return { ...state, observed: [...new Set([...state.observed, ...slugs])], lastFullSyncAt: syncedAt };
}

export function readStudyPlan(value: unknown): StudyPlan | null {
  try {
    const plan = value as StudyPlan;
    if (!plan || typeof plan.name !== "string" || !plan.name.trim() || plan.name.length > 150 ||
      typeof plan.slug !== "string" || parsePlanSlug(plan.slug) !== plan.slug ||
      !Array.isArray(plan.planSubGroups) || !plan.planSubGroups.length || plan.planSubGroups.length > 200) return null;
    if (plan.source && !["leetcode", "takeuforward", "codeforces", "external"].includes(plan.source)) return null;
    if (plan.sourceUrl !== undefined && !isSafeSourceUrl(plan.sourceUrl)) return null;
    if (plan.snapshotDate !== undefined && !/^\d{4}-\d{2}-\d{2}$/.test(plan.snapshotDate)) return null;
    const groups: StudyPlan["planSubGroups"] = [];
    const seen = new Set<string>();
    const names = new Set<string>();
    let total = 0;
    for (const group of plan.planSubGroups) {
      if (!group || typeof group.name !== "string" || !group.name.trim() || group.name.length > 150 ||
        names.has(group.name) || !Array.isArray(group.questions)) return null;
      names.add(group.name);
      const questions: StudyPlan["planSubGroups"][number]["questions"] = [];
      for (const question of group.questions) {
        if (++total > 1000 || !question || typeof question.title !== "string" || !question.title.trim() || question.title.length > 300 ||
          typeof question.titleSlug !== "string" || question.titleSlug.length > 200 || !/^[a-z0-9-]+$/.test(question.titleSlug) ||
          !["EASY", "MEDIUM", "HARD", "BASIC", "CORE", "PRO", "LESSON", "PRACTICE"].includes(question.difficulty)) return null;
        if (question.url !== undefined && !isSafeSourceUrl(question.url)) return null;
        if (question.leetcodeSlug !== undefined && !/^[a-z0-9-]{1,200}$/.test(question.leetcodeSlug)) return null;
        if (question.kind !== undefined && !["learning", "practice"].includes(question.kind)) return null;
        if (plan.source && plan.source !== "leetcode" && !question.url) return null;
        if (!seen.has(question.titleSlug)) {
          seen.add(question.titleSlug);
          questions.push({ title: question.title, titleSlug: question.titleSlug, difficulty: question.difficulty, ...(question.url ? { url: question.url } : {}), ...(question.leetcodeSlug ? { leetcodeSlug: question.leetcodeSlug } : {}), ...(question.kind ? { kind: question.kind } : {}) });
        }
      }
      if (questions.length) groups.push({ name: group.name, questions });
    }
    return groups.length ? { name: plan.name.trim(), slug: plan.slug, planSubGroups: groups, ...(plan.source ? { source: plan.source } : {}), ...(plan.sourceUrl ? { sourceUrl: plan.sourceUrl } : {}), ...(plan.snapshotDate ? { snapshotDate: plan.snapshotDate } : {}) } : null;
  } catch { return null; }
}

export function readProgress(raw: string | null): ProgressState {
  try {
    const parsed = JSON.parse(raw || "{}");
    const strings = (value: unknown): string[] => Array.isArray(value)
      ? [...new Set(value.filter((s): s is string => typeof s === "string"))] : [];
    const customPlans = Array.isArray(parsed.customPlans) ? [...new Map(parsed.customPlans
      .map(readStudyPlan).filter((p: StudyPlan | null): p is StudyPlan => p !== null && !STUDY_PLANS.some(b => b.slug === p.slug))
      .map((p: StudyPlan) => [p.slug, p] as const)).values()] as StudyPlan[] : [];
    const migrateDefaults = !(Number.isSafeInteger(parsed.defaultsVersion) && parsed.defaultsVersion >= DEFAULTS_VERSION);
    // Keep LeetCode 75 when an existing user explicitly followed it. Unselected
    // legacy starters are replaced by the new default set.
    if (migrateDefaults && strings(parsed.followed).includes("leetcode-75") && !strings(parsed.hiddenPlans).includes("leetcode-75") && !customPlans.some(p => p.slug === "leetcode-75")) {
      customPlans.push(BUNDLED_PLANS.find(p => p.slug === "leetcode-75")!);
    }
    const available = new Set([...STUDY_PLANS, ...customPlans].map(p => p.slug));
    const hiddenPlans = strings(parsed.hiddenPlans).filter(slug => available.has(slug) &&
      !(migrateDefaults && STUDY_PLANS.some(p => p.slug === slug)));
    return { followed: strings(parsed.followed).filter(slug => available.has(slug) && !hiddenPlans.includes(slug)), manual: strings(parsed.manual), observed: strings(parsed.observed), customPlans, hiddenPlans, codeforcesObserved: strings(parsed.codeforcesObserved), codeforcesHandle: typeof parsed.codeforcesHandle === "string" ? parsed.codeforcesHandle : null, codeforcesSyncedAt: typeof parsed.codeforcesSyncedAt === "string" ? parsed.codeforcesSyncedAt : null, defaultsVersion: migrateDefaults ? DEFAULTS_VERSION : parsed.defaultsVersion, lastFullSyncAt: Number.isFinite(parsed.lastFullSyncAt) && parsed.lastFullSyncAt > 0 && parsed.lastFullSyncAt <= Date.now() + 300000 ? parsed.lastFullSyncAt : null };
  } catch { return emptyProgress(); }
}

export function addStudyPlan(state: ProgressState, plan: StudyPlan): ProgressState {
  return {
    ...state,
    customPlans: STUDY_PLANS.some(p => p.slug === plan.slug) ? state.customPlans : [...state.customPlans.filter(p => p.slug !== plan.slug), plan],
    hiddenPlans: state.hiddenPlans.filter(slug => slug !== plan.slug),
    followed: [...new Set([...state.followed, plan.slug])],
  };
}

export function removeStudyPlan(state: ProgressState, slug: string): ProgressState {
  return {
    ...state,
    customPlans: state.customPlans.filter(p => p.slug !== slug),
    hiddenPlans: STUDY_PLANS.some(p => p.slug === slug) ? [...new Set([...state.hiddenPlans, slug])] : state.hiddenPlans.filter(s => s !== slug),
    followed: state.followed.filter(s => s !== slug),
  };
}

export function visiblePlans(state: ProgressState): StudyPlan[] {
  return [...STUDY_PLANS, ...state.customPlans].filter(plan => !state.hiddenPlans.includes(plan.slug));
}

export function restoreStarterPlans(state: ProgressState): ProgressState {
  return { ...state, hiddenPlans: state.hiddenPlans.filter(slug => !STUDY_PLANS.some(plan => plan.slug === slug)) };
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

export function planCounts(plan: StudyPlan, state: Pick<ProgressState, "manual" | "observed"> & Partial<Pick<ProgressState, "codeforcesHandle" | "codeforcesObserved">>) {
  const questions = [...new Map(plan.planSubGroups.flatMap(g => g.questions).map(q => [q.titleSlug, q])).values()];
  const tracked = questions.filter(q => questionLeetcodeSlug(q) !== null || state.codeforcesHandle && questionCodeforcesSlug(q));
  const done = questions.filter(q => questionSolved(q, state)).length;
  return { done, total: questions.length, automatic: tracked.length, external: questions.length - tracked.length, percent: questions.length ? Math.round(done / questions.length * 1000) / 10 : 0, next: questions.find(q => !questionSolved(q, state)) };
}

async function graphql<T>(query: string, variables: Record<string, unknown>, label = "public activity"): Promise<T> {
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
    if (body.errors || !body.data) throw new Error(`LeetCode could not return ${label}. Try again shortly.`);
    return body.data;
  } finally { clearTimeout(timeout); }
}

export async function fetchStudyPlan(input: string): Promise<StudyPlan> {
  const { source, slug, url } = parsePlanInput(input);
  if (source === "takeuforward" && slug === strivers.slug) {
    const plan = readStudyPlan(strivers);
    if (!plan) throw new Error("The bundled Striver’s sheet could not be loaded.");
    return plan;
  }
  if (source !== "leetcode") {
    const plan = readStudyPlan(await fetchPublicPlan(url!));
    if (!plan) throw new Error("This page did not produce a supported question list.");
    return plan;
  }
  const result = await graphql<{ studyPlanV2Detail: unknown }>(
    `query extensionStudyPlan($slug: String!) { studyPlanV2Detail(planSlug: $slug) {
      name slug planSubGroups { name questions { title titleSlug difficulty } }
    } }`, { slug }, "this study plan");
  const plan = readStudyPlan(result.studyPlanV2Detail);
  if (!plan || plan.slug !== slug) throw new Error("That study plan is unavailable. Check its link and try again.");
  return plan;
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
