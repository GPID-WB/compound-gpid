"""Contract tests for the versioned skill-management schema subset."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from skill_management import contracts
from skill_management.planning import OperationOutcome, result_envelope


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = REPO_ROOT / ".github/shared/skill-management/contracts"


def _contract(name: str) -> dict:
    return contracts.load_contract(CONTRACT_ROOT / name)


def _finding() -> dict:
    return {
        "code": "contract.invalid",
        "severity": "error",
        "path": "/arguments/id",
        "message": "The identifier is invalid.",
        "remediation": "Use a lowercase skill identifier.",
    }


def _request() -> dict:
    return {
        "schema": "cg-skill-request-v1",
        "operation": "validate",
        "phase": "read",
        "root": ".",
        "arguments": {"argv": ["--all"]},
    }


def _result() -> dict:
    return {
        "schema": "cg-skill-result-v1",
        "ok": True,
        "exitCode": 0,
        "operation": "validate",
        "phase": "read",
        "role": "consumer",
        "changed": False,
        "manifestHealth": "fresh",
        "actions": [],
        "findings": [],
        "data": {},
    }


def _plan() -> dict:
    return {
        "schema": "cg-skill-plan-v1",
        "digest": "a" * 64,
        "operation": "activate",
        "phase": "plan",
        "role": "consumer",
        "projectRoot": ".",
        "sourceRoot": ".",
        "arguments": {"capability": "project-skill-example"},
        "bindings": {
            "sourceRevision": "b" * 40,
            "configurationDigest": "c" * 64,
            "canonicalRegistryDigest": "d" * 64,
            "projectRegistryDigest": "e" * 64,
            "manifestDigest": "f" * 64,
            "provenanceDigest": "0" * 64,
            "referencesDigest": "1" * 64,
            "bundleInventoryDigest": "2" * 64,
        },
        "actions": [
            {
                "kind": "update-config",
                "path": "compound-gpid.local.md",
                "description": "Select the explicit project capability.",
            }
        ],
        "findings": [],
    }


def _descriptor() -> dict:
    return {
        "schema": "cg-skill-operation-descriptor-v1",
        "operation": "validate",
        "version": 1,
        "state": "active",
        "roles": ["consumer", "maintainer"],
        "phases": ["read"],
        "handler": "skill_management.operations.validate:handle",
        "contract": ".github/shared/skill-management/contracts/validate-v1.schema.json",
        "workflow": ".github/skills/cg-skill-management/workflows/validate.md",
        "documentation": "docs/skills/management/commands/validate.md",
        "tests": ["scripts/tests/test_skill_management_read.py"],
    }


def _project_registry() -> dict:
    return {
        "schema": "cg-project-skill-registry-v1",
        "schemaVersion": 1,
        "records": [
            {
                "id": "example",
                "origin": "project-imported",
                "owner": "project-local",
                "capability": "project-skill-example",
                "activationMode": "explicit-only",
                "sourcePath": ".compound-gpid/skills/example",
                "supportedSuites": ["cg"],
                "supportedPlatforms": ["copilot", "kilo"],
                "admission": "approved",
                "lifecycle": "current",
                "provenanceId": "example",
                "bundleDigest": "3" * 64,
            }
        ],
    }


def _provenance() -> dict:
    return {
        "schema": "cg-skill-provenance-v1",
        "schemaVersion": 1,
        "skillId": "example",
        "origin": "project-imported",
        "admission": "approved",
        "lifecycle": "current",
        "source": {
            "repository": "https://github.com/example/skills",
            "path": "skills/example",
            "commit": "4" * 40,
            "bundleDigest": "5" * 64,
        },
        "history": [
            {
                "sequence": 1,
                "event": "imported",
                "commit": "4" * 40,
                "bundleDigest": "5" * 64,
                "approval": {
                    "actor": "project-user",
                    "reviewReference": "commit:1234567",
                },
            }
        ],
        "migrations": [],
    }


def _attestation() -> dict:
    return {
        "schema": "cg-skill-release-attestation-v1",
        "schemaVersion": 1,
        "releaseTag": "v2.0.0",
        "tagRefObjectSha": "6" * 40,
        "peeledCommitSha": "7" * 40,
        "releasePayloadSha256": "8" * 64,
        "deprecationRecordDigests": {"example": "9" * 64},
        "reviewReference": "https://github.com/GPID-WB/compound-gpid/pull/1",
    }


def _migration() -> dict:
    return {
        "schema": "cg-skill-migration-v1",
        "schemaVersion": 1,
        "id": "example-to-next",
        "skillId": "example",
        "edits": [
            {
                "path": "docs/example.md",
                "expectedSha256": "a" * 64,
                "replacement": "Use next.\n",
            }
        ],
        "reviewer": "maintainer",
        "approvalReference": "review=" + "b" * 40,
    }


@pytest.mark.parametrize(
    "name",
    [
        "schema-subset-v1.schema.json",
        "operation-descriptor-v1.schema.json",
        "request-v1.schema.json",
        "result-v1.schema.json",
        "plan-v1.schema.json",
        "project-registry-v1.schema.json",
        "provenance-v1.schema.json",
        "release-attestation-v1.schema.json",
        "migration-v1.schema.json",
    ],
)
def test_each_contract_is_valid_in_the_closed_schema_subset(name: str) -> None:
    assert contracts.validate_schema_definition(_contract(name)) == ()


def test_each_contract_is_accepted_by_the_committed_meta_contract() -> None:
    meta_contract = _contract("schema-subset-v1.schema.json")
    for path in sorted(CONTRACT_ROOT.glob("*.schema.json")):
        assert contracts.validate_instance(
            contracts.load_contract(path), meta_contract
        ) == (), path.name


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("operation-descriptor-v1.schema.json", _descriptor()),
        ("request-v1.schema.json", _request()),
        ("result-v1.schema.json", _result()),
        ("plan-v1.schema.json", _plan()),
        ("project-registry-v1.schema.json", _project_registry()),
        ("provenance-v1.schema.json", _provenance()),
        ("release-attestation-v1.schema.json", _attestation()),
        ("migration-v1.schema.json", _migration()),
    ],
)
def test_valid_contract_fixtures_pass(name: str, value: dict) -> None:
    assert contracts.validate_instance(value, _contract(name)) == ()


def test_unsupported_schema_keyword_is_rejected_with_stable_finding() -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "invalid-v1",
        "type": "string",
        "format": "uri",
    }
    findings = contracts.validate_schema_definition(schema)
    assert [(item.path, item.code) for item in findings] == [
        ("/format", "schema.unsupported-keyword")
    ]


def test_remote_reference_is_rejected() -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "invalid-v1",
        "$ref": "https://example.test/schema.json",
    }
    findings = contracts.validate_schema_definition(schema)
    assert any(item.code == "schema.nonlocal-reference" for item in findings)


def test_runtime_validation_uses_the_same_closed_meta_validation() -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "invalid-v1",
        "type": "string",
        "format": "uri",
    }
    assert contracts.validate_instance("https://example.test", schema) == (
        contracts.validate_schema_definition(schema)
    )


@pytest.mark.parametrize(
    "source",
    [
        '{"$schema":"compound-gpid-schema-subset-v1","$id":"x","type":"string","type":"object"}',
        '{"$schema":"compound-gpid-schema-subset-v1","$id":"x","const":NaN}',
        '{"$schema":"compound-gpid-schema-subset-v1","$id":"x","const":Infinity}',
        '{"$schema":"compound-gpid-schema-subset-v1","$id":"x","const":-Infinity}',
    ],
)
def test_contract_loader_rejects_non_json_or_duplicate_members(
    tmp_path: Path, source: str
) -> None:
    path = tmp_path / "contract.json"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate|finite|JSON"):
        contracts.load_contract(path)


@pytest.mark.parametrize("escaped", [r"\ud800", r"\udfff"])
def test_contract_loader_rejects_lone_unicode_surrogates(
    tmp_path: Path, escaped: str
) -> None:
    path = tmp_path / "contract.json"
    path.write_text(
        '{"$schema":"compound-gpid-schema-subset-v1","$id":"x","const":"'
        + escaped
        + '"}',
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="Unicode|scalar|json-unicode"):
        contracts.load_contract(path)


@pytest.mark.parametrize(
    "value",
    [
        {"bad": math.nan},
        {"bad": math.inf},
        {"bad": b"bytes"},
        {"bad": ("tuple",)},
        {1: "non-string key"},
    ],
)
def test_runtime_validation_rejects_values_that_are_not_json(value: object) -> None:
    findings = contracts.validate_instance(
        value,
        {
            "$schema": contracts.SCHEMA_DIALECT,
            "$id": "open-object-v1",
            "type": "object",
            "additionalProperties": True,
        },
    )
    assert any(item.code.startswith("contract.json") for item in findings)


@pytest.mark.parametrize(
    ("schema", "code"),
    [
        (
            {"$schema": contracts.SCHEMA_DIALECT, "$id": "cycle-v1", "$ref": "#"},
            "schema.reference-cycle",
        ),
        (
            {
                "$schema": contracts.SCHEMA_DIALECT,
                "$id": "wrong-keyword-v1",
                "type": "array",
                "minLength": 1,
            },
            "schema.keyword-type",
        ),
        (
            {
                "$schema": contracts.SCHEMA_DIALECT,
                "$id": "unsafe-pattern-v1",
                "type": "string",
                "pattern": "^(a+)+$",
            },
            "schema.unsafe-pattern",
        ),
    ],
)
def test_schema_bypass_and_dos_constructs_are_rejected(
    schema: dict, code: str
) -> None:
    assert any(
        finding.code == code
        for finding in contracts.validate_schema_definition(schema)
    )


@pytest.mark.parametrize("pattern", [r"^(?:a+)+$", r"^(a|aa)+$"])
def test_additional_exponential_regex_shapes_are_rejected(pattern: str) -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "unsafe-v1",
        "type": "string",
        "pattern": pattern,
    }
    assert any(
        item.code == "schema.unsafe-pattern"
        for item in contracts.validate_schema_definition(schema)
    )


def test_invalid_json_pointer_escape_is_rejected() -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "pointer-v1",
        "$defs": {"bad~2name": {"type": "string"}},
        "$ref": "#/$defs/bad~2name",
    }
    assert any(
        item.code == "schema.unresolved-reference"
        for item in contracts.validate_schema_definition(schema)
    )


def test_meta_contract_and_runtime_reject_the_same_semantic_schema_error() -> None:
    invalid = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "invalid-v1",
        "type": "array",
        "minLength": 1,
    }
    findings = contracts.validate_instance(
        invalid,
        _contract("schema-subset-v1.schema.json"),
    )
    assert any(item.code == "schema.keyword-type" for item in findings)


def test_unknown_keys_and_missing_fields_fail_closed() -> None:
    request = _request()
    request.pop("operation")
    request["unexpected"] = True
    findings = contracts.validate_instance(request, _contract("request-v1.schema.json"))
    assert {(item.path, item.code) for item in findings} == {
        ("/operation", "contract.required"),
        ("/unexpected", "contract.additional-property"),
    }


@pytest.mark.parametrize("exit_code", [-1, 9, "0"])
def test_invalid_result_exit_codes_are_rejected(exit_code: object) -> None:
    result = _result()
    result["exitCode"] = exit_code
    assert contracts.validate_instance(result, _contract("result-v1.schema.json"))


def test_success_result_cannot_use_nonzero_exit_code() -> None:
    result = _result()
    result["exitCode"] = contracts.EXIT_ROLE_CONTEXT
    findings = contracts.validate_instance(result, _contract("result-v1.schema.json"))
    assert any(item.code == "contract.result-exit-code" for item in findings)


def test_result_cannot_report_success_with_an_error_finding() -> None:
    result = _result()
    result["findings"] = [_finding()]
    findings = contracts.validate_instance(result, _contract("result-v1.schema.json"))
    assert any(item.code == "contract.result-error-success" for item in findings)

    envelope = result_envelope(
        "validate",
        "read",
        "consumer",
        OperationOutcome(
            findings=(
                contracts.ContractFinding(
                    "/arguments",
                    "contract.invalid",
                    "error",
                    "Invalid input.",
                    "Repair the input.",
                ),
            ),
            exit_code=0,
        ),
    )
    assert envelope["ok"] is False
    assert envelope["exitCode"] == contracts.EXIT_CONTRACT


def test_result_schema_advertised_automation_role_is_runtime_valid() -> None:
    result = _result()
    result["role"] = "automation"
    assert contracts.validate_instance(result, _contract("result-v1.schema.json")) == ()


def test_invalid_finding_and_lifecycle_values_are_rejected() -> None:
    result = _result()
    finding = _finding()
    finding["severity"] = "fatal"
    result["findings"] = [finding]
    assert contracts.validate_instance(result, _contract("result-v1.schema.json"))

    registry = _project_registry()
    registry["records"][0]["lifecycle"] = "inactive"
    assert contracts.validate_project_registry(registry)


def test_project_registry_rejects_duplicate_ids_and_portable_shadowing() -> None:
    registry = _project_registry()
    duplicate = copy.deepcopy(registry["records"][0])
    duplicate["id"] = "Example"
    duplicate["capability"] = "project-skill-Example"
    duplicate["sourcePath"] = ".compound-gpid/skills/Example"
    registry["records"].append(duplicate)
    findings = contracts.validate_project_registry(registry)
    assert any(item.code == "registry.duplicate-id" for item in findings)

    findings = contracts.validate_project_registry(
        _project_registry(), canonical_ids=("example",)
    )
    assert any(item.code == "registry.canonical-shadow" for item in findings)


def test_project_registry_enforces_one_to_one_explicit_only_selection() -> None:
    registry = _project_registry()
    record = registry["records"][0]
    record["activationMode"] = "selector-derived"
    record["capability"] = "project-skill-other"
    findings = contracts.validate_project_registry(registry)
    assert {item.code for item in findings} >= {
        "registry.activation-mode",
        "registry.capability-id",
    }


def test_deprecated_registry_record_requires_a_valid_acyclic_successor() -> None:
    registry = _project_registry()
    registry["records"][0]["lifecycle"] = "deprecated"
    findings = contracts.validate_project_registry(registry)
    assert any(item.code == "registry.successor-required" for item in findings)

    successor = copy.deepcopy(registry["records"][0])
    successor["id"] = "next"
    successor["capability"] = "project-skill-next"
    successor["sourcePath"] = ".compound-gpid/skills/next"
    successor["provenanceId"] = "next"
    successor["lifecycle"] = "current"
    registry["records"].append(successor)
    registry["records"][0]["successorId"] = "next"
    assert not any(
        item.code.startswith("registry.successor")
        for item in contracts.validate_project_registry(registry)
    )


def test_provenance_tombstone_identity_and_latest_digest_must_match() -> None:
    provenance = _provenance()
    provenance["lifecycle"] = "removed"
    provenance["tombstone"] = {
        "skillId": "other",
        "removedRevision": "commit:abc",
        "recordDigest": "6" * 64,
    }
    findings = contracts.validate_instance(
        provenance,
        _contract("provenance-v1.schema.json"),
    )
    assert any(item.code == "provenance.tombstone-identity" for item in findings)


@pytest.mark.parametrize("path", ["../../escape", "/absolute", "C:/drive", "bad:name"])
def test_plan_actions_require_portable_repository_relative_paths(path: str) -> None:
    plan = _plan()
    plan["actions"][0]["path"] = path
    findings = contracts.validate_instance(plan, _contract("plan-v1.schema.json"))
    assert any(item.code == "contract.unsafe-path" for item in findings)


def test_anchored_identity_pattern_rejects_trailing_newline() -> None:
    request = _request()
    request["operation"] = "validate\n"
    findings = contracts.validate_instance(request, _contract("request-v1.schema.json"))
    assert any(item.code == "contract.pattern" for item in findings)


def test_error_order_is_json_pointer_then_finding_code() -> None:
    request = {"schema": "wrong", "arguments": [], "zzz": True}
    findings = contracts.validate_instance(request, _contract("request-v1.schema.json"))
    ordered = [(item.path, item.code) for item in findings]
    assert ordered == sorted(ordered)


def test_canonical_serialization_is_byte_stable_and_key_sorted() -> None:
    left = {"z": [3, 2, 1], "a": {"b": True}}
    right = {"a": {"b": True}, "z": [3, 2, 1]}
    assert contracts.canonical_json_bytes(left) == contracts.canonical_json_bytes(right)
    assert contracts.canonical_json_bytes(left) == b'{"a":{"b":true},"z":[3,2,1]}'


def test_state_vocabularies_align_across_code_schemas_and_skill_documentation() -> None:
    descriptor_schema = _contract("operation-descriptor-v1.schema.json")
    request_schema = _contract("request-v1.schema.json")
    result_schema = _contract("result-v1.schema.json")
    plan_schema = _contract("plan-v1.schema.json")
    registry_schema = _contract("project-registry-v1.schema.json")
    provenance_schema = _contract("provenance-v1.schema.json")
    record_properties = registry_schema["$defs"]["record"]["properties"]
    assert tuple(record_properties["lifecycle"]["enum"]) == contracts.LIFECYCLE_STATES
    assert tuple(record_properties["admission"]["enum"]) == contracts.ADMISSION_STATES
    assert tuple(provenance_schema["properties"]["origin"]["enum"]) == contracts.ORIGIN_STATES
    assert tuple(provenance_schema["properties"]["lifecycle"]["enum"]) == contracts.LIFECYCLE_STATES
    assert tuple(provenance_schema["properties"]["admission"]["enum"]) == contracts.ADMISSION_STATES
    assert tuple(descriptor_schema["properties"]["roles"]["items"]["enum"]) == contracts.CONTEXT_ROLES
    assert tuple(result_schema["properties"]["role"]["enum"]) == contracts.RESULT_ROLES
    assert tuple(descriptor_schema["properties"]["phases"]["items"]["enum"]) == contracts.PHASES
    assert tuple(request_schema["properties"]["phase"]["enum"]) == contracts.PHASES
    assert tuple(result_schema["properties"]["phase"]["enum"]) == contracts.PHASES
    assert tuple(result_schema["properties"]["manifestHealth"]["enum"]) == contracts.MANIFEST_HEALTH_STATES
    assert tuple(result_schema["$defs"]["finding"]["properties"]["severity"]["enum"]) == contracts.FINDING_SEVERITIES
    assert tuple(result_schema["$defs"]["action"]["properties"]["kind"]["enum"]) == contracts.ACTION_KINDS
    assert tuple(plan_schema["$defs"]["action"]["properties"]["kind"]["enum"]) == contracts.ACTION_KINDS

    documentation = (
        REPO_ROOT / ".github/skills/cg-skill-management/SKILL.md"
    ).read_text(encoding="utf-8")
    assert f"Lifecycle: {', '.join(contracts.LIFECYCLE_STATES)}" in documentation
    assert f"Admission: {', '.join(contracts.ADMISSION_STATES)}" in documentation
    assert f"Origin: {', '.join(contracts.ORIGIN_STATES)}" in documentation


def test_reserved_exit_codes_are_complete_and_stable() -> None:
    assert contracts.EXIT_CODES == {
        "success": 0,
        "internal": 1,
        "usage": 2,
        "contract": 3,
        "role-context": 4,
        "security": 5,
        "lifecycle-conflict": 6,
        "stale-plan": 7,
        "verification": 8,
    }


def test_project_registry_requires_canonical_record_and_selector_order() -> None:
    registry = _project_registry()
    second = copy.deepcopy(registry["records"][0])
    second["id"] = "alpha"
    second["capability"] = "project-skill-alpha"
    second["sourcePath"] = ".compound-gpid/skills/alpha"
    second["provenanceId"] = "alpha"
    registry["records"].append(second)
    registry["records"][0]["supportedPlatforms"] = ["kilo", "copilot"]
    findings = contracts.validate_project_registry(registry)
    assert any(item.code == "registry.order" for item in findings)


def test_malformed_registry_record_returns_findings_without_type_error() -> None:
    registry = _project_registry()
    registry["records"].append({})
    findings = contracts.validate_project_registry(registry)
    assert findings
    assert any(item.code == "contract.required" for item in findings)


def test_plan_rejects_mutable_source_revision_and_duplicate_or_protected_actions() -> None:
    plan = _plan()
    plan["bindings"]["sourceRevision"] = "main"
    plan["actions"].append(copy.deepcopy(plan["actions"][0]))
    plan["actions"].append(
        {
            "kind": "delete-file",
            "path": "roadmap.json",
            "description": "unsafe",
        }
    )
    findings = contracts.validate_instance(plan, _contract("plan-v1.schema.json"))
    assert {item.code for item in findings} >= {
        "contract.source-revision",
        "contract.path-collision",
        "contract.action-root",
    }


def test_removed_provenance_requires_terminal_removal_event() -> None:
    provenance = _provenance()
    provenance["lifecycle"] = "removed"
    provenance["tombstone"] = {
        "skillId": "example",
        "removedRevision": "4" * 40,
        "recordDigest": "6" * 64,
    }
    findings = contracts.validate_instance(
        provenance,
        _contract("provenance-v1.schema.json"),
    )
    assert any(item.code == "provenance.terminal-event" for item in findings)


def test_release_attestation_rejects_noncanonical_skill_keys() -> None:
    attestation = _attestation()
    attestation["deprecationRecordDigests"] = {"Example": "9" * 64}
    findings = contracts.validate_instance(
        attestation,
        _contract("release-attestation-v1.schema.json"),
    )
    assert any(item.code == "attestation.skill-id" for item in findings)
