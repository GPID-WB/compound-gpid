"""Created 2026-08-13. Optional local sparse retrieval adapter boundary."""
from __future__ import annotations

from collections.abc import Mapping

from ..schemas import SourceUnit
from .profiles import RankedCandidate, _rank_scores


def rank_sparse(
    units: list[SourceUnit],
    scores: Mapping[str, float],
) -> list[RankedCandidate]:
    """Rank sparse-adapter scores with deterministic source-unit tie-breaking.

    Args:
        units: Source units retrieved by the local sparse adapter.
        scores: Adapter scores keyed by source-unit ID.

    Returns:
        Candidates ordered by descending score then source-unit ID.

    Example:
        ``rank_sparse(units, {units[0].source_unit_id: 0.8})``.
    """
    return _rank_scores(units, scores)
