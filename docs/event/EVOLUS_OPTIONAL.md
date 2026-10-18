# Optional Evolus Business Agents on AMD — explicit partner checklist

Source of truth: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-iii (checked Oct 12 2026). Event workspace official API docs are authoritative for exact execution payload shapes.

## Official eligibility essentials

- Event workspace created at `https://app.evolus.ai` with code provided at kickoff.
- Main agent uses an **open model served via your own vLLM endpoint on AMD Developer Cloud**.
- Use **at least two** Evolus building blocks (e.g., Workflow + Document Extractor).
- Drive workflows/tools/libraries through Evolus REST, and agent chat through REST or compatible endpoint.
- Public GitHub, containerized app, no keys committed and runnable README.
- Event documentation says `X-ApiKey` and `X-Application-Id` for REST requests and `POST /api/v1/workflows/{id}/execute`. Confirm body JSON in your workspace interactive reference.

## Choose a concrete end-to-end use case

**Vendor specification discrepancy review**: upload two revisions and a purchase order; extraction pulls supplier, part, quantity, temperature limit; NSAI discovers disagreement; Evolus Workflow starts a structured human approval; receipt is returned and displayed. Do **not** perform any actual purchase or contact a third party in the demo without explicit authorization.

## Recommended building blocks

1. `Document Extractor` — create schema for `vendor`, `sku`, `quantity`, `spec_limit_c`, `document_revision`, `source_id`.
2. `Workflow` — parse, compare, branch conflict into a human-review step; optionally `AI Tools` as third block for text comparison.
3. Configure Evolus agent to use secured AMD model endpoint with an open model.
4. Use the starter's `src/nsai/integrations/evolus.py` only behind server-side authorization and rate limits. It is **not yet wired** to the NSAI API.

## Implementation steps

- Create workspace, capture non-secret application/workflow IDs in private config; set API key via secret file, not frontend env.
- Verify AMD private-vLLM endpoint from Evolus; this may require authenticated TLS ingress rather than Docker internal hostname.
- Create schema/workflow and test with **synthetic** supplier documents. Save redacted response JSON and errors.
- Confirm workflow REST method/payload per live workspace docs; adapter expects caller-supplied `payload`, not a fabricated schema.
- Show both building block configuration and actual successful call in demo.
- Confirm event workspace telemetry/credits and usage proof; screenshots must redact secrets.

## Stop conditions

If hosting the AMD model publicly requires unsafe networking, if model endpoint is not actually AMD, if no event workspace API key exists, or if building blocks cannot complete before main demo, **do not claim Evolus qualification**. Submit strong main-track demo instead.
