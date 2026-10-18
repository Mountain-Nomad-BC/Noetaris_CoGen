# Copy/paste handoff — NSAI master engineering instructions

You are implementing NSAI, a standalone evidence-governed knowledge operations prototype for AMD Developer Hackathon ACT III (Oct 12–18 2026). Work in this repository only. Read `README.md`, `plans/MASTER_BUILD_PLAN.md`, `plans/TASK_LEDGER.csv`, `docs/ARCHITECTURE_AND_INTERFACES.md`, `docs/IP_RELEASE_BOUNDARY.md`, `docs/runbooks/DOCKER_AND_SANDBOX.md`, and `docs/STATUS_MATRIX.md` before editing.

## Objective

Produce a working end-to-end synthetic-industrial-supplier demo: ingest source revisions -> preserve source hashes and spans -> identify contradictory candidate claims -> deliver a source-grounded answer -> execute real AMD ROCm/vLLM inference -> (optional) run a human-reviewed Evolus business workflow. Always distinguish implemented from scaffolded/unverified components.

## Source-use rules

- The Remy/RIE ZIP is proprietary per its supplied root LICENSE. Do NOT copy implementation, frontend, logo, data, tests or images from it to a public repository without actual authorization. Its TurnBurn and UI architecture are design references for independent new code.
- The PX ZIP is Apache-2.0 at root. Do NOT import PX wholesale; trace direct dependencies, verify notices and source provenance before adapting any file. This build kit contains **no copied PX source**; use `docs/SOURCE_USAGE_MATRIX.csv` as navigation only.
- Never invent licenses or move employer knowledge into event fixtures.

## Security and correctness invariants

- Candidate claims are not verified facts. No model output can approve itself, promote canon, activate index or release executable skill.
- Source locators must resolve to immutable source revision content.
- No Docker socket, privileged containers, host networking shortcuts, hardcoded keys, unauthenticated public API, or treating a read-only smoke container as an execution sandbox.
- On AMD Linux, verify actual ROCm devices and GPU use; PX Windows Job Object Gremlin enforcement is NOT Linux sandbox enforcement.
- Public hosting is disallowed until real OIDC/TLS, authorization, rate limits, backup, secret scanning and container/image review pass.
- Do not fake test passes, runtime measurements or AMD/Evolus logs. Report unverified clearly.

## Task management

1. Pick one unblocked task by ID from `plans/TASK_LEDGER.csv`, obey dependencies and prioritize current gate.
2. Inspect code and write failing unit/integration/adversarial tests where feasible.
3. Implement the smallest well-typed portable change. Use explicit tests, migrations and boundaries.
4. Run `python -m pytest -q`, `python scripts/validate_compose_security.py`, `python evaluations/run_fixture_baseline.py`; for Docker tasks additionally run actual `docker compose ...` and save evidence.
5. Update ledger status, `docs/STATUS_MATRIX.md`, and a `docs/validation/results/TASK-ID.md` receipt with exact commands/results, changes, blockers and rollback.
6. Never run model-generated code without a verified independent Linux sandbox and scoped owner authorization.

## Completion report required after each step

TASK IDs closed, changed files, command/test results, runtime or GPU evidence, failures/known gaps, exact next task IDs. If blocked, stop that task; do not bypass security or admission gates to continue. Ask only for genuinely unavailable external credentials/approvals/host access, and perform all safe offline work first.

## Preserve current system

Keep existing FastAPI API contract and Docker startup working. Build with additive changes/migrations and test backwards compatibility. Preserve local demo behavior even when AMD inference is unavailable. Avoid rewriting entire application to a new framework unless there is measurable benefit.
