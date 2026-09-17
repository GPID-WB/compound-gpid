"""Strict schema and source validation for evidence-backed command help.

This module validates inert JSON data and repository source evidence only. It
does not execute prompt, metadata, workflow, wrapper, or documentation content.
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from help.base import (
    CATALOG_OUTPUT_PATH,
    CATALOG_SCHEMA_PATH,
    CATALOG_SCHEMA_VERSION,
    HelpValidationError,
    MODULE_REGISTRY_PATH,
    QUALIFIED_ID_PATTERN,
    SEMANTIC_STATES,
    SHELL_METADATA_PATH,
    SourceMetadata,
    SUPPORTED_OS,
    SUPPORTED_PLATFORMS,
    TRANSPORT_OPERATIONS,
    TRANSPORT_SCHEMA_PATH,
    TRANSPORT_SCHEMA_VERSION,
    UUID_PATTERN,
    WORKFLOW_END,
    WORKFLOW_SOURCE_PATH,
    WORKFLOW_START,
    _repository_root,
    _sorted_unique,
    _validate_relative_path,
    load_strict_json,
    load_strict_json_bytes,
    normalize_command_key,
)
from help.installers import (
    parse_posix_installer_inventory,
    parse_windows_installer_inventory,
    require_exact_installer_inventory,
)


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
        ) or (
            isinstance(value, float)
            and math.isfinite(value)
            and value.is_integer()
        )
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and (not isinstance(value, float) or math.isfinite(value))
        )
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _json_values_equal(first: Any, second: Any) -> bool:
    """Apply JSON Schema equality without Python bool/integer coercion."""
    if isinstance(first, bool) or isinstance(second, bool):
        return type(first) is type(second) and first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return first == second
    if type(first) is not type(second):
        return False
    if isinstance(first, list):
        return len(first) == len(second) and all(
            _json_values_equal(left, right)
            for left, right in zip(first, second)
        )
    if isinstance(first, dict):
        return set(first) == set(second) and all(
            _json_values_equal(first[key], second[key]) for key in first
        )
    return first == second


def _schema_at(root: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    if not reference.startswith("#/"):
        raise HelpValidationError("unsupported schema reference: {}".format(reference))
    current: Any = root
    for part in reference[2:].split("/"):
        if not isinstance(current, Mapping) or part not in current:
            raise HelpValidationError("unresolved schema reference: {}".format(reference))
        current = current[part]
    if not isinstance(current, Mapping):
        raise HelpValidationError("schema reference is not an object: {}".format(reference))
    return current


def _schema_errors(
    value: Any,
    schema: Mapping[str, Any],
    root: Mapping[str, Any],
    path: str,
) -> List[str]:
    if "$ref" in schema:
        return _schema_errors(value, _schema_at(root, str(schema["$ref"])), root, path)
    errors: List[str] = []
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
        return ["{} must be {}".format(path, expected_type)]
    if "const" in schema and not _json_values_equal(value, schema["const"]):
        errors.append("{} must equal {!r}".format(path, schema["const"]))
    if "enum" in schema and not any(
        _json_values_equal(value, option) for option in schema["enum"]
    ):
        errors.append("{} must be one of {!r}".format(path, schema["enum"]))
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            errors.append("{} is too short".format(path))
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append("{} does not match required pattern".format(path))
    if isinstance(value, list):
        if len(value) < int(schema.get("minItems", 0)):
            errors.append("{} has too few items".format(path))
        if "maxItems" in schema and len(value) > int(schema["maxItems"]):
            errors.append("{} has more than {} items".format(path, schema["maxItems"]))
        if schema.get("uniqueItems"):
            if any(
                _json_values_equal(value[left], value[right])
                for left in range(len(value))
                for right in range(left + 1, len(value))
            ):
                errors.append("{} items must be unique".format(path))
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                errors.extend(
                    _schema_errors(item, item_schema, root, "{}[{}]".format(path, index))
                )
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append("{} is missing required field {!r}".format(path, key))
        properties = schema.get("properties", {})
        if isinstance(properties, Mapping):
            if schema.get("additionalProperties") is False:
                for key in value:
                    if key not in properties:
                        errors.append("{} has unknown field {!r}".format(path, key))
            for key, child in properties.items():
                if key in value and isinstance(child, Mapping):
                    errors.extend(
                        _schema_errors(value[key], child, root, "{}.{}".format(path, key))
                    )
    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        branch_errors = [
            _schema_errors(value, branch, root, path)
            for branch in one_of
            if isinstance(branch, Mapping)
        ]
        matches = sum(not branch for branch in branch_errors)
        if matches != 1:
            details = min(
                (branch for branch in branch_errors if branch),
                key=len,
                default=[],
            )
            errors.append(
                "{} must match exactly one schema branch{}".format(
                    path, ": " + details[0] if details else ""
                )
            )
    return errors


def _validate_against_schema(
    value: Any,
    schema: Mapping[str, Any],
    label: str,
    *,
    root_schema: Optional[Mapping[str, Any]] = None,
) -> None:
    errors = _schema_errors(value, schema, root_schema or schema, label)
    if errors:
        raise HelpValidationError("; ".join(errors[:10]))


def _load_schema(source_root: Path, relative_path: str) -> Mapping[str, Any]:
    value = load_strict_json(source_root / relative_path)
    if not isinstance(value, dict):
        raise HelpValidationError("{} must contain a JSON object".format(relative_path))
    return value


def _module_closure(registry: Mapping[str, Any], suite_name: str) -> set:
    suite_id = suite_name if suite_name.startswith("suite-") else "suite-" + suite_name
    from skill_management.services.registry import transitive_closure

    try:
        return transitive_closure(registry, [suite_id])
    except ValueError as error:
        raise HelpValidationError(str(error)) from error


def _validate_command_semantics(
    command: Mapping[str, Any], registry: Mapping[str, Any], label: str
) -> None:
    command_id = str(command["id"])
    kind, identifier = command_id.split(":", 1)
    name = str(command["name"])
    expected_name = "/" + identifier if kind == "slash" else identifier
    if command["kind"] != kind or name != expected_name:
        raise HelpValidationError(
            "{} id, kind, and name must agree".format(label)
        )
    modules = {
        item.get("id"): item
        for item in registry.get("modules", [])
        if isinstance(item, dict)
    }
    owner = command["ownerModule"]
    if owner not in modules:
        raise HelpValidationError("{}.ownerModule is unknown: {}".format(label, owner))
    suites = command["supportedSuites"]
    if not _sorted_unique(suites):
        raise HelpValidationError("{}.supportedSuites must be sorted and unique".format(label))
    expected_suites = []
    for module in modules.values():
        if module.get("layer") != "suite" or owner not in _module_closure(
            registry, str(module.get("id", ""))
        ):
            continue
        help_metadata = module.get("help")
        suite_id = (
            help_metadata.get("suiteId")
            if isinstance(help_metadata, Mapping)
            else None
        )
        if not isinstance(suite_id, str):
            module_id = str(module["id"])
            suite_id = module_id[6:] if module_id.startswith("suite-") else module_id
        expected_suites.append(suite_id)
    expected_suites.sort()
    if suites != expected_suites:
        raise HelpValidationError(
            "{}.supportedSuites must exactly match owner suite closures: {!r}"
            .format(label, expected_suites)
        )
    if not _sorted_unique(command["aliases"]):
        raise HelpValidationError("{}.aliases must be sorted and unique".format(label))
    platforms = command["supportedPlatforms"]
    if not _sorted_unique(platforms) or not set(platforms) <= SUPPORTED_PLATFORMS:
        raise HelpValidationError("{}.supportedPlatforms is invalid or unsorted".format(label))
    operating_systems = command["supportedOS"]
    if not _sorted_unique(operating_systems) or not set(operating_systems) <= SUPPORTED_OS:
        raise HelpValidationError("{}.supportedOS is invalid or unsorted".format(label))
    if kind == "slash" and operating_systems != ["any"]:
        raise HelpValidationError("{} slash commands must use supportedOS ['any']".format(label))
    if kind == "shell" and "any" in operating_systems:
        raise HelpValidationError("{} shell commands require per-OS support".format(label))
    for relation in command["relatedCommands"]:
        if not QUALIFIED_ID_PATTERN.fullmatch(relation["id"]):
            raise HelpValidationError("{}.relatedCommands id must be qualified".format(label))
    activation_suites = [item["suite"] for item in command["activation"]]
    if activation_suites != suites:
        raise HelpValidationError(
            "{}.activation must cover supportedSuites in sorted order".format(label)
        )
    for activation in command["activation"]:
        suite_module = modules.get("suite-" + activation["suite"])
        expected = (
            suite_module.get("help", {}).get("activation")
            if isinstance(suite_module, Mapping)
            else None
        )
        observed = {
            "sourcePath": activation["sourcePath"],
            "sourceSection": activation["sourceSection"],
        }
        if expected is not None and (
            not isinstance(expected, Mapping) or observed != dict(expected)
        ):
            raise HelpValidationError(
                "{}.activation has ambiguous or incorrect suite evidence".format(label)
            )


def validate_catalog(value: Any, registry: Mapping[str, Any]) -> None:
    """Validate a complete catalog against schema and cross-record invariants."""
    schema = _load_schema(_repository_root(), CATALOG_SCHEMA_PATH)
    _validate_against_schema(value, schema, "catalog")
    if not isinstance(value, dict):
        raise HelpValidationError("catalog must be an object")
    if value["schemaVersion"] != CATALOG_SCHEMA_VERSION:
        raise HelpValidationError("catalog.schemaVersion is unsupported")
    for field in ("suites", "commands", "workflows"):
        ids = [item["id"] for item in value[field]]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise HelpValidationError("catalog.{} must be sorted by unique id".format(field))
    known_suites = {item["id"] for item in value["suites"]}
    registry_modules = {
        item.get("id"): item
        for item in registry.get("modules", [])
        if isinstance(item, dict)
    }
    for suite in value["suites"]:
        module = registry_modules.get(suite["moduleId"])
        if not isinstance(module, dict) or module.get("layer") != "suite":
            raise HelpValidationError("catalog suite moduleId is unknown")
        if suite["moduleId"] not in {suite["id"], "suite-" + suite["id"]}:
            raise HelpValidationError("catalog suite id and moduleId disagree")
    known_commands = {item["id"] for item in value["commands"]}
    aliases = set()
    for index, command in enumerate(value["commands"]):
        label = "catalog.commands[{}]".format(index)
        _validate_command_semantics(command, registry, label)
        if not set(command["supportedSuites"]) <= known_suites:
            raise HelpValidationError("{}.supportedSuites is unknown".format(label))
        kind = command["kind"]
        primary = normalize_command_key(command["name"])
        for alias in [primary] + command["aliases"]:
            normalized_alias = normalize_command_key(alias)
            if not normalized_alias:
                raise HelpValidationError(
                    "command aliases must not normalize to an empty value"
                )
            key = (kind, normalized_alias)
            if key in aliases:
                raise HelpValidationError("duplicate kind-scoped command alias: {}".format(alias))
            aliases.add(key)
        for relation in command["relatedCommands"]:
            if relation["id"] not in known_commands:
                raise HelpValidationError("{} has unknown related command".format(label))
    for index, workflow in enumerate(value["workflows"]):
        label = "catalog.workflows[{}]".format(index)
        if not _sorted_unique(workflow["supportedSuites"]):
            raise HelpValidationError("{}.supportedSuites must be sorted".format(label))
        if not set(workflow["supportedSuites"]) <= known_suites:
            raise HelpValidationError("{} has unknown suite".format(label))
        for expected_order, step in enumerate(workflow["steps"], start=1):
            if step["order"] != expected_order or step["commandId"] not in known_commands:
                raise HelpValidationError("{} has broken workflow step".format(label))
            command = next(
                item for item in value["commands"] if item["id"] == step["commandId"]
            )
            if not set(workflow["supportedSuites"]) <= set(command["supportedSuites"]):
                raise HelpValidationError(
                    "{} uses a command unavailable to its suites".format(label)
                )


def validate_transport_envelope(value: Any) -> None:
    """Validate one operation-discriminated transport envelope."""
    schema = _load_schema(_repository_root(), TRANSPORT_SCHEMA_PATH)
    _validate_against_schema(value, schema, "transport")
    if not isinstance(value, dict) or value.get("schemaVersion") != TRANSPORT_SCHEMA_VERSION:
        raise HelpValidationError("transport schemaVersion is unsupported")
    operation = value.get("operation")
    if operation not in TRANSPORT_OPERATIONS:
        raise HelpValidationError("transport operation is unsupported")
    request_id = value.get("requestId")
    if request_id is not None and not UUID_PATTERN.fullmatch(request_id):
        raise HelpValidationError("transport requestId is invalid")
    if operation == "request-prepared":
        expected = ".compound-gpid/runtime/help-requests/{}.query.txt".format(request_id)
        if value["queryPath"] != expected:
            raise HelpValidationError("request-prepared queryPath does not match requestId")
    if operation == "selection-prepared":
        expected = ".compound-gpid/runtime/help-requests/{}.selection.json".format(
            request_id
        )
        if value["selectionPath"] != expected:
            raise HelpValidationError("selection-prepared selectionPath does not match requestId")
    result = value.get("result")
    if isinstance(result, dict) and result.get("state") not in SEMANTIC_STATES:
        raise HelpValidationError("semantic result state is unsupported")
    if isinstance(result, dict) and result.get("state") == "candidates":
        data = result["data"]
        command_ids = data["commandIds"]
        if not (
            len(command_ids)
            == len(data["reasons"])
            == len(data["followUpQueries"])
        ):
            raise HelpValidationError("candidate evidence arrays must have equal lengths")
        expected_queries = [
            "/cg-help /" + command_id.split(":", 1)[1]
            if command_id.startswith("slash:")
            else "/cg-help " + command_id
            for command_id in command_ids
        ]
        if data["followUpQueries"] != expected_queries:
            raise HelpValidationError(
                "candidate followUpQueries must use slash or shell-qualified syntax"
            )


def parse_transport_envelope(content: bytes, *, source: str) -> Dict[str, Any]:
    """Parse and validate one strict transport envelope from inert JSON bytes."""
    value = load_strict_json_bytes(content, source=source)
    validate_transport_envelope(value)
    if not isinstance(value, dict):  # Defensive narrowing after schema validation.
        raise HelpValidationError("transport envelope must be an object")
    return value


def _source_path(root: Path, relative_path: str, label: str) -> Path:
    """Resolve one canonical source path without permitting path or link escapes."""
    _validate_relative_path(relative_path, label)
    source_root = Path(root).resolve()
    candidate = source_root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(source_root)
    except (OSError, ValueError) as error:
        raise HelpValidationError(
            "{} is missing or escapes the repository: {}".format(label, relative_path)
        ) from error
    if candidate.is_symlink() or not resolved.is_file():
        raise HelpValidationError("{} must be a regular non-link file".format(label))
    return candidate


def _read_source_bytes(
    root: Path,
    relative_path: str,
    label: str,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> bytes:
    """Read exact bytes from one validated canonical source file."""
    path = _source_path(root, relative_path, label)
    if source_overrides is not None and relative_path in source_overrides:
        content = source_overrides[relative_path]
        if not isinstance(content, bytes):
            raise HelpValidationError(
                "{} override must contain exact bytes".format(relative_path)
            )
        return content
    try:
        return path.read_bytes()
    except OSError as error:
        raise HelpValidationError(
            "cannot read {}: {}".format(relative_path, error)
        ) from error


def compute_definition_digest(
    root: Path,
    sources: Sequence[str],
    *,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> str:
    """Hash sorted canonical source identities and exact bytes."""
    if list(sources) != sorted(set(sources)) or not sources:
        raise HelpValidationError("definitionSources must be sorted, unique, and non-empty")
    captured: List[Tuple[str, bytes]] = []
    for source in sources:
        captured.append(
            (
                source,
                _read_source_bytes(
                    root, source, "definition source", source_overrides
                ),
            )
        )
    if len(captured) == 1:
        return hashlib.sha256(captured[0][1]).hexdigest()
    hasher = hashlib.sha256()
    for source, content in captured:
        hasher.update(source.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(content)
        hasher.update(b"\0")
    return hasher.hexdigest()


def _heading_ids(text: str) -> Dict[str, int]:
    """Count GitHub-rendered heading anchors, which validators must match.

    GitHub lowercases each heading, strips non-word ASCII punctuation (keeping
    spaces, hyphens, and underscores), and converts each space run to a
    hyphen without collapsing existing separators (e.g. ``Step 3 - Link``
    anchors as ``step-3---link``).
    """
    result: Dict[str, int] = {}
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip().casefold()
        slug = re.sub(r"[^a-z0-9_\s-]", "", title)
        slug = re.sub(r"\s+", "-", slug).strip("-")
        if slug:
            result[slug] = result.get(slug, 0) + 1
    return result


def _validate_source_reference(
    root: Path,
    source_path: str,
    section: str,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> None:
    try:
        text = _read_source_bytes(
            root, source_path, "sourcePath", source_overrides
        ).decode("utf-8")
    except UnicodeError as error:
        raise HelpValidationError("source evidence is not UTF-8: {}".format(source_path)) from error
    counts = _heading_ids(text)
    if section not in counts:
        raise HelpValidationError(
            "source section {!r} is missing from {}".format(section, source_path)
        )
    if counts[section] > 1:
        raise HelpValidationError(
            "source section {!r} is ambiguous in {} ({} occurrences)"
            .format(section, source_path, counts[section])
        )


def _workflow_payload(
    root: Path,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> Tuple[Tuple[Dict[str, Any], ...], bytes]:
    """Extract only the fixed inert workflow JSON block and its exact bytes."""
    try:
        text = _read_source_bytes(
            root, WORKFLOW_SOURCE_PATH, "workflow source", source_overrides
        ).decode("utf-8")
    except UnicodeError as error:
        raise HelpValidationError(
            "{} must be UTF-8".format(WORKFLOW_SOURCE_PATH)
        ) from error
    if text.count(WORKFLOW_START) != 1 or text.count(WORKFLOW_END) != 1:
        raise HelpValidationError("workflow help markers must occur exactly once")
    marked = text.split(WORKFLOW_START, 1)[1].split(WORKFLOW_END, 1)[0].strip()
    match = re.fullmatch(r"```json\s*\n(.*)\n```", marked, flags=re.DOTALL)
    if match is None:
        raise HelpValidationError("workflow help marker must contain one JSON fence")
    payload = load_strict_json_bytes(match.group(1).encode("utf-8"), source=WORKFLOW_SOURCE_PATH)
    if not isinstance(payload, dict) or set(payload) != {"schemaVersion", "workflows"}:
        raise HelpValidationError("workflow metadata root has unknown or missing fields")
    if payload["schemaVersion"] != 1 or not isinstance(payload["workflows"], list):
        raise HelpValidationError("workflow metadata schemaVersion/workflows is invalid")
    return tuple(payload["workflows"]), match.group(1).encode("utf-8")


def _workflow_records(
    root: Path,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> Tuple[Dict[str, Any], ...]:
    """Return validated-shape workflow records for compatibility callers."""
    return _workflow_payload(root, source_overrides)[0]


def _validate_definition(
    root: Path,
    command: Mapping[str, Any],
    label: str,
    *,
    allow_stale: bool = False,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> str:
    digest = compute_definition_digest(
        root,
        command["definitionSources"],
        source_overrides=source_overrides,
    )
    if command["definitionDigest"] != digest and not allow_stale:
        raise HelpValidationError(
            "{} ({}) definitionDigest is stale; review metadata and repin this record"
            .format(label, command["id"])
        )
    _source_path(root, command["sourcePath"], "{}.sourcePath".format(label))
    for target in command["documentationTargets"]:
        _validate_source_reference(
            root,
            target["path"],
            target["section"],
            source_overrides,
        )
    for evidence in command["availability"]["evidence"]:
        _source_path(
            root,
            evidence["sourcePath"],
            "availability.evidence.sourcePath",
        )
    for activation in command["activation"]:
        _validate_source_reference(
            root,
            activation["sourcePath"],
            activation["sourceSection"],
            source_overrides,
        )
    return digest


def _validate_module_registry(root: Path, registry: Dict[str, Any]) -> None:
    """Run all layer and ownership checks before extracting help records."""
    try:
        import cg_validate_modules as module_validator
    except ImportError as error:
        raise HelpValidationError(
            "module registry validator is unavailable in this environment"
        ) from error

    errors = module_validator.validate_registry_schema(registry)
    if not errors:
        errors.extend(module_validator.check_layer_rules(registry))
    if errors:
        raise HelpValidationError(
            "module registry is invalid: {}".format("; ".join(errors[:10]))
        )
    try:
        assets = set(module_validator.canonical_assets(root))
    except (OSError, ValueError) as error:
        raise HelpValidationError(
            "module registry ownership inventory is invalid: {}".format(error)
        ) from error
    # The generated catalog remains an ownership asset when --check diagnoses
    # that its current output is absent.
    assets.add(CATALOG_OUTPUT_PATH)
    ordered_assets = tuple(sorted(assets))
    errors.extend(module_validator.check_no_physical_relocation(root))
    errors.extend(module_validator.check_owned_assets_exist(registry, ordered_assets))
    errors.extend(module_validator.check_ownership_closure(registry, ordered_assets))
    errors.extend(
        module_validator.check_frontmatter_ownership(root, registry, ordered_assets)
    )
    errors.extend(module_validator.check_ambiguous_entries(registry))
    if errors:
        raise HelpValidationError(
            "module registry is invalid: {}".format("; ".join(errors[:10]))
        )


def _slash_description(
    source_root: Path,
    command: Mapping[str, Any],
    label: str,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> str:
    """Derive the generated sidecar summary from the prompt frontmatter.

    The frontmatter description is the single source of truth; the generated
    catalog summary must equal it, so a missing or non-string description
    fails closed instead of emitting an author-provided summary.
    """
    content = _read_source_bytes(
        source_root, command["sourcePath"], "definition source", source_overrides
    )
    try:
        from brain.utils import parse_frontmatter

        parsed = parse_frontmatter(
            content.decode("utf-8", errors="strict"), source=command["sourcePath"]
        )
    except (UnicodeDecodeError, ImportError) as error:
        raise HelpValidationError(
            "{} prompt frontmatter could not be parsed: {}".format(label, error)
        )
    description = parsed.get("description")
    if not isinstance(description, str) or not description.strip():
        raise HelpValidationError(
            "{} prompt description is missing; generated summary requires it".format(
                label
            )
        )
    return description


def validate_source_metadata(
    root: Path,
    *,
    maintenance_definition_id: Optional[str] = None,
    require_current_definition: bool = False,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> SourceMetadata:
    """Validate exact canonical prompt, shell, registry, and workflow evidence.

    Named maintenance permits stale pins without relaxing source validation.
    Prospective repins must also require the named definition to be current.
    Without a maintenance ID, every definition must be current.
    """
    source_root = Path(root).resolve()
    source_inputs: Dict[str, bytes] = {}

    def capture(identity: str, content: bytes) -> None:
        previous = source_inputs.get(identity)
        if previous is not None and previous != content:
            raise HelpValidationError(
                "source identity has conflicting bytes: {}".format(identity)
            )
        source_inputs[identity] = content

    registry_bytes = _read_source_bytes(
        source_root,
        MODULE_REGISTRY_PATH,
        "module registry",
        source_overrides,
    )
    registry = load_strict_json_bytes(registry_bytes, source=MODULE_REGISTRY_PATH)
    if not isinstance(registry, dict) or registry.get("schemaVersion") != 2:
        raise HelpValidationError("module registry schemaVersion 2 is required")
    try:
        from skill_management.services.registry import matching_asset_owners
    except ImportError as error:
        raise HelpValidationError(
            "module registry service is unavailable in this environment"
        ) from error

    _validate_module_registry(source_root, registry)
    if matching_asset_owners(registry, CATALOG_OUTPUT_PATH) != ("cap-help",):
        raise HelpValidationError("help catalog must be owned only by cap-help")
    capture(MODULE_REGISTRY_PATH, registry_bytes)
    for module in registry.get("modules", []):
        if not isinstance(module, dict):
            continue
        activation = module.get("help", {}).get("activation")
        if isinstance(activation, dict):
            _validate_source_reference(
                source_root,
                activation["sourcePath"],
                activation["sourceSection"],
                source_overrides,
            )
    schema = _load_schema(source_root, CATALOG_SCHEMA_PATH)
    command_schema = _schema_at(schema, "#/$defs/command")
    workflow_schema = _schema_at(schema, "#/$defs/workflow")
    prompts = tuple(
        path
        for path in sorted((source_root / ".github/prompts").glob("*.prompt.md"))
        if path.name.startswith(("cg-", "cr-"))
    )
    sidecars = tuple(sorted((source_root / ".github/prompts").glob("*.help.json")))
    expected_sidecars = {
        path.name[: -len(".prompt.md")] + ".help.json" for path in prompts
    }
    actual_sidecars = {path.name for path in sidecars}
    if actual_sidecars != expected_sidecars:
        raise HelpValidationError(
            "slash metadata inventory mismatch: missing={!r}, extra={!r}".format(
                sorted(expected_sidecars - actual_sidecars),
                sorted(actual_sidecars - expected_sidecars),
            )
        )
    slash_commands: List[Dict[str, Any]] = []
    maintenance_target_found = False
    for sidecar in sidecars:
        relative = sidecar.relative_to(source_root).as_posix()
        sidecar_bytes = _read_source_bytes(
            source_root, relative, "help sidecar", source_overrides
        )
        command = load_strict_json_bytes(sidecar_bytes, source=relative)
        _validate_against_schema(
            command, command_schema, relative, root_schema=schema
        )
        description = _slash_description(
            source_root, command, relative, source_overrides
        )
        command = dict(command)
        command["summary"] = description
        _validate_against_schema(
            command, command_schema, relative, root_schema=schema
        )
        _validate_command_semantics(command, registry, relative)
        basename = sidecar.name[: -len(".help.json")]
        if command["id"] != "slash:" + basename or command["sourcePath"] != (
            ".github/prompts/" + basename + ".prompt.md"
        ):
            raise HelpValidationError("{} basename/source identity mismatch".format(relative))
        owners = matching_asset_owners(registry, relative)
        if owners != (command["ownerModule"],):
            raise HelpValidationError("{} sidecar ownership mismatch".format(relative))
        owner_module = next(
            item
            for item in registry["modules"]
            if item.get("id") == command["ownerModule"]
        )
        help_metadata = owner_module.get("help", {})
        identifier = command["id"].split(":", 1)[1]
        if command["kind"] not in help_metadata.get("commandKinds", []) or not any(
            identifier.startswith(prefix)
            for prefix in help_metadata.get("commandPrefixes", [])
        ):
            raise HelpValidationError("{} owner help prefix/kind mismatch".format(relative))
        if command["definitionSources"] != [command["sourcePath"]]:
            raise HelpValidationError(
                "{} slash definitionSources must contain only its prompt".format(relative)
            )
        selected = command["id"] == maintenance_definition_id
        maintenance_target_found = maintenance_target_found or selected
        _validate_definition(
            source_root,
            command,
            relative,
            allow_stale=maintenance_definition_id is not None
            and not (selected and require_current_definition),
            source_overrides=source_overrides,
        )
        capture(relative, sidecar_bytes)
        for definition_source in command["definitionSources"]:
            capture(
                definition_source,
                _read_source_bytes(
                    source_root,
                    definition_source,
                    "definition source",
                    source_overrides,
                ),
            )
        slash_commands.append(command)

    shell_bytes = _read_source_bytes(
        source_root,
        SHELL_METADATA_PATH,
        "shell metadata",
        source_overrides,
    )
    shell_payload = load_strict_json_bytes(shell_bytes, source=SHELL_METADATA_PATH)
    if not isinstance(shell_payload, dict) or set(shell_payload) != {"schemaVersion", "commands"}:
        raise HelpValidationError("shell metadata has unknown or missing fields")
    if shell_payload["schemaVersion"] != 1 or not isinstance(shell_payload["commands"], list):
        raise HelpValidationError("shell metadata schemaVersion/commands is invalid")
    if matching_asset_owners(registry, SHELL_METADATA_PATH) != ("cap-help",):
        raise HelpValidationError("shell metadata must be owned only by cap-help")
    capture(SHELL_METADATA_PATH, shell_bytes)
    help_owner = next(
        (
            item
            for item in registry["modules"]
            if isinstance(item, dict) and item.get("id") == "cap-help"
        ),
        None,
    )
    if not isinstance(help_owner, dict):
        raise HelpValidationError("cap-help module is missing")
    shell_commands: List[Dict[str, Any]] = []
    for index, command in enumerate(shell_payload["commands"]):
        label = "shell-commands.commands[{}]".format(index)
        _validate_against_schema(command, command_schema, label, root_schema=schema)
        _validate_command_semantics(command, registry, label)
        if command["kind"] != "shell":
            raise HelpValidationError("{} must be a shell command".format(label))
        if command["sourcePath"] != "bin/" + command["name"]:
            raise HelpValidationError("{} shell sourcePath must name its wrapper".format(label))
        identifier = command["id"].split(":", 1)[1]
        help_metadata = help_owner["help"]
        if "shell" not in help_metadata["commandKinds"] or not any(
            identifier.startswith(prefix)
            for prefix in help_metadata["commandPrefixes"]
        ):
            raise HelpValidationError("{} has an invalid shell command prefix".format(label))
        selected = command["id"] == maintenance_definition_id
        maintenance_target_found = maintenance_target_found or selected
        _validate_definition(
            source_root,
            command,
            label,
            allow_stale=maintenance_definition_id is not None
            and not (selected and require_current_definition),
            source_overrides=source_overrides,
        )
        for definition_source in command["definitionSources"]:
            capture(
                definition_source,
                _read_source_bytes(
                    source_root,
                    definition_source,
                    "definition source",
                    source_overrides,
                ),
            )
        evidence_os = {item["os"] for item in command["availability"]["evidence"]}
        if evidence_os != set(command["supportedOS"]):
            raise HelpValidationError("{} per-OS evidence mismatch".format(label))
        expected_evidence = {
            operating_system: (
                "bin/" + command["name"] + ".cmd"
                if operating_system == "windows"
                else "bin/" + command["name"]
            )
            for operating_system in command["supportedOS"]
        }
        observed_evidence = {
            item["os"]: item["sourcePath"]
            for item in command["availability"]["evidence"]
        }
        if observed_evidence != expected_evidence:
            raise HelpValidationError("{} per-OS wrapper evidence is invalid".format(label))
        shell_commands.append(command)
    shell_commands.sort(key=lambda item: item["id"])

    posix_wrappers = {
        path.name
        for path in (source_root / "bin").glob("cg-*")
        if path.is_file() and path.suffix != ".cmd"
    }
    windows_wrappers = {
        path.stem for path in (source_root / "bin").glob("cg-*.cmd") if path.is_file()
    }
    metadata_names = {item["name"] for item in shell_commands}
    metadata_windows = {
        item["name"] for item in shell_commands if "windows" in item["supportedOS"]
    }
    if metadata_names != posix_wrappers or metadata_windows != windows_wrappers:
        raise HelpValidationError("shell wrapper and metadata inventory mismatch")
    install_posix = _read_source_bytes(
        source_root, "scripts/install.sh", "POSIX installer", source_overrides
    )
    install_windows = _read_source_bytes(
        source_root, "install.ps1", "Windows installer", source_overrides
    )
    metadata_posix = {
        item["name"] for item in shell_commands if "posix" in item["supportedOS"]
    }
    metadata_windows = {
        item["name"] for item in shell_commands if "windows" in item["supportedOS"]
    }
    require_exact_installer_inventory(
        metadata_posix,
        parse_posix_installer_inventory(install_posix),
        "POSIX installer",
    )
    require_exact_installer_inventory(
        metadata_windows,
        parse_windows_installer_inventory(install_windows),
        "Windows installer",
    )
    for command in shell_commands:
        name = command["name"]
        definitions = set(command["definitionSources"])
        if "posix" in command["supportedOS"] and (
            "bin/" + name not in definitions
            or "scripts/install.sh" not in definitions
        ):
            raise HelpValidationError("{} lacks POSIX install evidence".format(name))
        if "windows" in command["supportedOS"] and (
            "bin/" + name + ".cmd" not in definitions
            or "install.ps1" not in definitions
        ):
            raise HelpValidationError("{} lacks Windows install evidence".format(name))

    workflow_records, workflow_bytes = _workflow_payload(
        source_root, source_overrides
    )
    workflows = sorted(workflow_records, key=lambda item: item.get("id", ""))
    capture(WORKFLOW_SOURCE_PATH + "#cg-help-workflows", workflow_bytes)
    command_ids = {item["id"] for item in slash_commands + shell_commands}
    if len(command_ids) != len(slash_commands) + len(shell_commands):
        raise HelpValidationError("canonical command ids must be unique")
    for command in slash_commands + shell_commands:
        for relation in command["relatedCommands"]:
            if relation["id"] not in command_ids:
                raise HelpValidationError("related command is unresolved")
    for index, workflow in enumerate(workflows):
        label = "workflows[{}]".format(index)
        _validate_against_schema(workflow, workflow_schema, label, root_schema=schema)
        _validate_source_reference(
            source_root, workflow["sourcePath"], workflow["sourceSection"]
        )
        for order, step in enumerate(workflow["steps"], start=1):
            if step["order"] != order or step["commandId"] not in command_ids:
                raise HelpValidationError("{} has unresolved workflow step".format(label))
            for evidence in step["evidence"]:
                _validate_source_reference(
                    source_root,
                    evidence["sourcePath"],
                    evidence["sourceSection"],
                    source_overrides,
                )
    if maintenance_definition_id is not None and not maintenance_target_found:
        raise HelpValidationError(
            "definition record is unknown: {}".format(maintenance_definition_id)
        )
    return SourceMetadata(
        sidecars,
        tuple(slash_commands),
        tuple(shell_commands),
        tuple(workflows),
        tuple(sorted(source_inputs.items())),
    )