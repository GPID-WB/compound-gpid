"""Schema and validation for artifact-view design evidence matrices."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

REQUIRED_OPEN_DESIGN_PATH = "/Users/r.andrescastaneda/.local/bin/od"
REQUIRED_VIEWPORTS = frozenset({(1440, 900), (768, 1024), (390, 844)})
REQUIRED_VIEWPORT_CHECKS = frozenset(
    {
        "nonblank",
        "noHorizontalOverflow",
        "noOverlap",
        "navigationReachable",
        "firstViewportIdentity",
    }
)
REQUIRED_ARTIFACT_CHECKS = frozenset(
    {
        "offlineLoad",
        "printPreview",
        "keyboardOrder",
        "visibleFocus",
        "zoom200",
        "contrast",
        "reducedMotion",
        "longDocumentOrientation",
        "completeProvenance",
    }
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class EvidenceValidationError(ValueError):
    """The design evidence is incomplete, stale, unsafe, or failing."""


@dataclass(frozen=True)
class EvidenceValidationResult:
    """Compact successful design-evidence validation summary."""

    artifact_count: int
    viewport_count: int


def validate_evidence_file(
    evidence_path: Path,
    *,
    require_all_pass: bool = False,
) -> EvidenceValidationResult:
    """Validate one complete artifact-view design evidence JSON document.

    Args:
        evidence_path: Evidence JSON path. Relative references are resolved from
            the nearest project root containing ``compound-gpid.md`` or, for
            isolated tests, from the evidence file's parent.
        require_all_pass: Require every named required result to be ``true``.

    Returns:
        Compact counts for the validated matrix.

    Raises:
        EvidenceValidationError: If schema, matrix coverage, hashes, files,
            Open Design identity, or required booleans are invalid.

    Example:
        ``validate_evidence_file(Path('evidence.json'), require_all_pass=True)``
        validates the complete matrix.
    """
    path = Path(evidence_path)
    if path.is_symlink() or not path.is_file():
        raise EvidenceValidationError(f"Evidence path is not a regular file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceValidationError(f"Evidence JSON is invalid: {error}") from error
    if not isinstance(data, dict):
        raise EvidenceValidationError("Evidence root must be a JSON object.")
    _reject_source_body(data)
    if data.get("schemaVersion") != 1:
        raise EvidenceValidationError("Evidence schemaVersion must be 1.")
    if not isinstance(data.get("generatedAt"), str) or not _TIMESTAMP_RE.fullmatch(
        data["generatedAt"]
    ):
        raise EvidenceValidationError("Evidence generatedAt must be UTC second precision.")
    _validate_open_design(data.get("openDesign"))
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise EvidenceValidationError("Evidence artifacts must be an array.")
    kinds = [item.get("kind") for item in artifacts if isinstance(item, dict)]
    if len(artifacts) != 2 or set(kinds) != {"brainstorm", "plan"}:
        raise EvidenceValidationError(
            "Evidence must contain exactly one brainstorm and exactly one plan."
        )

    project_root = _find_project_root(path)
    viewport_count = 0
    for artifact in artifacts:
        viewport_count += _validate_artifact(
            artifact,
            project_root,
            require_all_pass=require_all_pass,
        )
    return EvidenceValidationResult(len(artifacts), viewport_count)


def _validate_open_design(value: Any) -> None:
    if not isinstance(value, dict):
        raise EvidenceValidationError("openDesign must be an object.")
    if value.get("executable") != REQUIRED_OPEN_DESIGN_PATH:
        raise EvidenceValidationError(
            f"Open Design executable must be {REQUIRED_OPEN_DESIGN_PATH!r}."
        )
    version = value.get("version")
    if not isinstance(version, str) or not version.strip():
        raise EvidenceValidationError("Open Design version must be non-empty.")


def _validate_artifact(
    artifact: Mapping[str, Any],
    root: Path,
    *,
    require_all_pass: bool,
) -> int:
    kind = artifact.get("kind")
    source = _validated_file(root, artifact.get("sourcePath"), f"{kind} source")
    view = _validated_file(root, artifact.get("viewPath"), f"{kind} view")
    _validate_hash(source, artifact.get("sourceSha256"), f"{kind} source")
    _validate_hash(view, artifact.get("viewSha256"), f"{kind} view")
    print_preview = _validated_file(
        root,
        artifact.get("printPreviewArtifact"),
        f"{kind} print preview",
    )
    if print_preview.stat().st_size == 0:
        raise EvidenceValidationError(f"{kind} print preview is empty.")
    _validate_checks(
        artifact.get("checks"),
        REQUIRED_ARTIFACT_CHECKS,
        f"{kind} artifact",
        require_all_pass,
    )

    viewports = artifact.get("viewports")
    if not isinstance(viewports, list):
        raise EvidenceValidationError(f"{kind} viewports must be an array.")
    found: Set[Tuple[int, int]] = set()
    for viewport in viewports:
        if not isinstance(viewport, dict):
            raise EvidenceValidationError(f"{kind} viewport row must be an object.")
        size = (viewport.get("width"), viewport.get("height"))
        if size in found:
            raise EvidenceValidationError(f"{kind} has duplicate viewport {size}.")
        found.add(size)
        _validate_checks(
            viewport.get("checks"),
            REQUIRED_VIEWPORT_CHECKS,
            f"{kind} viewport {size}",
            require_all_pass,
        )
        screenshot = _validated_file(
            root,
            viewport.get("screenshot"),
            f"{kind} viewport {size} screenshot",
        )
        if screenshot.stat().st_size == 0:
            raise EvidenceValidationError(
                f"{kind} viewport {size} screenshot is empty."
            )
    if found != REQUIRED_VIEWPORTS:
        missing = sorted(REQUIRED_VIEWPORTS - found)
        extra = sorted(found - REQUIRED_VIEWPORTS)
        raise EvidenceValidationError(
            f"{kind} viewport matrix mismatch (missing={missing}, extra={extra})."
        )
    return len(viewports)


def _validate_checks(
    value: Any,
    required: Sequence[str],
    label: str,
    require_all_pass: bool,
) -> None:
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"{label} checks must be an object.")
    missing = sorted(set(required) - set(value))
    if missing:
        raise EvidenceValidationError(f"{label} is missing checks: {missing}.")
    for name in required:
        result = value[name]
        if type(result) is not bool:
            raise EvidenceValidationError(f"{label} check {name!r} must be boolean.")
        if require_all_pass and not result:
            raise EvidenceValidationError(f"{label} check {name!r} did not pass.")


def _validated_file(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidenceValidationError(f"{label} path must be non-empty.")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvidenceValidationError(f"{label} path must stay project-relative.")
    candidate = root / relative
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise EvidenceValidationError(f"{label} path escapes the project.") from error
    if candidate.is_symlink() or not candidate.is_file():
        raise EvidenceValidationError(f"{label} file is missing or unsafe: {value}.")
    return candidate


def _validate_hash(path: Path, value: Any, label: str) -> None:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise EvidenceValidationError(f"{label} SHA-256 is malformed.")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != value:
        raise EvidenceValidationError(
            f"{label} SHA-256 mismatch (expected {value}, actual {actual})."
        )


def _find_project_root(evidence_path: Path) -> Path:
    for candidate in (evidence_path.parent, *evidence_path.parents):
        if (candidate / "compound-gpid.md").is_file():
            return candidate
    return evidence_path.parent


def _reject_source_body(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in {"sourcebody", "sourcecontent", "markdownbody"}:
                raise EvidenceValidationError(
                    "Evidence must not contain canonical source body content."
                )
            _reject_source_body(child)
    elif isinstance(value, list):
        for child in value:
            _reject_source_body(child)
