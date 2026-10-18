import { defineConfig } from "@neon/config/v1";
import existing from "../../neon.ts";

// Explicit alternative, never applied automatically. Keep the owner's neon.ts intact.
// The Free plan cannot enable AI Gateway; no paid model route is substituted.
const secret = process.env.NSAI_NEON_ORIGIN_SECRET;
if (!secret || secret.length < 32 || secret.length > 256) throw new Error("NSAI_NEON_ORIGIN_SECRET is required");
export default defineConfig({
  ...existing,
  aiGateway: false,
  functions: {
    ...existing.functions,
    hello: { ...existing.functions.hello, source: "../../hello.ts", env: { NSAI_NEON_ORIGIN_SECRET: secret } },
  },
});
