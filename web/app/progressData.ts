import plans from "./data/study-plans.json";
import strivers from "./data/strivers-a2z.json";

export interface StudyQuestion {
  title: string;
  titleSlug: string;
  difficulty: string;
  url?: string;
  leetcodeSlug?: string;
  kind?: "learning" | "practice";
}

export interface StudyPlan {
  name: string;
  slug: string;
  planSubGroups: { name: string; questions: StudyQuestion[] }[];
  source?: "leetcode" | "takeuforward" | "codeforces" | "external";
  sourceUrl?: string;
  snapshotDate?: string;
}

export interface ProgressState {
  followed: string[];
  manual: string[];
  observed: string[];
  customPlans: StudyPlan[];
  hiddenPlans: string[];
  version: number;
}

export const BUNDLED_PLANS: StudyPlan[] = plans as StudyPlan[];
export const STUDY_PLANS: StudyPlan[] = [
  strivers as StudyPlan,
  (plans as StudyPlan[]).find(p => p.slug === "top-sql-50")!,
  (plans as StudyPlan[]).find(p => p.slug === "top-interview-150")!,
];

export function parsePlanSlug(input: string): string {
  let slug = input.trim();
  if (/^(?:www\.)?leetcode\.com\//i.test(slug)) slug = `https://${slug}`;
  if (slug.startsWith("https://")) {
    const url = new URL(slug);
    if (!["leetcode.com", "www.leetcode.com"].includes(url.hostname)) {
      throw new Error("Paste a study-plan link from leetcode.com.");
    }
    const match = url.pathname.match(/^\/studyplan\/([^/]+)\/?$/);
    if (!match) throw new Error("Use a link like https://leetcode.com/studyplan/30-days-of-javascript/.");
    slug = match[1];
  }
  if (slug.length > 100 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    throw new Error("Enter a LeetCode study-plan link or slug, such as 30-days-of-javascript.");
  }
  return slug;
}

export function publicUrl(input: string, base?: string): URL {
  const url = new URL(input, base);
  const host = url.hostname.toLowerCase();
  if (url.protocol !== "https:" || url.username || url.password || url.port || host.length > 253 ||
      !host.includes(".") || /[\[\]:]/.test(host) || /^[\d.]+$/.test(host) ||
      /(?:^|\.)(?:localhost|local|internal|test|invalid|example|onion)$/.test(host)) {
    throw new Error("Use a public HTTPS website link.");
  }
  url.hash = "";
  return url;
}

function hash(value: string): string {
  let result = 2166136261;
  for (const char of value) result = Math.imul(result ^ char.charCodeAt(0), 16777619);
  return (result >>> 0).toString(36);
}

export function importedPlanSlug(url: URL): string {
  return `web-${url.hostname.replace(/[^a-z0-9]+/g, "-").slice(0, 45)}-${hash(url.href)}`;
}

export function leetcodeSlug(url: URL): string | undefined {
  return /^(www\.)?leetcode\.com$/.test(url.hostname) ? url.pathname.match(/^\/problems\/([a-z0-9-]+)(?:\/|$)/)?.[1] : undefined;
}

function questionIdentity(url: URL): string {
  const lc = leetcodeSlug(url);
  if (lc) return `lc-${lc}`;
  if (/^(www\.)?codeforces\.com$/.test(url.hostname)) {
    const match = url.pathname.match(/^\/(?:problemset\/problem\/(\d+)\/([A-Za-z0-9]+)|(?:contest|gym)\/(\d+)\/problem\/([A-Za-z0-9]+))\/?$/);
    if (match) return `cf-${match[1] || match[3]}-${(match[2] || match[4]).toLowerCase()}`;
  }
  return `external-${hash(url.href)}`;
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
    try {
      const url = new URL(question.url);
      return ["leetcode.com", "www.leetcode.com"].includes(url.hostname) ? url.pathname.match(/^\/problems\/([a-z0-9-]+)\/?$/)?.[1] || null : null;
    } catch { return null; }
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

export function automaticQuestion(question: StudyQuestion, codeforcesHandle: string | null): boolean {
  return Boolean(questionLeetcodeSlug(question) || (codeforcesHandle && questionCodeforcesSlug(question)));
}

export function questionSolved(
  question: StudyQuestion,
  state: { manual: string[]; observed: string[]; codeforcesObserved?: string[]; codeforcesHandle?: string | null }
): boolean {
  const lc = questionLeetcodeSlug(question);
  if (lc !== null) return state.observed.includes(lc);
  const cf = questionCodeforcesSlug(question);
  if (cf && state.codeforcesHandle) return Boolean(state.codeforcesObserved?.includes(cf));
  return state.manual.includes(question.titleSlug);
}

export function readStudyPlan(value: unknown): StudyPlan | null {
  try {
    const plan = value as StudyPlan;
    if (!plan || typeof plan.name !== "string" || !plan.name.trim() || plan.name.length > 150 ||
      typeof plan.slug !== "string" || parsePlanSlug(plan.slug) !== plan.slug ||
      !Array.isArray(plan.planSubGroups) || !plan.planSubGroups.length || plan.planSubGroups.length > 200) return null;
    const groups: StudyPlan["planSubGroups"] = [];
    const seen = new Set<string>();
    const names = new Set<string>();
    let total = 0;
    for (const group of plan.planSubGroups) {
      if (!group || typeof group.name !== "string" || !group.name.trim() || group.name.length > 150 ||
        names.has(group.name) || !Array.isArray(group.questions)) return null;
      names.add(group.name);
      const questions: StudyQuestion[] = [];
      for (const question of group.questions) {
        if (++total > 1000 || !question || typeof question.title !== "string" || !question.title.trim() || question.title.length > 300 ||
          typeof question.titleSlug !== "string" || question.titleSlug.length > 200 || !/^[a-z0-9-]+$/.test(question.titleSlug) ||
          !["EASY", "MEDIUM", "HARD", "BASIC", "CORE", "PRO", "LESSON", "PRACTICE"].includes(question.difficulty)) return null;
        if (!seen.has(question.titleSlug)) {
          seen.add(question.titleSlug);
          questions.push({
            title: question.title,
            titleSlug: question.titleSlug,
            difficulty: question.difficulty,
            ...(question.url ? { url: question.url } : {}),
            ...(question.leetcodeSlug ? { leetcodeSlug: question.leetcodeSlug } : {}),
            ...(question.kind ? { kind: question.kind } : {}),
          });
        }
      }
      if (questions.length) groups.push({ name: group.name, questions });
    }
    return groups.length ? {
      name: plan.name.trim(),
      slug: plan.slug,
      planSubGroups: groups,
      ...(plan.source ? { source: plan.source } : {}),
      ...(plan.sourceUrl ? { sourceUrl: plan.sourceUrl } : {}),
      ...(plan.snapshotDate ? { snapshotDate: plan.snapshotDate } : {}),
    } : null;
  } catch { return null; }
}

export function visiblePlans(plansList: StudyPlan[], hiddenSlugs: string[]): StudyPlan[] {
  return plansList.filter(plan => !hiddenSlugs.includes(plan.slug));
}

export function planCounts(
  plan: StudyPlan,
  state: { manual: string[]; observed: string[]; codeforcesObserved?: string[]; codeforcesHandle?: string | null }
) {
  const questions = [...new Map(plan.planSubGroups.flatMap(g => g.questions).map(q => [q.titleSlug, q])).values()];
  const tracked = questions.filter(q => questionLeetcodeSlug(q) !== null || (state.codeforcesHandle && questionCodeforcesSlug(q)));
  const done = questions.filter(q => questionSolved(q, state)).length;
  return {
    done,
    total: questions.length,
    automatic: tracked.length,
    external: questions.length - tracked.length,
    percent: questions.length ? Math.round(done / questions.length * 1000) / 10 : 0,
    next: questions.find(q => !questionSolved(q, state)),
  };
}

export function planFromLinks(text: string, name: string): StudyPlan {
  const trimmedName = name.trim();
  if (!trimmedName || trimmedName.length > 150) throw new Error("Enter a playlist name up to 150 characters.");
  const urls: URL[] = [];
  const lines = text.split(/\r?\n/);
  for (const line of lines) {
    const words = line.trim().split(/\s+/);
    for (const word of words) {
      if (/^https?:\/\//i.test(word)) {
        try { urls.push(publicUrl(word)); } catch {}
      }
    }
  }
  if (!urls.length) throw new Error("Paste at least one valid question link.");
  if (urls.length > 1000) throw new Error("A custom playlist cannot exceed 1000 questions.");

  const questions: StudyQuestion[] = [];
  const seen = new Set<string>();
  for (const u of urls) {
    const slug = questionIdentity(u);
    if (!seen.has(slug)) {
      seen.add(slug);
      const lc = leetcodeSlug(u);
      const fallback = (lc || u.pathname.split("/").filter(Boolean).pop() || "Question").replace(/[-_]+/g, " ");
      questions.push({
        title: fallback.slice(0, 300),
        titleSlug: slug,
        difficulty: "PRACTICE",
        url: u.href,
        kind: "practice",
        ...(lc ? { leetcodeSlug: lc } : {}),
      });
    }
  }

  const slug = `playlist-${hash(trimmedName + urls[0].href).slice(0, 10)}`;
  return {
    name: trimmedName,
    slug,
    source: "external",
    planSubGroups: [{ name: "Questions", questions }],
  };
}

export function fetchBundledOrCatalogPlan(input: string): StudyPlan {
  const raw = input.trim();
  if (raw === strivers.slug || raw.includes("takeuforward.org")) {
    return strivers as StudyPlan;
  }
  const slug = parsePlanSlug(raw);
  const found = (plans as StudyPlan[]).find(p => p.slug === slug);
  if (found) return found;
  throw new Error(`Plan "${slug}" is not available in the offline catalog. You can paste question links directly below to create a custom playlist.`);
}
