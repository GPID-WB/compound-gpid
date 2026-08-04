"""Tests for schema-2 Playwright/Chromium/axe evidence validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from artifact_views.evidence_schema2 import (
    EvidenceSchema2Error,
    validate_schema2_evidence,
)

VIEWPORTS = ((390, 844), (768, 1024), (1024, 768), (1440, 900), (1920, 1080))
VIEWPORT_CHECKS = (
    "nonblank",
    "noHorizontalOverflow",
    "noOverlap",
    "navigationReachable",
    "firstViewportIdentity",
)
ARTIFACT_CHECKS = (
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
)

CELLS = (
    ("brainstorm", "reference"),
    ("brainstorm", "editorial"),
    ("plan", "reference"),
    ("plan", "editorial"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matrix(tmp_path: Path) -> Path:
    """Build a valid schema-2 evidence matrix in a temp directory."""
    cells = []
    for i, (doc_type, theme) in enumerate(CELLS):
        source = tmp_path / f"fixture-{doc_type}.md"
        view = tmp_path / f"{doc_type}-{theme}.html"
        if not source.exists():
            source.write_text(f"# {doc_type} ({theme})\n", encoding="utf-8")
        view.write_text(f"<!doctype html><title>{doc_type}/{theme}</title>\n", encoding="utf-8")

        viewports = []
        for width, height in VIEWPORTS:
            screenshot = tmp_path / f"{doc_type}-{theme}-{width}x{height}.png"
            screenshot.write_bytes(b"png")
            viewports.append(
                {
                    "width": width,
                    "height": height,
                    "checks": {
                        name: (True if name != "firstViewportIdentity" else width == VIEWPORTS[0][0])
                        for name in VIEWPORT_CHECKS
                    },
                    "screenshot": screenshot.name,
                    "screenshotSha256": _sha(screenshot),
                }
            )

        print_preview = tmp_path / f"{doc_type}-{theme}-print.pdf"
        print_preview.write_bytes(b"pdf")

        cells.append(
            {
                "documentType": doc_type,
                "theme": theme,
                "sourcePath": source.name,
                "sourceSha256": _sha(source),
                "viewPath": view.name,
                "viewSha256": _sha(view),
                "viewports": viewports,
                "checks": {
                    name: (True if name not in ("consoleErrors", "axeViolations") else 0)
                    for name in ARTIFACT_CHECKS
                },
                "printPreviewArtifact": print_preview.name,
                "printPreviewSha256": _sha(print_preview),
            }
        )

    evidence = {
        "schemaVersion": 2,
        "generatedAt": "2026-08-03T12:00:00Z",
        "producer": {
            "tool": "playwright",
            "version": "1.52.0",
            "browser": "chromium",
            "axeCoreVersion": "4.10.3",
        },
        "cells": cells,
    }
    path = tmp_path / "evidence-schema2.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return path


def test_complete_four_cell_matrix_passes(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)

    result = validate_schema2_evidence(evidence, require_all_pass=True)

    assert result.cell_count == 4
    assert result.viewport_count == 20  # 4 cells × 5 viewports


def test_requires_schema_version_2(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["schemaVersion"] = 1
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="schemaVersion must be 2"):
        validate_schema2_evidence(evidence)


def test_rejects_invalid_timestamp(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["generatedAt"] = "2026-02-30T12:00:00Z"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="valid UTC timestamp"):
        validate_schema2_evidence(evidence)


def test_rejects_nonzero_error_counts_in_strict_mode(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["checks"]["axeViolations"] = 1
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="axeViolations.*zero"):
        validate_schema2_evidence(evidence, require_all_pass=True)


def test_rejects_schema1_fields(tmp_path: Path) -> None:
    """Schema 1 fields (openDesign, artifacts) must not appear in schema 2."""
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["artifacts"] = data.pop("cells")
    data["openDesign"] = {"executable": "/usr/bin/od", "version": "1.0"}
    evidence.write_text(json.dumps(data), encoding="utf-8")

    # Schema 2 validator rejects "cells" missing
    with pytest.raises(EvidenceSchema2Error):
        validate_schema2_evidence(evidence)


def test_cell_uses_document_type_not_kind(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    # Replace documentType with kind (schema 1 style)
    for cell in data["cells"]:
        cell["kind"] = cell.pop("documentType")
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error):
        validate_schema2_evidence(evidence)


def test_deterministic_cell_ordering(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    # Reverse cells — should fail because order is deterministic
    data["cells"].reverse()
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="Cell 0 must be"):
        validate_schema2_evidence(evidence)


def test_wrong_number_of_cells(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"].pop()  # 3 cells instead of 4
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="exactly 4 cells"):
        validate_schema2_evidence(evidence)


def test_duplicate_cell_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    # Duplicate the first cell as the last cell
    data["cells"][3] = dict(data["cells"][0])
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="Cell 3 must be"):
        validate_schema2_evidence(evidence)


def test_missing_viewport_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["viewports"].pop()  # 4 viewports
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="viewport matrix mismatch"):
        validate_schema2_evidence(evidence)


def test_missing_check_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["checks"].pop("zoom200")
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="missing checks"):
        validate_schema2_evidence(evidence)


def test_missing_file_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["viewports"][0]["screenshot"] = "absent.png"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="missing or unsafe"):
        validate_schema2_evidence(evidence)


def test_hash_mismatch_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["viewSha256"] = "0" * 64
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="SHA-256 mismatch"):
        validate_schema2_evidence(evidence)


def test_false_required_result_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["viewports"][0]["checks"]["noOverlap"] = False
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="did not pass"):
        validate_schema2_evidence(evidence, require_all_pass=True)


def test_source_body_rejected(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["sourceBody"] = "canonical source body"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="source body"):
        validate_schema2_evidence(evidence)


def test_wrong_producer_tool_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["producer"]["tool"] = "puppeteer"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="producer.tool must be 'playwright'"):
        validate_schema2_evidence(evidence)


def test_wrong_browser_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["producer"]["browser"] = "firefox"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="producer.browser must be 'chromium'"):
        validate_schema2_evidence(evidence)


def test_schema1_unchanged_by_schema2(tmp_path: Path) -> None:
    """Verify schema 1 is not affected by schema 2 additions."""
    from artifact_views.evidence import validate_evidence_file

    # Build a schema 1 matrix
    from artifact_views.evidence import REQUIRED_OPEN_DESIGN_PATH

    artifacts = []
    for kind in ("brainstorm", "plan"):
        source = tmp_path / f"{kind}.md"
        view = tmp_path / f"{kind}.html"
        source.write_text(f"# {kind}\n", encoding="utf-8")
        view.write_text(f"<!doctype html><title>{kind}</title>\n", encoding="utf-8")
        viewports = []
        for width, height in ((1440, 900), (768, 1024), (390, 844)):
            ss = tmp_path / f"{kind}-{width}x{height}.png"
            ss.write_bytes(b"png")
            viewports.append(
                {
                    "width": width,
                    "height": height,
                    "checks": {
                        "nonblank": True,
                        "noHorizontalOverflow": True,
                        "noOverlap": True,
                        "navigationReachable": True,
                        "firstViewportIdentity": True,
                    },
                    "screenshot": ss.name,
                }
            )
        pp = tmp_path / f"{kind}-print.pdf"
        pp.write_bytes(b"pdf")
        artifacts.append(
            {
                "kind": kind,
                "sourcePath": source.name,
                "sourceSha256": _sha(source),
                "viewPath": view.name,
                "viewSha256": _sha(view),
                "viewports": viewports,
                "checks": {
                    "offlineLoad": True,
                    "printPreview": True,
                    "keyboardOrder": True,
                    "visibleFocus": True,
                    "zoom200": True,
                    "contrast": True,
                    "reducedMotion": True,
                    "longDocumentOrientation": True,
                    "completeProvenance": True,
                },
                "printPreviewArtifact": pp.name,
            }
        )
    evidence1 = {
        "schemaVersion": 1,
        "generatedAt": "2026-08-03T12:00:00Z",
        "openDesign": {
            "executable": REQUIRED_OPEN_DESIGN_PATH,
            "version": "open-design-local",
        },
        "artifacts": artifacts,
    }
    path1 = tmp_path / "evidence-v1.json"
    path1.write_text(json.dumps(evidence1, indent=2) + "\n", encoding="utf-8")

    validate_evidence_file(path1, require_all_pass=True)


def test_schema2_does_not_accept_schema1_even_if_valid(tmp_path: Path) -> None:
    """Schema 2 validator must reject schema 1 input."""
    from artifact_views.evidence import REQUIRED_OPEN_DESIGN_PATH

    evidence1 = {
        "schemaVersion": 1,
        "generatedAt": "2026-08-03T12:00:00Z",
        "openDesign": {
            "executable": REQUIRED_OPEN_DESIGN_PATH,
            "version": "open-design-local",
        },
        "artifacts": [],
    }
    path = tmp_path / "evidence-v1.json"
    path.write_text(json.dumps(evidence1, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(EvidenceSchema2Error, match="schemaVersion must be 2"):
        validate_schema2_evidence(path)


def test_console_errors_and_axe_violations_accept_integers(tmp_path: Path) -> None:
    """consoleErrors and axeViolations are integer counts, not booleans."""
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["cells"][0]["checks"]["consoleErrors"] = 3
    data["cells"][0]["checks"]["axeViolations"] = 1
    evidence.write_text(json.dumps(data), encoding="utf-8")

    # Should pass — non-boolean allowed for these two integer fields
    result = validate_schema2_evidence(evidence)
    assert result.cell_count == 4


# ---------------------------------------------------------------------------
# Binary exclusion sentinel tests
# ---------------------------------------------------------------------------


def test_evidence_html_excluded_from_model_context() -> None:
    """Evidence HTML bodies are excluded from model context."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/brainstorm-reference.html"
    )
    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/plan-editorial.html"
    )


