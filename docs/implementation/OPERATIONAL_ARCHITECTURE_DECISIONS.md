# Approved operational architecture — 2026-10-15

The user's latest architectural decisions resolve the three earlier planning questions. They authorize implementation, not deployment, spending, provider activation or certification. This decision record extends plan N and preserves the existing release gates, source custody, private ownership, canonical database and audit history.

**Superseding user decision: no cash spending.** Standard configurable usage limits govern actual use. The admin cost screen is a demonstration only. The earlier $20 allocation and cash reservation discussion below describe historical design, not dispatch permission. Migration 0031 and the Python dispatch boundary prohibit cash-funded requests. Unknown AMD/Evolus credit allocations remain disabled; exhausting credits never enables cash fallback. See [current implementation evidence](ZERO_CASH_AND_SHARED_OPERATIONS.md).

## Identity and voice

Implement Google/GitHub authorization-code OAuth with S256 PKCE using maintained Python OAuth/OIDC libraries. Keep existing local credentials, canonical principals, ownership, sessions, permissions and audit. Signup creates a new ordinary principal; login resolves verified issuer/subject. Email similarity is never automatic account linking. Linking requires an authenticated existing session, explicit consent and a fresh verified provider flow. State, PKCE verifier and OIDC nonce must be server-bound, single-use and expiring; no token/state logs or browser service keys. Supabase is not selected.

Authlib 1.9.1 is now pinned and integrated; real provider activation is still unqualified. See [integrated OAuth evidence](OAUTH_ACCOUNTS_AND_BROWSER_SESSIONS.md). Its [maintained client documentation](https://docs.authlib.org/en/stable/oauth2/client/http/index.html) describes S256 support. Verify pinned dependency hashes/licenses and actual Google/GitHub callbacks before acceptance. [GitHub's official flow](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps) supports S256 PKCE. [Google OIDC](https://developers.google.com/identity/openid-connect/openid-connect) requires verified token claims; use issuer/subject rather than mutable email as identity. Account linking must retain prior source owners and session histories.

Voice is local-first and provider-agnostic, with optional cloud fallback only through an explicitly approved free or verified promotional-credit allocation; cash-funded fallback is prohibited. Local ASR/TTS must remain available without a cloud account. Incremental transcription, language switching, bounded audio, clause synthesis, cancellation epochs, VAD/AEC and barge-in require real acoustic/quality/latency evidence. Existing Remy components may be evaluated only after their location and reuse rights are established; proprietary submission exclusions remain. No new OpenAI account/key is needed just to implement an OpenAI-compatible transport.

## Approved event envelope and budgets

| Setting | Initial value |
| --- | --- |
| Concurrent users | 5 |
| Ordinary API requests per minute per user | 120 |
| Active generations per user | 1 |
| Active ingestion operations per user | 1 |
| AI generations per UTC day per user | 20 |
| Active GPU inference operations globally | 1 |
| Waiting GPU operations | 10 |
| Cash exposure maximum | USD 20 |
| Cloud overage allocation | USD 5 |
| Paid AI/voice API allocation | USD 10 |
| Contingency allocation | USD 5 |

All are configurable by controlled operator/admin configuration, never untrusted request fields. Demo overrides need bounded scope, expiry and audit; existing local policy approvals must not be bypassed. Ordinary retrieval, authentication, ASR partials and streaming chunks are not AI generations. Clause-level synthesis must not multiply generation charges. Local compute has no cumulative token ceiling, but context/output safety bounds, resource admission and concurrency still apply.

Use integer micro-USD for cash. AMD and Evolus use independent provider-credit units; no fabricated USD conversion or implicit permission to charge cash after credits are exhausted. Unknown credit allocations start disabled. Reserve maximum estimated exposure before dispatch; record actual usage and provider cost. Do not refund unknown outcomes on timeout or TTL. Real overruns must be recorded even if they exceed a ceiling, and must halt new admission rather than disappearing from accounting. Budget alerts and instance limits do not guarantee a provider hard spending cap.

## Deployment and resilience

Prefer Cloud Run for public API/OAuth/stream coordination; keep one authoritative PostgreSQL identity/data/audit/accounting system. Redis may coordinate ephemeral limits/cache/queue state; loss must not lose canonical data or erase cash exposure. Cloud Run instances cannot rely on process-local counters, sticky sessions or background threads remaining alive. [Cloud Run WebSockets](https://docs.cloud.google.com/run/docs/triggering/websockets) are subject to request timeouts and best-effort session affinity, so reconnect, cancellation and shared state are mandatory.

Evaluate an Oracle A1 ARM64 host for persistent PostgreSQL/NSAI knowledge and workers; do not replace PostgreSQL with an incompatible database or add a second identity authority. [Current Oracle documentation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) lists 1,500 OCPU-hours / 9,000 GB-hours monthly, equivalent to 2 OCPUs / 12 GB for Always Free tenancies, and warns idle instances can be reclaimed. Older 4-OCPU/24-GB assumptions are unsuitable without account verification. Independent durable/off-host backup is necessary before placing user data there; no host or capacity is provisioned by this decision.

AMD is reserved for demanding inference/semantic work, behind approved provider routing. UI/login/private/shared retrieval/Atlas/memory and conversation should degrade to an approved available backend or explicit no-inference response without fabricated AI output. Local deterministic evidence operations must not depend on AMD or Evolus availability. Cloud Run/Oracle cross-cloud network security, database TLS, connection pooling, ARM64 wheels/images and restoration must be tested before deployment.

Evolus remains optional and disabled until official product/API documentation and account permissions are supplied and verified. Implement verified REST workflows/extractors/tools/libraries/agents/chat as authorized capabilities, with version pins, source scope, cost/credit reservations, durable idempotency and unknown-outcome reconciliation. Evolus never becomes a competing canonical knowledge store or a route around NSAI approvals.

## Current increment and open integration

Implemented in the current source increment: validated operator-limit configuration; configurable HTTP request allowance; PostgreSQL-backed per-user daily/active inference checks and global active count; additive cost-account/reservation/event tables; atomic reserve/settle operations; separate cash/credit units; conservative timeout retention; overrun shutdown; admin-only cost inspection and reserved-exposure alerts.

These primitives are not a completed paid-provider integration. Remaining work includes actual provider dispatch/metering and price verification, durable queue/admission for five users and ingestion, shared request limiting, controlled override workflows and synchronized financial-policy configuration. Environment policy cash values do not silently rewrite authoritative ledger balances/caps. Current SQL seed limits are authoritative until a reviewed administrative update is implemented. No cash has been spent and no provider activated by these tests.

OAuth, real ASR/TTS, full duplex, Redis/Nginx, Cloud Run deployment configuration, ARM64 compatibility, Evolus, operational fallback and the rest of the semantic/UI expansion remain subsequent verified slices. Do not mark their cards accepted from the new accounting tests. Preserve the user's section-4 audit notification and independent second/third audit/report comparison checkpoints.
