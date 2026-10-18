# Package build check record — October 12, 2026

**Environment:** authoring container, Python 3.13 runtime for these tests; project targets Python >=3.12. Docker Engine and AMD GPU were not available. This is **not** a claim of successful deployment.

Commands actually executed (from package root):

```bash
PYTHONPATH=src pytest -q
python evaluations/run_fixture_baseline.py
python scripts/validate_compose_security.py
python scripts/release_audit.py .
python -m compileall -q src scripts evaluations
```

Results:

- `16 passed` Python unit tests, including 6 new contract/gate/retrieval helper tests (no database integration).
- `5/5` deterministic synthetic fixture cases: C001–C004 extraction/locator, K001 contradiction.
- Static Docker Compose security-manifest check: `PASSED` (not a running-container security test).
- Basic offline release text scan: `PASSED` (not a full secret/license/history scan).
- Python compilation: successful.

Unverified:

- Docker image builds, DB health and actual Compose startup/restart.
- Synthetic API seed through live database (`scripts/verify_local.py`).
- Additive target SQL migration on actual Postgres.
- General PDF/Markdown/TurnBurn ingestion and source indexing.
- Complete PX memory and canonical knowledge admission.
- AMD/ROCm vLLM GPU, vLLM model endpoint, latency and billing.
- Evolus REST event workspace and business workflow.
- Public OIDC/TLS/security review and functional hosted app.

Each missing result is a separate gate in `docs/validation/RELEASE_GATES.md` and `plans/TASK_LEDGER.csv`.
