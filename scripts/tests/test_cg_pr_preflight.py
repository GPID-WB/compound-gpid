"""Contract tests for the CI-impact preflight and native target runner."""
from __future__ import annotations

import io
import hashlib
import json
import subprocess
from pathlib import Path

import cg_pr_preflight as preflight
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def receipt_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    """Use deterministic Git identities and commands, with external receipt storage."""
    root = tmp_path / "checkout"
    root.mkdir()
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(preflight, "inspect_cache_artifacts", lambda _: preflight.CacheReport())

    def git(_root: Path, arguments: tuple[str, ...]) -> preflight.GitResult:
        if arguments[:4] == preflight.RECEIPT_GIT_OPTIONS:
            arguments = arguments[4:]
        text = " ".join(arguments)
        if "HEAD^{commit}" in text:
            value = "a" * 40
        elif "HEAD^{tree}" in text:
            value = "b" * 40
        elif "core.autocrlf" in text:
            value = "false"
        elif "core.eol" in text:
            value = "lf"
        elif "status" in arguments:
            value = ""
        elif "clone" in arguments or "checkout" in arguments or arguments[:1] == ("config",):
            value = ""
        else:
            raise AssertionError(f"Unexpected Git query: {arguments}")
        return preflight.GitResult(0, value, "")

    monkeypatch.setattr(preflight, "_run_git", git)
    monkeypatch.setattr(
        preflight, "run_native_target",
        lambda root, selection, **kwargs: preflight.NativeRunResult(tuple(
            preflight.CommandResult(command, 0)
            for command in preflight.selected_native_commands(selection, root, **kwargs)
        )),
    )
    return root, receipt


