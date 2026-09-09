"""Created 2026-08-12. Deterministic hashes for resources and source units."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unicodedata

from .schemas import TypedLocator


def text_fingerprint(text: str) -> str:
    """Hash normalized source text for stable unit matching.

    Args:
        text: Source text to normalize and hash.

    Returns:
        A ``sha256:``-prefixed lowercase fingerprint.

    Example:
        ``text_fingerprint("A  sentence")`` equals its single-space variant.
    """
    normalized = " ".join(unicodedata.normalize("NFKC", text).split())
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash one local file in binary mode.

    Args:
        path: Existing regular file to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.

    Raises:
        OSError: If the file cannot be read.

    Example:
        ``sha256_file(Path("resources/notes.md"))`` returns a 64-character digest.
    """
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_locator(locator: TypedLocator) -> str:
    """Serialize a typed locator with stable key order and separators.

    Args:
        locator: Validated typed locator.

    Returns:
        Canonical compact JSON representation.

    Example:
        ``canonical_locator(locator)`` is suitable for identity derivation.
    """
    payload = locator.model_dump(mode="json", exclude_none=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def make_source_version_id(
    resource_id: str,
    source_hash: str,
    parser_profile: str,
    locator_schema_version: str,
    parser_version: str = "",
) -> str:
    """Derive an immutable source-version ID from all compatibility inputs.

    Args:
        resource_id: Logical resource identifier.
        source_hash: Lowercase SHA-256 of original bytes.
        parser_profile: Exact parser and configuration profile.
        locator_schema_version: Typed locator contract version.
        parser_version: Optional exact parser version; omitted for Phase 1
            compatibility with the original identity contract.

    Returns:
        A deterministic ``source-version:`` identifier.

    Example:
        ``make_source_version_id("r1", "a" * 64, "markdown-v1", "locator-v1")``.
    """
    components = [resource_id, source_hash, parser_profile, locator_schema_version]
    if parser_version:
        components.append(parser_version)
    payload = "\x1f".join(components)
    return "source-version:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def make_source_unit_id(
    source_version_id: str,
    locator: TypedLocator,
    normalized_text_fingerprint: str,
) -> str:
    """Derive a deterministic source-unit ID from version, locator, and text.

    Args:
        source_version_id: Immutable source-version identifier.
        locator: Validated typed locator.
        normalized_text_fingerprint: Normalized unit-text fingerprint.

    Returns:
        A deterministic ``source-unit:`` identifier.

    Example:
        ``make_source_unit_id("v1", locator, text_fingerprint("Text"))``.
    """
    payload = "\x1f".join(
        (source_version_id, canonical_locator(locator), normalized_text_fingerprint)
    )
    return "source-unit:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
