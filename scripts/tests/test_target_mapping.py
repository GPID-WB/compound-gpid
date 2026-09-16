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


@pytest.mark.parametrize("asset,keys", [
    ("cg-autopilot.prompt.md", ("agent",)),
    ("cg-autopilot.prompt.md", ("subtask",)),
    ("cg-autopilot.agent.md", ("mode",)),
    ("cg-autopilot.agent.md", ("permission",)),
    ("cg-autopilot.agent.md", ("permission", "*")),
    ("cg-autopilot.agent.md", ("permission", "task")),
    ("cg-autopilot.agent.md", ("permission", "task", "cg-workflow-stage")),
    ("cg-workflow-stage.agent.md", ("mode",)),
    ("cg-workflow-stage.agent.md", ("permission",)),
    ("cg-workflow-stage.agent.md", ("permission", "*")),
    ("cg-workflow-stage.agent.md", ("permission", "task")),
    ("cg-workflow-stage.agent.md", ("permission", "task", "cg-bootstrap-leaf")),
    ("cg-fix-problems.agent.md", ("permission", "task")),
    ("cg-bootstrap-leaf.agent.md", ("mode",)),
    ("cg-bootstrap-leaf.agent.md", ("permission",)),
    ("cg-bootstrap-leaf.agent.md", ("permission", "bash")),
    ("cg-bootstrap-leaf.agent.md", ("permission", "bash", "git rev-parse*")),
    ("cg-bootstrap-leaf.agent.md", ("permission", "cg_native_identity")),
])
def test_metadata_missing_required_field_fails(asset: str, keys: tuple[str, ...]) -> None:
    """Remove one field from a valid map; no sibling defect may mask it."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    node = target["assetMetadata"][asset]
    for key in keys[:-1]:
        node = node[key]
    del node[keys[-1]]
    errors = gen.validate_target_mapping(data)
    assert any(f"assetMetadata.{asset}" in e and "required" in e for e in errors)
    category = "prompts" if asset.endswith(".prompt.md") else "agents"
    source = {"relative_path": f".github/{category}/{asset}",
              "frontmatter": {"description": "Probe"}, "body": "Probe"}
    emit = gen._emit_command if category == "prompts" else gen._emit_agent
    with pytest.raises(gen.MappingValidationError, match="required"):
        emit(source, target)


@pytest.mark.parametrize("value", [True, 1, None, [], {}, "false"])
def test_subtask_requires_literal_false(value: object) -> None:
    """Only Boolean false routes the command to its dedicated primary."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    target["assetMetadata"]["cg-autopilot.prompt.md"]["subtask"] = value
    assert "assetMetadata.cg-autopilot.prompt.md.subtask: must be false" in gen.validate_target_mapping(data)


@pytest.mark.parametrize("value", [True, 1, None, [], {}, "invalid", "ask", "deny"])
def test_task_action_validation_is_not_masked_by_missing_fallback(value: object) -> None:
    """A complete otherwise-valid map isolates the action's type/value check."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    target["assetMetadata"]["cg-workflow-stage.agent.md"]["permission"]["task"]["cg-bootstrap-leaf"] = value
    assert gen.validate_target_mapping(data) == [
        "assetMetadata.cg-workflow-stage.agent.md.permission.task.cg-bootstrap-leaf: must be allow"]


def test_unknown_task_target_validation_is_not_masked() -> None:
    """Keep deny fallback and all required targets while adding one unknown."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    target["assetMetadata"]["cg-workflow-stage.agent.md"]["permission"]["task"]["unknown"] = "allow"
    assert gen.validate_target_mapping(data) == [
        "assetMetadata.cg-workflow-stage.agent.md.permission.task: unknown fields: unknown"]


@pytest.mark.parametrize("asset", ["cg-autopilot.agent.md", "cg-workflow-stage.agent.md", "cg-bootstrap-leaf.agent.md"])
def test_missing_asset_metadata_entry_fails(asset: str) -> None:
    """Removing a whole bootstrap entry cannot restore permissive defaults."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    del target["assetMetadata"][asset]
    assert any("assetMetadata" in e and "required" in e for e in gen.validate_target_mapping(data))


@pytest.mark.parametrize("asset,key", [
    ("cg-autopilot.agent.md", "permission"),
    ("cg-workflow-stage.agent.md", "permission"),
    ("cg-fix-problems.agent.md", "permission"),
])
def test_task_fallback_never_allows(asset: str, key: str) -> None:
    """A wildcard allow fallback is rejected for every bootstrap Task map.
    The leaf has no Task map at all and is rejected separately."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    task = target["assetMetadata"][asset][key]["task"]
    task["*"] = "allow"
    errors = gen.validate_target_mapping(data)
    assert any(f"assetMetadata.{asset}.{key}.task.*" in e for e in errors)


