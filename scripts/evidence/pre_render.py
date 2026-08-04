"""Pre-render fixture markdown as HTML for both themes.

Produces deterministic HTML files that the Playwright capture script reads.
Uses the internal rendering pipeline directly to avoid CLI path constraints.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from artifact_views.generic_model import GENERIC_DOCUMENT_TYPE
from artifact_views.generic_parser import parse_generic_markdown
from artifact_views.generic_renderer import render_generic_document
from artifact_views.provenance import PublicationProvenance
from artifact_views.themes import get_theme
from artifact_views import __version__

FIXTURE_DIR = PROJECT_ROOT / ".cg-docs" / "evidence-fixtures"
RENDERED_DIR = PROJECT_ROOT / ".cg-docs" / "views" / "evidence" / "curated-themes" / "rendered"

FIXTURES = {
    "brainstorm": FIXTURE_DIR / "fixture-brainstorm.md",
    "plan": FIXTURE_DIR / "fixture-plan.md",
}

THEMES = ["reference", "editorial"]
FIXTURE_GENERATED_AT = datetime(2026, 8, 4, 2, 43, 19, tzinfo=timezone.utc)


def render_all() -> list[Path]:
    RENDERED_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []

    for doc_type, fixture_path in FIXTURES.items():
        if not fixture_path.is_file():
            raise FileNotFoundError(f"Required fixture not found: {fixture_path}")

        source_rel = fixture_path.relative_to(PROJECT_ROOT)
        source_bytes = fixture_path.read_bytes()
        source_text = source_bytes.decode("utf-8")
        document = parse_generic_markdown(source_text, source_rel)

        for theme_name in THEMES:
            out_name = f"{doc_type}-{theme_name}"
            out_rel = f".cg-docs/views/evidence/curated-themes/rendered/{out_name}.html"

            provenance = PublicationProvenance.from_source(
                source_path=source_rel,
                source_bytes=source_bytes,
                output_path=Path(out_rel),
                document_type=GENERIC_DOCUMENT_TYPE,
                renderer_version=__version__,
                theme_name=theme_name,
                theme_version=get_theme(theme_name).contract_version,
                generated_at=FIXTURE_GENERATED_AT,
            )

            html_bytes = render_generic_document(
                document, provenance, project_root=PROJECT_ROOT
            )
            out_path = RENDERED_DIR / f"{out_name}.html"
            out_path.write_bytes(html_bytes)
            outputs.append(out_path)
            print(f"Rendered: {out_path}")

    return outputs


if __name__ == "__main__":
    paths = render_all()
    print(f"\nRendered {len(paths)} HTML files.")
