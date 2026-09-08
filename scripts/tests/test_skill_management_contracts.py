"""Contract tests for the versioned skill-management schema subset."""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path, PurePosixPath
from typing import Tuple

import pytest

from skill_management import contracts
from skill_management.planning import OperationOutcome, result_envelope


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = REPO_ROOT / ".github/shared/skill-management/contracts"
PROTECTED_MIGRATION_PATHS = (
    ".git/config",
    ".github/workflows/tests.yml",
    ".github/shared/module-registry.json",
    ".compound-gpid/skill-plans/plan.json",
    ".compound-gpid/skill-transactions/journal.json",
    ".compound-gpid/skill-transaction.lock",
    "scripts/tool.py",
    "bin/tool",
    "src/tool.py",
    "compound-gpid.md",
    "compound-gpid.local.md",
    "kilo.json",
    "roadmap.json",
    "SCHEMA_VERSION",
    "releases/v1.0.0.md",
    ".cg-docs/plans/change.md",
)
PORTABLE_PROTECTED_MIGRATION_ALIASES = (
    ".GIT/config",
    ".GITHUB/WORKFLOWS/tests.yml",
    ".COMPOUND-GPID/SKILL-PLANS/plan.json",
    "SCRIPTS/tool.py",
    "\u017fcripts/tool.py",
    "COMPOUND-GPID.MD",
    "ROADMAP.JSON",
    "schema_version",
    "RELEASES/v1.0.0.md",
    ".CG-DOCS/PLANS/change.md",
    ".cg-doc\u017f/plans/change.md",
)
SUPPORTED_MIGRATION_PATHS = (
    "README.md",
    "docs/use.md",
    "DOCS/use.md",
    "doc\u017f/use.md",
    "references/use.txt",
    "src/reference.md",
    "source/notes.markdown",
)
COMMITTED_SCHEMA_PATTERNS = (
    r"^#(?:/.*)?$",
    r"^\.compound-gpid/skills/[a-z][a-z0-9-]*$",
    (
        r"^\.github/shared/skill-management/contracts/"
        r"[a-z][a-z0-9-]*-v[0-9]+\.schema\.json$"
    ),
    (
        r"^\.github/skills/cg-skill-management/workflows/"
        r"[a-z][a-z0-9-]*\.md$"
    ),
    r"^[0-9a-f]{40}$",
    r"^[0-9a-f]{64}$",
    r"^[a-z][a-z0-9-]*$",
    r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$",
    r"^docs/skills/management/commands/[a-z][a-z0-9-]*\.md$",
    (
        r"^https://github\.com/[A-Za-z0-9_.-]+/"
        r"[A-Za-z0-9_.-]+(?:\.git)?$"
    ),
    r"^project-skill-[a-z][a-z0-9-]*$",
    r"^scripts/tests/test_[a-z0-9_]+\.py$",
    (
        r"^skill_management\.operations\."
        r"[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$"
    ),
    (
        r"^v[0-9]+\.[0-9]+\.[0-9]+"
        r"(?:\.[0-9]+|-[A-Za-z0-9.-]+)?"
        r"(?:\+[A-Za-z0-9.-]+)?$"
    ),
)
UNSAFE_PATTERN_CASES = (
    (r"^([a-z]+)+$", "nested quantified groups are not supported"),
    (r"^(?:[a-z]+)+$", "nested quantified groups are not supported"),
    (r"^([a-z]|[a-z][a-z])+$", "repeated alternation groups are not supported"),
    (r"^(?:a|aa)+$", "repeated alternation groups are not supported"),
    (r"^(([a-z]+))+$", "nested quantified groups are not supported"),
    (r"^([a-z]{1,}){2}$", "nested quantified groups are not supported"),
    (r"^((?:a|aa)){2,3}$", "repeated alternation groups are not supported"),
    (
        "(" * (contracts.MAX_PATTERN_PARSE_DEPTH + 1)
        + "a"
        + ")" * (contracts.MAX_PATTERN_PARSE_DEPTH + 1),
        f"pattern exceeds {contracts.MAX_PATTERN_PARSE_DEPTH} nested groups",
    ),
    (
        "a" * (contracts.MAX_PATTERN_LENGTH + 1),
        f"pattern exceeds {contracts.MAX_PATTERN_LENGTH} characters",
    ),
    (
        f"a{{{contracts.MAX_PATTERN_REPEAT + 1}}}",
        f"repeat count exceeds {contracts.MAX_PATTERN_REPEAT}",
    ),
)
INVALID_UNICODE_KEY_CASES = (
    ("\ud800", False),
    ("\udfff", False),
    ("\ud800", True),
    ("\udfff", True),
)


