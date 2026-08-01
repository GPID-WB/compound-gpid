"""Renderer-independent semantic validation for workflow artifacts."""
from __future__ import annotations

from pathlib import Path
import re
from typing import List, Optional, Sequence, Tuple

from artifact_views.errors import (
    ArtifactModelError,
    ArtifactReadError,
    ArtifactSchemaError,
    ArtifactValidationError,
    ArtifactViewError,
)
from artifact_views.model import (
    ArtifactDocument,
    BrainstormDocument,
    LexicalBlock,
    PlanDocument,
    SourceSpan,
    Step,
)
from artifact_views.parser import ParsedDocument, parse_artifact, parse_pipe_table
from artifact_views.schema import (
    BRAINSTORM_SCOPES,
    BRAINSTORM_STATUSES,
    DEVIATION_POLICIES,
    ID_PATTERNS,
    PLAN_STATUSES,
    PLAN_SCOPES,
    STANDARD_DEEP_SCOPES,
    ArtifactKind,
    SchemaSupport,
    schema_for,
)

MAX_VALIDATION_ERRORS = 20
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
_LABEL_RE_TEMPLATE = r"\*\*{label}\*\*:[ \t]*(.*?)(?:\r?\n|$)"


def validate_path(
    source_path: Path,
    kind: Optional[ArtifactKind] = None,
) -> ParsedDocument:
    """Read and validate exactly one canonical Markdown artifact.

    Args:
        source_path: Path to one UTF-8 Markdown source.
        kind: Explicit artifact kind when it cannot be inferred from the path.

    Returns:
        The validated immutable typed document.

    Raises:
        ArtifactReadError: If the source cannot be read as strict UTF-8.
        ArtifactValidationError: If semantic validation fails.
        ArtifactParseError: If parsing fails before semantic validation.

    Example:
        >>> path = Path(".cg-docs/plans/example.md")
        >>> path.exists() and validate_path(path).identity.kind.value == "plan"
        False
    """
    source_path = Path(source_path)
    try:
        source = source_path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ArtifactReadError(
            "Artifact source is not valid strict UTF-8.",
            source_path=source_path,
            corrective_action="Save the Markdown file as UTF-8 and retry.",
        ) from error
    except OSError as error:
        raise ArtifactReadError(
            f"Artifact source could not be read: {error}.",
            source_path=source_path,
            corrective_action="Verify the file exists and is readable.",
        ) from error
    return validate_source(source, source_path, kind)


def validate_source(
    source: str,
    source_path: Path,
    kind: Optional[ArtifactKind] = None,
) -> ParsedDocument:
    """Parse and validate one artifact without rendering or configuration.

    Args:
        source: Unmodified Markdown decoded as strict UTF-8.
        source_path: Source path used for identity and diagnostics.
        kind: Explicit artifact kind when path inference is unavailable.

    Returns:
        The validated immutable typed document.

    Raises:
        ArtifactValidationError: If one or more independent schema checks fail.
        ArtifactParseError: If the closed grammar cannot be parsed safely.

    Example:
        >>> source = "---\ntitle: Example\n---\n# Example\n"
        >>> validate_source(source, Path("x.md"), ArtifactKind.PLAN)
        Traceback (most recent call last):
        ...
        artifact_views.errors.ArtifactValidationError: ...
    """
    try:
        document = parse_artifact(source, source_path, kind)
    except ArtifactModelError as error:
        schema_error = ArtifactSchemaError(
            error.message,
            source_path=error.source_path or Path(source_path),
            span=error.span,
            corrective_action=error.corrective_action,
        )
        raise ArtifactValidationError((schema_error,)) from error

    errors = collect_validation_errors(document)
    if errors:
        raise ArtifactValidationError(errors)
    return document


