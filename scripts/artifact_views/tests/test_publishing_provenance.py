"""Tests for provenance schema dispatch and output ownership identity."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from artifact_views.provenance import (  # pylint: disable=import-error
    ArtifactProvenance,
    PublicationProvenance,
    parse_provenance,
)


def _publication() -> PublicationProvenance:
    return PublicationProvenance.from_source(
        source_path=Path("docs/guide.md"),
        source_bytes=b"# Guide\n",
        output_path=Path(".cg-docs/views/documents/docs/guide.html"),
        document_type="generic-markdown",
        renderer_version="0.2.0",
        theme_name="reference",
        theme_version=1,
        generated_at=datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc),
    )


def test_schema_2_records_exact_source_output_and_theme_identity() -> None:
    provenance = _publication()

    assert provenance.provenance_schema_version == 2
    assert provenance.output_path == ".cg-docs/views/documents/docs/guide.html"
    assert provenance.document_type == "generic-markdown"
    assert provenance.theme_name == "reference"
    assert provenance.theme_version == 1
    assert set(provenance.to_dict()) == {
        "documentType",
        "generatedAt",
        "outputPath",
        "provenanceSchemaVersion",
        "rendererVersion",
        "sourcePath",
        "sourceSha256",
        "themeName",
        "themeVersion",
    }


def test_schema_dispatch_preserves_v1_without_upgrading_it() -> None:
    legacy = ArtifactProvenance.from_source(
        source_path=Path(".cg-docs/plans/example.md"),
        source_bytes=b"# Plan\n",
        artifact_schema_version=1,
        renderer_version="0.1.0",
        generated_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
    )

    parsed = parse_provenance(legacy.to_json())

    assert isinstance(parsed, ArtifactProvenance)
    assert parsed == legacy


def test_schema_2_round_trips_with_exact_key_validation() -> None:
    provenance = _publication()

    assert parse_provenance(provenance.to_json()) == provenance
    extra = provenance.to_dict() | {"extra": True}
    with pytest.raises(ValueError, match="fields"):
        parse_provenance(json.dumps(extra))


@pytest.mark.parametrize(
    "mutation",
    (
        lambda data: data | {"provenanceSchemaVersion": 3},
        lambda data: data | {"outputPath": "../outside.html"},
        lambda data: data | {"themeVersion": True},
        lambda data: data | {"documentType": ""},
    ),
)
def test_schema_2_rejects_unknown_or_malformed_identity(mutation) -> None:
    with pytest.raises(ValueError):
        parse_provenance(json.dumps(mutation(_publication().to_dict())))


def test_schema_2_duplicate_keys_fail() -> None:
    raw = _publication().to_json()
    duplicate = raw[:-1] + ',"themeName":"reference"}'

    with pytest.raises(ValueError, match="Duplicate provenance key"):
        parse_provenance(duplicate)