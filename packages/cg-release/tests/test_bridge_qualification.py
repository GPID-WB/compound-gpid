"""Real authorized qualifier connection with only outer Git/GitHub I/O redirected."""

import base64
import copy
import json
import os
import subprocess
from types import SimpleNamespace

import pytest
from bridge_remote_fixture import BridgeRemote
from test_bridge_client_roundtrip import distribution as distribution

from cg_release.bridge_qualifier import qualify
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.profile_bridge import verify_bridge


@pytest.fixture(scope="module")
def qualification(distribution, tmp_path_factory):
    root, spec = distribution
    scratch = tmp_path_factory.mktemp("real-qualifier-connection")
    transport = BridgeRemote(root, spec)
    native = "windows" if os.name == "nt" else "unix"
    token = "offline-qualification-fixture-not-a-real-token"
    header = (
        "AUTHORIZATION: basic "
        + base64.b64encode(("x-access-token:" + token).encode()).decode()
    )
    clones = []
    env = dict(
        GH_TOKEN=token,
        GITHUB_ACTIONS="true",
        GITHUB_EVENT_NAME="workflow_dispatch",
        GITHUB_REPOSITORY_ID="123",
        GITHUB_REPOSITORY=spec.repository_slug,
        GITHUB_SHA=spec.bridge.revision,
        GITHUB_ACTOR_ID="7",
        GITHUB_RUN_ID="91" if native == "windows" else "92",
        GITHUB_RUN_ATTEMPT="1",
        CG_BRIDGE_PLATFORM=native,
    )
    original = subprocess.run

    def outer(argv, **kwargs):
        child_env = dict(kwargs.get("env", os.environ))
        if argv[:3] == ["git", "clone", "--no-local"]:
            assert argv[3] == "https://github.com/offline/fixture.git"
            assert child_env["GIT_CONFIG_COUNT"] == "3"
            assert child_env["GIT_CONFIG_KEY_1"] == (
                "http.https://github.com/offline/fixture.git.extraheader"
            )
            assert child_env["GIT_CONFIG_VALUE_1"] == header
            assert child_env["GIT_CONFIG_KEY_2"] == "http.followRedirects"
            assert child_env["GIT_CONFIG_VALUE_2"] == "false"
            assert "GH_TOKEN" not in child_env and "GITHUB_TOKEN" not in child_env
            assert token not in str(argv) and header not in str(argv)
            argv = [*argv[:3], str(root), *argv[4:]]
            clones.append(str(root))
        assert not any(
            str(arg).startswith(("https://", "http://", "ssh://", "git://"))
            for arg in argv
        ), "Unexpected remote subprocess in offline qualifier fixture"
        # Updater subprocesses inherit this restriction too. Only the exact
        # expected HTTPS clone above is redirected, never sent to a remote host.
        child_env.update(GIT_ALLOW_PROTOCOL="file")
        child_env.pop("GH_TOKEN", None)
        child_env.pop("GITHUB_TOKEN", None)
        kwargs["env"] = child_env
        return original(argv, **kwargs)

    api = GitHubReads(
        "github.com", spec.repository_slug, cwd=scratch, runner=transport.run
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("GH_TOKEN", token)
        patch.delenv("GITHUB_TOKEN", raising=False)
        patch.setattr(subprocess, "run", outer)
        receipt = qualify(spec, scratch / "private", env, authorized=True, api=api)
    assert clones == [str(root)]
    assert token not in json.dumps(receipt) and header not in json.dumps(receipt)
    bridge = transport.policy(receipt)
    policy = SimpleNamespace(repository_id=123, profile=SimpleNamespace(bridge=bridge))
    return scratch, transport, policy, receipt


def test_exact_real_qualifier_output_reaches_strict_verifier(qualification):
    scratch, transport, policy, receipt = qualification
    api = GitHubReads(
        "github.com", transport.spec.repository_slug, cwd=scratch, runner=transport.run
    )
    verify_bridge(api, policy)
    assert receipt["kind"] == "actual-bridge-clean-consumer-v1"
    assert receipt["stages"]["bridge"]["release"]["tree"] == transport.spec.bridge.tree
    assert receipt["new_pin_rejected_before_bridge"] is True


@pytest.mark.parametrize(
    "bad",
    [
        "arbitrary-fixture",
        "job-id",
        "artifact-run",
        "archive-bytes",
        "expired",
        "draft",
        "rerun",
    ],
)
def test_real_qualifier_evidence_rejects_substitution(qualification, bad):
    scratch, transport, policy, _ = qualification
    transport.bad = bad
    try:
        api = GitHubReads(
            "github.com",
            transport.spec.repository_slug,
            cwd=scratch,
            runner=transport.run,
        )
        with pytest.raises(ControllerError):
            verify_bridge(api, policy)
    finally:
        transport.bad = None


@pytest.mark.parametrize(
    "field", ["kind", "spec_digest", "tree", "managed", "pin", "run_attempt"]
)
def test_hash_valid_qualification_still_requires_exact_output(qualification, field):
    scratch, transport, policy, receipt = qualification
    changed = copy.deepcopy(receipt)
    if field == "tree":
        changed["stages"]["bridge"]["release"]["tree"] = "a" * 40
    elif field == "managed":
        changed["stages"]["bridge"]["managed"][".opencode/AGENTS.md"] = "a" * 64
    elif field == "pin":
        changed["stages"]["successor"]["pin"] = transport.spec.bridge.tag
    else:
        changed[field] = True if field == "run_attempt" else "offline-fixture-only"
    altered = SimpleNamespace(
        repository_id=123, profile=SimpleNamespace(bridge=transport.policy(changed))
    )
    try:
        api = GitHubReads(
            "github.com",
            transport.spec.repository_slug,
            cwd=scratch,
            runner=transport.run,
        )
        with pytest.raises(ControllerError):
            verify_bridge(api, altered)
    finally:
        transport.policy(receipt)
