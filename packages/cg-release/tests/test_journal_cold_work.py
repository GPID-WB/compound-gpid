"""Fresh-reader provider and decoded-tree work, without warm-session cache claims."""

import json
import subprocess

import pytest
from journal_store import MemoryStore
from test_lifecycle import receipt_fixture
from test_remote_faults import Server

from cg_release.git_journal import blob_id, transaction_files
from cg_release.github import GitHubReads
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal
from cg_release.journal_models import Record
from cg_release.models import canonical_bytes, load_record


def cold_work(tmp_path, count):
    """Measure one new authenticated fixture reader; return exact operation counts."""
    memory = Journal(MemoryStore())
    request = receipt_fixture().request
    for n in range(count):
        memory.admit(
            request.model_copy(
                update={"nonce": f"{n:032x}", "version": f"1.0.{n}", "tag": f"v1.0.{n}"}
            )
        )
    server = Server(tmp_path)
    server.policy = server.policy.model_copy(update={"journal_root": "a" * 40})
    server.current = server.policy.journal_root
    server._commit(server.current, None, {})
    files = {}
    for tx in memory.store.transactions:
        record = load_record(Record, canonical_bytes(json.loads(tx.event)["record"]))
        for path, raw in transaction_files(tx.event, record).items():
            server.objects[blob_id(raw)] = raw
            files[path] = blob_id(raw)
        server._commit(tx.commit, tx.parent, dict(files))
        server.current = tx.commit
    metrics = dict(
        events=count, provider_calls=0, processed_tree_entries=0, decoded_bytes=0
    )

    def wire(tool, argv, **kwargs):
        endpoint = argv[-1].removeprefix(f"repos/{server.slug}/")
        if endpoint.startswith("branches/"):
            value = server.branch(endpoint[9:])
        elif endpoint.startswith("git/trees/"):
            value = server._request(argv[-1], None)
            metrics["processed_tree_entries"] += len(value["tree"])
        else:
            value = server.get(endpoint)
        raw = json.dumps(value)
        metrics["provider_calls"] += 1
        metrics["decoded_bytes"] += len(raw.encode())
        return subprocess.CompletedProcess(argv, 0, "HTTP/2.0 200 OK\n\n" + raw, "")

    api = GitHubReads(server.host, server.slug, cwd=tmp_path, runner=wire)
    store = GitHubJournalStore(api, server.policy, bot_id=77)
    journal = Journal(store)
    assert len(journal.records()) == count
    metrics.update(store.last_reconstruction_work)
    return metrics


@pytest.mark.parametrize("count", [8, 16, 32])
def test_fresh_authenticated_history_work_is_measured(tmp_path, count):
    metrics = cold_work(tmp_path, count)
    assert metrics["provider_calls"] <= 2 * count + 4
    assert metrics["processed_tree_entries"] == 3 * count
    assert metrics["decoded_bytes"] > 0


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory(prefix="cg-journal-work-") as scratch:
        sys.stdout.write(
            json.dumps([cold_work(Path(scratch), n) for n in [8, 16, 32]]) + "\n"
        )
