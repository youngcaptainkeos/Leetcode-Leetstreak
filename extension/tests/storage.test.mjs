import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "../node_modules/esbuild/lib/main.js";

async function bundled(relative) {
  const result = await build({
    entryPoints: [fileURLToPath(new URL(relative, import.meta.url))],
    bundle: true,
    write: false,
    platform: "node",
    format: "esm",
  });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);
}

function mockStorage() {
  const values = new Map();
  globalThis.window = new EventTarget();
  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => {
      values.set(key, String(value));
      globalThis.localStorage[key] = String(value);
    },
    removeItem: (key) => {
      values.delete(key);
      delete globalThis.localStorage[key];
    },
  };
  // Ensure chrome is undefined for localStorage fallback testing
  delete globalThis.chrome;
  return values;
}

test("storage: getStoredSession returns null when empty", async () => {
  mockStorage();
  const storage = await bundled("../src/storage.ts");
  const session = await storage.getStoredSession();
  assert.equal(session, null);
});

test("storage: migrates legacy individual keys to versioned session contract", async () => {
  mockStorage();
  localStorage.setItem("codestreak_user_id", "42");
  localStorage.setItem("codestreak_access_token", "test-token-xyz");

  const storage = await bundled("../src/storage.ts");
  const session = await storage.getStoredSession();
  assert.deepEqual(session, {
    version: 2,
    userId: 42,
    accessToken: "test-token-xyz",
  });

  // Check that versioned key was populated
  const rawV2 = localStorage.getItem("codestreak_session_v2");
  assert.ok(rawV2);
  assert.deepEqual(JSON.parse(rawV2), {
    version: 2,
    userId: 42,
    accessToken: "test-token-xyz",
  });
});

test("storage: migrates legacy codestreak_user object", async () => {
  mockStorage();
  localStorage.setItem("codestreak_user", JSON.stringify({ id: 101, token: "tok-abc" }));

  const storage = await bundled("../src/storage.ts");
  const session = await storage.getStoredSession();
  assert.deepEqual(session, {
    version: 2,
    userId: 101,
    accessToken: "tok-abc",
  });
});

test("storage: setStoredSession stores versioned contract and synchronizes individual keys", async () => {
  mockStorage();
  const storage = await bundled("../src/storage.ts");
  await storage.setStoredSession({
    version: 2,
    userId: 77,
    accessToken: "tok-77",
  });

  const session = await storage.getStoredSession();
  assert.deepEqual(session, {
    version: 2,
    userId: 77,
    accessToken: "tok-77",
  });
  assert.equal(localStorage.getItem("codestreak_user_id"), "77");
  assert.equal(localStorage.getItem("codestreak_access_token"), "tok-77");
});

test("storage: clearStoredSession removes session and invalidates account caches", async () => {
  mockStorage();
  const storage = await bundled("../src/storage.ts");
  await storage.setStoredSession({
    version: 2,
    userId: 77,
    accessToken: "tok-77",
  });
  localStorage.setItem("codestreak_cached_dash", "cached-data");
  localStorage.setItem("codestreak_cached_board", "cached-board");
  localStorage.setItem("codestreak_menu_77", "tab");

  await storage.clearStoredSession();

  assert.equal(await storage.getStoredSession(), null);
  assert.equal(localStorage.getItem("codestreak_user_id"), null);
  assert.equal(localStorage.getItem("codestreak_access_token"), null);
  assert.equal(localStorage.getItem("codestreak_session_v2"), null);
  assert.equal(localStorage.getItem("codestreak_cached_dash"), null);
  assert.equal(localStorage.getItem("codestreak_cached_board"), null);
  assert.equal(localStorage.getItem("codestreak_menu_77"), null);
});

test("storage: sensitive drafts are rejected and cleared", async () => {
  mockStorage();
  const storage = await bundled("../src/storage.ts");
  await storage.setStored("codestreak_draft_password", "secret");
  assert.equal(localStorage.getItem("codestreak_draft_password"), null);
  assert.equal(await storage.getStored("codestreak_draft_password"), null);
});