def test_wildcard_tool_allow_is_rejected() -> None:
    """The leaf cannot gain an unrestricted tool fallback."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    assert target["assetMetadata"]["cg-bootstrap-leaf.agent.md"]["permission"]["*"] == "deny"
    target["assetMetadata"]["cg-bootstrap-leaf.agent.md"]["permission"]["*"] = "allow"
    assert any("assetMetadata.cg-bootstrap-leaf.agent.md.permission.*" in e
               for e in gen.validate_target_mapping(data))


def test_leaf_with_task_key_is_rejected() -> None:
    """A leaf never delegates; a task map on the leaf is an unknown field."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    target["assetMetadata"]["cg-bootstrap-leaf.agent.md"]["permission"]["task"] = {"*": "ask", "general": "allow"}
    errors = gen.validate_target_mapping(data)
    assert any("assetMetadata.cg-bootstrap-leaf.agent.md.permission" in e and "unknown" in e
               for e in errors)


def test_leaf_git_only_bash_map_is_required() -> None:
    """The leaf's bash map is closed: only the contract's read-only Git probes."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    bash = target["assetMetadata"]["cg-bootstrap-leaf.agent.md"]["permission"]["bash"]
    assert bash["*"] == "deny"
    assert set(bash) == {"*", "git branch --show-current*", "git rev-parse*", "git status --porcelain*"}
    bash["git commit*"] = "allow"
    assert any("assetMetadata.cg-bootstrap-leaf.agent.md.permission.bash" in e and "unknown" in e
               for e in gen.validate_target_mapping(data))


def test_leaf_has_native_identity_ask_only() -> None:
    """The leaf gains exactly cg_native_identity ask, no delegation or write surface."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == "kilo")
    permission = target["assetMetadata"]["cg-bootstrap-leaf.agent.md"]["permission"]
    assert permission["cg_native_identity"] == "ask"
    assert permission["*"] == "deny"
    for forbidden in ("task", "edit", "webfetch", "network", "model"):
        assert forbidden not in permission
    assert permission["bash"] == {
        "*": "deny", "git branch --show-current*": "allow",
        "git rev-parse*": "allow", "git status --porcelain*": "allow"}
    assert gen.validate_target_mapping(data) == []


def test_leaf_body_verifies_native_identity_before_probes() -> None:
    """The leaf must call cg_native_identity once and fail closed before any bash."""
    body = (REPO_ROOT / ".github/agents/cg-bootstrap-leaf.agent.md").read_text(encoding="utf-8")
    assert "cg_native_identity" in body
    assert "native-identity-unverified" in body
    assert "qualification" in body


def test_missing_bootstrap_metadata_blocks_emission() -> None:
    """Even direct emission must not supply the ordinary subagent default."""
    target = next(t for t in _load_repo_mapping()["targets"] if t["id"] == "kilo")
    del target["assetMetadata"]
    source = {"relative_path": ".github/agents/cg-autopilot.agent.md",
              "frontmatter": {"description": "Probe"}, "body": "Probe"}
    with pytest.raises(gen.MappingValidationError, match="required bootstrap metadata"):
        gen._emit_agent(source, target)


@pytest.mark.parametrize("target_id", ["copilot", "claude-code", "codex", "opencode"])
def test_asset_metadata_is_kilo_only(target_id: str) -> None:
    """Other adapters cannot receive Kilo routing metadata."""
    data = _load_repo_mapping()
    target = next(t for t in data["targets"] if t["id"] == target_id)
    target["assetMetadata"] = {"cg-autopilot.prompt.md": {"subtask": False}}
    assert any("assetMetadata" in error for error in gen.validate_target_mapping(data))


