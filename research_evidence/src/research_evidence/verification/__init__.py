"""Created 2026-08-12. Deterministic source and quotation verification."""

from .basic import VerificationResult, normalize_quote, verify_evidence, verify_evidence_context
from .confidence import ConfidenceDecision, decide_confidence

__all__ = [
	"ConfidenceDecision",
	"VerificationResult",
	"decide_confidence",
	"normalize_quote",
	"verify_evidence",
	"verify_evidence_context",
]
