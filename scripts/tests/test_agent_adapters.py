"""Regression tests for cross-agent adapter package files."""
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


ADAPTER_FILES = [
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "adapters/codex/AGENTS.md",
    REPO_ROOT / "adapters/claude/CLAUDE.md",
]


REQUIRED_CONTRACT_PHRASES = [
    "GitHub Copilot",
    ".github/prompts/",
    "/cg-<name> [args...]",
    "Prompt files are executable instructions",
    ".github/skills/<skill-name>/SKILL.md",
    ".github/agents/cg-*.agent.md",
    "<prefix>-skill-*",
    "@cg-*",
    "ExitPlanMode: ignore",
    ".github/copilot-instructions.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_adapter_manifest_lists_expected_files() -> None:
    manifest_path = REPO_ROOT / "adapters/manifest.json"

    manifest = json.loads(_read(manifest_path))

    assert manifest["schema_version"] == 1
    assert manifest["copilot_behavior"] == "unchanged"
    adapters = {adapter["id"]: adapter for adapter in manifest["adapters"]}
    assert adapters["codex"]["source"] == "adapters/codex/AGENTS.md"
    assert adapters["codex"]["target_filename"] == "AGENTS.md"
    assert adapters["codex"]["opt_in"] is True
    assert adapters["claude-code"]["source"] == "adapters/claude/CLAUDE.md"
    assert adapters["claude-code"]["target_filename"] == "CLAUDE.md"
    assert adapters["claude-code"]["opt_in"] is True


def test_packaged_adapter_files_exist() -> None:
    for path in ADAPTER_FILES:
        assert path.exists(), f"missing adapter file: {path}"


def test_adapters_share_core_dispatch_contract() -> None:
    for path in ADAPTER_FILES:
        content = _read(path)
        for phrase in REQUIRED_CONTRACT_PHRASES:
            assert phrase in content, f"{path.relative_to(REPO_ROOT)} missing {phrase!r}"


def test_packaged_adapters_are_opt_in_and_non_copilot() -> None:
    for relative in ("adapters/codex/AGENTS.md", "adapters/claude/CLAUDE.md"):
        content = _read(REPO_ROOT / relative)
        assert "GitHub Copilot" in content
        assert "Do not treat this adapter as changing the intended" in content
        assert "root" not in relative.split("/")


def test_adapter_readme_documents_copy_targets_and_boundaries() -> None:
    content = _read(REPO_ROOT / "adapters/README.md")

    assert "Copy to consumer repo root" in content
    assert "AGENTS.md" in content
    assert "CLAUDE.md" in content
    assert "not `cg-link` managed outputs" in content
    assert "GitHub Copilot does not read these files" in content
