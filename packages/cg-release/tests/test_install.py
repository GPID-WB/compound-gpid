"""Real wheel/sdist build and isolated installed CLI checks outside the source tree."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet

PACKAGE = Path(__file__).resolve().parents[1]


def test_default_locked_package_gate_collects_without_optional_groups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Collect the real full-package gate without the outer environment's groups."""
    root = PACKAGE.parents[1]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    import cg_pr_preflight as preflight

    command = list(preflight.FULL_PACKAGE_TEST_COMMAND)
    command.insert(2, "--isolated")
    command.extend(["--collect-only", "--tb=short", "-p", "no:cacheprovider"])
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTHON") and key != "VIRTUAL_ENV"
    }
    env["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True,
        timeout=180, check=False,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]
    assert "test_profile_workflow_authority.py::" in result.stdout
    assert "tests collected" in result.stdout


def checked(argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run build/install tooling with a bounded diagnostic on failure."""
    result = subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, timeout=180, check=False
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
    return result


@pytest.fixture(scope="module")
def installed(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Build both distributions and install the wheel with locked dependencies."""
    directory = tmp_path_factory.mktemp("generic-release-wheel")
    assert not directory.is_relative_to(PACKAGE)
    dist = directory / "dist"
    checked(
        [
            "uv",
            "build",
            "--project",
            str(PACKAGE),
            "--python",
            sys.executable,
            "--no-build-isolation",
            "--out-dir",
            str(dist),
        ],
        directory,
    )
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    assert len(list(dist.glob("*.tar.gz"))) == 1
    environment = directory / "installed"
    checked(["uv", "venv", "--python", sys.executable, str(environment)], directory)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirements = directory / "requirements.txt"
    checked(
        [
            "uv",
            "export",
            "--project",
            str(PACKAGE),
            "--locked",
            "--no-dev",
            "--no-emit-project",
            "--output-file",
            str(requirements),
        ],
        directory,
    )
    checked(
        [
            "uv",
            "pip",
            "install",
            "--link-mode",
            "copy",
            "--python",
            str(python),
            "--require-hashes",
            "-r",
            str(requirements),
        ],
        directory,
    )
    checked(
        [
            "uv",
            "pip",
            "install",
            "--link-mode",
            "copy",
            "--python",
            str(python),
            "--no-deps",
            str(wheels[0]),
        ],
        directory,
    )
    return python, directory


@pytest.mark.parametrize("command", ["plan", "start", "status", "resume"])
def test_installed_console_has_four_commands(
    installed: tuple[Path, Path], command: str
) -> None:
    python, directory = installed
    executable = python.with_name("cg-release.exe" if os.name == "nt" else "cg-release")
    result = checked([str(executable), command, "--help"], directory)
    assert command in result.stdout
    assert not (directory / ".github").exists()
    assert not (directory / "compound-gpid.md").exists()


def test_installed_package_has_no_repo_import_or_old_runtime_requirement(
    installed: tuple[Path, Path],
) -> None:
    python, directory = installed
    code = (
        "import importlib.metadata,importlib.util,json,pathlib,sys,cg_release; "
        "d=importlib.metadata.distribution('cg-release'); "
        "sys.stdout.write(json.dumps({'file':cg_release.__file__,"
        "'python':d.metadata['Requires-Python'],"
        "'yaml_available':importlib.util.find_spec('yaml') is not None,"
        "'typed':pathlib.Path(cg_release.__file__).with_name('py.typed').exists()}))"
    )
    metadata = json.loads(checked([str(python), "-I", "-c", code], directory).stdout)
    assert Path(metadata["file"]).is_relative_to(directory / "installed")
    assert metadata["typed"]
    assert not metadata["yaml_available"]
    assert "3.10" not in SpecifierSet(metadata["python"])
    assert "3.11" in SpecifierSet(metadata["python"])
    assert "3.12" in SpecifierSet(metadata["python"])


def test_installed_cli_does_not_claim_submission(installed: tuple[Path, Path]) -> None:
    python, directory = installed
    result = subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "cg_release.cli",
            "start",
            "--version",
            "1.0.0",
            "--yes",
            "--json",
        ],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 2
    # Phase 2 now reads origin. A generic non-checkout must fail locally before gh.
    assert json.loads(result.stdout)["code"] == "E_PROCESS"
    assert "queued" not in result.stdout
    assert "Traceback" not in result.stderr


