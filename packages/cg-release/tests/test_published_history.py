"""Published journal receipts are durable adopted history, not a bootstrap rewrite."""

import subprocess

import pytest
from test_history import History
from test_publisher import invoke

from cg_release.events import ControllerError
from cg_release.history import adopted_history
from cg_release.journal import digest


@pytest.fixture
def published_case(publication, tmp_path):
    record = invoke(publication)
    inputs, remote = publication[2], publication[-1]
    record = record.model_copy(
        update={
            "evidence": {
                **record.evidence,
                "publication-seal-41": {
                    "run_id": 41,
                    "inputs": inputs,
                    "digest": digest(inputs),
                },
            }
        }
    )
    api = History()
    api.policy = api.policy.model_copy(update={"bootstrap": []})
    api.release = {**remote.release, "published_at": "2026-09-12T00:00:00Z"}
    api.host, api.slug, api.cwd, api.read_seconds = (
        "github.com",
        "owner/repo",
        tmp_path,
        20,
    )
    api.remaining = lambda: 120
    api.pages = lambda endpoint: (
        [api.release] if endpoint == "releases" else list(remote.assets.values())
    )
    api.runner = lambda *a, **k: subprocess.CompletedProcess(
        a, 0, remote.assets["package.whl"]["bytes"], b""
    )
    api.ref["object"] = {
        "type": "tag",
        "sha": record.evidence["publication-tag-object"]["oid"],
    }
    original = api.get
    api.get = lambda path: (
        {
            "sha": api.ref["object"]["sha"],
            "tag": api.tag,
            "object": {"type": "commit", "sha": "a" * 40},
        }
        if path.startswith("git/tags/")
        else original(path)
    )
    return api, record, remote


def test_new_published_journal_identity_is_used_for_future_admission(published_case):
    api, record, _ = published_case
    rows, occupied = adopted_history(api, api.policy, records=[record])
    assert rows[0]["release_id"] == 71 and rows[0]["version"] == "1.0.0"
    assert occupied == ["1.0.0"]


@pytest.mark.parametrize("change", ["tag", "asset", "notes", "asset-id"])
def test_published_object_change_blocks_new_admission(published_case, change):
    api, record, remote = published_case
    if change == "tag":
        api.ref["object"] = {"type": "commit", "sha": "a" * 40}
    if change == "asset":
        remote.assets["package.whl"]["bytes"] = b"tampered"
    if change == "notes":
        api.release["body"] = "changed"
    if change == "asset-id":
        remote.assets["package.whl"]["id"] = 999
    with pytest.raises(ControllerError):
        adopted_history(api, api.policy, records=[record])
