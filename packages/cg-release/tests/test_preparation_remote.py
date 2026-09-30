"""Preparation writes reconcile exact Git objects and one all-state PR inventory."""

import json
import subprocess
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.models import Request, load_record
from cg_release.preparation import Edit, PreparedTree, object_id
from cg_release.preparation_remote import PreparationRemote, commit_spec


class API:
    host, slug, read_seconds = "github.com", "owner/repo", 20
    cwd = Path.cwd()

    def __init__(self):
        self.objects, self.prs, self.writes = {}, [], []
        self.lose = None

    def remaining(self):
        return 100

    def get(self, endpoint):
        from urllib.parse import unquote

        endpoint = unquote(endpoint)
        if endpoint not in self.objects:
            raise ControllerError("E_NOT_FOUND", "Absent.")
        return self.objects[endpoint]

    def _request(self, resource, page):
        assert "pulls?state=all" in resource
        return self.prs if page == 1 else []

    def runner(self, tool, argv, **kwargs):
        endpoint = argv[-1].split("/", 3)[-1]
        payload = json.loads(kwargs["input_text"])
        self.writes.append(endpoint)
        if endpoint == "git/blobs":
            import base64

            raw = base64.b64decode(payload["content"])
            oid = object_id("blob", raw)
            self.objects[f"git/blobs/{oid}"] = {"sha": oid}
        elif endpoint == "git/trees":
            self.objects["git/trees/" + "b" * 40] = {"sha": "b" * 40}
        elif endpoint == "git/commits":
            self.objects["git/commits/" + self.commit] = {
                "sha": self.commit,
                "tree": {"sha": payload["tree"]},
                "parents": [{"sha": payload["parents"][0]}],
            }
        elif endpoint == "git/refs":
            self.objects["git/ref/" + payload["ref"].removeprefix("refs/")] = {
                "ref": payload["ref"],
                "object": {"type": "commit", "sha": payload["sha"]},
            }
        elif endpoint == "pulls":
            self.prs.append(
                {
                    "number": 42,
                    "id": 99,
                    "state": "open",
                    "merged_at": None,
                    "head": {
                        "ref": payload["head"],
                        "sha": self.commit,
                        "repo": {"id": 123},
                    },
                    "base": {"ref": payload["base"], "repo": {"id": 123}},
                }
            )
        else:
            pytest.fail(endpoint)
        if self.lose == endpoint:
            raise ControllerError("E_TIMEOUT", "Response lost after write.")
        return subprocess.CompletedProcess(argv, 0, "HTTP/2.0 201 Created\n\n{}", "")


@pytest.fixture
def inputs():
    request = load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )
    raw = b'{"version":"1.0.0"}'
    import hashlib

    prepared = PreparedTree(
        "b" * 40,
        ("package.json",),
        (Edit("package.json", "c" * 64, hashlib.sha256(raw).hexdigest(), raw),),
    )
    date = "2026-09-11T00:00:00Z"
    api = API()
    api.commit, _ = commit_spec(request, prepared.tree, date)
    return api, request, prepared, date


@pytest.mark.parametrize(
    "lost", [None, "git/blobs", "git/trees", "git/commits", "git/refs", "pulls"]
)
def test_lost_response_and_repeat_do_not_duplicate_objects_or_pr(inputs, lost):
    api, request, prepared, date = inputs
    api.lose = lost
    remote = PreparationRemote(api)
    first = remote.ensure(request, prepared, "a" * 40, {"package.json": "100644"}, date)
    assert first["number"] == 42
    writes = list(api.writes)
    assert (
        remote.ensure(request, prepared, "a" * 40, {"package.json": "100644"}, date)
        == first
    )
    assert api.writes == writes and len(api.prs) == 1


def test_conflicting_branch_and_duplicate_or_closed_pr_stop(inputs):
    api, request, prepared, date = inputs
    remote = PreparationRemote(api)
    remote.ensure(request, prepared, "a" * 40, {"package.json": "100644"}, date)
    for mutation in ["duplicate", "closed", "head"]:
        import copy

        saved = copy.deepcopy(api.prs)
        if mutation == "duplicate":
            api.prs.append(copy.deepcopy(api.prs[0]))
        elif mutation == "closed":
            api.prs[0]["state"] = "closed"
        else:
            api.prs[0]["head"]["sha"] = "f" * 40
        with pytest.raises(ControllerError):
            remote.ensure(request, prepared, "a" * 40, {"package.json": "100644"}, date)
        api.prs = saved


def test_no_write_without_fresh_check_and_wrong_shape_is_typed(inputs):
    api, request, prepared, date = inputs

    def reject():
        raise ControllerError("E_STALE_PROPOSAL", "Moved.")

    with pytest.raises(ControllerError):
        PreparationRemote(api, fresh=reject).ensure(
            request, prepared, "a" * 40, {"package.json": "100644"}, date
        )
    assert api.writes == []
    api.prs = ["invalid"]
    with pytest.raises(ControllerError):
        PreparationRemote(api).ensure(
            request, prepared, "a" * 40, {"package.json": "100644"}, date
        )


def test_commit_spec_matches_real_git_object_bytes(inputs, tmp_path):
    api, request, prepared, date = inputs
    oid, payload = commit_spec(request, prepared.tree, date)
    from datetime import datetime

    timestamp = int(datetime.fromisoformat(date).timestamp())
    author = payload["author"]
    identity = f"{author['name']} <{author['email']}> {timestamp} +0000"
    raw = (
        f"tree {prepared.tree}\nparent {request.source_sha}\nauthor {identity}\n"
        f"committer {identity}\n\n{payload['message']}"
    )
    result = subprocess.run(
        ["git", "hash-object", "-t", "commit", "--stdin"],
        cwd=tmp_path,
        input=raw.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    assert result.stdout.decode("ascii").strip() == oid == api.commit