def test_receipt_verification_allows_a_different_python_location(
    receipt_run: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, receipt = receipt_run
    assert preflight.main(["--root", str(root), "--phase", "committed", "--full-gate",
                           "--run-native-target", "--emit-receipt", str(receipt)]) == 0
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload.pop("digest")
    for command in payload["commands"]:
        if command[0] == preflight.PYTHON:
            command[0] = str(root / "other-venv" / "python.exe")
    payload["digest"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    def must_not_execute(*args: object, **kwargs: object) -> None:
        raise AssertionError("Verifier must not execute a receipt-supplied interpreter")
    monkeypatch.setattr(preflight.subprocess, "run", must_not_execute)
    assert preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)


def test_receipt_destination_has_exclusive_ownership(
    receipt_run: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, receipt = receipt_run
    argv = ["--root", str(root), "--phase", "committed", "--full-gate",
            "--run-native-target", "--emit-receipt", str(receipt)]
    original_run = preflight.run_native_target
    calls = []
    def first_run(*args: object, **kwargs: object) -> preflight.NativeRunResult:
        calls.append("owner")
        # A second invocation collides deterministically while the first owns the gate.
        monkeypatch.setattr(preflight, "run_native_target", lambda *a, **kw:
                            pytest.fail("A colliding invocation must not start a gate"))
        assert preflight.main(argv) == 2
        return original_run(*args, **kwargs)
    monkeypatch.setattr(preflight, "run_native_target", first_run)
    assert preflight.main(argv) == 0
    assert calls == ["owner"]
    assert preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)
    # A later owner must invalidate the completed receipt before its own failure.
    monkeypatch.setattr(preflight, "run_native_target", lambda *a, **kw:
                        preflight.NativeRunResult((preflight.CommandResult(("uv", "--version"), 1),)))
    assert preflight.main(argv) == 1
    assert not receipt.exists()
    assert not receipt.with_name(receipt.name + ".lock").exists()


@pytest.mark.parametrize("change", ["relative-interpreter", "mixed-interpreters", "argument", "uv"])
def test_logical_command_contract_rejects_substitutions(change: str) -> None:
    commands = [list(command) for command in preflight.selected_native_commands(
        preflight.full_gate_selection(), Path("."))]
    python_commands = [command for command in commands if command[0] == preflight.PYTHON]
    if change == "relative-interpreter":
        for command in python_commands:
            command[0] = "python"
    elif change == "mixed-interpreters":
        python_commands[0][0] = str(Path(preflight.PYTHON).parent / "other" / "python")
    elif change == "argument":
        python_commands[0][-1] = "--collect-only"
    else:
        commands[0][0] = "different-tool"
    assert not preflight._receipt_commands_match(commands)


@pytest.mark.parametrize("hidden_change", ["normalized-crlf", "assume-unchanged", "skip-worktree"])
def test_receipt_gate_owns_fresh_checkout_with_actual_lf_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hidden_change: str,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    def git(*arguments: str) -> str:
        return subprocess.run(["git", "-C", str(source), *preflight.RECEIPT_GIT_OPTIONS, *arguments], check=True,
                              capture_output=True, text=True).stdout.strip()
    git("init")
    (source / ".gitattributes").write_bytes(b"*.py text eol=lf\n*.cmd text eol=crlf\n")
    (source / "code.py").write_bytes(b"answer = 42\n")
    (source / "launcher.cmd").write_bytes(b"@echo off\r\n")
    git("add", ".")
    git("-c", "user.name=Receipt Test", "-c", "user.email=receipt@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-m", "test: receipt fixture")
    if hidden_change == "normalized-crlf":
        (source / "code.py").write_bytes(b"answer = 42\r\n")
        # Refresh Git's stat cache through its clean filter. The index still
        # contains the original LF blob while the working file retains CRLF.
        git("add", "code.py")
        assert git("rev-parse", ":code.py") == git("rev-parse", "HEAD:code.py")
        assert (source / "code.py").read_bytes() == b"answer = 42\r\n"
    else:
        git("update-index", "--" + hidden_change, "code.py")
        (source / "code.py").write_bytes(b"answer = 0\r\n")
    assert git("status", "--porcelain") == ""
    observed = []
    def run(root: Path, selection: preflight.ChangeSelection, **kwargs: object) -> preflight.NativeRunResult:
        assert root != source
        local_config = subprocess.run(["git", "-C", str(root), "config", "--local", "--get-regexp",
                                       r"^core\.(autocrlf|eol)$"], capture_output=True, text=True)
        assert local_config.returncode == 1
        assert local_config.stdout == ""
        assert (root / "code.py").read_bytes() == b"answer = 42\n"
        assert (root / "launcher.cmd").read_bytes() == b"@echo off\r\n"
        observed.append(root)
        return preflight.NativeRunResult(tuple(preflight.CommandResult(command, 0)
            for command in preflight.selected_native_commands(selection, root, **kwargs)))
    monkeypatch.setattr(preflight, "run_native_target", run)
    receipt = tmp_path / "receipt.json"
    assert preflight.main(["--root", str(source), "--phase", "committed", "--full-gate",
                           "--run-native-target", "--emit-receipt", str(receipt)]) == 0
    assert preflight.verify_preflight_receipt(receipt, git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"))
    assert len(observed) == 1
    assert not observed[0].exists()


@pytest.mark.parametrize("operation", ["clone", "autocrlf", "eol", "checkout"])
def test_owned_receipt_checkout_failure_never_starts_gate_or_leaves_evidence(
    receipt_run: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    root, receipt = receipt_run
    receipt.write_text("stale evidence", encoding="utf-8")
    original_git = preflight._run_git
    clone_paths = []
    def git(directory: Path, arguments: tuple[str, ...]) -> preflight.GitResult:
        assert arguments[:4] == preflight.RECEIPT_GIT_OPTIONS
        logical = arguments[4:]
        if "clone" in arguments:
            clone = Path(arguments[-1])
            clone.mkdir()
            clone_paths.append(clone)
        selected = (
            (operation == "clone" and "clone" in arguments)
            or (operation == "autocrlf" and directory != root and logical == ("config", "--get", "core.autocrlf"))
            or (operation == "eol" and directory != root and logical == ("config", "--get", "core.eol"))
            or (operation == "checkout" and logical[:1] == ("checkout",))
        )
        return preflight.GitResult(1, "", "injected failure") if selected else original_git(directory, arguments)
    monkeypatch.setattr(preflight, "_run_git", git)
    monkeypatch.setattr(preflight, "run_native_target", lambda *a, **kw:
                        pytest.fail("Failed checkout preparation must not start a gate"))
    assert preflight.main(["--root", str(root), "--phase", "committed", "--full-gate",
                           "--run-native-target", "--emit-receipt", str(receipt)]) == 2
    assert not receipt.exists()
    assert not receipt.with_name(receipt.name + ".lock").exists()
    assert len(clone_paths) == 1
    assert not clone_paths[0].parent.exists()


def test_emit_receipt_binds_successful_full_gate(receipt_run: tuple[Path, Path]) -> None:
    root, receipt = receipt_run
    assert preflight.main([
        "--root", str(root), "--phase", "committed", "--full-gate",
        "--run-native-target", "--emit-receipt", str(receipt),
    ]) == 0
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    digest = payload.pop("digest")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert payload["schema_version"] == 1
    assert payload["commit_sha"] == "a" * 40
    assert payload["tree_sha"] == "b" * 40
    assert payload["line_ending_provenance"] == {"core.autocrlf": "false", "core.eol": "lf"}
    assert payload["timestamp"].endswith(("Z", "+00:00"))
    expected = preflight.selected_native_commands(preflight.full_gate_selection(), root)
    assert payload["commands"] == [list(command) for command in expected]
    assert payload["exit_codes"] == [0] * len(expected)
    assert list(receipt.parent.glob("*.tmp")) == []
    assert preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)
    assert preflight.main(["--verify-receipt", str(receipt), "--expected-commit", "a" * 40,
                           "--expected-tree", "b" * 40]) == 0


@pytest.mark.parametrize("field,value", [
    ("commit_sha", "c" * 40), ("tree_sha", "c" * 40),
    ("schema_version", True), ("schema_version", 1.0), ("schema_version", "1"),
    ("schema_version", 2), ("line_ending_provenance", {"core.autocrlf": "true", "core.eol": "crlf"}),
    ("commands", []), ("commands", [["echo", "success"]]), ("exit_codes", []),
    ("timestamp", None), ("timestamp", "invalid"), ("timestamp", "2026-09-17T00:00:00"),
    ("digest", "f" * 64),
])
def test_verify_receipt_rejects_invalid_evidence_even_with_new_digest(
    receipt_run: tuple[Path, Path], field: str, value: object,
) -> None:
    root, receipt = receipt_run
    assert preflight.main(["--root", str(root), "--phase", "committed", "--full-gate",
                           "--run-native-target", "--emit-receipt", str(receipt)]) == 0
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload.pop("digest")
    if field != "digest":
        payload[field] = value
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["digest"] = value if field == "digest" else hashlib.sha256(canonical.encode()).hexdigest()
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    assert not preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)


@pytest.mark.parametrize("code", [1, False, "0", 0.0])
def test_verify_receipt_requires_integer_zero_exit_codes(
    receipt_run: tuple[Path, Path], code: object,
) -> None:
    root, receipt = receipt_run
    assert preflight.main(["--root", str(root), "--phase", "committed", "--full-gate",
                           "--run-native-target", "--emit-receipt", str(receipt)]) == 0
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload.pop("digest")
    payload["exit_codes"][0] = code
    payload["digest"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    assert not preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)


@pytest.mark.parametrize("raw", [b"{", b"[]", b"null", b"true", b"\xff", b'{"digest":1,"digest":2}'])
def test_verify_receipt_rejects_malformed_documents(tmp_path: Path, raw: bytes) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_bytes(raw)
    assert not preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)


