"""Tests for normalized source identity and deterministic provenance."""
from __future__ import annotations

# pylint: disable=import-error

from datetime import datetime, timezone
import hashlib
from pathlib import Path

import pytest

from artifact_views.errors import ArtifactReadError
from artifact_views.provenance import (
    ArtifactProvenance,
    normalized_source_bytes,
    source_sha256,
)


def test_normalization_removes_one_bom_and_normalizes_all_newlines() -> None:
    source = "\ufeffalpha\r\nbeta\rgamma\n"

    assert normalized_source_bytes(source.encode("utf-8")) == b"alpha\nbeta\ngamma\n"


def test_normalization_preserves_unicode_whitespace_and_trailing_newlines() -> None:
    source = "\ufeff\ufeffcaf\u00e9  \r\n\r\n"
    expected = "\ufeffcaf\u00e9  \n\n".encode("utf-8")

    assert normalized_source_bytes(source.encode("utf-8")) == expected
    assert source_sha256(source.encode("utf-8")) == hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest()


def test_source_hash_distinguishes_bom_and_newline_bytes() -> None:
    variants = (b"alpha\n", b"alpha\r\n", b"\xef\xbb\xbfalpha\n")

    assert len({source_sha256(value) for value in variants}) == len(variants)


def test_invalid_utf8_fails_with_actionable_read_error() -> None:
    with pytest.raises(ArtifactReadError, match="strict UTF-8"):
        normalized_source_bytes(b"\xff\xfe")


def test_provenance_is_deterministic_for_fixed_complete_inputs() -> None:
    generated_at = datetime(2026, 7, 31, 12, 30, tzinfo=timezone.utc)
    provenance = ArtifactProvenance.from_source(
        source_path=Path(".cg-docs/plans/example.md"),
        source_bytes=b"alpha\r\n",
        artifact_schema_version=1,
        renderer_version="0.1.0",
        generated_at=generated_at,
    )

    assert provenance.source_sha256 == hashlib.sha256(b"alpha\r\n").hexdigest()
    assert provenance.generated_at == "2026-07-31T12:30:00Z"
    assert provenance.to_json() == provenance.to_json()
    assert provenance.to_dict() == {
        "artifactSchemaVersion": 1,
        "generatedAt": "2026-07-31T12:30:00Z",
        "rendererVersion": "0.1.0",
        "sourcePath": ".cg-docs/plans/example.md",
        "sourceSha256": provenance.source_sha256,
    }


def test_provenance_requires_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        ArtifactProvenance.from_source(
            source_path=Path(".cg-docs/plans/example.md"),
            source_bytes=b"alpha\n",
            artifact_schema_version=1,
            renderer_version="0.1.0",
            generated_at=datetime(2026, 7, 31, 12, 30),
        )
