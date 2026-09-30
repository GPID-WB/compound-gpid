"""Fresh shared-hook authority at registration and admitted recovery boundaries."""

import json

import pytest
from test_profile_lifecycle import context
from test_profile_lifecycle import published_profile as published_profile
from test_profile_policy_recovery import admit_grant
from test_profile_security import worker as worker

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.hook_authority import authorize_hooks
from cg_release.profile_docs import docs_step
from cg_release.profile_worker import register


@pytest.mark.parametrize("actor", [456, 8])
@pytest.mark.parametrize("endpoint", ["repos/owner/repo", "branches/production"])
def test_registration_rechecks_authority_after_final_helper_metadata(
    worker, actor, endpoint
):
    ctx, record, sealed, state, env = worker
    original, saw_run, revoked = ctx.api.runner, False, False
    before = ctx.journal.events()

    def delayed(tool, argv, **kwargs):
        nonlocal saw_run, revoked
        value = original(tool, argv, **kwargs)
        resource = argv[-1].removeprefix("repos/owner/repo/")
        if resource == "actions/runs/55":
            saw_run = True
        if saw_run and resource == endpoint:
            state["roles"][actor] = "read"
            revoked = True
        return value

    ctx.api.runner = delayed
    with pytest.raises(ControllerError, match="authority"):
        register(ctx, record, sealed["nonce"], env)
    assert revoked and ctx.journal.events() == before


@pytest.mark.parametrize("fresh", [False, True])
def test_shared_helper_ends_with_authority_and_preserves_optional_freshness(
    worker, fresh
):
    ctx, record, _, state, _ = worker
    state["calls"].clear()
    assert authorize_hooks(ctx, record, 8, fresh=fresh) == 8
    reads = state["calls"]
    assert reads[-1].endswith("/permission")
    metadata = ["repos/owner/repo", "branches/production"]
    assert all((endpoint in reads) is fresh for endpoint in metadata)


@pytest.mark.parametrize("damage", ["repository", "default", "protection", "sha"])
def test_shared_helper_retains_exact_policy_guards(worker, damage):
    ctx, record, _, _, _ = worker
    original = ctx.api.runner
    before = ctx.journal.events()

    def changed(tool, argv, **kwargs):
        value = original(tool, argv, **kwargs)
        endpoint = argv[-1].removeprefix("repos/owner/repo/")
        header, body = value.stdout.split("\n\n", 1)
        data = json.loads(body)
        if endpoint == "repos/owner/repo":
            if damage == "repository":
                data["id"] = 999
            elif damage == "default":
                data["default_branch"] = "other"
        elif endpoint == "branches/production":
            if damage == "protection":
                data["protected"] = False
            elif damage == "sha":
                data["commit"]["sha"] = "e" * 40
        value.stdout = header + "\n\n" + json.dumps(data)
        return value

    ctx.api.runner = changed
    with pytest.raises(ControllerError) as error:
        authorize_hooks(ctx, record, 8, fresh=True)
    assert error.value.code == "E_HOOK_POLICY"
    assert ctx.journal.events() == before


