"""Remote journal must use atomic expected-head mutation and signed App commits."""

import json
import subprocess

import pytest
from test_authority import Controls

from cg_release.events import ControllerError
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal


def test_missing_anchor_or_unsigned_history_is_not_empty_state():
    api = Controls()
    api.get = lambda endpoint: {
        "sha": "a" * 40,
        "parents": [],
        "commit": {"tree": {"sha": "b" * 40}},
    }
    with pytest.raises(ControllerError):
        Journal(GitHubJournalStore(api, api.policy, bot_id=77)).records()


def test_atomic_write_uses_expected_head_and_no_force(tmp_path):
    api = Controls()
    calls = []
    api.cwd = tmp_path
    api.read_seconds = 20
    api.remaining = lambda: 20

    def runner(tool, argv, **kwargs):
        calls.append((argv, json.loads(kwargs["input_text"])))
        return subprocess.CompletedProcess(
            argv,
            0,
            'HTTP/2.0 200 OK\n\n{"data":{"createCommitOnBranch":{"commit":{"oid":"'
            + "c" * 40
            + '"}}}}',
            "",
        )

    api.runner = runner
    store = GitHubJournalStore(api, api.policy, bot_id=77, writable=True)
    store.write_files(
        "a" * 40,
        {"events/0000000001.json": b'{"schema_version":1}'},
        "Queue checkpoint",
    )
    argv, body = calls[0]
    assert argv[-1] == "graphql" and "--input" in argv
    assert body["variables"]["input"]["expectedHeadOid"] == "a" * 40
    assert "force" not in json.dumps(body).lower()
    assert "createCommitOnBranch" in body["query"]


def test_read_only_store_cannot_write(tmp_path):
    api = Controls()
    with pytest.raises(ControllerError):
        GitHubJournalStore(api, api.policy, bot_id=77).write_files("a" * 40, {}, "No")
