"""Strict schema and source validators for evidence-backed command help.

This Phase 1 module validates inert JSON data only. It does not execute prompt,
metadata, workflow, wrapper, or documentation content.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


CATALOG_SCHEMA_VERSION = 1
TRANSPORT_SCHEMA_VERSION = 1
CATALOG_SCHEMA_PATH = "scripts/schemas/help_catalog_schema.json"
TRANSPORT_SCHEMA_PATH = "scripts/schemas/help_transport_schema.json"
MODULE_REGISTRY_PATH = ".github/shared/module-registry.json"
SHELL_METADATA_PATH = ".github/shared/shell-commands.json"
CATALOG_OUTPUT_PATH = ".github/shared/help-catalog.json"
WORKFLOW_SOURCE_PATH = "docs/workflow.md"
WORKFLOW_START = "<!-- cg:help-workflows:start -->"
WORKFLOW_END = "<!-- cg:help-workflows:end -->"
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_INSTALLER_BYTES = 1024 * 1024
POSIX_INSTALL_START = "# Step 3: Create bin/ wrappers"
POSIX_INSTALL_END = "# Step 4: Add bin/ to PATH via shell profile"
WINDOWS_INSTALL_START = "# Step 3: Register cg-* commands via .cmd wrappers on PATH"
WINDOWS_INSTALL_END = "# Add bin/ to user PATH"
SUPPORTED_PLATFORMS = frozenset(
    {"copilot", "claude-code", "codex", "opencode", "kilo"}
)
SUPPORTED_OS = frozenset({"any", "posix", "windows"})
SEMANTIC_STATES = frozenset(
    {"overview", "exact", "workflow", "candidates", "unsupported", "error"}
)
TRANSPORT_OPERATIONS = frozenset(
    {
        "request-prepared",
        "query-completed",
        "selection-prepared",
        "selection-rendered",
        "transport-error",
    }
)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
QUALIFIED_ID_PATTERN = re.compile(r"^(slash|shell):[a-z][a-z0-9-]*$")
WORKFLOW_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
GENERATOR_VERSION = "1.0.0"


class HelpValidationError(ValueError):
    """Raised when help schema or source evidence is invalid."""


class HelpCatalogStaleError(RuntimeError):
    """Raised when the emitted catalog is missing or differs from expected bytes."""


class HelpCatalogIOError(OSError):
    """Raised when validated catalog or metadata bytes cannot be replaced safely."""


@dataclass(frozen=True)
class SourceMetadata:
    """Validated canonical help source records.

    Args:
        sidecar_paths: Sorted canonical slash-command sidecar paths.
        slash_commands: Validated slash-command records.
        shell_commands: Validated shell-command records.
        workflows: Validated explicit workflow records.
        source_inputs: Sorted source identities and exact accepted source bytes.
    """

    sidecar_paths: Tuple[Path, ...]
    slash_commands: Tuple[Dict[str, Any], ...]
    shell_commands: Tuple[Dict[str, Any], ...]
    workflows: Tuple[Dict[str, Any], ...]
    source_inputs: Tuple[Tuple[str, bytes], ...] = ()


def _duplicate_key_hook(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HelpValidationError("duplicate JSON key: {!r}".format(key))
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise HelpValidationError("non-finite JSON number is forbidden: {}".format(value))


def _reject_surrogates(value: Any, source: str, path: str = "$") -> None:
    """Reject non-scalar Unicode recursively in parsed JSON keys and values."""
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise HelpValidationError(
                "{} contains a Unicode surrogate at {}".format(source, path)
            )
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_surrogates(item, source, "{}[{}]".format(path, index))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_surrogates(key, source, "{} object key".format(path))
            _reject_surrogates(
                item,
                source,
                "{}[{}]".format(path, json.dumps(key, ensure_ascii=True)),
            )


def load_strict_json_bytes(content: bytes, *, source: str) -> Any:
    """Parse bounded UTF-8 JSON while rejecting duplicate keys and constants."""
    if len(content) > MAX_JSON_BYTES:
        raise HelpValidationError("{} exceeds the JSON byte limit".format(source))
    if content.startswith(b"\xef\xbb\xbf"):
        raise HelpValidationError("{} must be UTF-8 without BOM".format(source))
    try:
        text = content.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_key_hook,
            parse_constant=_reject_constant,
        )
        _reject_surrogates(value, source)
        return value
    except HelpValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HelpValidationError("{} is not strict JSON: {}".format(source, error)) from error


def load_strict_json(path: Path) -> Any:
    """Load one strict JSON file without interpreting any extracted strings."""
    try:
        content = Path(path).read_bytes()
    except OSError as error:
        raise HelpValidationError("cannot read {}: {}".format(path, error)) from error
    return load_strict_json_bytes(content, source=Path(path).as_posix())


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


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sorted_unique(values: Sequence[str]) -> bool:
    return list(values) == sorted(set(values))


def normalize_command_key(value: str) -> str:
    """Normalize a command name or alias for kind-scoped exact matching."""
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    if normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def _module_closure(registry: Mapping[str, Any], suite_name: str) -> set:
    suite_id = suite_name if suite_name.startswith("suite-") else "suite-" + suite_name
    by_id = {
        item.get("id"): item
        for item in registry.get("modules", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    closure = set()
    frontier = [suite_id]
    while frontier:
        current = frontier.pop()
        if current in closure:
            continue
        closure.add(current)
        module = by_id.get(current)
        if isinstance(module, Mapping):
            frontier.extend(module.get("dependsOn", []))
    return closure


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


def _validate_relative_path(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or ":" in value
        or any(ord(character) < 32 for character in value)
    ):
        raise HelpValidationError("{} must be a portable relative path".format(label))
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or ".." in path.parts
        or "." in path.parts
    ):
        raise HelpValidationError("{} must not escape the repository".format(label))


def _heading_ids(text: str) -> set:
    result = set()
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip().casefold()
        slug = re.sub(r"[^a-z0-9 -]", "", title)
        slug = re.sub(r"[ -]+", "-", slug).strip("-")
        if slug:
            result.add(slug)
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
    if section not in _heading_ids(text):
        raise HelpValidationError(
            "source section {!r} is missing from {}".format(section, source_path)
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


def _bounded_installer_section(
    content: bytes,
    source: str,
    start_marker: str,
    end_marker: str,
) -> List[str]:
    """Return one exact bounded installer declaration section as lines."""
    if len(content) > MAX_INSTALLER_BYTES:
        raise HelpValidationError("{} exceeds the installer byte limit".format(source))
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise HelpValidationError("{} must be UTF-8".format(source)) from error
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise HelpValidationError(
            "{} installer inventory markers must occur exactly once".format(source)
        )
    section = text.split(start_marker, 1)[1].split(end_marker, 1)[0]
    return section.splitlines()


def _block_lines(lines: Sequence[str], start: int, closing: str) -> List[str]:
    for index in range(start + 1, len(lines)):
        if lines[index] == closing:
            return list(lines[start + 1:index])
    raise HelpValidationError("installer declaration block is not closed")


def parse_posix_installer_inventory(content: bytes) -> set:
    """Parse only executable command declarations in the POSIX install section."""
    lines = _bounded_installer_section(
        content,
        "scripts/install.sh",
        POSIX_INSTALL_START,
        POSIX_INSTALL_END,
    )
    commands = set()

    for index, line in enumerate(lines):
        loop = re.fullmatch(r"for cmd in ([a-z0-9 -]+); do", line)
        if loop is None:
            continue
        body = [item.strip() for item in _block_lines(lines, index, "done")]
        if (
            'WRAPPER="$BIN_DIR/cg-$cmd"' in body
            and any(item.startswith('cat > "$WRAPPER" <<') for item in body)
            and 'chmod +x "$WRAPPER"' in body
        ):
            commands.update("cg-" + name for name in loop.group(1).split())

    wrapper_indices = [
        index for index, line in enumerate(lines) if line.startswith("WRAPPER=")
    ]
    for position, index in enumerate(wrapper_indices):
        match = re.fullmatch(r'WRAPPER="\$BIN_DIR/(cg-[a-z0-9-]+)"', lines[index])
        if match is None:
            continue
        end = (
            wrapper_indices[position + 1]
            if position + 1 < len(wrapper_indices)
            else len(lines)
        )
        body = [item.strip() for item in lines[index + 1:end]]
        if (
            any(item.startswith('cat > "$WRAPPER" <<') for item in body)
            and 'chmod +x "$WRAPPER"' in body
        ):
            commands.add(match.group(1))

    for line in lines:
        match = re.fullmatch(
            r'(?P<variable>[A-Z][A-Z0-9_]*_DST)="\$BIN_DIR/(?P<name>cg-[a-z0-9-]+)"',
            line,
        )
        if match is None:
            continue
        variable_chmod = 'chmod +x "${}"'.format(match.group("variable"))
        literal_chmod = 'chmod +x "$BIN_DIR/{}"'.format(match.group("name"))
        if variable_chmod in (item.strip() for item in lines) or literal_chmod in (
            item.strip() for item in lines
        ):
            commands.add(match.group("name"))

    for index, line in enumerate(lines):
        if line != "for spec in \\":
            continue
        specs = []
        body_start = None
        for header_index in range(index + 1, len(lines)):
            declaration = lines[header_index].strip()
            terminal = declaration.endswith("; do")
            suffix = "; do" if terminal else "\\"
            if not declaration.endswith(suffix):
                raise HelpValidationError("POSIX installer summary declaration is malformed")
            quoted = declaration[: -len(suffix)].strip()
            match = re.fullmatch(r'"([a-z0-9-]+)\|[^"|]+\|[^"|]+"', quoted)
            if match is None:
                raise HelpValidationError("POSIX installer summary declaration is malformed")
            specs.append(match.group(1))
            if terminal:
                body_start = header_index
                break
        if body_start is None:
            raise HelpValidationError("POSIX installer summary declaration is not closed")
        body = [item.strip() for item in _block_lines(lines, body_start, "done")]
        if (
            'WRAPPER="$BIN_DIR/cg-$name"' in body
            and any(item.startswith('cat > "$WRAPPER" <<') for item in body)
            and 'chmod +x "$WRAPPER"' in body
        ):
            commands.update("cg-" + name for name in specs)
    return commands


def parse_windows_installer_inventory(content: bytes) -> set:
    """Parse only executable command declarations in the Windows install section."""
    lines = _bounded_installer_section(
        content,
        "install.ps1",
        WINDOWS_INSTALL_START,
        WINDOWS_INSTALL_END,
    )
    commands = set()
    for index, line in enumerate(lines):
        scripts = re.fullmatch(r'\$scripts\s*=\s*@\((?P<items>.*)\)', line)
        if scripts is None:
            continue
        names = re.findall(r'"([a-z0-9-]+)"', scripts.group("items"))
        normalized = re.sub(r'"[a-z0-9-]+"|[\s,]', "", scripts.group("items"))
        if not names or normalized:
            raise HelpValidationError("Windows installer script declaration is malformed")
        loop_index = next(
            (
                candidate
                for candidate in range(index + 1, len(lines))
                if lines[candidate] == "foreach ($script in $scripts) {"
            ),
            None,
        )
        if loop_index is None:
            continue
        body = [item.strip() for item in _block_lines(lines, loop_index, "}")]
        if (
            '$cmdPath = Join-Path $binDir "cg-$script.cmd"' in body
            and any(item.startswith("Set-Content -Path $cmdPath ") for item in body)
        ):
            commands.update("cg-" + name for name in names)

    destination_indices = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(
            r'\$[A-Za-z][A-Za-z0-9]*CmdDst\s*=\s*Join-Path \$binDir "cg-[a-z0-9-]+\.cmd"',
            line,
        )
    ]
    for position, index in enumerate(destination_indices):
        match = re.fullmatch(
            r'\$(?P<variable>[A-Za-z][A-Za-z0-9]*CmdDst)\s*=\s*Join-Path \$binDir "(?P<name>cg-[a-z0-9-]+)\.cmd"',
            lines[index],
        )
        assert match is not None
        end = (
            destination_indices[position + 1]
            if position + 1 < len(destination_indices)
            else len(lines)
        )
        body = "\n".join(lines[index + 1:end])
        source_variable = match.group("variable")[:-3] + "Src"
        if (
            re.search(
                r"^if \(Test-Path \${}\) \{{".format(source_variable),
                body,
                flags=re.MULTILINE,
            )
            and re.search(
                r"^\s*Copy-Item -Path \${} -Destination \${} -Force$".format(
                    source_variable, match.group("variable")
                ),
                body,
                flags=re.MULTILINE,
            )
        ):
            commands.add(match.group("name"))
    return commands


def require_exact_installer_inventory(
    expected: set, observed: set, label: str
) -> None:
    """Require one installer declaration set to match metadata exactly."""
    if expected != observed:
        raise HelpValidationError(
            "{} inventory mismatch: missing={!r}, extra={!r}".format(
                label,
                sorted(expected - observed),
                sorted(observed - expected),
            )
        )


def _validate_module_registry(root: Path, registry: Dict[str, Any]) -> None:
    """Run all layer and ownership checks before extracting help records."""
    import cg_validate_modules as module_validator

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


def validate_source_metadata(
    root: Path,
    *,
    allow_stale_definition_id: Optional[str] = None,
    source_overrides: Optional[Mapping[str, bytes]] = None,
) -> SourceMetadata:
    """Validate exact canonical prompt, shell, registry, and workflow evidence."""
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
    from skill_management.services.registry import matching_asset_owners

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
        if path.name.startswith(("cg-", "cr-")) and path.name != "cg-help.prompt.md"
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
    stale_target_found = False
    for sidecar in sidecars:
        relative = sidecar.relative_to(source_root).as_posix()
        sidecar_bytes = _read_source_bytes(
            source_root, relative, "help sidecar", source_overrides
        )
        command = load_strict_json_bytes(sidecar_bytes, source=relative)
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
        allow_stale = command["id"] == allow_stale_definition_id
        stale_target_found = stale_target_found or allow_stale
        _validate_definition(
            source_root,
            command,
            relative,
            allow_stale=allow_stale,
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
        allow_stale = command["id"] == allow_stale_definition_id
        stale_target_found = stale_target_found or allow_stale
        _validate_definition(
            source_root,
            command,
            label,
            allow_stale=allow_stale,
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
    if allow_stale_definition_id is not None and not stale_target_found:
        raise HelpValidationError(
            "definition record is unknown: {}".format(allow_stale_definition_id)
        )
    return SourceMetadata(
        sidecars,
        tuple(slash_commands),
        tuple(shell_commands),
        tuple(workflows),
        tuple(sorted(source_inputs.items())),
    )


def compute_source_digest(source_inputs: Sequence[Tuple[str, bytes]]) -> str:
    """Hash sorted normalized source identities and their exact accepted bytes."""
    identities = [identity for identity, _content in source_inputs]
    if identities != sorted(set(identities)) or not identities:
        raise HelpValidationError(
            "catalog source identities must be sorted, unique, and non-empty"
        )
    hasher = hashlib.sha256()
    for identity, content in source_inputs:
        path_identity, separator, fragment = identity.partition("#")
        _validate_relative_path(path_identity, "catalog source identity")
        if separator and (not fragment or "#" in fragment):
            raise HelpValidationError("catalog source fragment is invalid")
        if not isinstance(content, bytes):
            raise HelpValidationError("catalog source content must be exact bytes")
        hasher.update(identity.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(content)
        hasher.update(b"\0")
    return hasher.hexdigest()


def _catalog_suites(registry: Mapping[str, Any]) -> List[Dict[str, Any]]:
    suites: List[Dict[str, Any]] = []
    for module in registry.get("modules", []):
        if not isinstance(module, dict) or module.get("layer") != "suite":
            continue
        help_metadata = module.get("help")
        if not isinstance(help_metadata, dict):
            continue
        suite_id = help_metadata.get("suiteId")
        activation = help_metadata.get("activation")
        if not isinstance(suite_id, str) or not isinstance(activation, dict):
            raise HelpValidationError(
                "suite module {} has incomplete help evidence".format(module.get("id"))
            )
        suites.append(
            {
                "id": suite_id,
                "moduleId": module["id"],
                "displayName": module["displayName"],
                "activation": dict(activation),
            }
        )
    return sorted(suites, key=lambda item: item["id"])


def merge_catalog(
    registry: Mapping[str, Any], source: SourceMetadata
) -> Dict[str, Any]:
    """Normalize and merge a fully validated source graph into one catalog."""
    value = {
        "schemaVersion": CATALOG_SCHEMA_VERSION,
        "generatorVersion": GENERATOR_VERSION,
        "sourceDigest": compute_source_digest(source.source_inputs),
        "suites": _catalog_suites(registry),
        "commands": sorted(
            list(source.slash_commands) + list(source.shell_commands),
            key=lambda item: item["id"],
        ),
        "workflows": sorted(source.workflows, key=lambda item: item["id"]),
    }
    validate_catalog(value, registry)
    return value


def serialize_catalog(value: Mapping[str, Any]) -> bytes:
    """Serialize validated catalog data as stable UTF-8 JSON bytes."""
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def generate_catalog_bytes(root: Path) -> bytes:
    """Validate the complete source graph and return deterministic catalog bytes."""
    source_root = Path(root).resolve()
    source = validate_source_metadata(source_root)
    registry = load_strict_json_bytes(
        dict(source.source_inputs)[MODULE_REGISTRY_PATH], source=MODULE_REGISTRY_PATH
    )
    return serialize_catalog(merge_catalog(registry, source))


def _catalog_output_path(root: Path) -> Path:
    source_root = Path(root).resolve()
    return source_root.joinpath(*PurePosixPath(CATALOG_OUTPUT_PATH).parts)


def _atomic_replace(path: Path, content: bytes) -> None:
    """Replace one regular file atomically after all content validation succeeds."""
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise HelpCatalogIOError("refusing to replace non-regular output: {}".format(path))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=".{}.".format(path.name),
            suffix=".tmp",
        )
    except OSError as error:
        raise HelpCatalogIOError("cannot create atomic output: {}".format(error)) from error
    temporary_path = Path(temporary_name)
    operation_error: Optional[OSError] = None
    cleanup_error: Optional[OSError] = None
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary_path), str(path))
    except OSError as error:
        operation_error = error
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError as error:
                cleanup_error = error
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        except OSError as error:
            cleanup_error = error
    if operation_error is not None:
        detail = "{}; temporary cleanup failed: {}".format(
            operation_error, cleanup_error
        ) if cleanup_error is not None else str(operation_error)
        raise HelpCatalogIOError("cannot replace {}: {}".format(path, detail)) from operation_error
    if cleanup_error is not None:
        raise HelpCatalogIOError(
            "cannot clean temporary output for {}: {}".format(path, cleanup_error)
        ) from cleanup_error


def write_catalog(root: Path) -> bool:
    """Atomically write the catalog after complete source and output validation."""
    expected = generate_catalog_bytes(root)
    output = _catalog_output_path(root)
    try:
        if output.is_file() and not output.is_symlink() and output.read_bytes() == expected:
            return False
    except OSError as error:
        raise HelpCatalogIOError("cannot read existing catalog: {}".format(error)) from error
    _atomic_replace(output, expected)
    return True


def check_catalog(root: Path) -> None:
    """Fail without mutation when the emitted catalog is missing or stale."""
    expected = generate_catalog_bytes(root)
    output = _catalog_output_path(root)
    if not output.exists():
        raise HelpCatalogStaleError(
            "help catalog is missing; run --write after all definition digests pass"
        )
    if output.is_symlink() or not output.is_file():
        raise HelpCatalogStaleError("help catalog output is not a regular file")
    try:
        observed = output.read_bytes()
    except OSError as error:
        raise HelpCatalogIOError("cannot read help catalog: {}".format(error)) from error
    if observed != expected:
        raise HelpCatalogStaleError(
            "help catalog is stale or unexpected; run --write after review"
        )


def _definition_record(
    root: Path, command_id: str
) -> Tuple[Dict[str, Any], str, str, SourceMetadata]:
    if not QUALIFIED_ID_PATTERN.fullmatch(command_id):
        raise HelpValidationError("definition record id must be kind-qualified")
    source = validate_source_metadata(
        root, allow_stale_definition_id=command_id
    )
    matches = [
        item
        for item in source.slash_commands + source.shell_commands
        if item["id"] == command_id
    ]
    if len(matches) != 1:
        raise HelpValidationError("definition record must resolve exactly once")
    command = matches[0]
    metadata_path = (
        ".github/prompts/{}.help.json".format(command_id.split(":", 1)[1])
        if command["kind"] == "slash"
        else SHELL_METADATA_PATH
    )
    computed = compute_definition_digest(
        root,
        command["definitionSources"],
        source_overrides=dict(source.source_inputs),
    )
    return command, metadata_path, computed, source


def preview_definition_digest(root: Path, command_id: str) -> Dict[str, Any]:
    """Preview one pinned digest without changing metadata or catalog bytes."""
    command, metadata_path, computed, _source = _definition_record(root, command_id)
    current = command["definitionDigest"]
    return {
        "id": command_id,
        "metadataPath": metadata_path,
        "currentDefinitionDigest": current,
        "computedDefinitionDigest": computed,
        "stale": current != computed,
    }


def repin_definition_digest(root: Path, command_id: str) -> Dict[str, Any]:
    """Atomically refresh only one reviewed record's pinned definition digest."""
    command, metadata_path, computed, source = _definition_record(root, command_id)
    preview = {
        "id": command_id,
        "metadataPath": metadata_path,
        "currentDefinitionDigest": command["definitionDigest"],
        "computedDefinitionDigest": computed,
        "stale": command["definitionDigest"] != computed,
    }
    previous = preview["currentDefinitionDigest"]
    result = dict(preview)
    result["changed"] = previous != computed
    if previous == computed:
        return result
    path = _source_path(root, metadata_path, "definition metadata")
    source_graph = dict(source.source_inputs)
    content = source_graph.get(metadata_path)
    if content is None:
        raise HelpValidationError(
            "definition metadata is absent from the captured source graph"
        )
    pattern = re.compile(
        rb'("definitionDigest"\s*:\s*")' + previous.encode("ascii") + rb'(")'
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise HelpValidationError(
            "target definitionDigest must occur exactly once in {}".format(metadata_path)
        )
    match = matches[0]
    start = match.start() + len(match.group(1))
    updated = content[:start] + computed.encode("ascii") + content[start + 64 :]
    prospective = validate_source_metadata(
        root, source_overrides={metadata_path: updated}
    )
    source_graph[metadata_path] = updated
    if prospective.source_inputs != tuple(sorted(source_graph.items())):
        raise HelpValidationError(
            "catalog source graph changed during definition repin validation"
        )
    if _read_source_bytes(root, metadata_path, "definition metadata") != content:
        raise HelpValidationError(
            "definition metadata changed during repin validation"
        )
    _atomic_replace(path, updated)
    result.update(
        {
            "previousDefinitionDigest": previous,
            "currentDefinitionDigest": computed,
            "stale": False,
        }
    )
    return result
