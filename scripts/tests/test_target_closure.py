"""Phase 5 tests for target-local runtime dependency closure."""
from __future__ import annotations

import copy
import json
import re
import shutil
from pathlib import Path
from typing import Optional

import pytest

import cg_generate_targets as gen


REPO_ROOT = Path(__file__).resolve().parents[2]
NATIVE_TARGETS = ("claude-code", "codex", "opencode", "kilo")
CANONICAL_RUNTIME_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_.-])\.github/(?:prompts|skills|agents|instructions|shared)/"
    r"[^\s`'\"<>)]*"
)


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _mapping_target(target_id: str, *, custom_paths: bool = False) -> dict:
    mapping = json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )
    target = copy.deepcopy(next(item for item in mapping["targets"] if item["id"] == target_id))
    if not custom_paths:
        return target

    root = f".native-{target_id}"
    target["generatedTreePath"] = root
    target["outputPaths"] = {
        "commands": f"{root}/dispatch",
        "skills": f"{root}/capabilities",
        "agents": f"{root}/delegates",
        "instructions": f"{root}/language-rules",
        "shared": f"{root}/contracts",
        "rootAdapter": f"{root}/ROOT.md",
    }
    if target_id == "opencode":
        target["outputPaths"]["config"] = f"{root}/runtime.json"
    target.pop("installUnits", None)
    return target


def _canonical_fixture(root: Path, command_body: Optional[str] = None) -> None:
    command_body = command_body or """
Load `.github/prompts/setup-templates.md` and
`.github/prompts/resume-templates.md`.
Load `.github/skills/cg-skill-demo/SKILL.md` and dispatch
`@cg-demo` from `.github/agents/cg-demo.agent.md`.
Follow `.github/instructions/python.instructions.md` and
`.github/shared/completion.contract.md`.
"""
    _write(
        root,
        ".github/prompts/cg-demo.prompt.md",
        f"---\ndescription: Demo command\n---\n\n{command_body.strip()}\n",
    )
    _write(root, ".github/prompts/setup-templates.md", "# Setup templates\n")
    _write(root, ".github/prompts/resume-templates.md", "# Resume templates\n")
    _write(
        root,
        ".github/agents/cg-demo.agent.md",
        "---\ndescription: Demo agent\n---\n\n"
        "Use `.github/skills/cg-skill-demo/SKILL.md` and "
        "`.github/shared/context-loading.contract.md`.\n",
    )
    _write(
        root,
        ".github/skills/cg-skill-demo/SKILL.md",
        "---\nname: cg-skill-demo\ndescription: Demo skill\n---\n\n"
        "Follow `.github/instructions/python.instructions.md`.\n",
    )
    _write(
        root,
        ".github/instructions/python.instructions.md",
        "---\ndescription: Python rules\napplyTo: '**/*.py'\n---\n\n"
        "Use `.github/shared/context-loading.contract.md`.\n",
    )
    _write(root, ".github/shared/completion.contract.md", "# Completion contract\n")
    _write(root, ".github/shared/context-loading.contract.md", "# Context contract\n")


def _plan(root: Path, target: dict) -> gen.GenerationPlan:
    assets = gen.scan_canonical_assets(root)
    mapping = {"schemaVersion": 1, "description": "closure fixture", "targets": [target]}
    return gen.build_generation_plan(root, mapping, assets)


def _entry_map(plan: gen.GenerationPlan, target_id: str) -> dict[str, gen.OutputEntry]:
    return {entry.destination: entry for entry in plan.by_target[target_id].entries}


def _materialize_isolated(
    root: Path, plan: gen.GenerationPlan, target_id: str
) -> Path:
    isolated = root / "consumer"
    isolated.mkdir()
    _write(isolated, "README.md", "# Ordinary consumer project\n")
    for entry in plan.by_target[target_id].entries:
        destination = isolated / entry.destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(entry.content)
    assert not (isolated / ".github").exists()
    return isolated


def _assert_runtime_references_resolve(isolated: Path, target: dict) -> None:
    roots = tuple(target["outputPaths"][name] for name in (
        "commands", "skills", "agents", "instructions", "shared"
    ))
    markdown_entries = [
        path for root in roots if (isolated / root).exists()
        for path in (isolated / root).rglob("*")
        if path.is_file() and path.suffix == ".md"
    ]
    assert markdown_entries
    for path in markdown_entries:
        text = path.read_text(encoding="utf-8")
        assert not CANONICAL_RUNTIME_REFERENCE.findall(text), path.relative_to(isolated)

    expected = (
        f"{target['outputPaths']['commands']}/cg-demo.md",
        f"{target['outputPaths']['commands']}/setup-templates.md",
        f"{target['outputPaths']['commands']}/resume-templates.md",
        f"{target['outputPaths']['skills']}/cg-skill-demo/SKILL.md",
        f"{target['outputPaths']['instructions']}/python.instructions.md",
        f"{target['outputPaths']['shared']}/completion.contract.md",
        f"{target['outputPaths']['shared']}/context-loading.contract.md",
    )
    for relative in expected:
        assert (isolated / relative).is_file(), relative

    agent_suffix = ".toml" if target["id"] == "codex" else ".md"
    assert (isolated / target["outputPaths"]["agents"] / f"cg-demo{agent_suffix}").is_file()