def test_source_free_installed_profile_uses_verified_node_resources(installed):
    """The actual sdist-built wheel works with only installed dependencies and data."""
    python, directory = installed
    script = directory / "profile-check.py"
    script.write_text(
        """import base64, hashlib, json, pathlib, sys
from types import SimpleNamespace
from cg_release.hooks import selected_profile
from cg_release.profile_process import run_snapshot
assert selected_profile(SimpleNamespace(gpid_profile=None)) is None
assert "_cg_release_gpid" not in sys.modules
profile = selected_profile(SimpleNamespace(gpid_profile="v1"))
for name in ["docs-snapshots.js", "snapshot-data.js", "release-version.js"]:
    assert profile.resource(name).is_relative_to(pathlib.Path(sys.prefix))
files = dict.fromkeys(["index.html", "navigation.json", "assets/site.css",
                      "assets/site.js", ".nojekyll"], b"static")
record = dict(schemaVersion=2, kind="release", tag="v1.0.0", sha="a"*40,
              runId=12, runAttempt=1,
              files={p:hashlib.sha256(b).hexdigest() for p,b in sorted(files.items())})
encoded = json.dumps(record,separators=(",",":")).encode()
record["snapshotDigest"] = hashlib.sha256(encoded).hexdigest()
envelope = dict(record=record,
                files={p:base64.b64encode(b).decode() for p,b in files.items()})
root = pathlib.Path.cwd()
source = root / "snapshot.json"
source.write_text(json.dumps(envelope),encoding="utf-8")
run_snapshot("import", [str(source), str(root / "snapshot")], cwd=root)
assert (root / "snapshot/site/index.html").read_bytes() == b"static"
sys.stdout.write("installed-profile-ok\\n")
""",
        encoding="utf-8",
    )
    result = checked([str(python), "-I", str(script)], directory)
    assert result.stdout.strip() == "installed-profile-ok"


def test_ci_has_six_explicit_cells_and_fail_closed_aggregate() -> None:
    """Ordinary and registered release CI retain the complete matrix and strict gate."""
    workflow = (
        PACKAGE.parents[1] / ".github/workflows/release-controller-ci.yml"
    ).read_text()
    assert "pull_request:" in workflow and "merge_group:" in workflow
    assert "paths:" not in workflow and "paths-ignore:" not in workflow
    assert "python: ['3.11', '3.12']" in workflow
    assert "os: [ubuntu-24.04, windows-latest, macos-latest]" in workflow
    assert "fail-fast: false" in workflow
    assert "python-version: ${{ matrix.python }}" in workflow
    assert '--python "${{ matrix.python }}" --locked' in workflow
    assert "persist-credentials: false" in workflow
    assert "needs: [register, build, package, ruff]" in workflow
    assert "if: ${{ always() }}" in workflow
    assert "name: release-controller-ci" in workflow
    assert "cg_release.build_worker register" in workflow
    assert "environment: release-control" in workflow
    assert "needs.register.outputs.source_sha" in workflow
    assert "workflow_dispatch:" in workflow
    assert "build_request:" in workflow and "dispatch_nonce:" in workflow


@pytest.mark.parametrize(
    "package,ruff,expected",
    [
        ("success", "success", 0),
        ("skipped", "success", 1),
        ("success", "cancelled", 1),
        ("", "success", 1),
        ("failure", "success", 1),
    ],
)
def test_ci_aggregate_executes_and_rejects_missing_results(
    package: str,
    ruff: str,
    expected: int,
) -> None:
    """Execute the workflow's Python gate rather than infer its result from prose."""
    import ast

    workflow = (
        PACKAGE.parents[1] / ".github/workflows/release-controller-ci.yml"
    ).read_text()
    gate = next(
        line.strip()[len("run: python -c ") :]
        for line in workflow.splitlines()
        if "run: python -c " in line
    )
    result = subprocess.run(
        [sys.executable, "-c", ast.literal_eval(gate)],
        env={**os.environ, "PACKAGE_RESULT": package, "RUFF_RESULT": ruff},
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == expected
