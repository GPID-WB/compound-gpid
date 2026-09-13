"""Native wrappers preserve argv and never recurse into a shadowed executable."""

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

from .release_shell_fixture import invoke, setup_shell

ROOT = Path(__file__).resolve().parents[2]

SHELLS = ["cmd", "bash"] if os.name == "nt" else ["bash"]


@pytest.mark.skipif(os.name != "nt", reason="Windows PE fixture execution contract")
@pytest.mark.parametrize("kind", SHELLS)
def test_windows_fixture_executables_run_before_product_dispatch(tmp_path, kind):
    """Separate mock-executable startup failures from actual launcher regressions."""
    root, env, _ = setup_shell(tmp_path, kind)
    args = ["fixture-only", "", "two words & literal", 'embedded"quote', "slash\\"]
    for executable in (
        root / "packages/cg-release/.venv/Scripts/python.exe",
        tmp_path / "candidate executables/pwsh.exe",
    ):
        record = Path(env["ARGV_RECORD"])
        record.unlink(missing_ok=True)
        result = subprocess.run(
            [str(executable), *args], cwd=tmp_path, env=env, capture_output=True,
            text=True, timeout=30, check=False,
        )
        assert result.returncode == 37, (
            str(executable), result.returncode, result.stdout, result.stderr
        )
        assert json.loads(record.read_text()) == args


@pytest.mark.parametrize("kind", SHELLS)
@pytest.mark.parametrize(
    "operation",
    ["plan", "start", "status", "resume", "--legacy-bridge", "--legacy-recovery"],
)
def test_real_shell_preserves_argv_exit_and_does_not_recurse(tmp_path, kind, operation):
    root, env, shell = setup_shell(tmp_path, kind)
    args = [operation, "two words & literal", "", 'embedded"quote', "trailing slash\\"]
    result, actual = invoke(root, env, shell, args, kind)
    assert result.returncode == 37, result.stdout + result.stderr
    if operation.startswith("--legacy"):
        assert actual[:2] == ["-NoProfile", "-File"]
        assert Path(actual[2]) == root / "create-release.ps1"
        assert actual[3:5] == [
            "-LegacyOperation",
            "Bridge" if operation == "--legacy-bridge" else "Recovery",
        ]
        assert actual[5:] == args[1:]
    else:
        assert actual == ["-I", "-m", "cg_release.cli", *args]


@pytest.mark.parametrize("kind", SHELLS)
@pytest.mark.parametrize(
    "candidates,modes",
    [
        (("python",), {}),
        (("py",), {}),
        (("python3", "python", "py"), {"python3": "stub", "python": "old"}),
    ],
)
def test_real_shell_fallback_and_store_stub_rejection(
    tmp_path, kind, candidates, modes
):
    root, env, shell = setup_shell(tmp_path, kind, candidates)
    env.update({"CANDIDATE_" + key: value for key, value in modes.items()})
    result, actual = invoke(root, env, shell, ["plan", ""], kind)
    assert result.returncode == 37, result.stdout + result.stderr
    assert actual == ["-I", "-m", "cg_release.cli", "plan", ""]
    rows = [
        json.loads(line) for line in Path(env["SHELL_TRACE"]).read_text().splitlines()
    ]
    assert (
        not any(name == "python3" and args[:1] == ["-c"] for name, args in rows)
        if modes
        else True
    )


@pytest.mark.skipif(
    os.name != "nt", reason="CMD shim return is a Windows-only contract"
)
def test_real_cmd_shim_returns_for_fallback_and_preserves_child_exit(tmp_path):
    root, env, shell = setup_shell(
        tmp_path, "cmd", ("python3", "python"), shim={"python3"}
    )
    # The shim delegates to fixture.exe, so its version gate is controlled there.
    env["CANDIDATE_fixture"] = "old"
    fallback, actual = invoke(root, env, shell, ["status", ""], "cmd")
    assert fallback.returncode == 37, fallback.stdout + fallback.stderr
    assert actual == ["-I", "-m", "cg_release.cli", "status", ""]
    Path(env["ARGV_RECORD"]).unlink()
    env["CANDIDATE_python"] = "old"
    denied, actual = invoke(root, env, shell, ["status", ""], "cmd")
    assert denied.returncode == 1 and actual is None
    env["CANDIDATE_fixture"] = "valid"
    result, actual = invoke(root, env, shell, ["status", "", "two words"], "cmd")
    assert result.returncode == 37, result.stdout + result.stderr
    assert actual == ["-I", "-m", "cg_release.cli", "status", "", "two words"]


def test_launcher_routes_all_four_commands_without_shell_reparsing():
    spec = importlib.util.spec_from_file_location(
        "release_launcher", ROOT / "scripts/cg_release_cli.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for argv in (
        ["plan", "--branch", "feature/a", "--json"],
        [
            "start",
            "--version",
            "1.5.0-rc.10",
            "--reason",
            "two words & literal",
            "--yes",
        ],
        ["status", "rc1.locator", "--json"],
        ["resume", "rc1.locator"],
    ):
        calls = []
        assert (
            module.main(
                argv, run=lambda command, calls=calls: calls.append(command) or 17
            )
            == 17
        )
        assert calls[0][-len(argv) :] == list(argv)
        assert calls[0][1:4] == ["-I", "-m", "cg_release.cli"]


def test_all_five_slash_interfaces_use_same_cli():
    for name in (
        ".github/prompts/cg-release.prompt.md",
        ".kilo/commands/cg-release.md",
        ".claude/commands/cg-release.md",
        ".agents/commands/cg-release.md",
        ".opencode/commands/cg-release.md",
    ):
        content = (ROOT / name).read_text(encoding="utf-8")
        assert "Argument-Preserving Dispatch" in content
        assert "cg-release plan" in content and "cg-release start" in content
        assert "--legacy-bridge" in content and "--legacy-recovery" in content
        assert content.index("Argument-Preserving Dispatch") < content.index(
            "Dev-Repo Guardrail"
        )
