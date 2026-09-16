"""Real installed helper/process boundary with hostile argv and environment."""

import json

import pytest
from test_profile_adapter_reads import envelope

from cg_release.events import ControllerError


def test_installed_snapshot_helper_runs_without_node_preload(
    tmp_path, monkeypatch, installed_profile
):
    from cg_release.profile_process import run_snapshot

    source = tmp_path / "input.json"
    source.write_bytes(envelope(size=700000))
    monkeypatch.setenv("NODE_OPTIONS", "--require=never-execute-target-code.js")
    run_snapshot("import", [str(source), str(tmp_path / "site")], cwd=tmp_path)
    record = json.loads((tmp_path / "site/.docs-snapshot.json").read_text())
    assert record["tag"] == "v1.0.0"
    assert (tmp_path / "site/site/index.html").read_bytes() == b"x" * 700000


@pytest.mark.parametrize(
    "operation,args,timeout",
    [
        ("eval", ["malicious.js"], 20),
        ("import", ["../outside", "out"], 20),
        ("import", ["--require=evil", "out"], 20),
        ("import", ["input", "out"], 0),
        ("import", ["input", "out"], 121),
    ],
)
def test_process_rejects_unsafe_contract_before_spawn(
    tmp_path, operation, args, timeout
):
    from cg_release.profile_process import run_snapshot

    with pytest.raises(ControllerError):
        run_snapshot(operation, args, cwd=tmp_path, timeout=timeout)
    assert not (tmp_path / "out").exists()


def test_actual_installed_helper_obeys_deadline(tmp_path, installed_profile):
    from cg_release.profile_process import run_snapshot

    source = tmp_path / "input.json"
    source.write_bytes(envelope())
    with pytest.raises(ControllerError, match="deadline"):
        run_snapshot(
            "import",
            [str(source), str(tmp_path / "out")],
            cwd=tmp_path,
            timeout=0.000001,
        )
