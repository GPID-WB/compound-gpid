"""Isolated wheel fixture for real installed profile resources, never global install."""

import importlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def profile_wheel(tmp_path_factory):
    """Build current canonical resources once and unpack only into pytest scratch."""
    root = tmp_path_factory.mktemp("profile-wheel")
    package = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(root),
            str(package),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    wheel = next(root.glob("*.whl"))
    installed = root / "installed"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(installed)
    return installed


@pytest.fixture
def installed_profile(profile_wheel, monkeypatch):
    """Use the real wheel RECORD and bundled code without changing any installation."""
    monkeypatch.syspath_prepend(str(profile_wheel))
    monkeypatch.delitem(sys.modules, "_cg_release_gpid", raising=False)
    importlib.invalidate_caches()
    yield profile_wheel
    sys.modules.pop("_cg_release_gpid", None)
