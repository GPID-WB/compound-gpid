"""Shared lightweight contracts for help metadata validation (no I/O graph).

Runtime modules such as help.query import only this module, never the
build-time catalog, installer, or maintenance layers. It defines the inert
JSON contracts, strict loaders, and portable path rules the whole help domain
shares.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


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
    except RecursionError as error:
        raise HelpValidationError(
            "{} is nested too deeply for strict validation".format(source)
        ) from error


def load_strict_json(path: Path) -> Any:
    """Load one strict JSON file without interpreting any extracted strings."""
    try:
        content = Path(path).read_bytes()
    except OSError as error:
        raise HelpValidationError("cannot read {}: {}".format(path, error)) from error
    return load_strict_json_bytes(content, source=Path(path).as_posix())


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