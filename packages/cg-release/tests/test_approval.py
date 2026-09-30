"""Approval must identify one exact run, environment, seal and independent human."""

from copy import deepcopy

import pytest

from cg_release.approval import verify_approval
from cg_release.events import ControllerError
from cg_release.journal import digest


@pytest.fixture
def approval_case():
    inputs = {"version": "1.5.0-rc.10", "release_sha": "a" * 40}
    seal = {
        "inputs": inputs,
        "digest": digest(inputs),
        "run_id": 41,
        "run_attempt": 1,
        "workflow_path": ".github/workflows/release-controller-publish.yml",
        "controller_sha": "b" * 40,
        "controller_ref": "main",
        "repository_id": 123,
        "environment_id": 17,
        "environment": "release-publish",
        "requester_id": 7,
        "reconfirmers": [8],
        "mode": "initial",
    }
    run = {
        "id": 41,
        "run_attempt": 1,
        "event": "workflow_dispatch",
        "path": seal["workflow_path"],
        "head_sha": "b" * 40,
        "head_branch": "main",
        "repository": {"id": 123},
        "status": "in_progress",
    }
    environment = {
        "id": 17,
        "name": "release-publish",
        "can_admins_bypass": False,
        "protection_rules": [
            {
                "type": "required_reviewers",
                "prevent_self_review": True,
                "reviewers": [{"type": "User", "reviewer": {"id": 9}}],
            }
        ],
    }
    reviews = [
        {
            "state": "approved",
            "user": {"id": 9},
            "environments": [{"id": 17, "name": "release-publish"}],
        }
    ]
    job = {
        "id": 51,
        "run_id": 41,
        "run_attempt": 1,
        "name": "publish",
        "status": "in_progress",
        "conclusion": None,
    }
    return seal, run, environment, reviews, job


def test_exact_independent_approval(approval_case):
    assert verify_approval(*approval_case, permitted_reviewers={9}) == [9]


@pytest.mark.parametrize(
    "change",
    [
        "rerun",
        "digest",
        "workflow",
        "source-as-controller",
        "wrong-environment",
        "bypass",
        "self-review-setting",
        "requester",
        "reconfirmer",
        "unknown-reviewer",
        "rejected",
        "no-review",
        "wrong-job",
        "wrong-job-run",
        "completed-job",
    ],
)
def test_approval_rejects_unbound_or_self_approved_input(approval_case, change):
    seal, run, env, reviews, job = deepcopy(approval_case)
    if change == "rerun":
        run["run_attempt"] = 2
    if change == "digest":
        seal["inputs"]["version"] = "1.5.0"
    if change == "workflow":
        run["path"] = ".github/workflows/hostile.yml"
    if change == "source-as-controller":
        run["head_sha"] = "a" * 40
    if change == "wrong-environment":
        reviews[0]["environments"][0]["id"] = 18
    if change == "bypass":
        env["can_admins_bypass"] = True
    if change == "self-review-setting":
        env["protection_rules"][0]["prevent_self_review"] = False
    if change == "requester":
        reviews[0]["user"]["id"] = 7
    if change == "reconfirmer":
        reviews[0]["user"]["id"] = 8
    if change == "unknown-reviewer":
        reviews[0]["user"]["id"] = 10
    if change == "rejected":
        reviews[0]["state"] = "rejected"
    if change == "no-review":
        reviews.clear()
    if change == "wrong-job":
        job["name"] = "build"
    if change == "wrong-job-run":
        job["run_id"] = 42
    if change == "completed-job":
        job["status"] = "completed"
    with pytest.raises(ControllerError, match="approval"):
        verify_approval(seal, run, env, reviews, job, permitted_reviewers={7, 8, 9})


@pytest.mark.parametrize("index", range(5))
def test_malformed_approval_boundary_is_typed(approval_case, index):
    args = list(approval_case)
    args[index] = None
    with pytest.raises(ControllerError):
        verify_approval(*args, permitted_reviewers={9})
