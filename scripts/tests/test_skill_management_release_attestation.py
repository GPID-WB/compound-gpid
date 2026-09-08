"""Immutable plugin release and project revision grace tests."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import cg_release_attestation
from skill_management.services import release_attestation


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(root: Path, message: str) -> str:
    _git(root, "add", ".")
    _git(
        root,
        "-c",
        "user.name=Phase Six",
        "-c",
        "user.email=phase6@example.test",
        "commit",
        "-m",
        message,
    )
    return _git(root, "rev-parse", "HEAD")


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8", newline="\n")
    else:
        path.write_text(
            json.dumps(value, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )


def _tag(root: Path, remote: Path, tag: str, message: str) -> tuple[str, str, str]:
    _git(
        root,
        "-c",
        "user.name=Phase Six",
        "-c",
        "user.email=phase6@example.test",
        "tag",
        "-a",
        tag,
        "-m",
        message,
    )
    _git(root, "push", str(remote), tag)
    return (
        _git(root, "rev-parse", f"refs/tags/{tag}"),
        _git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}"),
        hashlib.sha256((root / f"releases/{tag}.json").read_bytes()).hexdigest(),
    )


def _plugin_grace_repo(tmp_path: Path) -> tuple[Path, Path, str]:
    root = tmp_path / "work"
    remote = tmp_path / "remote.git"
    root.mkdir()
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    _git(root, "init")
    _git(root, "remote", "add", "origin", str(remote))
    digest = "d" * 64
    provenance = {
        "schema": "cg-skill-provenance-v1",
        "schemaVersion": 1,
        "skillId": "demo-skill",
        "origin": "plugin-canonical",
        "admission": "approved",
        "lifecycle": "deprecated",
        "source": {
            "repository": "https://github.com/example/skills",
            "path": "skills/demo-skill",
            "commit": "a" * 40,
            "bundleDigest": "b" * 64,
        },
        "history": [],
        "migrations": [],
        "successorId": "next-skill",
        "deprecatedRecordDigest": digest,
    }
    _write(
        root / ".github/shared/skill-management/provenance/demo-skill.json",
        provenance,
    )
    _write(root / ".github/skills/demo-skill/SKILL.md", "# demo\n")
    _write(root / "releases/v1.0.0.json", {"tag": "v1.0.0"})
    _commit(root, "anchor release")
    first = _tag(root, remote, "v1.0.0", "anchor")
    _write(root / "releases/v1.1.0.json", {"tag": "v1.1.0"})
    _write(root / "later.txt", "later\n")
    _commit(root, "later release")
    second = _tag(root, remote, "v1.1.0", "later")
    for tag, evidence in (("v1.0.0", first), ("v1.1.0", second)):
        _write(
            root
            / ".github/shared/skill-management/release-attestations"
            / f"{tag}.json",
            {
                "schema": "cg-skill-release-attestation-v1",
                "schemaVersion": 1,
                "releaseTag": tag,
                "tagRefObjectSha": evidence[0],
                "peeledCommitSha": evidence[1],
                "releasePayloadSha256": evidence[2],
                "deprecationRecordDigests": {"demo-skill": digest},
                "reviewReference": "review=" + "f" * 40,
            },
        )
    return root, remote, digest


def test_plugin_grace_requires_two_pinned_annotated_descendant_releases(
    tmp_path: Path,
) -> None:
    root, _remote, digest = _plugin_grace_repo(tmp_path)

    evidence = release_attestation.verify_plugin_grace(
        root,
        "demo-skill",
        digest,
        ".github/shared/skill-management/provenance/demo-skill.json",
        ".github/skills/demo-skill",
    )

    assert evidence.anchor_release == "v1.0.0"
    assert evidence.descendant_release == "v1.1.0"
    assert evidence.removed_revision == _git(
        root, "rev-parse", "v1.1.0^{commit}"
    )


def test_moved_remote_tag_blocks_plugin_grace(tmp_path: Path) -> None:
    root, remote, digest = _plugin_grace_repo(tmp_path)
    _write(root / "moved.txt", "moved\n")
    _commit(root, "move tag")
    _git(root, "tag", "-d", "v1.1.0")
    _git(
        root,
        "-c",
        "user.name=Phase Six",
        "-c",
        "user.email=phase6@example.test",
        "tag",
        "-a",
        "v1.1.0",
        "-m",
        "moved",
    )
    _git(root, "push", "--force", str(remote), "v1.1.0")

    with pytest.raises(release_attestation.ReleaseAttestationError, match="tag|Tag"):
        release_attestation.verify_plugin_grace(
            root,
            "demo-skill",
            digest,
            ".github/shared/skill-management/provenance/demo-skill.json",
            ".github/skills/demo-skill",
        )


def test_post_release_attestation_binds_tag_payload_and_deprecation(
    tmp_path: Path,
) -> None:
    root, _remote, digest = _plugin_grace_repo(tmp_path)

    value = release_attestation.build_release_attestation(
        root, "v1.1.0", "review=" + "f" * 40
    )

    assert value["releaseTag"] == "v1.1.0"
    assert value["tagRefObjectSha"] == _git(root, "rev-parse", "refs/tags/v1.1.0")
    assert value["peeledCommitSha"] == _git(root, "rev-parse", "v1.1.0^{commit}")
    assert value["deprecationRecordDigests"] == {"demo-skill": digest}
    assert value["releasePayloadSha256"] == hashlib.sha256(
        (root / "releases/v1.1.0.json").read_bytes()
    ).hexdigest()


def test_post_release_attestation_write_is_deterministic_and_idempotent(
    tmp_path: Path,
) -> None:
    root, _remote, _digest = _plugin_grace_repo(tmp_path)
    review = "review=" + "f" * 40
    (
        root
        / ".github/shared/skill-management/release-attestations/v1.1.0.json"
    ).unlink()

    first = release_attestation.write_release_attestation(root, "v1.1.0", review)
    first_bytes = first.read_bytes()
    second = release_attestation.write_release_attestation(root, "v1.1.0", review)

    assert second == first
    assert second.read_bytes() == first_bytes
    assert json.loads(first_bytes)["schema"] == "cg-skill-release-attestation-v1"


def test_post_release_cli_writes_reviewed_attestation(tmp_path: Path) -> None:
    root, _remote, _digest = _plugin_grace_repo(tmp_path)
    (
        root
        / ".github/shared/skill-management/release-attestations/v1.1.0.json"
    ).unlink()

    exit_code = cg_release_attestation.main(
        [
            "--root",
            str(root),
            "--tag",
            "v1.1.0",
            "--review-reference",
            "review=" + "f" * 40,
        ]
    )

    assert exit_code == 0
    assert (
        root
        / ".github/shared/skill-management/release-attestations/v1.1.0.json"
    ).is_file()


def test_release_version_order_accepts_four_component_prereleases() -> None:
    assert release_attestation._version_key("v1.2.3.9001") > release_attestation._version_key(  # pylint: disable=protected-access
        "v1.2.3.9000"  # pylint: disable=protected-access
    )
    assert release_attestation._version_key("v1.2.3") > release_attestation._version_key(  # pylint: disable=protected-access
        "v1.2.3.9001"  # pylint: disable=protected-access
    )


def test_project_grace_uses_earliest_containing_commit_and_later_descendant(
    tmp_path: Path,
) -> None:
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init")
    digest = "d" * 64
    record = {"deprecatedRecordDigest": digest, "lifecycle": "deprecated"}
    _write(root / ".compound-gpid/skill-provenance/demo-skill.json", record)
    _write(root / ".compound-gpid/skills/demo-skill/SKILL.md", "# demo\n")
    anchor = _commit(root, "deprecate")
    _write(root / "later.txt", "later\n")
    later = _commit(root, "later reviewed revision")

    evidence = release_attestation.verify_project_grace(
        root,
        "demo-skill",
        digest,
        ".compound-gpid/skill-provenance/demo-skill.json",
        ".compound-gpid/skills/demo-skill",
    )

    assert evidence.anchor_revision == anchor
    assert evidence.removed_revision == later


def test_project_grace_blocks_same_revision(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init")
    digest = "d" * 64
    _write(
        root / ".compound-gpid/skill-provenance/demo-skill.json",
        {"deprecatedRecordDigest": digest, "lifecycle": "deprecated"},
    )
    _write(root / ".compound-gpid/skills/demo-skill/SKILL.md", "# demo\n")
    _commit(root, "deprecate")

    with pytest.raises(release_attestation.ReleaseAttestationError, match="later"):
        release_attestation.verify_project_grace(
            root,
            "demo-skill",
            digest,
            ".compound-gpid/skill-provenance/demo-skill.json",
            ".compound-gpid/skills/demo-skill",
        )
