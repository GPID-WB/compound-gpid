"""Schema 2 evidence validation for Playwright/Chromium/axe evidence matrices.

Schema 2 is the locked browser-evidence format produced by
``scripts/evidence/capture.js``. It is isolated from schema 1 (Open Design)
â€” the two schemas share no fields and are validated by separate functions.

Schema 2 cells use ``documentType`` (not ``kind``) and include a ``theme``
field. The producer metadata records the Playwright, Chromium, and axe-core
versions used during capture.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Collection, Mapping, Set, Tuple

REQUIRED_VIEWPORTS = frozenset(
    {(390, 844), (768, 1024), (1024, 768), (1440, 900), (1920, 1080)}
)
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
        "consoleErrors",
        "axeViolations",
    }
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class EvidenceSchema2Error(ValueError):
    """The schema-2 design evidence is incomplete, stale, or invalid."""


@dataclass(frozen=True)
class EvidenceSchema2Result:
    """Compact successful schema-2 evidence validation summary."""

    cell_count: int
    viewport_count: int


def validate_schema2_evidence(
    evidence_path: Path,
    *,
    require_all_pass: bool = False,
) -> EvidenceSchema2Result:
    """Validate a schema-2 Playwright/Chromium/axe evidence JSON document.

    Args:
        evidence_path: Evidence JSON path. Relative references are resolved
            from the nearest project root containing ``compound-gpid.md`` or,
            for isolated tests, from the evidence file's parent.
        require_all_pass: Require every named required result to be ``true``.

    Returns:
        Compact counts for the validated matrix.

    Raises:
        EvidenceSchema2Error: If schema, matrix coverage, hashes, files,
            or required booleans are invalid.

    Example:
        ``validate_schema2_evidence(Path('evidence-schema2.json'), require_all_pass=True)``
        validates the complete schema-2 matrix.
    """
    path = Path(evidence_path)
    if path.is_symlink() or not path.is_file():
        raise EvidenceSchema2Error(f"Evidence path is not a regular file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceSchema2Error(f"Evidence JSON is invalid: {error}") from error
    if not isinstance(data, dict):
        raise EvidenceSchema2Error("Evidence root must be a JSON object.")
    _reject_source_body(data)
    if data.get("schemaVersion") != 2:
        raise EvidenceSchema2Error("Evidence schemaVersion must be 2.")
    generated_at = data.get("generatedAt")
    if not isinstance(generated_at, str) or not _TIMESTAMP_RE.fullmatch(generated_at):
        raise EvidenceSchema2Error(
            "Evidence generatedAt must be UTC second precision."
        )
    try:
        datetime.strptime(generated_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise EvidenceSchema2Error(
            "Evidence generatedAt must be a valid UTC timestamp."
        ) from error
    _validate_producer(data.get("producer"))
    cells = data.get("cells")
    if not isinstance(cells, list):
        raise EvidenceSchema2Error("Evidence cells must be an array.")
    if len(cells) != 4:
        raise EvidenceSchema2Error(
            "Evidence must contain exactly 4 cells "
            "(brainstorm/reference, brainstorm/editorial, plan/reference, plan/editorial)."
        )
    expected_cells = [
        ("brainstorm", "reference"),
        ("brainstorm", "editorial"),
        ("plan", "reference"),
        ("plan", "editorial"),
    ]
    for i, (expected_doc, expected_theme) in enumerate(expected_cells):
        cell = cells[i]
        if not isinstance(cell, dict):
            raise EvidenceSchema2Error(f"Cell {i} must be an object.")
        actual_doc = cell.get("documentType")
        actual_theme = cell.get("theme")
        if actual_doc != expected_doc or actual_theme != expected_theme:
            raise EvidenceSchema2Error(
                f"Cell {i} must be {expected_doc}/{expected_theme}, "
                f"got {actual_doc}/{actual_theme}."
            )

    project_root = _find_project_root(path)
    viewport_count = 0
    for i, cell in enumerate(cells):
        viewport_count += _validate_cell(
            cell, i, project_root, require_all_pass=require_all_pass
        )
    return EvidenceSchema2Result(len(cells), viewport_count)


def _validate_producer(value: Any) -> None:
    if not isinstance(value, dict):
        raise EvidenceSchema2Error("producer must be an object.")
    if value.get("tool") != "playwright":
        raise EvidenceSchema2Error("producer.tool must be 'playwright'.")
    if not isinstance(value.get("version"), str) or not value["version"].strip():
        raise EvidenceSchema2Error("producer.version must be non-empty.")
    if value.get("browser") != "chromium":
        raise EvidenceSchema2Error("producer.browser must be 'chromium'.")
    if not isinstance(value.get("axeCoreVersion"), str) or not value["axeCoreVersion"].strip():
        raise EvidenceSchema2Error("producer.axeCoreVersion must be non-empty.")


def _validate_cell(
    cell: Mapping[str, Any],
    index: int,
    root: Path,
    *,
    require_all_pass: bool,
) -> int:
    label = f"cell {index} ({cell.get('documentType')}/{cell.get('theme')})"
    source = _validated_file(root, cell.get("sourcePath"), f"{label} source")
    view = _validated_file(root, cell.get("viewPath"), f"{label} view")
    _validate_hash(source, cell.get("sourceSha256"), f"{label} source")
    _validate_hash(view, cell.get("viewSha256"), f"{label} view")

    cell_checks = cell.get("checks") or {}
    print_preview_passed = cell_checks.get("printPreview", False)
    if print_preview_passed:
        print_preview = _validated_file(
            root,
            cell.get("printPreviewArtifact"),
            f"{label} print preview",
        )
        if print_preview.stat().st_size == 0:
            raise EvidenceSchema2Error(f"{label} print preview is empty.")
        _validate_hash(
            print_preview,
            cell.get("printPreviewSha256"),
            f"{label} print preview",
        )
    _validate_checks(
        cell_checks,
        REQUIRED_ARTIFACT_CHECKS,
        f"{label} artifact",
        require_all_pass,
    )

    viewports = cell.get("viewports")
    if not isinstance(viewports, list):
        raise EvidenceSchema2Error(f"{label} viewports must be an array.")
    found: Set[Tuple[int, int]] = set()
    for viewport_index, viewport in enumerate(viewports):
        if not isinstance(viewport, dict):
            raise EvidenceSchema2Error(f"{label} viewport row must be an object.")
        size = (viewport.get("width"), viewport.get("height"))
        if size in found:
            raise EvidenceSchema2Error(f"{label} has duplicate viewport {size}.")
        found.add(size)
        vp_checks = viewport.get("checks") or {}
        _validate_checks(
            vp_checks,
            REQUIRED_VIEWPORT_CHECKS,
            f"{label} viewport {size}",
            require_all_pass,
        )
        identity = viewport.get("checks", {}).get("firstViewportIdentity")
        if identity is not (viewport_index == 0):
            raise EvidenceSchema2Error(
                f"{label} viewport {size} has invalid firstViewportIdentity."
            )
        if vp_checks.get("nonblank", False):
            screenshot = _validated_file(
                root,
                viewport.get("screenshot"),
                f"{label} viewport {size} screenshot",
            )
            if screenshot.stat().st_size == 0:
                raise EvidenceSchema2Error(
                    f"{label} viewport {size} screenshot is empty."
                )
            _validate_hash(
                screenshot,
                viewport.get("screenshotSha256"),
                f"{label} viewport {size} screenshot",
            )
    if found != REQUIRED_VIEWPORTS:
        missing = sorted(REQUIRED_VIEWPORTS - found)
        extra = sorted(found - REQUIRED_VIEWPORTS)
        raise EvidenceSchema2Error(
            f"{label} viewport matrix mismatch (missing={missing}, extra={extra})."
        )
    return len(viewports)


def _validate_checks(
    value: Any,
    required: Collection[str],
    label: str,
    require_all_pass: bool,
) -> None:
    if not isinstance(value, dict):
        raise EvidenceSchema2Error(f"{label} checks must be an object.")
    missing = sorted(set(required) - set(value))
    if missing:
        raise EvidenceSchema2Error(f"{label} is missing checks: {missing}.")
    for name in required:
        result = value[name]
        if name in ("consoleErrors", "axeViolations"):
            if type(result) is not int or result < 0:
                raise EvidenceSchema2Error(
                    f"{label} check {name!r} must be a non-negative integer."
                )
            if require_all_pass and result != 0:
                raise EvidenceSchema2Error(
                    f"{label} check {name!r} must be zero."
                )
            continue
        if type(result) is not bool:
            raise EvidenceSchema2Error(f"{label} check {name!r} must be boolean.")
        if (
            require_all_pass
            and name != "firstViewportIdentity"
            and not result
        ):
            raise EvidenceSchema2Error(f"{label} check {name!r} did not pass.")


def _validated_file(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise EvidenceSchema2Error(f"{label} path must be non-empty.")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvidenceSchema2Error(f"{label} path must stay project-relative.")
    candidate = root / relative
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise EvidenceSchema2Error(f"{label} path escapes the project.") from error
    if candidate.is_symlink() or not candidate.is_file():
        raise EvidenceSchema2Error(f"{label} file is missing or unsafe: {value}.")
    return candidate


def _validate_hash(path: Path, value: Any, label: str) -> None:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise EvidenceSchema2Error(f"{label} SHA-256 is malformed.")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != value:
        raise EvidenceSchema2Error(
            f"{label} SHA-256 mismatch (expected {value}, actual {actual})."
        )


def _find_project_root(evidence_path: Path) -> Path:
    for candidate in evidence_path.parents:
        if (candidate / "compound-gpid.md").is_file():
            return candidate
    return evidence_path.parent


def _reject_source_body(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in {"sourcebody", "sourcecontent", "markdownbody"}:
                raise EvidenceSchema2Error(
                    "Evidence must not contain canonical source body content."
                )
            _reject_source_body(child)
    elif isinstance(value, list):
        for child in value:
            _reject_source_body(child)