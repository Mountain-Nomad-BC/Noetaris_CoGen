import test from "node:test";
import assert from "node:assert/strict";
import handler from "../hello.ts";

const secret = "synthetic-function-test-credential-00000000";
test("Neon function fails closed without server configuration", async () => {
  delete process.env.NSAI_NEON_ORIGIN_SECRET;
  assert.equal((await handler.fetch(new Request("https://function.invalid/"))).status, 503);
});
test("Neon function authenticates before work and exposes no credentials", async () => {
  process.env.NSAI_NEON_ORIGIN_SECRET = secret;
  for (const provided of [undefined, "wrong", "x".repeat(secret.length)]) {
    const headers = provided ? { "x-secret": provided } : {};
    assert.equal((await handler.fetch(new Request("https://function.invalid/", { headers }))).status, 401);
  }
  const response = await handler.fetch(new Request("https://function.invalid/", { headers: { "x-secret": secret } }));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Cache-Control"), "no-store");
  assert.deepEqual(await response.json(), { service: "nsai-neon-connectivity", reachable: true, authority_granted: false });
});
test("Authenticated function rejects arbitrary paths and writes", async () => {
  process.env.NSAI_NEON_ORIGIN_SECRET = secret;
  const headers = { "x-secret": secret };
  assert.equal((await handler.fetch(new Request("https://function.invalid/admin", { headers }))).status, 404);
  assert.equal((await handler.fetch(new Request("https://function.invalid/", { headers, method: "POST", body: "synthetic" }))).status, 405);
  delete process.env.NSAI_NEON_ORIGIN_SECRET;
});
