import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "../node_modules/esbuild/lib/main.js";

const bundle = await build({ entryPoints: [fileURLToPath(new URL("../src/progress/data.ts", import.meta.url))], bundle: true, write: false, platform: "node", format: "esm" });
const { STUDY_PLANS, BUNDLED_PLANS, dailySolved, emptyProgress, readProgress, progressKey, planCounts, fetchPractice, fetchFriendSubmissions, parsePlanSlug, parsePlanInput, readStudyPlan, fetchStudyPlan, addStudyPlan, removeStudyPlan, visiblePlans, restoreStarterPlans, questionSolved, questionUrl } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString("base64")}`);

test("bundled plans contain complete, unique official question lists", () => {
  for (const [index, expected] of [50, 75, 150].entries()) {
    const plan = BUNDLED_PLANS[index];
    const questions = plan.planSubGroups.flatMap(g => g.questions);
    assert.equal(questions.length, expected);
    assert.equal(new Set(questions.map(q => q.titleSlug)).size, expected);
    assert.ok(questions.every(q => q.title && /^[a-z0-9-]+$/.test(q.titleSlug) && ["EASY", "MEDIUM", "HARD"].includes(q.difficulty)));
  }
});

test("manual and automatic progress count each question once and select the next unsolved question", () => {
  const plan = STUDY_PLANS.find(p => p.slug === "top-sql-50");
  const slugs = plan.planSubGroups.flatMap(g => g.questions).map(q => q.titleSlug);
  const state = { followed: [plan.slug], manual: [slugs[0], slugs[1]], observed: [slugs[0], slugs[2], "unrelated-question"] };
  const count = planCounts(plan, state);
  assert.equal(count.done, 3);
  assert.equal(count.percent, 6);
  assert.equal(count.next.titleSlug, slugs[3]);
  const completed = planCounts(plan, { ...state, observed: slugs });
  assert.equal(completed.done, 50);
  assert.equal(completed.percent, 100);
  assert.equal(completed.next, undefined);
});

test("corrupt saved state is recoverable and progress is separated by account and handle", () => {
  for (const raw of [null, "{broken", "null", "42"]) assert.deepEqual(readProgress(raw), emptyProgress());
  assert.deepEqual(readProgress(JSON.stringify({ followed: ["top-sql-50", "invalid", "top-sql-50"], manual: ["big-countries", false, "big-countries"], observed: "invalid" })), { ...emptyProgress(), followed: ["top-sql-50"], manual: ["big-countries"] });
  assert.notEqual(progressKey(1, "handle"), progressKey(2, "handle"));
  assert.notEqual(progressKey(1, "handle"), progressKey(1, "changed_handle"));
  assert.equal(progressKey(1, "HANDLE"), progressKey(1, "handle"));
});

test("new users get three starters; removing all survives reload and restoration keeps solved history", () => {
  let state = readProgress(null);
  assert.deepEqual(visiblePlans(state).map(p => p.slug), ["strivers-a2z-dsa-sheet", "top-sql-50", "top-interview-150"]);
  state = { ...state, manual: ["big-countries"], observed: ["two-sum"], followed: ["top-sql-50"] };
  for (const plan of STUDY_PLANS) state = removeStudyPlan(state, plan.slug);
  const restoredSession = readProgress(JSON.stringify(state));
  assert.equal(visiblePlans(restoredSession).length, 0);
  assert.deepEqual(restoredSession.followed, []);
  assert.deepEqual(restoredSession.manual, ["big-countries"]);
  assert.equal(visiblePlans(restoreStarterPlans(restoredSession)).length, 3);
  assert.deepEqual(restoreStarterPlans(restoredSession).observed, ["two-sum"]);
  const reAdded = addStudyPlan(restoredSession, STUDY_PLANS.find(p => p.slug === "top-sql-50"));
  assert.equal(visiblePlans(reAdded).length, 1);
  assert.equal(planCounts(visiblePlans(reAdded)[0], reAdded).done, 1);
});

test("existing accounts get the new defaults once without losing followed plans or solve history", () => {
  const legacy = { followed: ["leetcode-75"], manual: ["big-countries"], observed: ["two-sum"], hiddenPlans: ["top-sql-50", "top-interview-150"], customPlans: [STUDY_PLANS[0]] };
  const migrated = readProgress(JSON.stringify(legacy));
  assert.deepEqual(visiblePlans(migrated).map(p => p.slug), ["strivers-a2z-dsa-sheet", "top-sql-50", "top-interview-150", "leetcode-75"]);
  assert.equal(migrated.customPlans.filter(p => p.slug === "strivers-a2z-dsa-sheet").length, 0);
  assert.deepEqual(migrated.followed, ["leetcode-75"]);
  assert.deepEqual(migrated.manual, legacy.manual);
  assert.deepEqual(migrated.observed, legacy.observed);
  assert.equal(visiblePlans(readProgress(JSON.stringify({ ...legacy, followed: [] }))).length, 3);
  const removedAgain = removeStudyPlan(migrated, "strivers-a2z-dsa-sheet");
  assert.equal(visiblePlans(readProgress(JSON.stringify(removedAgain))).some(p => p.slug === "strivers-a2z-dsa-sheet"), false, "user removals after migration must remain respected");
});

test("study-plan inputs accept supported sources and reject arbitrary hosts and executable URLs", () => {
  assert.equal(parsePlanSlug(" https://leetcode.com/studyplan/30-days-of-javascript/?utm_source=example "), "30-days-of-javascript");
  assert.equal(parsePlanSlug("leetcode.com/studyplan/top-sql-50"), "top-sql-50");
  assert.equal(parsePlanInput("https://takeuforward.org/prep-hub/strivers-a2z-dsa-sheet?open=none").source, "takeuforward");
  for (const link of ["https://evil.example/studyplan/top-sql-50", "https://leetcode.com.evil.example/studyplan/top-sql-50", "https://user:secret@leetcode.com/studyplan/top-sql-50/", "javascript:alert(1)", "https://leetcode.com/problems/two-sum/", "http://localhost:8000/private", "https://takeuforward.org/unknown-sheet"]) {
    assert.throws(() => parsePlanInput(link), undefined, link);
  }
});

test("invalid or empty imported plans cannot replace a valid saved library", () => {
  const plan = STUDY_PLANS[0];
  assert.equal(readStudyPlan({ ...plan, planSubGroups: [] }), null);
  assert.equal(readStudyPlan({ ...plan, sourceUrl: "javascript:alert(1)" }), null);
  assert.equal(readStudyPlan({ ...plan, planSubGroups: [{ name: "Examples", questions: [{ title: "Example", titleSlug: "example", difficulty: "EASY", url: "https://evil.example/" }] }] }), null);
  const saved = readProgress(JSON.stringify({ ...emptyProgress(), customPlans: [{ name: "Broken" }], hiddenPlans: ["top-sql-50"] }));
  assert.equal(visiblePlans(saved).length, 2);
  assert.equal(saved.customPlans.length, 0);
});

test("Striver's sheet imports offline, preserves sections, and only linked LeetCode questions auto-complete", async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => { throw new Error("External sheet import must use its bundled metadata"); };
    const plan = await fetchStudyPlan("https://takeuforward.org/prep-hub/strivers-a2z-dsa-sheet?open=none");
    const questions = plan.planSubGroups.flatMap(g => g.questions);
    assert.equal(questions.length, 495);
    assert.equal(new Set(questions.map(q => q.titleSlug)).size, 495);
    assert.ok(plan.planSubGroups.length > 50);
    const linked = questions.find(q => q.leetcodeSlug);
    const lesson = questions.find(q => q.kind === "learning");
    const state = { ...emptyProgress(), observed: [linked.leetcodeSlug] };
    assert.equal(questionSolved(linked, state), true);
    assert.equal(questionSolved(lesson, state), false);
    assert.equal(questionSolved(lesson, { ...state, manual: [lesson.titleSlug] }), true);
    assert.equal(planCounts(plan, { ...emptyProgress(), manual: [lesson.titleSlug] }).percent, 0.2, "one completed item should show progress on a large sheet");
    assert.match(questionUrl(linked), /^https:\/\/leetcode.com\/problems\//);
    assert.match(questionUrl(lesson), /^https:\/\/takeuforward.org\//);
    let saved = addStudyPlan(state, plan);
    saved = addStudyPlan(saved, plan);
    assert.equal(saved.customPlans.length, 0, "re-adding a default plan must not duplicate it");
    const reopened = readProgress(JSON.stringify(saved));
    assert.ok(reopened.followed.includes(plan.slug));
    const reopenedStrivers = visiblePlans(reopened).find(p => p.slug === plan.slug);
    assert.equal(reopenedStrivers.source, "takeuforward");
    assert.ok(planCounts(reopenedStrivers, reopened).done > 0);
    const removed = removeStudyPlan(reopened, plan.slug);
    assert.equal(removed.customPlans.length, 0);
    assert.equal(removed.followed.includes(plan.slug), false);
    assert.deepEqual(removed.observed, state.observed);
  } finally { globalThis.fetch = originalFetch; }
});

test("LeetCode importer fetches question metadata and handles unavailable plans without saving partial data", async () => {
  const originalFetch = globalThis.fetch;
  try {
    const plan = { ...BUNDLED_PLANS[0], slug: "example-plan", name: "Example plan" };
    let requests = 0;
    globalThis.fetch = async (url, options) => {
      requests++;
      assert.equal(url, "https://leetcode.com/graphql/");
      assert.equal(options.credentials, "omit");
      assert.equal(JSON.parse(options.body).variables.slug, "example-plan");
      return new Response(JSON.stringify({ data: { studyPlanV2Detail: plan } }));
    };
    const imported = await fetchStudyPlan("https://leetcode.com/studyplan/example-plan/");
    const saved = readProgress(JSON.stringify(addStudyPlan(emptyProgress(), imported)));
    assert.equal(saved.customPlans[0].name, "Example plan");
    assert.ok(saved.followed.includes("example-plan"));
    await assert.rejects(fetchStudyPlan("https://evil.example/studyplan/example-plan"));
    assert.equal(requests, 1, "unsupported URLs must never be requested");
    globalThis.fetch = async () => new Response(JSON.stringify({ data: { studyPlanV2Detail: null } }));
    await assert.rejects(fetchStudyPlan("missing-plan"), /unavailable/);
  } finally { globalThis.fetch = originalFetch; }
});

test("daily completion requires the matching problem accepted on the UTC challenge date", () => {
  const snapshot = { daily: { date: "2026-11-05", slug: "two-sum", title: "Two Sum" }, submissions: [], checkedAt: 0 };
  const row = (slug, iso) => ({ title: slug, titleSlug: slug, timestamp: String(Date.parse(iso) / 1000) });
  assert.equal(dailySolved({ ...snapshot, submissions: [row("two-sum", "2026-11-04T23:59:59Z"), row("big-countries", "2026-11-05T00:00:01Z")] }), false);
  assert.equal(dailySolved({ ...snapshot, submissions: [row("two-sum", "2026-11-05T00:00:00Z")] }), true);
  assert.equal(dailySolved({ ...snapshot, submissions: [row("two-sum", "2026-11-06T00:00:00Z")] }), false);
  assert.equal(dailySolved({ ...snapshot, submissions: [row("two-sum", "2026-11-05T05:30:00+05:30")] }), true);
  assert.equal(dailySolved({ ...snapshot, submissions: [{ titleSlug: "two-sum", timestamp: "invalid" }] }), false);
});

test("public requests omit cookies, coalesce duplicate loads, and reject upstream failures", async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  try {
    globalThis.fetch = async (url, options) => {
      calls++;
      assert.equal(url, "https://leetcode.com/graphql/");
      assert.equal(options.credentials, "omit");
      assert.equal(options.headers.Authorization, undefined);
      assert.ok(options.signal);
      const query = JSON.parse(options.body);
      assert.equal(query.variables.username, "public_example");
      return new Response(JSON.stringify({ data: { activeDailyCodingChallengeQuestion: { date: new Date().toISOString().slice(0, 10), question: { title: "Two Sum", titleSlug: "two-sum" } }, recentAcSubmissionList: [{ title: "Big Countries", titleSlug: "big-countries", timestamp: "1700000000" }, { title: "Bad", titleSlug: "bad", timestamp: "NaN" }] } }));
    };
    const [first, second] = await Promise.all([fetchPractice("public_example"), fetchPractice("public_example")]);
    assert.equal(calls, 1);
    assert.deepEqual(first, second);
    assert.equal(first.submissions.length, 1);
    await fetchPractice("public_example");
    assert.equal(calls, 1);
    await fetchPractice("public_example", true);
    assert.equal(calls, 2, "explicit refresh must bypass the short cache after a new solve");
    globalThis.fetch = async () => new Response("{}", { status: 503 });
    await assert.rejects(fetchPractice("failed_example"), /unavailable/);
    globalThis.fetch = async () => new Response(JSON.stringify({ errors: [{ message: "upstream failure" }] }));
    await assert.rejects(fetchFriendSubmissions("friend_example"), /public activity/);
    // A rejected request must not remain permanently stuck in the pending map.
    await assert.rejects(fetchPractice("failed_example"), /public activity/);
  } finally { globalThis.fetch = originalFetch; }
});
