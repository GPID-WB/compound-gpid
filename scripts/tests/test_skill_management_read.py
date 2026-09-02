"""Tests for the private read-only skill-management operations and services."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

import pytest

import cg_project_manifest as manifest_module
import cg_skill
from skill_management import contracts
from skill_management.operations import find, help as help_operation, info, validate
from skill_management.planning import OperationOutcome, result_envelope
from skill_management.services import bundles, catalog, registry


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(".compound-gpid/active-manifest.json")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def _registry(*, own_skill: bool = True) -> dict:
    skill_assets = [".github/skills/cg-skill-python-example/"] if own_skill else []
    return {
        "schemaVersion": 2,
        "description": "Phase 2 read fixture",
        "capabilities": [
            {
                "id": "python",
                "owningModule": "cap-language-python",
                "supportedSuites": ["cg"],
                "supportedPlatforms": ["copilot", "kilo"],
                "sourceProvenance": "canonical/.github",
                "activationCost": "low",
                "taskTriggers": ["language=python"],
                "configSelectors": [
                    {
                        "field": "language",
                        "operator": "contains",
                        "value": "python",
                    }
                ],
            }
        ],
        "modules": [
            {
                "id": "kernel",
                "layer": "kernel",
                "displayName": "Kernel",
                "description": "Fixture kernel.",
                "dependsOn": [],
                "ownedAssets": [
                    ".github/shared/module-registry.json",
                    ".github/shared/target-mapping.json",
                    ".github/shared/vendor-policy.json",
                ],
            },
            {
                "id": "cap-language-python",
                "layer": "capability",
                "displayName": "Python",
                "description": "Fixture Python capability.",
                "dependsOn": ["kernel"],
                "ownedAssets": skill_assets,
            },
            {
                "id": "cap-skill-management",
                "layer": "capability",
                "displayName": "Skill management",
                "description": "Fixture management substrate.",
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
                "description": "Fixture suite.",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
        ],
    }


def _copy_management_assets(root: Path) -> None:
    descriptors = ("find", "help", "info", "validate")
    common_contracts = (
        "operation-descriptor-v1.schema.json",
        "request-v1.schema.json",
        "result-v1.schema.json",
    )
    for name in common_contracts + tuple(f"{name}-v1.schema.json" for name in descriptors):
        source = REPO_ROOT / ".github/shared/skill-management/contracts" / name
        destination = root / ".github/shared/skill-management/contracts" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    for name in descriptors:
        for relative in (
            f".github/shared/skill-management/operations/{name}.json",
            f".github/skills/cg-skill-management/workflows/{name}.md",
            f"docs/skills/management/commands/{name}.md",
            f"scripts/skill_management/operations/{name}.py",
        ):
            source = REPO_ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
    skill_source = REPO_ROOT / ".github/skills/cg-skill-management/SKILL.md"
    skill_destination = root / ".github/skills/cg-skill-management/SKILL.md"
    skill_destination.parent.mkdir(parents=True, exist_ok=True)
    skill_destination.write_bytes(skill_source.read_bytes())
    policy_source = REPO_ROOT / ".github/shared/vendor-policy.json"
    policy_destination = root / ".github/shared/vendor-policy.json"
    policy_destination.parent.mkdir(parents=True, exist_ok=True)
    policy_destination.write_bytes(policy_source.read_bytes())
    _write(root / "scripts/tests/test_skill_management_read.py", "# fixture\n")
    _write(root / "scripts/tests/test_skill_management_completeness.py", "# fixture\n")


def _root(tmp_path: Path, *, own_skill: bool = True) -> Path:
    _write_json(tmp_path / ".github/shared/module-registry.json", _registry(own_skill=own_skill))
    _write_json(
        tmp_path / ".github/shared/target-mapping.json",
        {
            "schemaVersion": 1,
            "description": "fixture",
            "targets": [{"id": "copilot"}, {"id": "kilo"}],
        },
    )
    _write(
        tmp_path / "compound-gpid.local.md",
        "---\nlanguage: \"python\"\nsuites: [cg]\n---\n# Fixture\n",
    )
    _write(
        tmp_path / ".github/skills/cg-skill-python-example/SKILL.md",
        "---\nname: cg-skill-python-example\n"
        "description: \"Python catalog example.\"\n---\n"
        "# Example\n\nSee [details](references/details.md).\n",
    )
    _write(
        tmp_path / ".github/skills/cg-skill-python-example/references/details.md",
        "# Details\n",
    )
    _copy_management_assets(tmp_path)
    return tmp_path


def _context(root: Path) -> SimpleNamespace:
    return SimpleNamespace(project_root=root, source_root=root, role="consumer")


def _request(operation: str, arguments: Mapping[str, Any]) -> dict:
    return {
        "schema": "cg-skill-request-v1",
        "operation": operation,
        "phase": "read",
        "root": ".",
        "sourceRoot": ".",
        "arguments": dict(arguments),
    }


def _commit_manifest(root: Path) -> dict:
    resolved = manifest_module.resolve_active_manifest(root)
    path = root / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        manifest_module.canonical_manifest_bytes(resolved),
        encoding="utf-8",
        newline="\n",
    )
    return resolved


def _result(operation: str, outcome: OperationOutcome) -> dict:
    return result_envelope(operation, "read", "consumer", outcome)


def test_registry_snapshot_resolves_one_owner_and_capability(tmp_path: Path) -> None:
    root = _root(tmp_path)
    snapshot = registry.load_registry_snapshot(root)

    assert snapshot.owner_for_asset(
        ".github/skills/cg-skill-python-example/SKILL.md"
    ) == "cap-language-python"
    assert snapshot.capability_for_owner("cap-language-python")["id"] == "python"
    assert len(snapshot.digest) == 64
    with pytest.raises(TypeError):
        snapshot.registry["description"] = "changed"  # type: ignore[index]


def test_bundle_inventory_includes_nested_resources_and_valid_links(tmp_path: Path) -> None:
    root = _root(tmp_path)
    inventory = bundles.inventory_bundle(
        root,
        ".github/skills/cg-skill-python-example",
        origin="plugin-canonical",
    )

    assert inventory.identifier == "cg-skill-python-example"
    assert inventory.origin == "plugin-canonical"
    assert [item.bundle_path for item in inventory.files] == [
        "SKILL.md",
        "references/details.md",
    ]
    assert bundles.validate_markdown_references(inventory) == ()


def test_bundle_portable_collision_is_rejected() -> None:
    with pytest.raises(bundles.BundleValidationError, match="portable path collision"):
        bundles.validate_bundle_paths(("References/Guide.md", "references/guide.md"))


def test_fresh_catalog_reports_active_without_capability_disagreement(tmp_path: Path) -> None:
    root = _root(tmp_path)
    resolved = _commit_manifest(root)
    result = catalog.resolve_catalog(_context(root))

    assert result.manifest_health == "fresh"
    assert result.prospective is False
    python_row = next(
        row for row in result.rows if row["id"] == "cg-skill-python-example"
    )
    assert python_row["availability"] == "active"
    assert python_row["available"] is True
    assert python_row["capability"] == "python"
    manifest_row = next(
        row
        for row in resolved["catalogRecords"]
        if row["id"] == "cg-skill-python-example"
    )
    assert manifest_row["capability"] == "python"
    management_row = next(
        row for row in result.rows if row["id"] == "cg-skill-management"
    )
    assert management_row["availability"] == "inactive"
    assert "selected manifest closure" in management_row["inactiveReason"]


def test_missing_manifest_returns_only_prospective_canonical_rows(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _write(
        root / ".agents/skills/external/SKILL.md",
        "---\nname: external\ndescription: \"External.\"\n---\n",
    )

    result = catalog.resolve_catalog(_context(root))

    assert result.manifest_health == "missing"
    assert result.prospective is True
    assert [row["id"] for row in result.rows] == [
        "cg-skill-management",
        "cg-skill-python-example",
    ]
    assert all(row["availability"] == "prospective" for row in result.rows)
    assert all("available" not in row for row in result.rows)
    assert "cg-link" in result.remediation


def test_stale_manifest_never_claims_active_or_projected_state(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _commit_manifest(root)
    _write(
        root / "compound-gpid.local.md",
        "---\nlanguage: \"r\"\nsuites: [cg]\n---\n# Changed\n",
    )

    result = catalog.resolve_catalog(_context(root))

    assert result.manifest_health == "stale"
    assert result.prospective is True
    assert all(row["availability"] == "prospective" for row in result.rows)
    assert all("available" not in row for row in result.rows)
    assert "cg-update" in result.remediation


def test_invalid_manifest_fails_closed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _write(root / MANIFEST_PATH, "{not-json\n")

    with pytest.raises(catalog.CatalogError) as error:
        catalog.resolve_catalog(_context(root))

    assert error.value.manifest_health == "invalid"


def test_invalid_manifest_dispatch_result_preserves_contract_exit_code(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    _write(root / MANIFEST_PATH, "{not-json\n")

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/cg_skill.py"),
            "--project-root",
            str(root),
            "--source-root",
            str(REPO_ROOT),
            "--format",
            "json",
            "find",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == contracts.EXIT_CONTRACT
    assert payload["exitCode"] == contracts.EXIT_CONTRACT
    assert payload["manifestHealth"] == "invalid"
    assert payload["findings"][0]["code"] == "catalog.invalid-input"


def test_find_supports_partial_and_exact_identifier_filters(tmp_path: Path) -> None:
    root = _root(tmp_path)
    partial = find.handle(
        context=_context(root),
        request=_request("find", {"id": "python", "full": False}),
    )
    exact = find.handle(
        context=_context(root),
        request=_request(
            "find", {"id": "cg-skill-python-example", "exact": True, "full": True}
        ),
    )

    assert [row["id"] for row in partial.data["records"]] == [
        "cg-skill-python-example"
    ]
    assert exact.data["records"][0]["owner"] == "cap-language-python"
    assert exact.data["records"][0]["origin"] == "plugin-canonical"


def test_prospective_availability_filter_is_a_hard_stop(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outcome = find.handle(
        context=_context(root),
        request=_request("find", {"available": True}),
    )

    assert outcome.exit_code == contracts.EXIT_CONTRACT
    assert outcome.manifest_health == "missing"
    assert outcome.data["prospective"] is True
    assert outcome.data["records"] == []
    assert outcome.findings[0].code == "catalog.invalid-input"
    assert "cg-link" in outcome.findings[0].remediation


def test_info_unknown_identifier_returns_stable_usage_finding(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outcome = info.handle(
        context=_context(root),
        request=_request("info", {"positionals": ["missing-skill"]}),
    )

    assert outcome.exit_code == contracts.EXIT_USAGE
    assert [finding.code for finding in outcome.findings] == ["skill.unknown"]


def test_help_discovers_complete_descriptors_in_lexical_order(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outcome = help_operation.handle(
        context=_context(root),
        request=_request("help", {}),
    )

    assert [row["operation"] for row in outcome.data["operations"]] == [
        "find",
        "help",
        "info",
        "validate",
    ]
    assert outcome.manifest_health == "missing"
    assert outcome.data["prospective"] is True


def test_read_result_human_and_json_are_deterministic(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outcome = find.handle(
        context=_context(root),
        request=_request("find", {"id": "python", "full": True}),
    )
    result = _result("find", outcome)

    first_json = contracts.canonical_json_bytes(result)
    second_json = contracts.canonical_json_bytes(_result("find", outcome))
    first_human = cg_skill._render_human(result)  # pylint: disable=protected-access
    second_human = cg_skill._render_human(_result("find", outcome))  # pylint: disable=protected-access

    assert first_json == second_json
    assert first_human == second_human
    assert "prospective" in first_human


def test_validate_all_reports_valid_bundle_resources_and_descriptors(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outcome = validate.handle(
        context=_context(root),
        request=_request("validate", {"all": True}),
    )

    assert outcome.exit_code == contracts.EXIT_SUCCESS
    assert outcome.data["validatedIds"] == [
        "cg-skill-management",
        "cg-skill-python-example",
    ]
    assert outcome.data["descriptorOperations"] == ["find", "help", "info", "validate"]
    assert not any(finding.severity == "error" for finding in outcome.findings)


@pytest.mark.parametrize(
    "mutation,expected_code",
    [
        ("frontmatter", "bundle.frontmatter"),
        ("link", "bundle.reference-missing"),
        ("owner", "registry.owner-missing"),
    ],
)
def test_validate_reports_baseline_skill_errors(
    tmp_path: Path, mutation: str, expected_code: str
) -> None:
    root = _root(tmp_path, own_skill=mutation != "owner")
    if mutation == "frontmatter":
        _write(
            root / ".github/skills/cg-skill-python-example/SKILL.md",
            "# Missing frontmatter\n",
        )
    elif mutation == "link":
        _write(
            root / ".github/skills/cg-skill-python-example/SKILL.md",
            "---\nname: cg-skill-python-example\n"
            "description: \"Python catalog example.\"\n---\n"
            "See [missing](references/missing.md).\n",
        )

    outcome = validate.handle(
        context=_context(root),
        request=_request("validate", {"all": True}),
    )

    assert outcome.exit_code == contracts.EXIT_CONTRACT
    assert expected_code in {finding.code for finding in outcome.findings}
    assert all(finding.remediation for finding in outcome.findings)


def test_common_findings_sort_by_severity_then_path_and_code() -> None:
    findings = (
        contracts.ContractFinding("/b", "z.info", "info", "Info.", "None."),
        contracts.ContractFinding("/a", "a.warning", "warning", "Warning.", "Fix."),
        contracts.ContractFinding("/z", "b.error", "error", "Error.", "Fix."),
        contracts.ContractFinding("/a", "a.error", "error", "Error.", "Fix."),
    )

    rendered = result_envelope(
        "validate",
        "read",
        "consumer",
        OperationOutcome(findings=findings),
    )

    assert [item["code"] for item in rendered["findings"]] == [
        "a.error",
        "b.error",
        "a.warning",
        "z.info",
    ]
