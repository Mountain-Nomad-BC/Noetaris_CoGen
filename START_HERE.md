> Current local integration: **http://127.0.0.1:8790** (`noetaris-integration`, synthetic data, Gemma CPU and MiniLM helper). See [deployment stages](docs/implementation/DEPLOYMENT_STAGES.md) and the latest [handoff](HANDOFF.md). The older original-stack status below does not describe this separate integration project. Production release admission remains denied.

# Start here

Read the [current README](README.md), [deployment state](docs/implementation/DEPLOYMENT_STATE.md), and [full execution ledger](plans/implementation/EXECUTION_STATUS.md).

At the latest read-only check (2026-10-17 11:48 EDT), the Docker services had no host-published ports and `http://127.0.0.1:8787/healthz` was unreachable. Authentication and release admission remain blocked; this is not a host-accessible or release-ready deployment. Compose metadata references an absent overlay and exact runtime provenance is unresolved. Do not start, stop, rebuild, migrate, or repair the existing stack using guessed configuration. Central security, generated execution, AMD and Evolus remain disabled or deferred.

Testing and evidence are separate from deployment. Run `.venv/Scripts/python.exe -m pytest -q` for local tests. `scripts/qualify_local_stack.py` owns disposable resources for end-to-end acceptance. Old live-mutating verification entry points are retired; `scripts/verify_system.py --readiness-only` provides observational live checks.

Current receipts are under `evidence/implementation/`, and the live privacy repair has separate receipts under `evidence/live-evidence-privacy/`. No overall certification or publication clearance is granted by a passing helper or isolated case.
