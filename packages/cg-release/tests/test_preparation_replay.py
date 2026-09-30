"""An admitted request may exclude only its exact verified reservation."""

import pytest
from test_worker_e2e import start, worker
from test_worker_e2e import world as _world

from cg_release import controller
from cg_release.context import context_for
from cg_release.events import ControllerError

world = _world


def test_sealed_replay_excludes_only_own_reservation(world, monkeypatch, capsys):
    locator = start(world, capsys)
    assert worker(world, monkeypatch, capsys, locator)[0] == 0
    context = context_for(
        locator, cwd=world.cwd, clock=world.clock, deadline=world.clock() + 120
    )
    request = context.journal.get(locator).request
    proposal, snapshot = controller.revalidate(context, request, sealed=True)
    assert proposal.digest == request.proposal_digest
    assert snapshot.occupied == []
    world.tag_nodes = [
        {
            "name": request.tag,
            "target": {"__typename": "Commit", "oid": request.source_sha},
        }
    ]
    with pytest.raises(ControllerError):
        controller.revalidate(context, request, sealed=True)


def test_unsealed_or_changed_request_cannot_claim_own_reservation(world, capsys):
    locator = start(world, capsys)
    context = context_for(
        locator, cwd=world.cwd, clock=world.clock, deadline=world.clock() + 120
    )
    from cg_release.admission import discover
    from cg_release.inbox import GitHubInbox

    request = discover(locator, GitHubInbox(context.api)).request
    with pytest.raises(ControllerError):
        controller.revalidate(context, request, sealed=True)
