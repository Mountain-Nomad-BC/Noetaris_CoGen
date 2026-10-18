"""Deterministic reciprocal-rank fusion of already-authorized result IDs.

Caller must apply tenant/document permission filtering BEFORE this function;
result ranking is not an authorization boundary.
"""
from collections import defaultdict


def reciprocal_rank_fusion(ranked_sets: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    if k < 1:
        raise ValueError("k must be positive")
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_sets:
        for rank, item_id in enumerate(dict.fromkeys(ranked), 1):
            scores[item_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))
