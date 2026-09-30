"""Fault-injected GitHub Git/GraphQL protocol, including signed-history validation."""

import base64
import hashlib
import json
import subprocess

import pytest
from test_authority import Controls
from test_lifecycle import receipt_fixture

from cg_release.events import ControllerError
from cg_release.git_journal import blob_id, transaction_files
from cg_release.github import GitHubReads
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal
from cg_release.journal_models import Record
from cg_release.models import canonical_bytes, load_record
from cg_release.queue import cursor_for, scan


class Server(Controls):
    """Model irreversible atomic writes separately from response delivery."""

    def __init__(self, cwd):
        super().__init__()
        self.cwd, self.read_seconds = cwd, 20
        self.current = self.policy.journal_root
        self.objects, self.trees = {}, {}
        self.commits = {}
        self._commit(self.current, None, {})
        self.lost = False
        self.writes = 0

    def remaining(self):
        return 20

    def _commit(self, oid, parent, files):
        from cg_release.preparation import TreeEntry, tree_id

        tree = tree_id([TreeEntry(p, "100644", value) for p, value in files.items()])
        self.trees[tree] = {
            "sha": tree,
            "truncated": False,
            "tree": [
                {"path": path, "mode": "100644", "type": "blob", "sha": value}
                for path, value in files.items()
            ],
        }
        self.commits[oid] = {
            "sha": oid,
            "parents": [{"sha": parent}] if parent else [],
            "committer": {"id": 77},
            "commit": {
                "tree": {"sha": tree},
                "verification": {
                    "verified": True,
                    "reason": "valid",
                    "signature": "fixture-signature-not-live-evidence",
                    "payload": "fixture-payload",
                },
            },
        }

    def branch(self, name):
        return {"name": name, "protected": True, "commit": {"sha": self.current}}

    def _request(self, resource, page, **kwargs):
        if "/git/trees/" in resource:
            return self.trees[resource.rsplit("/", 1)[1].split("?")[0]]
        return super()._request(resource, page)

    def get(self, endpoint, **kwargs):
        if endpoint.startswith("commits/"):
            if endpoint[8:] not in self.commits:
                raise ControllerError("E_NOT_FOUND", "Missing commit.")
            return self.commits[endpoint[8:]]
        if endpoint.startswith("git/blobs/"):
            oid = endpoint[10:]
            raw = self.objects[oid]
            return {
                "sha": oid,
                "encoding": "base64",
                "size": len(raw),
                "content": base64.b64encode(raw).decode(),
            }
        return super().get(endpoint, **kwargs)

    def runner(self, tool, argv, **kwargs):
        payload = json.loads(kwargs["input_text"])["variables"]["input"]
        if payload["expectedHeadOid"] != self.current:
            return subprocess.CompletedProcess(
                argv, 0, 'HTTP/2.0 200 OK\n\n{"errors":[{"type":"STALE_DATA"}]}', ""
            )
        tree = self.trees[self.commits[self.current]["commit"]["tree"]["sha"]]
        files = {item["path"]: item["sha"] for item in tree["tree"]}
        for item in payload["fileChanges"]["additions"]:
            raw = base64.b64decode(item["contents"])
            oid = blob_id(raw)
            self.objects[oid] = raw
            files[item["path"]] = oid
        for item in payload["fileChanges"]["deletions"]:
            del files[item["path"]]
        oid = hashlib.sha1(self.current.encode() + canonical_bytes(files)).hexdigest()
        self._commit(oid, self.current, files)
        self.current = oid
        self.writes += 1
        if self.lost:
            self.lost = False
            raise ControllerError("E_TIMEOUT", "Response lost after remote acceptance.")
        return subprocess.CompletedProcess(
            argv,
            0,
            'HTTP/2.0 200 OK\n\n{"data":{"createCommitOnBranch":{"commit":{"oid":"'
            + oid
            + '"}}}}',
            "",
        )


def test_signed_atomic_remote_history_and_queue_survive_lost_response(tmp_path):
    server = Server(tmp_path)
    journal = Journal(
        GitHubJournalStore(server, server.policy, bot_id=77, writable=True)
    )
    server.lost = True
    receipt = receipt_fixture()
    journal.admit(receipt.request, receipt=receipt)
    assert server.writes == 1
    scan(journal, [{"number": 1}], lambda item: None)
    restarted = Journal(GitHubJournalStore(server, server.policy, bot_id=77))
    assert restarted.get(receipt.request_id).receipt == receipt
    assert cursor_for(restarted).cycle == 1
    assert len(restarted.events()) == 2


@pytest.mark.parametrize(
    "field", ["writer", "signature", "missing-event", "reservation", "root"]
)
def test_remote_journal_rejects_tampering(tmp_path, field):
    server = Server(tmp_path)
    journal = Journal(
        GitHubJournalStore(server, server.policy, bot_id=77, writable=True)
    )
    journal.admit(receipt_fixture().request)
    commit = server.commits[server.current]
    if field == "writer":
        commit["committer"]["id"] = 999
    elif field == "signature":
        commit["commit"]["verification"]["verified"] = False
    elif field == "root":
        commit["parents"][0]["sha"] = "f" * 40
    else:
        rows = server.trees[commit["commit"]["tree"]["sha"]]["tree"]
        prefix = "events/" if field == "missing-event" else "reservations/"
        rows[:] = [row for row in rows if not row["path"].startswith(prefix)]
    with pytest.raises(ControllerError):
        journal.records()


def test_backlog_rechecks_do_not_refetch_immutable_history(tmp_path):
    from journal_store import MemoryStore

    memory = Journal(MemoryStore())
    original = receipt_fixture().request
    for index in range(101):
        memory.admit(
            original.model_copy(
                update={
                    "nonce": f"{index:032x}",
                    "version": f"1.0.{index}",
                    "tag": f"v1.0.{index}",
                }
            )
        )
    server = Server(tmp_path)
    server.policy = server.policy.model_copy(update={"journal_root": "a" * 40})
    server.current = server.policy.journal_root
    server._commit(server.current, None, {})
    files = {}
    for transaction in memory.store.transactions:
        event = json.loads(transaction.event)
        record = load_record(Record, canonical_bytes(event["record"]))
        for path, raw in transaction_files(transaction.event, record).items():
            server.objects[blob_id(raw)] = raw
            files[path] = blob_id(raw)
        server._commit(transaction.commit, transaction.parent, dict(files))
        server.current = transaction.commit
    now, calls = [0.0], []

    def wire(tool, argv, **kwargs):
        resource = argv[-1]
        calls.append(resource)
        now[0] += 0.1
        endpoint = resource.removeprefix("repos/example/generic/")
        if endpoint.startswith("branches/"):
            value = server.branch(endpoint[9:])
        elif endpoint.startswith("git/trees/"):
            value = server._request(resource, None)
        else:
            value = server.get(endpoint)
        return subprocess.CompletedProcess(
            argv, 0, "HTTP/2.0 200 OK\n\n" + json.dumps(value), ""
        )

    api = GitHubReads(
        server.host,
        server.slug,
        cwd=tmp_path,
        runner=wire,
        clock=lambda: now[0],
        deadline=120,
    )
    journal = Journal(GitHubJournalStore(api, server.policy, bot_id=77))
    assert len(journal.records()) == 101
    before = len(calls)
    for _ in range(10):
        assert len(journal.records()) == 101
    assert len(calls) == before + 10
    assert now[0] < 120
