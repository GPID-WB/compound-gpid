"""Passive native-evidence source/generation checks, never native V1 proof.

Run: python -B -m pytest scripts/tests/test_native_evidence.py -q
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import cg_generate_targets as gen
import cg_validate_modules as modules
import cg_pr_preflight as preflight

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "plugins/cg-native-evidence.js",
    "plugin-support/cg-native-evidence/wire.mjs",
    "plugin-support/cg-native-evidence/transport.mjs",
    "plugin-support/cg-native-evidence/records.mjs",
    "plugin-support/cg-native-evidence/evidence.mjs",
)
TASKS = {
    "cg-autopilot.agent.md": {"*": "ask", "cg-workflow-stage": "allow"},
    "cg-workflow-stage.agent.md": {"*": "ask", "cg-code-quality": "allow", "cg-fix-problems": "allow", "cg-bootstrap-leaf": "allow"},
    "cg-fix-problems.agent.md": {"*": "ask", "general": "allow"},
}


def _run_node(files: tuple[str, ...]) -> None:
    """Run mandatory cases with zero internal skips; caller handles optional SDK absence."""
    node = shutil.which("node")
    if node is None:
        if os.environ.get("CG_NATIVE_EVIDENCE_REQUIRE_SDK") == "1":
            pytest.fail("Mandatory SDK CI requires Node")
        pytest.skip("Node is required for native-evidence offline tests")
    result = subprocess.run(
        [node, "--test", "--test-reporter=tap", *files],
        cwd=ROOT, capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "# skipped 0" in result.stdout, "Node cases were not all executed:\n" + result.stdout


def test_node_passive_evidence_contracts() -> None:
    """Run pure transport, identity and record cases without installing a framework."""
    _run_node(("scripts/tests/cg-native-evidence.test.mjs", "scripts/tests/cg-native-transport.test.mjs",
               "scripts/tests/cg-native-records.test.mjs"))


def test_installed_sdk_contract() -> None:
    """Report optional absence as pytest skip; incomplete or mandatory SDK absence fails."""
    explicit = os.environ.get("CG_NATIVE_EVIDENCE_SDK_CLIENT")
    client = Path(explicit) if explicit else ROOT / ".kilo/node_modules/@kilocode/sdk/dist/client.js"
    package = client.parent.parent
    if not package.exists() and not explicit and os.environ.get("CG_NATIVE_EVIDENCE_REQUIRE_SDK") != "1":
        pytest.skip("Optional native SDK package absent; actual-SDK evidence is incomplete")
    assert (package / "package.json").is_file() and client.is_file(), "Native SDK installation is missing or incomplete"
    _run_node(("scripts/tests/cg-native-sdk.test.mjs",))


def test_native_plugin_has_exact_kilo_only_ownership_and_generation() -> None:
    """Only the five named canonical resources may enter Kilo's plugin tree."""
    assets = gen.scan_canonical_assets(ROOT)
    plan = gen.build_generation_plan(ROOT, gen.load_target_mapping(ROOT), assets)
    outputs = [item for item in plan.entries if item.kind == "native-plugin"]
    assert {item.source for item in outputs} == {f".github/{name}" for name in FILES}
    registry = json.loads((ROOT / ".github/shared/module-registry.json").read_text(encoding="utf-8"))
    for item in outputs:
        assert item.target_id == "kilo"
        assert item.destination == item.source.replace(".github/", ".kilo/", 1)
        assert item.content == (ROOT / item.source).read_bytes()
        assert modules.resolve_asset_owner(registry, item.source) == "suite-cg"
        assert item.source in modules.canonical_assets(ROOT)
        assert len(item.content.splitlines()) < 300
    cr = gen.scan_canonical_assets(ROOT, active_suites=("cr",))
    assert cr.get("native_plugins", []) == []


def test_bootstrap_task_baselines_are_non_denying_with_exact_allows() -> None:
    """Approved ask baselines keep exact closed allow sets; leaf has no Task key."""
    kilo = next(t for t in gen.load_target_mapping(ROOT)["targets"] if t["id"] == "kilo")
    for name, task in TASKS.items():
        permission = kilo["assetMetadata"][name]["permission"]
        assert gen._yaml_scalar(permission["task"]) == gen._yaml_scalar(task)
        if name == "cg-fix-problems.agent.md":
            assert permission == {"task": task}
        else:
            assert permission == {"*": "deny", "read": "allow", "glob": "allow", "grep": "allow",
                                  "cg_native_identity": "ask", "cg_native_evidence": "ask", "task": task}
    assert "general.agent.md" not in kilo["assetMetadata"]
    leaf = kilo["assetMetadata"]["cg-bootstrap-leaf.agent.md"]
    assert leaf["mode"] == "subagent"
    assert "task" not in leaf["permission"]
    assert leaf["permission"]["cg_native_identity"] == "ask"
    assert leaf["permission"]["bash"] == {
        "*": "deny", "git branch --show-current*": "allow",
        "git rev-parse*": "allow", "git status --porcelain*": "allow"}


