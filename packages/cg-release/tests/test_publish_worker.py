"""Trusted publication worker rejects ambient callers and isolates credential roles."""

import subprocess

import pytest

from cg_release import publish_worker
from cg_release.events import ControllerError
from cg_release.publication_credentials import role_runner


def test_worker_outside_actions_does_not_resolve_remote(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setattr(
        publish_worker, "context_for", lambda *a, **k: pytest.fail("remote access")
    )
    assert (
        publish_worker.main(["seal", "--request-id", "invalid", "--nonce", "a" * 32])
        == 2
    )
    assert "E_CONTROLLER_TRUST" in capsys.readouterr().out


def test_rerun_rejected_before_credential_use(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    monkeypatch.setattr(
        publish_worker, "context_for", lambda *a, **k: pytest.fail("credential use")
    )
    assert (
        publish_worker.main(["publish", "--request-id", "invalid", "--nonce", "a" * 32])
        == 2
    )
    assert "E_CONTROLLER_TRUST" in capsys.readouterr().out


def test_role_runner_passes_only_selected_token(monkeypatch, tmp_path):
    monkeypatch.setenv("CG_RELEASE_CONTROL_TOKEN", "control-fixture")
    monkeypatch.setenv("CG_RELEASE_PUBLISHING_TOKEN", "publishing-fixture")
    monkeypatch.setenv("GH_TOKEN", "ambient-fixture")
    monkeypatch.setenv("RELEASE_SIGNING_PRIVATE_KEY", "key-fixture")
    calls = []

    def runner(tool, args, **kwargs):
        calls.append(kwargs["environment"])
        return subprocess.CompletedProcess(args, 0, "", "")

    for role, expected in [
        ("control", "control-fixture"),
        ("publishing", "publishing-fixture"),
    ]:
        call = role_runner(role, runner=runner)
        call(
            "gh",
            ["api", "--method", "GET", "repos/a/b"],
            cwd=tmp_path,
            environment={"PATH": "test-path"},
        )
        assert calls[-1]["GH_TOKEN"] == expected
        assert not any(
            key in calls[-1]
            for key in [
                "CG_RELEASE_CONTROL_TOKEN",
                "CG_RELEASE_PUBLISHING_TOKEN",
                "RELEASE_SIGNING_PRIVATE_KEY",
            ]
        )


@pytest.mark.parametrize(
    "role,args",
    [
        ("publishing", ["api", "--method", "POST", "graphql"]),
        ("control", ["api", "--method", "POST", "repos/a/b/releases"]),
        ("control", ["push", "https://github.com/a/b.git", "a:refs/tags/v1"]),
    ],
)
def test_cross_role_writes_are_denied_locally(monkeypatch, tmp_path, role, args):
    monkeypatch.setenv("CG_RELEASE_CONTROL_TOKEN", "control-fixture")
    monkeypatch.setenv("CG_RELEASE_PUBLISHING_TOKEN", "publishing-fixture")
    call = role_runner(role, runner=lambda *a, **k: pytest.fail("cross-role write"))
    with pytest.raises(ControllerError):
        call("git" if args[0] == "push" else "gh", args, cwd=tmp_path)
