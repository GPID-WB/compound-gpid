"""Each separate hook journal operation needs current authority, not a prior save."""

import json
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from hook_continuation_probe import assert_prefix, revoke_after
from test_profile_security import worker as worker

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.hook_authority import authorize_hooks
from cg_release.journal import digest
from cg_release.profile_dispatch import dispatch, recover_dispatch
from cg_release.profile_worker import register


@pytest.mark.parametrize("actor", [None, 456, 8])
def test_pending_dispatch_reconciliation_does_not_authorize_registration(worker, actor):
    ctx, record, sealed, state, env = worker
    store = CompositionJournal(ctx.journal)
    payload = dict(
        ref=ctx.default,
        inputs=dict(request_id=record.request_id, nonce=sealed["nonce"]),
    )
    item = store.intent(store.records()[-1], payload)
    probe = revoke_after(
        ctx.journal,
        state["roles"],
        actor,
        lambda e: e["audit"].get("stage") == "dispatch",
    )
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        assert register(ctx, record, sealed["nonce"], env) == sealed
    current = store.records()[-1]
    assert current.ticket == item.ticket and current.evidence["dispatch"] == payload
    assert current.intent is None
    assert_prefix(ctx.journal, probe)
    if actor:
        assert probe["revoked"] and "registration" not in current.evidence
        assert len(probe["appends"]) == 1
        with pytest.raises(ControllerError, match="authority"):
            authorize_hooks(ctx, record, 8, fresh=True)
    else:
        assert current.evidence["registration"] == dict(
            run_id=55, request_digest=digest(sealed)
        )
        assert len(probe["appends"]) == 2


@pytest.mark.parametrize("actor", [None, 456, 8])
@pytest.mark.parametrize("point", ["inventory", "dispatch-result"])
def test_absence_recovery_rechecks_each_separate_save(worker, actor, point):
    ctx, record, sealed, state, _ = worker
    store = CompositionJournal(ctx.journal)
    item = store.intent(
        store.records()[-1],
        dict(
            ref=ctx.default,
            inputs=dict(request_id=record.request_id, nonce=sealed["nonce"]),
        ),
    )
    probe = revoke_after(
        ctx.journal,
        state["roles"],
        actor if point == "dispatch-result" else None,
        lambda e: e["audit"].get("stage") == "dispatch",
    )
    original = ctx.api.runner

    def inventory(tool, argv, **kwargs):
        if "/runs?" in argv[-1]:
            if point == "inventory" and actor:
                state["roles"][actor] = "read"
                probe["revoked"] = True
            return SimpleNamespace(
                returncode=0,
                stdout="HTTP/2.0 200 OK\n\n"
                + json.dumps(dict(total_count=0, workflow_runs=[])),
            )
        return original(tool, argv, **kwargs)

    ctx.api.runner = inventory
    authorize_hooks(ctx, record, 8, fresh=True)
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        current, run, safe = recover_dispatch(ctx, record, item)
        assert run is None and not safe and "absence-first" in current.evidence
    current = store.records()[-1]
    assert_prefix(ctx.journal, probe)
    if actor:
        assert probe["revoked"] and "absence-first" not in current.evidence
        if point == "inventory":
            assert current.intent == item.intent and not probe["appends"]
        else:
            assert current.evidence["dispatch"] == {"uncertain": True}
            assert len(probe["appends"]) == 1


@pytest.mark.parametrize("actor", [None, 456, 8])
def test_dispatch_post_completion_does_not_authorize_result_save(worker, actor):
    ctx, record, _, state, _ = worker
    store = CompositionJournal(ctx.journal)
    original = ctx.api.runner
    posts = []

    def post(tool, argv, **kwargs):
        if argv[:3] == ["api", "--method", "POST"]:
            posts.append(kwargs["input_text"])
            if actor:
                state["roles"][actor] = "read"
            return SimpleNamespace(returncode=0, stdout="HTTP/2.0 204 No Content\n\n")
        return original(tool, argv, **kwargs)

    ctx.api.runner = post
    probe = revoke_after(ctx.journal, state["roles"], None, lambda e: False)
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        dispatch(ctx, record, store.records()[-1])
    assert len(posts) == 1
    assert_prefix(ctx.journal, probe)
    current = store.records()[-1]
    if actor:
        assert current.intent is not None and "dispatch" not in current.evidence
        assert len(probe["appends"]) == 1
    else:
        assert current.intent is None and "dispatch" in current.evidence