@pytest.mark.parametrize("endpoint", ["", "branches/main"])
def test_admitted_grant_rechecked_after_helper_metadata(
    published_profile, tmp_path, endpoint
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = admit_grant(ctx, ctx.journal.get(locator))
    get, revoked = world.get, False
    before = ctx.journal.events()

    def delayed(resource, **kwargs):
        nonlocal revoked
        value = get(resource, **kwargs)
        if resource == endpoint:
            world.roles[8] = "read"
            revoked = True
        return value

    world.get = delayed
    with pytest.raises(ControllerError, match="grant|authority"):
        authorize_hooks(ctx, record, 8, fresh=True)
    assert revoked and ctx.journal.events() == before


@pytest.mark.parametrize("principal", ["requester", "resumer"])
def test_dispatch_rechecks_after_durable_intent_before_post(
    published_profile, tmp_path, principal
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    actor = record.request.requester_id if principal == "requester" else 8
    store = CompositionJournal(ctx.journal)
    world.begin_docs(store.records()[-1])
    world.docs_runs[55].update(status="completed", conclusion="cancelled")
    append = ctx.journal.store.append
    before = list(world.dispatches)

    def delayed(parent, event, item):
        value = append(parent, event, item)
        if json.loads(event)["audit"]["operation"] == "composition-intent":
            world.roles[actor] = "read"
        return value

    ctx.journal.store.append = delayed
    with pytest.raises(ControllerError, match="authority"):
        docs_step(ctx, record, resuming_actor_id=8)
    current = store.records()[-1]
    assert current.intent is not None and "dispatch" not in current.evidence
    assert world.dispatches == before


@pytest.mark.parametrize("principal", ["requester", "resumer"])
@pytest.mark.parametrize("ticket_read", [1, 2])
def test_composition_ticket_read_precedes_authority_at_each_effect(
    published_profile, tmp_path, monkeypatch, principal, ticket_read
):
    from profile_transport import snapshot_bytes

    from cg_release.profile_worker import compose

    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    item = CompositionJournal(ctx.journal).records()[-1]
    actor = (
        record.request.requester_id
        if principal == "requester"
        else item.ticket["authority_actor_id"]
    )
    world.begin_docs(item)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="55",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{item.ticket['workflow_path']}@refs/heads/main",
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    register(ctx, record, item.ticket["nonce"], env)
    dev = tmp_path / "dev-artifact"
    dev.mkdir()
    (dev / "dev-docs.json").write_bytes(
        snapshot_bytes(None, item.ticket["dev_sha"], 55, "dev")
    )
    output = tmp_path / "composition"
    runner, history = ctx.api.runner, ctx.journal.store.history
    acquired, reads = False, 0

    def download(tool, argv, **kwargs):
        nonlocal acquired
        value = runner(tool, argv, **kwargs)
        if "/releases/assets/" in argv[-1] and kwargs.get("binary_output"):
            acquired = True
        return value

    def delayed_history():
        nonlocal reads
        value = history()
        if acquired:
            reads += 1
            if reads == ticket_read:
                world.roles[actor] = "read"
        return value

    ctx.api.runner = download
    ctx.journal.store.history = delayed_history
    with pytest.raises(ControllerError, match="authority"):
        compose(ctx, record, item.ticket["nonce"], output)
    assert acquired and reads >= ticket_read
    assert "composition" not in CompositionJournal(ctx.journal).records()[-1].evidence
    if ticket_read == 1:
        assert not output.exists()


@pytest.mark.parametrize("principal", ["requester", "resumer"])
def test_evidence_base_read_does_not_outlast_authority_before_intent(
    tmp_path, monkeypatch, capsys, installed_profile, principal
):
    from profile_transport import ProfileTransport
    from test_phase5_transport import publisher
    from test_profile_lifecycle import prepared

    from cg_release.hooks import selected_profile
    from cg_release.profile_evidence import evidence_step

    world = ProfileTransport(tmp_path)
    locator, nonce = prepared(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    for operation in ["seal", "publish"]:
        code, result = publisher(
            world, monkeypatch, capsys, tmp_path, locator, nonce, operation
        )
        assert code == 0, result
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    actor = record.request.requester_id if principal == "requester" else 8
    append, get = ctx.journal.store.append, world.get
    sealed, revoked = False, False

    def after_inputs(parent, event, value):
        nonlocal sealed
        result = append(parent, event, value)
        if "profile-evidence-inputs" in json.loads(event)["record"].get("evidence", {}):
            sealed = True
        return result

    def after_base(endpoint, **kwargs):
        nonlocal revoked
        value = get(endpoint, **kwargs)
        if sealed and endpoint == "branches/feature":
            world.roles[actor] = "read"
            revoked = True
        return value

    ctx.journal.store.append = after_inputs
    world.get = after_base
    before = (list(world.publication_writes), len(world.prs))
    with pytest.raises(ControllerError, match="authority"):
        evidence_step(
            ctx, record, selected_profile(ctx.policy).attestation, resuming_actor_id=8
        )
    assert revoked and ctx.journal.get(locator).intent is None
    assert (world.publication_writes, len(world.prs)) == before
