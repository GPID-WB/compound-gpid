"""Pure metadata edits must validate all blobs before returning an edit set."""

import hashlib
import json

import pytest

from cg_release.events import ControllerError
from cg_release.metadata import SourceBlob, project_version, proposed_edits
from cg_release.models import Changelog, MetadataAdapter


def test_supported_python_projections_and_dual_history() -> None:
    for version, expected in [
        ("1.5.0", "1.5.0"),
        ("1.5.0-alpha.2", "1.5.0a2"),
        ("1.5.0-beta.2", "1.5.0b2"),
        ("1.5.0-rc.2", "1.5.0rc2"),
        ("1.5.0-dev.2", "1.5.0.dev2"),
    ]:
        assert project_version(version, []) == expected
    for value in ["1.5.0-preview.1", "1.5.0-rc", "1.5.0+build", "1.5.0-rc.1.extra"]:
        with pytest.raises(ControllerError):
            project_version(value, [])
    with pytest.raises(ControllerError):
        project_version("1.5.0-dev.1", ["1.5.0b1"])
    assert project_version("1.5.0-rc.1", ["1.5.0b1"]) == "1.5.0rc1"


def edits(kind: str, raw: bytes, version: str = "1.5.0", **kwargs: object) -> tuple:
    """Exercise a single adapter plus a real changelog and manifest, without writes."""
    return proposed_edits(
        [
            MetadataAdapter(
                kind=kind,
                path="metadata",
                pointer="/version" if kind == "json" else None,
            )
        ],
        Changelog(path="CHANGELOG.md", marker="<!-- release -->"),
        {
            "metadata": SourceBlob(raw),
            "CHANGELOG.md": SourceBlob(b"# Changes\n<!-- release -->\n"),
        },
        version=version,
        tag="v" + version,
        line="current",
        source_sha="a" * 40,
        policy_digest="b" * 64,
        request_id="preview",
        notes="Reviewed changes.",
        projections_history={"metadata": []},
        outputs=["dist/file"],
        **kwargs,
    )


@pytest.mark.parametrize(
    "kind,raw",
    [
        ("json", b'{"version":"1.4.2","other":{"keep":true}}'),
        (
            "python-project",
            b'# Keep comment\n[project]\nname = "example"\nversion = "1.4.2"\n',
        ),
        (
            "r-description",
            b"Package: example\nVersion: 1.4.2\nDescription: Keep\n    continuation.\n",
        ),
    ],
)
def test_each_adapter_produces_hashed_edits_without_mutating_input(
    kind: str, raw: bytes
) -> None:
    result = edits(kind, raw)
    assert len(result) == 3
    metadata = next(e for e in result if e.path == "metadata")
    assert metadata.input_digest == hashlib.sha256(raw).hexdigest()
    assert metadata.output_digest == hashlib.sha256(metadata.content).hexdigest()
    assert b"1.5.0" in metadata.content
    assert raw not in {metadata.content}
    if kind == "python-project":
        assert b"# Keep comment" in metadata.content
    if kind == "r-description":
        assert b"    continuation." in metadata.content
    if kind == "json":
        assert json.loads(metadata.content)["other"] == {"keep": True}


@pytest.mark.parametrize(
    "kind,raw,version",
    [
        ("json", b'{"version":"1","version":"2"}', "1.5.0"),
        ("json", b'{"version":3}', "1.5.0"),
        ("json", b"{}", "1.5.0"),
        ("json", b"\xff", "1.5.0"),
        ("python-project", b'[project]\ndynamic=["version"]\nversion="1.0"', "1.5.0"),
        ("python-project", b'[project]\nname="example"', "1.5.0"),
        ("r-description", b"Version: 1.0.0\n", "1.5.0-rc.1"),
        ("r-description", b"Version: 1\nVersion: 2\n", "1.5.0"),
    ],
)
def test_unsupported_or_ambiguous_metadata_fails(
    kind: str, raw: bytes, version: str
) -> None:
    with pytest.raises(ControllerError):
        edits(kind, raw, version)


@pytest.mark.parametrize("path", ["../x", "/x", "C:/x", "x\\y", "CON", "x."])
def test_unsafe_paths_fail_before_edit(path: str) -> None:
    with pytest.raises(ControllerError):
        proposed_edits(
            [MetadataAdapter(kind="json", path=path, pointer="/version")],
            Changelog(path="notes", marker="marker"),
            {},
            version="1.0.0",
            tag="v1.0.0",
            line="current",
            source_sha="a" * 40,
            policy_digest="b" * 64,
            request_id="preview",
            notes="notes",
            projections_history={},
            outputs=[],
        )


def test_symlink_and_oversized_blobs_are_rejected() -> None:
    for mode, raw in [("120000", b"target"), ("100644", b"x" * 1048577)]:
        with pytest.raises(ControllerError):
            SourceBlob(raw, mode=mode)


def test_distinct_json_fields_share_one_validated_file_edit() -> None:
    raw = b'{"version":"1.0.0","nested":{"version":"1.0.0"}}'
    adapters = [
        MetadataAdapter(kind="json", path="package.json", pointer=p)
        for p in ("/version", "/nested/version")
    ]
    kwargs = dict(
        version="1.1.0",
        tag="v1.1.0",
        line="current",
        source_sha="a" * 40,
        policy_digest="b" * 64,
        request_id="preview",
        notes="notes",
        projections_history={},
        outputs=[],
    )
    blobs = {"package.json": SourceBlob(raw), "notes": SourceBlob(b"marker")}
    result = proposed_edits(
        adapters, Changelog(path="notes", marker="marker"), blobs, **kwargs
    )
    file_edit = next(e for e in result if e.path == "package.json")
    assert json.loads(file_edit.content) == {
        "version": "1.1.0",
        "nested": {"version": "1.1.0"},
    }
    assert (
        len(result) == 3 and file_edit.input_digest == hashlib.sha256(raw).hexdigest()
    )
    with pytest.raises(ControllerError):
        proposed_edits(
            [adapters[0], adapters[0]],
            Changelog(path="notes", marker="marker"),
            blobs,
            **kwargs,
        )


def test_reapplying_complete_edit_set_is_idempotent() -> None:
    adapter = MetadataAdapter(kind="json", path="package.json", pointer="/version")
    changelog = Changelog(path="notes", marker="marker")
    kwargs = dict(
        version="1.1.0",
        tag="v1.1.0",
        line="current",
        source_sha="a" * 40,
        policy_digest="b" * 64,
        request_id="preview",
        notes="notes",
        projections_history={},
        outputs=[],
    )
    first = proposed_edits(
        [adapter],
        changelog,
        {
            "package.json": SourceBlob(b'{"version":"1.0.0"}'),
            "notes": SourceBlob(b"marker"),
        },
        **kwargs,
    )
    again = proposed_edits(
        [adapter], changelog, {e.path: SourceBlob(e.content) for e in first}, **kwargs
    )
    assert [(e.path, e.content) for e in first] == [(e.path, e.content) for e in again]
