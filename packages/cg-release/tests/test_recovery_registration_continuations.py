"""Current native registration and reviewed recovery renew authority between effects."""

import json
from contextlib import nullcontext

import pytest
from hook_continuation_probe import assert_prefix, revoke_after
from profile_transport import ProfileTransport
from test_profile_lifecycle import connect, context, prepared
from test_profile_lifecycle import published_profile as published_profile
from test_profile_policy_recovery import admit_grant
from test_recovery_actions import restore_case as restore_case
from test_stranded_recovery import stranded_case as stranded_case

from cg_release import build_worker
from cg_release.events import ControllerError
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import digest
from cg_release.recovery_actions import restore_journal
from cg_release.stranded_recovery import recover_publication


@pytest.mark.parametrize("revoke", [False, True])
@pytest.mark.parametrize("point", ["run-read", "dispatch-result"])
def test_native_profile_registration_renews_authority_at_continuations(
    tmp_path, monkeypatch, capsys, installed_profile, revoke, point
):
    world = ProfileTransport(tmp_path)
    locator, tickets = prepared(
        world, monkeypatch, capsys, tmp_path, register_builds=False
    )
    sealed = next(t for t in tickets if t["produces_artifacts"])
    ctx = context(world, locator, tmp_path)
    actor = ctx.journal.get(locator).request.requester_id
    number = next(
        int(k.rsplit("-", 1)[1])
        for k, v in ctx.journal.get(locator).evidence.items()
        if k.startswith("build-request-") and v == sealed
    )
    operation = f"build-dispatch-{number}"
    payload = dict(
        ref=sealed["controller_ref"],
        inputs=dict(build_request=locator, dispatch_nonce=sealed["dispatch_nonce"]),
    )
    ctx.journal.intent(locator, operation, digest(payload))
    before = list(ctx.journal.store.history()[1])
    world.begin_build(sealed, 21)
    original, append = world.run, GitHubJournalStore.append
    saw_run, human_checked, revoked = False, False, False

    def delayed(tool, argv, **kwargs):
        nonlocal saw_run, human_checked, revoked
        value = original(tool, argv, **kwargs)
        if argv[-1].endswith("/actions/runs/21"):
            if human_checked and point == "run-read" and revoke:
                world.roles[actor] = "read"
                revoked = True
            saw_run = True
        if saw_run and argv[-1].endswith(f"/collaborators/user{actor}/permission"):
            human_checked = True
        return value

    def after_dispatch(store, parent, raw, record):
        nonlocal revoked
        value = append(store, parent, raw, record)
        event = json.loads(raw)
        if (
            point == "dispatch-result"
            and revoke
            and event["audit"]["operation"] == operation
            and event["record"].get("intent") is None
        ):
            world.roles[actor] = "read"
            revoked = True
        return value

    world.run = delayed
    connect(world, monkeypatch)
    monkeypatch.setattr(GitHubJournalStore, "append", after_dispatch)
    env = world.environment()
    env.update(
        GITHUB_RUN_ID="21",
        GITHUB_ACTOR_ID="77",
        GITHUB_WORKFLOW_REF=f"{world.slug}/{sealed['workflow_path']}@refs/heads/main",
        GITHUB_OUTPUT=str(tmp_path / "native-output"),
    )
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    code = build_worker.main(
        ["register", "--request-id", locator, "--nonce", sealed["dispatch_nonce"]]
    )
    capsys.readouterr()
    assert ctx.journal.store.history()[1][: len(before)] == before
    current = ctx.journal.get(locator)
    if revoke:
        assert revoked and code == 2
        assert f"build-registration-{number}" not in current.evidence
        if point == "dispatch-result":
            assert operation in current.evidence and current.intent is None
    else:
        assert code == 0 and f"build-registration-{number}" in current.evidence


@pytest.mark.parametrize("revoke", [False, True])
def test_stranded_admission_does_not_authorize_later_audit(stranded_case, revoke):
    ctx, spec, remote, _ = stranded_case
    get, revoked = ctx.api.get, False

    def permission(path, **kwargs):
        value = get(path, **kwargs)
        if revoked and path.endswith("/permission"):
            return {**value, "permission": "read"}
        return value

    ctx.api.get = permission
    append = ctx.journal.store.append
    prefix = list(ctx.journal.store.history()[1])

    def after_admit(parent, raw, record):
        nonlocal revoked
        value = append(parent, raw, record)
        if revoke and json.loads(raw)["audit"]["operation"] == "recover-admit":
            revoked = True
        return value

    ctx.journal.store.append = after_admit
    with (
        pytest.raises(ControllerError, match="maintainer|authority")
        if revoke
        else nullcontext()
    ):
        recover_publication(
            ctx,
            spec,
            actor_id=8,
            run_id=91,
            directive_digest=digest(spec),
            remote=remote,
        )
    assert ctx.journal.store.history()[1][: len(prefix)] == prefix
    events = ctx.journal.events()
    assert any(e["audit"]["operation"] == "recover-admit" for e in events)
    assert any(e["record"].get("kind") == "recovery" for e in events) is (not revoke)


@pytest.mark.parametrize("point", ["record-read", "grant-result"])
@pytest.mark.parametrize("revoke", [False, True])
def test_source_exception_checks_before_grant_and_before_separate_audit(
    published_profile, tmp_path, point, revoke
):
    world, locator = published_profile
    ctx = context(world, locator, tmp_path)
    record = ctx.journal.get(locator)
    probe = revoke_after(
        ctx.journal,
        world.roles,
        8 if revoke and point == "grant-result" else None,
        lambda e: e["audit"]["operation"] == "publication-exception-99",
    )
    history = ctx.journal.store.history

    def after_record():
        value = history()
        if point == "record-read" and revoke and not probe["revoked"]:
            world.roles[8] = "read"
            probe["revoked"] = True
        return value

    ctx.journal.store.history = after_record
    with (
        pytest.raises(ControllerError, match="maintainer|grant|authority")
        if revoke
        else nullcontext()
    ):
        admit_grant(ctx, record)
    assert_prefix(ctx.journal, probe)
    if revoke:
        assert probe["revoked"]
        assert not any(e["record"].get("kind") == "recovery" for e in probe["appends"])
        if point == "record-read":
            assert "publication-exception-99" not in ctx.journal.get(locator).evidence
        else:
            assert "publication-exception-99" in ctx.journal.get(locator).evidence


@pytest.mark.parametrize("revoke", [False, True])
def test_restore_readback_does_not_authorize_separate_audit(restore_case, revoke):
    ctx, spec, writes = restore_case
    original, get, revoked = ctx.api.runner, ctx.api.get, False

    def permission(path, **kwargs):
        value = get(path, **kwargs)
        return (
            {**value, "permission": "read"}
            if revoked and path.endswith("/permission")
            else value
        )

    def after_restore(tool, argv, **kwargs):
        nonlocal revoked
        value = original(tool, argv, **kwargs)
        if revoke and "/git/refs" in argv[-1]:
            revoked = True
        return value

    ctx.api.get, ctx.api.runner = permission, after_restore
    with (
        pytest.raises(ControllerError, match="maintainer|authority")
        if revoke
        else nullcontext()
    ):
        restore_journal(
            ctx, spec, actor_id=456, run_id=91, directive_digest=digest(spec)
        )
    assert len(writes) == 1 and ctx.journal.events()
    assert any(e["record"].get("kind") == "recovery" for e in ctx.journal.events()) is (
        not revoke
    )
