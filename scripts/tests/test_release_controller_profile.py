"""Offline GPID profile preparation, policy and post-publication contracts."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/cg-release/src"))
sys.path.insert(0, str(ROOT / "scripts"))


def profile():
    import release_profile_gpid

    return release_profile_gpid


def test_payload_is_prepared_before_review_and_does_not_contain_tag_object():
    from cg_release.metadata import SourceBlob

    p = profile()
    blobs = {name: SourceBlob(b"{}") for name in p.REQUIRED_FILES}
    blobs["releases/latest.json"] = SourceBlob(
        (ROOT / "releases/latest.json").read_bytes()
    )
    snapshot = SimpleNamespace(
        blobs=blobs,
        notes="Reviewed commit inventory.",
        host="github.com",
        slug="owner/repo",
    )
    edits = p.prepare(
        snapshot,
        tag="v1.5.0-rc.10",
        version="1.5.0-rc.10",
        created_at="2026-09-12T08:00:00Z",
    )
    assert {edit.path for edit in edits} == {
        "releases/latest.json",
        "releases/v1.5.0-rc.10.json",
    }
    assert edits[0].content == edits[1].content
    payload = json.loads(edits[0].content)
    assert payload["tag"] == "v1.5.0-rc.10"
    assert payload["publishedAt"] == "2026-09-12T08:00:00Z"
    assert "tagRefObjectSha" not in payload
    assert payload["sections"][0]["entries"] == ["Reviewed commit inventory."]


def test_profile_missing_files_and_existing_payload_fail_closed():
    from cg_release.events import ControllerError
    from cg_release.metadata import SourceBlob

    p = profile()
    s = SimpleNamespace(blobs={}, notes="notes", host="github.com", slug="owner/repo")
    with pytest.raises(ControllerError):
        p.prepare(s, tag="v1.0.0", version="1.0.0", created_at="2026-09-12T08:00:00Z")
    s.blobs = {name: SourceBlob(b"{}") for name in p.REQUIRED_FILES}
    s.blobs["releases/v1.0.0.json"] = SourceBlob(b"immutable")
    with pytest.raises(ControllerError):
        p.prepare(s, tag="v1.0.0", version="1.0.0", created_at="2026-09-12T08:00:00Z")


def test_disabled_installation_has_no_resolved_authority():
    data = json.loads((ROOT / ".release-controller.json").read_text())
    assert data["enabled"] is False
    assert data["repository_id"] is None and data["controller"]["revision"] is None
    assert data["gpid_profile"] == "v1" and data["profile"]["bridge"] is None
    for name in [
        "release-controller",
        "release-controller-build",
        "release-controller-publish",
        "release-controller-docs",
    ]:
        content = (ROOT / f".github/workflows/{name}.yml").read_text()
        assert "false &&" in content


def test_enablement_requires_bridge_and_native_source_bound_checks():
    from cg_release.events import ControllerError
    from cg_release.models import Policy, canonical_bytes, load_record
    from cg_release.policy import validate_policy

    data = json.loads(
        (ROOT / "packages/cg-release/tests/fixtures/policy.json").read_text()
    )
    data["gpid_profile"] = "v1"
    data["enabled"] = True
    p = load_record(Policy, canonical_bytes(data))
    with pytest.raises(ControllerError, match="[Bb]ridge|profile"):
        validate_policy(p, repository_id=123, host="github.com")


def test_attestation_is_tag_bound_and_only_after_publication():
    from cg_release.events import ControllerError

    p = profile()
    with pytest.raises(ControllerError):
        p.attestation(SimpleNamespace(state="building", published=False), b"{}", {})
    record = SimpleNamespace(
        state="published",
        published=True,
        request=SimpleNamespace(tag="v1.0.0"),
        evidence={
            "publication-receipt": {"release_sha": "a" * 40, "tag_oid": "b" * 40},
            "review-binding": {"pr_number": 12},
        },
    )
    payload = b'{"tag":"v1.0.0"}'
    value = p.attestation(record, payload, {"skill": "c" * 64})
    assert value["peeledCommitSha"] == "a" * 40
    assert value["tagRefObjectSha"] == "b" * 40
    assert value["releasePayloadSha256"] == hashlib.sha256(payload).hexdigest()


def test_completion_never_accepts_source_verified_boolean():
    from cg_release.events import ControllerError

    p = profile()
    context = SimpleNamespace(
        api=SimpleNamespace(get=lambda endpoint: {"verified": True})
    )
    record = SimpleNamespace(
        state="published",
        published=True,
        evidence={
            "profile-docs": {"verified": True},
            "profile-evidence": {"verified": True},
        },
    )
    with pytest.raises(ControllerError):
        p.complete(context, record)


def test_snapshot_verifier_rejects_wrong_run_and_changed_bytes():
    import base64

    from cg_release.events import ControllerError

    p = profile()
    files = {
        name: name.encode()
        for name in (
            "index.html",
            "navigation.json",
            "assets/site.css",
            "assets/site.js",
            ".nojekyll",
        )
    }
    record = {
        "schemaVersion": 2,
        "kind": "release",
        "tag": "v1.0.0",
        "sha": "a" * 40,
        "runId": 12,
        "runAttempt": 1,
        "files": {
            name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(files.items())
        },
    }
    record["snapshotDigest"] = hashlib.sha256(
        json.dumps(record, separators=(",", ":")).encode()
    ).hexdigest()
    envelope = {
        "record": record,
        "files": {name: base64.b64encode(raw).decode() for name, raw in files.items()},
    }
    p.verify_snapshot(
        json.dumps(envelope).encode(),
        tag="v1.0.0",
        sha="a" * 40,
        run_id=12,
        run_attempt=1,
    )
    with pytest.raises(ControllerError):
        p.verify_snapshot(
            json.dumps(envelope).encode(),
            tag="v1.0.0",
            sha="a" * 40,
            run_id=13,
            run_attempt=1,
        )
    envelope["files"]["index.html"] = base64.b64encode(b"changed").decode()
    with pytest.raises(ControllerError):
        p.verify_snapshot(
            json.dumps(envelope).encode(),
            tag="v1.0.0",
            sha="a" * 40,
            run_id=12,
            run_attempt=1,
        )
