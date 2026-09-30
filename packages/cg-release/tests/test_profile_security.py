"""Production worker boundaries with a real journal and GET transport fixtures."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from journal_store import MemoryStore
from test_publisher import invoke

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.journal import Journal, digest
from cg_release.models import Policy, load_record
from cg_release.prepare_stage import checkpoint
from cg_release.profile_worker import compose, register


@pytest.fixture
def worker(publication, tmp_path, monkeypatch):
    policy = load_record(
        Policy, (Path(__file__).parent / "fixtures/policy.json").read_bytes()
    )
    policy = policy.model_copy(update={"enabled": True})
    request = publication[1].request.model_copy(
        update={"policy_digest": digest(policy)}
    )
    journal = Journal(MemoryStore())
    record = journal.admit(request)
    for name, state in [
        ("prepare", "awaiting-review"),
        ("review", "building"),
        ("build", "awaiting-approval"),
    ]:
        record = checkpoint(journal, record, name, {"ok": True}, state)
    record = invoke((journal, record, *publication[2:]))
    sealed = {
        "nonce": "f" * 32,
        "controller_sha": "c" * 40,
        "controller_ref": "production",
        "repository_id": policy.repository_id,
        "created_at": 0,
        "workflow_path": ".github/workflows/release-controller-docs.yml",
        "authority_actor_id": 8,
        "policy_digest": digest(policy),
    }
    CompositionJournal(journal).create(record, sealed)
    state = {"roles": {}, "sha": "c" * 40, "calls": []}
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "55",
        "GITHUB_ACTOR_ID": "999",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": "c" * 40,
        "GITHUB_REF": "refs/heads/production",
        "GITHUB_WORKFLOW_REF": (
            "owner/repo/.github/workflows/release-controller-docs.yml"
            "@refs/heads/production"
        ),
        "CG_RELEASE_CONTROLLER_REVISION": policy.controller.revision,
        "CG_RELEASE_WHEEL_SHA256": policy.controller.wheel_digest,
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    def transport(executable, argv, **kwargs):
        assert executable == "gh" and argv[:3] == ["api", "--method", "GET"]
        endpoint = argv[-1].removeprefix("repos/owner/repo/")
        state["calls"].append(endpoint)
        if endpoint == "repos/owner/repo":
            value = {"id": policy.repository_id, "default_branch": "production"}
        elif endpoint == "branches/production":
            value = {
                "name": "production",
                "protected": True,
                "commit": {"sha": state["sha"]},
            }
        elif endpoint.startswith("user/"):
            uid = int(endpoint.split("/")[-1])
            value = {"id": uid, "login": f"user{uid}"}
        elif endpoint.startswith("collaborators/"):
            uid = int(endpoint.split("/")[1].removeprefix("user"))
            role = state["roles"].get(uid, "write")
            value = {"user": {"id": uid}, "role_name": role, "permission": role}
        elif endpoint == "actions/runs/55":
            if state.get("revoke_after_run"):
                state["roles"][state.get("revoke_id", record.request.requester_id)] = (
                    "read"
                )
            value = {
                "id": 55,
                "actor": {"id": 999},
                "event": "workflow_dispatch",
                "run_attempt": 1,
                "head_sha": "c" * 40,
                "head_branch": "production",
                "repository": {"id": policy.repository_id},
                "status": "in_progress",
                "path": sealed["workflow_path"],
            }
        else:
            raise AssertionError("Unexpected outer I/O: " + endpoint)
        return SimpleNamespace(
            returncode=0, stdout="HTTP/2.0 200 OK\n\n" + json.dumps(value)
        )

    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=transport)
    context = SimpleNamespace(
        api=api,
        journal=journal,
        policy=policy,
        default="production",
        policy_sha="c" * 40,
    )
    return context, record, sealed, state, env


@pytest.mark.parametrize("actor", [456, 8])
def test_revoked_requester_or_resumer_after_queue_has_no_registration(worker, actor):
    context, record, sealed, state, env = worker
    state["roles"][actor] = "read"
    before = context.journal.events()
    with pytest.raises(ControllerError, match="authority"):
        register(context, record, sealed["nonce"], env)
    assert context.journal.events() == before


def test_registration_rechecks_protected_default_after_queue(worker):
    context, record, sealed, state, env = worker
    state["sha"] = "e" * 40
    before = context.journal.events()
    with pytest.raises(ControllerError, match="policy"):
        register(context, record, sealed["nonce"], env)
    assert context.journal.events() == before


def test_registration_rechecks_actor_after_remote_run_read(worker):
    context, record, sealed, state, env = worker
    state["revoke_after_run"] = True
    before = context.journal.events()
    with pytest.raises(ControllerError, match="authority"):
        register(context, record, sealed["nonce"], env)
    assert context.journal.events() == before


def test_revoked_actor_after_build_cannot_start_composition(worker, tmp_path):
    context, record, sealed, state, env = worker
    register(context, record, sealed["nonce"], env)
    record = context.journal.get(record.request_id)
    state["roles"][record.request.requester_id] = "read"
    before = context.journal.events()
    root = tmp_path / "composition"
    with pytest.raises(ControllerError, match="authority"):
        compose(context, record, sealed["nonce"], root)
    assert not root.exists() and context.journal.events() == before


def test_changed_bound_policy_cannot_reconcile_published_request(worker):
    from cg_release.controller import reconcile

    context, record, _, _, _ = worker
    context.policy = context.policy.model_copy(update={"signing_required": True})
    before = context.journal.events()
    with pytest.raises(ControllerError, match="policy"):
        reconcile(context, record.request_id)
    assert context.journal.events() == before


def test_delayed_deployment_rechecks_authority(worker):
    from cg_release import profile_worker

    context, record, sealed, state, env = worker
    register(context, record, sealed["nonce"], env)
    record = context.journal.get(record.request_id)
    state["roles"][8] = "read"
    before = context.journal.events()
    with pytest.raises(ControllerError, match="authority"):
        profile_worker.authorize_deployment(context, record, sealed["nonce"], env)
    assert context.journal.events() == before


def test_deploy_checks_exact_manifest_and_policy_after_composition(worker):
    from cg_release.profile_deploy import authorize_deployment

    context, record, sealed, state, env = worker
    register(context, record, sealed["nonce"], env)
    record = context.journal.get(record.request_id)
    result = {
        "run_id": 55,
        "request_digest": digest(sealed),
        "manifest_sha256": "a" * 64,
    }
    store = CompositionJournal(context.journal)
    store.save(store.records()[-1], "composition", result)
    env["EXPECTED_MANIFEST"] = "a" * 64
    before = context.journal.events()
    assert authorize_deployment(context, record, sealed["nonce"], env) == result
    env["EXPECTED_MANIFEST"] = "b" * 64
    with pytest.raises(ControllerError, match="exact registered composition"):
        authorize_deployment(context, record, sealed["nonce"], env)
    env["EXPECTED_MANIFEST"] = "a" * 64
    state["sha"] = "e" * 40
    with pytest.raises(ControllerError, match="policy"):
        authorize_deployment(context, record, sealed["nonce"], env)
    assert context.journal.events() == before


def test_required_hooks_are_read_from_approved_build_not_current_profile(
    publication_context,
):
    """Pure evidence-decoder fixture; no substituted verifier or hook success."""
    from copy import deepcopy

    from cg_release.hook_authority import required_hooks
    from cg_release.publish_worker import execute_publication, seal_publication

    context, record, remote, env, _ = publication_context
    saved, _, _ = seal_publication(context, record, "a" * 32, env, remote)
    published = execute_publication(
        context, saved, "a" * 32, env, remote, now=1789171200
    )
    assert required_hooks(published) == set()
    # GPID archived evidence has a profile on its approved ticket. Decode it
    # independently of the currently loaded generic policy, including recovery.
    evidence = deepcopy(published.evidence)
    evidence["build-request-1"]["profile_version"] = "v1"
    archived = published.model_copy(update={"evidence": evidence})
    assert context.policy.gpid_profile is None
    assert required_hooks(archived) == {"docs", "evidence"}
    del evidence["build-request-1"]["profile_version"]
    with pytest.raises(ControllerError, match="Immutable required hook evidence"):
        required_hooks(archived)


@pytest.mark.parametrize("actor", [456, 8])
def test_final_deployment_run_read_cannot_outlast_human_authority(worker, actor):
    from cg_release.profile_deploy import authorize_deployment

    context, record, sealed, state, env = worker
    register(context, record, sealed["nonce"], env)
    store = CompositionJournal(context.journal)
    store.save(
        store.records()[-1],
        "composition",
        dict(run_id=55, request_digest=digest(sealed), manifest_sha256="a" * 64),
    )
    env["EXPECTED_MANIFEST"] = "a" * 64
    state.update(revoke_after_run=True, revoke_id=actor)
    before = context.journal.events()
    with pytest.raises(ControllerError, match="authority"):
        authorize_deployment(context, record, sealed["nonce"], env)
    assert context.journal.events() == before


def test_registration_storage_interleaving_rejects_old_ticket(worker):
    context, record, sealed, _, env = worker
    store = CompositionJournal(context.journal)
    item = store.records()[-1]
    item = store.save(item, "absence", {"observed_at": 1000})
    history = context.journal.store.history
    fired = False

    def interleaved():
        nonlocal fired
        snapshot = history()
        if not fired:
            fired = True
            store.create(record, {**sealed, "nonce": "2" * 32})
        return snapshot

    context.journal.store.history = interleaved
    with pytest.raises(ControllerError):
        register(context, record, sealed["nonce"], env)
    assert "registration" not in store.records()[-1].evidence
