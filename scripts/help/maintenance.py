"""Catalog generation and maintenance mutations for evidence-backed help.

This module serializes validated source metadata into the deterministic
catalog and performs the single named-record digest operations. Every mutation
delegates the final replace to the shared secure primitive.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Tuple

import secure_fs
from help.base import (
    CATALOG_OUTPUT_PATH,
    CATALOG_SCHEMA_VERSION,
    GENERATOR_VERSION,
    HelpCatalogIOError,
    HelpCatalogStaleError,
    HelpValidationError,
    MAX_JSON_BYTES,
    MODULE_REGISTRY_PATH,
    QUALIFIED_ID_PATTERN,
    SHELL_METADATA_PATH,
    SourceMetadata,
    compute_source_digest,
    load_strict_json_bytes,
)
from help.validation import (
    _read_source_bytes,
    _source_path,
    compute_definition_digest,
    validate_catalog,
    validate_source_metadata,
)


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
    content = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if len(content) > MAX_JSON_BYTES:
        raise HelpValidationError(
            "catalog output exceeds the JSON byte limit; shrink the source graph"
        )
    return content


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
    """Replace one regular file atomically via the shared secure primitive.

    The secure write backend fsyncs the content and, where supported, the
    parent directory, and treats post-publication cleanup loss as a
    non-fatal warning because the committed output already succeeded.
    """
    try:
        secure_fs.secure_write_bytes(path.parent, Path(path.name), content)
    except secure_fs.SecureMutationError as error:
        raise HelpCatalogIOError("cannot replace {}: {}".format(path, error)) from error


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
        root, maintenance_definition_id=command_id
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
        root,
        maintenance_definition_id=command_id,
        require_current_definition=True,
        source_overrides={metadata_path: updated},
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