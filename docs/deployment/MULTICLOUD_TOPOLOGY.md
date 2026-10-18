> October 17 owner update: the default remote inference target is AMD hosted Radeon API `Gemma-4-31B-IT`, with both exact free OpenRouter Gemmas as fallbacks and local CPU continuity. Dedicated AMD instance/compute-credit commissioning is superseded for this path. Automatic source-bearing hosted dispatch remains unqualified; preserve its admission/export/accounting gates. See `deploy/amd/hosted.env.example` and current HANDOFF.md.

# Multi-cloud topology and current fact table

The operator's October 17 delivery contract supersedes the earlier provisional Compute Engine assumption: **Firebase static React -> OCI ARM64 NSAI API/PostgreSQL -> authenticated AMD ROCm/vLLM**, with Evolus optional and disabled until configured. Source contract: `<owner-profile>/Downloads/02_CODING_AGENT_DEPLOYMENT_INSTRUCTIONS.md`, SHA-256 `b16d9be6854308a1352c7292dc24a127aaf81eea89ebe13c27b6c5e8b0761c3c`. The October 16 operational handoff is historical where newer exact evidence exists. No public deployment or release certification is authorized by local tests.

## Facts before target-specific changes

| Classification | Fact | Evidence/limit |
| --- | --- | --- |
| observed | No Git checkout/commit identity is available in this workspace | Use exact source/build-input hash maps; do not invent a commit |
| observed | Six-service local Docker integration is healthy at `http://127.0.0.1:8790` | `state/integration/identity.json`; only UI loopback port published |
| observed | Gemma 3 1B CPU and MiniLM helper are active | Artifact checksum and GGUF architecture verified; not AMD hardware qualification |
| observed | 1,614 backend tests pass with zero skips on the preceding frozen local candidate | `evidence/integration-deployment/qualification-a772430bacb74a55a2933f497b4c9001/receipt.json`; later source changes require new evidence |
| observed | Seven read-only operations screens have live backend data with four-role checks | 28 browser cases: 14 allowed, 14 denied; not workflow/agent execution acceptance |
| observed | Browser transport now supports exact owned same-site app/API origins; no split-origin deployment is yet commissioned | `deploymentOrigin.js`, `deployment_cors.py`, OAuth frontend redirect/CSRF configuration; contract tests pass, real provider E2E pending |
| observed | Google CLI is authenticated; a project named `noetaris` is visible | Read-only discovery only; no global project selection, API enablement or resource changes |
| inferred | `noetaris` is the likely Firebase project | Owner must confirm target/site/domain before publishing |
| observed | Supplied Evolus key is readable; verified application/workflow/agent/extractor bindings are absent | Evolus must be `NOT_CONFIGURED` and OFF; optional and not a standalone component release blocker |
| unverified | Actual OCI ARM64 images, sizing, native-worker performance and restore behavior | x86 Docker tests and wheel metadata are not ARM64 acceptance |
| unverified | Actual Google/GitHub OAuth, owned domains/TLS, production cookies and CSRF | Mocked providers and local role tokens are not real provider E2E |
| blocked | Public private-user content admission and independent release/security/legal acceptance | Original DENY gate remains authoritative |
| blocked | Neon is optional fallback; Cloudflare is intended for binary documents/images but exact product/bucket/credential bindings remain unverified | No guessed adapter, migration or data transfer |

## Current local data flow

Browser -> UI Nginx `127.0.0.1:8790` / container `8080` -> API `8787`. API has internal role-specific networks to PostgreSQL `5432`, isolated parser `8788`, llama.cpp `8080` and MiniLM encoder `8092`. Database, parser, encoder and model publish no host ports. API has no direct public port. The UI alone joins a front network. Partner credentials are API-only read-only mounts; partner setup refresh does not make remote requests.

PostgreSQL holds original bytes/revisions, semantic jobs/generations, claims/reviews, identity bindings, sessions, memory, inference and audit records. It remains the authoritative transactional/identity system. Named integration storage is synthetic and must not be silently copied into production. Model files are read-only bindings. Backups and receipts remain in private `state/` and `evidence/`; off-VM encryption/scheduling still need commissioning. Container logs are redacted and rotated; operational observations cover authorized visible records rather than every workspace event.

## Intended trust boundaries

Firebase serves only a scanned static build and public nonsecret configuration. OAuth credentials and browser sessions remain in NSAI/PostgreSQL; Firebase Authentication is not introduced. An owned same-site application/API domain pair is preferred. OCI exposes only a hardened HTTPS edge; API/DB/workers are private. AMD serving needs authenticated restricted ingress plus independently qualified model/driver/image provenance. Source-bearing remote dispatch stays disabled until export authorization and allowance/accounting are commissioned. Evolus is an optional bounded outbound integration, never an identity or authority replacement.

Cash spending remains prohibited. Free/credit availability and quotas must be checked by the owner; alerts are not spending caps. OCI A1 sizing must come from actual ARM64 measurements. Optional features must be explicitly disabled with honest degraded behavior rather than silently replaced by fixtures or unauthorized providers.

## Owner clarification: optional Neon and Cloudflare storage

The owner selected Google project `noetaris` and clarified that Neon is optional. Its official CLI/skills and Codex MCP plugin are installed, authenticated CLI project discovery succeeds, and no production service cutover was performed. AI Gateway is blocked on the current Free plan; no paid route is authorized. See NEON_SETUP.md.

Cloudflare is intended to hold original documents and extracted images. The supplied attachment contains a token permissions summary; bucket names, S3 endpoint and usable server credentials have not been verified. Current uploads still retain original bytes in PostgreSQL; Firebase is static hosting and does not currently store uploaded documents. No storage offload, duplicate-cost reduction, object-store recovery or image extraction upload is claimed before actual implementation and E2E qualification.
