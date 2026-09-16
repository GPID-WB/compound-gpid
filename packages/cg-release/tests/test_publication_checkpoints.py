"""Cancellation before/after every local publication intent/result checkpoint."""

import json

import pytest
from test_publisher import invoke

from cg_release.recovery import finish_hooks

SLOTS = ["publication-tag-object:atomic"] + [
    f"{name}:{kind}"
    for name in (
        "publication-tag",
        "publication-draft",
        "publication-asset-1",
        "publication-publish",
        "publication-receipt",
        "publication-hooks",
    )
    for kind in ("intent", "result")
]


@pytest.mark.parametrize("slot", SLOTS)
@pytest.mark.parametrize("boundary", ["before", "after"])
def test_each_checkpoint_replays_without_duplicate_effect(publication, slot, boundary):
    journal, _, _, _, _, remote = publication
    append = journal.store.append
    fired = []

    def interrupted(parent, raw, record):
        event = json.loads(raw)
        kind = (
            "atomic"
            if event["audit"].get("publication_atomic")
            else "intent"
            if record.intent
            else "result"
        )
        selected = event["audit"]["operation"] + ":" + kind == slot and not fired
        if selected:
            fired.append(True)
        if selected and boundary == "before":
            raise KeyboardInterrupt("checkpoint not accepted")
        result = append(parent, raw, record)
        if selected and boundary == "after":
            raise KeyboardInterrupt("checkpoint accepted; worker cancelled")
        return result

    journal.store.append = interrupted

    def complete():
        return finish_hooks(journal, invoke(publication), required=set(), verified={})

    with pytest.raises(KeyboardInterrupt):
        complete()
    assert fired and complete().state == "complete"
    assert remote.writes == ["tag", "draft", "asset-package.whl", "publish"]
