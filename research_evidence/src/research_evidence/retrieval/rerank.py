"""Created 2026-08-13. Optional local cross-encoder reranking boundary."""
from __future__ import annotations

from collections.abc import Mapping

from ..schemas import SourceUnit
from .profiles import RankedCandidate, _rank_scores


def rerank_candidates(
    units: list[SourceUnit],
    scores: Mapping[str, float],
) -> list[RankedCandidate]:
    """Rerank local candidate scores with deterministic tie-breaking.

    Args:
        units: Candidate source units supplied to a local reranker.
        scores: Reranker scores keyed by source-unit ID.

    Returns:
        Candidates ordered by descending score then source-unit ID.

    Example:
        ``rerank_candidates(units, {units[0].source_unit_id: 0.8})``.
    """
    return _rank_scores(units, scores)
