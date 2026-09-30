"""Expired post-tag build evidence returns to isolated builds without rollback."""

import pytest

from cg_release.events import ControllerError
from cg_release.publication_rebuild import begin_rebuild
from cg_release.publish_worker import execute_publication, seal_publication


def test_expired_partial_publication_rebuild_retains_tag_and_original_intent(
    publication_context,
):
    context, record, remote, env, _ = publication_context
    saved, _, _ = seal_publication(context, record, "a" * 32, env, remote)
    remote.fail = ("asset-package.whl", "before")
    with pytest.raises(ControllerError):
        execute_publication(context, saved, "a" * 32, env, remote, now=1789171200)
    previous = context.journal.get(record.request_id)
    get = context.api.get
    context.api.get = lambda path, **kw: (
        {**get(path), "status": "completed"}
        if path == "actions/runs/41"
        else get(path, **kw)
    )
    changed = begin_rebuild(
        context, previous, remote, actor_id=8, run_id=91, now=1789178400
    )
    assert (
        changed.state == "building"
        and changed.publication_started
        and not changed.published
    )
    assert changed.intent is None
    assert (
        changed.evidence["publication-rebuild-1"]["suspended_intent"] == previous.intent
    )
    assert (
        changed.evidence["publication-tag-object"]
        == previous.evidence["publication-tag-object"]
    )
    assert remote.writes == ["tag", "draft", "asset-package.whl"]


def test_live_owner_or_published_release_blocks_rebuild(publication_context):
    context, record, remote, env, _ = publication_context
    saved, _, _ = seal_publication(context, record, "a" * 32, env, remote)
    remote.fail = ("asset-package.whl", "before")
    with pytest.raises(ControllerError):
        execute_publication(context, saved, "a" * 32, env, remote, now=1789171200)
    pending = context.journal.get(record.request_id)
    with pytest.raises(ControllerError):
        begin_rebuild(context, pending, remote, actor_id=8, run_id=91, now=1789178400)
