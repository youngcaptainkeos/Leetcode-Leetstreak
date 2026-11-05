import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "../node_modules/esbuild/lib/main.js";

const bundle = await build({ entryPoints: [fileURLToPath(new URL("../src/progress/data.ts", import.meta.url))], bundle: true, write: false, platform: "node", format: "esm" });
const { STUDY_PLANS, dailySolved, emptyProgress, readProgress, progressKey, planCounts, fetchPractice, fetchFriendSubmissions } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString("base64")}`);

test("bundled plans contain complete, unique official question lists", () => {
  for (const [index, expected] of [50, 75, 150].entries()) {
    const plan = STUDY_PLANS[index];
    const questions = plan.planSubGroups.flatMap(g => g.questions);
    assert.equal(questions.length, expected);
    assert.equal(new Set(questions.map(q => q.titleSlug)).size, expected);
    assert.ok(questions.every(q => q.title && /^[a-z0-9-]+$/.test(q.titleSlug) && ["EASY", "MEDIUM", "HARD"].includes(q.difficulty)));
  }
});

test("manual and automatic progress count each question once and select the next unsolved question", () => {
  const plan = STUDY_PLANS[0];
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
  assert.deepEqual(readProgress(JSON.stringify({ followed: ["top-sql-50", "invalid", "top-sql-50"], manual: ["big-countries", false, "big-countries"], observed: "invalid" })), { followed: ["top-sql-50"], manual: ["big-countries"], observed: [] });
  assert.notEqual(progressKey(1, "handle"), progressKey(2, "handle"));
  assert.notEqual(progressKey(1, "handle"), progressKey(1, "changed_handle"));
  assert.equal(progressKey(1, "HANDLE"), progressKey(1, "handle"));
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
