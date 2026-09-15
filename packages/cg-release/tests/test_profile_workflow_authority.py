"""Replay the final workflow command order with real authorization and outer GETs.

This is a bounded connected boundary test, not execution of Bash or a Pages action.
The registered composition is seeded as in the existing deployment-gate fixture.
"""

import hashlib
import json
import re
import shlex
import socket
import subprocess
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from test_profile_security import worker as worker

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.profile_deploy import authorize_deployment
from cg_release.profile_worker import register

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def forbid_external_io(monkeypatch):
    """These memory-provider boundary cases must not start processes or sockets."""

    def denied(*args, **kwargs):
        pytest.fail("External process/network I/O is forbidden in this boundary test")

    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


@pytest.mark.parametrize(
    "source",
    [
        "packages/cg-release/templates/gpid-docs.yml",
        ".github/workflows/release-controller-docs.yml",
    ],
)
@pytest.mark.parametrize(
    "actor, delayed_read",
    [
        (None, None),
        (456, "branches/dev"),
        (456, "releases/latest"),
        (8, "branches/dev"),
        (8, "releases/latest"),
        (456, "repos/owner/repo"),
        (456, "branches/production"),
        (8, "repos/owner/repo"),
        (8, "branches/production"),
    ],
)
def test_workflow_freshness_reads_cannot_outlast_final_human_authority(
    worker, tmp_path, source, actor, delayed_read
):
    context, record, sealed, state, env = worker
    steps = yaml.safe_load((ROOT / source).read_text())["jobs"]["deploy"]["steps"]
    assert steps[-2]["id"] == "authorized"
    assert steps[-1]["uses"].startswith("actions/deploy-pages@")
    assert steps[-2].get("continue-on-error", False) is False
    assert steps[-1].get("if", "success()") == "success()"
    lines = [
        line.strip()
        for line in steps[-2]["run"].splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    manifest = tmp_path / "deployment.json"
    manifest.write_bytes(b'{"files":{}}\n')
    env.update(
        EXPECTED_MANIFEST=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        DEV_SHA="d" * 40,
        STABLE_TAG="v1.0.0",
    )
    register(context, record, sealed["nonce"], env)
    store = CompositionJournal(context.journal)
    result = dict(
        run_id=55,
        request_digest=digest(sealed),
        manifest_sha256=env["EXPECTED_MANIFEST"],
    )
    store.save(store.records()[-1], "composition", result)
    before, trace = context.journal.events(), []
    original = context.api.runner
    reads, revoked_at = [], None
    saw_run = False

    def delayed(executable, argv, **kwargs):
        nonlocal saw_run, revoked_at
        assert executable == "gh" and argv[:3] == ["api", "--method", "GET"]
        endpoint = argv[-1].removeprefix("repos/owner/repo/")
        reads.append(endpoint)
        if endpoint not in {"branches/dev", "releases/latest"}:
            response = original(executable, argv, **kwargs)
            if endpoint == "actions/runs/55":
                saw_run = True
            if saw_run and endpoint == delayed_read and revoked_at is None:
                state["roles"][actor] = "read"
                revoked_at = len(reads) - 1
            return response
        if endpoint == delayed_read:
            state["roles"][actor] = "read"
            revoked_at = len(reads) - 1
        value = (
            {"commit": {"sha": env["DEV_SHA"]}}
            if endpoint == "branches/dev"
            else {"tag_name": env["STABLE_TAG"]}
        )
        trace.append(endpoint)
        return SimpleNamespace(
            returncode=0, stdout="HTTP/2.0 200 OK\n\n" + json.dumps(value)
        )

    context.api.runner = delayed
    with pytest.raises(ControllerError, match="authority") if actor else nullcontext():
        for line in lines:
            if line == "set -euo pipefail":
                continue
            if "cg_release.profile_worker authorize-deploy" in line:
                assert shlex.split(line) == [
                    "packages/cg-release/.venv/bin/python",
                    "-I",
                    "-m",
                    "cg_release.profile_worker",
                    "authorize-deploy",
                    "--request-id",
                    "$REQUEST_ID",
                    "--nonce",
                    "$NONCE",
                ]
                trace.append("authorize-deploy")
                assert (
                    authorize_deployment(context, record, sealed["nonce"], env)
                    == result
                )
            elif line.startswith('test "$(sha256sum '):
                assert (
                    line == 'test "$(sha256sum composition/.docs-deployment.json '
                    '| cut -d\' \' -f1)" = "$EXPECTED_MANIFEST"'
                )
                assert (
                    hashlib.sha256(manifest.read_bytes()).hexdigest()
                    == env["EXPECTED_MANIFEST"]
                )
                trace.append("manifest")
            else:
                command = re.fullmatch(
                    r'test "\$\(gh api "repos/\$GITHUB_REPOSITORY/'
                    r'(branches/dev|releases/latest)" --jq (\.commit\.sha|\.tag_name)'
                    r'\)" = "\$(DEV_SHA|STABLE_TAG)"',
                    line,
                )
                assert command, "Unknown workflow statement requires a boundary test"
                endpoint, query, expected = command.groups()
                value = context.api.get(endpoint)
                if endpoint == "branches/dev":
                    assert (query, expected) == (".commit.sha", "DEV_SHA")
                    assert value["commit"]["sha"] == env[expected]
                else:
                    assert (query, expected) == (".tag_name", "STABLE_TAG")
                    assert value["tag_name"] == env[expected]
    assert context.journal.events() == before
    assert trace[-1] == "authorize-deploy"
    assert sorted(trace[:-1]) == ["branches/dev", "manifest", "releases/latest"]
    if actor:
        assert revoked_at is not None
        assert state["roles"][actor] == "read"
        assert any(
            endpoint.endswith("/permission") for endpoint in reads[revoked_at + 1 :]
        )
    else:
        assert reads[-1].endswith("/permission")
