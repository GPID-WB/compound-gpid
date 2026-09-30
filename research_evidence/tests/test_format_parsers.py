"""Created 2026-08-12. Tests for deterministic Phase 2 format parsers."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import zipfile

import pytest

from research_evidence.parsers import ParserInputError
from research_evidence.parsers.document import parse_docx, parse_document, parse_html, parse_latex, parse_pdf
from research_evidence.config import RuntimeSettings
from research_evidence.source_records import ingest_resource


def _write_minimal_pdf(path: Path, text: str) -> None:
    """Write a minimal one-page PDF fixture with a text or empty stream."""
    stream = f"BT\n/F1 12 Tf\n72 720 Td\n({text}) Tj\nET\n".encode("ascii") if text else b""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{number} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(bytes(content))


def _write_docx(path: Path) -> None:
    """Write a minimal DOCX package with a heading, paragraph, and table."""
    document = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Results</w:t></w:r></w:p>
<w:p><w:r><w:t>The rate fell.</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Year</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Rate</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>"""
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document)


def test_pdf_parser_preserves_page_locator_and_determinism(tmp_path: Path) -> None:
    """Parse text-layer PDF pages into deterministic typed source units."""
    path = tmp_path / "paper.pdf"
    _write_minimal_pdf(path, "Hello PDF")

    first = parse_pdf(path, "source-version:pdf")
    second = parse_pdf(path, "source-version:pdf")

    assert first.requires_ocr is False
    assert first.units[0].locator.kind.value == "pdf_text"
    assert first.units[0].locator.page == 1
    assert "Hello PDF" in first.units[0].text
    assert first.units == second.units


def test_pdf_without_text_layer_requests_explicit_ocr(tmp_path: Path) -> None:
    """Represent an image-only page as an explicit OCR requirement."""
    path = tmp_path / "scan.pdf"
    _write_minimal_pdf(path, "")

    parsed = parse_pdf(path, "source-version:scan")

    assert parsed.requires_ocr is True
    assert parsed.units == []
    assert "text layer" in parsed.warnings[0]


def test_docx_parser_preserves_paragraph_and_table_row_context(tmp_path: Path) -> None:
    """Parse DOCX XML without executing document content or losing table semantics."""
    path = tmp_path / "paper.docx"
    _write_docx(path)

    parsed = parse_docx(path, "source-version:docx")

    assert [unit.locator.kind.value for unit in parsed.units] == [
        "docx_paragraph",
        "docx_paragraph",
        "docx_table_row",
    ]
    assert parsed.units[1].heading_path == ["Results"]
    assert parsed.units[2].review_required is True
    assert parsed.units[2].unit_type == "table"


def test_latex_parser_marks_equations_review_required(tmp_path: Path) -> None:
    """Parse LaTeX blocks while keeping equations out of ordinary prose approval."""
    path = tmp_path / "paper.tex"
    path.write_text(
        "\\section{Methods}\n\nA sentence.\n\n\\begin{equation}\nx = y\n\\end{equation}\n",
        encoding="utf-8",
    )

    parsed = parse_latex(path, "source-version:latex")

    assert parsed.units[0].heading_path == ["Methods"]
    assert parsed.units[-1].unit_type == "equation"
    assert parsed.units[-1].review_required is True
    assert parsed.units[-1].locator.kind.value == "latex_block"


def test_html_parser_preserves_headings_and_tables(tmp_path: Path) -> None:
    """Parse HTML as data and retain heading, anchor, and table review context."""
    path = tmp_path / "paper.html"
    path.write_text(
        '<h1 id="results">Results</h1><p>The rate fell.</p><table><tr><td>Year</td></tr></table>',
        encoding="utf-8",
    )

    parsed = parse_html(path, "source-version:html")

    assert parsed.units[0].heading_path == ["Results"]
    assert parsed.units[0].locator.anchor == "results"
    assert parsed.units[-1].unit_type == "table"
    assert parsed.units[-1].review_required is True


def test_dispatch_rejects_malformed_and_unsupported_inputs(tmp_path: Path) -> None:
    """Fail clearly for malformed PDFs and unsupported resource extensions."""
    malformed = tmp_path / "bad.pdf"
    malformed.write_bytes(b"not a PDF")
    with pytest.raises(ParserInputError, match="PDF"):
        parse_document(malformed, "source-version:bad")

    unsupported = tmp_path / "data.csv"
    unsupported.write_text("a,b", encoding="utf-8")
    with pytest.raises(ParserInputError, match="unsupported"):
        parse_document(unsupported, "source-version:bad")


def test_source_record_ingestion_dispatches_non_markdown_formats(tmp_path: Path) -> None:
    """Create a versioned source record from a configured local HTML resource."""
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "paper.html").write_text("<h1>Results</h1><p>The rate fell.</p>", encoding="utf-8")
    settings = RuntimeSettings.from_paths(tmp_path, resources)

    parsed = ingest_resource(settings, "paper.html")

    assert parsed.source_version.parser_profile == "html-stdlib-v1"
    assert parsed.source_version.parser_version == "stdlib"
    assert parsed.units[0].text == "Results"
