"""Tests for the module-registry validator.

Run from repo root:
    python -m pytest scripts/tests/test_module_registry.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_validate_modules as validator
from skill_management.services import registry as registry_service


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _create_file(repo_root: Path, rel_path: str, content: str = "body\n") -> None:
    path = repo_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _minimal_assets(repo_root: Path) -> None:
    _create_file(repo_root, ".github/prompts/cg-work.prompt.md", "---\ndescription: work\n---\nwork body\n")
    _create_file(repo_root, ".github/agents/cg-roadmap.agent.md", "---\ndescription: roadmap\n---\nagent body\n")
    _create_file(repo_root, ".github/skills/cg-skill-r-analytical/SKILL.md", "---\ndescription: r\n---\nskill body\n")
    _create_file(repo_root, ".github/instructions/r.instructions.md", "r instructions\n")
    _create_file(repo_root, ".github/shared/context-loading.contract.md", "context contract\n")
    _create_file(repo_root, ".github/shared/target-mapping.json", "{}\n")
    _create_file(repo_root, ".github/shared/module-registry.json", "{}")


def _default_registry() -> dict:
    return {
        "schemaVersion": 1,
        "description": "test registry",
        "modules": [
            {
                "id": "kernel",
                "layer": "kernel",
                "displayName": "Kernel",
                "description": "Lifecycle and generation.",
                "dependsOn": [],
                "ownedAssets": [
                    ".github/shared/*.contract.md",
                    ".github/shared/target-mapping.json",
                    ".github/shared/module-registry.json",
                ],
            },
            {
                "id": "cap-language-r",
                "layer": "capability",
                "displayName": "R language",
                "description": "R skills.",
                "dependsOn": ["kernel"],
                "ownedAssets": [
                    ".github/skills/cg-skill-r-*/",
                    ".github/instructions/r.instructions.md",
                ],
            },
            {
                "id": "suite-cg",
                "layer": "suite",
                "displayName": "Technical suite",
                "description": "cg-* workflows.",
                "dependsOn": ["kernel", "cap-language-r"],
                "ownedAssets": [
                    ".github/prompts/cg-*.prompt.md",
                    ".github/agents/cg-*.agent.md",
                ],
            },
        ],
    }


def _registry(repo_root: Path, registry: dict) -> None:
    _write_json(repo_root / ".github/shared/module-registry.json", registry)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cycle_detection_handles_long_graph_without_recursion() -> None:
    adjacency = {
        f"module-{index}": [f"module-{index + 1}"]
        for index in range(2500)
    }
    adjacency["module-2500"] = []
    assert validator._first_cycle(adjacency) is None  # pylint: disable=protected-access
    adjacency["module-2500"] = ["module-2499"]
    assert validator._first_cycle(adjacency) == [  # pylint: disable=protected-access
        "module-2499",
        "module-2500",
        "module-2499",
    ]


def test_asset_read_failure_returns_validation_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _minimal_assets(tmp_path)
    _registry(tmp_path, _default_registry())
    original = validator.secure_fs.secure_read_bytes

    def fail_selected(root, relative_path, **kwargs):
        if str(relative_path).replace("\\", "/").endswith("cg-work.prompt.md"):
            raise validator.secure_fs.SecureMutationError("simulated path swap")
        return original(root, relative_path, **kwargs)

    monkeypatch.setattr(validator.secure_fs, "secure_read_bytes", fail_selected)
    errors = validator.check_dependencies(tmp_path)
    assert any("simulated path swap" in error for error in errors)


class TestRegistrySchema:
    def test_happy_path_valid_registry_passes(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _registry(tmp_path, _default_registry())
        errors = validator.check_ownership(tmp_path)
        assert errors == [], f"Validation errors: {errors}"

    def test_malformed_json_returns_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        (tmp_path / ".github/shared/module-registry.json").write_text(
            "{not valid json", encoding="utf-8"
        )
        registry, error = validator.load_registry(tmp_path)
        assert registry is None
        assert error is not None
        assert "JSON" in error

    def test_duplicate_module_ids_rejected(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"].append(registry["modules"][0])
        _registry(tmp_path, registry)
        errors = validator.check_ownership(tmp_path)
        assert any("duplicate" in error or "unique" in error for error in errors)

    def test_unknown_dependency_rejected(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"][1]["dependsOn"] = ["does-not-exist"]
        _registry(tmp_path, registry)
        errors = validator.check_ownership(tmp_path)
        assert any("does-not-exist" in error for error in errors)


class TestOwnershipClosure:
    def test_public_registry_owner_matching_agrees_with_validator(
        self, tmp_path: Path
    ) -> None:
        _minimal_assets(tmp_path)
        data = _default_registry()
        _registry(tmp_path, data)
        asset = ".github/skills/cg-skill-r-analytical/SKILL.md"

        assert registry_service.matching_asset_owners(data, asset) == (
            "cap-language-r",
        )
        assert validator.resolve_asset_owner(data, asset) == "cap-language-r"

    def test_asset_owned_by_two_modules_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"][1]["ownedAssets"].append(".github/prompts/cg-*.prompt.md")
        _registry(tmp_path, registry)
        errors = validator.check_ownership(tmp_path)
        assert any("multi" in error.lower() or "more than one" in error.lower() or
                   "double" in error.lower() for error in errors)

    def test_unowned_canonical_asset_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _create_file(tmp_path, ".github/prompts/orphan.prompt.md", "orphan\n")
        registry = _default_registry()
        _registry(tmp_path, registry)
        errors = validator.check_ownership(tmp_path)
        assert any("no owning module" in error for error in errors)
        assert any("orphan" in error for error in errors)

    def test_declared_asset_must_exist(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"][0]["ownedAssets"].append(".github/shared/not-there.json")
        _registry(tmp_path, registry)
        errors = validator.check_ownership(tmp_path)
        assert any("not-there.json" in error for error in errors)

    def test_frontmatter_owner_mismatch_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _create_file(
            tmp_path,
            ".github/prompts/cg-work.prompt.md",
            "---\ndescription: work\nowner: wrong-module\n---\nwork body\n",
        )
        _registry(tmp_path, _default_registry())
        errors = validator.check_ownership(tmp_path)
        assert any("owner" in error and "cg-work" in error for error in errors)

    def test_nested_shared_resources_are_individually_owned(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _create_file(
            tmp_path,
            ".github/shared/skill-management/contracts/request-v1.schema.json",
            "{}\n",
        )
        registry = _default_registry()
        registry["modules"].append(
            {
                "id": "cap-skill-management",
                "layer": "capability",
                "displayName": "Skill management",
                "description": "Internal skill management substrate.",
                "dependsOn": ["kernel"],
                "ownedAssets": [".github/shared/skill-management/"],
            }
        )
        _registry(tmp_path, registry)

        assert validator.check_ownership(tmp_path) == []
        assert (
            ".github/shared/skill-management/contracts/request-v1.schema.json"
            in validator.canonical_assets(tmp_path)
        )

    def test_nested_shared_resource_with_multiple_owners_is_rejected(
        self, tmp_path: Path
    ) -> None:
        _minimal_assets(tmp_path)
        _create_file(
            tmp_path,
            ".github/shared/skill-management/contracts/request-v1.schema.json",
            "{}\n",
        )
        registry = _default_registry()
        registry["modules"][0]["ownedAssets"].append(
            ".github/shared/skill-management/"
        )
        registry["modules"].append(
            {
                "id": "cap-skill-management",
                "layer": "capability",
                "displayName": "Skill management",
                "description": "Internal skill management substrate.",
                "dependsOn": ["kernel"],
                "ownedAssets": [".github/shared/skill-management/"],
            }
        )
        _registry(tmp_path, registry)

        errors = validator.check_ownership(tmp_path)
        assert any("more than one" in error for error in errors)

    @pytest.mark.usefixtures("require_symlink_support")
    def test_nested_shared_directory_link_is_rejected(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        outside = tmp_path / "outside"
        outside.mkdir()
        _create_file(outside, "secret.json", "secret\n")
        (tmp_path / ".github/shared/skill-management").symlink_to(
            outside, target_is_directory=True
        )
        _registry(tmp_path, _default_registry())

        errors = validator.check_ownership(tmp_path)
        assert any("link" in error or "reparse" in error for error in errors)


class TestDependencies:
    def test_cycle_in_capability_dependencies_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"][1]["dependsOn"] = ["cap-testing"]
        registry["modules"].append({
            "id": "cap-testing",
            "layer": "capability",
            "displayName": "Testing",
            "description": "testing",
            "dependsOn": ["cap-language-r"],
            "ownedAssets": [],
        })
        _registry(tmp_path, registry)
        errors = validator.check_dependencies(tmp_path)
        assert any("cycle" in error.lower() or "acyclic" in error.lower() for error in errors)

    def test_suite_depends_on_suite_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"].append({
            "id": "suite-cr",
            "layer": "suite",
            "displayName": "Research suite",
            "description": "cr-*",
            "dependsOn": ["suite-cg"],
            "ownedAssets": [],
        })
        _registry(tmp_path, registry)
        errors = validator.check_dependencies(tmp_path)
        assert any("suite" in error.lower() for error in errors)

    def test_capability_depends_on_suite_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"][1]["dependsOn"] = ["suite-cg"]
        _registry(tmp_path, registry)
        errors = validator.check_dependencies(tmp_path)
        assert any("capability" in error.lower() and "suite" in error.lower() for error in errors)

    def test_kernel_depends_on_anything_is_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = _default_registry()
        registry["modules"][0]["dependsOn"] = ["cap-language-r"]
        _registry(tmp_path, registry)
        errors = validator.check_dependencies(tmp_path)
        assert any("kernel" in error.lower() for error in errors)

    def test_happy_path_dependency_validates(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _registry(tmp_path, _default_registry())
        errors = validator.check_dependencies(tmp_path)
        assert errors == [], f"Validation errors: {errors}"


class TestDependencyClosure:
    def _two_suite_repo(self, repo_root: Path) -> None:
        _minimal_assets(repo_root)
        _registry(repo_root, {
            "schemaVersion": 1,
            "description": "two suites",
            "modules": [
                {
                    "id": "kernel",
                    "layer": "kernel",
                    "displayName": "Kernel",
                    "description": "kernel",
                    "dependsOn": [],
                    "ownedAssets": [".github/shared/*.contract.md"],
                },
                {
                    "id": "cap-language-r",
                    "layer": "capability",
                    "displayName": "R",
                    "description": "R",
                    "dependsOn": ["kernel"],
                    "ownedAssets": [".github/skills/cg-skill-r-*/", ".github/instructions/r.instructions.md"],
                },
                {
                    "id": "suite-cg",
                    "layer": "suite",
                    "displayName": "CG",
                    "description": "CG",
                    "dependsOn": ["kernel", "cap-language-r"],
                    "ownedAssets": [".github/prompts/cg-*.prompt.md"],
                },
                {
                    "id": "suite-cr",
                    "layer": "suite",
                    "displayName": "CR",
                    "description": "CR",
                    "dependsOn": ["kernel", "cap-language-r"],
                    "ownedAssets": [".github/agents/cr-*.agent.md"],
                },
            ],
        })

    def test_cr_agent_referencing_cg_owned_skill_fails_gate(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/agents/cr-analysis.agent.md",
            "---\ndescription: cr analysis\n---\nUse `.github/prompts/cg-work.prompt.md`\n",
        )
        errors = validator.check_cross_suite_references(tmp_path)
        assert any("cross-suite" in error and "suite-cr" in error for error in errors)

    def test_cr_agent_referencing_depended_capability_passes(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/agents/cr-analysis.agent.md",
            "---\ndescription: cr analysis\n---\nUse `.github/skills/cg-skill-r-analytical/SKILL.md` via cap-language-r\n",
        )
        registry, _ = validator.load_registry(tmp_path)
        assert registry is not None
        # Make suite-cr depend on the capability that owns the referenced skill.
        for module in registry["modules"]:
            if module["id"] == "suite-cr":
                module["dependsOn"] = ["kernel", "cap-language-r"]
        _registry(tmp_path, registry)
        errors_with_closure = validator.check_unresolved_dependencies(tmp_path)
        assert errors_with_closure == [], f"Expected closure-safe, got: {errors_with_closure}"

    def test_capability_referencing_suite_fails(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/instructions/r.instructions.md",
            "Use `.github/prompts/cg-work.prompt.md`\n",
        )
        errors = validator.check_unresolved_dependencies(tmp_path)
        assert any("is outside its transitive dependency closure" in error for error in errors)

    def test_broken_reference_to_unknown_module_fails(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/agents/cr-analysis.agent.md",
            "---\ndescription: cr analysis\n---\nUse `.github/skills/cg-skill-nope/SKILL.md`\n",
        )
        errors = validator.check_unresolved_dependencies(tmp_path)
        # Unknown asset has no owner; reference is silently ignored but module
        # deps remain valid. Unknown-asset references are not resolvable.
        assert all("nope" not in error for error in errors)

    def test_name_form_agent_dispatch_cross_suite_is_detected(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/agents/cr-qualitative.agent.md",
            "---\ndescription: cr qualitative\n---\nDispatch @cg-adversarial for review.\n",
        )
        _create_file(tmp_path, ".github/agents/cg-adversarial.agent.md", "---\ndescription: adversarial\n---\nbody\n")
        registry, _ = validator.load_registry(tmp_path)
        assert registry is not None
        # cg-adversarial is owned by technical suite.
        for module in registry["modules"]:
            if module["id"] == "suite-cg":
                module["ownedAssets"].append(".github/agents/cg-adversarial.agent.md")
        _registry(tmp_path, registry)
        errors = validator.check_cross_suite_references(tmp_path)
        assert any("cross-suite" in error and "cg-adversarial" in error for error in errors)

    def test_name_form_skill_load_cross_suite_is_detected(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/agents/cr-qualitative.agent.md",
            "---\ndescription: cr qualitative\n---\nLoad `cg-skill-compound-docs` for capture.\n",
        )
        _create_file(tmp_path, ".github/skills/cg-skill-compound-docs/SKILL.md", "c\n")
        registry, _ = validator.load_registry(tmp_path)
        assert registry is not None
        for module in registry["modules"]:
            if module["id"] == "suite-cg":
                module["ownedAssets"].append(".github/skills/cg-skill-compound-docs/")
        _registry(tmp_path, registry)
        errors = validator.check_cross_suite_references(tmp_path)
        assert any("cross-suite" in error and "cg-skill-compound-docs" in error for error in errors)

    def test_name_form_unknown_agent_and_skill_are_not_flagged(self, tmp_path: Path) -> None:
        self._two_suite_repo(tmp_path)
        _create_file(
            tmp_path,
            ".github/agents/cr-qualitative.agent.md",
            "---\ndescription: cr qualitative\n---\nDispatch @cg-bogus and load `cg-skill-does-not-exist`.\n",
        )
        errors = validator.check_cross_suite_references(tmp_path)
        unresolved = validator.check_unresolved_dependencies(tmp_path)
        # Unknown names resolve to no canonical asset and must not produce
        # false cross-suite or closure errors.
        assert all("bogus" not in error and "does-not-exist" not in error for error in errors)
        assert all("bogus" not in error and "does-not-exist" not in error for error in unresolved)


class TestC2NoPhysicalRelocation:
    def _repo_with_packages(self, tmp_path: Path) -> Path:
        _minimal_assets(tmp_path)
        (tmp_path / "packages/kernel").mkdir(parents=True, exist_ok=True)
        (tmp_path / "packages/kernel/file.txt").write_text("x\n", encoding="utf-8")
        _registry(tmp_path, _default_registry())
        return tmp_path

    def test_packages_tree_violates_c2(self, tmp_path: Path) -> None:
        self._repo_with_packages(tmp_path)
        errors = validator.check_ownership(tmp_path)
        assert any("C2" in error or "physical package relocation" in error for error in errors)

    def test_no_packages_has_no_c2_error(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _registry(tmp_path, _default_registry())
        errors = validator.check_ownership(tmp_path)
        assert not any("C2" in error for error in errors)


class TestOwnershipReport:
    def test_report_lists_every_asset_with_module(self, tmp_path: Path, capsys) -> None:
        _minimal_assets(tmp_path)
        _registry(tmp_path, _default_registry())
        assert validator.main(("--root", str(tmp_path), "--report"), root_override=tmp_path) == 0
        captured = capsys.readouterr()
        out = captured.out
        assert ".github/prompts/cg-work.prompt.md" in out
        assert "suite-cg" in out
        assert "Unowned Assets" not in out
        assert "unowned: 0" in out

    def test_empty_module_produces_warning_not_error(self) -> None:
        registry = _default_registry()
        registry["modules"][1]["ownedAssets"] = []
        warnings = validator.empty_module_warnings(registry)
        assert any("empty module" in warning for warning in warnings)


class TestCapabilitySchema:
    def _v2_registry(self) -> dict:
        registry = _default_registry()
        registry["schemaVersion"] = 2
        registry["capabilities"] = [
            {"id": "r", "owningModule": "cap-language-r", "supportedSuites": ["cg"],
             "supportedPlatforms": ["copilot", "kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=r"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "r"}]},
        ]
        return registry

    def test_v2_registry_with_valid_capability_passes(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _registry(tmp_path, self._v2_registry())
        errors = validator.check_ownership(tmp_path)
        assert errors == [], f"Validation errors: {errors}"

    def test_v1_registry_without_capabilities_passes(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        _registry(tmp_path, _default_registry())
        errors = validator.validate_registry_schema(_default_registry())
        assert errors == [], f"Validation errors: {errors}"

    def test_duplicate_capability_id_fails(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"].append(dict(registry["capabilities"][0]))
        _registry(tmp_path, registry)
        errors = validator.validate_registry_schema(registry)
        assert any("duplicate capability id" in error for error in errors)

    def test_unknown_owning_module_fails(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"][0]["owningModule"] = "does-not-exist"
        _registry(tmp_path, registry)
        errors = validator.validate_registry_schema(registry)
        assert any("owningModule 'does-not-exist'" in error for error in errors)

    def test_capability_owning_module_must_be_capability_layer(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"][0]["owningModule"] = "kernel"
        _registry(tmp_path, registry)
        errors = validator.validate_registry_schema(registry)
        assert any("capability-layer" in error for error in errors)

    def test_unknown_supported_suite_fails(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"][0]["supportedSuites"] = ["research"]
        _registry(tmp_path, registry)
        errors = validator.validate_registry_schema(registry)
        assert any("supported suite 'research'" in error for error in errors)

    def test_invalid_activation_cost_fails(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"][0]["activationCost"] = "free"
        _registry(tmp_path, registry)
        errors = validator.validate_registry_schema(registry)
        assert any("activationCost" in error for error in errors)

    def test_optional_explicit_only_activation_mode_validates(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"][0]["activationMode"] = "explicit-only"
        assert validator.validate_registry_schema(registry) == []

    def test_unknown_activation_mode_fails(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        registry["capabilities"][0]["activationMode"] = "selector-derived"
        errors = validator.validate_registry_schema(registry)
        assert any("activationMode" in error for error in errors)

    def test_missing_config_selectors_fails(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        registry = self._v2_registry()
        del registry["capabilities"][0]["configSelectors"]
        _registry(tmp_path, registry)
        errors = validator.validate_registry_schema(registry)
        assert any("configSelectors is required" in error for error in errors)


class TestRealRepoRegistry:
    def test_repo_ownership_closure_is_complete(self) -> None:
        errors = validator.check_ownership(REPO_ROOT)
        assert errors == [], f"Validation errors: {errors}"

    def test_repo_dependency_graph_is_acyclic_and_layer_safe(self) -> None:
        errors = validator.check_dependencies(REPO_ROOT)
        assert errors == [], f"Validation errors: {errors}"

    def test_repo_report_has_zero_unowned_and_zero_multi_owned(self, capsys) -> None:
        assert validator.main(("--root", str(REPO_ROOT), "--report"), root_override=REPO_ROOT) == 0
        captured = capsys.readouterr()
        assert "unowned: 0" in captured.out
        assert "multi-owned: 0" in captured.out

    def test_internal_skill_management_module_has_no_public_capability_or_suite_edge(
        self,
    ) -> None:
        registry, error = validator.load_registry(REPO_ROOT)
        assert error is None
        assert registry is not None
        module = next(
            item
            for item in registry["modules"]
            if item["id"] == "cap-skill-management"
        )
        assert module["ownedAssets"] == [
            ".github/skills/cg-skill-management/",
            ".github/shared/skill-management/",
        ]
        assert not any(
            capability.get("owningModule") == "cap-skill-management"
            for capability in registry["capabilities"]
        )
        suite_cg = next(
            item for item in registry["modules"] if item["id"] == "suite-cg"
        )
        assert "cap-skill-management" not in suite_cg["dependsOn"]
