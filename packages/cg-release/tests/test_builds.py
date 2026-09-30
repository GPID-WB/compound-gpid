"""Release evidence must bind a registered source, controller, run, and exact jobs."""

import copy
import json
from pathlib import Path

import pytest

from cg_release.build_evidence import MATRIX_JOBS, reuse_key, verify_build
from cg_release.events import ControllerError


def inputs():
    sealed = {
        "repository_id": 123,
        "request_digest": "a" * 64,
        "dispatch_nonce": "b" * 32,
        "workflow_path": ".github/workflows/release-controller-ci.yml",
        "controller_sha": "c" * 40,
        "controller_ref": "main",
        "release_sha": "d" * 40,
        "release_tree": "e" * 40,
        "policy_digest": "f" * 64,
        "controller_digest": "1" * 64,
        "required_checks_digest": "2" * 64,
        "build_inputs_digest": "3" * 64,
        "lock_digests": {"uv.lock": "4" * 64},
        "toolchain": "six-cell-v1",
        "profile_version": None,
        "app_id": 42,
        "produces_artifacts": True,
        "required_jobs": list(MATRIX_JOBS),
        "build_spec": json.loads(
            (Path(__file__).parent / "fixtures/policy.json").read_text()
        )["build"],
    }
    registration = {
        "build_digest": reuse_key(sealed),
        "dispatch_nonce": sealed["dispatch_nonce"],
        "run_id": 21,
        "run_attempt": 1,
        "release_sha": sealed["release_sha"],
    }
    run = {
        "id": 21,
        "run_attempt": 1,
        "event": "workflow_dispatch",
        "head_sha": sealed["controller_sha"],
        "head_branch": "main",
        "path": sealed["workflow_path"],
        "repository": {"id": 123},
        "status": "completed",
        "conclusion": "success",
        "check_suite_id": 31,
    }
    jobs = [
        {
            "id": i + 1,
            "name": name,
            "run_id": 21,
            "run_attempt": 1,
            "status": "completed",
            "conclusion": "success",
            "runner_id": 1000 + i,
            "runner_name": "Hosted Agent",
            "labels": [
                name.removeprefix("package-").rsplit("-py", 1)[0]
                if name.startswith("package-")
                else "ubuntu-24.04"
            ],
        }
        for i, name in enumerate(MATRIX_JOBS)
    ]
    suite = {"id": 31, "head_sha": sealed["controller_sha"], "app": {"id": 42}}
    return sealed, registration, run, jobs, suite


def test_controller_head_legitimately_differs_from_registered_release():
    sealed, registration, run, jobs, suite = inputs()
    result = verify_build(sealed, registration, run, jobs, suite)
    assert result["release_sha"] != run["head_sha"]
    assert result["reuse_key"] == reuse_key(sealed)


@pytest.mark.parametrize(
    "case",
    [
        "pr",
        "source",
        "attempt",
        "nonce",
        "producer",
        "workflow",
        "skipped",
        "missing",
        "duplicate",
        "runner",
    ],
)
def test_forged_or_incomplete_build_evidence_is_rejected(case):
    sealed, registration, run, jobs, suite = inputs()
    if case == "pr":
        run["event"] = "pull_request"
    elif case == "source":
        registration["release_sha"] = "9" * 40
    elif case == "attempt":
        run["run_attempt"] = 2
    elif case == "nonce":
        registration["dispatch_nonce"] = "9" * 32
    elif case == "producer":
        suite["app"]["id"] = 99
    elif case == "workflow":
        run["path"] = ".github/workflows/forged.yml"
    elif case == "skipped":
        jobs[0]["conclusion"] = "skipped"
    elif case == "missing":
        jobs.pop()
    elif case == "runner":
        jobs[0]["labels"] = ["self-hosted"]
    else:
        jobs.append(copy.deepcopy(jobs[0]))
    with pytest.raises(ControllerError):
        verify_build(sealed, registration, run, jobs, suite)


@pytest.mark.parametrize(
    "field",
    [
        "release_sha",
        "release_tree",
        "policy_digest",
        "controller_digest",
        "required_checks_digest",
        "build_inputs_digest",
        "lock_digests",
        "toolchain",
        "profile_version",
    ],
)
def test_reuse_key_changes_for_every_exact_input_boundary(field):
    sealed, *_ = inputs()
    changed = copy.deepcopy(sealed)
    changed[field] = (
        {"uv.lock": "9" * 64}
        if field == "lock_digests"
        else "9" * 40
        if field in {"release_sha", "release_tree"}
        else "9" * 64
        if field.endswith("digest")
        else "changed"
    )
    assert reuse_key(changed) != reuse_key(sealed)
