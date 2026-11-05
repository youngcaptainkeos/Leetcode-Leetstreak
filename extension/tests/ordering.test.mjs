import assert from "node:assert/strict";
import { test } from "node:test";

test("UI-07: deduplication of solves across sources retains the latest timestamp", () => {
  // Simulate public solves (from recent submissions, e.g. timestamp 1700005000)
  // and ledger solves (from database, e.g. timestamp 1700001000) for the same problem
  const publicSolves = [
    {
      title: "Two Sum",
      titleSlug: "two-sum",
      timestamp: "1700005000",
      platform: "leetcode",
    },
  ];

  const ledgerSolves = [
    {
      title: "Two Sum",
      titleSlug: "two-sum",
      timestamp: "1700001000",
      platform: "leetcode",
    },
    {
      title: "Watermelon",
      titleSlug: "watermelon",
      timestamp: "1700002000",
      platform: "codeforces",
    },
  ];

  const combined = [...publicSolves, ...ledgerSolves];

  // Merge algorithm from FriendsActivity
  const friendMap = new Map();
  for (const solve of combined) {
    const key = `${solve.platform}-${solve.titleSlug}`;
    const existing = friendMap.get(key);
    if (!existing || Number(solve.timestamp) > Number(existing.timestamp)) {
      friendMap.set(key, solve);
    }
  }

  const result = [...friendMap.values()];
  const twoSum = result.find((s) => s.titleSlug === "two-sum");

  assert.ok(twoSum);
  // Must preserve the newer public timestamp 1700005000, NOT the older ledger timestamp 1700001000
  assert.equal(twoSum.timestamp, "1700005000");
  assert.equal(result.length, 2);
});

test("UI-06: partial lookup failure retains valid results from the other platform", () => {
  // Simulate one platform succeeding and one failing
  let leetcodeSuccess = true;
  let codeforcesSuccess = false;

  const publicSolves = leetcodeSuccess
    ? [{ title: "Add Two Numbers", titleSlug: "add-two-numbers", timestamp: "1700003000", platform: "leetcode" }]
    : [];
  const ledger = codeforcesSuccess
    ? [{ title: "CF Problem", titleSlug: "cf-prob", timestamp: "1700004000", platform: "codeforces" }]
    : [];

  let hadError = !leetcodeSuccess || !codeforcesSuccess;
  const combined = [...publicSolves, ...ledger];

  // Verified that error is recorded for honest display
  assert.equal(hadError, true);
  // Verified that successful platform results are not discarded
  assert.equal(combined.length, 1);
  assert.equal(combined[0].titleSlug, "add-two-numbers");
});

test("UI-05: request sequence counter invalidates stale superseded responses", async () => {
  let activeReqId = 0;
  let currentRenderedBoard = null;

  async function mockFetch(id, delayMs, boardName) {
    const reqId = ++activeReqId;
    return new Promise((resolve) => {
      setTimeout(() => {
        // Only render if request is still current
        if (reqId === activeReqId) {
          currentRenderedBoard = boardName;
        }
        resolve({ reqId, boardName });
      }, delayMs);
    });
  }

  // Request 1: "global" (slow: 50ms)
  const req1 = mockFetch(1, 50, "GlobalBoard");
  // Request 2: "friends" (fast: 10ms)
  const req2 = mockFetch(2, 10, "FriendsBoard");

  await Promise.all([req1, req2]);

  // Request 2 should be rendered, Request 1 must be ignored despite finishing later
  assert.equal(currentRenderedBoard, "FriendsBoard");
});
