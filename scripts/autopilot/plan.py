"""Strict control frontmatter, immutable execution digest and batch validation.

Only schema-version-1 phased plans with a valid completion contract, deviation
policy and a consistent completed-prefix are eligible. The ``phases`` count
convenience field is never trusted: real phase headings are authoritative.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional, Sequence, Tuple

import secure_fs
from artifact_views.validator import (
    ArtifactKind,
    ArtifactValidationError,
    PlanDocument,
    SchemaSupport,
    validate_source,
)
from autopilot.arguments import BatchSegment
from autopilot.contracts import PlanError, sha256_hex

PLAN_FILE_LIMIT = 2 * 1024 * 1024
PROGRESS_FIELDS = (
    "status", "completed-date", "failing-steps",
    "completed-phases", "current-phase", "execution-report",
)
_CONTROL_FIELDS = ("phases", "completed-phases", "current-phase", "execution-report")
_SCALAR_EXTRACTABLE = PROGRESS_FIELDS + ("phases",)
_FM_RE = re.compile(r"^\ufeff?---[ \t]*\n(.*?)\n---[ \t]*\n", re.DOTALL)
_INLINE_LIST_RE = re.compile(r"^\[(\d+(?:,\s*\d+)*)?\]$")
_PATH_FORBIDDEN_RE = re.compile(r"[\[\]()\\\s]")


@dataclass(frozen=True)
class ValidatedPlan:
    """One strict autopilot plan with its authoritative phase structure."""

    source: str
    digest: str
    title: str
    phases: Tuple[int, ...]
    current_phase: int
    completed_phases: Tuple[int, ...]
    execution_report: str
    status: str


def _normalize(source: str) -> str:
    """Normalize to LF line endings without touching body whitespace."""
    return source.replace("\r\n", "\n").replace("\r", "\n")


def _frontmatter_lines(source: str) -> Tuple[str, ...]:
    """Return raw frontmatter content lines, rejecting duplicate keys."""
    match = _FM_RE.match(_normalize(source))
    if not match:
        raise PlanError(
            "missing frontmatter: an autopilot plan requires a delimited "
            "'---' frontmatter block."
        )
    lines = match.group(1).split("\n")
    seen: dict[str, int] = {}
    for index, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith(("#", "-")):
            continue
        key = line.split(":", 1)[0].strip()
        if key and key in seen:
            raise PlanError(
                f"duplicate-key {key!r}: control frontmatter keys must appear once.",
                error_code="autopilot-plan-error",
            )
        if key:
            seen[key] = index
    return lines


def _control_values(source: str) -> dict:
    """Extract strict scalar control values from raw frontmatter lines."""
    values: dict[str, str] = {}
    for line in _frontmatter_lines(source):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-")):
            continue
        key, separator, raw = line.partition(":")
        if not separator or key.strip() not in _SCALAR_EXTRACTABLE:
            continue
        value = raw.strip()
        if any(character in value for character in "&*!{|}>"):
            raise PlanError(
                f"control field {key.strip()!r} contains YAML anchors, tags, "
                "aliases or block scalars; use a plain scalar."
            )
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise PlanError(f"control field {key.strip()!r} has an unterminated quote.")
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _control_int(source: str, field: str, minimum: int = 1) -> int:
    raw = _control_values(source).get(field)
    if raw is None:
        raise PlanError(f"control field {field!r} is required for autopilot plans.")
    if not re.fullmatch(r"\d+", raw):
        raise PlanError(f"control field {field!r} must be a non-negative integer.")
    value = int(raw)
    if value < minimum:
        raise PlanError(f"control field {field!r} must be at least {minimum}.")
    return value


def _completed_phases(source: str) -> Tuple[int, ...]:
    raw = _control_values(source).get("completed-phases")
    if raw is None:
        raise PlanError("control field 'completed-phases' is required.")
    match = _INLINE_LIST_RE.fullmatch(raw)
    if not match:
        raise PlanError(
            "control field 'completed-phases' must be an inline list of "
            "integers like '[1, 2]'."
        )
    inner = match.group(1)
    if inner is None or not inner.strip():
        return ()
    values = tuple(int(item) for item in inner.split(","))
    if len(set(values)) != len(values):
        raise PlanError(
            "completed-prefix: control field 'completed-phases' contains duplicates."
        )
    return values


def _execution_report(source: str) -> str:
    raw = _control_values(source).get("execution-report")
    if raw is None:
        raise PlanError("control field 'execution-report' is required.")
    if (
        not raw
        or raw.startswith("/")
        or "://" in raw
        or _PATH_FORBIDDEN_RE.search(raw)
        or PurePosixPath(raw).is_absolute()
        or ".." in PurePosixPath(raw).parts
    ):
        raise PlanError(
            f"execution-report {raw!r} must be a contained relative path with no "
            "link escapes, backslashes or whitespace."
        )
    return raw


def execution_digest(source: str) -> str:
    """Compute the immutable digest over normalized LF source.

    Only the six progress fields are excluded from the frontmatter; the body
    is never normalized away. Duplicate control keys are rejected first.
    """
    normalized = _normalize(source)
    kept = [
        line for line in _frontmatter_lines(normalized)
        if line.split(":", 1)[0].strip() not in PROGRESS_FIELDS
    ]
    match = _FM_RE.match(normalized)
    digest_source = "---\n" + "\n".join(kept) + "---\n" + normalized[match.end():]
    return sha256_hex(digest_source.encode("utf-8"))


def progress_delta(old_source: str, new_source: str) -> Tuple[str, ...]:
    """Return the changed progress fields, rejecting any non-progress change."""
    if execution_digest(old_source) != execution_digest(new_source):
        raise PlanError(
            "plan-body-changed: the plan body or non-progress frontmatter "
            "changed; only progress fields may advance between versions."
        )
    return tuple(
        field for field in PROGRESS_FIELDS
        if _control_values(old_source).get(field) != _control_values(new_source).get(field)
    )


def validate_autopilot_plan(source: str, source_path: Path) -> ValidatedPlan:
    """Validate one schema-version-1 phased plan with strict control metadata.

    Requires an explicit artifact-schema-version 1, a deviation policy, valid
    completion metadata, real consecutive phase headings and a completed-prefix
    consistent with ``current-phase``.
    """
    _frontmatter_lines(source)
    try:
        document = validate_source(source, source_path, ArtifactKind.PLAN)
    except ArtifactValidationError as error:
        raise PlanError(
            f"plan validation failed: {error}",
            corrective_action=getattr(error, "corrective_action", None),
        ) from error
    if not isinstance(document, PlanDocument):
        raise PlanError("the document is not a plan.")
    identity = document.identity
    if identity.schema_support is not SchemaSupport.STRICT or identity.schema_version != 1:
        raise PlanError(
            "unsupported artifact-schema-version: autopilot requires an explicit "
            "schema-version 1 plan."
        )
    if not document.phases:
        raise PlanError("the plan has no phases; autopilot requires phased plans.")
    real_phases = tuple(phase.number for phase in document.phases)
    declared = _control_int(source, "phases")
    if declared != len(real_phases):
        raise PlanError(
            f"phase-count-mismatch: frontmatter declares {declared} phases but "
            f"the real headings are {real_phases}; the count field is never trusted."
        )
    current = _control_int(source, "current-phase")
    completed = _completed_phases(source)
    if current > len(real_phases):
        raise PlanError(
            f"unknown-phase: current-phase {current} exceeds the {len(real_phases)} "
            "real phases."
        )
    if tuple(completed) != tuple(range(1, current)):
        raise PlanError(
            f"completed-prefix: completed-phases {list(completed)} must be exactly "
            f"the prefix 1..{current - 1} of current-phase {current}."
        )
    report = _execution_report(source)
    status = _control_values(source).get("status")
    return ValidatedPlan(
        source=source,
        digest=execution_digest(source),
        title=identity.title,
        phases=real_phases,
        current_phase=current,
        completed_phases=completed,
        execution_report=report,
        status=status or "",
    )


def read_plan(root: Path, relative_path: str) -> ValidatedPlan:
    """Acquire one plan through the secure-read API and validate those bytes.

    The exact acquired bytes are parsed and hashed; there is no pathname
    fallback, chunk read or automatic limit increase.
    """
    if not isinstance(relative_path, str) or not relative_path:
        raise PlanError("plan path must be a non-empty contained path.")
    try:
        normalized = secure_fs.normalize_relative_path(PurePosixPath(relative_path))
    except (secure_fs.SecureMutationError, ValueError) as error:
        raise PlanError(f"plan path is outside the repository: {relative_path!r}.") from error
    try:
        raw = secure_fs.secure_read_bytes(
            root, PurePosixPath(normalized), max_bytes=PLAN_FILE_LIMIT, reject_hardlinks=True
        )
    except FileNotFoundError as error:
        raise PlanError(
            f"plan-missing: the plan file does not exist: {relative_path!r}."
        ) from error
    except secure_fs.SecureMutationError as error:
        if "hard link" in str(error):
            raise PlanError(
                f"plan-unsafe: plan read rejected a hard-linked or aliased "
                f"source: {error}"
            ) from error
        raise PlanError(
            f"plan-too-large: plan read failed: {error}"
        ) from error
    except OSError as error:
        raise PlanError(f"plan-unreadable: plan read failed: {error}") from error
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise PlanError("the plan is not valid strict UTF-8.") from error
    return validate_autopilot_plan(source, root / normalized)


def validate_batches(
    plan: ValidatedPlan, segments: Sequence[BatchSegment]
) -> Tuple[int, ...]:
    """Validate batch segments against the plan's real phases.

    Rejects unknown phases and gaps over incomplete prerequisites: the union
    of batched phases must be contiguous and start at ``current-phase``.
    Segments are consumed lazily; each segment's width must not exceed the
    plan's real phase count.
    """
    for segment in segments:
        if segment.end - segment.start + 1 > len(plan.phases):
            raise PlanError(
                f"segment-too-wide: segment '{segment.display()}' spans "
                f"{segment.end - segment.start + 1} phases but the plan has "
                f"only {len(plan.phases)} real phases."
            )
    union = tuple(phase for segment in segments for phase in segment.iter_phases())
    if not union:
        raise PlanError("phase-gap: batches must contain at least one phase.")
    for phase in union:
        if phase not in plan.phases:
            raise PlanError(
                f"unknown-phase: {phase} is not one of the plan's real phases "
                f"{plan.phases}."
            )
    expected = tuple(range(plan.current_phase, plan.current_phase + len(union)))
    if tuple(union) != expected:
        raise PlanError(
            f"phase-gap: batched phases {union} skip an incomplete prerequisite; "
            f"the union must be the contiguous range {expected} starting at "
            f"current-phase {plan.current_phase}."
        )
    return union
