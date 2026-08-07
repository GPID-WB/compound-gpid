"""Characterization tests for CG workflows and generated-target parity.

Pins current CG behavior as a baseline before modular refactoring:
1. The generated-target manifest (per-platform file list + sha256) reproduces
   exactly the committed baseline fixture.
2. Key workflow prompt bodies retain the required structural section headings.

Run from repo root:
    python -m pytest scripts/tests/test_cg_characterization.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import cg_generate_targets as gen

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "scripts/tests/fixtures/cg_characterization_manifest.json"


def _build_manifest(root: Path) -> dict:
    mapping = gen.load_target_mapping(root)
    assets = gen.scan_canonical_assets(root)
    plan = gen.build_generation_plan(root, mapping, assets)
    out: dict = {}
    for target_id, result in plan.by_target.items():
        out[target_id] = sorted(
            ({"path": entry.destination, "kind": entry.kind, "sha256": entry.sha256} for entry in result.entries),
            key=lambda item: item["path"],
        )
    return out


def test_cg_characterization_baseline_manifest_is_committed() -> None:
    assert FIXTURE.exists(), f"Missing characterization fixture: {FIXTURE}"


def test_generator_reproduces_characterization_baseline_exactly() -> None:
    baseline = json.loads(FIXTURE.read_text(encoding="utf-8"))
    current = _build_manifest(REPO_ROOT)
    assert set(current) == set(baseline), "Platform set drifted"
    for platform, entries in baseline.items():
        assert current[platform] == entries, (
            f"CG characterization drift on platform '{platform}'.\n"
            "Run: python scripts/cg_generate_targets.py --all\n"
            f"Then regenerate: scripts/tests/fixtures/cg_characterization_manifest.json"
        )


REQUIRED_SECTIONS = {
    "cg-work.prompt.md": {
        "File Permissions",
        "Process",
        "Work Summary",
        "Rules",
    },
    "cg-plan.prompt.md": {
        "File Permissions",
        "Process",
        "Objective",
        "Context",
        "Requirements",
        "Implementation Steps",
        "Testing Strategy",
        "Documentation Checklist",
        "Risks & Mitigations",
        "Out of Scope",
        "Completion Contract",
    },
    "cg-brainstorm.prompt.md": {
        "File Permissions",
        "Process",
        "Context",
        "Requirements",
        "Approaches Considered",
        "Decision",
        "Next Steps",
    },
}


def _section_headings(text: str) -> set[str]:
    return {
        line[3:].strip()
        for line in text.splitlines()
        if line.startswith("## ")
    }


def test_key_workflow_prompts_retain_required_sections() -> None:
    prompts_root = REPO_ROOT / ".github/prompts"
    for filename, required in REQUIRED_SECTIONS.items():
        text = (prompts_root / filename).read_text(encoding="utf-8")
        headings = _section_headings(text)
        assert required <= headings, (
            f"{filename} missing required characterization sections: "
            f"{sorted(required - headings)}"
        )
