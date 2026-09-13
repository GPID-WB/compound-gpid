"""Canonical incremental tree identities are checked against Git, not server flags."""

import subprocess

import pytest
from test_lifecycle import receipt_fixture
from test_remote_faults import Server

from cg_release.events import ControllerError
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal
from cg_release.journal_tree import JournalTree
from cg_release.preparation import TreeEntry, tree_id
from cg_release.queue import scan


def test_incremental_journal_tree_matches_real_git(tmp_path):
    subprocess.run(
        ["git", "init", "--bare", str(tmp_path)], check=True, capture_output=True
    )
    tree = JournalTree()
    assert tree.oid == "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    changes = [
        {
            "events/0000000001.json": b"one",
            "requests/" + "f" * 64 + ".json": b"request",
        },
        {
            "events/0000000002.json": b"two",
            "requests/" + "a" * 64 + ".json": b"earlier",
            "queue.json": b"queue",
        },
        {"requests/" + "f" * 64 + ".json": b"updated"},
        {
            "requests/" + "f" * 64 + ".json": None,
            "requests/" + "a" * 64 + ".json": None,
        },
        {"events/10000000000.json": b"long ordinal", "queue.json": None},
    ]
    for delta in changes:
        oid = tree.update(delta)
        nodes = {}
        for path, value in tree.paths.items():
            parent, _, name = path.rpartition("/")
            nodes.setdefault(parent, {})[name] = ("100644", "blob", value)
        root = nodes.pop("", {})

        def git_tree(rows):
            raw = b"".join(
                f"{mode} {kind} {sha}\t{name}\0".encode()
                for name, (mode, kind, sha) in rows.items()
            )
            result = subprocess.run(
                ["git", "mktree", "-z", "--missing"],
                cwd=tmp_path,
                input=raw,
                capture_output=True,
                check=True,
            )
            return result.stdout.decode().strip()

        for parent, rows in nodes.items():
            root[parent] = ("040000", "tree", git_tree(rows))
        assert oid == git_tree(root)


@pytest.mark.parametrize("damage", ["extra-file", "mode", "event-bytes"])
def test_restored_head_does_not_hide_an_invalid_historical_tree(tmp_path, damage):
    server = Server(tmp_path)
    journal = Journal(
        GitHubJournalStore(server, server.policy, bot_id=77, writable=True)
    )
    journal.admit(receipt_fixture().request)
    first = server.current
    scan(journal, [], lambda item: None)
    commit = server.commits[first]
    rows = [dict(row) for row in server.trees[commit["commit"]["tree"]["sha"]]["tree"]]
    if damage == "extra-file":
        rows.append(dict(path="unexpected", mode="100644", sha="e" * 40))
    elif damage == "mode":
        rows[0]["mode"] = "100755"
    else:
        rows[0]["sha"] = "e" * 40
    commit["commit"]["tree"]["sha"] = tree_id(
        [TreeEntry(r["path"], r["mode"], r["sha"]) for r in rows]
    )
    with pytest.raises(ControllerError, match="atomic tree"):
        Journal(GitHubJournalStore(server, server.policy, bot_id=77)).records()
