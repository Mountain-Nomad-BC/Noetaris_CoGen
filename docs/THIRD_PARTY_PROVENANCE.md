# Third-party provenance ledger (populate before public release)

Current-byte reconciliation, 2026-10-15: the current vendor compatibility files
do **not** match the earlier adopted-byte hashes in `component-provenance.json`.
Their current hashes and declared roles are recorded in
[current-component-inventory.json](current-component-inventory.json). Current
application imports use local source/query-plan contracts; `NOTICE` describes the
retired runtime imports. This is an inventory correction, not a legal/IP audit or
permission to publish. Historical adoption records remain unchanged.

Exact current image package inventories/advisories are retained in
[package scan 490d31a1](../evidence/package-risk/490d31a17f6447ff84b44ef012d05d2c/package-receipt.json).
The encoder dependency update and its requalification are subsequent evidence.
Package inventories and included notices do not constitute material-rights acceptance.

| Component | Exact upstream version/commit | License | Changes | NOTICE requirement | Reviewed by/date |
|---|---|---|---|---|---|
| `python:3.12-slim` | **PIN SHA256** | Python/Debian package licenses | Docker base | See upstream | PENDING |
| `postgres:16-alpine` | **PIN SHA256** | PostgreSQL + Alpine packages | DB base | See upstream | PENDING |
| ROCm vLLM image | **PIN SHA256**, verify tag and host architecture | Upstream licenses | GPU image | See upstream | PENDING |
| Chosen Qwen model | **VERIFY EXACT MODEL ID/REVISION** | Model card license | inference only | Model card | PENDING |
| PX historical adoption / current compatibility file | See current inventory; historical adopted hash differs | Historical Apache-2.0 attribution retained; current per-file origin review required | Current declared compatibility contract | Existing LICENSES/NOTICE retained pending review | PENDING |
| Remy historical adoption / current compatibility alias | See current inventory; current file imports local contracts | Historical source restriction is not a blanket license determination for current files | Current alias differs from historical adopted body | No public publication authorization; current origin/IP review remains required | PENDING |

New NSAI source in this build kit: see root MIT `LICENSE`. Consult `docs/IP_RELEASE_BOUNDARY.md`.

## Staged PDF viewer assets, 2026-10-15

PDF.js code is pinned to npm `pdfjs-dist` 6.4.299 with the original archive's
SHA-512 integrity and per-file SHA-256 values in `assets/pdfjs/provenance.json`.
Unmodified standard font data from that same verified archive is separately
inventoried in `assets/pdfjs/standard_fonts/provenance.json`. Complete accompanying
`LICENSE_FOXIT` and `LICENSE_LIBERATION` files are retained. Font terms are separate
from the renderer's Apache-2.0 code license; the Liberation assets include GPL v2
font exceptions. Independent distribution/source-obligation review remains pending
before external rollout or publication. No blanket license clearance is claimed.
