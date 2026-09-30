"""Trusted controller admission cannot execute arbitrary source or later phases."""

import pytest
from journal_store import MemoryStore
from test_authority import Controls
from test_lifecycle import receipt_fixture

from cg_release.controller import reconcile, verify_run, work_inventory
from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.runtime import Context


def test_workflow_identity_is_bound_to_default_sha_actor_and_attempt():
    api = Controls()
    policy = api.policy
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "10",
        "GITHUB_ACTOR_ID": "456",
        "GITHUB_SHA": "a" * 40,
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": "example/generic/.github/workflows/"
        "release-controller.yml@refs/heads/main",
        "CG_RELEASE_CONTROLLER_REVISION": policy.controller.revision,
        "CG_RELEASE_WHEEL_SHA256": policy.controller.wheel_digest,
    }
    original = api.get

    def get(endpoint):
        if endpoint == "actions/runs/10":
            return {
                "id": 10,
                "run_attempt": 1,
                "head_sha": "a" * 40,
                "head_branch": "main",
                "path": ".github/workflows/release-controller.yml",
                "event": "workflow_dispatch",
                "repository": {"id": 123},
                "actor": {"id": 456},
                "status": "in_progress",
            }
        return original(endpoint)

    api.get = get
    context = Context(api, policy, "a" * 40, "main", Journal(MemoryStore()))
    assert verify_run(context, env) == (456, "workflow_dispatch")
    for key, invalid in [
        ("GITHUB_SHA", "b" * 40),
        ("GITHUB_RUN_ATTEMPT", "2"),
        ("CG_RELEASE_WHEEL_SHA256", "f" * 64),
        ("GITHUB_REF", "refs/heads/feature"),
    ]:
        with pytest.raises(ControllerError):
            verify_run(context, {**env, key: invalid})


def test_disabled_policy_keeps_sealed_request_at_admission(monkeypatch):
    api = Controls()
    receipt = receipt_fixture()
    journal = Journal(MemoryStore())
    journal.admit(receipt.request)
    context = Context(api, api.policy, receipt.request.policy_sha, "main", journal)
    monkeypatch.setattr("cg_release.controller.actor_role", lambda *args: "maintain")
    event = reconcile(context, receipt.request_id)
    assert event.observed == "queued" and len(journal.events()) == 1
    assert event.next_action == "Policy is disabled; reviewed setup is required."


def test_sealed_request_remains_in_work_inventory_after_issue_deletion():
    receipt = receipt_fixture()
    journal = Journal(MemoryStore())
    journal.admit(receipt.request, receipt=receipt)
    inventory = work_inventory(journal, [])
    assert inventory == [{"number": 1, "sealed_request_id": receipt.request_id}]