def collect_validation_errors(
    document: ArtifactDocument,
) -> Tuple[ArtifactViewError, ...]:
    """Collect a bounded set of independent semantic validation errors.

    Args:
        document: Parsed immutable Brainstorm or Plan model.

    Returns:
        Up to ``MAX_VALIDATION_ERRORS`` actionable errors in deterministic
        source/check order.

    Example:
        A document returned by :func:`validate_source` always produces ``()``.
    """
    errors: List[ArtifactViewError] = []
    schema = schema_for(document.identity.kind)

    if document.identity.schema_support is SchemaSupport.UNSUPPORTED:
        version = document.identity.schema_version
        _add_error(
            errors,
            _schema_error(
                document,
                f"Unsupported artifact schema version {version}.",
                None,
                f"Use a renderer that supports version {version}, or migrate "
                "the canonical Markdown to version 1.",
            ),
        )

    required_frontmatter = schema.required_frontmatter
    if document.identity.schema_support is SchemaSupport.COMPATIBLE_LEGACY:
        required_frontmatter = tuple(
            key for key in required_frontmatter if key != "artifact-schema-version"
        )
    for key in required_frontmatter:
        value = document.frontmatter.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Required frontmatter field {key!r} is missing or empty.",
                    None,
                    f"Add a non-empty {key}: value to the frontmatter.",
                ),
            )

    _validate_frontmatter_values(document, errors)
    _validate_required_sections(document, schema.required_sections, errors)

    if isinstance(document, BrainstormDocument):
        if not document.alternatives:
            _add_error(
                errors,
                _schema_error(
                    document,
                    "Approaches Considered must contain at least one Approach heading.",
                    _section_heading_span(document, "Approaches Considered"),
                    "Add a level-three 'Approach N: name' heading.",
                ),
            )
    elif isinstance(document, PlanDocument):
        _validate_plan(document, errors)

    return tuple(errors[:MAX_VALIDATION_ERRORS])


def _validate_frontmatter_values(
    document: ArtifactDocument,
    errors: List[ArtifactViewError],
) -> None:
    status_value = document.frontmatter.get("status")
    status = status_value.strip() if isinstance(status_value, str) else ""
    scope_value = document.frontmatter.get("scope")
    scope = scope_value.strip() if isinstance(scope_value, str) else ""
    if document.identity.kind is ArtifactKind.BRAINSTORM:
        if not isinstance(scope_value, str) or scope not in BRAINSTORM_SCOPES:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Unknown Brainstorm scope {scope_value!r}.",
                    None,
                    "Use Lightweight, Standard, Deep, Focused, Extended, or Strategic.",
                ),
            )
        if not isinstance(status_value, str) or status not in BRAINSTORM_STATUSES:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Unknown Brainstorm status {status!r}.",
                    None,
                    "Use decided, in-progress, or abandoned.",
                ),
            )
        return

    if not isinstance(scope_value, str) or scope not in PLAN_SCOPES:
        _add_error(
            errors,
            _schema_error(
                document,
                f"Unknown Plan scope {scope_value!r}.",
                None,
                "Use Lightweight, Standard, or Deep.",
            ),
        )
    if not isinstance(status_value, str) or status not in PLAN_STATUSES:
        _add_error(
            errors,
            _schema_error(
                document,
                f"Unknown Plan status {status!r}.",
                None,
                "Use active, blocked, or completed.",
            ),
        )
    deviation_value = document.frontmatter.get("deviation-policy")
    deviation = deviation_value.strip() if isinstance(deviation_value, str) else ""
    if not isinstance(deviation_value, str) or deviation not in DEVIATION_POLICIES:
        _add_error(
            errors,
            _schema_error(
                document,
                f"Unknown deviation policy {deviation_value!r}.",
                None,
                "Use ask, autonomous, or strict.",
            ),
        )


def _validate_required_sections(
    document: ArtifactDocument,
    required_sections: Sequence[str],
    errors: List[ArtifactViewError],
) -> None:
    level_two = [
        (title, block)
        for block in document.lexical_blocks
        for level, title in [_heading(block) or (0, "")]
        if level == 2
    ]
    for title in required_sections:
        matches = [block for heading_title, block in level_two if heading_title == title]
        if len(matches) != 1:
            span = matches[0].span if matches else None
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Required section must appear exactly once: {title!r} "
                    f"(found {len(matches)}).",
                    span,
                    f"Keep one level-two '## {title}' section.",
                ),
            )


def _validate_plan(
    document: PlanDocument,
    errors: List[ArtifactViewError],
) -> None:
    _validate_requirements(document, errors)
    _validate_steps_and_phases(document, errors)
    _validate_completion_contract(document, errors)


