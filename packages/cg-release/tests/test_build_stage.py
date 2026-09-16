"""Build coordinator waits for registration and collects trusted remote evidence."""

import hashlib
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

from journal_store import MemoryStore
from test_builds import inputs

from cg_release.build_evidence import reuse_key
from cg_release.build_stage import build_step
from cg_release.journal import Journal, digest
from cg_release.models import Policy, Request, load_record


def test_registered_build_advances_once_with_verified_inventory(monkeypatch, tmp_path):
    sealed, registration, run, jobs, suite = inputs()
    policy = load_record(
        Policy, (Path(__file__).parent / "fixtures/policy.json").read_bytes()
    ).model_copy(update={"enabled": True})
    journal = Journal(MemoryStore())
    request = load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    ).model_copy(
        update={"policy_digest": digest(policy), "repository_slug": "owner/repo"}
    )
    sealed.update(policy_digest=digest(policy), request_digest=request.proposal_digest)
    registration["build_digest"] = reuse_key(sealed)
    record = journal.admit(request)
    for op, state, evidence in [
        ("prepare", "awaiting-review", {}),
        (
            "review-binding",
            "building",
            {
                "release_sha": sealed["release_sha"],
                "release_tree": sealed["release_tree"],
            },
        ),
        ("build-request-1", "building", sealed),
        ("build-registration-1", "building", registration),
    ]:
        journal.intent(record.request_id, op, digest(evidence))
        record = journal.result(
            record.request_id, op, digest(evidence), state, evidence=evidence
        )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("dist/package.whl", b"wheel")
    raw = output.getvalue()
    artifact = {
        "id": 51,
        "name": "release-assets",
        "expired": False,
        "size_in_bytes": len(raw),
        "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "workflow_run": {"id": run["id"], "head_sha": run["head_sha"]},
    }

    def observed(endpoint):
        if endpoint == "":
            return {"id": policy.repository_id, "default_branch": "main"}
        if endpoint == "branches/main":
            return {"protected": True, "commit": {"sha": sealed["controller_sha"]}}
        if endpoint == "collaborators/fixture/permission":
            return {
                "role_name": "write",
                "permission": "write",
                "user": {"id": request.requester_id},
            }
        if endpoint.startswith("check-suites/"):
            return suite
        assert endpoint in {"actions/runs/21", "actions/runs/21/attempts/1"}
        return run

    api = SimpleNamespace(
        slug="owner/repo",
        get=observed,
        branch=lambda name: observed("branches/" + name),
        _request=lambda resource, page: (
            {"id": request.requester_id, "login": "fixture"}
            if resource == f"user/{request.requester_id}"
            else {"total_count": len(jobs), "jobs": jobs}
            if resource.endswith("/jobs")
            else {"total_count": 1, "artifacts": [artifact]}
        ),
    )
    context = SimpleNamespace(
        api=api,
        journal=journal,
        policy=policy,
        default="main",
        policy_sha=sealed["controller_sha"],
    )
    monkeypatch.setattr(
        "cg_release.build_stage.make_ticket",
        lambda *a, **k: {**sealed, "dispatch_nonce": k["nonce"]},
    )
    monkeypatch.setattr("cg_release.build_stage.download_archive", lambda *a: raw)
    result = build_step(context, record)
    assert result.state == "awaiting-approval"
    assert (
        result.evidence["build-evidence-1"]["inventory"]["files"][0]["sha256"]
        == hashlib.sha256(b"wheel").hexdigest()
    )
    before = len(journal.events())
    assert build_step(context, result) == result
    assert len(journal.events()) == before
    artifact["expired"] = True
    replacement = build_step(context, result)
    assert replacement.state == "building"
    assert (
        replacement.evidence["build-request-2"]["dispatch_nonce"]
        != sealed["dispatch_nonce"]
    )
    assert "build-validated-1" in replacement.evidence
