"""Tests for machine-validated Open Design evidence matrices."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from artifact_views.evidence import (
    REQUIRED_OPEN_DESIGN_PATH,
    EvidenceValidationError,
    validate_evidence_file,
)

VIEWPORTS = ((1440, 900), (768, 1024), (390, 844))
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
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matrix(tmp_path: Path) -> Path:
    artifacts = []
    for kind in ("brainstorm", "plan"):
        source = tmp_path / f"{kind}.md"
        view = tmp_path / f"{kind}.html"
        source.write_text(f"# {kind}\n", encoding="utf-8")
        view.write_text(f"<!doctype html><title>{kind}</title>\n", encoding="utf-8")
        viewports = []
        for width, height in VIEWPORTS:
            screenshot = tmp_path / f"{kind}-{width}x{height}.png"
            screenshot.write_bytes(b"png")
            viewports.append(
                {
                    "width": width,
                    "height": height,
                    "checks": {name: True for name in VIEWPORT_CHECKS},
                    "screenshot": screenshot.name,
                }
            )
        print_preview = tmp_path / f"{kind}-print.pdf"
        print_preview.write_bytes(b"pdf")
        artifacts.append(
            {
                "kind": kind,
                "sourcePath": source.name,
                "sourceSha256": _sha(source),
                "viewPath": view.name,
                "viewSha256": _sha(view),
                "viewports": viewports,
                "checks": {name: True for name in ARTIFACT_CHECKS},
                "printPreviewArtifact": print_preview.name,
            }
        )
    evidence = {
        "schemaVersion": 1,
        "generatedAt": "2026-07-31T12:30:00Z",
        "openDesign": {
            "executable": REQUIRED_OPEN_DESIGN_PATH,
            "version": "open-design-local",
        },
        "artifacts": artifacts,
        "observations": [{"name": "extra", "passed": False}],
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return path


def test_complete_two_artifact_matrix_passes(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)

    result = validate_evidence_file(evidence, require_all_pass=True)

    assert result.artifact_count == 2
    assert result.viewport_count == 6


def test_evidence_order_and_extra_observations_do_not_affect_validity(
    tmp_path: Path,
) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["artifacts"].reverse()
    for artifact in data["artifacts"]:
        artifact["viewports"].reverse()
        artifact["checks"]["additionalObservation"] = False
    evidence.write_text(json.dumps(data), encoding="utf-8")

    validate_evidence_file(evidence, require_all_pass=True)


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_viewport",
        "missing_check",
        "missing_file",
        "hash_mismatch",
        "false_required_result",
        "wrong_open_design",
    ),
)
def test_incomplete_or_false_evidence_fails(tmp_path: Path, mutation: str) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    artifact = data["artifacts"][0]
    if mutation == "missing_viewport":
        artifact["viewports"].pop()
    elif mutation == "missing_check":
        artifact["checks"].pop("zoom200")
    elif mutation == "missing_file":
        artifact["viewports"][0]["screenshot"] = "absent.png"
    elif mutation == "hash_mismatch":
        artifact["viewSha256"] = "0" * 64
    elif mutation == "false_required_result":
        artifact["viewports"][0]["checks"]["noOverlap"] = False
    elif mutation == "wrong_open_design":
        data["openDesign"]["executable"] = "/usr/bin/od"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceValidationError):
        validate_evidence_file(evidence, require_all_pass=True)


def test_duplicate_artifact_kind_fails(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["artifacts"][1]["kind"] = "brainstorm"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceValidationError, match="exactly one"):
        validate_evidence_file(evidence, require_all_pass=True)


def test_source_body_is_forbidden_from_evidence(tmp_path: Path) -> None:
    evidence = _matrix(tmp_path)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["artifacts"][0]["sourceBody"] = "canonical source body"
    evidence.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(EvidenceValidationError, match="source body"):
        validate_evidence_file(evidence, require_all_pass=True)
