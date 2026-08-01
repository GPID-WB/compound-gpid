"""Executable schema and Markdown grammar for workflow artifact version 1."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Tuple

ARTIFACT_SCHEMA_VERSION = 1
STATUS_METADATA_COMMENT = (
    "<!-- Valid status values: decided, in-progress, abandoned -->"
)

BLOCK_GRAMMAR: Tuple[str, ...] = (
    "atx_heading",
    "paragraph",
    "blank_line",
    "ordered_list",
    "unordered_list",
    "task_list",
    "pipe_table",
    "fenced_code",
    "blockquote",
    "thematic_break",
    "raw_html",
)

INLINE_GRAMMAR: Tuple[str, ...] = (
    "literal_text",
    "backslash_escape",
    "emphasis",
    "strong_emphasis",
    "code_span",
    "link",
    "autolink",
    "hard_line_break",
    "soft_line_break",
)

PLAN_INVARIANTS: Tuple[str, ...] = (
    "unique_requirement_ids",
    "unique_verification_ids",
    "unique_constraint_ids",
    "globally_unique_consecutive_steps",
    "unique_consecutive_phases",
    "one_phase_owner_per_phased_step",
    "declared_requirement_mappings",
    "complete_requirement_coverage",
    "declared_verification_phase_mappings",
    "required_verification_evidence",
)

ID_PATTERNS: Dict[str, str] = {
    "requirement": r"^R[1-9][0-9]*$",
    "verification": r"^V[1-9][0-9]*$",
    "constraint": r"^C[1-9][0-9]*$",
}
STANDARD_DEEP_SCOPES: FrozenSet[str] = frozenset({"Standard", "Deep"})
BRAINSTORM_SCOPES: FrozenSet[str] = frozenset(
    {"Lightweight", "Standard", "Deep", "Focused", "Extended", "Strategic"}
)
PLAN_SCOPES: FrozenSet[str] = frozenset({"Lightweight", "Standard", "Deep"})
BRAINSTORM_STATUSES: FrozenSet[str] = frozenset(
    {"decided", "in-progress", "abandoned"}
)
PLAN_STATUSES: FrozenSet[str] = frozenset({"active", "blocked", "completed"})
DEVIATION_POLICIES: FrozenSet[str] = frozenset({"ask", "autonomous", "strict"})


class ArtifactKind(str, Enum):
    """Supported canonical workflow artifact types."""

    BRAINSTORM = "brainstorm"
    PLAN = "plan"


class SchemaSupport(str, Enum):
    """Compatibility classification for an artifact schema version."""

    STRICT = "strict"
    COMPATIBLE_LEGACY = "compatible-legacy"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ArtifactSchema:
    """Immutable required fields and sections for one artifact type."""

    version: int
    kind: ArtifactKind
    required_frontmatter: Tuple[str, ...]
    required_sections: Tuple[str, ...]
    required_completion_sections: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanInvariant:
    """One deterministic invariant applied to Standard and Deep Plans."""

    name: str
    description: str


BRAINSTORM_SCHEMA = ArtifactSchema(
    version=ARTIFACT_SCHEMA_VERSION,
    kind=ArtifactKind.BRAINSTORM,
    required_frontmatter=(
        "artifact-schema-version",
        "date",
        "title",
        "status",
        "scope",
    ),
    required_sections=(
        "Context",
        "Requirements",
        "Approaches Considered",
        "Decision",
        "Next Steps",
    ),
)

PLAN_SCHEMA = ArtifactSchema(
    version=ARTIFACT_SCHEMA_VERSION,
    kind=ArtifactKind.PLAN,
    required_frontmatter=(
        "artifact-schema-version",
        "date",
        "title",
        "status",
        "scope",
        "deviation-policy",
    ),
    required_sections=(
        "Objective",
        "Context",
        "Requirements",
        "Testing Strategy",
        "Documentation Checklist",
        "Risks & Mitigations",
        "Out of Scope",
        "Completion Contract",
    ),
    required_completion_sections=(
        "Outcome",
        "Verification Surface",
        "Constraints",
        "Boundaries",
        "Iteration Policy",
        "Blocked-Stop Conditions",
    ),
)

SCHEMAS: Dict[ArtifactKind, ArtifactSchema] = {
    ArtifactKind.BRAINSTORM: BRAINSTORM_SCHEMA,
    ArtifactKind.PLAN: PLAN_SCHEMA,
}

PLAN_INVARIANT_SPECS: Tuple[PlanInvariant, ...] = (
    PlanInvariant("unique_requirement_ids", "Requirement IDs are unique."),
    PlanInvariant("unique_verification_ids", "Verification IDs are unique."),
    PlanInvariant("unique_constraint_ids", "Constraint IDs are unique."),
    PlanInvariant(
        "globally_unique_consecutive_steps",
        "Step numbers are globally unique and consecutive from one.",
    ),
    PlanInvariant(
        "unique_consecutive_phases",
        "Phase numbers are unique and consecutive from one.",
    ),
    PlanInvariant(
        "one_phase_owner_per_phased_step",
        "Every phased step has exactly one enclosing phase.",
    ),
    PlanInvariant(
        "declared_requirement_mappings",
        "Every step mapping names a declared requirement.",
    ),
    PlanInvariant(
        "complete_requirement_coverage",
        "Every requirement maps to at least one implementation step.",
    ),
    PlanInvariant(
        "declared_verification_phase_mappings",
        "Every numeric verification phase names a declared phase.",
    ),
    PlanInvariant(
        "required_verification_evidence",
        "Required verification rows contain non-empty evidence commands.",
    ),
)


def schema_for(kind: ArtifactKind) -> ArtifactSchema:
    """Return the version 1 schema for an artifact kind.

    Args:
        kind: Brainstorm or Plan artifact kind.

    Returns:
        The immutable schema registered for ``kind``.

    Raises:
        ValueError: If ``kind`` is not supported.

    Example:
        >>> schema_for(ArtifactKind.PLAN).version
        1
    """
    try:
        normalized = ArtifactKind(kind)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Unsupported artifact kind: {kind!r}") from error
    return SCHEMAS[normalized]


def schema_support(version: object) -> SchemaSupport:
    """Classify strict, legacy, and unsupported schema versions.

    Args:
        version: Parsed ``artifact-schema-version`` value, or ``None`` when
            the field is absent.

    Returns:
        The compatibility classification used by validation and rendering.

    Example:
        >>> schema_support(1) is SchemaSupport.STRICT
        True
        >>> schema_support(None) is SchemaSupport.COMPATIBLE_LEGACY
        True
    """
    if version is None:
        return SchemaSupport.COMPATIBLE_LEGACY
    if isinstance(version, bool):
        return SchemaSupport.UNSUPPORTED
    if version == ARTIFACT_SCHEMA_VERSION or version == str(
        ARTIFACT_SCHEMA_VERSION
    ):
        return SchemaSupport.STRICT
    return SchemaSupport.UNSUPPORTED


def is_non_substantive_metadata(raw_block: str) -> bool:
    """Return whether a raw block is the exact emitted status comment.

    Args:
        raw_block: Unmodified source text for one lexical raw HTML block.

    Returns:
        ``True`` only for the exact Brainstorm status metadata comment.

    Example:
        >>> is_non_substantive_metadata(STATUS_METADATA_COMMENT)
        True
    """
    return raw_block == STATUS_METADATA_COMMENT
