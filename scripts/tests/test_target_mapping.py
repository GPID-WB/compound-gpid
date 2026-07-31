"""Tests for target-mapping.json schema validation.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_mapping.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_generate_targets as gen

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_repo_mapping() -> dict:
    return json.loads((REPO_ROOT / ".github/shared/target-mapping.json").read_text(encoding="utf-8"))


class TestTargetMappingSchema:
    def test_repo_target_mapping_validates(self) -> None:
        data = _load_repo_mapping()
        errors = gen.validate_target_mapping(data)
        assert errors == [], f"Validation errors: {errors}"

    def test_schema_version_is_1(self) -> None:
        data = _load_repo_mapping()
        assert data["schemaVersion"] == 1

    def test_json_schema_closes_mapping_objects(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "scripts/schemas/target_mapping_schema.json").read_text(encoding="utf-8")
        )
        definitions = schema["definitions"]
        assert schema["additionalProperties"] is False
        target = definitions["target"]
        assert target["additionalProperties"] is False
        for name in ("capabilities", "formats", "outputPaths"):
            assert target["properties"][name]["additionalProperties"] is False
        assert definitions["installUnit"]["additionalProperties"] is False

    def test_has_four_targets(self) -> None:
        data = _load_repo_mapping()
        ids = {t["id"] for t in data["targets"]}
        assert ids == {"copilot", "claude-code", "codex", "opencode"}

    def test_copilot_has_null_generated_tree_path(self) -> None:
        data = _load_repo_mapping()
        copilot = next(t for t in data["targets"] if t["id"] == "copilot")
        assert copilot["generatedTreePath"] is None

    def test_non_copilot_targets_have_generated_tree_path(self) -> None:
        data = _load_repo_mapping()
        for target in data["targets"]:
            if target["id"] == "copilot":
                continue
            assert target["generatedTreePath"] is not None
            assert target["generatedTreePath"].startswith(".")

    def test_all_targets_have_required_capabilities(self) -> None:
        data = _load_repo_mapping()
        for target in data["targets"]:
            caps = target["capabilities"]
            for field in gen.REQUIRED_CAPABILITY_FIELDS:
                assert field in caps, f"{target['id']}: missing capability {field}"
                assert isinstance(caps[field], bool)

    def test_all_targets_define_runtime_output_roots(self) -> None:
        data = _load_repo_mapping()
        for target in data["targets"]:
            assert set(gen.REQUIRED_OUTPUT_PATH_FIELDS) <= set(target["outputPaths"])

    def test_model_mapping_fields_are_absent(self) -> None:
        data = _load_repo_mapping()
        for target in data["targets"]:
            assert "modelMappingMode" not in target
            assert "modelMapping" not in target
            assert "modelMapping" not in target["outputPaths"]

    def test_codex_has_fallback_agent_format(self) -> None:
        data = _load_repo_mapping()
        codex = next(t for t in data["targets"] if t["id"] == "codex")
        assert "fallbackAgentFormat" in codex["formats"]

    def test_opencode_is_multi_vendor(self) -> None:
        data = _load_repo_mapping()
        opencode = next(t for t in data["targets"] if t["id"] == "opencode")
        assert opencode["capabilities"]["supportsMultiVendorModels"] is True

    def test_all_targets_define_install_units(self) -> None:
        data = _load_repo_mapping()
        for target in data["targets"]:
            units = target.get("installUnits")
            assert isinstance(units, list), f"{target['id']}: missing installUnits"
            assert units, f"{target['id']}: empty installUnits"

    def test_opencode_config_install_unit_has_manual_snippet(self) -> None:
        data = _load_repo_mapping()
        opencode = next(t for t in data["targets"] if t["id"] == "opencode")
        config_units = [u for u in opencode["installUnits"] if u["target"] == ".opencode/opencode.json"]
        assert len(config_units) == 1
        assert config_units[0]["strategy"] == "config-copy-or-snippet"
        assert "manualSnippet" in config_units[0]


class TestTargetMappingValidation:
    def test_missing_schema_version_fails(self) -> None:
        errors = gen.validate_target_mapping({"targets": []})
        assert any("schemaVersion" in e for e in errors)

    def test_missing_targets_fails(self) -> None:
        errors = gen.validate_target_mapping({"schemaVersion": 1})
        assert any("targets" in e for e in errors)

    def test_empty_targets_fails(self) -> None:
        errors = gen.validate_target_mapping({"schemaVersion": 1, "targets": []})
        assert any("non-empty" in e for e in errors)

    def test_duplicate_target_id_fails(self) -> None:
        data = {
            "schemaVersion": 1,
            "targets": [
                {"id": "x", "name": "X", "generatedTreePath": ".x",
                 "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                 "formats": {f: "x" for f in gen.REQUIRED_FORMAT_FIELDS},
                 "outputPaths": {f: f".x/{f}" for f in gen.REQUIRED_OUTPUT_PATH_FIELDS}},
                {"id": "x", "name": "X2", "generatedTreePath": ".x2",
                 "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                 "formats": {f: "x" for f in gen.REQUIRED_FORMAT_FIELDS},
                 "outputPaths": {f: f".x2/{f}" for f in gen.REQUIRED_OUTPUT_PATH_FIELDS}},
            ],
        }
        errors = gen.validate_target_mapping(data)
        assert any("duplicate" in e for e in errors)

    def test_stale_model_mapping_fields_fail(self) -> None:
        data = {
            "schemaVersion": 1,
            "targets": [
                {"id": "x", "name": "X", "generatedTreePath": ".x",
                 "modelMappingMode": "exact", "modelMapping": {"coding": "model"},
                 "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                 "formats": {f: "x" for f in gen.REQUIRED_FORMAT_FIELDS},
                 "outputPaths": {**{f: f".x/{f}" for f in gen.REQUIRED_OUTPUT_PATH_FIELDS}, "modelMapping": ".x/models.json"}},
            ],
        }
        errors = gen.validate_target_mapping(data)
        assert any("modelMappingMode" in e for e in errors)
        assert any("modelMapping is not supported" in e for e in errors)
        assert any("outputPaths.modelMapping" in e for e in errors)

    def test_missing_capability_fails(self) -> None:
        data = {
            "schemaVersion": 1,
            "targets": [
                {"id": "x", "name": "X", "generatedTreePath": ".x",
                 "capabilities": {"supportsNativeCommands": True},
                 "formats": {f: "x" for f in gen.REQUIRED_FORMAT_FIELDS},
                 "outputPaths": {f: f".x/{f}" for f in gen.REQUIRED_OUTPUT_PATH_FIELDS}},
            ],
        }
        errors = gen.validate_target_mapping(data)
        assert any("capabilities" in e for e in errors)

    def test_install_unit_missing_source_fails(self) -> None:
        data = _load_repo_mapping()
        broken = json.loads(json.dumps(data))
        del broken["targets"][0]["installUnits"][0]["source"]
        errors = gen.validate_target_mapping(broken)
        assert any("installUnits" in e and "source" in e for e in errors)

    def test_install_unit_missing_target_fails(self) -> None:
        data = _load_repo_mapping()
        broken = json.loads(json.dumps(data))
        del broken["targets"][0]["installUnits"][0]["target"]
        errors = gen.validate_target_mapping(broken)
        assert any("installUnits" in e and "target" in e for e in errors)

    def test_install_unit_unknown_type_fails(self) -> None:
        data = _load_repo_mapping()
        broken = json.loads(json.dumps(data))
        broken["targets"][0]["installUnits"][0]["type"] = "unknown"
        errors = gen.validate_target_mapping(broken)
        assert any("installUnits" in e and "type" in e for e in errors)

    def test_install_unit_unknown_strategy_fails(self) -> None:
        data = _load_repo_mapping()
        broken = json.loads(json.dumps(data))
        broken["targets"][0]["installUnits"][0]["strategy"] = "unknown"
        errors = gen.validate_target_mapping(broken)
        assert any("installUnits" in e and "strategy" in e for e in errors)

    def test_schema_version_other_than_one_fails(self) -> None:
        data = _load_repo_mapping()
        data["schemaVersion"] = 2
        errors = gen.validate_target_mapping(data)
        assert any("schemaVersion" in error and "1" in error for error in errors)

    def test_description_is_required_and_string(self) -> None:
        data = _load_repo_mapping()
        del data["description"]
        assert any("description" in error for error in gen.validate_target_mapping(data))
        data["description"] = 3
        assert any("description" in error for error in gen.validate_target_mapping(data))

    def test_target_id_matches_schema_pattern(self) -> None:
        data = _load_repo_mapping()
        data["targets"][0]["id"] = "Bad_ID"
        errors = gen.validate_target_mapping(data)
        assert any("id" in error and "lowercase" in error for error in errors)

    def test_repo_path_python_validator_is_canonical(self) -> None:
        """Python _validate_repo_relative_path is the canonical validator for repoPath.

        The JSON Schema regex is a basic structural guard only. Full constraints
        (empty components, '.' parts, trailing dots/spaces, Windows reserved names)
        are enforced by the Python validator. This test documents the relationship.
        """
        assert gen._validate_repo_relative_path("desc", "a//b") != []
        assert gen._validate_repo_relative_path("desc", "a/./b") != []
        assert gen._validate_repo_relative_path("desc", "a/ ") != []
        assert gen._validate_repo_relative_path("desc", "a/b.") != []
        assert gen._validate_repo_relative_path("desc", "a/CON/b") != []
