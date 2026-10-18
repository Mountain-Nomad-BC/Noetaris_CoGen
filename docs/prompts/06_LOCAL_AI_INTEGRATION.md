# COPY TO CODING MODEL — local Docker AI bring-up

Work only inside clean-room NSAI code. Do not copy Remy proprietary source. Preserve candidate-only evidence semantics and immutable source history. Objective: fully exercise API + UI + Postgres + Ollama before AMD GPU work.

1. Read `LOCAL_AI_START_HERE.md`, `plans/LOCAL_FIRST_IMPLEMENTATION.md`, base Compose and overlay, `src/nsai/inference.py`, `src/nsai/api.py`, all scripts/tests.
2. Execute `python -m pytest -q` and `python scripts/validate_compose_security.py`. Run `docker compose ... config --quiet` before `up`.
3. Run `scripts/local-ai-start.ps1` (or .sh). Confirm images and services healthy, local model pulled.
4. Run `scripts/verify_local.py` and `scripts/verify_local_ai.py`. Use browser UI to inspect evidence, ask deterministic question and Ask connected AI. Confirm nonzero source references and correct mode/model.
5. Record actual outputs, container logs and local model timing. Do not claim GPU/AMD test until on that hardware.
6. Resolve integration issues with minimal patches and add regression tests. Do not weaken cgroup, seccomp, cap_drop, no-new-privileges, loopback-only ports or remove auth.
7. Then implement G3 ingestion in bounded increments, golden tests and UI job reporting. Proceed G4/G5 only after source locators and permission checks work. Carry a task-based completion ledger with actual proof per gate.

DONE when an actual local model answers evidence-grounded questions from Docker through the browser, input/output is clearly labelled unverified, and run/restart tests pass. Avoid imaginary tool/agent actions and automated promotion.
