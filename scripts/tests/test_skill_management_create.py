"""Permanent canonical skill creation tests for Phase 5."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

import cg_project_manifest as manifest_module
from skill_management.operations import create
from scripts.tests.test_project_projection import (
    _canonical_assets,
    _real_registry,
    _small_mapping,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ALL_PLATFORMS = "copilot,claude-code,codex,opencode,kilo"


def _canonical_root(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    _real_registry(root)
    _small_mapping(root)
    _canonical_assets(root)
    registry_path = root / ".github/shared/module-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["modules"].append(
        {
            "id": "cap-new-skill",
            "layer": "capability",
            "displayName": "New skill owner",
            "description": "Fixture owner for an inactive permanent skill.",
            "dependsOn": ["kernel"],
            "ownedAssets": [],
            "ambiguous": [],
        }
    )
    kernel = next(item for item in registry["modules"] if item["id"] == "kernel")
    kernel["ownedAssets"].extend(
        [
            ".github/shared/module-registry.json",
            ".github/shared/target-mapping.json",
            ".github/shared/vendor-policy.json",
        ]
    )
    suite_cg = next(item for item in registry["modules"] if item["id"] == "suite-cg")
    suite_cg["ownedAssets"] = [
        item
        for item in suite_cg["ownedAssets"]
        if item != ".github/skills/cg-skill-brain-query/"
    ]
    suite_cr = next(item for item in registry["modules"] if item["id"] == "suite-cr")
    suite_cr["ownedAssets"] = [
        item
        for item in suite_cr["ownedAssets"]
        if item != ".github/instructions/r.instructions.md"
    ]
    registry["modules"].append(
        {
            "id": "cap-skill-management",
            "layer": "capability",
            "displayName": "Internal skill management",
            "description": "Fixture owner for management templates and provenance.",
            "dependsOn": ["kernel"],
            "ownedAssets": [
                ".github/skills/cg-skill-management/"
            ],
            "ambiguous": [],
        }
    )
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (root / "compound-gpid.local.md").write_text(
        '---\nlanguage: "r"\nsuites: [cg]\n---\n# fixture\n',
        encoding="utf-8",
    )
    policy_source = REPO_ROOT / ".github/shared/vendor-policy.json"
    policy_target = root / ".github/shared/vendor-policy.json"
    policy_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(policy_source, policy_target)
    template_source = REPO_ROOT / ".github/skills/cg-skill-management/templates"
    template_target = root / ".github/skills/cg-skill-management/templates"
    template_target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / ".github/skills/cg-skill-management/SKILL.md",
        template_target.parent / "SKILL.md",
    )
    for template in template_source.iterdir():
        if template.is_file():
            shutil.copy2(template, template_target / template.name)
    manifest = manifest_module.resolve_active_manifest(root)
    (root / ".compound-gpid").mkdir(parents=True, exist_ok=True)
    (root / ".compound-gpid/active-manifest.json").write_text(
        manifest_module.canonical_manifest_bytes(manifest), encoding="utf-8"
    )
    return root


def _context(root: Path, *, maintainer: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        project_root=root,
        source_root=root,
        role="maintainer" if maintainer else "consumer",
        can_write_canonical=maintainer,
        write_context_errors=() if maintainer else ("not a canonical checkout",),
    )


def _arguments(**overrides) -> dict:
    arguments = {
        "positionals": ["permanent-demo"],
        "scope": "permanent",
        "description": "Focused permanent demo skill.",
        "owner": "cap-new-skill",
        "capability": "permanent-demo",
        "suites": "cg",
        "platforms": ALL_PLATFORMS,
        "activation_cost": "low",
        "triggers": "permanent-demo",
        "selectors": "[]",
        "approver": "maintainer@example.com",
        "review_reference": "reviewed-commit=" + "a" * 40,
    }
    arguments.update(overrides)
    return arguments


def _plan(root: Path, arguments: dict):
    return create.handle(
        context=_context(root),
        request={"phase": "plan", "arguments": arguments},
    )


def test_minimal_permanent_skill_is_planned_then_applied_inactive(
    tmp_path: Path,
) -> None:
    root = _canonical_root(tmp_path)
    arguments = _arguments()

    planned = _plan(root, arguments)

    assert not planned.findings
    assert planned.plan_digest
    assert not (root / ".github/skills/permanent-demo").exists()
    applied = create.handle(
        context=_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )
    assert not applied.findings
    skill = root / ".github/skills/permanent-demo/SKILL.md"
    assert skill.is_file()
    assert 'description: "Focused permanent demo skill."' in skill.read_text("utf-8")
    registry = json.loads(
        (root / ".github/shared/module-registry.json").read_text("utf-8")
    )
    capability = next(
        item for item in registry["capabilities"] if item["id"] == "permanent-demo"
    )
    assert capability["activationMode"] == "explicit-only"
    assert capability["owningModule"] == "cap-new-skill"
    manifest = json.loads(
        (root / ".compound-gpid/active-manifest.json").read_text("utf-8")
    )
    row = next(
        item for item in manifest["catalogRecords"] if item["id"] == "permanent-demo"
    )
    assert row["available"] is False
    assert "cap-new-skill" not in manifest["selection"]["moduleClosure"]
    provenance = json.loads(
        (
            root
            / ".github/shared/skill-management/provenance/permanent-demo.json"
        ).read_text("utf-8")
    )
    assert provenance["history"][0]["event"] == "created"
    assert provenance["history"][0]["approval"]["actor"] == "maintainer@example.com"


def test_create_scaffolds_only_requested_focused_resources(tmp_path: Path) -> None:
    root = _canonical_root(tmp_path)
    arguments = _arguments(
        references="guide",
        workflows="review",
        examples="minimal",
        resources="diagram.svg",
        resource_classes='{"resources/diagram.svg":"diagram"}',
    )

    planned = _plan(root, arguments)
    assert not planned.findings
    applied = create.handle(
        context=_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )

    assert not applied.findings
    actual = {
        path.relative_to(root / ".github/skills/permanent-demo").as_posix()
        for path in (root / ".github/skills/permanent-demo").rglob("*")
        if path.is_file()
    }
    assert actual == {
        "SKILL.md",
        "examples/minimal.md",
        "references/guide.md",
        "resources/diagram.svg",
        "workflows/review.md",
    }


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"positionals": ["Bad_Name"]}, "identifier"),
        (
            {"description": "Non-ASCII cafe\N{LATIN SMALL LETTER E WITH ACUTE}."},
            "ASCII",
        ),
        ({"resources": "table.csv"}, "rejected"),
        ({"resources": "diagram.svg"}, "approved non-data class"),
        ({"approver": ""}, "approver"),
        ({"review_reference": "pull/123"}, "immutable"),
    ],
)
def test_create_rejects_invalid_metadata_or_resources(
    tmp_path: Path, overrides: dict, message: str
) -> None:
    outcome = _plan(_canonical_root(tmp_path), _arguments(**overrides))

    assert outcome.findings
    assert message.casefold() in outcome.findings[0].message.casefold()


def test_consumer_cannot_create_permanent_skill(tmp_path: Path) -> None:
    root = _canonical_root(tmp_path)

    outcome = create.handle(
        context=_context(root, maintainer=False),
        request={"phase": "plan", "arguments": _arguments()},
    )

    assert outcome.findings
    assert outcome.exit_code == 4


def test_create_registers_explicit_new_owner_module_without_manual_repair(
    tmp_path: Path,
) -> None:
    root = _canonical_root(tmp_path)
    arguments = _arguments(owner="cap-permanent-demo")
    planned = _plan(root, arguments)
    assert not planned.findings
    applied = create.handle(
        context=_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )

    assert not applied.findings
    registry = json.loads(
        (root / ".github/shared/module-registry.json").read_text("utf-8")
    )
    owner = next(
        item for item in registry["modules"] if item["id"] == "cap-permanent-demo"
    )
    assert owner["layer"] == "capability"
    assert owner["ownedAssets"] == [".github/skills/permanent-demo/"]


def test_existing_capability_must_be_explicit_only_and_unselected(
    tmp_path: Path,
) -> None:
    root = _canonical_root(tmp_path)
    registry_path = root / ".github/shared/module-registry.json"
    registry = json.loads(registry_path.read_text("utf-8"))
    registry["capabilities"].append(
        {
            "id": "existing-opt-in",
            "owningModule": "cap-new-skill",
            "activationMode": "explicit-only",
            "supportedSuites": ["cg"],
            "supportedPlatforms": [
                "copilot",
                "claude-code",
                "codex",
                "opencode",
                "kilo",
            ],
            "sourceProvenance": "canonical/.github",
            "activationCost": "low",
            "taskTriggers": ["permanent-demo"],
            "configSelectors": [],
        }
    )
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    manifest = manifest_module.resolve_active_manifest(root)
    (root / ".compound-gpid/active-manifest.json").write_text(
        manifest_module.canonical_manifest_bytes(manifest), encoding="utf-8"
    )

    inactive = _plan(root, _arguments(capability="existing-opt-in"))
    assert not inactive.findings

    config = root / "compound-gpid.local.md"
    config.write_text(
        '---\nlanguage: "r"\nsuites: [cg]\ncapabilities: [existing-opt-in]\n---\n',
        encoding="utf-8",
    )
    active_manifest = manifest_module.resolve_active_manifest(root)
    (root / ".compound-gpid/active-manifest.json").write_text(
        manifest_module.canonical_manifest_bytes(active_manifest), encoding="utf-8"
    )
    active = _plan(root, _arguments(capability="existing-opt-in"))
    assert active.findings
    assert "active" in active.findings[0].message.casefold()
