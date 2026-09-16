"""Created 2026-08-12. Format parser dispatch contracts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import zipfile

from ..schemas import SourceUnit


class ParserInputError(ValueError):
    """Signal malformed, unsupported, or unavailable local parser input.

    Args:
        message: Human-readable parser failure.

    Returns:
        An exception describing why parsing did not proceed.

    Example:
        ``raise ParserInputError("unsupported resource extension")``.
    """


@dataclass(frozen=True)
class ParsedDocument:
    """Bundle parsed source units with parser provenance and uncertainty.

    Args:
        format: Normalized source format.
        parser_profile: Stable parser profile identifier.
        parser_version: Exact parser/runtime version string.
        units: Typed parsed source units.
        warnings: Explicit parser warnings.
        requires_ocr: Whether an image-only PDF needs the OCR path.

    Returns:
        An immutable parsed document result.

    Example:
        ``parsed.units`` supplies source records for indexing.
    """

    format: str
    parser_profile: str
    parser_version: str
    units: list[SourceUnit]
    warnings: list[str]
    requires_ocr: bool = False


def parse_document(path: Path, source_version_id: str) -> ParsedDocument:
    """Dispatch one local supported resource to its deterministic parser.

    Args:
        path: Existing local resource path.
        source_version_id: Immutable source-version identifier.

    Returns:
        Parsed document with typed source units and parser metadata.

    Raises:
        ParserInputError: If the extension is unsupported or parsing fails.

    Example:
        ``parse_document(Path("paper.html"), "source-version:1")``.
    """
    if not source_version_id:
        raise ParserInputError("A source version is required for parsing")
    suffix = Path(path).suffix.lower()
    try:
        if suffix in {".md", ".markdown"}:
            from .markdown import parse_markdown

            return ParsedDocument(
                format="markdown",
                parser_profile="markdown-v1",
                parser_version="stdlib",
                units=parse_markdown(Path(path).read_text(encoding="utf-8"), source_version_id),
                warnings=[],
            )
        if suffix == ".pdf":
            return parse_pdf(path, source_version_id)
        if suffix == ".docx":
            return parse_docx(path, source_version_id)
        if suffix in {".tex", ".latex"}:
            return parse_latex(path, source_version_id)
        if suffix in {".html", ".htm"}:
            return parse_html(path, source_version_id)
    except ParserInputError:
        raise
    except (OSError, UnicodeError, ValueError, KeyError, IndexError, zipfile.BadZipFile) as error:
        raise ParserInputError(f"Unable to parse {suffix or 'resource'}: {error}") from error
    raise ParserInputError(f"unsupported resource extension: {suffix or '<none>'}")


def parse_pdf(path: Path, source_version_id: str) -> ParsedDocument:
    """Parse PDF text pages and expose image-only pages for OCR.

    Args:
        path: Existing local PDF path.
        source_version_id: Immutable source-version identifier.

    Returns:
        PDF page units with typed page locators.

    Raises:
        ParserInputError: If pypdf is unavailable, the PDF is encrypted, or malformed.

    Example:
        ``parse_pdf(Path("paper.pdf"), "source-version:pdf")``.
    """
    try:
        import pypdf
        from pypdf import PdfReader
    except ImportError as error:
        raise ParserInputError("PDF parser capability pypdf is unavailable") from error
    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            raise ParserInputError("PDF is encrypted and cannot be parsed locally")
        units: list[SourceUnit] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            from ..identity import make_source_unit_id, text_fingerprint
            from ..schemas import LocatorKind, TypedLocator

            fingerprint = text_fingerprint(text)
            locator = TypedLocator(
                kind=LocatorKind.PDF_TEXT,
                page=page_number,
                line_start=1,
                line_end=max(1, len(text.splitlines())),
                unit_fingerprint=fingerprint,
            )
            units.append(
                SourceUnit(
                    source_unit_id=make_source_unit_id(source_version_id, locator, fingerprint),
                    source_version_id=source_version_id,
                    locator=locator,
                    text=text,
                    parser_metadata={"parser": "pypdf", "page": str(page_number)},
                )
            )
        requires_ocr = not units and len(reader.pages) > 0
        warnings = ["PDF has no text layer; explicit OCR is required"] if requires_ocr else []
        return ParsedDocument(
            format="pdf",
            parser_profile="pdf-pypdf-v1",
            parser_version=str(getattr(pypdf, "__version__", "unknown")),
            units=units,
            warnings=warnings,
            requires_ocr=requires_ocr,
        )
    except ParserInputError:
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        IndexError,
        pypdf.errors.PdfReadError,
        pypdf.errors.PdfStreamError,
    ) as error:
        raise ParserInputError(f"Unable to parse PDF: {error}") from error


def parse_docx(path: Path, source_version_id: str) -> ParsedDocument:
    """Parse DOCX paragraphs and table rows from the local XML package.

    Args:
        path: Existing local DOCX path.
        source_version_id: Immutable source-version identifier.

    Returns:
        DOCX paragraph/table source units with heading context.

    Raises:
        ParserInputError: If the package or document XML is malformed.

    Example:
        ``parse_docx(Path("paper.docx"), "source-version:docx")``.
    """
    import xml.etree.ElementTree as element_tree

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
        root = element_tree.fromstring(xml_bytes)
    except (OSError, KeyError, ValueError, zipfile.BadZipFile) as error:
        raise ParserInputError(f"Unable to parse DOCX: {error}") from error
    from ..identity import make_source_unit_id, text_fingerprint
    from ..schemas import LocatorKind, TypedLocator

    units: list[SourceUnit] = []
    heading_path: list[str] = []
    block = 0
    body = root.find(f".//{namespace}body")
    if body is None:
        raise ParserInputError("Unable to parse DOCX: document body is missing")
    for child in list(body):
        tag = child.tag.rsplit("}", 1)[-1]
        block += 1
        text = " ".join(item.text or "" for item in child.iter(f"{namespace}t")).strip()
        if not text:
            continue
        style = child.find(f"./{namespace}pPr/{namespace}pStyle")
        style_value = style.attrib.get(f"{namespace}val", "") if style is not None else ""
        if tag == "p":
            unit_type = "prose"
            review_required = False
            if style_value.lower().startswith("heading"):
                heading_path = [text]
            locator_kind = LocatorKind.DOCX_PARAGRAPH
        elif tag == "tbl":
            unit_type = "table"
            review_required = True
            locator_kind = LocatorKind.DOCX_TABLE_ROW
        else:
            continue
        fingerprint = text_fingerprint(text)
        locator = TypedLocator(
            kind=locator_kind,
            block=block,
            unit_fingerprint=fingerprint,
        )
        units.append(
            SourceUnit(
                source_unit_id=make_source_unit_id(source_version_id, locator, fingerprint),
                source_version_id=source_version_id,
                locator=locator,
                text=text,
                heading_path=list(heading_path),
                unit_type=unit_type,
                review_required=review_required,
                parser_metadata={"parser": "stdlib-docx-xml", "style": style_value},
            )
        )
    return ParsedDocument(
        format="docx",
        parser_profile="docx-stdlib-xml-v1",
        parser_version="stdlib",
        units=units,
        warnings=[],
    )


def parse_latex(path: Path, source_version_id: str) -> ParsedDocument:
    """Parse LaTeX prose and equation blocks without executing TeX.

    Args:
        path: Existing local LaTeX path.
        source_version_id: Immutable source-version identifier.

    Returns:
        LaTeX source units with heading and equation uncertainty metadata.

    Raises:
        ParserInputError: If an equation environment is unclosed.

    Example:
        ``parse_latex(Path("paper.tex"), "source-version:latex")``.
    """
    import re

    text = Path(path).read_text(encoding="utf-8")
    heading_path: list[str] = []
    units: list[SourceUnit] = []
    block = 0
    equation_pattern = re.compile(r"\\begin\{(equation\*?|align\*?)\}(.*?)\\end\{\1\}", re.S)
    consumed: list[tuple[int, int]] = []
    for match in equation_pattern.finditer(text):
        consumed.append((match.start(), match.end()))
    if text.count("\\begin{equation") != text.count("\\end{equation"):
        raise ParserInputError("Unable to parse LaTeX: unclosed equation environment")
    segments: list[tuple[str, bool]] = []
    cursor = 0
    for start, end in consumed:
        if text[cursor:start].strip():
            segments.append((text[cursor:start], False))
        segments.append((text[start:end], True))
        cursor = end
    if text[cursor:].strip():
        segments.append((text[cursor:], False))
    from ..identity import make_source_unit_id, text_fingerprint
    from ..schemas import LocatorKind, TypedLocator

    for segment, is_equation in segments:
        lines = [line.strip() for line in segment.splitlines() if line.strip()]
        if not lines:
            continue
        heading_matches = re.findall(r"\\(?:section|subsection|subsubsection)\{([^}]*)\}", segment)
        if heading_matches:
            heading_path = [heading_matches[-1].strip()]
        unit_text = "\n".join(lines)
        block += 1
        fingerprint = text_fingerprint(unit_text)
        locator = TypedLocator(
            kind=LocatorKind.LATEX_BLOCK,
            block=block,
            anchor=heading_path[-1] if heading_path else None,
            unit_fingerprint=fingerprint,
        )
        units.append(
            SourceUnit(
                source_unit_id=make_source_unit_id(source_version_id, locator, fingerprint),
                source_version_id=source_version_id,
                locator=locator,
                text=unit_text,
                heading_path=list(heading_path),
                unit_type="equation" if is_equation else "prose",
                review_required=is_equation,
                parser_metadata={"parser": "stdlib-latex", "equation": str(is_equation).lower()},
            )
        )
    return ParsedDocument(
        format="latex",
        parser_profile="latex-stdlib-v1",
        parser_version="stdlib",
        units=units,
        warnings=[],
    )


def parse_html(path: Path, source_version_id: str) -> ParsedDocument:
    """Parse HTML text containers as untrusted data with structural context.

    Args:
        path: Existing local HTML path.
        source_version_id: Immutable source-version identifier.

    Returns:
        HTML source units with headings, anchors, and table review flags.

    Raises:
        ParserInputError: If the local HTML cannot be decoded.

    Example:
        ``parse_html(Path("paper.html"), "source-version:html")``.
    """
    from html.parser import HTMLParser

    class _HTMLUnitParser(HTMLParser):
        """Collect visible structural HTML blocks without executing markup."""

        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.heading_path: list[str] = []
            self.current_tag: Optional[str] = None
            self.current_anchor: Optional[str] = None
            self.current_text: list[str] = []
            self.current_table = False
            self.blocks: list[tuple[str, list[str], Optional[str], bool]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
            """Collect the start of one visible structural element.

            Args:
                tag: HTML element name supplied by ``HTMLParser``.
                attrs: Element attributes supplied by ``HTMLParser``.

            Returns:
                ``None``; parser state is updated for matching character data.

            Example:
                ``parser.handle_starttag("h1", [("id", "results")])``.
            """
            if tag in {"h1", "h2", "h3", "p", "li", "caption", "td", "th"}:
                self.current_tag = tag
                self.current_text = []
                self.current_anchor = dict(attrs).get("id")
                self.current_table = tag in {"td", "th", "caption"}

        def handle_data(self, data: str) -> None:
            """Collect character data for the active structural element.

            Args:
                data: Text fragment supplied by ``HTMLParser``.

            Returns:
                ``None``; data is buffered until the element closes.

            Example:
                ``parser.handle_data("The rate fell.")``.
            """
            if self.current_tag is not None:
                self.current_text.append(data)

        def handle_endtag(self, tag: str) -> None:
            """Finalize one visible structural element as a source block.

            Args:
                tag: HTML element name supplied by ``HTMLParser``.

            Returns:
                ``None``; completed block metadata is appended when non-empty.

            Example:
                ``parser.handle_endtag("p")`` finalizes a paragraph block.
            """
            if tag != self.current_tag:
                return
            text = " ".join("".join(self.current_text).split())
            if text:
                if tag.startswith("h"):
                    self.heading_path = [text]
                self.blocks.append((text, list(self.heading_path), self.current_anchor, self.current_table))
            self.current_tag = None
            self.current_text = []
            self.current_anchor = None
            self.current_table = False

    parser = _HTMLUnitParser()
    try:
        parser.feed(Path(path).read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError, ValueError) as error:
        raise ParserInputError(f"Unable to parse HTML: {error}") from error
    from ..identity import make_source_unit_id, text_fingerprint
    from ..schemas import LocatorKind, TypedLocator

    units: list[SourceUnit] = []
    for block, (unit_text, heading_path, anchor, is_table) in enumerate(parser.blocks, start=1):
        fingerprint = text_fingerprint(unit_text)
        locator = TypedLocator(
            kind=LocatorKind.HTML_BLOCK,
            block=block,
            anchor=anchor or (heading_path[-1] if heading_path else None),
            unit_fingerprint=fingerprint,
        )
        units.append(
            SourceUnit(
                source_unit_id=make_source_unit_id(source_version_id, locator, fingerprint),
                source_version_id=source_version_id,
                locator=locator,
                text=unit_text,
                heading_path=heading_path,
                unit_type="table" if is_table else "prose",
                review_required=is_table,
                parser_metadata={"parser": "stdlib-html"},
            )
        )
    return ParsedDocument(
        format="html",
        parser_profile="html-stdlib-v1",
        parser_version="stdlib",
        units=units,
        warnings=[],
    )