def _validate_requirements(
    document: PlanDocument,
    errors: List[ArtifactViewError],
) -> None:
    section = _section_body(document.lexical_blocks, 2, "Requirements")
    table = next((block for block in section if block.kind == "pipe_table"), None)
    if table is None:
        _add_error(
            errors,
            _schema_error(
                document,
                "Requirements section must contain a pipe table.",
                _section_heading_span(document, "Requirements"),
                "Add ID, Requirement, and Source columns.",
            ),
        )
        return
    headers, _ = parse_pipe_table(table.raw)
    missing = [name for name in ("id", "requirement", "source") if name not in headers]
    if missing:
        _add_error(
            errors,
            _schema_error(
                document,
                f"Requirements table is missing columns: {missing}.",
                table.span,
                "Add ID, Requirement, and Source headers.",
            ),
        )
    if not document.requirements:
        _add_error(
            errors,
            _schema_error(
                document,
                "Requirements table must contain at least one requirement row.",
                table.span,
                "Add a row with a unique R<number> ID.",
            ),
        )
    for requirement in document.requirements:
        if re.fullmatch(ID_PATTERNS["requirement"], requirement.identifier) is None:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Invalid requirement ID {requirement.identifier!r}.",
                    _block_span(document, requirement.source_block_id),
                    "Use IDs R1, R2, and so on.",
                ),
            )
        if not requirement.text.strip():
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Requirement {requirement.identifier!r} has no text.",
                    _block_span(document, requirement.source_block_id),
                    "Add a non-empty Requirement cell.",
                ),
            )


def _validate_steps_and_phases(
    document: PlanDocument,
    errors: List[ArtifactViewError],
) -> None:
    if not document.steps:
        _add_error(
            errors,
            _schema_error(
                document,
                "Plan must contain at least one globally numbered step.",
                None,
                "Add a '### 1. Step title' implementation step.",
            ),
        )
        return

    step_numbers = [step.number for step in document.steps]
    expected_steps = list(range(1, len(step_numbers) + 1))
    if step_numbers != expected_steps:
        _add_error(
            errors,
            _schema_error(
                document,
                f"Step numbers must be consecutive from 1; found {step_numbers}.",
                _step_span(document, document.steps[0]),
                f"Renumber steps as {expected_steps} in source order.",
            ),
        )

    phase_numbers = [phase.number for phase in document.phases]
    expected_phases = list(range(1, len(phase_numbers) + 1))
    if phase_numbers != expected_phases:
        _add_error(
            errors,
            _schema_error(
                document,
                f"Phase numbers must be consecutive from 1; found {phase_numbers}.",
                _block_span(document, document.phases[0].source_block_id)
                if document.phases
                else None,
                f"Renumber phases as {expected_phases} in source order.",
            ),
        )

    declared = {requirement.identifier for requirement in document.requirements}
    mapped = set()
    for step in document.steps:
        duplicate = _first_duplicate(step.requirement_ids)
        if duplicate is not None:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Step {step.number} maps requirement {duplicate!r} more than once.",
                    _step_span(document, step),
                    "List each requirement ID once per step.",
                ),
            )
        if not step.requirement_ids:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Step {step.number} has no requirement mapping.",
                    _step_span(document, step),
                    "Add non-empty **Requirements** metadata.",
                ),
            )
        for identifier in step.requirement_ids:
            if identifier not in declared:
                _add_error(
                    errors,
                    _schema_error(
                        document,
                        f"Step {step.number} maps unknown requirement ID "
                        f"{identifier!r}.",
                        _step_span(document, step),
                        "Declare the ID in Requirements or correct the mapping.",
                    ),
                )
            else:
                mapped.add(identifier)
        if document.phases and step.phase_number is None:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Step {step.number} has no phase owner in a phased Plan.",
                    _step_span(document, step),
                    "Move the step below exactly one '## Phase N:' heading.",
                ),
            )
        if not _step_has_nonempty_label(document, step, "Tests"):
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Step {step.number} is missing non-empty Tests metadata.",
                    _step_span(document, step),
                    "Add a '- **Tests**: <command or test file>' line.",
                ),
            )

    scope = str(document.frontmatter.get("scope") or "").strip()
    if scope in STANDARD_DEEP_SCOPES:
        for identifier in sorted(declared - mapped, key=_id_sort_key):
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Requirement {identifier!r} is not mapped to any step.",
                    _requirement_span(document, identifier),
                    "Add the ID to at least one step's **Requirements** metadata.",
                ),
            )


