"""Controller wakeups dispatch one immutable publication ticket and then return."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from cg_release.events import ControllerError
from cg_release.publication_stage import publication_step


def test_dispatch_is_once_and_does_not_publish(publication, tmp_path):
    journal, record, *_ = publication
    calls = []

    def runner(tool, args, **kwargs):
        calls.append((args, json.loads(kwargs["input_text"])))
        return subprocess.CompletedProcess(args, 0, "HTTP/2.0 204 No Content\n\n", "")

    api = SimpleNamespace(
        runner=runner,
        host="github.com",
        slug="owner/repo",
        cwd=tmp_path,
        read_seconds=20,
        remaining=lambda: 120,
    )
    context = SimpleNamespace(journal=journal, api=api, default="main")
    result = publication_step(context, record, resuming_actor_id=7)
    assert result.state == "awaiting-approval" and not result.publication_started
    assert calls[0][1]["ref"] == "main"
    assert calls[0][0][-1].endswith("release-controller-publish.yml/dispatches")
    assert publication_step(context, result) == result
    assert len(calls) == 1


def test_unknown_dispatch_never_blindly_replays(publication, tmp_path):
    journal, record, *_ = publication
    calls = []

    def lost(*args, **kwargs):
        calls.append(args)
        raise ControllerError("E_TIMEOUT", "lost")

    api = SimpleNamespace(
        runner=lost,
        host="github.com",
        slug="owner/repo",
        cwd=tmp_path,
        read_seconds=20,
        remaining=lambda: 120,
    )
    context = SimpleNamespace(journal=journal, api=api, default="main")
    with pytest.raises(ControllerError):
        publication_step(context, record)
    with pytest.raises(ControllerError):
        publication_step(context, journal.get(record.request_id))
    assert len(calls) == 1
