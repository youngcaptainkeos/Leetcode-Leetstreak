import type { StudyPlan, StudyQuestion } from "./data";

// Read public metadata only. Page HTML and scripts are never mounted or executed.
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
export function importedPlanSlug(url: URL): string { return `web-${url.hostname.replace(/[^a-z0-9]+/g, "-").slice(0, 45)}-${hash(url.href)}`; }
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
function questionLink(url: URL): boolean {
  if (leetcodeSlug(url)) return true;
  const path = url.pathname;
  if (/^(www\.)?codeforces\.com$/.test(url.hostname)) return /^\/(?:problemset\/problem\/\d+\/\w+|(?:contest|gym)\/\d+\/problem\/\w+|group\/[^/]+\/contest\/\d+\/problem\/\w+|edu\/course\/\d+\/lesson\/\d+\/\d+\/practice\/contest\/\d+\/problem\/\w+)\/?$/.test(path);
  if (url.hostname === "atcoder.jp") return /^\/contests\/[^/]+\/tasks\/[^/]+\/?$/.test(path);
  if (/^(www\.)?codechef\.com$/.test(url.hostname)) return /\/problems\/[^/]+\/?$/.test(path);
  if (url.hostname === "cses.fi") return /^\/problemset\/task\/\d+\/?$/.test(path);
  if (/^(www\.)?hackerrank\.com$/.test(url.hostname)) return /\/challenges\/[^/]+\/problem\/?$/.test(path);
  if (/^(www\.)?geeksforgeeks\.org$/.test(url.hostname)) return /^\/problems\/[^/]+\/?$/.test(path);
  if (/^(www\.)?takeuforward\.org$/.test(url.hostname)) return /^\/(?:plus\/dsa\/problems|blogs\/[^/]+)\/.+/.test(path);
  return false;
}
function makeQuestion(url: URL, title?: string): StudyQuestion {
  const lc = leetcodeSlug(url);
  if (lc) { url.pathname = `/problems/${lc}/`; url.search = ""; }
  const fallback = (lc || url.pathname.split("/").filter(Boolean).pop() || "Question").replace(/[-_]+/g, " ");
  return { title: (title?.replace(/\s+/g, " ").trim() || fallback).slice(0, 300), titleSlug: questionIdentity(url), difficulty: "PRACTICE", url: url.href, kind: "practice", ...(lc ? { leetcodeSlug: lc } : {}) };
}
function checkedPlan(plan: StudyPlan): StudyPlan {
  const seen = new Set<string>();
  plan.planSubGroups = plan.planSubGroups.map(group => ({ ...group, questions: group.questions.filter(q => { if (seen.has(q.titleSlug)) return false; seen.add(q.titleSlug); return true; }) })).filter(g => g.questions.length);
  if (!seen.size) throw new Error("No public question links were found. Try pasting the question links instead; login-only or interactive pages cannot always be scanned.");
  if (seen.size > 1000 || plan.planSubGroups.length > 200) throw new Error("This list is too large. Choose a smaller playlist or filter it to at most 1,000 questions.");
  return plan;
}

export function planFromLinks(text: string, name: string, source?: string): StudyPlan {
  const groups = [{ name: "Questions", questions: [] as StudyQuestion[] }];
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/https:\/\/[^\s<>"\]]+/);
    if (!match) continue;
    try {
      const url = publicUrl(match[0].replace(/[),.;]+$/, ""));
      const title = line.replace(match[0], "").replace(/^(?:[-*]\s+|\d+[.)]\s+)/, "").replace(/[|:\[\]()]+/g, " ").trim();
      groups[0].questions.push(makeQuestion(url, title));
    } catch { throw new Error("A question link is invalid. Use public HTTPS links, one per line."); }
  }
  const sourceUrl = source ? publicUrl(source).href : undefined;
  const identity = sourceUrl || groups[0].questions.map(q => q.url).sort().join("\n");
  return checkedPlan({ name: name.trim().slice(0, 150) || "My practice plan", slug: `links-${hash(identity)}`, source: "external", ...(sourceUrl ? { sourceUrl } : {}), planSubGroups: groups });
}

