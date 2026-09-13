"""Execute isolated preparation against real Git trees, never a remote target."""

import hashlib
import subprocess
from dataclasses import replace

import pytest

from cg_release.events import ControllerError
from cg_release.metadata import Edit, SourceBlob, proposed_edits
from cg_release.models import Changelog, MetadataAdapter
from cg_release.preparation import TreeEntry, apply_edits


def git(path, *args):
    """Run fixture-only Git commands in a temporary repository."""
    return subprocess.run(
        ["git", "-c", "core.autocrlf=false", *args],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def source(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "--quiet", "--template=")
    raw = b'{"version":"1.0.0"}\r\n'
    (repo / "package.json").write_bytes(raw)
    (repo / "keep.txt").write_bytes(b"unchanged\n")
    git(repo, "add", "--", ".")
    tree = git(repo, "write-tree")
    entries = []
    for row in git(repo, "ls-files", "--stage").splitlines():
        head, path = row.split("\t")
        mode, oid, _ = head.split()
        entries.append(TreeEntry(path, mode, oid))
    content = b'{"version":"1.1.0"}\r\n'
    edit = Edit(
        "package.json",
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(content).hexdigest(),
        content,
    )
    return repo, tree, entries, {"package.json": SourceBlob(raw)}, edit


def test_exact_expected_tree_preserves_source_worktree_and_format(source):
    repo, tree, entries, blobs, edit = source
    before = git(repo, "status", "--porcelain")
    prepared = apply_edits(tree, entries, blobs, (edit,), {edit.path})
    assert git(repo, "status", "--porcelain") == before
    assert (repo / "package.json").read_bytes() == blobs[edit.path].content
    (repo / "package.json").write_bytes(edit.content)
    git(repo, "add", "--", "package.json")
    assert prepared.tree == git(repo, "write-tree")
    assert prepared.changed_paths == ("package.json",)
    assert prepared.edits == (edit,)
    assert apply_edits(tree, entries, blobs, (edit,), {edit.path}) == prepared


@pytest.mark.parametrize("field", ["input_digest", "output_digest", "content"])
def test_tampered_edit_stops_before_git_or_filesystem_write(source, field, monkeypatch):
    _, tree, entries, blobs, edit = source
    value = b"tampered" if field == "content" else "0" * 64
    monkeypatch.setattr(
        "cg_release.preparation.TemporaryDirectory",
        lambda **kwargs: pytest.fail("invalid input reached staging"),
    )
    with pytest.raises(ControllerError):
        apply_edits(
            tree, entries, blobs, (replace(edit, **{field: value}),), {edit.path}
        )


@pytest.mark.parametrize("path", ["../escape", ".git/config", "PACKAGE.JSON", "a/b"])
def test_edit_allowlist_alias_and_parent_collision(source, path):
    _, tree, entries, blobs, edit = source
    with pytest.raises(ControllerError):
        apply_edits(tree, entries, blobs, (replace(edit, path=path),), {edit.path})


def test_source_tree_identity_and_input_blob_oid_are_verified(source):
    _, tree, entries, blobs, edit = source
    with pytest.raises(ControllerError):
        apply_edits("0" * 40, entries, blobs, (edit,), {edit.path})
    corrupt = [replace(e, oid="0" * 40) if e.path == edit.path else e for e in entries]
    with pytest.raises(ControllerError):
        apply_edits(tree, corrupt, blobs, (edit,), {edit.path})


def test_duplicate_edit_and_undeclared_partial_set_fail(source):
    _, tree, entries, blobs, edit = source
    for edits, allowed in [
        ((edit, edit), {edit.path}),
        ((edit,), {edit.path, "missing"}),
    ]:
        with pytest.raises(ControllerError):
            apply_edits(tree, entries, blobs, edits, allowed)


def test_symlink_parent_and_case_alias_fail(source):
    _, tree, entries, blobs, edit = source
    for extra in [
        TreeEntry("PACKAGE.JSON", "100644", "a" * 40),
        TreeEntry("package.json/nested", "100644", "a" * 40),
    ]:
        with pytest.raises(ControllerError):
            apply_edits(tree, entries + [extra], blobs, (edit,), {edit.path})
    link = [replace(e, mode="120000") if e.path == edit.path else e for e in entries]
    with pytest.raises(ControllerError):
        apply_edits(tree, link, blobs, (edit,), {edit.path})


def test_new_manifest_requires_absence_and_regular_outputs(source):
    _, tree, entries, blobs, edit = source
    content = b'{"request":"bound"}\n'
    manifest = Edit(
        ".release-manifest.json", None, hashlib.sha256(content).hexdigest(), content
    )
    result = apply_edits(
        tree, entries, blobs, (edit, manifest), {edit.path, manifest.path}
    )
    assert result.changed_paths == (".release-manifest.json", "package.json")
    with pytest.raises(ControllerError):
        apply_edits(
            tree, entries, blobs, (replace(edit, input_digest=None),), {edit.path}
        )


def test_hostile_git_environment_cannot_redirect_staging(source, tmp_path, monkeypatch):
    repo, tree, entries, blobs, edit = source
    original = git(repo, "write-tree")
    monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repo))
    monkeypatch.setenv("GIT_INDEX_FILE", str(repo / ".git" / "index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.worktree")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(tmp_path))
    assert apply_edits(tree, entries, blobs, (edit,), {edit.path}).tree != original
    assert (repo / "package.json").read_bytes() == blobs[edit.path].content