def _contract(name: str) -> dict:
    return contracts.load_contract(
        REPO_ROOT,
        contracts.CONTRACTS_ROOT / name,
    )


def _write_contract_fixture(
    root: Path,
    relative: PurePosixPath = PurePosixPath("contracts/nested/valid.schema.json"),
    *,
    identifier: str = "captured-contract-v1",
) -> Tuple[Path, dict]:
    value = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": identifier,
        "type": "string",
    }
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path, value


def _schema_patterns(value: object) -> set[str]:
    patterns = set()
    if isinstance(value, dict):
        pattern = value.get("pattern")
        if isinstance(pattern, str):
            patterns.add(pattern)
        for child in value.values():
            patterns.update(_schema_patterns(child))
    elif isinstance(value, list):
        for child in value:
            patterns.update(_schema_patterns(child))
    return patterns


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
            contracts.load_contract(
                REPO_ROOT,
                contracts.CONTRACTS_ROOT / path.name,
            ),
            meta_contract,
        ) == (), path.name


def test_positive_pattern_fixtures_cover_every_committed_schema_pattern() -> None:
    committed = set()
    for path in sorted(CONTRACT_ROOT.glob("*.schema.json")):
        committed.update(_schema_patterns(_contract(path.name)))
    assert committed == set(COMMITTED_SCHEMA_PATTERNS)


@pytest.mark.parametrize("pattern", COMMITTED_SCHEMA_PATTERNS)
def test_each_committed_schema_pattern_is_in_the_safe_subset(pattern: str) -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "pattern-fixture-v1",
        "type": "string",
        "pattern": pattern,
    }
    assert contracts.validate_schema_definition(schema) == ()


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
        contracts.load_contract(tmp_path, PurePosixPath(path.name))


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
        contracts.load_contract(tmp_path, PurePosixPath(path.name))


def test_contract_loader_reads_valid_nested_contract_from_one_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    target, expected = _write_contract_fixture(root, relative)
    replacement = dict(expected, **{"$id": "replacement-v1"})
    original = contracts.secure_fs.secure_read_bytes
    calls = 0

    def capture_then_replace(read_root, read_relative, **kwargs):
        nonlocal calls
        calls += 1
        content = original(read_root, read_relative, **kwargs)
        target.write_text(json.dumps(replacement), encoding="utf-8")
        return content

    def reject_path_read(_path: Path) -> bytes:
        raise AssertionError("contract bytes were reopened by pathname")

    monkeypatch.setattr(
        contracts.secure_fs,
        "secure_read_bytes",
        capture_then_replace,
    )
    monkeypatch.setattr(Path, "read_bytes", reject_path_read)

    assert contracts.load_contract(root, relative) == expected
    assert calls == 1


@pytest.mark.usefixtures("require_symlink_support")
def test_contract_loader_rejects_leaf_link_swap_before_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    target, _ = _write_contract_fixture(root, relative)
    outside, _ = _write_contract_fixture(
        tmp_path / "outside",
        PurePosixPath("replacement.schema.json"),
        identifier="outside-v1",
    )
    original = contracts.secure_fs.secure_read_bytes

    def swap_then_read(read_root, read_relative, **kwargs):
        def swap(_path: Path) -> None:
            target.unlink()
            target.symlink_to(outside)

        return original(
            read_root,
            read_relative,
            before_open=swap,
            **kwargs,
        )

    monkeypatch.setattr(contracts.secure_fs, "secure_read_bytes", swap_then_read)

    with pytest.raises((OSError, ValueError), match="link|reparse|safe|regular"):
        contracts.load_contract(root, relative)


