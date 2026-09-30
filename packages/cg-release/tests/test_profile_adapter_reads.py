"""Real reader, snapshot and strict policy boundaries; no remote operations."""

import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.models import ProfilePolicy
from cg_release.profile_snapshot import verify_snapshot

ROOT = Path(__file__).resolve().parents[3]
CORPUS = json.loads((ROOT / "scripts/tests/fixtures/snapshot-paths.json").read_text())
REQUIRED = [
    "index.html",
    "navigation.json",
    "assets/site.css",
    "assets/site.js",
    ".nojekyll",
]


def envelope(paths=(), size=1):
    """Return exact schema-v2 bytes, e.g. envelope(['extra.txt'])."""
    files = dict.fromkeys([*REQUIRED, *paths], b"x" * size)
    record = dict(
        schemaVersion=2,
        kind="release",
        tag="v1.0.0",
        sha="a" * 40,
        runId=12,
        runAttempt=1,
        files={p: hashlib.sha256(b).hexdigest() for p, b in sorted(files.items())},
    )
    record["snapshotDigest"] = hashlib.sha256(
        json.dumps(record, separators=(",", ":")).encode()
    ).hexdigest()
    return json.dumps(
        dict(
            record=record,
            files={p: base64.b64encode(b).decode() for p, b in files.items()},
        )
    ).encode()


def verify(raw):
    """Call the real approval verifier with exact synthetic identities."""
    return verify_snapshot(raw, tag="v1.0.0", sha="a" * 40, run_id=12, run_attempt=1)


@pytest.mark.parametrize("case", CORPUS)
def test_shared_path_corpus(case):
    raw = envelope(case["paths"])
    if case["valid"]:
        assert verify(raw)["tag"] == "v1.0.0"
    else:
        with pytest.raises(ControllerError):
            verify(raw)


def test_snapshot_decoder_exceeds_generic_api_limit_without_relaxing_it():
    from cg_release.jsonio import decode_json

    raw = envelope(size=700000)
    assert len(raw) > 4 * 1024 * 1024
    assert verify(raw)["runId"] == 12
    with pytest.raises(ControllerError):
        decode_json(raw.decode())


def test_canonical_snapshot_ignores_object_order_but_rejects_ambiguous_json():
    value = json.loads(envelope())
    value["record"] = dict(reversed(list(value["record"].items())))
    value["record"]["files"] = dict(reversed(list(value["record"]["files"].items())))
    assert verify(json.dumps(value).encode())["tag"] == "v1.0.0"
    for raw in [
        b"\xef\xbb\xbf" + envelope(),
        envelope().replace(
            b'"schemaVersion": 2', b'"schemaVersion": 2, "schemaVersion": 2'
        ),
    ]:
        with pytest.raises(ControllerError):
            verify(raw)


def test_production_dedicated_tree_and_pages_reads(tmp_path):
    seen = []

    def transport(tool, argv, **kwargs):
        assert tool == "gh" and argv[:3] == ["api", "--method", "GET"]
        seen.append(argv[-1])
        value = (
            {"sha": "a" * 40, "truncated": False, "tree": []}
            if "git/trees" in argv[-1]
            else []
        )
        return SimpleNamespace(
            returncode=0, stdout="HTTP/2.0 200 OK\n\n" + json.dumps(value)
        )

    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=transport)
    assert api.tree("a" * 40, recursive=True)["tree"] == []
    assert api.pages("releases") == []
    assert api.deployments("github-pages") == []
    assert seen == [
        "repos/owner/repo/git/trees/" + "a" * 40 + "?recursive=1",
        "repos/owner/repo/releases?per_page=100&page=1",
        "repos/owner/repo/deployments?environment=github-pages&per_page=100&page=1",
    ]
    with pytest.raises(ControllerError):
        api.deployments("github-pages&sha=evil")


def test_composition_retry_policy_is_strict_and_bounded():
    raw = dict(
        bridge=None,
        payload_directory="releases",
        latest_payload="releases/latest.json",
        attestation_directory=".github/shared/skill-management/release-attestations",
        docs_workflow=".github/workflows/release-controller-docs.yml",
    )
    assert ProfilePolicy(**raw).composition_retries == 3
    for value in [True, "3", -1, 11]:
        with pytest.raises(ValueError):
            ProfilePolicy(**raw, composition_retries=value)


def test_dispatch_discovery_uses_bounded_recent_inventory_not_lifetime_cap(tmp_path):
    seen = []

    def transport(tool, argv, **kwargs):
        seen.append(argv[-1])
        return SimpleNamespace(
            returncode=0,
            stdout='HTTP/2.0 200 OK\n\n{"total_count":0,"workflow_runs":[]}',
        )

    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=transport)
    workflow = ".github/workflows/release-controller-docs.yml"
    assert api.composition_runs(workflow, since=1000) == []
    assert seen[0].endswith(
        "?event=workflow_dispatch&created=%3E%3D1970-01-01T00%3A11%3A40Z&per_page=100&page=1"
    )
    for invalid in [True, -1, float("nan"), float("inf"), "1000"]:
        with pytest.raises(ControllerError):
            api.composition_runs(workflow, since=invalid)
    assert len(seen) == 1
