"""Normalized source identity and deterministic artifact-view provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
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
_PUBLICATION_PROVENANCE_KEYS = {
    "documentType",
    "generatedAt",
    "outputPath",
    "provenanceSchemaVersion",
    "rendererVersion",
    "sourcePath",
    "sourceSha256",
    "themeName",
    "themeVersion",
}


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
    """Return the lowercase SHA-256 of the exact canonical source bytes.

    Args:
        source_bytes: Canonical strict UTF-8 source bytes.

    Returns:
        A 64-character lowercase hexadecimal digest of the unmodified bytes.
        Byte-order marks and line endings change the digest.

    Example:
        >>> len(source_sha256(b"artifact\n"))
        64
    """
    return hashlib.sha256(source_bytes).hexdigest()


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


@dataclass(frozen=True)
class PublicationProvenance:
    """Schema-2 provenance carrying source, output, and theme ownership."""

    source_path: str
    source_sha256: str
    output_path: str
    document_type: str
    renderer_version: str
    theme_name: str
    theme_version: int
    generated_at: str
    provenance_schema_version: int = 2

    @classmethod
    def from_source(
        cls,
        *,
        source_path: Path,
        source_bytes: bytes,
        output_path: Path,
        document_type: str,
        renderer_version: str,
        theme_name: str,
        theme_version: int,
        generated_at: datetime,
    ) -> "PublicationProvenance":
        """Build exact schema-2 provenance from complete publication inputs.

        Args:
            source_path: Project-relative canonical source identity.
            source_bytes: Exact canonical source bytes.
            output_path: Registered project-relative HTML destination.
            document_type: Stable strict or generic document type.
            renderer_version: Deterministic renderer identity.
            theme_name: Registered presentation theme name.
            theme_version: Registered theme contract version.
            generated_at: Explicit timezone-aware UTC timestamp.

        Returns:
            Immutable schema-2 publication provenance.

        Example:
            Build this object only after source, output, and theme resolution.
        """
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("generated_at must be a timezone-aware UTC timestamp.")
        if generated_at.utcoffset() != timezone.utc.utcoffset(generated_at):
            raise ValueError("generated_at must be a timezone-aware UTC timestamp.")
        timestamp = generated_at.astimezone(timezone.utc).replace(microsecond=0)
        return cls(
            source_path=Path(source_path).as_posix(),
            source_sha256=source_sha256(source_bytes),
            output_path=Path(output_path).as_posix(),
            document_type=document_type,
            renderer_version=renderer_version,
            theme_name=theme_name,
            theme_version=theme_version,
            generated_at=timestamp.isoformat().replace("+00:00", "Z"),
        )

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "PublicationProvenance":
        """Validate one already-decoded exact schema-2 provenance object.

        Args:
            data: Decoded JSON mapping with exact schema-2 keys.

        Returns:
            Strictly validated publication provenance.

        Example:
            ``PublicationProvenance.from_mapping(decoded)`` rejects extra keys.
        """
        if set(data) != _PUBLICATION_PROVENANCE_KEYS:
            raise ValueError("Provenance JSON fields do not match schema 2.")
        if data["provenanceSchemaVersion"] != 2:
            raise ValueError("Unknown provenance schema version.")
        source_path = _validate_relative_identity(data["sourcePath"], "sourcePath")
        output_path = _validate_relative_identity(data["outputPath"], "outputPath")
        source_hash = data["sourceSha256"]
        if not isinstance(source_hash, str) or not _SHA256_RE.fullmatch(source_hash):
            raise ValueError("Provenance sourceSha256 must be a lowercase SHA-256.")
        document_type = data["documentType"]
        renderer_version = data["rendererVersion"]
        theme_name = data["themeName"]
        theme_version = data["themeVersion"]
        generated_at = data["generatedAt"]
        for field_name, value in (
            ("documentType", document_type),
            ("rendererVersion", renderer_version),
            ("themeName", theme_name),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"Provenance {field_name} must be non-empty.")
        if isinstance(theme_version, bool) or not isinstance(theme_version, int):
            raise ValueError("Provenance themeVersion must be an integer.")
        if theme_version < 0:
            raise ValueError("Provenance themeVersion cannot be negative.")
        if not isinstance(generated_at, str):
            raise ValueError("Provenance generatedAt must be a UTC string.")
        try:
            datetime.strptime(generated_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as error:
            raise ValueError(
                "Provenance generatedAt must be a real UTC timestamp."
            ) from error
        return cls(
            source_path=source_path,
            source_sha256=source_hash,
            output_path=output_path,
            document_type=document_type,
            renderer_version=renderer_version,
            theme_name=theme_name,
            theme_version=theme_version,
            generated_at=generated_at,
        )

    def generated_datetime(self) -> datetime:
        """Return the schema-2 generation timestamp in UTC.

        Args:
            None.

        Returns:
            Timezone-aware UTC generation timestamp.

        Example:
            ``provenance.generated_datetime().tzinfo`` is UTC.
        """
        return datetime.strptime(
            self.generated_at,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)

    def to_dict(self) -> Dict[str, Union[int, str]]:
        """Return the exact canonical schema-2 JSON object.

        Args:
            None.

        Returns:
            JSON-compatible mapping with exact schema-2 field names.

        Example:
            ``provenance.to_dict()['provenanceSchemaVersion']`` returns 2.
        """
        return {
            "documentType": self.document_type,
            "generatedAt": self.generated_at,
            "outputPath": self.output_path,
            "provenanceSchemaVersion": self.provenance_schema_version,
            "rendererVersion": self.renderer_version,
            "sourcePath": self.source_path,
            "sourceSha256": self.source_sha256,
            "themeName": self.theme_name,
            "themeVersion": self.theme_version,
        }

    def to_json(self) -> str:
        """Serialize deterministic compact schema-2 provenance JSON.

        Args:
            None.

        Returns:
            Sorted compact JSON with no insignificant whitespace.

        Example:
            ``provenance.to_json()`` is embedded in generated HTML.
        """
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


Provenance = Union[ArtifactProvenance, PublicationProvenance]


def parse_provenance(raw_json: str) -> Provenance:
    """Dispatch exact schema-1 or schema-2 provenance without coercion.

    Args:
        raw_json: Embedded provenance JSON text.

    Returns:
        Validated legacy artifact or schema-2 publication provenance.

    Example:
        ``parse_provenance(payload)`` preserves schema-1 dispatch unchanged.
    """
    data = _load_json_object(raw_json)
    if "provenanceSchemaVersion" not in data:
        return ArtifactProvenance.from_json(raw_json)
    return PublicationProvenance.from_mapping(data)


def _load_json_object(raw_json: str) -> Dict[str, Any]:
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
    if not isinstance(data, dict):
        raise ValueError("Provenance JSON must be an object.")
    return data


def _validate_relative_identity(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"Provenance {field_name} must be a relative POSIX path.")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"Provenance {field_name} must be a relative POSIX path.")
    return path.as_posix()
