"""Closed schema-subset validation and common skill-management contracts."""
from __future__ import annotations

import json
import math
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import secure_fs

from skill_management import paths as path_policy


SCHEMA_DIALECT = "compound-gpid-schema-subset-v1"
ALLOWED_SCHEMA_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$ref",
        "$defs",
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "const",
        "pattern",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "uniqueItems",
    }
)
JSON_TYPES = (
    "array",
    "boolean",
    "integer",
    "null",
    "number",
    "object",
    "string",
)
CONTEXT_ROLES = ("consumer", "maintainer")
RESULT_ROLES = CONTEXT_ROLES + ("automation",)
ROLES = CONTEXT_ROLES
PHASES = ("read", "plan", "apply")
FINDING_SEVERITIES = ("error", "warning", "info")
MANIFEST_HEALTH_STATES = ("fresh", "missing", "stale", "invalid")
ORIGIN_STATES = ("plugin-canonical", "project-imported")
ADMISSION_STATES = ("quarantined", "approved", "rejected")
LIFECYCLE_STATES = ("current", "deprecated", "removed")
AVAILABILITY_STATES = ("inactive", "active")
ACTION_KINDS = (
    "create-directory",
    "write-file",
    "delete-file",
    "update-registry",
    "update-config",
    "update-manifest",
    "generate-targets",
    "publish-projection",
    "apply-migration",
    "write-tombstone",
    "verify",
)

EXIT_SUCCESS = 0
EXIT_INTERNAL = 1
EXIT_USAGE = 2
EXIT_CONTRACT = 3
EXIT_ROLE_CONTEXT = 4
EXIT_SECURITY = 5
EXIT_LIFECYCLE_CONFLICT = 6
EXIT_STALE_PLAN = 7
EXIT_VERIFICATION = 8
EXIT_CODES = {
    "success": EXIT_SUCCESS,
    "internal": EXIT_INTERNAL,
    "usage": EXIT_USAGE,
    "contract": EXIT_CONTRACT,
    "role-context": EXIT_ROLE_CONTEXT,
    "security": EXIT_SECURITY,
    "lifecycle-conflict": EXIT_LIFECYCLE_CONFLICT,
    "stale-plan": EXIT_STALE_PLAN,
    "verification": EXIT_VERIFICATION,
}

MAX_CONTRACT_BYTES = 1024 * 1024
MAX_VALIDATION_DEPTH = 64
MAX_VALIDATION_NODES = 10000
MAX_VALIDATION_FINDINGS = 1000
MAX_VALUE_STRING_LENGTH = 1024 * 1024
MAX_VALUE_ARRAY_ITEMS = 10000
MAX_PATTERN_LENGTH = 512
_REPARSE_POINT_FLAG = 0x400
OPERATIONS_ROOT = PurePosixPath(".github/shared/skill-management/operations")
CONTRACTS_ROOT = PurePosixPath(".github/shared/skill-management/contracts")
OPERATION_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def operation_handler_module(operation: str, handler: str) -> str:
    """Validate and return one descriptor-bound focused handler module.

    The regular module is the operation identifier with underscores. A
    ``_skill`` suffix is also permitted for Python-keyword operation names such
    as ``import``. No descriptor can select another operation or package.
    """
    base = operation.replace("-", "_")
    match = re.fullmatch(
        r"skill_management\.operations\.([a-z][a-z0-9_]*):handle",
        handler,
    )
    if match is None or match.group(1) not in {base, f"{base}_skill"}:
        raise ValueError("Operation descriptor handler does not match its operation identity.")
    return match.group(1)


@dataclass(frozen=True, order=True)
class ContractFinding:
    """One deterministic contract or schema validation finding."""

    path: str
    code: str
    severity: str
    message: str
    remediation: str

    def to_dict(self) -> Dict[str, str]:
        """Return the stable public finding representation."""
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class OperationDescriptor:
    """One complete validated operation descriptor and operation contract."""

    operation: str
    descriptor: Mapping[str, Any]
    contract: Mapping[str, Any]


