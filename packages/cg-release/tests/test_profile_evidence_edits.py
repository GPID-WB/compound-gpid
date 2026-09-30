"""Safe pre-seal native attestation generation using actual immutable provider reads."""

import hashlib
import json

import pytest
from profile_git import GitData

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.preparation import TreeEntry, apply_edits

TARGETS = {
    "claude-code": ".claude",
    "codex": ".agents",
    "opencode": ".opencode",
    "kilo": ".kilo",
}


def fixture_files():
    """Return a synthetic all-target immutable metadata baseline."""
    mapping = {
        "schemaVersion": 1,
        "targets": [
            {
                "id": name,
                "generatedTreePath": root,
                "outputPaths": {"shared": root + "/shared"},
            }
            for name, root in TARGETS.items()
        ],
    }
    files = {".github/shared/target-mapping.json": json.dumps(mapping).encode()}
    for name, root in TARGETS.items():
        files[root + "/.compound-gpid-generated.json"] = (
            json.dumps(
                {"schemaVersion": 1, "target": name, "policyVersion": 1, "files": []},
                indent=2,
            )
            + "\n"
        ).encode()
    return files


def test_exact_canonical_native_manifest_edit_set_before_pr(tmp_path):
    from cg_release.profile_attestations import attestation_edits

    data = GitData()
    root = data.tree(fixture_files())
    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=data.transport)
    path = ".github/shared/skill-management/release-attestations/v1.0.0.json"
    raw = b'{"releaseTag":"v1.0.0"}\n'
    blobs, edits = attestation_edits(api, root, path, raw)
    assert len(edits) == 9
    expected = (
        {path}
        | {
            r + "/shared/skill-management/release-attestations/v1.0.0.json"
            for r in TARGETS.values()
        }
        | {r + "/.compound-gpid-generated.json" for r in TARGETS.values()}
    )
    assert {e.path for e in edits} == expected
    entries = [
        TreeEntry(r["path"], r["mode"], r["sha"]) for r in data.flat[root]["tree"]
    ]
    prepared = apply_edits(
        root,
        entries,
        blobs,
        edits,
        expected,
        create_paths={e.path for e in edits if e.input_digest is None},
    )
    assert set(prepared.changed_paths) == expected
    assert all(e.content == raw for e in edits if "/release-attestations/" in e.path)


def test_foreign_target_mapping_cannot_expand_privileged_edit_set(tmp_path):
    from cg_release.profile_attestations import attestation_edits

    files = fixture_files()
    mapping = json.loads(files[".github/shared/target-mapping.json"])
    mapping["targets"][0]["outputPaths"]["shared"] = ".github/workflows"
    files[".github/shared/target-mapping.json"] = json.dumps(mapping).encode()
    data = GitData()
    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=data.transport)
    with pytest.raises(ControllerError):
        attestation_edits(
            api,
            data.tree(files),
            ".github/shared/skill-management/release-attestations/v1.0.0.json",
            b"{}\n",
        )


def test_projection_preserves_historical_bytes_and_exact_manifest_format(tmp_path):
    from cg_release.profile_attestations import attestation_edits

    files = fixture_files()
    old = ".github/shared/skill-management/release-attestations/v0.9.0.json"
    files[old] = b'{"historical":true}\n'
    files["scripts/cg_generate_targets.py"] = (
        b"raise RuntimeError('must never execute source')\n"
    )
    entries = {}
    for name, root in TARGETS.items():
        target = root + old[len(".github") :]
        files[target] = files[old]
        entries[name] = {
            "path": target,
            "source": old,
            "kind": "shared",
            "sha256": hashlib.sha256(files[old]).hexdigest(),
            "executable": False,
        }
        files[root + "/.compound-gpid-generated.json"] = (
            json.dumps(
                {
                    "schemaVersion": 1,
                    "target": name,
                    "policyVersion": 1,
                    "files": [entries[name]],
                },
                indent=2,
            )
            + "\n"
        ).encode()
    data = GitData()
    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=data.transport)
    path, raw = old.replace("v0.9.0", "v1.0.0"), b'{"releaseTag":"v1.0.0"}\n'
    _, edits = attestation_edits(api, data.tree(files), path, raw)
    assert len(edits) == 9
    for name, root in TARGETS.items():
        expected = {
            "schemaVersion": 1,
            "target": name,
            "policyVersion": 1,
            "files": [
                entries[name],
                {
                    "path": root + path[len(".github") :],
                    "source": path,
                    "kind": "shared",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "executable": False,
                },
            ],
        }
        actual = next(
            e.content
            for e in edits
            if e.path == root + "/.compound-gpid-generated.json"
        )
        assert (
            actual
            == (json.dumps(expected, indent=2, ensure_ascii=False) + "\n").encode()
        )
    assert not any(e.path == old or e.path.startswith("scripts/") for e in edits)