@pytest.mark.backend_posix
@pytest.mark.skipif(
    not contracts.secure_fs.supports_secure_dir_fd(),
    reason="requires POSIX pinned no-follow directory handles",
)
@pytest.mark.usefixtures("require_symlink_support")
def test_contract_loader_uses_pinned_parent_during_ancestor_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    target, expected = _write_contract_fixture(root, relative)
    original_parent = target.parent
    moved_parent = original_parent.with_name("nested-captured")
    outside_parent = tmp_path / "outside"
    outside, _ = _write_contract_fixture(
        outside_parent,
        PurePosixPath(target.name),
        identifier="outside-v1",
    )
    original = contracts.secure_fs.secure_read_bytes

    def swap_then_read(read_root, read_relative, **kwargs):
        def swap(_path: Path) -> None:
            original_parent.rename(moved_parent)
            original_parent.symlink_to(outside.parent, target_is_directory=True)

        return original(
            read_root,
            read_relative,
            before_open=swap,
            **kwargs,
        )

    monkeypatch.setattr(contracts.secure_fs, "secure_read_bytes", swap_then_read)

    assert contracts.load_contract(root, relative) == expected


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_contract_loader_blocks_ancestor_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    target, _ = _write_contract_fixture(root, relative)
    original_parent = target.parent
    moved_parent = original_parent.with_name("nested-captured")
    original = contracts.secure_fs.secure_read_bytes
    attempted = False

    def swap_then_read(read_root, read_relative, **kwargs):
        def swap(_path: Path) -> None:
            nonlocal attempted
            attempted = True
            original_parent.rename(moved_parent)
            original_parent.mkdir()
            (original_parent / target.name).write_text(
                '{"$id":"outside-v1"}',
                encoding="utf-8",
            )

        return original(
            read_root,
            read_relative,
            before_open=swap,
            **kwargs,
        )

    monkeypatch.setattr(contracts.secure_fs, "secure_read_bytes", swap_then_read)

    with pytest.raises(OSError):
        contracts.load_contract(root, relative)
    assert attempted is True


