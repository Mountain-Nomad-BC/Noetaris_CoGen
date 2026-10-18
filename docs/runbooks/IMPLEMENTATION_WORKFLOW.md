# Operating procedure for implementing the 57 task cards

## One card at a time

1. Read `plans/MASTER_BUILD_PLAN.md`, identify the first `BLOCKER` whose prerequisites pass. Use `plans/TASK_LEDGER.csv` for filtering or import into project management.
2. Read `docs/STATUS_MATRIX.md`; do not mistake a helper module for full integration.
3. Create a topic branch (`git switch -c task/ING-02-parser-locators`).
4. Read relevant files in `docs/SOURCE_USAGE_MATRIX.csv`; use Remy as **architecture reference only**, not copyable source. Verify a PX file's direct import closure and licenses if porting.
5. Change only files in target card, plus tests/migrations directly required. Record newly discovered dependencies rather than silently expanding scope.
6. Add unit+integration+adversarial tests for task's negative cases and allowed cases.
7. Execute checks from `scripts/run-checks.ps1` or `.sh`. Any Docker/GPU change also requires actual runtime evidence.
8. Update task status, `docs/STATUS_MATRIX.md` and an ADR if changing a locked architectural invariant.
9. Attach one **result receipt** in `docs/validation/` containing exact commands, stdout summary, environment, changed files, risk, failures and fallback.
10. Merge only after acceptance gate passes; failing tests do not become 'known pass' by documenting them.

## Result receipt template

```markdown
# Result: TASK-ID
Date/time UTC:
Git commit/branch:
OS + Python + Docker + image/model digests:
Changed files:
Dependencies satisfied:
Implementation summary:
Commands executed:
Pass/fail counts and evidence:
Security tests / negative cases:
Known remaining gaps:
Rollback command:
Status: PASS / FAIL / BLOCKED
```

## AI coding model instructions

See `docs/prompts/00_MASTER_AGENT_HANDOFF.md` plus one phase-specific prompt. Assign only one task or small dependency-complete task batch to a coding agent. Never use a sweeping "implement all" instruction unless execution can be reviewed in small atomic commits. Never ask it to fabricate tests, authorizations, GPU usage, license rights or success counts.

## When blocked

Record the exact missing prerequisite and continue a safe independent lane (UI fixtures, docs, synthetic test cases). Do not bypass authority gates, widen network access or grant privileged Docker flags to make a test turn green.
