"""Native exporter bytes must pass trusted approval and installed import unchanged."""

import json
import subprocess

import pytest
from profile_transport import snapshot_bytes

from cg_release.events import ControllerError
from cg_release.profile_selection import capacity, deployment_capacity
from cg_release.profile_snapshot import verify_snapshot
from cg_release.snapshot_contract import REQUIRED


@pytest.mark.parametrize("names", [["0"], ["a", "a+b"]])
def test_installed_native_export_passes_python_and_installed_import(
    tmp_path, installed_profile, names
):
    from cg_release.profile_process import resource

    script = resource("docs-snapshots.js")
    root = tmp_path / "source"
    for name in REQUIRED | set(names):
        file = root / "docs" / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(name.encode())
    options = dict(
        root=str(root),
        out=str(tmp_path / "snapshot"),
        kind="release",
        tag="v1.0.0",
        sha="a" * 40,
        runId=12,
        runAttempt=1,
    )
    config = tmp_path / "config.json"
    config.write_text(json.dumps(options), encoding="utf-8")
    envelope = tmp_path / "envelope.json"
    for args in [["build", str(config)], ["export", options["out"], str(envelope)]]:
        result = subprocess.run(
            ["node", str(script), *args], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
    raw = envelope.read_bytes()
    verify_snapshot(raw, tag="v1.0.0", sha="a" * 40, run_id=12, run_attempt=1)
    result = subprocess.run(
        ["node", str(script), "import", str(envelope), str(tmp_path / "restored")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for name in REQUIRED | set(names):
        assert (tmp_path / "restored/site" / name).read_bytes() == name.encode()


def test_approval_rejects_candidate_inclusive_envelope_capacity():
    summary = capacity(snapshot_bytes("v1.0.0", "a" * 40, 12))
    # Count proof uses verified summary shape without allocating half a GiB.
    summary.update(bytes=30 * 1024 * 1024, envelope_bytes=41 * 1024 * 1024)
    items = [(f"v1.0.{n}", summary) for n in range(13)]
    with pytest.raises(ControllerError, match="capacity"):
        deployment_capacity(items, "v1.0.12")


def test_approval_rejects_candidate_version_directory_alias():
    summary = capacity(snapshot_bytes("v1.0.0", "a" * 40, 12))
    with pytest.raises(ControllerError, match="alias|graph"):
        deployment_capacity(
            [(tag, summary) for tag in ["v1.0.0", "v1.1.0-rc.A", "v1.1.0-rc.a"]],
            "v1.0.0",
        )
