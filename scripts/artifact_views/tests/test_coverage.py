"""Tests for exact-once substantive source-block render ownership."""
from __future__ import annotations

from pathlib import Path

import pytest

from artifact_views.coverage import CoverageLedger, RenderedOwner
from artifact_views.errors import ArtifactCoverageError
from artifact_views.parser import parse_artifact
from artifact_views.schema import ArtifactKind

FIXTURES = Path(__file__).parent / "fixtures"


def _document():
    return parse_artifact(
        (FIXTURES / "strict_plan.md").read_text(encoding="utf-8"),
        Path(".cg-docs/plans/strict.md"),
        ArtifactKind.PLAN,
    )


def test_complete_exact_once_coverage_passes() -> None:
    document = _document()
    owners = tuple(
        RenderedOwner(f"owner-{index}", block.source_id)
        for index, block in enumerate(document.substantive_blocks, start=1)
    )

    CoverageLedger(document).validate(owners)


def test_missing_source_owner_fails() -> None:
    document = _document()
    owners = tuple(
        RenderedOwner(f"owner-{index}", block.source_id)
        for index, block in enumerate(document.substantive_blocks[:-1], start=1)
    )

    with pytest.raises(ArtifactCoverageError, match="Missing rendered owner"):
        CoverageLedger(document).validate(owners)


def test_duplicate_source_owner_fails() -> None:
    document = _document()
    source_id = document.substantive_blocks[0].source_id

    with pytest.raises(ArtifactCoverageError, match="Duplicate rendered owner"):
        CoverageLedger(document).validate(
            (
                RenderedOwner("first", source_id),
                RenderedOwner("second", source_id),
            )
        )


def test_unknown_source_owner_fails() -> None:
    document = _document()

    with pytest.raises(ArtifactCoverageError, match="unknown source block"):
        CoverageLedger(document).validate(
            (RenderedOwner("invented", "block-9999"),)
        )


def test_duplicate_render_owner_id_fails() -> None:
    document = _document()

    with pytest.raises(ArtifactCoverageError, match="Duplicate rendered owner ID"):
        CoverageLedger(document).validate(
            (
                RenderedOwner("same", document.substantive_blocks[0].source_id),
                RenderedOwner("same", document.substantive_blocks[1].source_id),
            )
        )


def test_derived_owner_cannot_satisfy_source_coverage() -> None:
    document = _document()
    source_id = document.substantive_blocks[0].source_id

    with pytest.raises(ArtifactCoverageError, match="Derived owner"):
        RenderedOwner("derived-map", source_id, derived=True)
