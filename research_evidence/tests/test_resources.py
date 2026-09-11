"""Created 2026-08-12. Tests for deterministic local resource discovery."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from research_evidence.config import RuntimeSettings
from research_evidence.errors import PathPolicyError
from research_evidence.resources import (
    ResourceEventKind,
    ResourceSnapshot,
    discover_resources,
)


def _settings(tmp_path: Path) -> RuntimeSettings:
    """Create isolated project/resource roots for discovery tests."""
    resources = tmp_path / "resources"
    resources.mkdir()
    return RuntimeSettings.from_paths(tmp_path, resources)


def test_discovery_reports_new_and_unsupported_resources(tmp_path: Path) -> None:
    """Discover supported files and report unsupported files explicitly."""
    settings = _settings(tmp_path)
    (settings.resources_root / "notes.md").write_text("text", encoding="utf-8")
    (settings.resources_root / "data.csv").write_text("a,b", encoding="utf-8")

    result = discover_resources(settings)

    assert [item.relative_path for item in result.resources] == ["notes.md"]
    assert [event.kind for event in result.events] == [ResourceEventKind.NEW, ResourceEventKind.UNSUPPORTED]
    assert result.events[1].relative_path == "data.csv"


def test_unchanged_hash_ignores_timestamp_changes(tmp_path: Path) -> None:
    """Classify identical bytes as unchanged even when mtime metadata changes."""
    settings = _settings(tmp_path)
    path = settings.resources_root / "notes.md"
    path.write_text("text", encoding="utf-8")
    previous = discover_resources(settings).snapshot()
    os.utime(path, ns=(1_000_000_000, 2_000_000_000))

    result = discover_resources(settings, previous)

    assert [event.kind for event in result.events] == [ResourceEventKind.UNCHANGED]


def test_changed_bytes_are_revised_at_the_same_path(tmp_path: Path) -> None:
    """Detect a same-path byte revision without relying on file timestamps."""
    settings = _settings(tmp_path)
    path = settings.resources_root / "notes.md"
    path.write_text("old", encoding="utf-8")
    previous = discover_resources(settings).snapshot()
    path.write_text("new", encoding="utf-8")

    result = discover_resources(settings, previous)

    assert result.events[0].kind == ResourceEventKind.CHANGED
    assert result.events[0].relative_path == "notes.md"
    assert result.events[0].resource_id == previous.resources[0].resource_id
    assert result.resources[0].resource_id == previous.resources[0].resource_id


def test_unambiguous_move_preserves_resource_identity(tmp_path: Path) -> None:
    """Preserve logical identity when one unchanged file moves within the root."""
    settings = _settings(tmp_path)
    original = settings.resources_root / "old.md"
    original.write_text("content", encoding="utf-8")
    previous = discover_resources(settings).snapshot()
    original.rename(settings.resources_root / "nested.md")

    result = discover_resources(settings, previous)

    assert result.events[0].kind == ResourceEventKind.MOVED
    assert result.events[0].previous_path == "old.md"
    assert result.events[0].relative_path == "nested.md"
    assert result.events[0].resource_id == previous.resources[0].resource_id
    assert result.resources[0].resource_id == previous.resources[0].resource_id


def test_duplicate_content_requires_review(tmp_path: Path) -> None:
    """Flag duplicate bytes instead of silently choosing a source identity."""
    settings = _settings(tmp_path)
    (settings.resources_root / "one.md").write_text("same", encoding="utf-8")
    (settings.resources_root / "two.md").write_text("same", encoding="utf-8")

    result = discover_resources(settings)

    assert all(event.kind == ResourceEventKind.DUPLICATE_CONTENT for event in result.events)
    assert all(event.requires_review for event in result.events)


def test_removed_resource_is_reported(tmp_path: Path) -> None:
    """Emit a removal event for a previous resource absent from the new scan."""
    settings = _settings(tmp_path)
    path = settings.resources_root / "gone.md"
    path.write_text("content", encoding="utf-8")
    previous = discover_resources(settings).snapshot()
    path.unlink()

    result = discover_resources(settings, previous)

    assert result.events[0].kind == ResourceEventKind.REMOVED
    assert result.events[0].relative_path == "gone.md"


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    """Reject a resource link that resolves outside the configured corpus."""
    settings = _settings(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("outside-content", encoding="utf-8")
    link = settings.resources_root / "escape.md"
    link.symlink_to(outside)

    with pytest.raises(PathPolicyError, match="symbolic link"):
        discover_resources(settings)


def test_snapshot_round_trip_is_deterministic(tmp_path: Path) -> None:
    """Serialize and reload a snapshot without losing content identity."""
    settings = _settings(tmp_path)
    (settings.resources_root / "notes.md").write_text("text", encoding="utf-8")

    snapshot = discover_resources(settings).snapshot()
    restored = ResourceSnapshot.model_validate(snapshot.model_dump(mode="json"))

    assert restored == snapshot
