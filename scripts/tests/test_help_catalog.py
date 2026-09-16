"""Phase 1 and 2 contracts for evidence-backed command help metadata."""
from __future__ import annotations

import copy
import importlib
import io
import json
import re
import shutil
import stat
import subprocess
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

import pytest

import cg_generate_targets as target_generator
from help import catalog, maintenance


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "help"
ALL_PLATFORMS = ["claude-code", "codex", "copilot", "kilo", "opencode"]
SEMANTIC_STATES = {
    "candidates",
    "error",
    "exact",
    "overview",
    "unsupported",
    "workflow",
}
TRANSPORT_OPERATIONS = {
    "query-completed",
    "request-prepared",
    "selection-prepared",
    "selection-rendered",
    "transport-error",
}


def _fixture(name: str) -> dict:
    return catalog.load_strict_json(FIXTURE_ROOT / name)


def _copy_catalog_source_graph(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    source = catalog.validate_source_metadata(REPO_ROOT)
    shutil.copytree(REPO_ROOT / ".github", root / ".github")
    (root / catalog.CATALOG_OUTPUT_PATH).unlink()
    paths = {
        catalog.CATALOG_SCHEMA_PATH,
        catalog.MODULE_REGISTRY_PATH,
        catalog.SHELL_METADATA_PATH,
        catalog.WORKFLOW_SOURCE_PATH,
    }
    paths.update(path.relative_to(REPO_ROOT).as_posix() for path in source.sidecar_paths)
    for command in source.slash_commands + source.shell_commands:
        paths.add(command["sourcePath"])
        paths.update(command["definitionSources"])
        paths.update(item["path"] for item in command["documentationTargets"])
        paths.update(item["sourcePath"] for item in command["availability"]["evidence"])
        paths.update(item["sourcePath"] for item in command["activation"])
    for workflow in source.workflows:
        paths.add(workflow["sourcePath"])
        for step in workflow["steps"]:
            paths.update(item["sourcePath"] for item in step["evidence"])
    registry = catalog.load_strict_json(REPO_ROOT / catalog.MODULE_REGISTRY_PATH)
    for module in registry["modules"]:
        activation = module.get("help", {}).get("activation")
        if activation:
            paths.add(activation["sourcePath"])
    for relative in sorted(paths):
        if relative.startswith(".github/"):
            continue
        source_path = REPO_ROOT / Path(*relative.split("/"))
        destination = root / Path(*relative.split("/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
    return root


@pytest.fixture
def committed_catalog_source_graph(tmp_path: Path) -> Path:
    """Validate a complete committed baseline, independent of worktree edits."""
    root = tmp_path / "repo"
    archive = subprocess.run(
        [
            "git", "archive", "--format=zip", "HEAD",
            ".github", "bin", "docs", "scripts", "install.ps1",
        ],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    with zipfile.ZipFile(io.BytesIO(archive.stdout)) as sources:
        for member in sources.infolist():
            assert (root / member.filename).resolve().is_relative_to(root.resolve())
            assert not stat.S_ISLNK(member.external_attr >> 16)
        sources.extractall(root)

    # These are strict checks, not stale-digest allowances or fixture repins.
    catalog.validate_source_metadata(root)
    # P3.23 derives generated summaries from the prompt descriptions; the
    # archived catalog predates that contract and the worktree catalog was
    # regenerated, so reproduce the baseline before the strict check.
    catalog.write_catalog(root)
    catalog.check_catalog(root)
    return root


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _maintenance_artifact_bytes(root: Path) -> dict[str, bytes]:
    """Snapshot every pin and catalog output for maintenance no-write checks."""
    paths = set((root / ".github/prompts").glob("*.help.json"))
    paths.update(root / path for path in (
        catalog.SHELL_METADATA_PATH, catalog.CATALOG_OUTPUT_PATH,
    ))
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in paths}


def _reference_json_equal(first: Any, second: Any) -> bool:
    """Compare JSON values independently from Python's bool/number equality."""
    if isinstance(first, bool) or isinstance(second, bool):
        return type(first) is type(second) and first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return first == second
    if type(first) is not type(second):
        return False
    if isinstance(first, list):
        return len(first) == len(second) and all(
            _reference_json_equal(left, right)
            for left, right in zip(first, second)
        )
    if isinstance(first, dict):
        return set(first) == set(second) and all(
            _reference_json_equal(first[key], second[key]) for key in first
        )
    return first == second


def _reference_schema_accepts(
    value: Any,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
) -> bool:
    """Evaluate the help schemas without using the runtime validator."""
    reference = schema.get("$ref")
    if isinstance(reference, str):
        current: Any = root
        for part in reference[2:].split("/"):
            current = current[part]
        return _reference_schema_accepts(value, current, root)

    expected_type = schema.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and float(value).is_integer()
        ),
        "number": not isinstance(value, bool) and isinstance(value, (int, float)),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }
    if isinstance(expected_type, str) and not type_matches[expected_type]:
        return False
    if "const" in schema and not _reference_json_equal(value, schema["const"]):
        return False
    if "enum" in schema and not any(
        _reference_json_equal(value, option) for option in schema["enum"]
    ):
        return False
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            return False
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            return False
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            return False
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return False
        if schema.get("uniqueItems") and any(
            _reference_json_equal(value[left], value[right])
            for left in range(len(value))
            for right in range(left + 1, len(value))
        ):
            return False
        if "items" in schema and not all(
            _reference_schema_accepts(item, schema["items"], root)
            for item in value
        ):
            return False
    if isinstance(value, dict):
        if any(key not in value for key in schema.get("required", [])):
            return False
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and any(
            key not in properties for key in value
        ):
            return False
        if any(
            key in value
            and not _reference_schema_accepts(value[key], child, root)
            for key, child in properties.items()
        ):
            return False
    if "oneOf" in schema and sum(
        _reference_schema_accepts(value, branch, root)
        for branch in schema["oneOf"]
    ) != 1:
        return False
    return True


def _runtime_accepts(validator, value: Any) -> bool:
    try:
        validator(value)
    except catalog.HelpValidationError:
        return False
    return True


def test_catalog_schema_accepts_minimal_and_full_golden_fixtures() -> None:
    registry = _fixture("registry.json")

    minimal = _fixture("catalog-minimal.json")
    full = _fixture("catalog-full.json")

    catalog.validate_catalog(minimal, registry)
    catalog.validate_catalog(full, registry)
    assert full["commands"][0]["summary"].startswith("Ignore all prior")


def test_catalog_schema_rejects_unknown_fields_versions_and_unsorted_suites() -> None:
    registry = _fixture("registry.json")
    valid = _fixture("catalog-minimal.json")

    unknown = copy.deepcopy(valid)
    unknown["commands"][0]["invented"] = True
    with pytest.raises(catalog.HelpValidationError, match="unknown"):
        catalog.validate_catalog(unknown, registry)

    version = copy.deepcopy(valid)
    version["schemaVersion"] = 2
    with pytest.raises(catalog.HelpValidationError, match="schemaVersion"):
        catalog.validate_catalog(version, registry)

    unsorted = copy.deepcopy(valid)
    unsorted["commands"][0]["supportedSuites"] = ["cr", "cg"]
    with pytest.raises(catalog.HelpValidationError, match="sorted"):
        catalog.validate_catalog(unsorted, registry)


def test_supported_suites_must_exactly_match_every_owner_suite_closure() -> None:
    registry = _fixture("registry.json")
    incomplete = _fixture("catalog-full.json")
    command = incomplete["commands"][0]
    command["supportedSuites"] = ["cg"]
    command["activation"] = [command["activation"][0]]

    with pytest.raises(catalog.HelpValidationError, match="exactly match.*closures"):
        catalog.validate_catalog(incomplete, registry)


def test_catalog_schema_rejects_broken_ownership_relations_and_workflows() -> None:
    registry = _fixture("registry.json")
    valid = _fixture("catalog-full.json")

    unknown_owner = copy.deepcopy(valid)
    unknown_owner["commands"][0]["ownerModule"] = "cap-invented"
    with pytest.raises(catalog.HelpValidationError, match="ownerModule"):
        catalog.validate_catalog(unknown_owner, registry)

    relation = copy.deepcopy(valid)
    relation["commands"][0]["relatedCommands"] = [
        {"id": "slash:not-real", "relation": "next"}
    ]
    with pytest.raises(catalog.HelpValidationError, match="related"):
        catalog.validate_catalog(relation, registry)

    workflow = copy.deepcopy(valid)
    workflow["workflows"][0]["steps"][0]["commandId"] = "shell:not-real"
    with pytest.raises(catalog.HelpValidationError, match="workflow"):
        catalog.validate_catalog(workflow, registry)


def test_catalog_schema_allows_same_visible_name_across_kinds_but_not_alias_kind() -> None:
    registry = _fixture("registry.json")
    valid = _fixture("catalog-full.json")
    catalog.validate_catalog(valid, registry)

    duplicate = copy.deepcopy(valid)
    duplicate["commands"][1]["aliases"] = ["/cg-skill"]
    with pytest.raises(catalog.HelpValidationError, match="alias"):
        catalog.validate_catalog(duplicate, registry)


def test_alias_collisions_use_shared_nfkc_trim_slash_and_case_normalization() -> None:
    registry = _fixture("registry.json")
    collision_pairs = [
        ["/skill-chat", "/ｓｋｉｌｌ-chat"],
        [" skill-chat", "skill-chat"],
    ]

    assert catalog.normalize_command_key("  ／ＣＧ-SKILL  ") == "cg-skill"
    for aliases in collision_pairs:
        duplicate = _fixture("catalog-full.json")
        duplicate["commands"][1]["aliases"] = aliases
        with pytest.raises(catalog.HelpValidationError, match="alias"):
            catalog.validate_catalog(duplicate, registry)


def test_acceptance_metadata_fixture_covers_phase_one_structural_cases() -> None:
    cases = _fixture("acceptance-cases.json")
    examples = _fixture("acceptance-examples.json")

    assert set(cases) == {
        "brokenRelation",
        "brokenWorkflow",
        "duplicateAlias",
        "inactiveSuite",
        "instructionLikeData",
        "staleDigest",
        "unsupportedDirectAgent",
        "windowsPosixAvailability",
    }
    assert all(
        value.startswith("Ignore all prior")
        for value in cases["instructionLikeData"].values()
    )
    assert {item["case"] for item in examples} == {
        "ambiguous",
        "exact-shell",
        "exact-slash",
        "inactive-suite",
        "natural-language",
        "no-argument",
        "typo",
        "unsupported",
        "workflow",
    }
    assert all(item["expectedState"] in SEMANTIC_STATES for item in examples)


def test_transport_envelope_schema_accepts_every_operation_and_semantic_state() -> None:
    operations = set()
    states = set()
    for path in sorted(FIXTURE_ROOT.glob("transport-*.json")):
        envelope = catalog.parse_transport_envelope(
            path.read_bytes(), source=path.as_posix()
        )
        operations.add(envelope["operation"])
        result = envelope.get("result")
        if isinstance(result, dict):
            states.add(result["state"])

    assert operations == TRANSPORT_OPERATIONS
    assert states == SEMANTIC_STATES
    candidates = _fixture("transport-query-candidates.json")
    assert candidates["result"]["data"]["followUpQueries"] == [
        "/cg-help shell:cg-skill",
        "/cg-help /cg-skill",
        "/cg-help /cg-work",
    ]


def test_runtime_validator_matches_independent_json_schema_corpus() -> None:
    catalog_schema = catalog.load_strict_json(
        REPO_ROOT / catalog.CATALOG_SCHEMA_PATH
    )
    transport_schema = catalog.load_strict_json(
        REPO_ROOT / catalog.TRANSPORT_SCHEMA_PATH
    )
    valid_catalog = _fixture("catalog-full.json")
    float_order = copy.deepcopy(valid_catalog)
    float_order["workflows"][0]["steps"][0]["order"] = 1.0
    fractional_order = copy.deepcopy(valid_catalog)
    fractional_order["workflows"][0]["steps"][0]["order"] = 1.5
    boolean_version = copy.deepcopy(valid_catalog)
    boolean_version["schemaVersion"] = True
    valid_transport = _fixture("transport-request-prepared.json")
    float_constant = copy.deepcopy(valid_transport)
    float_constant["maxBytes"] = 4096.0
    boolean_constant = copy.deepcopy(valid_transport)
    boolean_constant["maxBytes"] = True

    cases = [
        ("catalog-valid", valid_catalog, catalog_schema, True, lambda value: catalog.validate_catalog(value, _fixture("registry.json"))),
        ("catalog-integral-float", float_order, catalog_schema, True, lambda value: catalog.validate_catalog(value, _fixture("registry.json"))),
        ("catalog-fractional-order", fractional_order, catalog_schema, False, lambda value: catalog.validate_catalog(value, _fixture("registry.json"))),
        ("catalog-boolean-version", boolean_version, catalog_schema, False, lambda value: catalog.validate_catalog(value, _fixture("registry.json"))),
        ("transport-valid", valid_transport, transport_schema, True, catalog.validate_transport_envelope),
        ("transport-integral-float-constant", float_constant, transport_schema, True, catalog.validate_transport_envelope),
        ("transport-boolean-constant", boolean_constant, transport_schema, False, catalog.validate_transport_envelope),
    ]
    for label, value, schema, expected, validator in cases:
        reference_accepts = _reference_schema_accepts(value, schema, schema)
        runtime_accepts = _runtime_accepts(validator, value)
        assert reference_accepts is expected, label
        assert runtime_accepts is reference_accepts, label


def test_transport_envelope_rejects_uuid_path_mismatch_and_too_many_candidates() -> None:
    prepared = _fixture("transport-request-prepared.json")
    prepared["queryPath"] = ".compound-gpid/runtime/help-requests/other.query.txt"
    with pytest.raises(catalog.HelpValidationError, match="queryPath"):
        catalog.validate_transport_envelope(prepared)

    candidates = _fixture("transport-query-candidates.json")
    candidates["result"]["data"]["commandIds"].append("slash:cg-review")
    with pytest.raises(catalog.HelpValidationError, match="3"):
        catalog.validate_transport_envelope(candidates)


def test_transport_envelope_rejects_unknown_fields_and_duplicate_json_keys() -> None:
    prepared = _fixture("transport-request-prepared.json")
    prepared["query"] = "untrusted raw text"
    with pytest.raises(catalog.HelpValidationError, match="unknown"):
        catalog.validate_transport_envelope(prepared)

    with pytest.raises(catalog.HelpValidationError, match="duplicate"):
        catalog.load_strict_json_bytes(
            b'{"schemaVersion":1,"schemaVersion":1}', source="duplicate.json"
        )


def test_surrogate_source_is_exit_two_with_diagnostic_and_no_mutation(
    tmp_path: Path,
) -> None:
    with pytest.raises(catalog.HelpValidationError, match="surrogate.json.*surrogate"):
        catalog.load_strict_json_bytes(
            b'{"nested":["\\ud800"]}', source="surrogate.json"
        )

    root = _copy_catalog_source_graph(tmp_path)
    generator = importlib.import_module("cg_generate_help_catalog")
    output = root / catalog.CATALOG_OUTPUT_PATH
    output.write_bytes(b"existing catalog\n")
    before = output.read_bytes()
    sidecar = root / ".github/prompts/cg-work.help.json"
    sidecar.write_bytes(b'{"summary":"\\ud800"}\n')
    stdout = io.BytesIO()
    stderr = io.BytesIO()

    assert generator.main(
        ["--root", str(root), "--write"], stdout, stderr
    ) == generator.EXIT_SOURCE_INVALID
    assert stdout.getvalue() == b""
    assert b"cg-work.help.json" in stderr.getvalue()
    assert b"surrogate" in stderr.getvalue()
    assert output.read_bytes() == before


@pytest.mark.parametrize(
    "request_id",
    ["../123e4567-e89b-12d3-a456-426614174000", "ABC", "123e4567/e89b"],
)
def test_transport_envelope_rejects_unsafe_uuid_separators(request_id: str) -> None:
    prepared = _fixture("transport-request-prepared.json")
    prepared["requestId"] = request_id

    with pytest.raises(catalog.HelpValidationError):
        catalog.validate_transport_envelope(prepared)


def test_canonical_help_metadata_inventory_is_complete_and_strict() -> None:
    source = catalog.validate_source_metadata(REPO_ROOT)
    prompt_names = {
        path.name[: -len(".prompt.md")]
        for path in (REPO_ROOT / ".github/prompts").glob("*.prompt.md")
        if path.name.startswith(("cg-", "cr-"))
    }
    sidecar_names = {
        path.name[: -len(".help.json")] for path in source.sidecar_paths
    }

    assert sidecar_names == prompt_names
    assert all(command["kind"] == "slash" for command in source.slash_commands)
    assert {command["id"] for command in source.shell_commands} >= {
        "shell:cg-brain-init",
        "shell:cg-kilo",
        "shell:cg-skill",
    }
    assert source.workflows


def test_canonical_help_metadata_includes_help_prompt_and_sidecar() -> None:
    source = catalog.validate_source_metadata(REPO_ROOT)
    prompt = REPO_ROOT / ".github/prompts/cg-help.prompt.md"
    sidecar = REPO_ROOT / ".github/prompts/cg-help.help.json"
    assert prompt.is_file() and sidecar.is_file()
    assert sidecar in source.sidecar_paths
    assert {command["id"] for command in source.slash_commands} >= {"slash:cg-help"}


def test_shell_metadata_inventory_has_per_os_implementation_evidence() -> None:
    source = catalog.validate_source_metadata(REPO_ROOT)
    by_name = {command["name"]: command for command in source.shell_commands}
    posix_wrappers = {
        path.name for path in (REPO_ROOT / "bin").glob("cg-*") if path.suffix != ".cmd"
    }
    windows_wrappers = {
        path.stem for path in (REPO_ROOT / "bin").glob("cg-*.cmd")
    }

    assert set(by_name) == posix_wrappers
    assert windows_wrappers == {
        name for name, command in by_name.items() if "windows" in command["supportedOS"]
    }
    for command in source.shell_commands:
        evidence_os = {item["os"] for item in command["availability"]["evidence"]}
        assert evidence_os == set(command["supportedOS"])


def test_help_sidecars_are_absent_from_every_target_plan_and_ownership_record() -> None:
    assets = target_generator.scan_canonical_assets(REPO_ROOT)
    sidecar_sources = {item["relative_path"] for item in assets["help_sidecars"]}
    prompt_sources = {item["relative_path"] for item in assets["prompts"]}
    mapping = target_generator.load_target_mapping(REPO_ROOT)
    plan = target_generator.build_generation_plan(REPO_ROOT, mapping, assets)

    assert sidecar_sources
    assert not sidecar_sources & prompt_sources
    assert all(not item["filename"].endswith(".help.json") for item in assets["prompts"])
    assert set(plan.by_target) == set(ALL_PLATFORMS)
    for result in plan.by_target.values():
        assert all(
            not entry.source.endswith(".help.json")
            and not entry.destination.endswith(".help.json")
            for entry in result.entries
        )
        ownership = json.loads(
            target_generator._ownership_manifest_bytes(result).decode("utf-8")
        )
        assert all(
            not record["source"].endswith(".help.json")
            and not record["path"].endswith(".help.json")
            for record in ownership["files"]
        )


def test_workflow_metadata_has_explicit_kind_qualified_steps_and_evidence() -> None:
    source = catalog.validate_source_metadata(REPO_ROOT)
    command_ids = {
        command["id"] for command in source.slash_commands + source.shell_commands
    }

    for workflow in source.workflows:
        assert workflow["sourcePath"] == "docs/workflow.md"
        for index, step in enumerate(workflow["steps"], start=1):
            assert step["order"] == index
            assert step["commandId"] in command_ids
            assert step["evidence"]


def test_catalog_generation_is_byte_deterministic_and_normalizes_record_order(
    tmp_path: Path,
) -> None:
    root = _copy_catalog_source_graph(tmp_path)

    first = catalog.generate_catalog_bytes(root)
    second = catalog.generate_catalog_bytes(root)
    value = catalog.load_strict_json_bytes(first, source="generated catalog")
    source = catalog.validate_source_metadata(root)
    shuffled = replace(
        source,
        slash_commands=tuple(reversed(source.slash_commands)),
        shell_commands=tuple(reversed(source.shell_commands)),
        workflows=tuple(reversed(source.workflows)),
    )
    registry = catalog.load_strict_json(root / catalog.MODULE_REGISTRY_PATH)

    assert first == second
    assert first.endswith(b"\n")
    assert catalog.merge_catalog(registry, shuffled) == value
    assert [item["id"] for item in value["commands"]] == sorted(
        item["id"] for item in value["commands"]
    )
    assert [item["id"] for item in value["workflows"]] == sorted(
        item["id"] for item in value["workflows"]
    )


def test_catalog_bytes_do_not_depend_on_absolute_root_or_unrelated_docs(
    tmp_path: Path,
) -> None:
    first_root = _copy_catalog_source_graph(tmp_path / "first")
    second_root = _copy_catalog_source_graph(tmp_path / "second")
    baseline = catalog.generate_catalog_bytes(first_root)

    workflow_path = first_root / catalog.WORKFLOW_SOURCE_PATH
    workflow_path.write_bytes(
        workflow_path.read_bytes() + b"\nUnrelated workflow prose.\n"
    )
    view_path = first_root / ".cg-docs/views/unrelated.html"
    view_path.parent.mkdir(parents=True)
    view_path.write_text("not catalog evidence", encoding="utf-8")

    assert catalog.generate_catalog_bytes(first_root) == baseline
    assert catalog.generate_catalog_bytes(second_root) == baseline


def test_definition_sources_require_canonical_portable_paths(tmp_path: Path) -> None:
    source = tmp_path / "definition.txt"
    source.write_bytes(b"definition\n")

    assert catalog.compute_definition_digest(tmp_path, ["definition.txt"]) == (
        "c2c54173550dea558c2bcb6182558ec44c71a649c2a672e7fedcef63e26d9a3c"
    )
    for unsafe in ("../definition.txt", "./definition.txt", "a//b", "a\\b", "C:/a"):
        with pytest.raises(catalog.HelpValidationError, match="relative|escape"):
            catalog.compute_definition_digest(tmp_path, [unsafe])


def test_accepted_metadata_change_updates_source_digest(tmp_path: Path) -> None:
    root = _copy_catalog_source_graph(tmp_path)
    before = catalog.load_strict_json_bytes(
        catalog.generate_catalog_bytes(root), source="before"
    )
    sidecar_path = root / ".github/prompts/cg-work.help.json"
    sidecar = catalog.load_strict_json(sidecar_path)
    sidecar["summary"] = sidecar["summary"] + " Reviewed."
    _write_json(sidecar_path, sidecar)

    after = catalog.load_strict_json_bytes(
        catalog.generate_catalog_bytes(root), source="after"
    )

    assert after["sourceDigest"] != before["sourceDigest"]
    from brain.utils import parse_frontmatter

    prompt = (root / ".github/prompts/cg-work.prompt.md").read_text(encoding="utf-8")
    expected = parse_frontmatter(prompt, source="cg-work.prompt.md").get("description")
    assert next(
        item for item in after["commands"] if item["id"] == "slash:cg-work"
    )["summary"] == expected


def test_generated_summary_is_derived_from_prompt_description(tmp_path: Path) -> None:
    """The sidecar summary field is not the source of truth; generation derives it."""
    from brain.utils import parse_frontmatter

    root = _copy_catalog_source_graph(tmp_path)
    sidecar_path = root / ".github/prompts/cg-work.help.json"
    sidecar = catalog.load_strict_json(sidecar_path)
    sidecar["summary"] = "Invented divergent summary."
    _write_json(sidecar_path, sidecar)

    after = catalog.load_strict_json_bytes(
        catalog.generate_catalog_bytes(root), source="after"
    )
    prompt = (root / ".github/prompts/cg-work.prompt.md").read_text(encoding="utf-8")
    expected = parse_frontmatter(prompt, source="cg-work.prompt.md").get("description")

    assert next(
        item for item in after["commands"] if item["id"] == "slash:cg-work"
    )["summary"] == expected


def test_missing_prompt_description_fails_generation_closed(tmp_path: Path) -> None:
    root = _copy_catalog_source_graph(tmp_path)
    prompt_path = root / ".github/prompts/cg-work.prompt.md"
    content = prompt_path.read_bytes()
    key = b'description: "'
    assert content.count(key) >= 1
    prompt_path.write_bytes(content.replace(key, b"renamed: \"", 1))

    with pytest.raises(catalog.HelpValidationError, match="description is missing"):
        catalog.generate_catalog_bytes(root)


def test_changed_definition_fails_until_explicit_one_record_repin(
    committed_catalog_source_graph: Path,
) -> None:
    root = committed_catalog_source_graph
    sidecar_path = root / ".github/prompts/cg-work.help.json"
    other_sidecar = root / ".github/prompts/cg-review.help.json"
    shell_metadata = root / catalog.SHELL_METADATA_PATH
    prompt_path = root / ".github/prompts/cg-work.prompt.md"
    before = catalog.load_strict_json(sidecar_path)
    other_before = other_sidecar.read_bytes()
    shell_before = shell_metadata.read_bytes()
    prompt_path.write_bytes(prompt_path.read_bytes() + b"\nReviewed definition change.\n")

    with pytest.raises(catalog.HelpValidationError, match="definitionDigest is stale"):
        catalog.generate_catalog_bytes(root)
    preview = catalog.preview_definition_digest(root, "slash:cg-work")

    assert preview["stale"] is True
    assert preview["currentDefinitionDigest"] == before["definitionDigest"]
    assert preview["computedDefinitionDigest"] != before["definitionDigest"]

    result = catalog.repin_definition_digest(root, "slash:cg-work")
    after = catalog.load_strict_json(sidecar_path)

    assert result["changed"] is True
    assert after["definitionDigest"] == preview["computedDefinitionDigest"]
    assert {key: value for key, value in after.items() if key != "definitionDigest"} == {
        key: value for key, value in before.items() if key != "definitionDigest"
    }
    assert other_sidecar.read_bytes() == other_before
    assert shell_metadata.read_bytes() == shell_before
    catalog.generate_catalog_bytes(root)


def test_repin_forced_final_validation_failure_preserves_metadata_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_catalog_source_graph(tmp_path)
    metadata_path = root / ".github/prompts/cg-work.help.json"
    prompt_path = root / ".github/prompts/cg-work.prompt.md"
    original_metadata = metadata_path.read_bytes()
    prompt_path.write_bytes(prompt_path.read_bytes() + b"\nReviewed definition change.\n")
    original_validate = catalog.validate_source_metadata
    calls = 0

    def fail_final_validation(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise catalog.HelpValidationError("forced final source validation failure")
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(maintenance, "validate_source_metadata", fail_final_validation)

    with pytest.raises(catalog.HelpValidationError, match="forced final"):
        catalog.repin_definition_digest(root, "slash:cg-work")

    assert calls == 2
    assert metadata_path.read_bytes() == original_metadata


def test_changed_shell_definition_is_detected_without_bulk_repin(
    committed_catalog_source_graph: Path,
) -> None:
    root = committed_catalog_source_graph
    definition = root / "scripts/cg_index.py"
    definition.write_bytes(definition.read_bytes() + b"\n# changed parser\n")

    with pytest.raises(catalog.HelpValidationError, match="shell:cg-index.*stale"):
        catalog.generate_catalog_bytes(root)

    generator = importlib.import_module("cg_generate_help_catalog")
    with pytest.raises(SystemExit):
        generator.parse_args(["--repin-all"])


@pytest.mark.parametrize("operation", ["preview", "repin"])
def test_multi_stale_shell_definitions_allow_one_record_maintenance(
    committed_catalog_source_graph: Path, operation: str,
) -> None:
    """One reviewed record can be maintained while every other pin stays fixed."""
    root = committed_catalog_source_graph
    source = catalog.validate_source_metadata(root)
    sidecars_before = {path: path.read_bytes() for path in source.sidecar_paths}
    metadata_path = root / catalog.SHELL_METADATA_PATH
    metadata_bytes_before = metadata_path.read_bytes()
    metadata_before = catalog.load_strict_json(metadata_path)
    catalog_path = root / catalog.CATALOG_OUTPUT_PATH
    catalog_before = catalog_path.read_bytes()
    selected_id = "shell:cg-brain-init"
    other_id = "shell:cg-diff-summary"
    for name in ("cg-brain-init", "cg-diff-summary"):
        definition = root / "bin" / name
        definition.write_bytes(
            definition.read_bytes() + b"\n# Reviewed fixture definition change.\n"
        )
    computed = {
        command["id"]: catalog.compute_definition_digest(
            root, command["definitionSources"]
        )
        for command in source.slash_commands + source.shell_commands
    }
    assert {
        command["id"]
        for command in source.slash_commands + source.shell_commands
        if command["definitionDigest"] != computed[command["id"]]
    } == {selected_id, other_id}

    generator = importlib.import_module("cg_generate_help_catalog")
    arguments = ["--root", str(root)]
    for mode in ("--write", "--check"):
        stderr = io.BytesIO()
        assert generator.main(
            arguments + [mode], io.BytesIO(), stderr
        ) == generator.EXIT_SOURCE_INVALID
        assert b"definitionDigest is stale" in stderr.getvalue()
    assert metadata_path.read_bytes() == metadata_bytes_before
    assert catalog_path.read_bytes() == catalog_before

    maintenance = [f"--{operation}-definition-digest", selected_id]
    if operation == "repin":
        maintenance.append("--reviewed")
    stdout, stderr = io.BytesIO(), io.BytesIO()
    exit_code = generator.main(arguments + maintenance, stdout, stderr)
    assert exit_code == generator.EXIT_SUCCESS, stderr.getvalue().decode("utf-8")
    result = catalog.load_strict_json_bytes(stdout.getvalue(), source="maintenance")
    assert result["computedDefinitionDigest"] == computed[selected_id]
    expected_metadata = copy.deepcopy(metadata_before)
    selected = next(
        command for command in expected_metadata["commands"]
        if command["id"] == selected_id
    )
    if operation == "repin":
        assert result["previousDefinitionDigest"] == selected["definitionDigest"]
        assert result["currentDefinitionDigest"] == computed[selected_id]
        assert result["changed"] is True
        selected["definitionDigest"] = computed[selected_id]
    else:
        assert result["currentDefinitionDigest"] == selected["definitionDigest"]
        assert result["stale"] is True
        assert metadata_path.read_bytes() == metadata_bytes_before
    assert catalog.load_strict_json(metadata_path) == expected_metadata
    assert all(path.read_bytes() == content for path, content in sidecars_before.items())
    assert catalog_path.read_bytes() == catalog_before

    for mode in ("--write", "--check"):
        stderr = io.BytesIO()
        assert generator.main(
            arguments + [mode], io.BytesIO(), stderr
        ) == generator.EXIT_SOURCE_INVALID
        stale_id = other_id if operation == "repin" else selected_id
        assert stale_id.encode("utf-8") in stderr.getvalue()
        assert b"definitionDigest is stale" in stderr.getvalue()
    assert catalog.load_strict_json(metadata_path) == expected_metadata
    assert catalog_path.read_bytes() == catalog_before


@pytest.mark.parametrize("operation", ["preview", "repin"])
@pytest.mark.parametrize(
    "selected_id, changed_paths, stale_ids",
    [
        (
            "slash:cg-work",
            (".github/prompts/cg-work.prompt.md", ".github/prompts/cg-review.prompt.md"),
            {"slash:cg-work", "slash:cg-review"},
        ),
        (
            "slash:cg-work",
            (".github/prompts/cg-work.prompt.md", "bin/cg-brain-init"),
            {"slash:cg-work", "shell:cg-brain-init"},
        ),
        (
            "shell:cg-brain-init",
            (".github/prompts/cg-work.prompt.md", "bin/cg-brain-init"),
            {"slash:cg-work", "shell:cg-brain-init"},
        ),
        ("shell:cg-brain-init", ("scripts/install.sh",), None),
    ],
    ids=["slash", "mixed-slash", "mixed-shell", "shared-installer"],
)
def test_named_maintenance_preserves_other_pins_and_source_bytes(
    committed_catalog_source_graph: Path,
    operation: str,
    selected_id: str,
    changed_paths: tuple[str, ...],
    stale_ids: set[str] | None,
) -> None:
    """User requirement: maintain one named pin, including shared-source changes."""
    root = committed_catalog_source_graph
    source = catalog.validate_source_metadata(root)
    records = source.slash_commands + source.shell_commands
    selected = next(command for command in records if command["id"] == selected_id)
    if stale_ids is None:
        stale_ids = {command["id"] for command in source.shell_commands}
    for relative in changed_paths:
        path = root / relative
        path.write_bytes(path.read_bytes() + b"\n# Reviewed fixture change.\n")
    computed = {
        command["id"]: catalog.compute_definition_digest(
            root, command["definitionSources"]
        )
        for command in records
    }
    assert {
        command["id"] for command in records
        if computed[command["id"]] != command["definitionDigest"]
    } == stale_ids
    source_bytes = {
        relative: (root / relative).read_bytes()
        for relative in {
            path for command in records for path in command["definitionSources"]
        }
    }
    before = _maintenance_artifact_bytes(root)
    metadata_path = (
        selected["sourcePath"].replace(".prompt.md", ".help.json")
        if selected["kind"] == "slash" else catalog.SHELL_METADATA_PATH
    )
    generator = importlib.import_module("cg_generate_help_catalog")
    arguments = [
        "--root", str(root), f"--{operation}-definition-digest", selected_id,
    ]
    if operation == "repin":
        arguments.append("--reviewed")
    stdout, stderr = io.BytesIO(), io.BytesIO()

    assert generator.main(arguments, stdout, stderr) == 0, stderr.getvalue()
    result = catalog.load_strict_json_bytes(stdout.getvalue(), source="maintenance")
    assert result["id"] == selected_id
    assert result["metadataPath"] == metadata_path
    assert result["computedDefinitionDigest"] == computed[selected_id]
    expected = dict(before)
    if operation == "repin":
        assert result["previousDefinitionDigest"] == selected["definitionDigest"]
        assert result["currentDefinitionDigest"] == computed[selected_id]
        assert result["changed"] is True
        assert result["stale"] is False
        old_digest = selected["definitionDigest"].encode("ascii")
        assert before[metadata_path].count(old_digest) == 1
        expected[metadata_path] = before[metadata_path].replace(
            old_digest, computed[selected_id].encode("ascii"), 1
        )
        # A now-current selection must remain a no-op despite other stale pins.
        stdout, stderr = io.BytesIO(), io.BytesIO()
        assert generator.main(arguments, stdout, stderr) == 0, stderr.getvalue()
        repeated = catalog.load_strict_json_bytes(stdout.getvalue(), source="repeat")
        assert repeated["changed"] is False
        assert repeated["stale"] is False
        assert repeated["currentDefinitionDigest"] == computed[selected_id]
    else:
        assert result["currentDefinitionDigest"] == selected["definitionDigest"]
        assert result["stale"] is True
    assert _maintenance_artifact_bytes(root) == expected
    assert all(
        (root / path).read_bytes() == content
        for path, content in source_bytes.items()
    )
    for mode in ("--write", "--check", "--stdout"):
        stdout, stderr = io.BytesIO(), io.BytesIO()
        assert generator.main(["--root", str(root), mode], stdout, stderr) == 2
        assert b"definitionDigest is stale" in stderr.getvalue()
        assert stdout.getvalue() == b""
    assert _maintenance_artifact_bytes(root) == expected


@pytest.mark.parametrize("operation", ["preview", "repin"])
@pytest.mark.parametrize(
    "fault, diagnostic",
    [
        ("unknown-id", b"definition record is unknown"),
        ("unqualified-id", b"kind-qualified"),
        ("malformed-pin", b"pattern"),
        ("missing-definition", b"missing"),
        ("unsafe-definition", b"escape"),
        ("missing-sidecar", b"missing"),
        ("extra-wrapper", b"inventory mismatch"),
        ("missing-section", b"source section"),
        ("malformed-workflow", b"markers must occur exactly once"),
    ],
)
def test_multi_stale_maintenance_rejects_invalid_evidence_without_writes(
    committed_catalog_source_graph: Path,
    operation: str,
    fault: str,
    diagnostic: bytes,
) -> None:
    """Freshness allowances must not weaken any source validation boundary."""
    root = committed_catalog_source_graph
    installer = root / "scripts/install.sh"
    installer.write_bytes(installer.read_bytes() + b"\n# Reviewed fixture change.\n")
    selected_id = "shell:cg-brain-init"
    shell_path = root / catalog.SHELL_METADATA_PATH
    payload = catalog.load_strict_json(shell_path)
    other = next(
        item for item in payload["commands"] if item["id"] == "shell:cg-diff-summary"
    )
    if fault == "unknown-id":
        selected_id = "shell:cg-not-real"
    elif fault == "unqualified-id":
        selected_id = "cg-brain-init"
    elif fault == "malformed-pin":
        other["definitionDigest"] = "not-a-digest"
        _write_json(shell_path, payload)
    elif fault == "missing-definition":
        (root / "bin/cg-diff-summary").unlink()
    elif fault == "unsafe-definition":
        other["definitionSources"] = ["../outside"]
        _write_json(shell_path, payload)
    elif fault == "missing-sidecar":
        (root / ".github/prompts/cg-work.help.json").unlink()
    elif fault == "extra-wrapper":
        (root / "bin/cg-not-real").write_bytes(b"# unregistered wrapper\n")
    elif fault == "missing-section":
        other["documentationTargets"] = [
            {"path": catalog.WORKFLOW_SOURCE_PATH, "section": "no-such-section"}
        ]
        _write_json(shell_path, payload)
    else:
        workflow = root / catalog.WORKFLOW_SOURCE_PATH
        workflow.write_bytes(
            workflow.read_bytes() + catalog.WORKFLOW_START.encode("ascii")
        )
    before = _maintenance_artifact_bytes(root)
    generator = importlib.import_module("cg_generate_help_catalog")
    arguments = [
        "--root", str(root), f"--{operation}-definition-digest", selected_id,
    ]
    if operation == "repin":
        arguments.append("--reviewed")
    stdout, stderr = io.BytesIO(), io.BytesIO()

    assert generator.main(arguments, stdout, stderr) == 2
    assert diagnostic in stderr.getvalue()
    assert stdout.getvalue() == b""
    assert _maintenance_artifact_bytes(root) == before


@pytest.mark.parametrize(
    "fault, diagnostic",
    [
        ("selected-pin-stale", b"(shell:cg-brain-init) definitionDigest is stale"),
        ("final-invalid-evidence", b"markers must occur exactly once"),
        ("source-snapshot", b"source graph changed during definition repin"),
        ("metadata-conflict", b"definition metadata changed during repin"),
    ],
)
def test_multi_stale_repin_final_validation_and_conflicts_preserve_bytes(
    committed_catalog_source_graph: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
    diagnostic: bytes,
) -> None:
    """Inject faults at the second boundary without replacing real validation."""
    root = committed_catalog_source_graph
    for name in ("cg-brain-init", "cg-diff-summary"):
        path = root / "bin" / name
        path.write_bytes(path.read_bytes() + b"\n# Reviewed fixture change.\n")
    before = _maintenance_artifact_bytes(root)
    expected = dict(before)
    changed_path = None
    changed_content = None
    original_validate = catalog.validate_source_metadata
    calls = 0

    def inject_final_fault(*args: Any, **kwargs: Any) -> catalog.SourceMetadata:
        nonlocal calls, changed_path, changed_content
        calls += 1
        if calls == 2:
            if fault == "selected-pin-stale":
                kwargs["source_overrides"] = {
                    catalog.SHELL_METADATA_PATH: before[catalog.SHELL_METADATA_PATH]
                }
            else:
                relative = {
                    "final-invalid-evidence": catalog.WORKFLOW_SOURCE_PATH,
                    "source-snapshot": "bin/cg-diff-summary",
                    "metadata-conflict": catalog.SHELL_METADATA_PATH,
                }[fault]
                changed_path = root / relative
                addition = (
                    catalog.WORKFLOW_START.encode("ascii")
                    if fault == "final-invalid-evidence" else b"\n"
                )
                changed_content = changed_path.read_bytes() + addition
                changed_path.write_bytes(changed_content)
                if fault == "metadata-conflict":
                    expected[relative] = changed_content
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(maintenance, "validate_source_metadata", inject_final_fault)
    generator = importlib.import_module("cg_generate_help_catalog")
    stdout, stderr = io.BytesIO(), io.BytesIO()

    assert generator.main(
        [
            "--root", str(root), "--repin-definition-digest",
            "shell:cg-brain-init", "--reviewed",
        ],
        stdout, stderr,
    ) == 2
    assert calls == 2
    assert diagnostic in stderr.getvalue()
    assert stdout.getvalue() == b""
    assert _maintenance_artifact_bytes(root) == expected
    if changed_path is not None:
        assert changed_path.read_bytes() == changed_content


def test_malformed_late_source_prevents_catalog_write(tmp_path: Path) -> None:
    root = _copy_catalog_source_graph(tmp_path)
    output = root / catalog.CATALOG_OUTPUT_PATH
    output.write_bytes(b"existing catalog\n")
    sidecar_path = root / ".github/prompts/cg-work.help.json"
    sidecar = catalog.load_strict_json(sidecar_path)
    sidecar["unexpected"] = "inert"
    _write_json(sidecar_path, sidecar)

    with pytest.raises(catalog.HelpValidationError, match="unknown"):
        catalog.write_catalog(root)

    assert output.read_bytes() == b"existing catalog\n"


def test_module_help_records_and_catalog_ownership_are_strict(tmp_path: Path) -> None:
    root = _copy_catalog_source_graph(tmp_path)
    registry_path = root / catalog.MODULE_REGISTRY_PATH
    registry = catalog.load_strict_json(registry_path)
    help_module = next(item for item in registry["modules"] if item["id"] == "cap-help")
    help_module["help"]["unexpected"] = True
    _write_json(registry_path, registry)

    with pytest.raises(catalog.HelpValidationError, match="unknown"):
        catalog.generate_catalog_bytes(root)

    del help_module["help"]["unexpected"]
    help_module["ownedAssets"].remove(catalog.CATALOG_OUTPUT_PATH)
    _write_json(registry_path, registry)
    with pytest.raises(catalog.HelpValidationError, match="no owning module.*help-catalog"):
        catalog.generate_catalog_bytes(root)


def test_registry_layer_and_ownership_fail_before_help_extraction(tmp_path: Path) -> None:
    cases = (("cycle", "cycle"), ("ownership", "more than one"))
    for case, diagnostic in cases:
        root = _copy_catalog_source_graph(tmp_path / case)
        registry_path = root / catalog.MODULE_REGISTRY_PATH
        registry = catalog.load_strict_json(registry_path)
        if case == "cycle":
            kernel = next(item for item in registry["modules"] if item["id"] == "kernel")
            kernel["dependsOn"] = ["cap-help"]
        else:
            suite = next(item for item in registry["modules"] if item["id"] == "suite-cg")
            suite["ownedAssets"].append(catalog.SHELL_METADATA_PATH)
        _write_json(registry_path, registry)
        (root / ".github/prompts/cg-work.help.json").write_bytes(b"{}\n")

        with pytest.raises(
            catalog.HelpValidationError,
            match="module registry is invalid.*{}".format(diagnostic),
        ):
            catalog.generate_catalog_bytes(root)


def test_installer_inventory_ignores_comment_only_command_fixture() -> None:
    content = (FIXTURE_ROOT / "installer-posix-comment-only.sh").read_bytes()

    assert catalog.parse_posix_installer_inventory(content) == set()
    with pytest.raises(catalog.HelpValidationError, match="cg-index"):
        catalog.require_exact_installer_inventory(
            {"cg-index"}, set(), "POSIX installer"
        )


def test_posix_installer_requires_chmod_at_the_same_execution_level() -> None:
    """Comments and here-document bodies cannot carry the chmod evidence."""
    content = (
        b"if false; then\n"
        b"for cmd in index; do\n"
        b'  WRAPPER="$BIN_DIR/cg-$cmd"\n'
        b'  # chmod +x "$WRAPPER"\n'
        b"done\n"
        b"fi\n"
        b"if false; then\n"
        b'CG_EVIL_DST="$BIN_DIR/cg-evil"\n'
        b'# chmod +x "$BIN_DIR/cg-evil"\n'
        b"fi\n"
    )
    start = catalog.POSIX_INSTALL_START
    end = catalog.POSIX_INSTALL_END
    section = (start + "\n" + content.decode("utf-8") + "# pad\n" + end + "\n").encode("utf-8")

    assert catalog.parse_posix_installer_inventory(section) == set()


def test_windows_installer_requires_set_content_at_the_same_execution_level() -> None:
    """Commented declarations and bodies cannot satisfy Windows evidence."""
    content = (
        b"# $scripts = @(\"index\")\n"
        b'# foreach ($script in $scripts) { $cmdPath = Join-Path $binDir "cg-$script.cmd"; Set-Content -Path $cmdPath "x" }\n'
        b"if ($false) {\n"
        b'$indexCmdDst = Join-Path $binDir "cg-index.cmd"\n'
        b'if (Test-Path $indexCmdSrc) { Copy-Item -Path $indexCmdSrc -Destination $indexCmdDst -Force }\n'
        b"}\n"
    )
    start = catalog.WINDOWS_INSTALL_START
    end = catalog.WINDOWS_INSTALL_END
    section = (start + "\n" + content.decode("utf-8") + "# pad\n" + end + "\n").encode("utf-8")

    assert catalog.parse_windows_installer_inventory(section) == set()


def test_catalog_write_check_stdout_and_distinct_exit_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _copy_catalog_source_graph(tmp_path)
    generator = importlib.import_module("cg_generate_help_catalog")
    output = root / catalog.CATALOG_OUTPUT_PATH

    assert generator.main(["--root", str(root), "--check"], io.BytesIO(), io.BytesIO()) == 3
    stdout = io.BytesIO()
    assert generator.main(["--root", str(root), "--stdout"], stdout, io.BytesIO()) == 0
    assert stdout.getvalue() == catalog.generate_catalog_bytes(root)
    assert not output.exists()
    assert generator.main(["--root", str(root), "--write"], io.BytesIO(), io.BytesIO()) == 0
    assert output.read_bytes() == catalog.generate_catalog_bytes(root)
    assert generator.main(["--root", str(root), "--check"], io.BytesIO(), io.BytesIO()) == 0

    output.write_bytes(output.read_bytes() + b" ")
    stale_bytes = output.read_bytes()
    assert generator.main(["--root", str(root), "--check"], io.BytesIO(), io.BytesIO()) == 3
    assert output.read_bytes() == stale_bytes

    sidecar = root / ".github/prompts/cg-work.help.json"
    sidecar.write_bytes(b"{}\n")
    assert generator.main(["--root", str(root), "--write"], io.BytesIO(), io.BytesIO()) == 2
    assert output.read_bytes() == stale_bytes

    shutil.copyfile(REPO_ROOT / ".github/prompts/cg-work.help.json", sidecar)
    import secure_fs

    def interrupted_write(*_args, **_kwargs):
        raise secure_fs.SecureMutationError("interrupted replace")

    monkeypatch.setattr(secure_fs, "secure_write_bytes", interrupted_write)
    assert generator.main(["--root", str(root), "--write"], io.BytesIO(), io.BytesIO()) == 4
    assert output.read_bytes() == stale_bytes
    assert not list(output.parent.glob(".help-catalog.json.*.tmp"))


def test_maintainer_workflow_checks_reviews_and_writes_before_native_generation() -> None:
    prompt = (REPO_ROOT / ".github/prompts/cg-commit-push-pr.prompt.md").read_text(
        encoding="utf-8"
    )
    prompt_lower = prompt.lower()
    prompt_words = " ".join(prompt.split())

    check = prompt.index("cg_generate_help_catalog.py --check")
    preview = prompt.index("--preview-definition-digest")
    repin = prompt.index("--repin-definition-digest")
    write = prompt.index("cg_generate_help_catalog.py --write")
    native = prompt.index("cg_generate_targets.py --all")

    assert check < preview < repin < write < native
    assert "never auto-repin" in prompt_lower
    assert "halt before native-target generation" in prompt_lower
    assert ".cg-docs/views/**" in prompt
    assert "outside the marked help-workflow block" in prompt_words
