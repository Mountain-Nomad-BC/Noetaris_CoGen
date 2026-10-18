# Implementation handoff — NOETARIS CoGen frontend v0.2

## Guardrails

1. **Do not replace working backend workflows.** The recovered UI is a presentation layer. Validate route and DTO shapes against the actual hackathon repository before connecting it. The source `contracts/registry.js` is an *inventory claim*, not live evidence.
2. **Preserve provenance.** Every simulated response remains tagged DEMO_FIXTURE. A backend error must show an error, never a plausible mock answer masquerading as a real answer.
3. **Keep server authority.** Identity, ACL, document isolation, security, spend, workflow run authorization and audit records are enforced by the backend. Frontend gating is defense-in-depth, not security.
4. **Do not share raw browser-only files.** Local PDF previews create object URLs in the browser, are not uploaded, and have no server citations. Revoke URLs when closed.
5. **Keep motion beautiful but controlled.** 3D/WebGL and animation must stop offscreen, pause on hidden tabs and respect reduced motion; don't tie requestAnimationFrame loops to global app rerenders.

## Screen / implementation matrix

| Screen(s) | What is recovered | Outstanding backend/functionality |
|---|---|---|
| Landing, marketing, access | Layout, cards, routing, WebGL lattice, animations | Actual user auth, approved demos, real marketing claims |
| Command Center | Navigation, KPI/fleet panels, sparkline, status cards | Live aggregate telemetry; no invented data on live mode |
| Chat / voice | Thread controls, composer, TTS, microphone meter, optional browser STT, shared state, API adapter | Validated POST `/v1/chat` DTO, citations, streaming SSE, server transcription, identity and per-document ACL |
| PDF Workspace | Demo pagination/zoom/rotation, selection toolbar, citation demo, local browser PDF preview | Authenticated GET `/v1/sources/{document_id}/original`, PDF.js worker, word geometry, anchored highlight overlays, OCR verification, true shared source/session lineage |
| Library | Search, demo revision/status inspector, local upload admission preview | GET `/v1/documents`, POST `/v1/files`, GET `/v1/capabilities`, workflow progress and signed bytes |
| Knowledge Explorer | Filterable fixture graph/list | GET `/v1/knowledge/{document_id}/browse`, lineage, graph data, revisions, server permissions |
| Workflow Studio | React Flow graph, canvas, local undo/redo/drafts, diff/review controls | Validated PUT `/v1/workflows/{id}/drafts`; proposals, immutable revision publish, run permissions, version/race control |
| Agents/Models/Execution | Detailed fixture panels, status and trace UI | Registered model/agent/execution endpoints, measured latency/usage, SSE, audited real actions |
| Costs, Observability, Governance, Audit | Rich fixture tables, filter UI, cards | Actual authenticated reporting, immutable audit, export, restrictive role policies |
| Developers/Contracts | Recovered endpoint contract list | OpenAPI schemas, error types, server version and integration tests |
| Demo Controls | Per-tab scenario and motion preferences | No global backend policy toggles; keep isolated |
| Knowledge Review, Research, Memory, Analytics, Agent Detail/New, Workflow Versions, Templates, Queue, Integrations/Provider Detail, Approvals, Evaluations, Evidence | Route placeholders with consistent shell | **14 separate routes need actual feature implementations** |

## Immediate P0 wiring sequence

### 1. Authentication and production access

- Map real login/session endpoints with backend maintainer; do not guess endpoint names.
- Add server session introspection, login/logout and CSRF. Use cookie-based sessions when compatible with backend policy; ensure SameSite, Secure, HttpOnly flags at server.
- Remove the `LiveAuthGate` denial *only after* live backend calls return authenticated session and per-resource authorization.
- Test direct navigation to private routes, 401/403, expired sessions, identity switching, document cross-tenant access and log-out cleanup. Backend must reject unauthorized calls irrespective of UI.

### 2. Unified chat session and citation DTO

- Verify real POST `/v1/chat` payload and response against implementation. `src/noetaris/services/api.js` currently proposes `message`, `session_id`, `document_id` and expects `answer` or `response.text`; **this wire shape is NOT verified.** Update it to match actual OpenAPI, add typed runtime validation and integration tests.
- For conversation persistence, replace browser demo session state with backend chat history. For streaming, bind `/v1/chat/turns/{turn_id}/stream` only after server contract confirmation. Tie SSE to active message IDs and abort on navigation.
- Require verified citation source IDs, pages, spans, confidence and permission checks. Never render arbitrary citation text as if server-qualified.
- Shared frontend voice draft is mounted in `VoiceProvider`, enabling navigation between chat and document Q&A without discarding dictation. Replace browser STT with an explicit user-consented `/v1/voice/transcribe` stream if sensitive-data policies require on-prem handling.

### 3. Document renderer and ingestion

- Use PDF.js and its matching worker at the same package version for real PDF pages; choose canvas or text-layer overlays. Preserve page rotation/zoom with correctly transformed geometry.
- Fetch authenticated PDF bytes only from source API; avoid exposing unscoped public object URLs or caching protected document bytes across users.
- Render highlights only for verified geometry records from `/v1/citations/{citation_id}/geometry`. OCR uncertain text must not get fabricated boxes.
- Replace demo 2 MiB admission snapshot with live capabilities returned by `/v1/capabilities`. Implement queueing/error states for >100 page documents only after parser qualification. Display per-stage progress after POST `/v1/files` using authoritative ingestion events.

### 4. Workflow / execution / governance

- Separate local working draft from published revision. Use backend ETag/version or equivalent compare-and-swap; handle conflicts, authorization and failed saves.
- Execution trace must come from backend, not fixture timers. Block paid or restricted run actions server-side; audit all sensitive mutations.
- Verify governance sandbox isolation as a separate production requirement; no CSS toggle constitutes an isolation boundary.

## UI / animation acceptance conditions

- Run at 320, 375, 768, 1280 and 1920 CSS px; verify no clipped controls; keyboard-only path through chat, sidebar, PDF, workflow and modals.
- Test 3D with WebGL enabled, hardware acceleration disabled, low-powered mobile, offscreen and hidden-tab conditions. Reduced-motion must stop animation and keep controls functional.
- Target interaction responsiveness without blocking main thread, but **do not claim an FPS or performance score without measurement**. Capture Chrome Performance/Memory and Lighthouse in the actual host environment.
- Verify voice after `chat -> documents/doc-1 -> chat`, stopping microphone, microphone denied, unsupported STT, simultaneous TTS, and signout.
- Verify chat new thread + async response to old thread, PDF question appearing in shared thread, cancelled requests, malformed JSON and schema errors.
- Verify arbitrary document routes do not display the wrong sample PDF, local preview is not uploaded, and local blob URLs are revoked.
- Audit all 14 placeholder routes before claiming feature completeness.

## Engineering/build verification

```bash
npm install
npm run check
npm run build
npm run preview
```

These are required on a host with npm registry access. The static source check validates JS/JSX parse, local import presence and CSS grammar but is not a substitute for bundle/browser/E2E tests. CI workflow runs source check and build when connected.

## Recommended API response status model

Every server-backed panel should implement discriminated states: `loading`, `ready`, `empty`, `error`, `forbidden`, `unavailable`, `demo`. Do not auto-fallback from errors/forbidden to fixtures. Include request IDs and safe error messages; do not log sensitive tokens or document content.