def _validate_completion_contract(
    document: PlanDocument,
    errors: List[ArtifactViewError],
) -> None:
    completion = _section_body(document.lexical_blocks, 2, "Completion Contract")
    schema = schema_for(ArtifactKind.PLAN)
    scope = document.frontmatter.get("scope")
    required_completion_sections = schema.required_completion_sections
    if scope == "Lightweight":
        required_completion_sections = ("Outcome", "Verification Surface")
    level_three = [
        (title, block)
        for block in completion
        for level, title in [_heading(block) or (0, "")]
        if level == 3
    ]
    for title in required_completion_sections:
        matches = [block for heading_title, block in level_three if heading_title == title]
        if len(matches) != 1:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Completion Contract subsection must appear exactly once: "
                    f"{title!r} (found {len(matches)}).",
                    matches[0].span if matches else None,
                    f"Keep one level-three '### {title}' subsection.",
                ),
            )

    verification_table = _validate_completion_table(
        document,
        completion,
        "Verification Surface",
        ("id", "evidence required", "command/artifact", "required"),
        errors,
    )
    if scope != "Lightweight":
        _validate_completion_table(
            document,
            completion,
            "Constraints",
            ("id", "constraint", "check"),
            errors,
        )

    phases = {phase.number for phase in document.phases}
    verification_rows = [
        row for row in document.completion_rows if row.row_type == "verification"
    ]
    constraint_rows = [
        row for row in document.completion_rows if row.row_type == "constraint"
    ]
    _validate_completion_ids(
        document,
        verification_rows,
        "verification",
        ID_PATTERNS["verification"],
        errors,
    )
    _validate_completion_ids(
        document,
        constraint_rows,
        "constraint",
        ID_PATTERNS["constraint"],
        errors,
    )

    if verification_table is not None and not verification_rows:
        _add_error(
            errors,
            _schema_error(
                document,
                "Verification Surface must contain at least one row.",
                verification_table.span,
                "Add a V<number> verification row.",
            ),
        )
    for row in verification_rows:
        required_value = row.value_for("required").strip().lower()
        if required_value not in {"yes", "no"}:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Verification {row.identifier!r} Required value must be yes or no.",
                    _block_span(document, row.source_block_id),
                    "Set Required to exactly yes or no.",
                ),
            )
        if isinstance(row.phase, int) and row.phase not in phases:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Verification {row.identifier!r} maps unknown phase "
                    f"{row.phase}.",
                    _block_span(document, row.source_block_id),
                    "Use a declared phase number or final.",
                ),
            )
        if isinstance(row.phase, str) and row.phase != "final":
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Verification {row.identifier!r} has invalid phase "
                    f"{row.phase!r}.",
                    _block_span(document, row.source_block_id),
                    "Use a declared phase number or final.",
                ),
            )
        if row.required:
            if not row.value_for("evidence required").strip():
                _add_error(
                    errors,
                    _schema_error(
                        document,
                        f"Required verification {row.identifier!r} needs non-empty "
                        "Evidence Required text.",
                        _block_span(document, row.source_block_id),
                        "Describe the objective evidence that must pass.",
                    ),
                )
            if not row.value_for("command/artifact").strip():
                _add_error(
                    errors,
                    _schema_error(
                        document,
                        f"Required verification {row.identifier!r} needs a non-empty "
                        "Command/Artifact cell.",
                        _block_span(document, row.source_block_id),
                        "Add an executable command or machine-validated artifact.",
                    ),
                )


def _validate_completion_table(
    document: PlanDocument,
    completion: Sequence[LexicalBlock],
    title: str,
    required_headers: Sequence[str],
    errors: List[ArtifactViewError],
) -> Optional[LexicalBlock]:
    section = _section_body(completion, 3, title)
    table = next((block for block in section if block.kind == "pipe_table"), None)
    if table is None:
        _add_error(
            errors,
            _schema_error(
                document,
                f"{title} must contain a pipe table.",
                None,
                "Add the documented completion-contract table.",
            ),
        )
        return None
    headers, _ = parse_pipe_table(table.raw)
    display_names = {
        "id": "ID",
        "evidence required": "Evidence Required",
        "command/artifact": "Command/Artifact",
        "required": "Required",
        "constraint": "Constraint",
        "check": "Check",
    }
    missing = [header for header in required_headers if header not in headers]
    if missing:
        names = [display_names.get(header, header) for header in missing]
        _add_error(
            errors,
            _schema_error(
                document,
                f"{title} table is missing required columns: {names}.",
                table.span,
                "Add every required header; column order is flexible.",
            ),
        )
    return table


