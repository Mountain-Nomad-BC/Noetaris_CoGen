# NSAI — next implementation queue and source-use handoff

## Definition of 'done' for the starter

The package includes original source code for the small console, bounded text-claim extraction, PostgreSQL model, authenticated FastAPI endpoints, Docker, AMD candidate override and security guidance. It intentionally does **not** contain copied proprietary Remy code or a full PX memory port. Do not mistake scaffolding and green unit tests for all-platform integration verification.

## Immediate work sequence (no architectural reinvention)

### Task 0: runtime base validation — required before more features

- Execute `python scripts/bootstrap_secrets.py`, `docker compose config --quiet`, `docker compose up -d --build` on the local Docker host.
- Check `GET /healthz`, `GET /readyz`, token rejection and accepted Bearer token.
- Run `python scripts/demo_seed.py`, confirm two distinct candidate claims, one conflict group, two documents, stable dedupe on repeated seed.
- Restart containers (without deleting volume), verify persistence and authentication still work.
- Execute `docker compose --profile sandbox run --rm sandbox-smoke`; inspect network namespace, uid, mounts, limits, readonly root filesystem.
- Run `python scripts/validate_compose_security.py` and `pytest -q`.
- Fix any actual Docker errors and record `docker version`, platform and Compose version.

### Task 1: canonical object contracts (use PX)

- Read actual source `Pacify-X-main/contracts/nsai/knowledge-object.schema.json`, `formula-object.schema.json`, and `runtime/nsai_knowledge.py`; list its imports, tests and exact required fields.
- Implement standalone `nsai.contracts` schemas compatible with approved fields, reject unknown authority flags, and add reproducible JSON canonicalization. Preserve Apache-2.0 file notices if original code is adopted.
- Create a `schema_migration` bridge from starter `claims` to candidate NSAI knowledge objects. Do not auto-promote.

### Task 2: TurnBurn-inspired ingestion (clean room until license approved)

- Implement independent MIME-allowlisted PDF/Markdown/TXT parsers; page/section/line locators, original hash and revision, corrupt input handling.
- Add content-addressed chunks, deterministic source manifests and bounded token chunk sizes.
- Add semantic embedder and lexical retrieval; create index generations with source hash, embedder digest and index checksums.
- Validate candidate index on golden queries and missing-source adversarial fixtures. Promote index only after validated; rollback to known-good index.
- **DO NOT import or paste Remy proprietary implementation or internal data into public repository absent written authorization.**

### Task 3: evidence lifecycle

- Adapt/refactor only selected Apache-licensed PX concepts from `knowledge_refinery.py`, `trusted_evidence.py`, `learning_promotion.py`.
- Candidate -> conflict/novel/duplicate -> review -> versioned approval, recording actor, evidence receipt, exact old/new hash.
- Separate index activation, canonical object promotion, executable skill promotion. Make all 3 authorization events distinct.

### Task 4: AMD inference

- Confirm AMD event host, Linux driver, render node, ROCm version, image digest, available VRAM, model license.
- Run ROCm/vLLM GPU service in dedicated private container or separate VM; confirm GPU visibility.
- Set NSAI_MODEL_URL to internal hostname or secured HTTPS private address.
- Call `/v1/reason`, record real latency, image/model digests, token usage if exposed, and explicit `model_unverified` status.
- Keep inference down during unrelated local development to save event GPU credits.

### Task 5: skills + security (only once above works)

- Define skill candidate manifest, tests, sandbox resource quotas, admission receipts, independent approving actor.
- Use an ephemeral Linux isolated execution backend, not PX Windows Job enforcement. No Docker socket anywhere inside NSAI services.
- Start with preapproved, non-executable plans and simple bounded workers. **Do not run arbitrary LLM-generated code inside the existing API or `sandbox-smoke` service.**

### Task 6: deploy

- Add production identity (OIDC), rate limits, TLS, host/cloud network firewall, egress rules, image digest pinning, SBOM and vulnerability scan.
- Replace local database connection only after staging migrations and secured managed DB validation. Postgres tables are intentionally compatible with a PostgreSQL target; Supabase-specific auth, RLS and features are not yet enabled.
- Record demo metrics from source-backed test runs, not estimated values.

## Test obligations

1. Schema invalid/missing/NaN/duplicate IDs, too-big files, archives with path traversal and embedded symlinks.
2. Conflicting source revisions, ambiguity, unsupported claims, stale citations, missing source content.
3. Tenant/document visibility and permission bypass attempts; no admin read through public API.
4. Model prompt injection attempts treated as document text; model cannot authorize write/promotion.
5. Hostile code isolation test in an actually hardened executor, fail-closed on containment failure.
6. Database restart/crash/recovery, migrations, persistent state and rollback.
7. AMD dropout/timeouts/5xx/TLS/cost ceiling and non-AMD fallback clearly labeled.

## Handoff constraints for another coding model

Work only in NSAI standalone repository. Do not copy any Remy/RIE proprietary code or employer data; use it only as an architectural reference unless explicit legal authorization arrives. Keep new APIs typed, testable, narrow and documented. Respect distinctions between candidate knowledge, promoted truth, index activation and executable skills. Before enabling execution, require a genuine Linux sandbox on the AMD host. Preserve Docker safety settings and expose only intended public frontend ingress after authentication/TLS and rate limiting. Report tested vs untested accurately.
