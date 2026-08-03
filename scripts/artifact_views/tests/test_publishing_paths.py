"""Tests for generic source routing and portable destination identity."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# pylint: disable=import-error
from artifact_views.errors import ArtifactPathError
from artifact_views.paths import resolve_generic_paths
from artifact_views.writer import ViewNamespace
# pylint: enable=import-error


def _write(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Guide\n", encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("source", "output"),
    (
        ("README.md", ".cg-docs/views/documents/README.html"),
        ("docs/nested/guide.v2.md", ".cg-docs/views/documents/docs/nested/guide.v2.html"),
    ),
)
def test_generic_default_output_mirrors_complete_source_path(
    tmp_path: Path,
    source: str,
    output: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / source)

    paths = resolve_generic_paths(root, source)

    assert paths.source_relative.as_posix() == source
    assert paths.output_relative.as_posix() == output
    assert paths.output_identity == output
    assert paths.document_type == "generic-markdown"
    assert paths.destination.namespace is ViewNamespace.DOCUMENTS
    assert paths.destination.relative.as_posix() == output


def test_explicit_output_stays_in_registered_documents_namespace(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "docs/guide.md")

    paths = resolve_generic_paths(
        root,
        "docs/guide.md",
        Path(".cg-docs/views/documents/custom/guide.html"),
    )

    assert paths.output_relative.as_posix().endswith("custom/guide.html")


@pytest.mark.parametrize(
    "source",
    (
        ".cg-docs/brainstorms/idea.md",
        ".cg-docs/plans/plan.md",
        ".cg-docs/views/documents/rendered.md",
    ),
)
def test_generic_resolver_rejects_typed_and_generated_roots(
    tmp_path: Path,
    source: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / source)

    with pytest.raises(ArtifactPathError, match="cg-render-artifact|generated"):
        resolve_generic_paths(root, source)


@pytest.mark.parametrize(
    "output",
    (
        "outside.html",
        ".cg-docs/views/plans/typed.html",
        ".cg-docs/views/documents/../escape.html",
        ".cg-docs/views/documents/CON.html",
        ".cg-docs/views/documents/trailing. /file.html",
        ".cg-docs/views/documents/name:stream.html",
        ".cg-docs\\views\\documents\\backslash.html",
    ),
)
def test_explicit_output_rejects_nonportable_identity(
    tmp_path: Path,
    output: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "guide.md")

    with pytest.raises(ArtifactPathError, match="portable|documents|namespace"):
        resolve_generic_paths(root, "guide.md", output)


@pytest.mark.parametrize(
    "output",
    (
        ".CG-DOCS/views/documents/guide.html",
        ".cg-docs/VIEWS/documents/guide.html",
        ".cg-docs/views/DOCUMENTS/guide.html",
    ),
)
def test_explicit_output_rejects_mixed_case_registered_namespace(
    tmp_path: Path,
    output: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "guide.md")

    with pytest.raises(ArtifactPathError, match="documents|namespace"):
        resolve_generic_paths(root, "guide.md", output)


def test_generic_source_hard_link_alias_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    original = _write(root / "original.md")
    alias = root / "alias.md"
    os.link(original, alias)

    with pytest.raises(ArtifactPathError, match="hard link|multiple"):
        resolve_generic_paths(root, alias)


def test_output_identity_normalizes_case_for_portable_ownership(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "Guide.md")

    paths = resolve_generic_paths(root, "Guide.md")

    assert paths.ownership_key == paths.output_identity.casefold()


@pytest.mark.parametrize(
    "source",
    ("CON.md", "docs/name:.md", "docs/trailing./guide.md"),
)
@pytest.mark.skipif(os.name == "nt", reason="Windows cannot create these lexical names")
def test_default_output_rejects_nonportable_source_components(
    tmp_path: Path,
    source: str,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / source)

    with pytest.raises(ArtifactPathError, match="portable"):
        resolve_generic_paths(root, source)


@pytest.mark.skipif(os.name == "nt", reason="requires case-sensitive sibling names")
def test_existing_case_equivalent_output_collision_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _write(root / "docs/Guide.md")
    existing = root / ".cg-docs/views/documents/docs/guide.html"
    existing.parent.mkdir(parents=True)
    existing.write_text("owned by lower-case source", encoding="utf-8")

    with pytest.raises(ArtifactPathError, match="case|collision"):
        resolve_generic_paths(root, "docs/Guide.md")