def _validate_completion_ids(
    document: PlanDocument,
    rows: Sequence,
    label: str,
    pattern: str,
    errors: List[ArtifactViewError],
) -> None:
    for row in rows:
        if re.fullmatch(pattern, row.identifier) is None:
            _add_error(
                errors,
                _schema_error(
                    document,
                    f"Invalid {label} ID {row.identifier!r}.",
                    _block_span(document, row.source_block_id),
                    f"Use the documented {label} ID prefix and a positive integer.",
                ),
            )


def _step_has_nonempty_label(
    document: PlanDocument,
    step: Step,
    label: str,
) -> bool:
    if label == "Tests":
        return any(
            test.name == f"step-{step.number}" and bool(test.command.strip())
            for test in document.tests
        )
    pattern = re.compile(
        _LABEL_RE_TEMPLATE.format(label=re.escape(label)),
        re.IGNORECASE,
    )
    blocks = _blocks_by_id(document)
    for source_id in step.source_block_ids:
        match = pattern.search(blocks[source_id].raw)
        if match and match.group(1).strip():
            return True
    return False


def _heading(block: LexicalBlock) -> Optional[Tuple[int, str]]:
    if block.kind != "atx_heading":
        return None
    match = _HEADING_RE.match(block.raw.rstrip("\r\n"))
    if not match:
        return None
    title = (match.group(2) or "").strip()
    title = re.sub(r"[ \t]+#+[ \t]*$", "", title).strip()
    return len(match.group(1)), title


def _section_body(
    blocks: Sequence[LexicalBlock],
    level: int,
    title: str,
) -> Tuple[LexicalBlock, ...]:
    start: Optional[int] = None
    for index, block in enumerate(blocks):
        if _heading(block) == (level, title):
            start = index + 1
            break
    if start is None:
        return ()
    end = len(blocks)
    for index in range(start, len(blocks)):
        heading = _heading(blocks[index])
        if heading and heading[0] <= level:
            end = index
            break
    return tuple(blocks[start:end])


def _blocks_by_id(document: ArtifactDocument) -> dict:
    return {block.block_id: block for block in document.lexical_blocks}


def _block_span(
    document: ArtifactDocument,
    block_id: str,
) -> Optional[SourceSpan]:
    block = _blocks_by_id(document).get(block_id)
    return block.span if block is not None else None


def _section_heading_span(
    document: ArtifactDocument,
    title: str,
) -> Optional[SourceSpan]:
    for block in document.lexical_blocks:
        if _heading(block) == (2, title):
            return block.span
    return None


def _step_span(document: PlanDocument, step: Step) -> Optional[SourceSpan]:
    return _block_span(document, step.source_block_ids[0]) if step.source_block_ids else None


def _requirement_span(
    document: PlanDocument,
    identifier: str,
) -> Optional[SourceSpan]:
    for requirement in document.requirements:
        if requirement.identifier == identifier:
            return _block_span(document, requirement.source_block_id)
    return None


def _first_duplicate(values: Sequence[str]) -> Optional[str]:
    seen = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None


def _id_sort_key(identifier: str) -> Tuple[str, int]:
    match = re.fullmatch(r"([A-Za-z]+)([0-9]+)", identifier)
    if not match:
        return identifier, 0
    return match.group(1), int(match.group(2))


def _add_error(
    errors: List[ArtifactViewError],
    error: ArtifactViewError,
) -> None:
    if len(errors) < MAX_VALIDATION_ERRORS:
        errors.append(error)


def _schema_error(
    document: ArtifactDocument,
    message: str,
    span: Optional[SourceSpan],
    corrective_action: str,
) -> ArtifactSchemaError:
    return ArtifactSchemaError(
        message,
        source_path=document.identity.source_path,
        span=span,
        corrective_action=corrective_action,
    )
