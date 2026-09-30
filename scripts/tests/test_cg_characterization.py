"""Characterization tests for stable CG workflow semantics.

Generated-target parity is enforced by ``test_target_drift.py`` against the
committed platform trees and ownership manifests. These tests retain small,
human-reviewable workflow contracts without duplicating target checksums.

Run from repo root:
    python -m pytest scripts/tests/test_cg_characterization.py -q
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_does_not_duplicate_generated_target_drift_snapshot() -> None:
    """Keep generated-target authority in target drift tests and manifests."""
    snapshot = REPO_ROOT / "scripts/tests/fixtures/cg_characterization_manifest.json"
    assert not snapshot.exists(), (
        "Generated-target snapshots duplicate test_target_drift.py and create "
        "stale-baseline CI failures."
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