class DescriptorValidationError(ValueError):
    """Raised when an operation descriptor is invalid or incomplete."""

    def __init__(self, code: str, path: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.path = path


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _finding(
    path: str,
    code: str,
    message: str,
    remediation: str,
    severity: str = "error",
) -> ContractFinding:
    return ContractFinding(path, code, severity, message, remediation)


def _sorted(findings: Iterable[ContractFinding]) -> Tuple[ContractFinding, ...]:
    return tuple(sorted(findings, key=lambda item: (item.path, item.code)))


def sort_findings(findings: Iterable[ContractFinding]) -> Tuple[ContractFinding, ...]:
    """Sort common result findings by severity, path, and stable code."""
    severity_order = {"error": 0, "warning": 1, "info": 2}
    return tuple(
        sorted(
            findings,
            key=lambda item: (
                severity_order.get(item.severity, len(severity_order)),
                item.path,
                item.code,
            ),
        )
    )


def _pointer(path: str, token: object) -> str:
    value = str(token).replace("~", "~0").replace("/", "~1")
    return f"{path}/{value}" if path else f"/{value}"


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize one JSON value to deterministic UTF-8 bytes."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"JSON number must be finite: {value}")


def _reject_duplicate_members(pairs: Sequence[Tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON object contains duplicate member: {key!r}")
        result[key] = value
    return result


def _strict_json_loads(content: str) -> Any:
    return json.loads(
        content,
        object_pairs_hook=_reject_duplicate_members,
        parse_constant=_reject_json_constant,
    )


def load_contract(path: Path) -> dict:
    """Load one bounded regular JSON contract without following its leaf."""
    contract_path = Path(path)
    metadata = os.lstat(str(contract_path))
    if stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    ):
        raise ValueError(f"Contract path is a link or reparse point: {contract_path}")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Contract path is not a regular file: {contract_path}")
    if metadata.st_size > MAX_CONTRACT_BYTES:
        raise ValueError(f"Contract exceeds {MAX_CONTRACT_BYTES} bytes: {contract_path}")
    try:
        return load_contract_bytes(contract_path.read_bytes(), source=str(contract_path))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Contract is not valid UTF-8 JSON: {contract_path}") from error


def load_contract_bytes(content: bytes, *, source: str = "<contract>") -> dict:
    """Load strict UTF-8 JSON contract bytes."""
    if len(content) > MAX_CONTRACT_BYTES:
        raise ValueError(f"Contract exceeds {MAX_CONTRACT_BYTES} bytes: {source}")
    try:
        value = _strict_json_loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Contract is not valid UTF-8 JSON: {source}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Contract root must be an object: {source}")
    json_findings = _json_value_findings(value)
    if json_findings:
        details = "; ".join(
            f"{finding.path}: {finding.code}" for finding in json_findings
        )
        raise ValueError(f"Contract contains invalid JSON scalar data: {details}")
    return value


def _json_identity(value: Any) -> bytes:
    try:
        return canonical_json_bytes(value)
    except (TypeError, ValueError):
        return repr((type(value).__name__, value)).encode("utf-8", errors="replace")


def _resolve_local_reference(root: Mapping[str, Any], reference: str) -> Any:
    if reference == "#":
        return root
    if not reference.startswith("#/"):
        raise ValueError("reference is not a local JSON pointer")
    current: Any = root
    for raw_token in reference[2:].split("/"):
        if re.search(r"~(?![01])", raw_token):
            raise ValueError("reference contains an invalid JSON Pointer escape")
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise KeyError(token)
        current = current[token]
    return current


def _unsafe_pattern_reason(pattern: str) -> Optional[str]:
    if len(pattern) > MAX_PATTERN_LENGTH:
        return f"pattern exceeds {MAX_PATTERN_LENGTH} characters"
    if re.search(r"\\[1-9]", pattern):
        return "backreferences are not supported"
    if any(token in pattern for token in ("(?=", "(?!", "(?<=", "(?<!", "(?P")):
        return "lookarounds and named groups are not supported"
    for match in re.finditer(r"\((?:\?:)?([^)]*)\)([+*]|\{)", pattern):
        content = match.group(1)
        if "|" in content:
            return "repeated alternation groups are not supported"
        if re.search(r"[+*]|\{[0-9]+,?", content) and re.match(
            r"^\[[^]]+\]", content
        ) is None:
            return "nested quantified groups are not supported"
    return None


def _reference_chain_error(root: Mapping[str, Any], reference: str) -> Optional[str]:
    seen = set()  # type: set[str]
    current = reference
    for _ in range(MAX_VALIDATION_DEPTH + 1):
        if current in seen:
            return "cycle"
        seen.add(current)
        if current.endswith("/$defs") or current.endswith("/properties"):
            return "container"
        try:
            target = _resolve_local_reference(root, current)
        except (KeyError, ValueError):
            return None
        if not isinstance(target, dict):
            return None
        next_reference = target.get("$ref")
        if not isinstance(next_reference, str):
            return None
        current = next_reference
    return "depth"


def validate_schema_definition(schema: Any) -> Tuple[ContractFinding, ...]:
    """Validate a schema against the closed Compound GPID subset."""
    findings = []  # type: list[ContractFinding]
    if not isinstance(schema, dict):
        return (
            _finding(
                "",
                "schema.type",
                "A schema must be a JSON object.",
                "Use an object containing $schema and $id.",
            ),
        )

    node_count = [0]

    def walk(
        node: Any,
        path: str,
        *,
        root_node: bool = False,
        depth: int = 0,
    ) -> None:
        if len(findings) >= MAX_VALIDATION_FINDINGS:
            return
        node_count[0] += 1
        if depth > MAX_VALIDATION_DEPTH or node_count[0] > MAX_VALIDATION_NODES:
            findings.append(
                _finding(
                    path,
                    "schema.validation-budget",
                    "Schema exceeds the validation depth or node budget.",
                    "Reduce schema nesting or node count.",
                )
            )
            return
        if not isinstance(node, dict):
            findings.append(
                _finding(
                    path,
                    "schema.type",
                    "A schema node must be an object.",
                    "Replace the value with a schema object.",
                )
            )
            return
        for keyword in sorted(node):
            if keyword not in ALLOWED_SCHEMA_KEYWORDS:
                findings.append(
                    _finding(
                        _pointer(path, keyword),
                        "schema.unsupported-keyword",
                        f"Schema keyword {keyword!r} is not in {SCHEMA_DIALECT}.",
                        "Remove the keyword or express the rule with the declared subset.",
                    )
                )

        if root_node:
            if node.get("$schema") != SCHEMA_DIALECT:
                findings.append(
                    _finding(
                        "/$schema",
                        "schema.dialect",
                        f"The root $schema must be {SCHEMA_DIALECT!r}.",
                        f"Set $schema to {SCHEMA_DIALECT!r}.",
                    )
                )
            if not isinstance(node.get("$id"), str) or not node.get("$id"):
                findings.append(
                    _finding(
                        "/$id",
                        "schema.id",
                        "The root schema requires a non-empty $id.",
                        "Add a stable versioned $id.",
                    )
                )

        reference = node.get("$ref")
        if "$ref" in node:
            reference_path = _pointer(path, "$ref")
            if not isinstance(reference, str) or not reference.startswith("#"):
                findings.append(
                    _finding(
                        reference_path,
                        "schema.nonlocal-reference",
                        "Only local JSON-pointer references are supported.",
                        "Replace the reference with # or a #/... pointer.",
                    )
                )
            else:
                try:
                    target = _resolve_local_reference(schema, reference)
                except (KeyError, ValueError):
                    findings.append(
                        _finding(
                            reference_path,
                            "schema.unresolved-reference",
                            f"Local reference {reference!r} does not resolve.",
                            "Point $ref to an existing local $defs schema.",
                        )
                    )
                else:
                    if not isinstance(target, dict):
                        findings.append(
                            _finding(
                                reference_path,
                                "schema.reference-type",
                                "A local reference must resolve to a schema object.",
                                "Point $ref to an object-valued schema node.",
                            )
                        )
                    else:
                        chain_error = _reference_chain_error(schema, reference)
                        if chain_error == "cycle":
                            findings.append(
                                _finding(
                                    reference_path,
                                    "schema.reference-cycle",
                                    "Local reference chain contains a cycle.",
                                    "Replace the cycle with an acyclic local schema reference.",
                                )
                            )
                        elif chain_error == "container":
                            findings.append(
                                _finding(
                                    reference_path,
                                    "schema.reference-container",
                                    "Local reference resolves to a schema container, not a schema node.",
                                    "Point $ref to one schema below $defs or properties.",
                                )
                            )
                        elif chain_error == "depth":
                            findings.append(
                                _finding(
                                    reference_path,
                                    "schema.validation-budget",
                                    "Local reference chain exceeds the hop budget.",
                                    "Shorten the local reference chain.",
                                )
                            )

        type_value = node.get("type")
        if "type" in node and type_value not in JSON_TYPES:
            findings.append(
                _finding(
                    _pointer(path, "type"),
                    "schema.type-value",
                    f"Schema type must be one of {list(JSON_TYPES)!r}.",
                    "Use one supported JSON type string.",
                )
            )

        keyword_types = {
            "properties": "object",
            "required": "object",
            "additionalProperties": "object",
            "items": "array",
            "minItems": "array",
            "maxItems": "array",
            "uniqueItems": "array",
            "pattern": "string",
            "minLength": "string",
            "maxLength": "string",
            "minimum": ("integer", "number"),
            "maximum": ("integer", "number"),
        }
        if isinstance(type_value, str):
            for keyword, expected in keyword_types.items():
                expected_types = (expected,) if isinstance(expected, str) else expected
                if keyword in node and type_value not in expected_types:
                    findings.append(
                        _finding(
                            _pointer(path, keyword),
                            "schema.keyword-type",
                            f"{keyword} is not applicable to schema type {type_value!r}.",
                            f"Remove {keyword} or use an applicable schema type.",
                        )
                    )

        for container_name in ("properties", "$defs"):
            if container_name not in node:
                continue
            container = node[container_name]
            container_path = _pointer(path, container_name)
            if not isinstance(container, dict):
                findings.append(
                    _finding(
                        container_path,
                        "schema.mapping",
                        f"{container_name} must be an object.",
                        f"Replace {container_name} with an object of schema nodes.",
                    )
                )
                continue
            for name in sorted(container):
                walk(container[name], _pointer(container_path, name), depth=depth + 1)

        if "required" in node:
            required = node["required"]
            valid_required = isinstance(required, list) and all(
                isinstance(item, str) and item for item in required
            )
            if not valid_required or (
                isinstance(required, list) and len(set(required)) != len(required)
            ):
                findings.append(
                    _finding(
                        _pointer(path, "required"),
                        "schema.required-value",
                        "required must be an array of unique non-empty strings.",
                        "List each required property name once.",
                    )
                )

        additional = node.get("additionalProperties")
        if "additionalProperties" in node:
            if isinstance(additional, dict):
                walk(additional, _pointer(path, "additionalProperties"), depth=depth + 1)
            elif not isinstance(additional, bool):
                findings.append(
                    _finding(
                        _pointer(path, "additionalProperties"),
                        "schema.additional-properties-value",
                        "additionalProperties must be a boolean or schema object.",
                        "Use true, false, or a schema object.",
                    )
                )

        if "items" in node:
            walk(node["items"], _pointer(path, "items"), depth=depth + 1)

        if "enum" in node:
            enum = node["enum"]
            identities = [_json_identity(item) for item in enum] if isinstance(enum, list) else []
            if not isinstance(enum, list) or not enum or len(set(identities)) != len(identities):
                findings.append(
                    _finding(
                        _pointer(path, "enum"),
                        "schema.enum-value",
                        "enum must be a non-empty array of unique JSON values.",
                        "List each accepted JSON value once.",
                    )
                )

        if "pattern" in node:
            pattern = node["pattern"]
            try:
                if not isinstance(pattern, str):
                    raise TypeError
                re.compile(pattern)
            except (TypeError, re.error):
                findings.append(
                    _finding(
                        _pointer(path, "pattern"),
                        "schema.pattern-value",
                        "pattern must be a valid regular expression string.",
                        "Use a Python-compatible regular expression.",
                    )
                )
            else:
                unsafe_reason = _unsafe_pattern_reason(pattern)
                if unsafe_reason is not None:
                    findings.append(
                        _finding(
                            _pointer(path, "pattern"),
                            "schema.unsafe-pattern",
                            f"Pattern is outside the safe subset: {unsafe_reason}.",
                            "Use a bounded pattern without backreferences, lookarounds, or nested quantifiers.",
                        )
                    )

        for keyword in ("minLength", "maxLength", "minItems", "maxItems"):
            if keyword in node and (
                type(node[keyword]) is not int or node[keyword] < 0
            ):
                findings.append(
                    _finding(
                        _pointer(path, keyword),
                        "schema.nonnegative-integer",
                        f"{keyword} must be a non-negative integer.",
                        f"Set {keyword} to zero or a positive integer.",
                    )
                )
        for keyword in ("minimum", "maximum"):
            value = node.get(keyword)
            if keyword in node and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                findings.append(
                    _finding(
                        _pointer(path, keyword),
                        "schema.number-value",
                        f"{keyword} must be a finite number.",
                        f"Set {keyword} to a finite JSON number.",
                    )
                )
        if "uniqueItems" in node and not isinstance(node["uniqueItems"], bool):
            findings.append(
                _finding(
                    _pointer(path, "uniqueItems"),
                    "schema.boolean-value",
                    "uniqueItems must be a boolean.",
                    "Set uniqueItems to true or false.",
                )
            )
        if (
            isinstance(node.get("minLength"), int)
            and isinstance(node.get("maxLength"), int)
            and node["minLength"] > node["maxLength"]
        ) or (
            isinstance(node.get("minItems"), int)
            and isinstance(node.get("maxItems"), int)
            and node["minItems"] > node["maxItems"]
        ) or (
            isinstance(node.get("minimum"), (int, float))
            and not isinstance(node.get("minimum"), bool)
            and isinstance(node.get("maximum"), (int, float))
            and not isinstance(node.get("maximum"), bool)
            and node["minimum"] > node["maximum"]
        ):
            findings.append(
                _finding(
                    path,
                    "schema.invalid-range",
                    "A minimum constraint is greater than its maximum.",
                    "Make each minimum less than or equal to its maximum.",
                )
            )

    walk(schema, "", root_node=True)
    return _sorted(findings)


def _matches_type(value: Any, type_name: str) -> bool:
    if type_name == "null":
        return value is None
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return type(value) is int
    if type_name == "number":
        return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "object":
        return isinstance(value, dict)
    return False


def _valid_unicode_scalar(value: str) -> bool:
    return not any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def _json_value_findings(value: Any) -> Tuple[ContractFinding, ...]:
    findings = []  # type: list[ContractFinding]
    stack = [(value, "", 0, frozenset())]
    nodes = 0
    while stack and len(findings) < MAX_VALIDATION_FINDINGS:
        current, path, depth, ancestors = stack.pop()
        nodes += 1
        if depth > MAX_VALIDATION_DEPTH or nodes > MAX_VALIDATION_NODES:
            findings.append(
                _finding(
                    path,
                    "contract.json-budget",
                    "JSON value exceeds the validation depth or node budget.",
                    "Reduce input nesting or node count.",
                )
            )
            break
        if current is None or isinstance(current, bool) or type(current) is int:
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                findings.append(
                    _finding(
                        path,
                        "contract.json-number",
                        "JSON numbers must be finite.",
                        "Replace NaN or infinity with a finite number.",
                    )
                )
            continue
        if isinstance(current, str):
            if len(current) > MAX_VALUE_STRING_LENGTH:
                findings.append(
                    _finding(
                        path,
                        "contract.json-string-budget",
                        "JSON string exceeds the validation length budget.",
                        "Provide a shorter string.",
                    )
                )
            elif not _valid_unicode_scalar(current):
                findings.append(
                    _finding(
                        path,
                        "contract.json-unicode",
                        "JSON string contains an invalid Unicode surrogate.",
                        "Use valid Unicode scalar values.",
                    )
                )
            continue
        if isinstance(current, list):
            identity = id(current)
            if identity in ancestors:
                findings.append(
                    _finding(
                        path,
                        "contract.json-cycle",
                        "JSON arrays and objects must not contain cycles.",
                        "Replace the cycle with an acyclic JSON value.",
                    )
                )
                continue
            if len(current) > MAX_VALUE_ARRAY_ITEMS:
                findings.append(
                    _finding(
                        path,
                        "contract.json-array-budget",
                        "JSON array exceeds the item budget.",
                        "Reduce the array item count.",
                    )
                )
                continue
            next_ancestors = ancestors | {identity}
            for index in range(len(current) - 1, -1, -1):
                stack.append((current[index], _pointer(path, index), depth + 1, next_ancestors))
            continue
        if isinstance(current, dict):
            identity = id(current)
            if identity in ancestors:
                findings.append(
                    _finding(
                        path,
                        "contract.json-cycle",
                        "JSON arrays and objects must not contain cycles.",
                        "Replace the cycle with an acyclic JSON value.",
                    )
                )
                continue
            invalid_keys = [key for key in current if not isinstance(key, str)]
            for key in invalid_keys:
                findings.append(
                    _finding(
                        path,
                        "contract.json-key",
                        f"JSON object key must be a string, not {type(key).__name__}.",
                        "Use string keys for every JSON object.",
                    )
                )
            next_ancestors = ancestors | {identity}
            for key in sorted(
                (key for key in current if isinstance(key, str)),
                reverse=True,
            ):
                stack.append((current[key], _pointer(path, key), depth + 1, next_ancestors))
            continue
        findings.append(
            _finding(
                path,
                "contract.json-type",
                f"Value of type {type(current).__name__} is not JSON.",
                "Use null, boolean, finite number, string, array, or object.",
            )
        )
    return _sorted(findings)


def validate_instance(instance: Any, schema: Mapping[str, Any]) -> Tuple[ContractFinding, ...]:
    """Validate one JSON-compatible value against a valid subset schema."""
    schema_findings = validate_schema_definition(schema)
    if schema_findings:
        return schema_findings
    json_findings = _json_value_findings(instance)
    if json_findings:
        return json_findings
    findings = []  # type: list[ContractFinding]
    active_pairs = set()  # type: set[Tuple[int, int]]
    node_count = [0]

    def walk(value: Any, node: Mapping[str, Any], path: str, depth: int = 0) -> None:
        if len(findings) >= MAX_VALIDATION_FINDINGS:
            return
        node_count[0] += 1
        if depth > MAX_VALIDATION_DEPTH or node_count[0] > MAX_VALIDATION_NODES:
            findings.append(
                _finding(
                    path,
                    "contract.validation-budget",
                    "Instance validation exceeds the depth or node budget.",
                    "Reduce input nesting or node count.",
                )
            )
            return
        pair = (id(value), id(node))
        if pair in active_pairs:
            return
        active_pairs.add(pair)
        try:
            reference = node.get("$ref")
            if isinstance(reference, str):
                target = _resolve_local_reference(schema, reference)
                walk(value, target, path, depth + 1)

            expected_type = node.get("type")
            if isinstance(expected_type, str) and not _matches_type(value, expected_type):
                findings.append(
                    _finding(
                        path,
                        "contract.type",
                        f"Expected JSON type {expected_type}.",
                        f"Provide a {expected_type} value at this path.",
                    )
                )
                return

            if "enum" in node and not any(
                _json_identity(value) == _json_identity(candidate)
                for candidate in node["enum"]
            ):
                findings.append(
                    _finding(
                        path,
                        "contract.enum",
                        f"Value is not one of {node['enum']!r}.",
                        "Use one of the declared enum values.",
                    )
                )
            if "const" in node and _json_identity(value) != _json_identity(node["const"]):
                findings.append(
                    _finding(
                        path,
                        "contract.const",
                        f"Value must equal {node['const']!r}.",
                        "Use the declared constant value.",
                    )
                )

            if isinstance(value, dict):
                properties = node.get("properties", {})
                required = node.get("required", [])
                for name in sorted(required):
                    if name not in value:
                        findings.append(
                            _finding(
                                _pointer(path, name),
                                "contract.required",
                                f"Required property {name!r} is missing.",
                                f"Add property {name!r}.",
                            )
                        )
                additional = node.get("additionalProperties", True)
                for name in sorted(value):
                    child_path = _pointer(path, name)
                    if name in properties:
                        walk(value[name], properties[name], child_path, depth + 1)
                    elif additional is False:
                        findings.append(
                            _finding(
                                child_path,
                                "contract.additional-property",
                                f"Property {name!r} is not allowed.",
                                "Remove the unknown property.",
                            )
                        )
                    elif isinstance(additional, dict):
                        walk(value[name], additional, child_path, depth + 1)

            if isinstance(value, list):
                if "minItems" in node and len(value) < node["minItems"]:
                    findings.append(
                        _finding(path, "contract.min-items", "Array has too few items.", "Add the required items.")
                    )
                if "maxItems" in node and len(value) > node["maxItems"]:
                    findings.append(
                        _finding(path, "contract.max-items", "Array has too many items.", "Remove excess items.")
                    )
                if node.get("uniqueItems") is True:
                    identities = [_json_identity(item) for item in value]
                    if len(set(identities)) != len(identities):
                        findings.append(
                            _finding(path, "contract.unique-items", "Array items must be unique.", "Remove duplicate items.")
                        )
                item_schema = node.get("items")
                if isinstance(item_schema, dict):
                    for index, item in enumerate(value):
                        walk(item, item_schema, _pointer(path, index), depth + 1)

            if isinstance(value, str):
                if "minLength" in node and len(value) < node["minLength"]:
                    findings.append(
                        _finding(path, "contract.min-length", "String is too short.", "Provide a longer string.")
                    )
                if "maxLength" in node and len(value) > node["maxLength"]:
                    findings.append(
                        _finding(path, "contract.max-length", "String is too long.", "Provide a shorter string.")
                    )
                pattern = node.get("pattern")
                anchored = (
                    isinstance(pattern, str)
                    and pattern.startswith("^")
                    and pattern.endswith("$")
                )
                matches = (
                    re.fullmatch(pattern, value) if anchored else re.search(pattern, value)
                ) if isinstance(pattern, str) else True
                if isinstance(pattern, str) and matches is None:
                    findings.append(
                        _finding(path, "contract.pattern", "String does not match the required pattern.", "Use the documented string format.")
                    )

            if not isinstance(value, bool) and isinstance(value, (int, float)):
                if "minimum" in node and value < node["minimum"]:
                    findings.append(
                        _finding(path, "contract.minimum", "Number is below the minimum.", "Increase the number to the declared minimum.")
                    )
                if "maximum" in node and value > node["maximum"]:
                    findings.append(
                        _finding(path, "contract.maximum", "Number is above the maximum.", "Reduce the number to the declared maximum.")
                    )
        finally:
            active_pairs.remove(pair)

    walk(instance, schema, "")
    schema_id = schema.get("$id")
    if schema_id == SCHEMA_DIALECT and isinstance(instance, dict):
        findings.extend(validate_schema_definition(instance))
    if schema_id == "cg-skill-result-v1" and isinstance(instance, dict):
        findings.extend(_result_invariants(instance))
        findings.extend(_action_path_invariants(instance.get("actions"), "/actions"))
    if schema_id == "cg-skill-plan-v1" and isinstance(instance, dict):
        findings.extend(_action_path_invariants(instance.get("actions"), "/actions"))
        findings.extend(_plan_invariants(instance))
    if schema_id == "cg-project-skill-registry-v1" and isinstance(instance, dict):
        findings.extend(_project_registry_invariants(instance))
    if schema_id == "cg-skill-provenance-v1" and isinstance(instance, dict):
        findings.extend(_provenance_invariants(instance))
        source = instance.get("source")
        if isinstance(source, dict):
            findings.extend(_portable_path_findings(source.get("path"), "/source/path"))
    if schema_id == "cg-skill-release-attestation-v1" and isinstance(instance, dict):
        findings.extend(_attestation_invariants(instance))
    return _sorted(findings)


def _result_invariants(result: Mapping[str, Any]) -> Sequence[ContractFinding]:
    findings = []  # type: list[ContractFinding]
    ok = result.get("ok")
    exit_code = result.get("exitCode")
    if (ok is True and exit_code != EXIT_SUCCESS) or (
        ok is False and exit_code == EXIT_SUCCESS
    ):
        findings.append(
            _finding(
                "/exitCode",
                "contract.result-exit-code",
                "Result ok and exitCode values disagree.",
                "Use exit code 0 only for an ok result.",
            )
        )
    result_findings = result.get("findings")
    has_error = isinstance(result_findings, list) and any(
        isinstance(item, dict) and item.get("severity") == "error"
        for item in result_findings
    )
    if has_error and (ok is True or exit_code == EXIT_SUCCESS):
        findings.append(
            _finding(
                "/findings",
                "contract.result-error-success",
                "A result with an error finding cannot report success.",
                "Use a nonzero exit code and ok=false when error findings exist.",
            )
        )
    return findings


def _portable_path_findings(value: Any, path: str) -> Sequence[ContractFinding]:
    if not isinstance(value, str):
        return ()
    parts = value.replace("\\", "/").split("/")
    unsafe = (
        not value
        or "\\" in value
        or "\x00" in value
        or value.startswith(("/", "//", "\\\\"))
        or re.match(r"^[A-Za-z]:", value) is not None
        or any(part in ("", ".", "..") for part in parts)
    )
    for part in parts:
        portable = unicodedata.normalize("NFC", part).casefold().rstrip(". ")
        if (
            any(ord(character) < 32 or character in '<>:"|?*' for character in part)
            or part.endswith((".", " "))
            or portable.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES
        ):
            unsafe = True
    if not unsafe:
        return ()
    return (
        _finding(
            path,
            "contract.unsafe-path",
            "Path must be a portable repository-relative path.",
            "Remove absolute, traversal, reserved, control, or forbidden path components.",
        ),
    )


def _action_path_invariants(actions: Any, path: str) -> Sequence[ContractFinding]:
    findings = []  # type: list[ContractFinding]
    seen = {}  # type: Dict[Tuple[str, ...], str]
    if not isinstance(actions, list):
        return findings
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        value = action.get("path")
        item_path = f"{path}/{index}/path"
        findings.extend(_portable_path_findings(value, item_path))
        if isinstance(value, str):
            key = tuple(
                unicodedata.normalize("NFC", part).casefold().rstrip(". ")
                for part in PurePosixPath(value.replace("\\", "/")).parts
            )
            prior = seen.get(key)
            if prior is not None:
                findings.append(
                    _finding(
                        item_path,
                        "contract.path-collision",
                        f"Action path collides portably with {prior!r}.",
                        "Use one portable path identity per action set.",
                    )
                )
            else:
                seen[key] = value
            kind = action.get("kind")
            if isinstance(kind, str) and kind != "verify" and not _action_path_allowed(
                kind, value
            ):
                findings.append(
                    _finding(
                        item_path,
                        "contract.action-root",
                        f"Action kind {kind!r} cannot target {value!r}.",
                        "Use the managed root assigned to this action kind.",
                    )
                )
    return findings


def _action_path_allowed(kind: str, value: str) -> bool:
    if kind == "apply-migration":
        return value != "roadmap.json" and not value.startswith(
            (".cg-docs/", "releases/")
        )
    exact = {
        "update-config": {"compound-gpid.local.md"},
        "update-registry": {
            ".github/shared/module-registry.json",
            ".compound-gpid/project-skill-registry.json",
        },
        "update-manifest": {".compound-gpid/active-manifest.json"},
    }
    prefixes = {
        "create-directory": (
            ".github/skills/",
            ".github/shared/skill-management/",
            ".compound-gpid/skills/",
            ".compound-gpid/skill-provenance/",
        ),
        "write-file": (
            ".github/skills/",
            ".github/shared/skill-management/",
            ".compound-gpid/skills/",
            ".compound-gpid/skill-provenance/",
        ),
        "delete-file": (
            ".github/skills/",
            ".github/shared/skill-management/",
            ".compound-gpid/skills/",
            ".compound-gpid/skill-provenance/",
        ),
        "generate-targets": (".claude/", ".agents/", ".opencode/", ".kilo/"),
        "publish-projection": (
            ".github/skills/",
            ".claude/",
            ".agents/",
            ".opencode/",
            ".kilo/",
        ),
        "write-tombstone": (
            ".github/shared/skill-management/",
            ".compound-gpid/skill-provenance/",
        ),
    }
    if kind in exact:
        return value in exact[kind]
    return any(value.startswith(prefix) for prefix in prefixes.get(kind, ()))


def _plan_invariants(plan: Mapping[str, Any]) -> Sequence[ContractFinding]:
    bindings = plan.get("bindings")
    if not isinstance(bindings, dict):
        return ()
    revision = bindings.get("sourceRevision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        return (
            _finding(
                "/bindings/sourceRevision",
                "contract.source-revision",
                "Plan source revision must be one full immutable commit SHA.",
                "Bind the plan to a lowercase 40-character commit SHA.",
            ),
        )
    return ()


def _project_registry_invariants(registry: Mapping[str, Any]) -> Sequence[ContractFinding]:
    findings = []  # type: list[ContractFinding]
    seen_ids = {}  # type: Dict[str, int]
    seen_capabilities = {}  # type: Dict[str, int]
    seen_paths = {}  # type: Dict[str, int]
    records = registry.get("records", [])
    if not isinstance(records, list):
        return findings
    by_id = {
        record.get("id"): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    successor_edges = {}  # type: Dict[str, str]
    record_ids = [
        record.get("id")
        for record in records
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    ]
    if record_ids != sorted(record_ids):
        findings.append(
            _finding(
                "/records",
                "registry.order",
                "Project registry records must be ordered by identifier.",
                "Sort records by id before serialization.",
            )
        )
    suite_order = {"cg": 0, "cr": 1}
    platform_order = {
        name: index
        for index, name in enumerate(
            ("copilot", "claude-code", "codex", "opencode", "kilo")
        )
    }
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        prefix = f"/records/{index}"
        identifier = record.get("id")
        if isinstance(identifier, str):
            key = identifier.casefold()
            if key in seen_ids:
                findings.append(
                    _finding(f"{prefix}/id", "registry.duplicate-id", "Project skill identifiers collide portably.", "Use one unique lowercase project skill identifier.")
                )
            else:
                seen_ids[key] = index
            if record.get("capability") != f"project-skill-{identifier}":
                findings.append(
                    _finding(f"{prefix}/capability", "registry.capability-id", "Project capability must be project-skill-<id>.", "Set capability from the immutable skill identifier.")
                )
            if record.get("sourcePath") != f".compound-gpid/skills/{identifier}":
                findings.append(
                    _finding(f"{prefix}/sourcePath", "registry.source-path", "Project source path must match the skill identifier.", "Use .compound-gpid/skills/<id>.")
                )
            if record.get("provenanceId") != identifier:
                findings.append(
                    _finding(f"{prefix}/provenanceId", "registry.provenance-id", "Provenance identity must match the skill identifier.", "Use the immutable skill identifier for provenanceId.")
                )
        if record.get("activationMode") != "explicit-only":
            findings.append(
                _finding(f"{prefix}/activationMode", "registry.activation-mode", "Project skills must use explicit-only activation.", "Set activationMode to explicit-only.")
            )
        for field, order in (
            ("supportedSuites", suite_order),
            ("supportedPlatforms", platform_order),
        ):
            values = record.get(field)
            if isinstance(values, list) and values != sorted(
                values, key=lambda value: order.get(value, len(order))
            ):
                findings.append(
                    _finding(
                        f"{prefix}/{field}",
                        "registry.order",
                        f"{field} must use canonical order.",
                        f"Sort {field} by the documented enum order.",
                    )
                )
        for field, seen, code in (
            ("capability", seen_capabilities, "registry.duplicate-capability"),
            ("sourcePath", seen_paths, "registry.duplicate-source-path"),
        ):
            value = record.get(field)
            if isinstance(value, str):
                key = value.casefold()
                if key in seen:
                    findings.append(
                        _finding(f"{prefix}/{field}", code, f"Project records share {field}.", f"Assign one unique {field} per project skill.")
                    )
                else:
                    seen[key] = index
        lifecycle = record.get("lifecycle")
        successor = record.get("successorId")
        if lifecycle == "deprecated":
            if not isinstance(successor, str):
                findings.append(
                    _finding(
                        f"{prefix}/successorId",
                        "registry.successor-required",
                        "Deprecated skills require a successor.",
                        "Set successorId to a current skill in the same registry.",
                    )
                )
            elif successor == identifier:
                findings.append(
                    _finding(
                        f"{prefix}/successorId",
                        "registry.successor-self",
                        "A skill cannot succeed itself.",
                        "Choose another current skill as successor.",
                    )
                )
            elif successor not in by_id or by_id[successor].get("lifecycle") != "current":
                findings.append(
                    _finding(
                        f"{prefix}/successorId",
                        "registry.successor-invalid",
                        "Successor must identify a current registry record.",
                        "Choose an existing current successor.",
                    )
                )
            elif isinstance(identifier, str):
                successor_edges[identifier] = successor
        elif successor is not None:
            findings.append(
                _finding(
                    f"{prefix}/successorId",
                    "registry.successor-state",
                    "Only deprecated skills may declare a successor.",
                    "Remove successorId or mark the skill deprecated.",
                )
            )
    for start in sorted(successor_edges):
        seen_chain = set()  # type: set[str]
        current = start
        while current in successor_edges:
            if current in seen_chain:
                findings.append(
                    _finding(
                        "/records",
                        "registry.successor-cycle",
                        "Successor graph contains a cycle.",
                        "Use an acyclic successor chain.",
                    )
                )
                break
            seen_chain.add(current)
            current = successor_edges[current]
    return findings


def _provenance_invariants(provenance: Mapping[str, Any]) -> Sequence[ContractFinding]:
    findings = []  # type: list[ContractFinding]
    history = provenance.get("history", [])
    if isinstance(history, list):
        sequences = [entry.get("sequence") for entry in history if isinstance(entry, dict)]
        if sequences and sequences != list(range(1, len(sequences) + 1)):
            findings.append(
                _finding("/history", "provenance.sequence", "History sequence values must be contiguous and append-only.", "Number history entries from 1 in stored order.")
            )
    lifecycle = provenance.get("lifecycle")
    successor_id = provenance.get("successorId")
    deprecated_digest = provenance.get("deprecatedRecordDigest")
    skill_id = provenance.get("skillId")
    if isinstance(skill_id, str) and len(skill_id) > 80:
        findings.append(
            _finding(
                "/skillId",
                "provenance.skill-id-length",
                "Skill identifiers may contain at most 80 characters.",
                "Use the same immutable identifier limit as the project registry.",
            )
        )
    if lifecycle == "removed" and "tombstone" not in provenance:
        findings.append(
            _finding("/tombstone", "provenance.tombstone-required", "Removed skills require an immutable tombstone.", "Add the removal tombstone before marking the skill removed.")
        )
    if lifecycle in {"deprecated", "removed"}:
        if not isinstance(successor_id, str):
            findings.append(
                _finding(
                    "/successorId",
                    "provenance.successor-required",
                    "Deprecated and removed skills require a successor.",
                    "Record one current same-origin successor.",
                )
            )
        if not isinstance(deprecated_digest, str):
            findings.append(
                _finding(
                    "/deprecatedRecordDigest",
                    "provenance.deprecation-digest-required",
                    "Deprecated and removed skills require an immutable record digest.",
                    "Store the digest of the exact reviewed deprecation record.",
                )
            )
    elif successor_id is not None or deprecated_digest is not None:
        findings.append(
            _finding(
                "/lifecycle",
                "provenance.deprecation-state",
                "Current provenance cannot contain deprecation metadata.",
                "Remove deprecation metadata or use deprecated lifecycle state.",
            )
        )
    tombstone = provenance.get("tombstone")
    if lifecycle == "removed" and isinstance(tombstone, dict):
        if tombstone.get("skillId") != provenance.get("skillId"):
            findings.append(
                _finding(
                    "/tombstone/skillId",
                    "provenance.tombstone-identity",
                    "Tombstone identity must match the provenance skillId.",
                    "Set tombstone.skillId to the immutable skillId.",
                )
            )
        if isinstance(deprecated_digest, str) and tombstone.get(
            "recordDigest"
        ) != deprecated_digest:
            findings.append(
                _finding(
                    "/tombstone/recordDigest",
                    "provenance.tombstone-record",
                    "Tombstone recordDigest must preserve the deprecation record digest.",
                    "Copy the exact deprecatedRecordDigest into the tombstone.",
                )
            )
        successor = tombstone.get("successorId")
        if isinstance(successor, str) and len(successor) > 80:
            findings.append(
                _finding(
                    "/tombstone/successorId",
                    "provenance.skill-id-length",
                    "Successor identifiers may contain at most 80 characters.",
                    "Use the shared immutable skill identifier limit.",
                )
            )
    elif lifecycle != "removed" and tombstone is not None:
        findings.append(
            _finding(
                "/tombstone",
                "provenance.tombstone-state",
                "Only removed skills may contain a tombstone.",
                "Remove the tombstone or mark lifecycle removed.",
            )
        )
    if isinstance(history, list) and history:
        latest = history[-1]
        source = provenance.get("source")
        if isinstance(latest, dict) and isinstance(source, dict):
            if latest.get("bundleDigest") != source.get("bundleDigest"):
                findings.append(
                    _finding(
                        "/history",
                        "provenance.latest-digest",
                        "Latest history bundle digest must match source bundle digest.",
                        "Make the source and latest history entry describe the same bundle.",
                    )
                )
            expected_terminal = {
                "deprecated": "deprecated",
                "removed": "removed",
            }.get(lifecycle)
            if expected_terminal is not None and latest.get("event") != expected_terminal:
                findings.append(
                    _finding(
                        "/history",
                        "provenance.terminal-event",
                        f"Lifecycle {lifecycle!r} requires terminal event {expected_terminal!r}.",
                        "Append the lifecycle event before changing the stored lifecycle.",
                    )
                )
            if lifecycle in {"deprecated", "removed"} and isinstance(
                deprecated_digest, str
            ):
                terminal = next(
                    (
                        item
                        for item in history
                        if isinstance(item, dict)
                        and item.get("event") == "deprecated"
                    ),
                    None,
                )
                if terminal is None or terminal.get("recordDigest") != deprecated_digest:
                    findings.append(
                        _finding(
                            "/history",
                            "provenance.deprecation-record",
                            "Deprecation history must preserve the exact record digest.",
                            "Append one digest-bound deprecation event before removal.",
                        )
                    )
            if lifecycle == "removed" and isinstance(tombstone, dict):
                latest_commit = latest.get("commit")
                if (
                    isinstance(latest_commit, str)
                    and tombstone.get("removedRevision") != latest_commit
                ):
                    findings.append(
                        _finding(
                            "/tombstone/removedRevision",
                            "provenance.removed-revision",
                            "Tombstone removedRevision must match the removal history commit.",
                            "Bind the tombstone to the terminal removal event commit.",
                        )
                    )
    migrations = provenance.get("migrations")
    if isinstance(migrations, list):
        migration_ids = [
            item.get("id") for item in migrations if isinstance(item, dict)
        ]
        if len(migration_ids) != len(set(migration_ids)):
            findings.append(
                _finding(
                    "/migrations",
                    "provenance.duplicate-migration",
                    "Migration identifiers must be unique.",
                    "Use one immutable identifier per migration.",
                )
            )
    return findings


def _attestation_invariants(attestation: Mapping[str, Any]) -> Sequence[ContractFinding]:
    digests = attestation.get("deprecationRecordDigests")
    if not isinstance(digests, dict):
        return ()
    findings = []  # type: list[ContractFinding]
    seen = {}  # type: Dict[str, str]
    for identifier in sorted(digests):
        canonical = unicodedata.normalize("NFC", identifier).casefold()
        if re.fullmatch(r"[a-z][a-z0-9-]{0,79}", identifier) is None:
            findings.append(
                _finding(
                    _pointer("/deprecationRecordDigests", identifier),
                    "attestation.skill-id",
                    "Attestation keys must be canonical lowercase skill identifiers.",
                    "Use the immutable lowercase skill identifier.",
                )
            )
        prior = seen.get(canonical)
        if prior is not None and prior != identifier:
            findings.append(
                _finding(
                    _pointer("/deprecationRecordDigests", identifier),
                    "attestation.skill-id-collision",
                    f"Attestation key collides portably with {prior!r}.",
                    "Use one canonical skill identifier.",
                )
            )
        seen[canonical] = identifier
    return findings


def validate_project_registry(
    registry: Mapping[str, Any],
    *,
    canonical_ids: Iterable[str] = (),
    canonical_capabilities: Iterable[str] = (),
) -> Tuple[ContractFinding, ...]:
    """Validate project records and reject canonical identifier shadowing."""
    contract_path = Path(__file__).resolve().parents[2] / (
        ".github/shared/skill-management/contracts/project-registry-v1.schema.json"
    )
    findings = list(validate_instance(registry, load_contract(contract_path)))
    canonical_id_set = {value.casefold() for value in canonical_ids}
    canonical_capability_set = {value.casefold() for value in canonical_capabilities}
    records = registry.get("records", []) if isinstance(registry, dict) else []
    if isinstance(records, list):
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            identifier = record.get("id")
            capability = record.get("capability")
            if isinstance(identifier, str) and identifier.casefold() in canonical_id_set:
                findings.append(
                    _finding(f"/records/{index}/id", "registry.canonical-shadow", "Project skill identifier shadows a canonical identifier.", "Choose a project identifier not used by canonical assets.")
                )
            if isinstance(capability, str) and capability.casefold() in canonical_capability_set:
                findings.append(
                    _finding(f"/records/{index}/capability", "registry.canonical-capability-shadow", "Project capability shadows a canonical capability.", "Use the reserved project-skill-<id> capability.")
                )
    return _sorted(findings)


def validate_contract_file(path: Path) -> Tuple[ContractFinding, ...]:
    """Load and meta-validate one contract file in the closed dialect."""
    try:
        schema = load_contract(path)
    except (OSError, ValueError) as error:
        return (
            _finding("", "schema.read", str(error), "Repair the contract as bounded regular UTF-8 JSON."),
        )
    return validate_schema_definition(schema)


def _read_root_file(
    source_root: Path,
    relative: PurePosixPath,
    *,
    label: str,
    max_bytes: int = MAX_CONTRACT_BYTES,
) -> bytes:
    errors = path_policy.validate_repo_relative_path(label, relative.as_posix())
    if errors:
        raise DescriptorValidationError(
            "descriptor.invalid", relative.as_posix(), "; ".join(errors)
        )
    try:
        return secure_fs.secure_read_bytes(
            source_root,
            relative,
            reject_hardlinks=True,
            max_bytes=max_bytes,
        )
    except (OSError, ValueError) as error:
        raise DescriptorValidationError(
            "descriptor.incomplete",
            relative.as_posix(),
            f"Declared {label} is missing or unsafe: {relative.as_posix()}: {error}",
        ) from error


def load_operation_descriptor(
    source_root: Path, operation: str
) -> OperationDescriptor:
    """Load one complete active descriptor without importing its handler.

    Args:
        source_root: Canonical Compound GPID source root.
        operation: Lowercase operation identifier.

    Returns:
        Validated descriptor and operation contract.

    Raises:
        FileNotFoundError: If no descriptor exists for the operation.
        DescriptorValidationError: If any declaration is invalid or incomplete.

    Example:
        ``record = load_operation_descriptor(root, "find")``
    """
    if OPERATION_PATTERN.fullmatch(operation) is None:
        raise DescriptorValidationError(
            "descriptor.invalid", "/operation", "Operation identifier is invalid."
        )
    root = Path(source_root).resolve()
    descriptor_relative = OPERATIONS_ROOT / f"{operation}.json"
    try:
        descriptor_bytes = secure_fs.secure_read_bytes(
            root,
            descriptor_relative,
            reject_hardlinks=True,
            max_bytes=MAX_CONTRACT_BYTES,
        )
    except FileNotFoundError:
        raise
    except (OSError, ValueError) as error:
        raise DescriptorValidationError(
            "descriptor.invalid",
            descriptor_relative.as_posix(),
            f"Operation descriptor cannot be read safely: {error}",
        ) from error
    try:
        descriptor = load_contract_bytes(
            descriptor_bytes, source=descriptor_relative.as_posix()
        )
        descriptor_schema = load_contract_bytes(
            _read_root_file(
                root,
                CONTRACTS_ROOT / "operation-descriptor-v1.schema.json",
                label="descriptor meta-contract",
            ),
            source=(CONTRACTS_ROOT / "operation-descriptor-v1.schema.json").as_posix(),
        )
    except ValueError as error:
        raise DescriptorValidationError(
            "descriptor.invalid", descriptor_relative.as_posix(), str(error)
        ) from error
    descriptor_findings = validate_instance(descriptor, descriptor_schema)
    if descriptor_findings:
        detail = "; ".join(
            f"{finding.path}: {finding.code}" for finding in descriptor_findings
        )
        raise DescriptorValidationError(
            "descriptor.invalid",
            descriptor_relative.as_posix(),
            f"Operation descriptor is invalid: {detail}",
        )
    if descriptor.get("operation") != operation:
        raise DescriptorValidationError(
            "descriptor.invalid",
            descriptor_relative.as_posix(),
            "Operation descriptor identity does not match its filename.",
        )
    try:
        module_name = operation_handler_module(operation, str(descriptor.get("handler", "")))
    except ValueError as error:
        raise DescriptorValidationError(
            "descriptor.invalid",
            descriptor_relative.as_posix(),
            str(error),
        ) from error
    handler_relative = PurePosixPath(
        f"scripts/skill_management/operations/{module_name}.py"
    )
    _read_root_file(root, handler_relative, label="handler")
    _read_root_file(
        root,
        PurePosixPath(descriptor["workflow"]),
        label="workflow",
        max_bytes=4 * 1024 * 1024,
    )
    _read_root_file(
        root,
        PurePosixPath(descriptor["documentation"]),
        label="documentation",
        max_bytes=4 * 1024 * 1024,
    )
    tests = descriptor["tests"]
    if tests != sorted(tests):
        raise DescriptorValidationError(
            "descriptor.invalid",
            descriptor_relative.as_posix(),
            "Operation descriptor test declarations must use lexical order.",
        )
    for test_path in tests:
        _read_root_file(
            root, PurePosixPath(test_path), label="test", max_bytes=4 * 1024 * 1024
        )
    contract_relative = PurePosixPath(descriptor["contract"])
    if contract_relative.name != f"{operation}-v1.schema.json":
        raise DescriptorValidationError(
            "descriptor.invalid",
            contract_relative.as_posix(),
            "Operation contract filename does not match the operation.",
        )
    try:
        operation_contract = load_contract_bytes(
            _read_root_file(root, contract_relative, label="operation contract"),
            source=contract_relative.as_posix(),
        )
    except ValueError as error:
        raise DescriptorValidationError(
            "descriptor.invalid", contract_relative.as_posix(), str(error)
        ) from error
    schema_findings = validate_schema_definition(operation_contract)
    if schema_findings:
        detail = "; ".join(
            f"{finding.path}: {finding.code}" for finding in schema_findings
        )
        raise DescriptorValidationError(
            "descriptor.invalid",
            contract_relative.as_posix(),
            f"Operation contract is invalid: {detail}",
        )
    contract_id = operation_contract.get("$id")
    if not isinstance(contract_id, str) or not contract_id.startswith(
        f"cg-skill-{operation}-"
    ):
        raise DescriptorValidationError(
            "descriptor.invalid",
            contract_relative.as_posix(),
            "Operation contract identity does not match the operation.",
        )
    definitions = operation_contract.get("$defs")
    if not isinstance(definitions, dict) or not all(
        isinstance(definitions.get(name), dict)
        for name in ("arguments", "resultData")
    ):
        raise DescriptorValidationError(
            "descriptor.invalid",
            contract_relative.as_posix(),
            "Operation contract must define arguments and resultData schemas.",
        )
    return OperationDescriptor(operation, descriptor, operation_contract)


def _validate_operation_documentation(
    operation: str,
    descriptor: Mapping[str, Any],
    argument_schema: Mapping[str, Any],
    relative: PurePosixPath,
    content: bytes,
) -> None:
    """Validate descriptor identity and contract grammar in one command page."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DescriptorValidationError(
            "descriptor.documentation",
            relative.as_posix(),
            "Operation documentation must be valid UTF-8.",
        ) from error

    expected_heading = f"# `cg-skill {operation}`"
    lines = text.splitlines()
    if not lines or lines[0] != expected_heading:
        raise DescriptorValidationError(
            "descriptor.documentation",
            relative.as_posix(),
            f"Operation documentation must start with {expected_heading!r}.",
        )
    if len(lines) < 3 or not lines[2].strip() or lines[2].lstrip().startswith("#"):
        raise DescriptorValidationError(
            "descriptor.documentation",
            relative.as_posix(),
            "Operation documentation must include a focused description after its H1.",
        )

    role_text = ", ".join(f"`{role}`" for role in descriptor["roles"])
    phase_text = ", ".join(f"`{phase}`" for phase in descriptor["phases"])
    required_markers = (
        f"**Roles:** {role_text}",
        f"**Phases:** {phase_text}",
        "## Synopsis",
        "## Options",
        "## Examples",
        "## Lifecycle Effect",
        "## Results",
    )
    missing_markers = [marker for marker in required_markers if marker not in text]
    if missing_markers:
        raise DescriptorValidationError(
            "descriptor.documentation",
            relative.as_posix(),
            "Operation documentation is missing required markers: "
            + ", ".join(missing_markers),
        )

    properties = argument_schema.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    expected_options = {
        "--" + str(name).replace("_", "-")
        for name in properties
        if name != "positionals"
    }
    if "apply" in descriptor["phases"]:
        expected_options.add("--apply")
    documented_options = set(re.findall(r"(?<![a-z0-9-])--[a-z][a-z0-9-]*", text))
    missing_options = sorted(expected_options - documented_options)
    if missing_options:
        raise DescriptorValidationError(
            "descriptor.documentation",
            relative.as_posix(),
            "Operation documentation is missing contract options: "
            + ", ".join(missing_options),
        )

    example_pattern = re.compile(
        rf"^python scripts/cg_skill\.py .*\b{re.escape(operation)}(?:\s|$)",
        re.MULTILINE,
    )
    if example_pattern.search(text) is None:
        raise DescriptorValidationError(
            "descriptor.documentation",
            relative.as_posix(),
            "Operation documentation must include an executable private-CLI example.",
        )


def discover_operation_descriptors(
    source_root: Path,
) -> Tuple[Tuple[OperationDescriptor, ...], Tuple[ContractFinding, ...]]:
    """Discover all complete active operation descriptors in lexical order.

    Args:
        source_root: Canonical Compound GPID source root.

    Returns:
        Tuple of valid descriptor records and deterministic findings.

    Example:
        ``records, findings = discover_operation_descriptors(root)``
    """
    root = Path(source_root).resolve()
    directory = root.joinpath(*OPERATIONS_ROOT.parts)
    try:
        metadata = os.lstat(str(directory))
    except OSError as error:
        finding = ContractFinding(
            OPERATIONS_ROOT.as_posix(),
            "descriptor.incomplete",
            "error",
            f"Operation descriptor directory is missing: {error}",
            "Create the canonical operations directory and complete descriptors.",
        )
        return (), (finding,)
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        finding = ContractFinding(
            OPERATIONS_ROOT.as_posix(),
            "descriptor.invalid",
            "error",
            "Operation descriptor directory is a link, reparse point, or non-directory.",
            "Replace it with one real canonical directory.",
        )
        return (), (finding,)
    operation_names = []
    findings = []
    with os.scandir(str(directory)) as entries:
        ordered = sorted(entries, key=lambda item: item.name)
    seen_paths = {}
    for entry in ordered:
        entry_metadata = entry.stat(follow_symlinks=False)
        relative = f"{OPERATIONS_ROOT.as_posix()}/{entry.name}"
        key = path_policy.portable_path_key(relative)
        prior = seen_paths.get(key)
        if prior is not None:
            findings.append(
                ContractFinding(
                    relative,
                    "descriptor.invalid",
                    "error",
                    f"Operation descriptor path collides portably with {prior}.",
                    "Use one lowercase portable descriptor filename.",
                )
            )
            continue
        seen_paths[key] = relative
        if (
            _is_link_or_reparse(entry_metadata)
            or not stat.S_ISREG(entry_metadata.st_mode)
            or not entry.name.endswith(".json")
        ):
            findings.append(
                ContractFinding(
                    relative,
                    "descriptor.invalid",
                    "error",
                    "Operation descriptor entry must be one regular JSON file.",
                    "Remove non-JSON, linked, or non-regular operation entries.",
                )
            )
            continue
        operation_names.append(entry.name[:-5])
    records = []
    for operation in operation_names:
        try:
            record = load_operation_descriptor(root, operation)
            documentation_relative = PurePosixPath(record.descriptor["documentation"])
            documentation_bytes = _read_root_file(
                root,
                documentation_relative,
                label="documentation",
                max_bytes=4 * 1024 * 1024,
            )
            _validate_operation_documentation(
                operation,
                record.descriptor,
                record.contract["$defs"]["arguments"],
                documentation_relative,
                documentation_bytes,
            )
            records.append(record)
        except (FileNotFoundError, DescriptorValidationError) as error:
            if isinstance(error, DescriptorValidationError):
                code = error.code
                path = error.path
                message = str(error)
            else:
                code = "descriptor.incomplete"
                path = f"{OPERATIONS_ROOT.as_posix()}/{operation}.json"
                message = str(error)
            findings.append(
                ContractFinding(
                    path,
                    code,
                    "error",
                    message,
                    "Add or repair the descriptor, workflow, handler, contract, tests, and documentation page together.",
                )
            )
    return tuple(records), sort_findings(findings)


def descriptor_completeness_findings(
    source_root: Path,
) -> Tuple[ContractFinding, ...]:
    """Return completeness findings for every registered operation.

    Args:
        source_root: Canonical Compound GPID source root.

    Returns:
        Empty tuple when every operation is complete.

    Example:
        ``assert not descriptor_completeness_findings(root)``
    """
    _, findings = discover_operation_descriptors(source_root)
    return findings