def test_evidence_screenshots_excluded_from_model_context() -> None:
    """Evidence screenshot PNGs are excluded from model context."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/brainstorm-reference-390x844.png"
    )
    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/plan-editorial-1920x1080.png"
    )


def test_evidence_pdfs_excluded_from_model_context() -> None:
    """Evidence print PDFs are excluded from model context."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/brainstorm-reference-print.pdf"
    )
    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/plan-editorial-print.pdf"
    )


def test_evidence_manifest_excluded_from_model_context() -> None:
    """Evidence manifest JSON is excluded from model context."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/evidence-schema2.json"
    )


def test_evidence_fixtures_are_included_in_model_context() -> None:
    """Evidence fixture markdown sources are included in model context."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    assert not is_model_context_excluded(
        ".cg-docs/evidence-fixtures/fixture-brainstorm.md"
    )
    assert not is_model_context_excluded(
        ".cg-docs/evidence-fixtures/fixture-plan.md"
    )


def test_evidence_work_report_attestations_are_included() -> None:
    """Manual attestation work reports are included in model context."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    assert not is_model_context_excluded(
        ".cg-docs/work-reports/2026-08-04-editorial-theme-manual-attestations.json"
    )


def test_evidence_paths_do_not_escape_views_prefix() -> None:
    """All evidence paths stay under .cg-docs/views/evidence/."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from cg_audit_context import is_model_context_excluded

    # Paths that look like evidence but aren't under views/ should NOT be excluded
    assert not is_model_context_excluded(
        ".cg-docs/evidence-fixtures/fixture-brainstorm.md"
    )
    # Paths under views/evidence/ should be excluded
    assert is_model_context_excluded(
        ".cg-docs/views/evidence/curated-themes/rendered/brainstorm-reference.html"
    )
    # Non-evidence views paths should also be excluded (existing behavior)
    assert is_model_context_excluded(
        ".cg-docs/views/plans/plan.html"
    )