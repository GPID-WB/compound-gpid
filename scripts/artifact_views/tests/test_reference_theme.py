"""Tests for the frozen reference theme contract and strict byte stability."""
from __future__ import annotations

# pylint: disable=import-error

from datetime import datetime, timezone
import hashlib
import inspect
from pathlib import Path

from artifact_views.parser import parse_artifact
from artifact_views.provenance import ArtifactProvenance
from artifact_views.reference_theme import REFERENCE_CONTRACT_VERSION, reference_css
from artifact_views.renderer import render_document
from artifact_views.schema import ArtifactKind
from artifact_views.templates import design_contract

FIXTURES = Path(__file__).parent / "fixtures"
FIXED_TIME = datetime(2026, 7, 31, 12, 30, tzinfo=timezone.utc)


def _hash(fixture: str, kind: ArtifactKind) -> str:
    source = (FIXTURES / fixture).read_text(encoding="utf-8")
    source_path = Path(f".cg-docs/{kind.value}s/{fixture}")
    document = parse_artifact(source, source_path, kind)
    provenance = ArtifactProvenance.from_source(
        source_path=source_path,
        source_bytes=source.encode("utf-8"),
        artifact_schema_version=1,
        renderer_version="0.1.0",
        generated_at=FIXED_TIME,
    )
    return hashlib.sha256(render_document(document, provenance)).hexdigest()


def test_reference_theme_is_versioned_and_owns_frozen_tokens_and_css() -> None:
    assert REFERENCE_CONTRACT_VERSION == 1
    assert design_contract()["schemaVersion"] == REFERENCE_CONTRACT_VERSION
    assert "--paper: #f6f5f0" in reference_css()
    assert "@media print" in reference_css()


def test_reference_extraction_preserves_strict_render_bytes() -> None:
    assert _hash("strict_brainstorm.md", ArtifactKind.BRAINSTORM) == (
        "7c6ab9fb46b041076d17c14de67b5adf2633f3a997f2d80e5d45550ae943541e"
    )
    assert _hash("strict_deep_plan.md", ArtifactKind.PLAN) == (
        "f4e3cdb8d7a74a87a1745c19a305b75e3827057097dd191a4db4b9b1e08ad0ce"
    )


def test_strict_renderer_uses_shared_source_owner_loop() -> None:
    implementation = inspect.getsource(render_document)

    assert "render_source_blocks(" in implementation
    assert "CoverageLedger(document).validate" not in implementation
