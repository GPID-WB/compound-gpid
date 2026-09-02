"""Tests for the private skill-management dispatcher and write context."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

import pytest

import cg_skill
from skill_management import context
from skill_management.planning import OperationOutcome


REPO_ROOT = Path(cg_skill.__file__).resolve().parents[1]


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _repository(
    tmp_path: Path,
    name: str = "repo",
    *,
    branch: str = "feature/skill-management",
    origin: str = context.CANONICAL_SOURCE_ORIGIN,
) -> Path:
    root = tmp_path / name
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "tests@example.test")
    _git(root, "config", "user.name", "Tests")
    _git(root, "remote", "add", "origin", origin)
    _git(root, "checkout", "-b", branch)
    _git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    registry = {
        "schemaVersion": 2,
        "description": "fixture",
        "capabilities": [],
        "modules": [
            {
                "id": "kernel",
                "layer": "kernel",
                "displayName": "Kernel",
                "description": "fixture",
                "dependsOn": [],
                "ownedAssets": [".github/shared/module-registry.json"],
            },
            {
                "id": "cap-skill-management",
                "layer": "capability",
                "displayName": "Skill management",
                "description": "fixture",
                "dependsOn": ["kernel"],
                "ownedAssets": [
                    ".github/skills/cg-skill-management/",
                    ".github/shared/skill-management/",
                ],
            },
            {
                "id": "suite-cg",
                "layer": "suite",
                "displayName": "CG",
                "description": "fixture",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
        ],
    }
    _write(root / ".github/shared/module-registry.json", json.dumps(registry))
    _write(root / "compound-gpid.md", "# Fixture\n")
    for name in (
        "operation-descriptor-v1.schema.json",
        "request-v1.schema.json",
        "result-v1.schema.json",
    ):
        source = REPO_ROOT / ".github/shared/skill-management/contracts" / name
        _write(
            root / ".github/shared/skill-management/contracts" / name,
            source.read_text(encoding="utf-8"),
        )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


def _consumer_repository(tmp_path: Path, name: str = "consumer") -> Path:
    """Create a consumer Git project without canonical installation assets."""
    root = tmp_path / name
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "tests@example.test")
    _git(root, "config", "user.name", "Tests")
    _git(root, "checkout", "-b", "feature/consumer")
    _write(root / "compound-gpid.md", "# Consumer fixture\n")
    _write(
        root / "compound-gpid.local.md",
        '---\nlanguage: "python"\nsuites: [cg]\n---\n# Consumer config\n',
    )
    _git(root, "add", ".")
    _git(root, "commit", "-m", "consumer fixture")
    return root


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    return path


def _descriptor(
    root: Path,
    operation: str = "echo",
    *,
    roles: tuple[str, ...] = ("consumer",),
    handler: str = "skill_management.operations.echo:handle",
) -> None:
    contract_path = (
        root / f".github/shared/skill-management/contracts/{operation}-v1.schema.json"
    )
    operation_contract = {
        "$schema": "compound-gpid-schema-subset-v1",
        "$id": f"cg-skill-{operation}-arguments-v1",
        "$defs": {
            "arguments": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
                "additionalProperties": False,
            },
            "resultData": {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
        },
    }
    _write(contract_path, json.dumps(operation_contract))
    _write(
        root / f".github/skills/cg-skill-management/workflows/{operation}.md",
        "# Fixture workflow\n",
    )
    _write(
        root / f"docs/skills/management/commands/{operation}.md",
        "# Fixture command\n",
    )
    _write(root / f"scripts/tests/test_skill_management_{operation}.py", "# fixture\n")
    _write(
        root / f"scripts/skill_management/operations/{operation}.py",
        "# fixture operation\n",
    )
    descriptor = {
        "schema": "cg-skill-operation-descriptor-v1",
        "operation": operation,
        "version": 1,
        "state": "active",
        "roles": list(roles),
        "phases": ["read", "apply"],
        "handler": handler,
        "contract": contract_path.relative_to(root).as_posix(),
        "workflow": (
            f".github/skills/cg-skill-management/workflows/{operation}.md"
        ),
        "documentation": f"docs/skills/management/commands/{operation}.md",
        "tests": [f"scripts/tests/test_skill_management_{operation}.py"],
    }
    _write(
        root / f".github/shared/skill-management/operations/{operation}.json",
        json.dumps(descriptor),
    )


def _fake_loader(
    calls: list[str],
    root: Path,
    handler: Optional[Callable[..., OperationOutcome]] = None,
) -> Callable[..., object]:
    def default_handler(**_: object) -> OperationOutcome:
        return OperationOutcome(data={"value": "ok"})

    def load_handler(
        source_root: Path,
        operation: str,
        handler_spec: Optional[str] = None,
    ) -> object:
        assert source_root == root
        if handler_spec is not None:
            assert handler_spec.startswith("skill_management.operations.")
        calls.append(f"skill_management.operations.{operation}")
        return handler or default_handler

    return load_handler


def _isolated_dispatch_runtime(tmp_path: Path) -> Path:
    """Create one runnable dispatcher installation below a fixture root."""
    root = _repository(tmp_path)
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    shutil.copy2(REPO_ROOT / "scripts/cg_skill.py", scripts / "cg_skill.py")
    shutil.copy2(REPO_ROOT / "scripts/secure_fs.py", scripts / "secure_fs.py")
    shutil.copytree(
        REPO_ROOT / "scripts/skill_management",
        scripts / "skill_management",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    _descriptor(root)
    return root


def _handler_importing_helper(root: Path, marker: Path, helper: str) -> None:
    _write(
        root / "scripts/skill_management/operations/echo.py",
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('handler', encoding='utf-8')\n"
        f"from skill_management.operations.{helper} import VALUE\n"
        "from skill_management.planning import OperationOutcome\n"
        "def handle(**kwargs):\n"
        "    return OperationOutcome(data={'value': VALUE})\n",
    )


def _run_isolated_dispatch(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts/cg_skill.py"),
            "--project-root",
            str(root),
            "--source-root",
            str(root),
            "--format",
            "json",
            "echo",
            "--message",
            "hello",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _run_preloaded_dispatch(
    root: Path, module_name: str, module_path: Path
) -> subprocess.CompletedProcess[str]:
    arguments = [
        "--project-root",
        str(root),
        "--source-root",
        str(root),
        "--format",
        "json",
        "echo",
        "--message",
        "hello",
    ]
    program = (
        "import runpy, sys, types\n"
        f"sys.path.insert(0, {str(root / 'scripts')!r})\n"
        f"module = types.ModuleType({module_name!r})\n"
        f"module.__file__ = {str(module_path)!r}\n"
        f"sys.modules[{module_name!r}] = module\n"
        f"sys.argv = [{str(root / 'scripts/cg_skill.py')!r}, *{arguments!r}]\n"
        f"runpy.run_path({str(root / 'scripts/cg_skill.py')!r}, run_name='__main__')\n"
    )
    return subprocess.run(
        [sys.executable, "-c", program],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _installed_wrapper_command() -> list[str]:
    """Return the platform command for the installed public wrapper."""
    if os.name == "nt":
        return ["cmd.exe", "/d", "/c", str(REPO_ROOT / "bin/cg-skill.cmd")]
    return [str(REPO_ROOT / "bin/cg-skill")]


def test_unknown_operation_returns_usage_without_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))

    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "missing"],
        invocation_path=root,
        runtime_root=root,
    )

    assert exit_code == 2
    assert calls == []
    assert "operation.unknown" in capsys.readouterr().err


@pytest.mark.parametrize("operation", ["../echo", "operations/echo", r"operations\echo", "."])
def test_path_like_operation_is_rejected(
    tmp_path: Path, operation: str, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), operation],
        invocation_path=root,
        runtime_root=root,
    )
    assert exit_code == 2
    assert "operation.invalid" in capsys.readouterr().err


def test_malformed_descriptor_fails_before_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)
    descriptor = root / ".github/shared/skill-management/operations/echo.json"
    descriptor.write_text("{}", encoding="utf-8")
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))

    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo"],
        invocation_path=root,
        runtime_root=root,
    )

    assert exit_code == 3
    assert calls == []


def test_handler_outside_allowed_package_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    _descriptor(root, handler="skill_management.operations.other:handle")
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))

    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo"],
        invocation_path=root,
        runtime_root=root,
    )

    assert exit_code == 3
    assert calls == []


def test_operation_contract_identity_must_match_descriptor_operation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)
    source = root / ".github/shared/skill-management/contracts/echo-v1.schema.json"
    wrong = root / ".github/shared/skill-management/contracts/other-v1.schema.json"
    wrong.write_bytes(source.read_bytes())
    descriptor_path = root / ".github/shared/skill-management/operations/echo.json"
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["contract"] = wrong.relative_to(root).as_posix()
    descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))
    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo"],
        invocation_path=root,
        runtime_root=root,
    )
    assert exit_code == 3
    assert calls == []


def test_installed_wrapper_help_uses_trusted_source_for_consumer_project(
    tmp_path: Path,
) -> None:
    project = _consumer_repository(tmp_path)

    completed = subprocess.run(
        [
            *_installed_wrapper_command(),
            "--project-root",
            ".",
            "--format",
            "json",
            "help",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0, completed.stderr
    assert payload["ok"] is True
    assert payload["operation"] == "help"
    assert payload["role"] == "consumer"
    assert "help" in {
        record["operation"] for record in payload["data"]["operations"]
    }
    assert not (project / ".github").exists()


def test_explicit_source_root_still_must_match_runtime_root(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    runtime = _repository(tmp_path, "runtime")
    project = _consumer_repository(tmp_path)

    exit_code = cg_skill.main(
        [
            "--project-root",
            str(project),
            "--source-root",
            str(project),
            "--format",
            "json",
            "help",
        ],
        invocation_path=project,
        runtime_root=runtime,
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 3
    assert payload["findings"][0]["code"] == "context.untrusted-source"


@pytest.mark.usefixtures("require_symlink_support")
def test_linked_helper_is_rejected_before_any_module_side_effect(
    tmp_path: Path,
) -> None:
    root = _isolated_dispatch_runtime(tmp_path)
    handler_marker = tmp_path / "handler-executed.txt"
    helper_marker = tmp_path / "helper-executed.txt"
    helper_name = "_dispatch_linked_helper"
    _handler_importing_helper(root, handler_marker, helper_name)
    outside = tmp_path / "outside-linked-helper.py"
    outside.write_text(
        "from pathlib import Path\n"
        f"Path({str(helper_marker)!r}).write_text('helper', encoding='utf-8')\n"
        "VALUE = 'untrusted'\n",
        encoding="utf-8",
    )
    helper_path = root / f"scripts/skill_management/operations/{helper_name}.py"
    helper_path.symlink_to(outside)

    completed = _run_isolated_dispatch(root)
    payload = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert payload["findings"][0]["code"] == "internal.dispatch"
    assert not handler_marker.exists()
    assert not helper_marker.exists()


def test_hard_linked_helper_is_rejected_before_any_module_side_effect(
    tmp_path: Path,
) -> None:
    root = _isolated_dispatch_runtime(tmp_path)
    handler_marker = tmp_path / "handler-executed.txt"
    helper_marker = tmp_path / "helper-executed.txt"
    helper_name = "_dispatch_hardlink_helper"
    _handler_importing_helper(root, handler_marker, helper_name)
    outside = tmp_path / "outside-hardlink-helper.py"
    outside.write_text(
        "from pathlib import Path\n"
        f"Path({str(helper_marker)!r}).write_text('helper', encoding='utf-8')\n"
        "VALUE = 'untrusted'\n",
        encoding="utf-8",
    )
    helper_path = root / f"scripts/skill_management/operations/{helper_name}.py"
    try:
        os.link(outside, helper_path)
    except OSError:
        pytest.skip("hard-link creation is unavailable")

    completed = _run_isolated_dispatch(root)
    payload = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert payload["findings"][0]["code"] == "internal.dispatch"
    assert not handler_marker.exists()
    assert not helper_marker.exists()


def test_wrong_root_preloaded_helper_is_rejected_before_disk_code_executes(
    tmp_path: Path,
) -> None:
    root = _isolated_dispatch_runtime(tmp_path)
    handler_marker = tmp_path / "handler-executed.txt"
    helper_marker = tmp_path / "helper-executed.txt"
    helper_name = "_dispatch_preloaded_helper"
    module_name = f"skill_management.operations.{helper_name}"
    _handler_importing_helper(root, handler_marker, helper_name)
    helper_path = root / f"scripts/skill_management/operations/{helper_name}.py"
    helper_path.write_text(
        "from pathlib import Path\n"
        f"Path({str(helper_marker)!r}).write_text('helper', encoding='utf-8')\n"
        "VALUE = 'untrusted'\n",
        encoding="utf-8",
    )

    completed = _run_preloaded_dispatch(
        root,
        module_name,
        tmp_path / "wrong-root" / f"{helper_name}.py",
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert payload["findings"][0]["code"] == "internal.dispatch"
    assert not handler_marker.exists()
    assert not helper_marker.exists()


def test_helper_swap_after_capture_executes_only_captured_bytes(tmp_path: Path) -> None:
    root = _isolated_dispatch_runtime(tmp_path)
    helper_marker = tmp_path / "swapped-helper-executed.txt"
    helper_name = "_dispatch_swapped_helper"
    helper_relative = f"scripts/skill_management/operations/{helper_name}.py"
    _write(
        root / "scripts/skill_management/operations/echo.py",
        f"from skill_management.operations.{helper_name} import VALUE\n"
        "from skill_management.planning import OperationOutcome\n"
        "def handle(**kwargs):\n"
        "    return OperationOutcome(data={'value': VALUE})\n",
    )
    _write(root / helper_relative, "VALUE = 'captured'\n")
    arguments = [
        "--project-root",
        str(root),
        "--source-root",
        str(root),
        "--format",
        "json",
        "echo",
        "--message",
        "hello",
    ]
    malicious = (
        "from pathlib import Path\n"
        f"Path({str(helper_marker)!r}).write_text('helper', encoding='utf-8')\n"
        "VALUE = 'swapped'\n"
    )
    program = (
        "import runpy, sys\n"
        "from pathlib import Path\n"
        f"sys.path.insert(0, {str(root / 'scripts')!r})\n"
        "import secure_fs\n"
        "original = secure_fs.secure_read_bytes\n"
        "def swapping(root_path, relative, **kwargs):\n"
        "    content = original(root_path, relative, **kwargs)\n"
        f"    if relative.as_posix() == {helper_relative!r}:\n"
        f"        Path(root_path, *relative.parts).write_text({malicious!r}, encoding='utf-8')\n"
        "    return content\n"
        "secure_fs.secure_read_bytes = swapping\n"
        f"sys.argv = [{str(root / 'scripts/cg_skill.py')!r}, *{arguments!r}]\n"
        f"runpy.run_path({str(root / 'scripts/cg_skill.py')!r}, run_name='__main__')\n"
    )

    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert payload["data"] == {"value": "captured"}
    assert not helper_marker.exists()


def test_unselected_operation_source_remains_lazy(tmp_path: Path) -> None:
    root = _isolated_dispatch_runtime(tmp_path)
    marker = tmp_path / "unselected-executed.txt"
    _write(
        root / "scripts/skill_management/operations/echo.py",
        "from skill_management.planning import OperationOutcome\n"
        "def handle(**kwargs):\n"
        "    return OperationOutcome(data={'value': 'selected'})\n",
    )
    _write(
        root / "scripts/skill_management/operations/unselected.py",
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('unselected', encoding='utf-8')\n",
    )

    completed = _run_isolated_dispatch(root)
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert payload["data"] == {"value": "selected"}
    assert not marker.exists()


def test_selected_descriptor_causes_exactly_one_lazy_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    _descriptor(root, "echo")
    _descriptor(root, "other")
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))

    exit_code = cg_skill.main(
        [
            "--project-root",
            str(root),
            "--source-root",
            str(root),
            "--format",
            "json",
            "echo",
            "--message",
            "hello",
        ],
        invocation_path=root,
        runtime_root=root,
    )

    assert exit_code == 0
    assert calls == ["skill_management.operations.echo"]
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {"value": "ok"}
    assert payload["role"] == "consumer"


def test_human_success_output_includes_operation_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)
    monkeypatch.setattr(
        cg_skill,
        "_load_handler",
        _fake_loader([], root),
    )
    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo", "--message", "hello"],
        invocation_path=root,
        runtime_root=root,
    )
    assert exit_code == 0
    assert 'Data: {"value":"ok"}' in capsys.readouterr().out


def test_apply_digest_selects_apply_phase_and_is_removed_from_operation_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)
    captured_request = {}

    def handler(**kwargs: object) -> OperationOutcome:
        captured_request.update(kwargs["request"])  # type: ignore[arg-type]
        return OperationOutcome(data={"value": "applied"})

    monkeypatch.setattr(
        cg_skill,
        "_load_handler",
        _fake_loader([], root, handler),
    )
    digest = "a" * 64
    exit_code = cg_skill.main(
        [
            "--project-root",
            str(root),
            "--source-root",
            str(root),
            "--format",
            "json",
            "echo",
            "--message",
            "hello",
            "--apply",
            digest,
        ],
        invocation_path=root,
        runtime_root=root,
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["phase"] == "apply"
    assert captured_request["planDigest"] == digest
    assert captured_request["arguments"] == {"message": "hello"}


def test_handler_result_data_is_checked_against_operation_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)

    def handler(**_: object) -> OperationOutcome:
        return OperationOutcome(data={"unexpected": True})

    monkeypatch.setattr(
        cg_skill,
        "_load_handler",
        _fake_loader([], root, handler),
    )
    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo", "--message", "hello"],
        invocation_path=root,
        runtime_root=root,
    )
    assert exit_code == 1
    assert "internal.dispatch" in capsys.readouterr().err


def test_unexpected_handler_exception_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)

    def handler(**_: object) -> OperationOutcome:
        raise RuntimeError("secret-token-value")

    monkeypatch.setattr(
        cg_skill,
        "_load_handler",
        _fake_loader([], root, handler),
    )
    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo", "--message", "hello"],
        invocation_path=root,
        runtime_root=root,
    )
    rendered = capsys.readouterr().err
    assert exit_code == 1
    assert "internal.dispatch" in rendered
    assert "secret-token-value" not in rendered


def test_consumer_is_safe_default_for_noncanonical_checkout(tmp_path: Path) -> None:
    root = _repository(tmp_path, origin="https://github.com/example/not-canonical.git")
    discovered = context.discover_context(root, root, invocation_path=root)
    assert discovered.role == "consumer"
    assert any("origin" in reason.lower() for reason in discovered.write_context_errors)


def test_forged_origin_refs_and_registry_cannot_receive_maintainer_role(
    tmp_path: Path,
) -> None:
    root = _repository(tmp_path)
    assert context.discover_context(root, root, invocation_path=root).role == "consumer"
    trusted = context.discover_context(
        root,
        root,
        invocation_path=root,
        trusted_source_root=root,
    )
    assert trusted.role == "consumer"
    assert any(
        "trust anchor" in reason.lower()
        for reason in trusted.write_context_errors
    )


def test_equal_roots_use_one_git_root_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    original = context._git_root  # pylint: disable=protected-access
    calls = []

    def tracked(path: Path) -> Optional[Path]:
        calls.append(path)
        return original(path)

    monkeypatch.setattr(context, "_git_root", tracked)
    context.discover_context(
        root,
        root,
        invocation_path=root,
        trusted_source_root=root,
    )
    assert calls == [root.resolve()]


def test_linked_valid_global_source_remains_consumer(tmp_path: Path) -> None:
    project = _repository(
        tmp_path,
        "project",
        origin="https://github.com/example/consumer.git",
    )
    source = _repository(tmp_path, "source")
    discovered = context.discover_context(
        project,
        source,
        invocation_path=project,
        trusted_source_root=source,
    )
    assert discovered.project_root == project.resolve()
    assert discovered.source_root == source.resolve()
    assert discovered.role == "consumer"
    assert any("same" in reason.lower() for reason in discovered.write_context_errors)


@pytest.mark.parametrize("branch", ["main", "release/2.0", "protected/security"])
def test_default_and_protected_branches_cannot_be_maintainer(
    tmp_path: Path, branch: str
) -> None:
    root = _repository(tmp_path, branch=branch)
    discovered = context.discover_context(root, root, invocation_path=root)
    assert discovered.role == "consumer"
    with pytest.raises(context.WriteContextError):
        context.require_maintainer_write_context(discovered)


def test_detached_head_cannot_be_maintainer(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    _write(root / "tracked.txt", "fixture\n")
    _git(root, "add", "tracked.txt")
    _git(root, "commit", "-m", "fixture")
    commit = _git(root, "rev-parse", "HEAD")
    _git(root, "checkout", "--detach", commit)
    discovered = context.discover_context(root, root, invocation_path=root)
    assert discovered.role == "consumer"
    assert any("detached" in reason.lower() for reason in discovered.write_context_errors)


def test_spoofed_canonical_files_do_not_elevate_role(tmp_path: Path) -> None:
    root = _repository(tmp_path, origin="https://github.com/example/spoof.git")
    discovered = context.discover_context(root, root, invocation_path=root)
    assert discovered.role == "consumer"


def test_mismatched_invocation_project_or_source_roots_do_not_elevate(
    tmp_path: Path,
) -> None:
    canonical = _repository(tmp_path, "canonical")
    other = _repository(tmp_path, "other")
    assert context.discover_context(
        canonical, canonical, invocation_path=other
    ).role == "consumer"
    assert context.discover_context(
        canonical, other, invocation_path=canonical
    ).role == "consumer"


def test_wrong_origin_blocks_maintainer_even_with_a_feature_branch(tmp_path: Path) -> None:
    root = _repository(tmp_path, origin="https://github.com/example/wrong.git")
    discovered = context.discover_context(root, root, invocation_path=root)
    with pytest.raises(context.WriteContextError, match="origin"):
        context.require_maintainer_write_context(discovered)


def test_role_override_argument_is_rejected_without_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    _descriptor(root)
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))
    exit_code = cg_skill.main(
        [
            "--project-root",
            str(root),
            "--source-root",
            str(root),
            "echo",
            "--role",
            "maintainer",
        ],
        invocation_path=root,
        runtime_root=root,
    )
    assert exit_code == 4
    assert calls == []
    assert "role.override" in capsys.readouterr().err


def test_maintainer_descriptor_fails_on_consumer_context_before_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path, origin="https://github.com/example/consumer.git")
    _descriptor(root, roles=("maintainer",))
    calls: list[str] = []
    monkeypatch.setattr(cg_skill, "_load_handler", _fake_loader(calls, root))
    exit_code = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "echo"],
        invocation_path=root,
        runtime_root=root,
    )
    assert exit_code == 4
    assert calls == []


def test_json_and_human_errors_render_the_same_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = _repository(tmp_path)
    json_exit = cg_skill.main(
        [
            "--project-root",
            str(root),
            "--source-root",
            str(root),
            "--format",
            "json",
            "missing",
        ],
        invocation_path=root,
        runtime_root=root,
    )
    json_payload = json.loads(capsys.readouterr().out)

    human_exit = cg_skill.main(
        ["--project-root", str(root), "--source-root", str(root), "missing"],
        invocation_path=root,
        runtime_root=root,
    )
    human_error = capsys.readouterr().err

    assert json_exit == human_exit == 2
    assert json_payload["findings"][0]["code"] == "operation.unknown"
    assert "operation.unknown" in human_error


def test_private_dispatcher_file_contains_no_lifecycle_operations() -> None:
    source = Path(cg_skill.__file__).read_text(encoding="utf-8")
    forbidden = (
        "def activate",
        "def deactivate",
        "def import_skill",
        "def remove",
        "def update_registry",
    )
    assert not any(marker in source for marker in forbidden)
