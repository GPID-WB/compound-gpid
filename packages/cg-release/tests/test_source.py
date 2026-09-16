"""Immutable source acquisition with strict GitHub wire-shape fixtures."""

import base64
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from cg_release import source
from cg_release.cli import parse_args
from cg_release.events import ControllerError

POLICY_DATA = json.loads((Path(__file__).parent / "fixtures/policy.json").read_bytes())
POLICY_DATA["release_lines"][0]["branches"].append("feature")
POLICY = json.dumps(POLICY_DATA).encode()


class Remote:
    """Fake only the read API; it has no mutation method or source-policy authority."""

    host, slug = "github.com", "owner/repo"
    deadline, read_seconds, read_attempts = 120, 20, 3

    def __init__(self) -> None:
        self.calls = []
        self.policy = POLICY
        self.repo = {
            "id": 123,
            "full_name": "owner/repo",
            "default_branch": "main",
            "fork": False,
        }
        self.branches = {
            "main": {"name": "main", "protected": True, "commit": {"sha": "a" * 40}},
            "feature": {
                "name": "feature",
                "protected": False,
                "commit": {"sha": "b" * 40},
            },
        }
        self.mode = "100644"

    def remaining(self) -> float:
        return 100

    def actor(self) -> dict:
        return {"id": 7, "login": "maintainer"}

    def branch(self, name: str) -> dict:
        if name not in self.branches:
            raise ControllerError("E_NOT_FOUND", "Branch not found.")
        return self.branches[name]

    def pages(self, endpoint: str) -> list:
        assert endpoint == "releases"
        return []

    def refs(self) -> list:
        return []

    def _request(self, path: str, page: int) -> list:
        assert "commits?sha=" in path and page == 1
        return [{"sha": path.split("sha=")[1], "commit": {"message": "Initial source"}}]

    def get(self, endpoint: str, **_kwargs: object) -> object:
        self.calls.append(endpoint)
        blobs = {
            ".release-controller.json": self.policy,
            "package.json": b'{"version":"0.9.0"}',
            "CHANGELOG.md": b"<!-- release -->\n",
        }
        hashed = {
            hashlib.sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest(): raw
            for raw in blobs.values()
        }
        if endpoint == "":
            return self.repo
        if endpoint == "collaborators/maintainer/permission":
            return {"permission": "write", "role_name": "write", "user": {"id": 7}}
        if endpoint.startswith("git/commits/"):
            return {
                "sha": endpoint.rsplit("/", 1)[1],
                "tree": {"sha": "c" * 40},
                "message": "Initial source",
            }
        if endpoint.startswith("git/trees/"):
            return {
                "sha": "c" * 40,
                "truncated": False,
                "tree": [
                    {
                        "path": p,
                        "mode": self.mode,
                        "type": "blob",
                        "sha": hashlib.sha1(
                            b"blob " + str(len(raw)).encode() + b"\0" + raw
                        ).hexdigest(),
                    }
                    for p, raw in blobs.items()
                ],
            }
        if endpoint.startswith("git/blobs/"):
            sha = endpoint.rsplit("/", 1)[1]
            return {
                "sha": sha,
                "encoding": "base64",
                "size": len(hashed[sha]),
                "content": base64.b64encode(hashed[sha]).decode(),
            }
        pytest.fail("Unexpected endpoint: " + endpoint)


def acquire(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, remote: Remote, args: list[str]
):
    """Inject local discovery and remote reads, never discover a real origin."""
    calls = []

    def git(
        tool: str, argv: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess:
        calls.append(argv)
        assert tool == "git" and argv in [
            ["remote", "get-url", "origin"],
            ["symbolic-ref", "--quiet", "--short", "HEAD"],
        ]
        return subprocess.CompletedProcess(
            [],
            0,
            "https://github.com/owner/repo.git\n" if argv[0] == "remote" else "main\n",
            "",
        )

    monkeypatch.setattr(source, "run_process", git)
    result = source.acquire_snapshot(
        parse_args(args), cwd=tmp_path, api_factory=lambda *_a, **_k: remote
    )
    assert len(calls) <= 2
    return result


def test_source_policy_comes_only_from_default_commit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    remote = Remote()
    result = acquire(
        monkeypatch,
        tmp_path,
        remote,
        ["plan", "--version", "1.0.0", "--branch", "feature"],
    )
    assert result.source_sha == "b" * 40 and result.policy_sha == "a" * 40
    assert result.policy_raw == POLICY
    assert remote.calls.index("git/commits/" + "a" * 40) < remote.calls.index(
        "git/commits/" + "b" * 40
    )


def test_snapshot_uses_verified_canonical_repository_spelling(monkeypatch, tmp_path):
    remote = Remote()
    remote.repo["full_name"] = "Owner/Repo"
    result = acquire(monkeypatch, tmp_path, remote, ["plan", "--version", "1.0.0"])
    assert result.slug == "Owner/Repo"


@pytest.mark.parametrize(
    "mutation", ["fork", "identity", "unprotected", "symlink", "unknown-policy"]
)
def test_invalid_remote_authority_or_blob_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation: str
) -> None:
    remote = Remote()
    if mutation == "fork":
        remote.repo["fork"] = True
    elif mutation == "identity":
        remote.repo["id"] = 999
    elif mutation == "unprotected":
        remote.branches["main"]["protected"] = False
    elif mutation == "symlink":
        remote.mode = "120000"
    else:
        data = json.loads(POLICY)
        data["unexpected"] = True
        remote.policy = json.dumps(data).encode()
    with pytest.raises(ControllerError):
        acquire(monkeypatch, tmp_path, remote, ["plan", "--version", "1.0.0"])


def test_detached_head_requires_branch_before_remote_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    remote = Remote()

    def git(_tool: str, argv: list[str], **_kwargs: object):
        return subprocess.CompletedProcess(
            [],
            0 if argv[0] == "remote" else 1,
            "https://github.com/owner/repo.git" if argv[0] == "remote" else "",
            "",
        )

    monkeypatch.setattr(source, "run_process", git)
    with pytest.raises(ControllerError) as error:
        source.acquire_snapshot(
            parse_args(["plan", "--version", "1.0.0"]),
            cwd=tmp_path,
            api_factory=lambda *_a, **_k: remote,
        )
    assert error.value.code == "E_DETACHED" and remote.calls == []


def test_missing_branch_is_not_local_branch_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ControllerError) as error:
        acquire(
            monkeypatch,
            tmp_path,
            Remote(),
            ["plan", "--version", "1.0.0", "--branch", "absent"],
        )
    assert error.value.code == "E_NOT_FOUND"


def test_existing_state_requires_journal_reader_not_empty_reservations(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    remote = Remote()
    remote.branches["release-controller-state"] = {
        "name": "release-controller-state",
        "protected": True,
        "commit": {"sha": "e" * 40},
    }

    def unavailable(*args):
        raise ControllerError("E_JOURNAL", "Journal verification unavailable.")

    monkeypatch.setattr(source, "read_reservations", unavailable)
    with pytest.raises(ControllerError) as error:
        acquire(monkeypatch, tmp_path, remote, ["plan", "--version", "1.0.0"])
    assert error.value.code == "E_JOURNAL"


def test_dirty_worktree_files_are_neither_read_nor_changed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dirty = tmp_path / "package.json"
    dirty.write_bytes(b"uncommitted hostile data")
    result = acquire(monkeypatch, tmp_path, Remote(), ["plan", "--version", "1.0.0"])
    assert dirty.read_bytes() == b"uncommitted hostile data"
    assert result.blobs["package.json"].content == b'{"version":"0.9.0"}'
