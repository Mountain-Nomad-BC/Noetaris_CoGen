"""Pure evaluators: return reasons, never mutate authoritative state."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    eligible_for_review: bool
    reasons: tuple[str, ...]


def assess_candidate(*, source_count: int, conflicting: bool, eval_total: int,
                     eval_passed: int, authorized_reviewer_present: bool) -> GateResult:
    issues = []
    if source_count < 1:
        issues.append("missing attributable source")
    if conflicting:
        issues.append("unresolved contradictory evidence")
    if eval_total <= 0:
        issues.append("evaluation coverage missing")
    elif eval_passed != eval_total:
        issues.append("regression suite not fully passing")
    if not authorized_reviewer_present:
        issues.append("independent human reviewer missing")
    return GateResult(not issues, tuple(issues))
