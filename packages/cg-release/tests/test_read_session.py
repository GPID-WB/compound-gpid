"""Cache only immutable Git objects within one bounded command session."""

import json
import subprocess

import pytest

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.jsonio import decode_json
from cg_release.read_session import ReadCache, ReadSession


def test_repeated_git_objects_are_cached_but_mutable_authority_is_fresh(tmp_path):
    calls = []

    def runner(tool, argv, **kwargs):
        calls.append(argv[-1])
        return subprocess.CompletedProcess(
            argv, 0, "HTTP/2.0 200 OK\n\n" + json.dumps({"value": len(calls)}), ""
        )

    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=runner)
    first = api.get("git/blobs/" + "a" * 40)
    first["value"] = 999
    assert api.get("git/blobs/" + "a" * 40) == {"value": 1}
    for endpoint in (
        "branches/main",
        "collaborators/member/permission",
        "rulesets",
        "actions/runs/1",
    ):
        assert api.get(endpoint) != api.get(endpoint)
    assert len(calls) == 9


def test_cache_never_extends_deadline(tmp_path):
    now = [0.0]
    api = GitHubReads(
        "github.com",
        "owner/repo",
        cwd=tmp_path,
        clock=lambda: now[0],
        deadline=10,
        runner=lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, "HTTP/2.0 200 OK\n\n{}", ""
        ),
    )
    api.get("git/blobs/" + "a" * 40)
    now[0] = 11
    with pytest.raises(ControllerError) as caught:
        api.get("git/blobs/" + "a" * 40)
    assert caught.value.code == "E_DEADLINE"


def test_session_is_local_and_repository_scoped(tmp_path):
    session = ReadSession()
    first = session("github.com", "owner/repo", cwd=tmp_path, deadline=10)
    assert session("github.com", "owner/repo", cwd=tmp_path, deadline=20) is first
    assert first.deadline == 20
    assert session("github.com", "Owner/Repo", cwd=tmp_path, deadline=20) is first
    assert session("github.com", "other/repo", cwd=tmp_path, deadline=20) is not first
    assert ReadSession()("github.com", "owner/repo", cwd=tmp_path) is not first


def test_cache_has_explicit_byte_and_entry_bounds():
    cache = ReadCache(max_bytes=32, max_entries=2)
    for index in range(10):
        resource = "repos/owner/repo/git/blobs/" + f"{index:040x}"
        cache.read(resource, None, None, lambda: 10, lambda: {"value": index})
    assert cache.byte_count <= 32 and len(cache.values) <= 2


def test_overflowed_json_float_is_not_a_cache_serialization_exception():
    with pytest.raises(ControllerError):
        decode_json('{"elapsed":1e309}')
