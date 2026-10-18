# Release acceptance matrix

Overall verdict: DENY. Local developer evidence does not constitute independent release acceptance.

| Area | Current evidence | Remaining acceptance |
| --- | --- | --- |
| Local frontend/API | Production build and focused preparation tests pass; exact running identity in state/integration/identity.json | See newest HANDOFF.md receipts for frozen regression, 19 HTTP checks, six desktop/mobile document workflows, separate reviewer workflow, 11 core navigation pages, 32 operations permission cases and 50-table restore; independent acceptance remains outstanding |
| Full feature set | Live core workspace and eight read-only operations screens; unavailable features remain explicitly gated | Workflow/agent/template/evaluation/execution features are not all live; do not claim complete integration |
| Split-origin security | Exact owned same-site origins, credentialed CORS, CSRF and cookie contract tests | Actual registered Google/GitHub flows in production Chromium and Firefox |
| Firebase | Strict public static bundler, SPA/cache/CSP templates, no source maps | Confirm project/site/domain, test real CSP, approve publication |
| OCI | Hardened ARM64 Compose/edge/systemd templates, fail-closed release gate | Actual ARM64 images/hardware/performance, TLS/firewall, production backup/restore |
| Database services | Verified-CA transport support and contract tests | Two services and intended roles not identified; no live linking |
| AMD | Token admission and boundary fixtures; historical synthetic Gemma API probe | Protected owned ROCm/vLLM deployment, real tokenizer/accounting/export and integrated fallback dispatch |
| Evolus | Strict configuration/adapter/error contracts; mocked tests | Optional NOT_CONFIGURED; missing verified endpoint/application/workflow/agent/extractor/schema, then authenticated live E2E |
| Security | Rebuilt frontend runtime Scout reports zero detected findings; five HIGH build-tool findings remain. API Scout retains26LOW/1MEDIUM/1HIGH; no suppression | Remediation and canonical managed scan plus independent reviewer |
| Rights/private content | Existing gates retained | Independent rights, identity/ACL and criterion acceptance; private-user content remains denied |

Current observations and exact new receipts are recorded at the top of HANDOFF.md. Earlier receipts remain historical when source or image identities change. No successful remote provider commissioning is inferred from mocks, catalogs or readable keys.
