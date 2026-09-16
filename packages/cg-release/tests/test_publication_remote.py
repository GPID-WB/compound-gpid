"""GitHub CLI wire contracts, absence classification and role-specific operations."""

import json
import os
import subprocess

import pytest

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.process import run_process
from cg_release.publication_remote import GitHubPublicationRemote, ReadOnlyPublication
from cg_release.signing import create_tag


@pytest.mark.parametrize("operation", ["push_tag", "create_draft", "upload", "publish"])
def test_published_recovery_adapter_has_no_write_capability(operation):
    remote = ReadOnlyPublication(None)
    with pytest.raises(ControllerError, match="Published recovery"):
        getattr(remote, operation)()


def test_draft_and_publish_are_explicit_not_default_latest(tmp_path):
    calls = []

    def runner(tool, args, **kwargs):
        calls.append((tool, args, kwargs))
        return subprocess.CompletedProcess(args, 0, "HTTP/2.0 201 Created\n\n{}", "")

    remote = GitHubPublicationRemote(
        GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=runner)
    )
    remote.create_draft("v1.5.0-rc.10", "a" * 40, "notes", True)
    remote.publish(71, False)
    draft = json.loads(calls[0][2]["input_text"])
    final = json.loads(calls[1][2]["input_text"])
    assert (
        draft["draft"] is True
        and draft["make_latest"] == "false"
        and draft["prerelease"] is True
    )
    assert final == {"draft": False, "make_latest": "false"}
    assert calls[1][1][2] == "PATCH"
    assert not any("--clobber" in args or "DELETE" in args for _, args, _ in calls)


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "E_AUTH"),
        (403, "E_FORBIDDEN"),
        (404, "E_NOT_FOUND"),
        (500, "E_WRITE_UNKNOWN"),
    ],
)
def test_write_http_errors_remain_typed_without_body_leak(tmp_path, status, code):
    def runner(tool, args, **kwargs):
        return subprocess.CompletedProcess(
            args, 1, f"HTTP/2.0 {status} Error\n\nopaque-private-body", ""
        )

    remote = GitHubPublicationRemote(
        GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=runner)
    )
    with pytest.raises(ControllerError) as caught:
        remote.publish(71, False)
    assert caught.value.code == code and "opaque" not in caught.value.message


def test_missing_release_requires_complete_inventory_not_403(tmp_path):
    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path)
    api.pages = lambda endpoint: []
    remote = GitHubPublicationRemote(api)
    assert remote.observe_release("v1.5.0") is None

    def denied(endpoint):
        raise ControllerError("E_FORBIDDEN", "denied")

    api.pages = denied
    with pytest.raises(ControllerError, match="denied"):
        remote.observe_release("v1.5.0")


def test_asset_upload_uses_only_verified_repository_and_no_url_input(tmp_path):
    calls = []

    def runner(tool, args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "HTTP/2.0 201 Created\n\n{}", "")

    remote = GitHubPublicationRemote(
        GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=runner)
    )
    remote.upload(
        71, {"name": "package.whl", "media_type": "application/zip"}, b"bytes"
    )
    assert calls[0][:2] == ["api", "--method"]
    assert "--clobber" not in calls[0]
    assert any(
        "repos/owner/repo/releases/71/assets?name=package.whl" in arg
        for arg in calls[0]
    )


def test_exact_nonforce_push_uses_real_temporary_bare_git(tmp_path):
    bare = tmp_path / "remote.git"
    subprocess.run(
        ["git", "init", "--bare", str(bare)], check=True, capture_output=True
    )
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    }
    tree = (
        subprocess.run(
            ["git", "mktree"], cwd=bare, input=b"", check=True, capture_output=True
        )
        .stdout.decode()
        .strip()
    )
    sha = (
        subprocess.run(
            ["git", "commit-tree", tree, "-m", "fixture"],
            cwd=bare,
            env=env,
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
    subprocess.run(
        ["git", "update-ref", "refs/heads/main", sha],
        cwd=bare,
        check=True,
        capture_output=True,
    )
    calls = []

    def runner(tool, args, **kwargs):
        calls.append(args)
        assert tool == "git"
        # Replace only transport location in this test. All production ref/object
        # argv, real Git pack transfer and non-force rejection remain exercised.
        args = [
            str(bare) if a == "https://github.com/owner/repo.git" else a for a in args
        ]
        args = ["-c", "protocol.file.allow=always", *args]
        return run_process(tool, args, **kwargs)

    remote = GitHubPublicationRemote(
        GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=runner)
    )
    tag = create_tag("v1.5.0", sha, "Fixture", "fixture@example.invalid", 1720000000)
    remote.push_tag("v1.5.0", tag, sha)
    actual = (
        subprocess.run(
            ["git", "rev-parse", "refs/tags/v1.5.0"],
            cwd=bare,
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
    assert actual == tag["oid"]
    changed = create_tag(
        "v1.5.0", sha, "Fixture", "fixture@example.invalid", 1720000001
    )
    with pytest.raises(ControllerError):
        remote.push_tag("v1.5.0", changed, sha)
    assert all("--force" not in args for args in calls)
    assert [
        a for args in calls if "push" in args for a in args if ":refs/tags/" in a
    ] == [tag["oid"] + ":refs/tags/v1.5.0", changed["oid"] + ":refs/tags/v1.5.0"]
