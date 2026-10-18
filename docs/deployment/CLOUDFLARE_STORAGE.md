# Cloudflare document and image storage

Intended role: hold immutable original documents and extracted image assets in private object storage. Firebase serves only the static app. PostgreSQL remains authoritative for identities, source revisions/checksums, ACLs, parsed text, graph/index state and audit records. Neon is optional fallback; it is not required for this storage role.

## Current verified account state

The owner enabled R2 and reports a 10 GB cap. The fresh authenticated bucket-list check succeeded (HTTP 200) and confirms the owner-created `docs` and `images` buckets. The token is active. This verifies account access, not an application storage binding or a provider-enforced spending limit. The agent created no buckets. Two 59-byte synthetic connectivity objects were written, read back byte-for-byte and deleted successfully; no user content was sent. Both r2.dev endpoints are disabled and both custom-domain lists are empty. Authenticated S3 HEAD succeeds (HTTP 200) for both buckets using the documented token-ID/SHA-256 derivation, without persisting derived credentials. The bounded synthetic S3 write/read/delete check passes in both buckets with cleanup complete (six requests total). Both bucket detail responses confirm Standard storage. Durable quotas and application external custody remain unqualified.

## Zero-spend requirement

The owner explicitly prohibits paid storage usage. Treat this as a deployment constraint. Standard R2 currently includes 10 GB-month storage, 1 million Class A operations and 10 million Class B operations per month; Infrequent Access does not receive this free tier. Reference: https://developers.cloudflare.com/r2/pricing/

The reported 10 GB setting has not been independently verified as a hard billing cutoff. A storage cap alone does not bound operation charges. Do not activate automatic external uploads until durable combined document/image storage reservations, conservative request budgets, bounded retries and fail-closed exhaustion behavior have been implemented and qualified. Proposed application storage ceiling: 9,000,000,000 bytes combined, including pending uploads and unreconciled objects; this is a design requirement, not an implemented quota. Account usage by other clients must also be accounted for. No paid plan, Infrequent Access tier, paid storage fallback or automatic limit increase is authorized. Keep current database custody intact until the external replacement is qualified.

Server credentials are kept in ignored `secrets/` and account configuration in ignored `state/cloudflare/`. Neither is staged for GitHub or bundled into the frontend. The supplied attachment is a broad permissions summary, not an S3 access-key/secret pair. The extra supplied identifier has not been assumed to be a usable S3 access key. Do not derive or fabricate credentials without verifying the documented token contract.

## Required next work

1. Verify the reported cap and account-wide usage; verify private access for the existing `docs` and `images` buckets and establish least-privilege S3 credentials through a restricted server file. Qualify the zero-spend admission controls before enabling automatic uploads.
2. Qualify read/write/delete with uniquely prefixed synthetic objects only. Verify anonymous access denied and exact bytes/checksums on retrieval. Keep object keys bound to source identity/revision/checksum, not user-controlled paths.
3. Implement external-original custody and extracted-image storage with transactional publication, bounded retry/orphan handling, ACL checks before access, immutable digest verification, original download/PDF/reparse/review compatibility and storage-aware backup/restore. Existing database byte custody must remain intact until that replacement is qualified.
4. Repeat actual browser upload-to-index-to-query, original-byte and source-revocation tests on the storage-backed candidate. Do not claim storage offload or cost/space reduction from configuration templates or duplicated archives.

Current Docker uploads still retain original bytes in PostgreSQL. Synthetic Cloudflare object roundtrips pass; application upload/download E2E and storage-backed custody have not been performed. Private-user admission and release acceptance remain denied.

References: https://developers.cloudflare.com/r2/get-started/s3/ and https://developers.cloudflare.com/r2/api/tokens/
