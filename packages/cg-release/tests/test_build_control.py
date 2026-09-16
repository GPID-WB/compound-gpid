"""Build requests register exactly one trusted run before accepting source evidence."""

from types import SimpleNamespace

import pytest
from journal_store import MemoryStore
from test_builds import inputs
from test_journal import release_request as _release_request

from cg_release.build_control import dispatch_build, register_build
from cg_release.events import ControllerError
from cg_release.journal import Journal, digest

release_request = _release_request


@pytest.mark.parametrize("unknown_dispatch", [False, True])
def test_registration_is_bound_and_duplicate_attempt_loses(
    release_request, unknown_dispatch
):
    sealed, _, run, _, _ = inputs()
    journal = Journal(MemoryStore())
    record = journal.admit(release_request)
    for op, state in [("prepare", "awaiting-review"), ("review", "building")]:
        journal.intent(record.request_id, op, digest({}))
        record = journal.result(record.request_id, op, digest({}), state)
    journal.intent(record.request_id, "build-request-1", digest(sealed))
    record = journal.result(
        record.request_id,
        "build-request-1",
        digest(sealed),
        "building",
        evidence=sealed,
    )
    run.update(status="in_progress", conclusion=None)
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "21",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": sealed["controller_sha"],
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_WORKFLOW_REF": "owner/repo/"
        + sealed["workflow_path"]
        + "@refs/heads/main",
    }
    context = SimpleNamespace(
        journal=journal,
        api=SimpleNamespace(slug="owner/repo", get=lambda ep: run),
        policy_sha=sealed["controller_sha"],
    )
    if unknown_dispatch:
        payload = {
            "ref": sealed["controller_ref"],
            "inputs": {
                "build_request": record.request_id,
                "dispatch_nonce": sealed["dispatch_nonce"],
            },
        }
        journal.intent(record.request_id, "build-dispatch-1", digest(payload))
    result = register_build(context, record.request_id, sealed["dispatch_nonce"], env)
    assert result["run_id"] == 21
    with pytest.raises(ControllerError):
        register_build(context, record.request_id, sealed["dispatch_nonce"], env)


@pytest.mark.parametrize(
    "field,value",
    [
        ("GITHUB_SHA", "0" * 40),
        ("GITHUB_REF", "refs/heads/feature"),
        ("GITHUB_RUN_ATTEMPT", "2"),
    ],
)
def test_invalid_registration_cannot_write(release_request, field, value):
    sealed, _, run, _, _ = inputs()
    record = SimpleNamespace(state="building", evidence={"build-request-1": sealed})
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "21",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": sealed["controller_sha"],
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_WORKFLOW_REF": "owner/repo/"
        + sealed["workflow_path"]
        + "@refs/heads/main",
    }
    env[field] = value
    journal = SimpleNamespace(
        get=lambda rid: record, intent=lambda *a: pytest.fail("untrusted write")
    )
    context = SimpleNamespace(
        journal=journal,
        api=SimpleNamespace(slug="owner/repo", get=lambda ep: run),
        policy_sha=sealed["controller_sha"],
    )
    with pytest.raises(ControllerError):
        register_build(context, "request", sealed["dispatch_nonce"], env)


def test_unknown_dispatch_is_never_replayed(release_request):
    sealed, *_ = inputs()
    journal = Journal(MemoryStore())
    record = journal.admit(release_request)
    for operation, state in [("prepare", "awaiting-review"), ("review", "building")]:
        journal.intent(record.request_id, operation, digest({}))
        record = journal.result(record.request_id, operation, digest({}), state)
    journal.intent(record.request_id, "build-request-1", digest(sealed))
    record = journal.result(
        record.request_id,
        "build-request-1",
        digest(sealed),
        "building",
        evidence=sealed,
    )
    writes = []

    def lost(*args, **kwargs):
        writes.append(1)
        raise ControllerError("E_TIMEOUT", "Unknown remote acceptance.")

    api = SimpleNamespace(
        host="github.com",
        slug="owner/repo",
        runner=lost,
        cwd=None,
        read_seconds=20,
        remaining=lambda: 10,
    )
    context = SimpleNamespace(journal=journal, api=api)
    for _ in range(2):
        with pytest.raises(ControllerError) as caught:
            dispatch_build(context, journal.get(record.request_id))
        assert caught.value.code == "E_DISPATCH_UNKNOWN"
    assert writes == [1]
