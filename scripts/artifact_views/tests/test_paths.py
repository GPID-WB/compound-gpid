"""Tests for canonical artifact source and mirrored view paths."""
from __future__ import annotations

from pathlib import Path

import pytest

from artifact_views.errors import ArtifactPathError
from artifact_views.paths import resolve_artifact_paths
from artifact_views.schema import ArtifactKind


def _write(path: Path, content: str = "# Artifact\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("source", "kind", "view"),
    (
        (
            ".cg-docs/brainstorms/idea.md",
            ArtifactKind.BRAINSTORM,
            ".cg-docs/views/brainstorms/idea.html",
        ),
        (
            ".cg-docs/plans/nested/plan.v2.md",
            ArtifactKind.PLAN,
            ".cg-docs/views/plans/nested/plan.v2.html",
        ),
    ),
)
def test_source_maps_to_mirrored_view(
    tmp_path: Path,
    source: str,
    kind: ArtifactKind,
    view: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / source)

    paths = resolve_artifact_paths(root, root / source)

    assert paths.kind is kind
    assert paths.source_relative.as_posix() == source
    assert paths.view_relative.as_posix() == view
    assert paths.view_path == root / view


def test_relative_source_path_is_anchored_to_project_root(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / ".cg-docs/plans/with space.md")

    paths = resolve_artifact_paths(root, Path(".cg-docs/plans/with space.md"))

    assert paths.source_path == root / ".cg-docs/plans/with space.md"


@pytest.mark.parametrize(
    "source",
    (
        ".cg-docs/solutions/not-supported.md",
        ".cg-docs/plans/not-markdown.txt",
        ".cg-docs/plans/archive.tar.md.txt",
    ),
)
def test_unsupported_source_location_or_suffix_fails(
    tmp_path: Path,
    source: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / source)

    with pytest.raises(ArtifactPathError):
        resolve_artifact_paths(root, root / source)


def test_source_outside_project_fails(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = _write(tmp_path / "outside.md")

    with pytest.raises(ArtifactPathError, match="outside project root"):
        resolve_artifact_paths(root, outside)


def test_missing_source_fails(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    with pytest.raises(ArtifactPathError, match="regular file"):
        resolve_artifact_paths(root, root / ".cg-docs/plans/missing.md")


def test_source_symlink_and_symlink_ancestor_fail(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    target = _write(outside / "plan.md")
    source_parent = root / ".cg-docs/plans"
    source_parent.mkdir(parents=True)
    (source_parent / "linked.md").symlink_to(target)

    with pytest.raises(ArtifactPathError, match="symlink|link"):
        resolve_artifact_paths(root, source_parent / "linked.md")

    (source_parent / "linked.md").unlink()
    source_parent.rmdir()
    source_parent.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ArtifactPathError, match="symlink|link"):
        resolve_artifact_paths(root, source_parent / "plan.md")
