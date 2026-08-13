"""Created 2026-08-12. Local source-format parsers."""

from .document import (
	ParsedDocument,
	ParserInputError,
	parse_docx,
	parse_document,
	parse_html,
	parse_latex,
	parse_pdf,
)
from .ocr import OCRCapabilityError, OCRProfile, OCRResult, run_ocr

__all__ = [
	"ParsedDocument",
	"ParserInputError",
	"parse_docx",
	"parse_document",
	"parse_html",
	"parse_latex",
	"parse_pdf",
	"OCRCapabilityError",
	"OCRProfile",
	"OCRResult",
	"run_ocr",
]