@pytest.mark.parametrize("target_id", NATIVE_TARGETS)
def test_isolated_target_has_deterministic_static_runtime_closure(
    tmp_path: Path, target_id: str
) -> None:
    source = tmp_path / "source"
    _canonical_fixture(source)
    target = _mapping_target(target_id)

    first = _plan(source, target)
    second = _plan(source, target)
    assert first.by_target[target_id].entries == second.by_target[target_id].entries

    isolated = _materialize_isolated(tmp_path, first, target_id)
    _assert_runtime_references_resolve(isolated, target)


@pytest.mark.parametrize("target_id", NATIVE_TARGETS)
def test_known_canonical_runtime_roots_rewrite_to_custom_output_paths(
    tmp_path: Path, target_id: str
) -> None:
    source = tmp_path / "source"
    _canonical_fixture(source)
    target = _mapping_target(target_id, custom_paths=True)
    plan = _plan(source, target)
    isolated = _materialize_isolated(tmp_path, plan, target_id)

    _assert_runtime_references_resolve(isolated, target)
    all_text = "\n".join(
        entry.content.decode("utf-8")
        for entry in plan.by_target[target_id].entries
        if entry.destination.endswith((".md", ".toml", ".json"))
    )
    for root_name in ("commands", "skills", "agents", "instructions", "shared"):
        assert target["outputPaths"][root_name] in all_text
    assert target["generatedTreePath"] + "/agents/" not in all_text


def test_codex_agents_use_configured_subagents_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _canonical_fixture(source)
    target = _mapping_target("codex")
    entries = _entry_map(_plan(source, target), "codex")

    assert ".agents/subagents/cg-demo.toml" in entries
    assert ".agents/agents/cg-demo.toml" not in entries


@pytest.mark.parametrize("target_id", NATIVE_TARGETS)
def test_consumer_github_paths_and_prose_are_not_rewritten(
    tmp_path: Path, target_id: str
) -> None:
    consumer_text = """
Create `.github/workflows/tests.yml` in the consumer project.
The consumer project's `.github/` directory may be absent.
Do not edit `.github/CODEOWNERS`.
Load `.github/shared/completion.contract.md`.
"""
    source = tmp_path / "source"
    _canonical_fixture(source, consumer_text)
    target = _mapping_target(target_id)
    command = _entry_map(_plan(source, target), target_id)[
        f"{target['outputPaths']['commands']}/cg-demo.md"
    ].content.decode("utf-8")

    assert ".github/workflows/tests.yml" in command
    assert "project's `.github/` directory" in command
    assert ".github/CODEOWNERS" in command
    assert ".github/shared/completion.contract.md" not in command
    assert f"{target['outputPaths']['shared']}/completion.contract.md" in command


def test_unresolved_required_canonical_runtime_dependency_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _canonical_fixture(source, "Load `.github/shared/missing.contract.md`.")

    with pytest.raises(ValueError, match=r"missing\.contract\.md|unresolved|dependency"):
        _plan(source, _mapping_target("claude-code"))


@pytest.mark.parametrize(
    "unsafe_reference",
    (
        ".github/shared/../../outside.md",
        ".github/prompts/%2e%2e/secrets.md",
        ".github/skills/C:/escape/SKILL.md",
    ),
)
def test_unsafe_canonical_runtime_rewrite_is_rejected(
    tmp_path: Path, unsafe_reference: str
) -> None:
    source = tmp_path / "source"
    _canonical_fixture(source, f"Load `{unsafe_reference}`.")

    with pytest.raises((gen.PathSafetyError, ValueError), match=r"unsafe|escape|traversal|dependency"):
        _plan(source, _mapping_target("opencode"))


def _cli_evidence(target_id: str) -> dict[str, str]:
    executable = {"claude-code": "claude", "codex": "codex", "opencode": "opencode", "kilo": "kilo"}[target_id]
    path = shutil.which(executable)
    return {
        "target": target_id,
        "staticClosure": "required",
        "cli": executable,
        "cliEvidence": "available-not-run" if path else "unavailable",
    }


@pytest.mark.parametrize("target_id", NATIVE_TARGETS)
def test_cli_availability_reporting_is_separate_from_required_static_closure(
    monkeypatch: pytest.MonkeyPatch, target_id: str
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    unavailable = _cli_evidence(target_id)
    monkeypatch.setattr(shutil, "which", lambda name: f"/tools/{name}")
    available = _cli_evidence(target_id)

    assert unavailable["staticClosure"] == available["staticClosure"] == "required"
    assert unavailable["cliEvidence"] == "unavailable"
    assert available["cliEvidence"] == "available-not-run"
    assert "skip" not in unavailable.values()
