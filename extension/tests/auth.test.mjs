import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "../node_modules/esbuild/lib/main.js";

async function bundled(relative) {
  const result = await build({ entryPoints: [fileURLToPath(new URL(relative, import.meta.url))], bundle: true, write: false, platform: "node", format: "esm" });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);
}

function browser() {
  const values = new Map();
  globalThis.window = new EventTarget();
  globalThis.localStorage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => { values.set(key, String(value)); globalThis.localStorage[key] = String(value); },
    removeItem: key => { values.delete(key); delete globalThis.localStorage[key]; },
  };
  return values;
}

test("website publishes a session only after its token is stored", async () => {
  browser();
  const session = await bundled("../../web/app/session.ts");
  localStorage.setItem("codestreak_user_id", "1");
  assert.equal(session.getSessionUserId(), null);
  let observed;
  window.addEventListener("leetstreak:session", () => { observed = session.getSessionUserId(); });
  session.setSessionUserId(2, "synthetic-token");
  assert.equal(observed, 2);
  assert.equal(localStorage.getItem("codestreak_access_token"), "synthetic-token");
  session.setSessionUserId(null);
  assert.equal(session.getSessionUserId(), null);
  assert.equal(localStorage.getItem("codestreak_access_token"), null);
});

for (const source of ["../src/lib/api.ts", "../../web/app/lib/api.ts"]) {
  test(`${source}: authenticated requests, controlled expiry, and stale-response protection`, async () => {
    browser();
    localStorage.setItem("codestreak_access_token", "synthetic-old-token");
    const { api, AUTH_EXPIRED } = await bundled(source);
    let expired = 0;
    window.addEventListener(AUTH_EXPIRED, () => expired++);
    globalThis.fetch = async (_url, options) => {
      assert.equal(options.headers.Authorization, "Bearer synthetic-old-token");
      return Response.json({ detail: "Please sign in again." }, { status: 401 });
    };
    await assert.rejects(api.dashboard(1), error => error.status === 401);
    assert.equal(expired, 1);
    await assert.rejects(api.login("demo@example.com", "fictional-password"));
    assert.equal(expired, 1, "bad login must not expire an unrelated session");
    globalThis.fetch = async () => {
      localStorage.setItem("codestreak_access_token", "synthetic-new-token");
      return Response.json({ detail: "Old session" }, { status: 401 });
    };
    await assert.rejects(api.dashboard(1));
    assert.equal(expired, 1, "a late old-token failure must not expire a newer login");
  });
}
