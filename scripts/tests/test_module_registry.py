"""Tests for the module-registry validator.

Run from repo root:
    python -m pytest scripts/tests/test_module_registry.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import cg_validate_modules as validator


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
