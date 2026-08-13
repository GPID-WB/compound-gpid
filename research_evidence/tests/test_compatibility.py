"""Created 2026-08-12. Tests for legacy external-record compatibility."""
from __future__ import annotations

from pathlib import Path

import yaml

from research_evidence.compatibility import (
    MigrationDisposition,
    migrate_legacy_record,
    migrate_and_persist_legacy_record,
    persist_quarantine_result,
)
from research_evidence.transactions import ArtifactStore


def test_external_opt_in_is_preserved_as_read_only_quarantine(tmp_path: Path) -> None:
    """Preserve external metadata without fetching, indexing, or approving it."""
    original = {
        "id": "legacy-1",
        "origin": "external-opt-in",
        "url": "https://example.org/paper.pdf",
        "quote": "Copied text",
        "verified": True,
    }
    result = migrate_legacy_record(original, tmp_path)
    assert result.disposition == MigrationDisposition.EXTERNAL_QUARANTINE
    assert result.eligible_for_approval is False
    assert result.preserved_record == original
    assert result.requires_local_verification is True


def test_missing_origin_is_unresolved(tmp_path: Path) -> None:
    """Block activation when legacy provenance does not declare its origin."""
    result = migrate_legacy_record({"id": "legacy-2", "quote": "text"}, tmp_path)
    assert result.disposition == MigrationDisposition.UNRESOLVED
    assert result.eligible_for_approval is False


def test_converted_only_verification_is_flagged(tmp_path: Path) -> None:
    """Require original verification when legacy evidence cites converted text only."""
    result = migrate_legacy_record(
        {
            "id": "legacy-3",
            "origin": "repo-local",
            "original_path": "resources/paper.md",
            "verification_basis": "converted-text",
        },
        tmp_path,
    )
    assert result.disposition == MigrationDisposition.LOCAL_REVIEW_REQUIRED
    assert result.reason == "legacy-converted-authority"
    assert result.eligible_for_approval is False


def test_external_quarantine_persists_read_only_across_reload(tmp_path: Path) -> None:
    """Persist external metadata without making it indexable or approvable."""
    root = tmp_path / "resources"
    root.mkdir()
    record = {
        "id": "legacy-persisted",
        "origin": "external-opt-in",
        "url": "https://example.org/paper.pdf",
    }
    store = ArtifactStore(tmp_path / "evidence")
    result = migrate_and_persist_legacy_record(
        record,
        root,
        store,
        expected_revision=0,
    )

    payload = yaml.safe_load(
        (store.root / "external-quarantine.yaml").read_text(encoding="utf-8")
    )
    assert payload["records"][0]["id"] == "legacy-persisted"
    assert payload["records"][0]["eligible_for_approval"] is False
    assert payload["records"][0]["requires_local_verification"] is True
    reloaded = yaml.safe_load(
        (store.root / "external-quarantine.yaml").read_text(encoding="utf-8")
    )
    assert reloaded == payload
