# NOETARIS live library and source preservation

The live library now uses the existing canonical Python identity, backend content admission and read permissions. Only integrated library routes mount live content; individual content admission and remaining fixture/placeholder screens stay gated. The separate live shell displays the actual actor and contains no sample user, notification counters or simulation state.

The library uses authorized keyset pages (25 records/page), literal title filters, durable upload receipts, current source/index state and stored source evidence. Limits come from capabilities; ingest controls require the canonical ingest permission. Backend authorization independently enforces every request. Index queue state is not factual review or publication. Source text and manifest previews explicitly show their display bounds without changing retained data.

Original downloads use bounded same-origin streaming, current credentials/actor proof, stale-response cancellation and SHA-256 comparison with the selected authorized source before producing a browser download. Download handles are revoked. The read safety envelope is 32 MiB, independent of smaller new-upload limits; retained admitted originals remain readable after admission limits decrease. Source names/text render literally. Client validation clears file selection so users can retry the same file after correcting a revision.

Current exact frontend: sha256:141ac9bac2ec67fcef228fc6e869af704d6271d3739cdc487067b0ecdf87b982. Existing API: sha256:2cb14915a827ee050fe7a2dd04d2d1c79a211891154501ed2e72c57a97299ec0. Both retained with explicit hold tags. New code uses existing endpoints and storage; there is no schema migration or live data rewrite.

Fresh evidence:

- 14 transport/contract tests run inside the frontend Docker build; evidence/noetaris-integration/docker-library-qualified-build.log.
- 38 actual NOETARIS/API/parser/PostgreSQL/Chromium checks: evidence/noetaris-integration/1e3955108f0d47cbb6a1423704e8f66b/receipt.json. Covers 26-record pagination/filter reset, TXT/MD/CSV/TSV/JSON/XLSX/PDF upload and byte-identical download, queued state, duplicate identity, malformed/excluded/oversized rejection without partial records, raw numeric spelling, literal labels, five viewport widths, sign-out clearing, viewer read-only behavior and private individual admission.
- One explicit negative test substitutes corrupt original-response bytes after the positive real-service checks; the UI withholds the download on SHA mismatch. This fault injection is recorded separately from positive API behavior. A historical-profile fixture above 2 MiB remains downloadable while current API admission remains 2 MiB and rejects a new oversized source.
- 23 current Docker/auth/browser checks: evidence/noetaris-integration/586e1cf72a044e808e64e823630cbeda/receipt.json.
- 21 current HTTPS OAuth/resilience checks: evidence/oauth-browser-tls/df34d924a46c40d8b51561188b0f56c5/receipt.json. External provider boundaries are simulated; NSAI endpoints are real, including database-outage logout/retry. Real provider/public TLS qualification remains open.
- The prior 1,327 backend test inputs still match the current packaged API source byte-for-byte; these frontend changes do not constitute a newly rerun full backend suite. Current bindings, original-download preservation and exact changed-file map are in evidence/noetaris-integration/current-evidence.json and changed-imported-files.json.

Failed attempts are retained. Actual fixes include accepting normal URL-encoded spaces in filters and constraining the native file input at 320 px. An early verifier used full-page navigation after local in-memory login, which correctly discards that credential; it was corrected to use actual SPA navigation. No persistent credential storage was introduced to accommodate that verifier.

Changed surfaces: frontend App routes/gate, separate LiveAppShell, LibraryPage/LiveLibrary, libraryContracts and liveTransport, source/transport tests, and working frontend README. The supplied original 44 files remain unchanged in Downloads. Only explicitly owned isolated Docker resources were used and removed. Rollback selects the retained frontend image or original UI/API images; no data rollback or deletion is required.

Remaining: sharing/revocation controls and deterministic analysis in this inspector; PDF.js geometry, chat, Atlas/memory, remaining operational/placeholder screens, voice and wider operational expansion. Seven build-dependency advisories, real provider activation, capacity qualification and independent release acceptance remain open. These checks are scoped implementation evidence, not system certification or public rollout approval.
