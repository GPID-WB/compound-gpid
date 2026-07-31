"""Red-phase contracts for user-selected execution and advisory routing."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_KEY = re.compile(r"(?m)^\s*model\s*:")


def test_canonical_prompts_and_agents_do_not_assign_execution_models() -> None:
    canonical = list((REPO_ROOT / ".github/prompts").glob("*.prompt.md"))
    canonical += list((REPO_ROOT / ".github/agents").glob("*.agent.md"))

    assert canonical
    assigned = [
        path.as_posix()
        for path in canonical
        if MODEL_KEY.search(path.read_text(encoding="utf-8"))
    ]
    assert assigned == []


def test_target_mapping_has_no_model_assignment_or_mapping_artifacts() -> None:
    mapping = json.loads(
        (REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8")
    )

    for target in mapping["targets"]:
        assert "modelMappingMode" not in target
        assert "modelMapping" not in target
        assert "modelMapping" not in target["outputPaths"]
        assert all("model-mapping" not in str(unit) for unit in target.get("installUnits", []))


def test_execution_model_catalog_and_generated_mapping_files_are_absent() -> None:
    assert not (REPO_ROOT / ".github/shared/model-catalog.json").exists()
    assert not list(REPO_ROOT.glob(".claude/model-mapping.*.json"))
    assert not list(REPO_ROOT.glob(".agents/model-mapping.*.json"))
    assert not list(REPO_ROOT.glob(".opencode/model-mapping.*.json"))
