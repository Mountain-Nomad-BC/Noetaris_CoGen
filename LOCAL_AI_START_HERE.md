> Current local integration: **http://127.0.0.1:8790** (`noetaris-integration`, synthetic data, Gemma CPU and MiniLM helper). See [deployment stages](docs/implementation/DEPLOYMENT_STAGES.md) and the latest [handoff](HANDOFF.md). The older original-stack status below does not describe this separate integration project. Production release admission remains denied.

# Local CPU foundation

Start with the [current README](README.md), [execution ledger](plans/implementation/EXECUTION_STATUS.md) and [remaining work](docs/implementation/REMAINING_WORK.md). Earlier starter instructions are historical and do not define the current implementation.

The CPU Docker profile describes the intended local model/parser/API layout; it does not attest to the current runtime. At the latest read-only check (2026-10-17 11:48 EDT), no service had a host-published port and `http://127.0.0.1:8787/healthz` was unreachable. Authentication and release admission remain blocked, and the runtime Compose overlay is unresolved. Do not start, stop, rebuild, migrate, or repair the existing stack from inferred configuration.

Routine tests use `.venv/Scripts/python.exe -m pytest -q`. Integration qualification uses owned disposable resources; evidence is under `evidence/implementation/`. Do not use live user data for acceptance fixtures. The full required plan remains open and does not have blanket certification.

The deployment entry point is `powershell -File scripts/start-cpu.ps1`; it builds images and migrates the database. It is mutating and must not be run against the current stack. A qualified release, recovered/approved exact Compose configuration, release admission, and reviewed rollback must precede any deployment or shutdown operation against persistent user data.

Central security and generated execution stay disabled. Optional OCR admission is restricted to its proven scope. All future hardware/provider integrations remain deferred.
