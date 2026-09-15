"""Locked native interpreter and approval-bound dependency receipt tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]


def test_clean_locked_native_environment_executes_builder_probe(tmp_path):
    """Use a real empty venv, cached locked distributions and the actual builder."""
    environment = tmp_path / "native environment"
    env = dict(os.environ, UV_PROJECT_ENVIRONMENT=str(environment))
    result = subprocess.run(
        [
            "uv",
            "sync",
            "--project",
            str(PACKAGE),
            "--locked",
            "--offline",
            "--python",
            sys.executable,
            "--no-default-groups",
            "--group",
            "dev",
            "--group",
            "gpid-native",
            "--no-install-project",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    env["CG_RELEASE_NATIVE_PYTHON"] = str(python)
    result = subprocess.run(
        [
            str(python),
            str(PACKAGE.parents[1] / "scripts/release_profile_build.py"),
            "--check-environment",
        ],
        cwd=PACKAGE.parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["packages"]["pyyaml"] == "6.0.2"
    assert "pytest" in data["packages"]
    assert data["gate_owner"] == "gpid-native-profile"
    assert "cg-release" not in data["packages"]
    from cg_release.profile_native import verify_environment

    data.update(schema_version=1, source_sha="a" * 40, run_id=12, run_attempt=1)
    verify_environment(
        json.dumps(data).encode(),
        (PACKAGE / "uv.lock").read_bytes(),
        sha="a" * 40,
        run_id=12,
        run_attempt=1,
        expected_platform=sys.platform,
        python_minor=".".join(data["python"].split(".")[:2]),
    )
    env["CG_RELEASE_NATIVE_PYTHON"] = sys.executable
    denied = subprocess.run(
        [
            str(python),
            str(PACKAGE.parents[1] / "scripts/release_profile_build.py"),
            "--check-environment",
        ],
        cwd=PACKAGE.parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert denied.returncode != 0


@pytest.mark.parametrize(
    "field", ["lock_sha256", "source_sha", "run_id", "packages", "gate_owner"]
)
def test_native_receipt_rejects_substitution(field):
    from cg_release.events import ControllerError
    from cg_release.profile_native import verify_environment

    lock = (PACKAGE / "uv.lock").read_bytes()
    import hashlib

    data = dict(
        schema_version=1,
        source_sha="a" * 40,
        run_id=12,
        run_attempt=1,
        gate_owner="gpid-native-profile",
        lock_sha256=hashlib.sha256(lock).hexdigest(),
        python="3.12.9",
        platform="linux",
        packages={
            row["name"]: row["version"]
            for row in __import__("tomllib").loads(lock.decode())["package"]
            if "registry" in row["source"]
            and row["name"] not in {"colorama", "win32-setctime"}
        },
    )
    verify_environment(
        json.dumps(data).encode(), lock, sha="a" * 40, run_id=12, run_attempt=1
    )
    data[field] = {} if field == "packages" else "substituted"
    with pytest.raises(ControllerError, match="native"):
        verify_environment(
            json.dumps(data).encode(), lock, sha="a" * 40, run_id=12, run_attempt=1
        )


@pytest.mark.parametrize("damage", ["missing", "platform-extra"])
def test_complete_native_closure_is_required(damage):
    import hashlib
    import tomllib

    from cg_release.events import ControllerError
    from cg_release.profile_native import verify_environment

    lock = (PACKAGE / "uv.lock").read_bytes()
    packages = {
        p["name"]: p["version"]
        for p in tomllib.loads(lock.decode())["package"]
        if "registry" in p["source"] and p["name"] not in {"colorama", "win32-setctime"}
    }
    assert len(packages) == 20
    if damage == "missing":
        packages = {k: packages[k] for k in ["pytest", "pyyaml"]}
    else:
        packages["colorama"] = "0.4.6"
    data = dict(
        schema_version=1,
        source_sha="a" * 40,
        run_id=12,
        run_attempt=1,
        gate_owner="gpid-native-profile",
        lock_sha256=hashlib.sha256(lock).hexdigest(),
        python="3.12.9",
        platform="linux",
        packages=packages,
    )
    with pytest.raises(ControllerError):
        verify_environment(
            json.dumps(data).encode(), lock, sha="a" * 40, run_id=12, run_attempt=1
        )