def test_contract_loader_rejects_hard_linked_contract(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    target, _ = _write_contract_fixture(root, relative)
    try:
        os.link(target, tmp_path / "contract-hard-link.json")
    except OSError as error:
        pytest.skip(f"host does not permit hard links: {error}")

    with pytest.raises((OSError, ValueError), match="multiple hard links"):
        contracts.load_contract(root, relative)


@pytest.mark.usefixtures("require_symlink_support")
def test_contract_loader_rejects_existing_symlink_or_reparse_point(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    outside, _ = _write_contract_fixture(
        tmp_path / "outside",
        PurePosixPath("outside.schema.json"),
    )
    target = root / relative
    target.parent.mkdir(parents=True)
    target.symlink_to(outside)

    with pytest.raises((OSError, ValueError), match="link|reparse|safe|regular"):
        contracts.load_contract(root, relative)


@pytest.mark.backend_windows
@pytest.mark.skipif(os.name != "nt", reason="requires Windows handle semantics")
def test_windows_contract_loader_rejects_reparse_file_handle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/valid.schema.json")
    _write_contract_fixture(root, relative)
    original = contracts.secure_fs._windows_require_safe_handle

    def reject_reparse(handle, path: Path, *, directory: bool) -> None:
        if directory:
            original(handle, path, directory=True)
            return
        contracts.secure_fs._windows_close_handle(handle)
        raise contracts.secure_fs.SecureMutationError(
            f"Pinned path is a reparse point: {path}."
        )

    monkeypatch.setattr(
        contracts.secure_fs,
        "_windows_require_safe_handle",
        reject_reparse,
    )

    with pytest.raises(OSError, match="reparse point"):
        contracts.load_contract(root, relative)


def test_contract_loader_rejects_oversized_file_before_decode(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/oversized.schema.json")
    target = root / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(b"x" * (contracts.MAX_CONTRACT_BYTES + 1))

    with pytest.raises((OSError, ValueError), match="exceeds.*read limit"):
        contracts.load_contract(root, relative)


def test_contract_loader_reports_invalid_utf8_with_relative_source(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    relative = PurePosixPath("contracts/nested/invalid.schema.json")
    target = root / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(b"\xff")

    with pytest.raises(ValueError) as error:
        contracts.load_contract(root, relative)
    assert str(error.value) == (
        "Contract is not valid UTF-8 JSON: contracts/nested/invalid.schema.json"
    )


@pytest.mark.parametrize(
    ("key", "nested"),
    INVALID_UNICODE_KEY_CASES,
    ids=("high-root", "low-root", "high-nested", "low-nested"),
)
def test_schema_surrogate_keys_fail_before_pointer_sort_or_serialization(
    key: str, nested: bool
) -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "unicode-key-v1",
        "type": "object",
    }
    expected_path = "/properties" if nested else ""
    if nested:
        schema["properties"] = {key: {"type": "string"}}
    else:
        schema[key] = None

    assert [
        finding.to_dict()
        for finding in contracts.validate_schema_definition(schema)
    ] == [
        {
            "code": "contract.json-key-unicode",
            "severity": "error",
            "path": expected_path,
            "message": "JSON object key contains an invalid Unicode surrogate.",
            "remediation": "Use valid Unicode scalar values in every object key.",
        }
    ]
    with pytest.raises(ValueError) as serialization_error:
        contracts.canonical_json_bytes(schema)
    assert "contract.json-key-unicode" in str(serialization_error.value)
    source = json.dumps(schema, ensure_ascii=True).encode("ascii")
    with pytest.raises(ValueError) as load_error:
        contracts.load_contract_bytes(source)
    assert str(load_error.value) == (
        "contract.json-key-unicode: "
        "JSON object key contains an invalid Unicode surrogate."
    )


@pytest.mark.parametrize(
    ("key", "nested"),
    INVALID_UNICODE_KEY_CASES,
    ids=("high-root", "low-root", "high-nested", "low-nested"),
)
def test_instance_surrogate_key_findings_use_only_valid_parent_pointers(
    key: str, nested: bool
) -> None:
    contract = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "open-object-v1",
        "type": "object",
        "additionalProperties": True,
    }
    instance = {"outer": {key: None}} if nested else {key: None}
    expected_path = "/outer" if nested else ""

    assert [
        finding.to_dict()
        for finding in contracts.validate_instance(instance, contract)
    ] == [
        {
            "code": "contract.json-key-unicode",
            "severity": "error",
            "path": expected_path,
            "message": "JSON object key contains an invalid Unicode surrogate.",
            "remediation": "Use valid Unicode scalar values in every object key.",
        }
    ]


def test_key_validation_precedes_duplicate_identity_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError) as unicode_error:
        contracts.load_contract_bytes(b'{"valid":0,"valid":1,"\\ud800":2}')
    assert str(unicode_error.value).startswith("contract.json-key-unicode:")

    monkeypatch.setattr(contracts, "MAX_VALUE_STRING_LENGTH", 4)
    with pytest.raises(ValueError) as budget_error:
        contracts.load_contract_bytes(b'{"okay":0,"okay":1,"abcde":2}')
    assert str(budget_error.value).startswith("contract.json-key-budget:")
    with pytest.raises(ValueError) as serialization_error:
        contracts.canonical_json_bytes({"abcde": None})
    assert str(serialization_error.value) == (
        "Value is not bounded scalar JSON: <root>: contract.json-key-budget"
    )


def test_non_ascii_scalar_keys_validate_build_pointers_and_serialize() -> None:
    outer_key = "caf\u00e9"
    inner_key = "\u6771\u4eac"
    value = {outer_key: {inner_key: "valid"}}
    open_contract = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "open-object-v1",
        "type": "object",
        "additionalProperties": True,
    }
    assert contracts.validate_instance(value, open_contract) == ()

    content = contracts.canonical_json_bytes(value)
    assert content == '{"caf\u00e9":{"\u6771\u4eac":"valid"}}'.encode("utf-8")
    assert contracts.load_contract_bytes(content) == value

    closed_contract = dict(open_contract, additionalProperties=False)
    findings = contracts.validate_instance({outer_key: True}, closed_contract)
    assert [(finding.path, finding.code) for finding in findings] == [
        ("/caf\u00e9", "contract.additional-property")
    ]


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


