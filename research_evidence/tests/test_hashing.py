"""Created 2026-08-12. Tests for resource hashing and file identity."""
from __future__ import annotations

from pathlib import Path

from research_evidence.hashing import file_identity, sha256_file


def test_sha256_file_is_content_deterministic(tmp_path: Path) -> None:
    """Hash the same bytes identically regardless of file metadata."""
    path = tmp_path / "resource.md"
    path.write_text("content", encoding="utf-8")
    first = sha256_file(path)
    path.touch()
    assert sha256_file(path) == first


def test_file_identity_is_stable_for_one_inode(tmp_path: Path) -> None:
    """Expose device/inode identity for explaining an unambiguous move."""
    path = tmp_path / "resource.md"
    path.write_text("content", encoding="utf-8")
    identity = file_identity(path)
    assert identity.device >= 0
    assert identity.inode > 0
    assert identity == file_identity(path)
