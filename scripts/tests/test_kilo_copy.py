"""Tests for checksum-owned, no-follow Kilo copy-directory synchronization."""
from __future__ import annotations

from pathlib import Path

import pytest

import cg_kilo_copy as kilo_copy


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_sync_writes_marker_and_preserves_modified_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "commands/cg-test.md", "source-v1")
    _write(source / "skills/cg-test/SKILL.md", "---\nname: cg-test\ndescription: test\n---\n")

    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert (target / "commands/cg-test.md").read_text(encoding="utf-8") == "source-v1"
    assert (target / kilo_copy.MARKER_NAME).is_file()

    _write(target / "commands/cg-test.md", "user-edit")
    _write(source / "commands/cg-test.md", "source-v2")
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert (target / "commands/cg-test.md").read_text(encoding="utf-8") == "user-edit"


def test_sync_removes_only_unchanged_stale_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write(source / "old.md", "old")
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    (source / "old.md").unlink()
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert not (target / "old.md").exists()

    _write(source / "old.md", "old")
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    _write(target / "old.md", "user-edit")
    (source / "old.md").unlink()
    kilo_copy.sync_directory(source, target, ".kilo/skills")
    assert (target / "old.md").read_text(encoding="utf-8") == "user-edit"


def test_sync_rejects_source_symlink(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    try:
        (source / "linked.md").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this host")

    with pytest.raises(kilo_copy.CopyError, match="link or reparse"):
        kilo_copy.sync_directory(source, target, ".kilo/skills")
