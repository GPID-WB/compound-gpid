"""Stage coordinator seals inputs before writes and retains observed PR IDs."""

import json
from types import SimpleNamespace

from journal_store import MemoryStore
from test_preview import snapshot

from cg_release.admission import Locator, Receipt
from cg_release.cli import parse_args
from cg_release.journal import Journal
from cg_release.models import Policy, canonical_bytes, load_record
from cg_release.preparation import TreeEntry, object_id, tree_id
from cg_release.prepare_stage import prepare_step
from cg_release.preview import create_proposal, request_from_proposal


def test_prepare_then_review_binding_uses_real_journal(monkeypatch):
    state = snapshot()
    from dataclasses import replace

    raw_policy = json.loads(state.policy_raw)
    raw_policy["enabled"] = True
    state = replace(state, policy_raw=canonical_bytes(raw_policy))
    args = parse_args(["start", "--version", "1.0.0", "--yes"])
    proposal = create_proposal(state, args)
    request = request_from_proposal(proposal, nonce="1" * 32)
    locator = Locator.from_request(request).encode()
    journal = Journal(MemoryStore())
    record = journal.admit(
        request,
        receipt=Receipt(
            request_id=locator,
            number=1,
            node_id="node",
            url="https://github.com/owner/repo/issues/1",
            request=request,
            created_at="2026-09-11T00:00:00Z",
        ),
    )
    entries = [
        TreeEntry(p, b.mode, object_id("blob", b.content))
        for p, b in state.blobs.items()
    ]
    root = tree_id(entries)
    api = SimpleNamespace(
        slug="owner/repo",
        host="github.com",
        clock=lambda: 0,
        deadline=120,
        remaining=lambda: 120,
        branch=lambda name: {
            "commit": {
                "sha": request.policy_sha if name == "default" else request.source_sha
            }
        },
        get=lambda endpoint: {"sha": request.source_sha, "tree": {"sha": root}},
        _request=lambda endpoint, page: {
            "sha": root,
            "truncated": False,
            "tree": [
                {"path": e.path, "mode": e.mode, "sha": e.oid, "type": "blob"}
                for e in entries
            ],
        },
    )
    context = SimpleNamespace(
        api=api,
        policy=load_record(Policy, state.policy_raw),
        policy_sha=request.policy_sha,
        default="default",
        journal=journal,
    )
    monkeypatch.setattr(
        "cg_release.controller.revalidate", lambda *a, **k: (proposal, state)
    )
    monkeypatch.setattr("cg_release.prepare_stage.authorize_resume", lambda *a: None)
    seen = []

    def ensure(self, req, prepared, source_tree, modes, created_at):
        assert journal.get(locator).intent["operation"] == "prepare"
        manifest = next(e for e in prepared.edits if e.path == ".release-manifest.json")
        assert json.loads(manifest.content)["request_id"] == locator
        seen.append(1)
        return {
            "number": 42,
            "id": 99,
            "head": "b" * 40,
            "branch": "release-controller/" + request.nonce,
            "tree": prepared.tree,
            "source_sha": request.source_sha,
        }

    monkeypatch.setattr("cg_release.prepare_stage.PreparationRemote.ensure", ensure)
    result = prepare_step(context, record)
    assert (
        result.state == "awaiting-review"
        and result.evidence["prepare-pr"]["number"] == 42
    )
    monkeypatch.setattr(
        "cg_release.prepare_stage.verify_merge",
        lambda *a, **k: {
            "release_sha": "d" * 40,
            "release_tree": result.evidence["prepare-pr"]["tree"],
            "review_ids": [10],
        },
    )
    context.policy_sha = "d" * 40
    api.branch = lambda name: {"commit": {"sha": "d" * 40}}
    result = prepare_step(context, result)
    assert (
        result.state == "building"
        and result.evidence["review-binding"]["release_sha"] == "d" * 40
    )
    assert seen == [1]