def test_typed_bootstrap_metadata_validates() -> None:
    """Allow typed command routing and a closed parent Task permission map."""
    data = _load_repo_mapping()
    assert gen.validate_target_mapping(data) == []


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

    def test_has_five_targets(self) -> None:
        data = _load_repo_mapping()
        ids = {t["id"] for t in data["targets"]}
        assert ids == {"copilot", "claude-code", "codex", "opencode", "kilo"}

    def test_copilot_has_skill_only_projection_mode(self) -> None:
        data = _load_repo_mapping()
        copilot = next(t for t in data["targets"] if t["id"] == "copilot")
        assert copilot["generatedTreePath"] is None
        assert copilot["projectedCategories"] == ["skills"]
        assert copilot["projectRoots"]["managed"] == [".github/skills"]
        assert not any(
            unit["target"] == ".github/skills" for unit in copilot["installUnits"]
        )

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
            assert all("model-mapping" not in str(unit) for unit in target.get("installUnits", []))

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

    def test_source_marker_is_not_an_output_or_install_path(self) -> None:
        data = _load_repo_mapping()
        marker = ".compound-gpid-source.json"
        for target in data["targets"]:
            assert all(marker not in path for path in target["outputPaths"].values())
            for unit in target["installUnits"]:
                assert marker not in unit["source"]
                assert marker not in unit["target"]

    def test_opencode_config_install_unit_has_manual_snippet(self) -> None:
        data = _load_repo_mapping()
        opencode = next(t for t in data["targets"] if t["id"] == "opencode")
        config_units = [u for u in opencode["installUnits"] if u["target"] == ".opencode/opencode.json"]
        assert len(config_units) == 1
        assert config_units[0]["strategy"] == "config-copy-or-snippet"
        assert "manualSnippet" in config_units[0]

    def test_kilo_target_has_generated_tree_and_config(self) -> None:
        data = _load_repo_mapping()
        kilo = next(t for t in data["targets"] if t["id"] == "kilo")
        assert kilo["generatedTreePath"] == ".kilo"
        assert kilo["outputPaths"]["config"] == ".kilo/kilo.json"
        assert kilo["outputPaths"]["commands"] == ".kilo/commands"
        assert kilo["outputPaths"]["skills"] == ".kilo/skills"
        assert kilo["outputPaths"]["agents"] == ".kilo/agents"
        config_units = [u for u in kilo["installUnits"] if u["target"] == ".kilo/kilo.json"]
        assert len(config_units) == 1
        assert config_units[0]["strategy"] == "config-copy-or-snippet"

    def test_kilo_directory_units_are_project_local_copies(self) -> None:
        data = _load_repo_mapping()
        kilo = next(t for t in data["targets"] if t["id"] == "kilo")
        directory_units = [u for u in kilo["installUnits"] if u["type"] == "directory"]
        assert directory_units
        assert all(u["strategy"] == "copy-directory" for u in directory_units)

    def test_codex_directories_remain_link_directory(self) -> None:
        data = gen.load_target_mapping(REPO_ROOT)
        codex = next(t for t in data["targets"] if t["id"] == "codex")
        directories = [
            unit for unit in codex["installUnits"]
            if unit["type"] == "directory"
        ]
        assert len(directories) == 5
        assert {unit["strategy"] for unit in directories} == {"link-directory"}
        assert any(unit["target"] == ".agents/skills" for unit in directories)


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
                {"id": "x", "name": "X", "generatedTreePath": ".x", "modelMappingMode": "exact",
                 "capabilities": {f: True for f in gen.REQUIRED_CAPABILITY_FIELDS},
                 "formats": {f: "x" for f in gen.REQUIRED_FORMAT_FIELDS},
                 "outputPaths": {**{f: f".x/{f}" for f in gen.REQUIRED_OUTPUT_PATH_FIELDS}, "modelMapping": ".x/models.json"},
                 "modelMapping": {"coding": "model"}},
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

    def test_projected_categories_reject_unknown_or_duplicate_values(self) -> None:
        data = _load_repo_mapping()
        copilot = data["targets"][0]
        copilot["projectedCategories"] = ["skills", "prompts"]
        assert any("projectedCategories" in error for error in gen.validate_target_mapping(data))
        copilot["projectedCategories"] = ["skills", "skills"]
        assert any("projectedCategories" in error for error in gen.validate_target_mapping(data))

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