def test_passive_source_has_no_execution_hooks_or_mutating_api() -> None:
    """Keep native admission, Git execution and general-tool guards out of scope."""
    content = "\n".join((ROOT / f".github/{name}").read_text(encoding="utf-8") for name in FILES)
    for forbidden in ("tool.execute.before", "permission.ask", "session.create(", "session.prompt(",
                      "session.update(", "client.config", "child_process", "Bun.$", "process.env", "._client"):
        assert forbidden not in content
    assert "always: []" in content
    assert "qualification: 'unverified'" in content


def test_final_recovery_ci_and_lf_contracts() -> None:
    """Touched tests have one central registration and a secure, mandatory SDK CI fixture."""
    import yaml

    for name in ("test_native_evidence.py", "test_autopilot_contracts.py", "test_autopilot_runtime.py"):
        assert preflight.NATIVE_PYTEST_FILES.count(f"scripts/tests/{name}") == 1
    workflow = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["native-targets"]
    assert job["env"]["CG_NATIVE_EVIDENCE_REQUIRE_SDK"] == "1"
    assert "native-sdk/node_modules/@kilocode/sdk/dist/client.js" in job["env"]["CG_NATIVE_EVIDENCE_SDK_CLIENT"]
    assert any(step.get("with", {}).get("node-version") == "24.x" for step in job["steps"])
    assert any("npm ci --prefix scripts/tests/native-sdk --ignore-scripts" in step.get("run", "") for step in job["steps"])
    manifest = json.loads((ROOT / "scripts/tests/native-sdk/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "scripts/tests/native-sdk/package-lock.json").read_text(encoding="utf-8"))
    assert manifest["dependencies"] == {"@kilocode/sdk": "7.6.2"}
    assert lock["packages"][""]["dependencies"] == manifest["dependencies"]
    assert len(lock["packages"]) == 8
    for name, package in lock["packages"].items():
        if not name:
            continue
        assert package["resolved"].startswith("https://registry.npmjs.org/")
        assert package["integrity"].startswith("sha512-")
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for pattern in (".github/plugins/*.js", ".github/plugin-support/cg-native-evidence/*.mjs",
                    ".kilo/plugins/*.js", ".kilo/plugin-support/cg-native-evidence/*.mjs"):
        assert f"{pattern} text eol=lf" in attributes


def test_plugin_sources_and_generated_files_are_lf() -> None:
    """Verify bytes and Git checkout attributes without staging or renormalization."""
    paths = [f"{root}/{name}" for root in (".github", ".kilo") for name in FILES]
    for name in paths:
        assert b"\r" not in (ROOT / name).read_bytes()
    result = subprocess.run(["git", "check-attr", "text", "eol", "--", *paths],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    for name in paths:
        assert f"{name}: text: set" in result.stdout
        assert f"{name}: eol: lf" in result.stdout


def test_optional_sdk_absence_is_an_explicit_pytest_skip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An absent optional package is visible, not a green wrapper around SDK skips."""
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    monkeypatch.delenv("CG_NATIVE_EVIDENCE_SDK_CLIENT", raising=False)
    monkeypatch.delenv("CG_NATIVE_EVIDENCE_REQUIRE_SDK", raising=False)
    with pytest.raises(pytest.skip.Exception, match="actual-SDK evidence is incomplete"):
        test_installed_sdk_contract()


def test_incomplete_or_required_sdk_never_skips(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Both missing required SDK and partial installation are failures before subprocess use."""
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    monkeypatch.delenv("CG_NATIVE_EVIDENCE_SDK_CLIENT", raising=False)
    monkeypatch.setenv("CG_NATIVE_EVIDENCE_REQUIRE_SDK", "1")
    with pytest.raises(AssertionError, match="missing or incomplete"):
        test_installed_sdk_contract()
    (tmp_path / ".kilo/node_modules/@kilocode/sdk").mkdir(parents=True)
    monkeypatch.delenv("CG_NATIVE_EVIDENCE_REQUIRE_SDK")
    with pytest.raises(AssertionError, match="missing or incomplete"):
        test_installed_sdk_contract()
