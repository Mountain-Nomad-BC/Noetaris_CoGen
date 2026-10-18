# NSAI Local-First Implementation Plan — exact execution gates

This plan corrects a missing critical path in the earlier 57-task ledger: **an actual local inference service** and its integration testing belong BEFORE AMD ROCm. It also distinguishes a usable UI shell from complete TurnBurn, PX and skill execution.

## G0 — Host/Docker prerequisites and static tests (today)

- P0.1 Docker Desktop WSL2/Linux containers, Docker Compose plugin, free disk/RAM. Do not copy proprietary Remy source into this clean-room repo.
- P0.2 Fresh extraction; `python -m pip install -e ".[test]"`; `pytest -q`; run static security checks.
- P0.3 Bootstrap local secrets; never commit `.env` or `secrets/`.
- P0.4 Compose configuration resolves for both base and optional local AI profile. Verify security gates.

**Exit:** static tests green; Docker daemon available; no secrets in git index.

## G1 — Baseline API, database and browser UI

- B1.1 Start `db` + `api`; inspect logs/health. Base `compose.yaml` publishes only the loopback API port.
- B1.2 Open browser, connect with token, review evidence. Wrong token rejected.
- B1.3 Ingest synthetic two revisions; inspect conflict; refresh/restart confirms persistence.
- B1.4 Console renders on desktop and narrow view; no raw HTML injection from model output.

**Exit:** `python scripts/verify_local.py` passes on host; human sees UI + contradictions.

## G2 — Actual local model inference (NEW FIRST-CLASS GATE)

- LLM2.1 Add `deploy/local/compose.ollama.yaml` service and API overlay.
- LLM2.2 Pull `qwen2.5:3b` in container, preserve named model-cache volume.
- LLM2.3 Check `/v1/model/status` is configured/reachable/model_loaded; start with CPU.
- LLM2.4 UI `Ask connected AI` returns genuine local model text, source metadata and latency.
- LLM2.5 Confirm model-down/timeout/invalid-name failures are visibly labeled, with NO fake generated response.
- LLM2.6 Run `python scripts/verify_local_ai.py`; take screenshot and retain model timing.

**Exit:** real local model end-to-end integration passes and is repeatable after restart. Local inference is NOT AMD verification.

## G3 — TurnBurn-inspired ingestion implementation (NOT YET DONE)

- ING3.1 file upload endpoint with byte and MIME allowlist; secure parse to text, store SHA256, source ID and immutable revision.
- ING3.2 TXT + MD first; PDF pages and bounded extraction second. Encrypted/oversized PDFs should fail clearly.
- ING3.3 content chunk IDs derived deterministically from document version + source offset; dedupe and idempotency.
- ING3.4 candidate extraction from general text via LLM with JSON schema; validate strict source span, refuse unsourced claims.
- ING3.5 maintain asynchronous job status and error receipt; UI can inspect records.

**Exit:** same supplied synthetic documents create repeatable attributed chunks/claims; malicious instructions in documents cannot execute actions.

## G4 — Retrieval, concepts and memory (NOT YET DONE)

- RET4.1 exact/lexical retrieval baseline before embeddings.
- RET4.2 embedding provider interface; local model embeddings, versioned index, background rebuild and rollback.
- RET4.3 evidence ranking + conflict grouping; retrieved context is constrained and never authority.
- MEM4.4 integrate selected PX M01/M02/M03 via adapter after dependency/test audit; implement event history, candidate hypotheses, temporal validity.
- MEM4.5 publish proof links for source IDs, version, locator and claim status.

**Exit:** retrieval recall and precision on golden fixtures measured; bitemporal history consistent; reindex doesn't mutate authoritative evidence.

## G5 — Autodidactics / evaluations (NOT YET DONE)

- LR5.1 TurnBurn inspiration: propose learning updates as candidates, not active knowledge.
- LR5.2 PX-style contracts and evidence receipts, negative/prompt-injection cases, regression evaluator.
- LR5.3 candidate skill generator may propose specs, but may NOT authorize execution.
- LR5.4 separate reviewed promotion and append-only audit (real authorization checks, not schema-only).
- SEC5.5 implement independent short-lived tool runner with network=none, no Docker socket, non-root UID, no caps, read-only filesystem, size/time/memory/pid quotas. Fail-closed. Code execution remains disabled until host isolation is validated.

**Exit:** regression suite and independent reviewer deny/approve tests pass; adversarial tests verify no auto-promotion or sandbox escape.

## G6 — AMD migration and measurements (AFTER LOCAL GATES)

- AMD6.1 Confirm ROCm GPU instance, drivers, render device; container run succeeds with least privilege.
- AMD6.2 Deploy ROCm vLLM with SAME API contract; model ID and license verified.
- AMD6.3 Change env adapter only; UI and inference integration code unchanged.
- AMD6.4 Rerun end-to-end local-model acceptance steps against AMD endpoint; capture real GPU traces and p50/p95 latency.
- AMD6.5 Verify public remote ingress protection, limits, logs, clean IP/license release, demo and rollback.

**Exit:** live AMD inference proven; no reliance on fake/replayed results. This must be completed before hackathon submission.

## Execution order and stopping rule

G0 -> G1 -> G2 are the **immediate priority**. G3 -> G4 -> G5 build the intelligence system. G6 is infrastructure swap plus hardware-specific testing. Never call a gate passed based on source code or config alone; attach running host logs/tests for every operational gate.

## Testing matrix

| Validation | Local Docker | AMD |
|---|---|---|
| Static contracts/security | required | required |
| API/auth/database | required | required |
| Browser UI workflow | required | required |
| Ollama 3B real chat | required | replaced by vLLM |
| Model endpoint down/timeout | required | required |
| Source provenance/conflicts | required | required |
| General document ingestion | G3 | replay G3 |
| Index activation/rollback | G4 | replay G4 |
| PX memory/candidate advancement | G4/G5 | replay G4/G5 |
| GPU utilization/driver proof | optional local NVIDIA | required ROCm |
