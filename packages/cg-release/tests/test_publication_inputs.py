"""Publication input acquisition rechecks registered builds and source lineage."""

import hashlib
import io
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_builds import inputs as build_fixture

from cg_release.build_evidence import reuse_key, verify_build
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.models import Policy, load_record
from cg_release.publication_inputs import verify_release_gates


def test_gate_acquisition_rejects_missing_final_evidence(publication):
    journal, record, *_ = publication
    context = SimpleNamespace(journal=journal, api=SimpleNamespace(), policy=None)
    with pytest.raises(ControllerError):
        verify_release_gates(context, record)


@pytest.fixture
def ready_build(publication, tmp_path):
    sealed, registration, run, jobs, suite = build_fixture()
    policy = load_record(
        Policy, (Path(__file__).parent / "fixtures/policy.json").read_bytes()
    )
    policy = policy.model_copy(update={"enabled": True})
    request = publication[1].request.model_copy(
        update={"policy_digest": digest(policy)}
    )
    sealed.update(
        policy_digest=digest(policy),
        controller_digest=digest(policy.controller),
        request_digest=request.proposal_digest,
        build_inputs_digest=digest(policy.build),
        required_checks_digest=digest(
            {"checks": [c.model_dump(mode="json") for c in policy.required_checks]}
        ),
    )
    registration["build_digest"] = reuse_key(sealed)
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("dist/package.whl", b"wheel bytes")
    raw = data.getvalue()
    metadata = {
        "id": 51,
        "name": "release-assets",
        "expired": False,
        "size_in_bytes": len(raw),
        "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "workflow_run": {"id": 21, "head_sha": sealed["controller_sha"]},
    }
    inventory = {
        "artifact_id": 51,
        "run_id": 21,
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "files": [
            {
                "name": "package.whl",
                "path": "dist/package.whl",
                "media_type": "application/zip",
                "size": 11,
                "sha256": hashlib.sha256(b"wheel bytes").hexdigest(),
            }
        ],
    }
    evidence = {
        "review-binding": {
            "release_sha": sealed["release_sha"],
            "release_tree": sealed["release_tree"],
        },
        "build-request-1": sealed,
        "build-registration-1": registration,
        "build-evidence-1": {
            **verify_build(sealed, registration, run, jobs, suite),
            "inventory": inventory,
        },
        "build-validated-1": {
            "gates": {
                sealed["workflow_path"]: {
                    "request": 1,
                    "reuse_key": reuse_key(sealed),
                    "run_id": 21,
                    "run_attempt": 1,
                }
            },
            "inventory": inventory,
        },
    }

    def get(endpoint, **kwargs):
        return {
            "actions/runs/21": run,
            "actions/runs/21/attempts/1": run,
            "check-suites/31": suite,
            "actions/runs/21/attempts/1/jobs": {"total_count": len(jobs), "jobs": jobs},
            "actions/runs/21/artifacts": {"total_count": 1, "artifacts": [metadata]},
        }[endpoint]

    api = SimpleNamespace(
        get=get,
        host="github.com",
        slug="owner/repo",
        cwd=tmp_path,
        _request=lambda resource, page: get(resource.removeprefix("repos/owner/repo/")),
        read_seconds=20,
        remaining=lambda: 120,
        runner=lambda *a, **k: subprocess.CompletedProcess(a, 0, raw, b""),
    )
    record = publication[1].model_copy(
        update={"request": request, "evidence": evidence}
    )
    return SimpleNamespace(api=api, policy=policy), record, metadata, jobs


def test_registered_gate_and_verified_bytes(ready_build):
    context, record, _, _ = ready_build
    final, data = verify_release_gates(context, record)
    assert data == {"package.whl": b"wheel bytes"}
    assert final == record.evidence["build-validated-1"]


@pytest.mark.parametrize(
    "change",
    ["expired", "skipped", "changed-policy", "missing-gate", "wrong-archive-run"],
)
def test_stale_gate_cannot_supply_publication_bytes(ready_build, change):
    context, record, metadata, jobs = ready_build
    if change == "expired":
        metadata["expired"] = True
    if change == "skipped":
        jobs[0]["conclusion"] = "skipped"
    if change == "changed-policy":
        context.policy = context.policy.model_copy(update={"signing_required": True})
    if change == "missing-gate":
        record.evidence["build-validated-1"]["gates"].clear()
    if change == "wrong-archive-run":
        metadata["workflow_run"]["id"] = 22
    with pytest.raises(ControllerError):
        verify_release_gates(context, record)
