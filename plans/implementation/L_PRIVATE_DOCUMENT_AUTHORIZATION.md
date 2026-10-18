# Private document authorization integration

Binding Release 1 policy, supplied 2026-10-15: uploader-private by default; explicit user/group sharing; explicitly authorized, audited administrative access; local RBAC retained; centralized integration disabled. This extends K and FIN-04/05/09/10/11/14/19/20. None of the following storage/runtime integrations is accepted merely because the pure policy tests pass.

## Foundation implemented

`security.py` supports an optional bounded local-user registry with stable actors and existing role permissions. Legacy role tokens remain compatible but are shared identities, not individual privacy. No real credentials or live configuration changed. `document_access.py` defines private-first owner/read-grant decisions, no admin/agent bypass, complete-provenance requirements for derived outputs, and actor/policy/membership epoch cache identities. API admission deliberately denies content routes to new local-user principals until the complete authorization adapter is installed. This protects the intermediate build; it does not make it a usable private release.

## Required integration cards

2026-10-15 status: ACL-01 persistence seams are implemented in migration 0008 and
qualified against isolated PostgreSQL, including replay/grant convergence and audit
failure/concurrent-change checks. Production ingestion does not yet establish owners;
therefore ACL-01 remains **partial**. ACL-04 has qualified storage functions for
owner-only share/revoke, server-owned group membership and audited privileged read
authorization, but its routes/UI and response integration remain **unverified**.
ACL-02/03/05/06/07/08 remain open. See the current
[scoped receipt](../../evidence/private-access/15039969887647eba6a1e469d5a9aad3/receipt.json).
Database functions trust server-resolved actors and roles; do not expose those
arguments to clients. They do not establish content-table RLS or derived access
enforcement. Do not enable private ingestion before legacy readers and all derived
paths are protected.

| Card | Change | Acceptance |
|---|---|---|
| ACL-01 Policy persistence | Append-only migration for immutable source ownership, explicit user/group grants, server-owned group memberships, revocation/expiry and monotonic policy/membership epochs. Separate mutable operational state from immutable access events. | Owner established in source transaction; no implicit project/admin/agent grants; compare-and-swap changes audited; migration privilege regrant allowlist converges correctly. |
| ACL-02 Private ingestion and dedup | Owner-scoped logical source identity and content-hash dedup. Existing global hash/revision uniqueness must not merge private logical documents. Preserve old source IDs and artifacts; quarantine ambiguous legacy ownership for explicit mapping, never infer a person from a shared role. | A and B uploading identical bytes cannot discover each other's private document or create ACL collisions; failure rolls back ownership and derived state; no timing/response duplicate signal across tenants. |
| ACL-03 Read/query enforcement | Bind verified actor to every database transaction with safe pool reset. Apply source filters before ranking, pagination, counts and graph traversal. Use database enforcement as defense in depth; app joins must not rely solely on a client-supplied scope. | Unauthorized IDs return indistinguishable not-found responses; queries, source originals/HEAD, knowledge/formulas/units, supplements and source inspection enforce identical current policy. Reused pooled connections cannot inherit authority. |
| ACL-04 Shares/groups/admin | Owner-only share/revoke routes and UI; explicit server-controlled memberships. Shared readers may read/query, not reshare. Admin role alone grants no content access. Every privileged read requires a committed access audit before returning bytes; audit failure denies. | Owner, shared reader, unrelated member, explicit admin and scoped agent matrix verified with two same-role users; group removal, expiry, concurrent revoke and unavailable audit store tested. Demo corpus explicitly shared to a demo group. |
| ACL-05 Derived provenance | Every passage, formula, graph node/edge, memory, supplement, engineering flow, learning proposal and export records its complete contributing source set. Unknown or incomplete provenance denies access. | Bob's public paper cannot expose Alice's manual through an edge label, existence/count, answer, node ID, nearest neighbor, reflection or export. Multi-source artifacts require access to every source or independently regenerated authorized-only output. |
| ACL-06 Chat/caches/revocation | Session messages, invocation receipts, model prompts and cached responses carry source dependencies and policy epochs. Reauthorize on every read and immediately before response serialization. Cancel or withhold in-flight outputs if permissions change. | Share then query then revoke: no old answer, memory, receipt, cache, citation or export can be fetched after revocation. Model output cannot launder revoked/private evidence into a lower-trust artifact. Cache key changes alone is not sufficient. |
| ACL-07 Background jobs | Source-scoped service identities/capabilities with bounded grants and lease lifetime. Job authorization checked at claim and publication; no unrestricted learning identity. | Replacement, deletion, expiry/revoke or stale lease prevents publication and source-dependent graph activation. Parser/encoder do not receive broad DB or administrative credentials. |
| ACL-08 Independent qualification | Real owned PostgreSQL tests, two-user/group browser scenarios and adversarial inference tests, with source hashes and current images. Enable the new-user content adapter only after all routes and derived paths pass. | Cross-user identity, no-bypass admin, group revocation, cache/in-flight leakage, SQL grants and pooled-context isolation pass. An independently reviewed source-policy matrix and evidence remain separate from deployment. |

## Migration and compatibility rules

Changing source IDs would invalidate corpus artifacts and citations. Preserve legacy records and identify new owner-scoped logical sources deliberately; retain physical hash custody separately. The current native source ID and global unique hash/revision key are not sufficient for private multiuser deduplication. No automatic destructive rewrite of existing documents or learned artifacts.

Conversation and invocation JSON can contain several sources. Filtering its primary document ID is insufficient. New provenance must be complete and old unqualified messages/receipts withheld from private-user mode. Audit exports also need source filtering; a global audit stream can contain private titles, identifiers and query text. Administrative policy management and administrative content access remain distinct.

Do not flip a deployment flag to bypass the current intermediate deny. The eventual adapter must cover each content/derived route, recovery and source revocation. Legacy shared-role demonstration evidence does not qualify individual document privacy. The explicitly shared demo library needs named user identities and real group membership, not an anonymous visibility flag.

## Commissioning boundaries

No cloud/OIDC setup, central activation, AMD/Evolus enablement or live credential changes are part of this foundation slice. Current file/page limits remain unchanged. Qualify ACL-01 through ACL-08 before the full-library semantic rollout, then rerun retrieval and P0/P1 tests against the authorized corpus rather than a global corpus.
