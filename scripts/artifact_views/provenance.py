"""Normalized source identity and deterministic artifact-view provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple, Union

from artifact_views.errors import ArtifactReadError

_PROVENANCE_KEYS = {
    "artifactSchemaVersion",
    "generatedAt",
    "rendererVersion",
    "sourcePath",
    "sourceSha256",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def normalized_source_bytes(source_bytes: bytes) -> bytes:
    """Normalize source bytes exactly as defined by the artifact contract.

    Args:
        source_bytes: Canonical source encoded as strict UTF-8.

    Returns:
        UTF-8 bytes after removing one BOM and normalizing CRLF/lone CR to LF.
        All Unicode, remaining whitespace, and trailing newlines are preserved.

    Raises:
        ArtifactReadError: If ``source_bytes`` is not strict UTF-8.

    Example:
        >>> normalized_source_bytes(b"a\r\nb\r")
        b'a\nb\n'
    """
    try:
        text = source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ArtifactReadError(
            "Artifact source is not valid strict UTF-8.",
            corrective_action="Save the canonical Markdown source as UTF-8.",
        ) from error
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def source_sha256(source_bytes: bytes) -> str:
    """Return the lowercase SHA-256 of normalized canonical source bytes.

    Args:
        source_bytes: Canonical strict UTF-8 source bytes.

    Returns:
        A 64-character lowercase hexadecimal digest.

    Example:
        >>> len(source_sha256(b"artifact\n"))
        64
    """
    return hashlib.sha256(normalized_source_bytes(source_bytes)).hexdigest()


@dataclass(frozen=True)
class ArtifactProvenance:
    """Complete machine-readable and visible artifact-view provenance."""

    source_path: str
    source_sha256: str
    artifact_schema_version: Union[int, str]
    renderer_version: str
    generated_at: str

    @classmethod
    def from_source(
        cls,
        *,
        source_path: Path,
        source_bytes: bytes,
        artifact_schema_version: Union[int, str],
        renderer_version: str,
        generated_at: datetime,
    ) -> "ArtifactProvenance":
        """Build provenance from explicit complete renderer inputs.

        Args:
            source_path: Project-relative canonical source path.
            source_bytes: Exact canonical source bytes.
            artifact_schema_version: Strict version or legacy label.
            renderer_version: Deterministic renderer version identifier.
            generated_at: Explicit timezone-aware UTC timestamp.

        Returns:
            Immutable provenance ready for JSON serialization.

        Raises:
            ValueError: If the timestamp is not timezone-aware UTC.

        Example:
            Build provenance at render time with an explicit UTC timestamp.
        """
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("generated_at must be a timezone-aware UTC timestamp.")
        if generated_at.utcoffset() != timezone.utc.utcoffset(generated_at):
            raise ValueError("generated_at must be a timezone-aware UTC timestamp.")
        timestamp = generated_at.astimezone(timezone.utc).replace(microsecond=0)
        return cls(
            source_path=Path(source_path).as_posix(),
            source_sha256=source_sha256(source_bytes),
            artifact_schema_version=artifact_schema_version,
            renderer_version=renderer_version,
            generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        )

    @classmethod
    def from_json(cls, raw_json: str) -> "ArtifactProvenance":
        """Parse and strictly validate embedded provenance JSON.

        Args:
            raw_json: JSON text from the generated provenance script element.

        Returns:
            Validated immutable provenance.

        Raises:
            ValueError: If JSON is malformed, duplicated, incomplete, or typed
                differently from the provenance contract.

        Example:
            ``ArtifactProvenance.from_json(embedded_json)`` validates metadata.
        """
        def reject_duplicates(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"Duplicate provenance key: {key!r}.")
                result[key] = value
            return result

        try:
            data = json.loads(raw_json, object_pairs_hook=reject_duplicates)
        except json.JSONDecodeError as error:
            raise ValueError(f"Provenance JSON is malformed: {error}.") from error
        if not isinstance(data, dict) or set(data) != _PROVENANCE_KEYS:
            raise ValueError("Provenance JSON fields do not match the contract.")
        source_path = data["sourcePath"]
        source_hash = data["sourceSha256"]
        renderer_version = data["rendererVersion"]
        generated_at = data["generatedAt"]
        schema_version = data["artifactSchemaVersion"]
        if not isinstance(source_path, str) or not source_path:
            raise ValueError("Provenance sourcePath must be a non-empty string.")
        if not isinstance(source_hash, str) or not _SHA256_RE.fullmatch(source_hash):
            raise ValueError("Provenance sourceSha256 must be a lowercase SHA-256.")
        if not isinstance(renderer_version, str) or not renderer_version:
            raise ValueError("Provenance rendererVersion must be non-empty.")
        if not isinstance(generated_at, str):
            raise ValueError("Provenance generatedAt must be a UTC string.")
        try:
            datetime.strptime(generated_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as error:
            raise ValueError("Provenance generatedAt must be a real UTC timestamp.") from error
        if isinstance(schema_version, bool) or not isinstance(schema_version, (int, str)):
            raise ValueError("Provenance artifactSchemaVersion must be an integer or string.")
        return cls(
            source_path=source_path,
            source_sha256=source_hash,
            artifact_schema_version=schema_version,
            renderer_version=renderer_version,
            generated_at=generated_at,
        )

    def generated_datetime(self) -> datetime:
        """Return the embedded generation time as a timezone-aware UTC value.

        Args:
            None.

        Returns:
            The parsed generation timestamp in UTC.

        Example:
            ``provenance.generated_datetime().tzinfo`` is ``timezone.utc``.
        """
        return datetime.strptime(
            self.generated_at,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)

    def to_dict(self) -> Dict[str, Union[int, str]]:
        """Return the canonical JSON-compatible provenance object.

        Args:
            None.

        Returns:
            Provenance fields using their embedded JSON names.

        Example:
            ``provenance.to_dict()["sourceSha256"]`` returns the source digest.
        """
        return {
            "artifactSchemaVersion": self.artifact_schema_version,
            "generatedAt": self.generated_at,
            "rendererVersion": self.renderer_version,
            "sourcePath": self.source_path,
            "sourceSha256": self.source_sha256,
        }

    def to_json(self) -> str:
        """Serialize deterministic compact JSON for embedding in HTML.

        Args:
            None.

        Returns:
            Sorted compact JSON with no insignificant whitespace.

        Example:
            ``provenance.to_json()`` produces the embedded provenance payload.
        """
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
