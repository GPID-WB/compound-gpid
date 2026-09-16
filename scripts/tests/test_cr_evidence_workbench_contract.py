"""Created 2026-08-13. Contract tests for CR workbench integration."""
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    """Read one canonical CR asset as UTF-8 text."""
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_cr_evidence_skill_documents_workbench_boundary() -> None:
    """Document local workbench use without weakening provenance rules."""
    text = _read(".github/skills/cr-skill-evidence-provenance/SKILL.md").lower()
    for term in (
        "research_evidence",
        "local evidence workbench",
        "external-quarantine",
        "external-opt-in",
        "candidate",
        "original files remain authoritative",
        "no internet search",
    ):
        assert term in text, term


def test_cr_work_prompt_documents_start_resume_and_p0_boundary() -> None:
    """Make the existing CR work launcher aware of local evidence runs."""
    text = _read(".github/prompts/cr-work.prompt.md").lower()
    for term in (
        "research_evidence",
        "start",
        "resume",
        "external-quarantine",
        "candidate",
        "original source",
        "no external api",
    ):
        assert term in text, term


def test_cr_review_prompt_audits_workbench_provenance() -> None:
    """Route CR review attention to the workbench evidence boundary."""
    text = _read(".github/prompts/cr-review.prompt.md").lower()
    for term in ("research_evidence", "external-quarantine", "source version", "locator"):
        assert term in text, term


def test_research_suite_owns_cr_surfaces_without_cg_cross_suite_ownership() -> None:
    """Keep CR workbench integration in suite-cr and engineering behavior isolated."""
    registry = json.loads(
        (REPO_ROOT / ".github/shared/module-registry.json").read_text(encoding="utf-8")
    )
    modules = {module["id"]: module for module in registry["modules"]}
    research_assets = set(modules["suite-cr"]["ownedAssets"])
    technical_assets = set(modules["suite-cg"]["ownedAssets"])
    assert ".github/prompts/cr-*.prompt.md" in research_assets
    assert ".github/skills/cr-skill-evidence-provenance/" in research_assets
    assert not any(asset.startswith(".github/prompts/cr-") for asset in technical_assets)
