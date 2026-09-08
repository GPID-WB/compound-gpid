"""Tests for the projection skill-loading baseline matrix (Step 3).

Run from repo root:
    python -m pytest scripts/tests/test_projection_benchmark.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_projection_benchmark as benchmark

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _create_file(repo_root: Path, rel_path: str, content: str = "body\n") -> None:
    path = repo_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _minimal_assets(repo_root: Path) -> None:
    _create_file(repo_root, ".github/prompts/cg-work.prompt.md", "---\ndescription: work\n---\nwork body\n")
    _create_file(repo_root, ".github/prompts/cr-work.prompt.md", "---\ndescription: cr work\n---\ncr body\n")
    _create_file(repo_root, ".github/skills/cg-skill-r-analytical/SKILL.md", "---\ndescription: R\n---\nr body\n")
    _create_file(repo_root, ".github/skills/cr-skill-publication-output/SKILL.md", "---\ndescription: publication output\n---\ncr skill body\n")
    _create_file(repo_root, ".github/shared/context-loading.contract.md", "contract\n")


def _fixture_registry() -> dict:
    return {
        "schemaVersion": 2,
        "description": "test registry",
        "capabilities": [
            {"id": "r", "owningModule": "cap-language-r", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=r"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "r"}]},
            {"id": "python", "owningModule": "cap-language-python", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=python"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "python"}]},
            {"id": "research-output", "owningModule": "cap-research-output", "supportedSuites": ["cr"],
             "supportedPlatforms": ["kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "high", "taskTriggers": ["/cr-work"],
             "configSelectors": []},
            {"id": "research-language", "owningModule": "cap-language-research", "supportedSuites": ["cr"],
             "supportedPlatforms": ["kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "medium", "taskTriggers": ["/cr-work"],
             "configSelectors": []},
        ],
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
                "ownedAssets": [".github/skills/cg-skill-r-*/"],
            },
            {
                "id": "cap-language-python",
                "layer": "capability",
                "displayName": "Python",
                "description": "python",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
            {
                "id": "cap-language-stata",
                "layer": "capability",
                "displayName": "Stata",
                "description": "stata",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
            {
                "id": "cap-language-powershell",
                "layer": "capability",
                "displayName": "PowerShell",
                "description": "pwsh",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
            {
                "id": "cap-research-output",
                "layer": "capability",
                "displayName": "Research output",
                "description": "output",
                "dependsOn": ["kernel"],
                "ownedAssets": [".github/skills/cr-skill-publication-output/"],
            },
            {
                "id": "cap-language-research",
                "layer": "capability",
                "displayName": "Research language",
                "description": "latex/math",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
            {
                "id": "suite-cg",
                "layer": "suite",
                "displayName": "CG",
                "description": "cg",
                "dependsOn": ["kernel"],
                "ownedAssets": [".github/prompts/cg-*.prompt.md"],
            },
            {
                "id": "suite-cr",
                "layer": "suite",
                "displayName": "CR",
                "description": "cr",
                "dependsOn": ["kernel", "cap-research-output", "cap-language-research"],
                "ownedAssets": [".github/prompts/cr-*.prompt.md"],
            },
        ],
    }


def _make_repo(tmp_path: Path) -> Path:
    _minimal_assets(tmp_path)
    _write_json(tmp_path / ".github/shared/module-registry.json", _fixture_registry())
    return tmp_path


def _cg_only_profile() -> dict:
    return {
        "id": "cg-only",
        "description": "cg-only fixture",
        "suites": ["cg"],
        "capabilities": [],
        "config": {"language": "both"},
        "requestedCommand": "/cg-work",
        "expectedRoute": "cg-work",
        "expectedCatalogSummary": "cg active",
        "expectedHardStop": "cr inactive",
        "expectedInventoryIncludes": ["kernel", "suite-cg"],
        "expectedInventoryExcludes": ["suite-cr", "cap-research-output"],
        "hostProcedure": "python scripts/cg_projection_benchmark.py --profiles cg-only --validate",
    }


class TestProfiles:
    def test_all_fixture_profiles_have_required_fields(self) -> None:
        for profile in benchmark.PROFILES:
            for field in (
                "id", "description", "suites", "requestedCommand", "expectedRoute",
                "expectedCatalogSummary", "expectedInventoryIncludes",
                "expectedInventoryExcludes", "hostProcedure",
            ):
                assert field in profile, f"{profile['id']} missing {field}"

    def test_four_profiles_include_all_target_shapes(self) -> None:
        ids = {p["id"] for p in benchmark.PROFILES}
        assert ids == {"cg-only", "cr-only", "mixed", "capability-python"}


class TestCollectProfile:
    def test_collect_profile_baseline_has_comparable_fields(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        record = benchmark.collect_profile_baseline(root, _cg_only_profile())
        assert record["id"] == "cg-only"
        assert "digest" in record["generatedInventory"]
        assert record["oracleStatus"] == "passed"
        assert record["hostEvidence"]["status"] == "available"
        assert record["sourceInventory"]["totalFiles"] >= 0
        assert "contextAudit" in record

    def test_unselected_capability_changes_inventory_but_not_task_success(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        # Without cap-research-output selected (cg-only), the suite-cr module is
        # excluded. An explicit request for a cr command would hard-stop, but the
        # cg-only task oracle must still pass.
        record = benchmark.collect_profile_baseline(root, _cg_only_profile())
        assert "suite-cr" not in record["generatedInventory"]["loadableModuleIds"]
        assert any(
            check["name"] == "excludes suite-cr" and check["ok"]
            for check in record["taskOracle"]["checks"]
        )
        assert record["oracleStatus"] == "passed"

    def test_digest_is_deterministic_and_suite_sensitive(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        first = benchmark._generated_selected_inventory(root, _cg_only_profile())
        second = benchmark._generated_selected_inventory(root, _cg_only_profile())
        assert first["digest"] == second["digest"]
        cr = {"suites": ["cr"], "capabilities": [], "requestedCommand": "/cr-work",
              "expectedRoute": "cr-work", "expectedCatalogSummary": "cr",
              "expectedInventoryIncludes": [], "expectedInventoryExcludes": [],
              "hostProcedure": ""}
        cr_inventory = benchmark._generated_selected_inventory(root, cr)
        assert cr_inventory["digest"] != first["digest"]


class TestOracle:
    def test_oracle_reports_unavailable_when_registry_missing(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        result = benchmark.run_task_oracle(tmp_path, _cg_only_profile())
        assert result["available"] is False
        assert result["passed"] is False
        assert result["error"]

    def test_oracle_route_failure_stops_profile(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        profile = _cg_only_profile()
        profile["expectedRoute"] = "cr-work"
        profile["requestedCommand"] = "/cr-work"
        result = benchmark.run_task_oracle(root, profile)
        assert result["available"] is True
        assert result["passed"] is False
        assert any(check["name"] == "route cr-work" and not check["ok"] for check in result["checks"])

    def test_oracle_flags_inactive_skill_leak(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        # Force an inactive-research skill into the cg-only advertised set by
        # making the research capability suite-eligible for cg.
        registry_path = root / ".github/shared/module-registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        for cap in registry["capabilities"]:
            if cap["id"] == "research-output":
                cap["supportedSuites"] = ["cg"]
        _write_json(registry_path, registry)
        profile = _cg_only_profile()
        result = benchmark.run_task_oracle(root, profile)
        assert result["available"] is True
        leak = next(
            (c for c in result["checks"] if c["name"].startswith("catalog does not advertise")),
            None,
        )
        assert leak is not None, "leak check missing from oracle"
        assert leak["ok"] is False


class TestUnavailableHostEvidence:
    def test_run_benchmark_blocks_missing_registry_end_to_end(self, tmp_path: Path) -> None:
        _minimal_assets(tmp_path)
        payload = benchmark.run_benchmark(tmp_path, ["cg-only"])
        record = payload["profiles"][0]
        assert record["oracleStatus"] == "unavailable"
        assert record["hostEvidence"]["status"] == "unavailable"
        errors = benchmark.validate_payload(payload)
        assert any("oracle is unavailable" in error for error in errors)

    def test_unknown_profile_id_raises(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        with pytest.raises(ValueError, match="unknown profile id"):
            benchmark.run_benchmark(root, ["nope"])


class TestValidation:
    def test_validate_rejects_incomplete_record(self) -> None:
        payload = {
            "kind": "skill-loading-baseline",
            "disclaimer": benchmark.DISCLAIMER,
            "profiles": [{"id": "broken"}],
        }
        errors = benchmark.validate_payload(payload)
        assert errors

    def test_validate_rejects_failed_oracle(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        payload = benchmark.run_benchmark(root, ["cg-only"])
        payload["profiles"][0]["oracleStatus"] = "failed"
        errors = benchmark.validate_payload(payload)
        assert any("task oracle failed" in error for error in errors)

    def test_validate_rejects_incomplete_required_profile(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        payload = benchmark.run_benchmark(root, ["cg-only"])
        del payload["profiles"][0]["expectedRoute"]
        errors = benchmark.validate_payload(payload)
        assert any("missing required field" in error for error in errors)

    def test_validate_blocks_unavailable_required_host_evidence(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        payload = benchmark.run_benchmark(root, ["cg-only"])
        payload["profiles"][0]["hostEvidence"] = {"status": "unavailable", "note": "host missing"}
        errors = benchmark.validate_payload(payload)
        assert any("requires host evidence" in error for error in errors)

    def test_validate_passes_complete_fixture_payload(self, tmp_path: Path) -> None:
        root = _make_repo(tmp_path)
        payload = benchmark.run_benchmark(root)
        for record in payload["profiles"]:
            assert record["oracleStatus"] == "passed"
        assert benchmark.validate_payload(payload) == [], benchmark.validate_payload(payload)


class TestRealRepo:
    def test_real_repo_baseline_validates(self) -> None:
        payload = benchmark.run_benchmark(REPO_ROOT)
        errors = benchmark.validate_payload(payload)
        assert errors == [], f"Validation errors: {errors}"

    def test_real_repo_profiles_pass_oracles(self) -> None:
        payload = benchmark.run_benchmark(REPO_ROOT)
        for record in payload["profiles"]:
            assert record["oracleStatus"] == "passed", record["id"]