@pytest.mark.parametrize(
    ("pattern", "reason"),
    UNSAFE_PATTERN_CASES,
    ids=(
        "character-class-nested",
        "noncapturing-character-class-nested",
        "character-class-ambiguous-alternative",
        "noncapturing-ambiguous-alternative",
        "wrapped-nested-near-miss",
        "bounded-outer-near-miss",
        "wrapped-alternative-near-miss",
        "parse-depth-budget",
        "pattern-length-budget",
        "repeat-count-budget",
    ),
)
def test_exponential_regex_shapes_are_rejected_with_exact_finding(
    pattern: str, reason: str
) -> None:
    schema = {
        "$schema": contracts.SCHEMA_DIALECT,
        "$id": "unsafe-v1",
        "type": "string",
        "pattern": pattern,
    }
    assert [
        item.to_dict() for item in contracts.validate_schema_definition(schema)
    ] == [
        {
            "code": "schema.unsafe-pattern",
            "severity": "error",
            "path": "/pattern",
            "message": f"Pattern is outside the safe subset: {reason}.",
            "remediation": (
                "Use a bounded pattern without backreferences, lookarounds, or "
                "nested quantifiers."
            ),
        }
    ]


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


@pytest.mark.parametrize(
    "path", PROTECTED_MIGRATION_PATHS + PORTABLE_PROTECTED_MIGRATION_ALIASES
)
def test_migration_contracts_reject_protected_and_executable_paths(path: str) -> None:
    migration = _migration()
    migration["edits"][0]["path"] = path
    migration_findings = contracts.validate_instance(
        migration, _contract("migration-v1.schema.json")
    )
    plan = _plan()
    plan["actions"] = [
        {
            "kind": "apply-migration",
            "path": path,
            "description": "unsafe migration",
        }
    ]
    plan_findings = contracts.validate_instance(plan, _contract("plan-v1.schema.json"))

    assert any(item.code == "contract.action-root" for item in migration_findings)
    assert any(item.code == "contract.action-root" for item in plan_findings)


@pytest.mark.parametrize("path", SUPPORTED_MIGRATION_PATHS)
def test_migration_contracts_allow_documentation_and_reference_paths(path: str) -> None:
    migration = _migration()
    migration["edits"][0]["path"] = path
    plan = _plan()
    plan["actions"] = [
        {
            "kind": "apply-migration",
            "path": path,
            "description": "reviewed reference migration",
        }
    ]

    assert contracts.validate_instance(
        migration, _contract("migration-v1.schema.json")
    ) == ()
    assert contracts.validate_instance(plan, _contract("plan-v1.schema.json")) == ()


def test_migration_contracts_use_portable_unicode_path_identity() -> None:
    first = _migration()["edits"][0]
    second = copy.deepcopy(first)
    first["path"] = "docs/Caf\u00e9.md"
    second["path"] = "DOCS/Cafe\u0301.md"
    migration = _migration()
    migration["edits"] = [first, second]
    plan = _plan()
    plan["actions"] = [
        {
            "kind": "apply-migration",
            "path": str(edit["path"]),
            "description": "reviewed reference migration",
        }
        for edit in migration["edits"]
    ]

    migration_findings = contracts.validate_instance(
        migration, _contract("migration-v1.schema.json")
    )
    plan_findings = contracts.validate_instance(plan, _contract("plan-v1.schema.json"))

    assert any(item.code == "contract.path-collision" for item in migration_findings)
    assert any(item.code == "contract.path-collision" for item in plan_findings)


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
