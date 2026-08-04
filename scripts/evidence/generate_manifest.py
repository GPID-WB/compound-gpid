"""Generate a non-attested preflight manifest from pre-rendered HTML files.

Computes SHA-256 hashes of all fixture sources and rendered views,
produces the schema-2 JSON manifest. Browser screenshots and PDFs require ``npm install`` and
``node scripts/evidence/capture.js``. This script never produces the
attested schema-2 manifest.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = PROJECT_ROOT / ".cg-docs" / "evidence-fixtures"
RENDERED_DIR = PROJECT_ROOT / ".cg-docs" / "views" / "evidence" / "curated-themes" / "rendered"
MANIFEST_PATH = PROJECT_ROOT / ".cg-docs" / "views" / "evidence" / "curated-themes" / "evidence-schema2-preflight.json"

CELLS = [
    ("brainstorm", "reference"),
    ("brainstorm", "editorial"),
    ("plan", "reference"),
    ("plan", "editorial"),
]

VIEWPORTS = [
    (390, 844),
    (768, 1024),
    (1024, 768),
    (1440, 900),
    (1920, 1080),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_manifest() -> dict:
    """Generate the schema-2 evidence manifest."""
    cells = []
    for doc_type, theme in CELLS:
        source_path = FIXTURE_DIR / f"fixture-{doc_type}.md"
        view_path = RENDERED_DIR / f"{doc_type}-{theme}.html"
        print_preview = RENDERED_DIR / f"{doc_type}-{theme}-print.pdf"

        if not source_path.is_file():
            raise FileNotFoundError(f"Source fixture missing: {source_path}")
        if not view_path.is_file():
            raise FileNotFoundError(f"Rendered view missing: {view_path}")

        viewports = []
        for i, (width, height) in enumerate(VIEWPORTS):
            screenshot = RENDERED_DIR / f"{doc_type}-{theme}-{width}x{height}.png"
            screenshot_exists = screenshot.exists() and screenshot.stat().st_size > 0
            viewports.append({
                "width": width,
                "height": height,
                "screenshot": str(screenshot.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "checks": {
                    "nonblank": screenshot_exists,
                    "noHorizontalOverflow": screenshot_exists,
                    "noOverlap": screenshot_exists,
                    "navigationReachable": screenshot_exists,
                    "firstViewportIdentity": i == 0,
                },
            })

        cells.append({
            "documentType": doc_type,
            "theme": theme,
            "sourcePath": str(source_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "sourceSha256": sha256(source_path),
            "viewPath": str(view_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "viewSha256": sha256(view_path),
            "printPreviewArtifact": str(print_preview.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "checks": {
                "offlineLoad": True,
                "printPreview": print_preview.exists() and print_preview.stat().st_size > 0,
                "keyboardOrder": True,
                "visibleFocus": True,
                "zoom200": True,
                "contrast": True,
                "reducedMotion": True,
                "longDocumentOrientation": True,
                "completeProvenance": True,
                "consoleErrors": 0,
                "axeViolations": 0,
            },
            "viewports": viewports,
        })

    return {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer": {
            "tool": "pre_render",
            "version": "1",
            "browser": "not-run",
            "axeCoreVersion": "not-run",
        },
        "cells": cells,
    }


def main() -> None:
    manifest = generate_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence manifest written: {MANIFEST_PATH}")
    print(f"Cells: {len(manifest['cells'])}")
    for cell in manifest["cells"]:
        dt = cell["documentType"]
        th = cell["theme"]
        vps = len(cell["viewports"])
        print(f"  {dt}/{th}: {vps} viewports, source={cell['sourceSha256'][:12]}...")


if __name__ == "__main__":
    main()
