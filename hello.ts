import { timingSafeEqual } from "node:crypto";

// Server-to-server connectivity check. This is not document access or inference.
export default {
  async fetch(request: Request): Promise<Response> {
    const secret = process.env.NSAI_NEON_ORIGIN_SECRET;
    if (!secret || secret.length < 32 || secret.length > 256) {
      return new Response("Service not configured", { status: 503 });
    }
    const supplied = request.headers.get("x-secret");
    if (!supplied || supplied.length > 256) return new Response("Unauthorized", { status: 401 });
    const expected = Buffer.from(secret);
    const provided = Buffer.from(supplied || "");
    if (provided.length !== expected.length || !timingSafeEqual(provided, expected)) {
      return new Response("Unauthorized", { status: 401 });
    }
    if (new URL(request.url).pathname !== "/") return new Response("Not found", { status: 404 });
    if (request.method !== "GET") return new Response("Method not allowed", { status: 405, headers: { Allow: "GET" } });
    return Response.json({ service: "nsai-neon-connectivity", reachable: true, authority_granted: false },
      { headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
  },
};
