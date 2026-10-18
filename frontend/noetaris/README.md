# NOETARIS CoGen frontend integration

Working React/Vite frontend for the existing NSAI Python service. The supplied v0.2 source and handoff remain preserved byte-identically in the original download location and are bound by `../../evidence/noetaris-integration/import-manifest.json`.

Live mode is the default. It requires the same-origin Python proxy; it never substitutes demo fixtures on errors. Canonical local credential verification, browser session introspection, explicit Google/GitHub login/signup/linking and logout are integrated. Provider credentials remain optional and uncommissioned. Only the live library/source inspector is currently admitted for identities whose backend capabilities explicitly admit content access. Individual content admission and unfinished screens remain gated. Full product/release certification is incomplete.

## Build and checks

Node 22 is pinned in the Docker builder. `npm ci --ignore-scripts --no-fund --no-audit`, then `npm run build`. The build runs source checks and transport/contract tests. `package-lock.json` fixes dependency resolution. Build dependency advisories remain open; do not interpret a successful build as risk acceptance.

To preview labeled fixtures locally, explicitly set `VITE_NOETARIS_MODE=demo` before `npm run dev`. A local Vite preview is not the deployed live service and does not supply authenticated API routing. `.env.example` describes demo preview only. Live deployment uses the project Compose overlays and the Dockerfile, which selects live mode.

## Integrated Docker surfaces

- `../../deploy/local/compose.noetaris.yaml`: nonroot read-only static UI and same-origin Python API/auth proxy.
- `../../deploy/local/compose.noetaris-tls.yaml`: optional supplied loopback TLS certificate/key.
- Existing OAuth provider overlays: canonical Python implementation, disabled until configured and qualified.

Do not run against or replace the existing live data stack as part of candidate verification. Qualification runners create isolated owned API/parser/PostgreSQL/browser resources and remove only those resources.

See `../../docs/implementation/NOETARIS_AUTH_INTEGRATION.md` and `../../plans/implementation/NOETARIS_FRONTEND_INTEGRATION.md` for current scoped evidence, integration order, limitations and rollback. The historical supplied `docs/VALIDATION_REPORT.md` describes the pre-integration source recovery, not current qualification.

Live library uses actual authorized keyset pages, dynamic upload limits, durable parser/storage receipts, source manifests and SHA-verified original downloads. Queue state is separate from indexing publication, factual review and OCR/geometry accuracy. Source previews are explicitly bounded; originals are unchanged. Browser cloud speech recognition is disabled in live mode while local-first voice integration remains unfinished. No external provider is mandatory and cash-funded dispatch remains prohibited by the backend.