def test_verify_receipt_missing_or_oversized_file_fails_closed(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    assert not preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)
    receipt.write_bytes(b" " * (preflight.MAX_RECEIPT_BYTES + 1))
    assert not preflight.verify_preflight_receipt(receipt, "a" * 40, "b" * 40)


@pytest.mark.parametrize("change", ["commit", "tree", "dirty", "config", "incomplete", "replace-error"])
def test_emit_receipt_checks_end_state_and_atomic_write(
    receipt_run: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    root, receipt = receipt_run
    original_run = preflight.run_native_target
    original_git = preflight._run_git

    def run(*args: object, **kwargs: object) -> preflight.NativeRunResult:
        result = original_run(*args, **kwargs)
        def git(root: Path, arguments: tuple[str, ...]) -> preflight.GitResult:
            text = " ".join(arguments)
            if ((change == "commit" and "HEAD^{commit}" in text)
                    or (change == "tree" and "HEAD^{tree}" in text)):
                return preflight.GitResult(0, "c" * 40, "")
            if change == "dirty" and "status" in arguments:
                return preflight.GitResult(0, " M changed.py", "")
            if change == "config" and "core.eol" in arguments:
                return preflight.GitResult(0, "crlf", "")
            return original_git(root, arguments)
        monkeypatch.setattr(preflight, "_run_git", git)
        return preflight.NativeRunResult(result.commands[:-1]) if change == "incomplete" else result

    monkeypatch.setattr(preflight, "run_native_target", run)
    if change == "replace-error":
        def fail_replace(*args: object) -> None:
            raise OSError("injected replace failure")
        monkeypatch.setattr(preflight.os, "replace", fail_replace)
    assert preflight.main(["--root", str(root), "--phase", "committed", "--full-gate",
                           "--run-native-target", "--emit-receipt", str(receipt)]) != 0
    assert not receipt.exists()
    assert list(receipt.parent.glob("*.tmp")) == []


@pytest.mark.parametrize("flags", [
    [], ["--selection-only"], ["--run-native-target", "--selection-only"],
])
def test_emit_receipt_never_certifies_selection_only(
    receipt_run: tuple[Path, Path], flags: list[str],
) -> None:
    root, receipt = receipt_run
    assert preflight.main([
        "--root", str(root), "--phase", "committed", "--full-gate",
        "--emit-receipt", str(receipt), *flags,
    ]) == 0
    assert not receipt.exists()


@pytest.mark.parametrize("failure", ["command", "selection", "interrupted"])
def test_emit_receipt_never_leaves_success_after_failed_gate(
    receipt_run: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    root, receipt = receipt_run
    receipt.write_text('{"old": "receipt"}', encoding="utf-8")
    if failure == "selection":
        monkeypatch.setattr(preflight, "inspect_cache_artifacts",
                            lambda _: preflight.CacheReport(fatal=True))
    elif failure == "command":
        monkeypatch.setattr(preflight, "run_native_target", lambda *a, **kw:
                            preflight.NativeRunResult((preflight.CommandResult(("uv", "--version"), 1),)))
    else:
        def interrupted(*args: object, **kwargs: object) -> None:
            raise KeyboardInterrupt
        monkeypatch.setattr(preflight, "run_native_target", interrupted)
    argv = ["--root", str(root), "--phase", "committed", "--full-gate",
            "--run-native-target", "--emit-receipt", str(receipt)]
    if failure == "interrupted":
        with pytest.raises(KeyboardInterrupt):
            preflight.main(argv)
    else:
        assert preflight.main(argv) != 0
    assert not receipt.exists()
    assert not receipt.with_name(receipt.name + ".lock").exists()


@pytest.mark.parametrize("condition", ["prepare", "partial", "profile", "dirty", "in-tree"])
def test_emit_receipt_rejects_insufficient_release_evidence(
    receipt_run: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, condition: str,
) -> None:
    root, receipt = receipt_run
    phase = "prepare" if condition == "prepare" else "committed"
    flags = ["--changed-file", "README.md"] if condition == "partial" else ["--full-gate"]
    if condition == "profile":
        flags += ["--gate-owner", "gpid-native-profile"]
    if condition == "dirty":
        original_git = preflight._run_git
        monkeypatch.setattr(preflight, "_run_git", lambda root, args:
                            preflight.GitResult(0, " M scripts/cg_pr_preflight.py", "")
                            if "status" in args else original_git(root, args))
    if condition == "in-tree":
        receipt = root / "receipt.json"
    assert preflight.main([
        "--root", str(root), "--phase", phase, *flags,
        "--run-native-target", "--emit-receipt", str(receipt),
    ]) != 0
    assert not receipt.exists()


def test_native_producer_installs_pinned_controller_tool_before_preflight() -> None:
    import yaml

    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/tests.yml").read_text())
    steps = workflow["jobs"]["native-targets"]["steps"]
    gate_index = next(i for i, step in enumerate(steps)
                      if "scripts/cg_pr_preflight.py" in step.get("run", ""))
    install = f"python -m pip install uv=={preflight.CONTROLLER_UV_VERSION}"
    assert any(install in step.get("run", "") for step in steps[:gate_index])
    assert "uv==" in preflight.__doc__


@pytest.mark.parametrize("version", ["uv 0.1.0", "not-uv", ""])
def test_controller_rejects_unpinned_tool_before_running_gate(
    version: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    import subprocess

    calls = []

    def wrong_version(argv: list, **_kwargs: object) -> subprocess.CompletedProcess:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, version, "")

    monkeypatch.setattr(preflight.subprocess, "run", wrong_version)
    selection = preflight.classify_changed_files(["packages/cg-release/uv.lock"])
    result = preflight.run_native_target(tmp_path, selection)
    assert result.exit_code != 0
    assert calls == [["uv", "--version"]]
    assert "uv==0.11.3" in result.commands[0].stderr


def test_missing_uv_reports_actionable_prerequisite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    def missing(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError("uv")

    monkeypatch.setattr(preflight.subprocess, "run", missing)
    selection = preflight.classify_changed_files(["packages/cg-release/uv.lock"])
    result = preflight.run_native_target(tmp_path, selection)
    assert result.exit_code != 0
    assert "python -m pip install uv==0.11.3" in result.commands[0].stderr


@pytest.mark.parametrize("path", [
    "packages/cg-release/src/cg_release/cli.py",
    "packages/cg-release/uv.lock",
    ".github/workflows/release-controller-ci.yml",
    ".github/workflows/tests.yml",
    "scripts/benchmark_release.py",
    "create-release.ps1",
    "scripts/cg_pr_preflight.py",
])
def test_controller_impact_selects_separate_locked_gate(path: str) -> None:
    selection = preflight.classify_changed_files([path])
    assert selection.controller_required is True
    assert selection.no_impact is False
    assert selection.as_dict()["controller_required"] is True
    commands = preflight.selected_native_commands(selection, Path("repo"))
    assert any("packages/cg-release" in command and "--locked" in command
               for command in commands)


def test_package_only_changes_do_not_change_native_test_list() -> None:
    selection = preflight.classify_changed_files(["packages/cg-release/pyproject.toml"])
    assert selection.native_required is False
    assert all(not path.startswith("packages/") for path in preflight.NATIVE_PYTEST_FILES)
    assert not preflight.classify_changed_files(["packages/cg-release-other/x"]).controller_required


def test_full_gate_requires_controller_package() -> None:
    assert preflight.full_gate_selection().controller_required is True


@pytest.mark.parametrize("path", ["scripts/release_profile_gpid.py", "scripts/release_profile_build.py",
                                   "scripts/release_profile_install.py", ".release-controller.json",
                                   ".github/workflows/release-controller-docs.yml", "bin/cg-release.cmd"])
def test_profile_impact_selects_package_and_profile_gate(path: str) -> None:
    assert preflight.classify_changed_files([path]).controller_required


def test_controller_missing_runtime_does_not_pass_or_download(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    import subprocess

    calls = []

    def missing_runtime(argv: list, **kwargs: object) -> subprocess.CompletedProcess:
        calls.append(argv)
        if argv == ["uv", "--version"]:
            return subprocess.CompletedProcess(argv, 0, "uv 0.11.3", "")
        return subprocess.CompletedProcess(argv, 2, "", "No interpreter found for Python >=3.11,<3.13")

    monkeypatch.setattr(preflight.subprocess, "run", missing_runtime)
    selection = preflight.classify_changed_files(["packages/cg-release/uv.lock"])
    result = preflight.run_native_target(tmp_path, selection)
    assert result.exit_code == 2
    assert len(calls) == 2
    assert calls[0] == ["uv", "--version"]
    assert "--no-python-downloads" in calls[1]
    assert "No interpreter found" in result.commands[1].stderr


@pytest.mark.parametrize("command, timeout", [
    (("first",), 600),
    (preflight.FULL_PACKAGE_TEST_COMMAND, 1800),
])
@pytest.mark.parametrize("outcome", [0, 1, "timeout"])
def test_native_progress_is_flushed_and_failures_stop_execution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcome: object,
    command: tuple[str, ...], timeout: int,
) -> None:
    """Progress precedes the blocking child and preserves the failure contract."""
    class ProgressStream(io.StringIO):
        def flush(self) -> None:
            self.flushed = self.getvalue()

    progress = ProgressStream()
    monkeypatch.setattr(preflight.sys, "stderr", progress)
    calls = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append(argv)
        assert f"starting native command {len(calls)}/2" in progress.flushed
        expected_timeout = timeout if len(calls) == 1 else 600
        assert kwargs["timeout"] == expected_timeout
        assert f"timeout={expected_timeout}s" in progress.flushed
        assert kwargs["capture_output"] is True
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(argv, expected_timeout)
        return subprocess.CompletedProcess(argv, outcome, "child output", "")

    monkeypatch.setattr(preflight.subprocess, "run", run)
    result = preflight.run_native_target(tmp_path, commands=(command, ("second",)))
    assert result.exit_code == (127 if outcome == "timeout" else outcome)
    assert len(calls) == (2 if outcome == 0 else 1)
    assert f"exited {result.exit_code} after" in progress.flushed
    if outcome == "timeout":
        assert (preflight.CONTROLLER_UV_PREREQUISITE if command[0] == "uv"
                else "TimeoutExpired") in result.commands[0].stderr


def test_native_progress_preserves_json_stdout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Machine-readable stdout remains a single final JSON document."""
    monkeypatch.setattr(preflight, "inspect_cache_artifacts", lambda _: preflight.CacheReport())
    monkeypatch.setattr(
        preflight.subprocess, "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, f"uv {preflight.CONTROLLER_UV_VERSION}" if command == ["uv", "--version"] else "", ""
        ),
    )
    assert preflight.main([
        "--root", str(tmp_path), "--phase", "committed", "--full-gate",
        "--run-native-target", "--format", "json",
    ]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["exit_code"] == 0
    assert "inspecting selection and cache (phase=committed)" in captured.err
    command_count = len(preflight.selected_native_commands(preflight.full_gate_selection(), tmp_path))
    assert f"native command {command_count}/{command_count} exited 0" in captured.err


def test_release_prompt_requires_blocking_budget_and_no_blind_retry() -> None:
    """Release calls must outlive child budgets without weakening the gate."""
    prompt = (REPO_ROOT / ".github/prompts/cg-release.prompt.md").read_text(encoding="utf-8")
    assert "`7200000` milliseconds (120 minutes)" in prompt
    commands = preflight.selected_native_commands(preflight.full_gate_selection(), REPO_ROOT)
    assert 7200 > sum(preflight.FULL_PACKAGE_TEST_TIMEOUT_SECONDS
                      if command == preflight.FULL_PACKAGE_TEST_COMMAND
                      else preflight.NATIVE_COMMAND_TIMEOUT_SECONDS for command in commands)
    assert "blocking foreground call" in prompt
    assert "or an automatic retry after a timeout" in prompt
    assert "never substitute `--phase prepare`" in prompt
    assert "python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target" in prompt


def test_canonical_change_selects_native_and_module_gates() -> None:
    selection = preflight.classify_changed_files([".github/prompts/cg-work.prompt.md"])

    assert selection.native_required is True
    assert selection.module_checks == ("dependencies", "cross-suite", "ownership")
    assert "prompt" in selection.reasons


def test_generated_tree_change_selects_committed_drift_gate() -> None:
    selection = preflight.classify_changed_files([".agents/commands/cg-work.md"])

    assert selection.native_required is True
    assert selection.generated_tree_changed is True
    assert selection.drift_required is True


def test_no_impact_change_does_not_select_native_target() -> None:
    selection = preflight.classify_changed_files(["README.md"])

    assert selection.native_required is False
    assert selection.module_checks == ()
    assert selection.drift_required is False


@pytest.mark.parametrize("path", ["compound-gpid.local.md", ".compound-gpid/active-manifest.json"])
def test_project_selection_changes_are_native_and_module_impacting(path: str) -> None:
    selection = preflight.classify_changed_files([path])

    assert selection.native_required is True
    assert selection.module_checks == ("dependencies", "cross-suite", "ownership")
    assert "project-config" in selection.reasons


def test_base_resolution_prefers_existing_pr_base() -> None:
    assert preflight.resolve_base_branch("release", "feature-base", "main") == "release"
    assert preflight.resolve_base_branch(None, "feature-base", "main") == "feature-base"
    assert preflight.resolve_base_branch(None, None, "main") == "main"


def test_missing_history_is_visible_and_uses_explicit_full_gate_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        preflight,
        "_run_git",
        lambda *args, **kwargs: preflight.GitResult(128, "", "shallow history"),
    )

    result = preflight.derive_changed_files(tmp_path, base="origin/main")

    assert result.selection_error is not None
    assert result.full_gate_fallback is False


def test_zero_before_revision_requests_full_gate_fallback(tmp_path: Path) -> None:
    result = preflight.derive_changed_files(tmp_path, base="0" * 40)

    assert result.full_gate_fallback is True
    assert result.selection_error is None


def test_cache_artifacts_distinguish_tracked_manifest_and_local_noise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cache = tmp_path / ".github/skills/cg-skill-test/__pycache__/module.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"bytecode")
    monkeypatch.setattr(preflight, "git_tracked_paths", lambda *args, **kwargs: set())

    report = preflight.inspect_cache_artifacts(tmp_path)

    assert report.fatal is False
    assert report.paths == (".github/skills/cg-skill-test/__pycache__/module.pyc",)


def test_git_tracking_failure_is_fatal_for_cache_provenance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        preflight,
        "_run_git",
        lambda *args, **kwargs: preflight.GitResult(128, "", "not a repository"),
    )

    report = preflight.inspect_cache_artifacts(tmp_path)

    assert report.fatal is True
    assert report.git_error is not None


def test_cache_report_bounds_local_path_samples(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(preflight, "git_tracked_paths", lambda *args, **kwargs: set())
    for index in range(preflight.MAX_CACHE_REPORT_PATHS + 5):
        cache = tmp_path / f"scripts/cache-{index}/__pycache__/module.pyc"
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b"bytecode")

    report = preflight.inspect_cache_artifacts(tmp_path)

    assert report.path_count == preflight.MAX_CACHE_REPORT_PATHS + 5
    assert report.truncated is True
    assert len(report.paths) == preflight.MAX_CACHE_REPORT_PATHS


def test_native_command_contains_ordered_pytest_marker_and_all_module_checks() -> None:
    commands = preflight.native_commands(Path("repo"))
    pytest_command = commands[0]

    assert pytest_command[:4] == (preflight.PYTHON, "-m", "pytest", "scripts/tests/test_target_mapping.py")
    assert "-m" in pytest_command
    assert "not integration" in pytest_command
    assert (preflight.PYTHON, "scripts/cg_validate_modules.py", "--check-dependencies") in commands
    assert (preflight.PYTHON, "scripts/cg_validate_modules.py", "--check-cross-suite") in commands
    assert (preflight.PYTHON, "scripts/cg_validate_modules.py", "--check-ownership") in commands
    assert "scripts/tests/test_project_projection.py" in commands[0]


def test_native_command_never_invokes_pester() -> None:
    commands = preflight.native_commands(Path("repo"))

    assert all("pester" not in " ".join(command).casefold() for command in commands)
    assert all("Run-Tests.ps1" not in " ".join(command) for command in commands)


def test_prepare_defers_head_drift_until_committed_phase() -> None:
    prepare = preflight.build_preflight_result(
        Path("repo"),
        phase="prepare",
        changed_files=[".github/prompts/cg-commit-push-pr.prompt.md"],
    )
    committed = preflight.build_preflight_result(
        Path("repo"),
        phase="committed",
        changed_files=[".github/prompts/cg-commit-push-pr.prompt.md"],
    )

    assert all(
        "test_target_drift.py" not in " ".join(command)
        for command in prepare.selected_commands
    )
    assert any(
        "test_target_drift.py" in " ".join(command)
        for command in committed.selected_commands
    )


def test_full_gate_selection_includes_committed_drift_and_all_module_commands() -> None:
    result = preflight.build_preflight_result(
        Path("repo"), phase="committed", changed_files=(), full_gate=True
    )
    command_text = " ".join(" ".join(command) for command in result.selected_commands)

    assert result.full_gate_fallback is True
    assert "test_target_drift.py" in command_text
    assert all(check in command_text for check in ("check-dependencies", "check-cross-suite", "check-ownership"))


def test_cli_consumes_neutral_and_blocking_kilo_results(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr(preflight, "inspect_cache_artifacts", lambda _root: preflight.CacheReport())
    neutral_path = tmp_path / "neutral.json"
    neutral_path.write_text(json.dumps({
        "status": "missing-kilo", "exit_code": 3, "inventory": {},
    }), encoding="utf-8")

    neutral_exit = preflight.main([
        "--root", str(tmp_path), "--changed-file", "README.md",
        "--kilo-result-json", str(neutral_path), "--selection-only", "--format", "json",
    ])
    neutral_output = json.loads(capsys.readouterr().out)
    assert neutral_exit == 0
    assert neutral_output["kilo"]["outcome"] == "generic-not-applicable"

    blocking_path = tmp_path / "blocking.json"
    blocking_path.write_text(json.dumps({
        "status": "local-content-invalid", "exit_code": 2, "inventory": {},
    }), encoding="utf-8")
    blocking_exit = preflight.main([
        "--root", str(tmp_path), "--changed-file", "README.md",
        "--kilo-result-json", str(blocking_path), "--selection-only", "--format", "json",
    ])
    assert blocking_exit == 2


def test_kilo_adapter_preserves_authoritative_status_and_evidence() -> None:
    payload = {
        "status": "missing-kilo",
        "exit_code": 3,
        "message": "No supported Kilo executable was found",
        "remediation": "Install Kilo",
        "kilo_version": None,
        "kilo_executable_sha256": None,
        "certified_launch_required": False,
        "inventory": {"records": []},
    }

    outcome = preflight.adapt_kilo_result(payload)

    assert outcome.outcome == "generic-not-applicable"
    assert outcome.source_status == "missing-kilo"
    assert outcome.exit_code == 3
    assert outcome.inventory == {"records": []}


def test_kilo_adapter_rejects_unknown_status() -> None:
    with pytest.raises(preflight.KiloResultError, match="unknown Kilo status"):
        preflight.adapt_kilo_result({"status": "future-status", "exit_code": 0})


@pytest.mark.parametrize(
    ("status", "expected", "exit_code"),
    [
        ("ok", "certified-ready", 0),
        ("ok-no-coexistence", "generic-not-applicable", 0),
        ("missing-kilo", "generic-not-applicable", 3),
        ("unsupported-kilo-version", "generic-not-applicable", 3),
        ("local-projection-missing", "blocking-configuration", 2),
        ("local-projection-invalid", "blocking-configuration", 2),
        ("local-content-invalid", "blocking-content", 2),
        ("host-command-error", "blocking-configuration", 3),
        ("host-schema-error", "blocking-configuration", 5),
        ("local-inventory-missing", "blocking-content", 5),
        ("containment-unhonored", "blocking-containment", 4),
    ],
)
def test_kilo_adapter_maps_every_authoritative_status(
    status: str, expected: str, exit_code: int
) -> None:
    payload = {"status": status, "exit_code": exit_code, "inventory": {}}
    if status == "ok":
        payload.update({
            "kilo_version": "7.4.21",
            "kilo_executable": "/opt/kilo",
            "kilo_executable_sha256": "a" * 64,
        })
    outcome = preflight.adapt_kilo_result(payload)

    assert outcome.outcome == expected
    assert outcome.source_status == status


def test_kilo_adapter_rejects_malformed_result() -> None:
    with pytest.raises(preflight.KiloResultError, match="exit_code"):
        preflight.adapt_kilo_result({"status": "ok"})
    with pytest.raises(preflight.KiloResultError, match="inventory"):
        preflight.adapt_kilo_result({"status": "ok", "exit_code": 0, "inventory": "invalid"})


def test_json_and_text_results_are_bounded() -> None:
    result = preflight.PreflightResult(
        phase="prepare",
        selection=preflight.classify_changed_files(["scripts/cg_generate_targets.py"]),
        changed_files=("scripts/cg_generate_targets.py",),
    )

    rendered = preflight.render_result(result, "json")
    decoded = json.loads(rendered)
    assert decoded["phase"] == "prepare"
    assert "native_commands" in decoded
    assert "full_output" not in decoded
    assert "prepare" in preflight.render_result(result, "text")


def test_text_result_exposes_bounded_failed_command_output() -> None:
    result = preflight.PreflightResult(
        phase="committed",
        selection=preflight.full_gate_selection(),
        changed_files=(),
        command_results=(
            preflight.CommandResult(
                command=("python", "-m", "pytest"),
                returncode=1,
                stdout="assertion failure",
                stderr="pytest error",
            ),
        ),
    )

    rendered = preflight.render_result(result, "text")

    assert "assertion failure" in rendered
    assert "pytest error" in rendered


def test_workflow_delegates_native_selection_and_preserves_context() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    native_start = workflow.index("- name: Run authoritative native target preflight")
    publisher_start = workflow.index("- name: Run generic publisher", native_start)
    native_block = workflow[native_start:publisher_start]

    assert "scripts/cg_pr_preflight.py" in native_block
    assert "python -m pytest" not in native_block
    assert "github.event.pull_request.base.sha" in native_block
    assert "github.event.before" in native_block
    assert "--full-gate" in native_block
    assert "git rev-parse --verify --quiet" in native_block
    assert "Push-before revision is unavailable" in native_block
    assert "0000000000000000000000000000000000000000" in native_block
    assert "fetch-depth: 0" in workflow
    assert "origin/HEAD" not in native_block
    assert "tests/Run-Tests.ps1" in workflow
    assert "E2E smoke test" in workflow


def test_native_target_owns_deterministic_kilo_and_preflight_tests() -> None:
    assert "scripts/tests/test_commit_push_pr_source_detection.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_cg_compound_gpid_rd_registry.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_kilo_coexistence.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_kilo_copy.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_link_projection_order.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_skill_management_contracts.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_skill_management_dispatch.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_cg_pr_preflight.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_project_manifest.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_project_projection.py" in preflight.NATIVE_PYTEST_FILES
    assert "scripts/tests/test_release_policy.py" in preflight.NATIVE_PYTEST_FILES


def test_workflow_reports_neutral_generic_kilo_capability() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    start = workflow.index("kilo-capability-report:")
    end = workflow.index("  native-targets:", start)
    block = workflow[start:end]

    assert "CG_KILO_CERTIFIED_RUNNER" in block
    assert "CG_KILO_CERTIFIED_VERSION" in block
    assert "CG_KILO_CERTIFIED_SHA256" in block
    assert "generic-not-applicable" in block
    assert "real-host integration" in block
    assert "upload-artifact" in block


def test_certified_kilo_job_is_protected_and_hash_pinned() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    start = workflow.index("kilo-certified-integration:")
    block = workflow[start:workflow.index("  native-targets:", start)]

    assert "github.event_name == 'push'" in block
    assert "github.event_name == 'workflow_dispatch'" in block
    assert "github.ref == 'refs/heads/dev'" in block
    assert "github.ref_protected" in block
    assert "github.event_name != 'pull_request'" in block
    assert "vars.CG_KILO_CERTIFIED_RUNNER" in block
    assert "vars.CG_KILO_CERTIFIED_VERSION" in block
    assert "vars.CG_KILO_CERTIFIED_SHA256" in block
    assert "environment: cg-kilo-certified" in block
    assert "ref: ${{ needs.kilo-certified-subject.outputs.subject }}" in block
    assert "ref: ${{ github.event.repository.default_branch }}" not in block
    assert "git checkout --detach" in block
    assert "git rev-parse HEAD" in block
    subject = workflow[workflow.index("  kilo-certified-subject:"):start]
    assert "subject_commit" in workflow
    assert "github.sha" in subject
    assert "[0-9a-f]{40}" in subject
    assert "github.rest.repos.getCommit" in subject
    assert "commit.data.sha !== subject" in subject
    assert "kilo_executable_sha256" in block
    assert "CG_KILO_CERTIFIED_SHA256" in block
    assert "CG_KILO_CERTIFIED_VERSION" in block
    assert "certified-host" in block
    assert "cg-kilo" in block
    assert "CG_KILO_CERTIFIED_EXECUTABLE" in block
    assert "-m pytest scripts/tests/test_kilo_coexistence.py -m integration" in block


@pytest.mark.parametrize("case", ["valid", "mutable", "missing", "newline", "foreign", "fork", "mismatch", "absent-commit"])
def test_certified_subject_script_rejects_untrusted_inputs(case):
    """Execute the exact workflow script with a local GitHub client fixture.

    The fixture is genuinely untrusted input: the subject script bytes are
    extracted verbatim from the workflow's ``script: |`` block (anchored at
    its literal 10-space indentation, so a re-indentation fails loudly at
    extraction instead of silently testing stale bytes) and executed under
    ``node`` with injected adversarial inputs covering a non-string/mutable
    subject, missing or newline-contaminated subjects, foreign or forked
    repositories, SHA mismatches, and absent commits. A host without a
    ``node`` executable skips instead of erroring out the whole module.
    """
    import shutil
    if shutil.which("node") is None:
        pytest.skip("node is required to execute the certified-subject script")
    import subprocess
    import textwrap
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    block = workflow.split("  kilo-certified-subject:", 1)[1].split("  kilo-certified-integration:", 1)[0]
    script = textwrap.dedent(block.split("          script: |\n", 1)[1])
    sha = "a" * 40
    data = {"subject": sha, "repository": "owner/repo", "fork": False, "returned": sha, "missing": False}
    if case in ("mutable", "missing", "newline"):
        data["subject"] = {"mutable": "dev", "missing": "", "newline": sha + "\n"}[case]
    elif case == "foreign":
        data["repository"] = "fork/repo"
    elif case == "fork":
        data["fork"] = True
    elif case == "mismatch":
        data["returned"] = "b" * 40
    elif case == "absent-commit":
        data["missing"] = True
    harness = """
const data = JSON.parse(process.argv[1]);
process.env.SUBJECT_COMMIT = data.subject;
const context = {repo:{owner:'owner',repo:'repo'},payload:{repository:{full_name:data.repository,fork:data.fork}}};
const github = {rest:{repos:{getCommit:async request => {
  if(data.missing || request.ref !== data.subject || request.owner !== 'owner' || request.repo !== 'repo') throw Error('missing');
  return {data:{sha:data.returned}};
}}}};
const core = {setOutput:(name,value) => process.stdout.write(JSON.stringify({name,value}))};
"""
    result = subprocess.run(["node", "-e", harness + "\n(async()=>{\n" + script + "\n})().catch(()=>process.exit(42));", json.dumps(data)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == (0 if case == "valid" else 42), result.stderr
    if case == "valid":
        assert json.loads(result.stdout) == {"name": "subject", "value": sha}
    else:
        assert result.stdout == ""


def test_generic_e2e_consumes_declared_capability_without_host_probe() -> None:
    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    start = workflow.index("# Windows E2E smoke test")
    end = workflow.index("# macOS: pwsh", start)
    block = workflow[start:end]

    assert "needs.kilo-capability-report.outputs.outcome" in workflow
    assert "CG_KILO_CAPABILITY" in block
    assert "generic-not-applicable" in block
    assert "kilo debug skill" not in block


def test_base_resolution_preserves_existing_pr_precedence_for_standalone() -> None:
    # The standalone resolver keeps its documented precedence: an existing PR
    # base wins over the explicit and default values. Autopilot publication
    # must never reuse this silently-adopting precedence (see the focused
    # ordering guard below), but standalone behavior stays unchanged.
    assert preflight.resolve_base_branch("feature-base", "main", "main") == "feature-base"
    assert preflight.resolve_base_branch(None, "explicit", "main") == "explicit"
    assert preflight.resolve_base_branch(None, "", "main") == "main"


def test_autopilot_publication_requires_selected_base_before_existing_pr() -> None:
    # Step 10 (publication reconciliation): the selected base precedes any
    # existing-PR base resolution, so a conflicting PR base is detected instead
    # of being adopted through the standalone resolver above.
    from autopilot import queries as pub

    assert pub.require_selected_base("origin/dev") == "origin/dev"
    for missing in (None, "", "   "):
        with pytest.raises(pub.QueryError, match="base-required"):
            pub.require_selected_base(missing)
