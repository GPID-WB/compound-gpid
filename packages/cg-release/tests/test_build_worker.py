"""Unprivileged build execution uses isolated installed code and exact source HEAD."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from cg_release.build_worker import execute_build
from cg_release.events import ControllerError


def test_build_runs_declared_argv_and_stages_only_declared_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "--quiet", "--template="], cwd=source, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "source",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    spec = json.loads((Path(__file__).parent / "fixtures/policy.json").read_text())[
        "build"
    ]
    (source / "dist").mkdir()
    (source / "dist/package.whl").write_bytes(b"wheel")
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0)

    execute_build(spec, sha, source=source, output=tmp_path / "staged", runner=runner)
    assert calls == [spec["argv"]]
    assert (tmp_path / "staged/dist/package.whl").read_bytes() == b"wheel"
    with pytest.raises(ControllerError):
        execute_build(
            spec, "0" * 40, source=source, output=tmp_path / "wrong", runner=runner
        )
    assert len(calls) == 1
    spec["argv"] = [
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "Path('dist/package.whl').write_bytes(b'command-built-wheel')",
    ]
    execute_build(spec, sha, source=source, output=tmp_path / "real-staged")
    assert (
        tmp_path / "real-staged/dist/package.whl"
    ).read_bytes() == b"command-built-wheel"