@pytest.mark.parametrize(
    "kind,raw",
    [
        ("json", b'{"version":"1.0.0","keep":true}\n'),
        ("python-project", b'# Keep\n[project]\nname="example"\nversion="1.0.0"\n'),
        (
            "r-description",
            b"Package: example\nVersion: 1.0.0\nDescription: Keep\n    text\n",
        ),
    ],
)
def test_all_pure_adapters_apply_without_format_or_unrelated_tree_changes(
    tmp_path, kind, raw
):
    from cg_release.preparation import object_id, tree_id

    blobs = {
        "nested/metadata": SourceBlob(raw),
        "notes": SourceBlob(b"<!-- release -->\n"),
    }
    entries = [
        TreeEntry(path, blob.mode, object_id("blob", blob.content))
        for path, blob in blobs.items()
    ]
    # Preserve unrelated symlink/submodule objects without checking them out.
    entries += [
        TreeEntry("unrelated-link", "120000", "a" * 40),
        TreeEntry("submodule", "160000", "b" * 40),
    ]
    edits = proposed_edits(
        [
            MetadataAdapter(
                kind=kind,
                path="nested/metadata",
                pointer="/version" if kind == "json" else None,
            )
        ],
        Changelog(path="notes", marker="<!-- release -->"),
        blobs,
        version="1.1.0",
        tag="v1.1.0",
        line="current",
        source_sha="c" * 40,
        policy_digest="d" * 64,
        request_id="preview",
        notes="Reviewed changes.",
        projections_history={"nested/metadata": []},
        outputs=["dist/output"],
    )
    staged = apply_edits(
        tree_id(entries), entries, blobs, edits, {e.path for e in edits}
    )
    expected = {e.path: e for e in entries}
    for edit in edits:
        expected[edit.path] = TreeEntry(
            edit.path, "100644", object_id("blob", edit.content)
        )
    assert staged.tree == tree_id(list(expected.values()))
    assert tuple(e.content for e in staged.edits) == tuple(e.content for e in edits)


def test_untrusted_attributes_are_not_materialized_or_executed(source):
    from cg_release.preparation import object_id, tree_id

    _, _, entries, blobs, edit = source
    attributes = b"* filter=untrusted diff=untrusted\n"
    entries += [TreeEntry(".gitattributes", "100644", object_id("blob", attributes))]
    calls = []
    from cg_release.process import run_process

    def observed(tool, args, **kwargs):
        calls.append(args)
        assert not (kwargs["cwd"] / ".gitattributes").exists()
        return run_process(tool, args, **kwargs)

    apply_edits(tree_id(entries), entries, blobs, (edit,), {edit.path}, runner=observed)
    assert not any(
        "checkout" in args or "add" in args or "commit" in args for args in calls
    )
    assert any("--no-filters" in args for args in calls)


def test_preparation_uses_one_shared_deadline(source):
    _, tree, entries, blobs, edit = source
    from cg_release.process import run_process

    now, calls = [0.0], []

    def observed(tool, args, **kwargs):
        calls.append(kwargs["timeout"])
        result = run_process(tool, args, **kwargs)
        now[0] += 2
        return result

    with pytest.raises(ControllerError) as caught:
        apply_edits(
            tree,
            entries,
            blobs,
            (edit,),
            {edit.path},
            runner=observed,
            clock=lambda: now[0],
            deadline=3,
        )
    assert caught.value.code == "E_DEADLINE"
    assert calls == [3, 1]
