"""Distinct trusted gate workflows share one authoritative artifact producer."""

from pathlib import Path
from types import SimpleNamespace

from cg_release.build_evidence import MATRIX_JOBS, reuse_key
from cg_release.build_stage import make_ticket
from cg_release.journal import digest
from cg_release.metadata import SourceBlob
from cg_release.models import Policy, Request, RequiredCheck, load_record


def test_separate_build_and_gate_workflows_have_distinct_registered_tuples(monkeypatch):
    fixtures = Path(__file__).parent / "fixtures"
    policy = load_record(Policy, (fixtures / "policy.json").read_bytes())
    policy = policy.model_copy(
        update={
            "enabled": True,
            "required_checks": [
                *policy.required_checks,
                RequiredCheck(
                    stage="release",
                    name="build",
                    app_id=42,
                    workflow_path=".github/workflows/release-controller-build.yml",
                ),
            ],
        }
    )
    request = load_record(Request, (fixtures / "request.json").read_bytes()).model_copy(
        update={"policy_digest": digest(policy)}
    )
    record = SimpleNamespace(
        request=request,
        publication_started=False,
        evidence={
            "review-binding": {"release_sha": "d" * 40, "release_tree": "e" * 40}
        },
    )
    context = SimpleNamespace(
        policy=policy,
        policy_sha="c" * 40,
        default="default",
        api=SimpleNamespace(
            branch=lambda branch: {
                "commit": {"sha": "c" * 40 if branch == "default" else "d" * 40}
            }
        ),
    )
    monkeypatch.setattr("cg_release.build_stage.authorize_record", lambda *a: None)
    monkeypatch.setattr("cg_release.build_stage.commit_tree", lambda *a: "e" * 40)
    monkeypatch.setattr(
        "cg_release.build_stage.read_blobs",
        lambda *a: {"uv.lock": SourceBlob(b"locked")},
    )
    build = make_ticket(
        context,
        record,
        nonce="1" * 32,
        workflow=".github/workflows/release-controller-build.yml",
    )
    gate = make_ticket(
        context,
        record,
        nonce="2" * 32,
        workflow=".github/workflows/release-controller-ci.yml",
    )
    assert build["produces_artifacts"] is True and build["required_jobs"] == ["build"]
    assert gate["produces_artifacts"] is False and set(gate["required_jobs"]) == set(
        MATRIX_JOBS
    )
    assert build["app_id"] == 42 and gate["app_id"] == 15368
    assert build["release_sha"] == gate["release_sha"]
    assert reuse_key(build) != reuse_key(gate)