function decodeFlight(html: string): unknown[] {
  let stream = "";
  for (const match of html.matchAll(/self\.__next_f\.push\((\[1,[\s\S]*?\])\)<\/script>/g)) {
    try { const chunk = JSON.parse(match[1]); if (typeof chunk[1] === "string") stream += chunk[1]; } catch { /* Not a public JSON chunk. */ }
  }
  const records: unknown[] = [];
  for (const match of stream.matchAll(/[0-9a-f]+:(?=[\[{])/g)) {
    const start = match.index! + match[0].length;
    let depth = 0, quoted = false, escaped = false;
    for (let i = start; i < stream.length; i++) {
      const char = stream[i];
      if (quoted) { if (escaped) escaped = false; else if (char === "\\") escaped = true; else if (char === '"') quoted = false; }
      else if (char === '"') quoted = true;
      else if (char === "[" || char === "{") depth++;
      else if ((char === "]" || char === "}") && --depth === 0) {
        try { records.push(JSON.parse(stream.slice(start, i + 1))); } catch { /* Ignore non-JSON records. */ }
        break;
      }
    }
  }
  return records;
}
function findSheet(value: unknown, depth = 0): Record<string, any> | null {
  if (!value || typeof value !== "object" || depth > 30) return null;
  const obj = value as Record<string, any>;
  if (obj.sheet_syllabus?.fields && obj.sheet_syllabus?.rows) return obj;
  for (const item of Object.values(obj)) { const found = findSheet(item, depth + 1); if (found) return found; }
  return null;
}
function tufPlan(html: string, source: URL): StudyPlan | null {
  const sheet = decodeFlight(html).map(record => findSheet(record)).find(Boolean);
  if (!sheet) return null;
  const { fields, rows, roots } = sheet.sheet_syllabus;
  if (!Array.isArray(fields) || !Array.isArray(rows) || !Array.isArray(roots) || rows.length > 10000) throw new Error("This sheet's public structure is unsupported. Paste its question links instead.");
  const groups = new Map<string, StudyQuestion[]>();
  const visited = new Set<number>();
  function visit(index: number, path: string[]) {
    if (!Number.isInteger(index) || visited.has(index) || path.length > 20) return;
    visited.add(index);
    const row = rows[index];
    if (!Array.isArray(row) || !Array.isArray(fields[row[0]])) return;
    const item = Object.fromEntries(fields[row[0]].map((key: string, i: number) => [key, row[i + 1]]));
    if (item.type === "category") {
      if (typeof item.label !== "string" || !Array.isArray(item.children)) return;
      item.children.forEach((child: number) => visit(child, [...path, item.label])); return;
    }
    if (typeof item.label !== "string" || item.type !== "item") return;
    let link: URL;
    try { link = publicUrl(item.leetcode_link || item.free_blog_link || source.href, source.href); } catch { return; }
    const question = makeQuestion(link, item.label);
    question.titleSlug = `tuf-${hash(source.pathname)}-${String(item.id).replace(/[^a-z0-9-]/gi, "-").slice(0, 50)}-${hash(String(item.redirectTo?.category || path.join("/")))}`;
    question.kind = item.layoutType === "learning" ? "learning" : "practice";
    question.difficulty = question.kind === "learning" ? "LESSON" : ({ basic: "BASIC", core: "CORE", pro: "PRO", easy: "EASY", medium: "MEDIUM", hard: "HARD" } as Record<string, string>)[String(item.difficulty).toLowerCase()] || "PRACTICE";
    const name = path.join(" / ").slice(0, 150) || "Questions";
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name)!.push(question);
  }
  roots.forEach((index: number) => visit(index, []));
  // If the provider changes its hierarchy, don't silently import a partial sheet.
  const itemCount = rows.filter((row: unknown) => Array.isArray(row) && fields[row[0]]?.includes("type") && row[fields[row[0]].indexOf("type") + 1] === "item").length;
  if ([...groups.values()].flat().length !== itemCount) throw new Error("Some sheet items could not be identified. Paste question links instead of saving a partial plan.");
  const doc = new DOMParser().parseFromString(html, "text/html");
  return checkedPlan({ name: (typeof sheet.info?.name === "string" ? sheet.info.name : doc.querySelector("h1")?.textContent?.trim() || source.pathname.split("/").pop()!.replace(/-/g, " ")).slice(0, 150), slug: source.pathname.split("/").filter(Boolean).pop()!, source: "takeuforward", sourceUrl: source.href, snapshotDate: new Date().toISOString().slice(0, 10), planSubGroups: [...groups].map(([name, questions]) => ({ name, questions })) });
}

export function planFromPage(html: string, input: string): StudyPlan {
  const source = publicUrl(input);
  if (/^(www\.)?takeuforward\.org$/.test(source.hostname)) {
    const plan = tufPlan(html, source);
    if (plan) return plan;
  }
  const doc = new DOMParser().parseFromString(html, "text/html");
  doc.querySelectorAll("script,style,nav,header,footer,aside").forEach(node => node.remove());
  const questions: StudyQuestion[] = [];
  const main = doc.querySelector("main,article,[role=main]") || doc.body;
  for (const anchor of main.querySelectorAll<HTMLAnchorElement>("a[href]")) {
    try {
      const url = publicUrl(anchor.getAttribute("href")!, source.href);
      if (!questionLink(url)) continue;
      questions.push(makeQuestion(url, anchor.textContent || undefined));
    } catch { /* Not a public exercise link. */ }
  }
  return checkedPlan({ name: (doc.querySelector("h1")?.textContent || doc.title || "Imported practice plan").trim().slice(0, 150), slug: importedPlanSlug(source), source: source.hostname.replace(/^www\./, "") === "codeforces.com" ? "codeforces" : "external", sourceUrl: source.href, snapshotDate: new Date().toISOString().slice(0, 10), planSubGroups: [{ name: "Detected questions", questions }] });
}

// Must be called directly from the user's Scan link click, before network awaits.
export async function requestImportAccess(input: string): Promise<void> {
  const url = publicUrl(input);
  if (typeof chrome === "undefined" || !chrome.permissions?.request) return;
  const origins = [`${url.origin}/*`];
  if (url.hostname === "www.codeforces.com") origins.push("https://codeforces.com/*");
  const granted = await chrome.permissions.request({ origins });
  if (!granted) throw new Error("Website access was declined. You can paste question links instead.");
}
async function publicText(url: string, maxBytes = 6000000): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(url, { credentials: "omit", redirect: "error", signal: controller.signal });
    if (!response.ok) throw new Error("This public page could not be read. Paste its question links instead.");
    if (Number(response.headers.get("content-length")) > maxBytes) throw new Error("This page is too large to scan.");
    const reader = response.body?.getReader();
    if (!reader) throw new Error("This page could not be read.");
    const chunks: Uint8Array[] = []; let length = 0;
    while (true) {
      const { value, done } = await reader.read(); if (done) break;
      length += value.byteLength;
      if (length > maxBytes) { await reader.cancel(); throw new Error("This page is too large to scan."); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(length); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    return new TextDecoder().decode(bytes);
  } finally { clearTimeout(timeout); }
}
async function codeforcesPlan(source: URL): Promise<StudyPlan | null> {
  const contest = source.pathname.match(/^\/contest\/(\d+)(?:\/(?:problems)?)?\/?$/);
  const problemset = /^\/problemset(?:\/page\/\d+)?\/?$/.test(source.pathname);
  if (!contest && !problemset) return null;
  const tags = source.searchParams.get("tags") || "";
  // Codeforces combines tag/rating filters in `tags`, e.g. dp;800-1200.
  const filters = tags.split(";").filter(Boolean);
  const ratings = filters.find(filter => /^\d+-\d+$/.test(filter));
  const api = new URL("https://codeforces.com/api/problemset.problems");
  const topicTags = filters.filter(filter => !/^\d+-\d+$/.test(filter));
  if (topicTags.length) api.searchParams.set("tags", topicTags.join(";"));
  const result = JSON.parse(await publicText(api.href, 12000000));
  if (result.status !== "OK" || !Array.isArray(result.result?.problems)) throw new Error("Codeforces could not return this public list. Paste its question links instead.");
  const bounds = ratings?.split("-").map(Number);
  const problems = result.result.problems.filter((p: any) => (!contest || String(p.contestId) === contest[1]) && (!bounds || Number.isFinite(p.rating) && p.rating >= bounds[0] && p.rating <= bounds[1]));
  if (problems.length > 1000) throw new Error("This Codeforces problemset has over 1,000 questions. Add tag/rating filters or choose a contest.");
  const order = source.searchParams.get("order");
  if (contest) problems.sort((a: any, b: any) => String(a.index).localeCompare(String(b.index), "en", { numeric: true }));
  else if (order === "BY_RATING_ASC" || order === "BY_RATING_DESC") problems.sort((a: any, b: any) => (order === "BY_RATING_ASC" ? 1 : -1) * ((a.rating || 0) - (b.rating || 0)));
  const questions = problems.map((p: any) => {
    if (!Number.isSafeInteger(p.contestId) || !/^[A-Za-z0-9]+$/.test(p.index) || typeof p.name !== "string") throw new Error("Codeforces returned an unsupported question.");
    return makeQuestion(new URL(`https://codeforces.com/problemset/problem/${p.contestId}/${p.index}`), `${p.index}. ${p.name}`);
  });
  return checkedPlan({ name: contest ? `Codeforces contest ${contest[1]}` : `Codeforces · ${tags || "Problemset"}`, slug: importedPlanSlug(source), source: "codeforces", sourceUrl: source.href, snapshotDate: new Date().toISOString().slice(0, 10), planSubGroups: [{ name: "Questions", questions }] });
}
export async function fetchPublicPlan(input: string): Promise<StudyPlan> {
  const source = publicUrl(input);
  try {
    if (/^(www\.)?codeforces\.com$/.test(source.hostname)) {
      const plan = await codeforcesPlan(source);
      if (plan) return plan;
    }
    return planFromPage(await publicText(source.href), source.href);
  } catch (error) {
    if (error instanceof TypeError || error instanceof DOMException) throw new Error("This site blocked scanning, redirected, or took too long. Paste its question links instead.");
    throw error;
  }
}
