"""Typed, actionable errors for artifact validation and rendering."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from artifact_views.model import SourceSpan


class ArtifactViewError(Exception):
    """Base error carrying source location and corrective action.

    Args:
        message: Concise description of the failure.
        source_path: Canonical artifact path, when known.
        span: One-based source span, when known.
        corrective_action: Exact action that can resolve the failure.

    Example:
        >>> error = ArtifactViewError(
        ...     "Missing title.",
        ...     source_path=Path("plan.md"),
        ...     corrective_action="Add a non-empty title field.",
        ... )
        >>> "Missing title" in str(error)
        True
    """

    error_code = "artifact-view-error"

    def __init__(
        self,
        message: str,
        *,
        source_path: Optional[Path] = None,
        span: Optional["SourceSpan"] = None,
        corrective_action: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.source_path = Path(source_path) if source_path is not None else None
        self.span = span
        self.corrective_action = corrective_action

    def __str__(self) -> str:
        location = ""
        if self.source_path is not None:
            location = self.source_path.as_posix()
            if self.span is not None:
                if self.span.start_line == self.span.end_line:
                    location += f":{self.span.start_line}"
                else:
                    location += (
                        f":{self.span.start_line}-{self.span.end_line}"
                    )
        elif self.span is not None:
            location = (
                f"line {self.span.start_line}"
                if self.span.start_line == self.span.end_line
                else f"lines {self.span.start_line}-{self.span.end_line}"
            )

        rendered = f"{location}: {self.message}" if location else self.message
        if self.corrective_action:
            rendered += f" Corrective action: {self.corrective_action}"
        return rendered


class ArtifactReadError(ArtifactViewError):
    """The canonical Markdown source could not be read safely."""

    error_code = "artifact-read-error"


class ArtifactParseError(ArtifactViewError):
    """The source does not conform to the closed Markdown grammar."""

    error_code = "artifact-parse-error"


class ArtifactSchemaError(ArtifactViewError):
    """The parsed artifact violates its versioned schema."""

    error_code = "artifact-schema-error"


class ArtifactValidationError(ArtifactViewError):
    """A bounded collection of independent artifact validation failures."""

    error_code = "artifact-validation-error"

    def __init__(self, errors: Sequence[ArtifactViewError]) -> None:
        collected = tuple(errors)
        if not collected:
            raise ValueError("ArtifactValidationError requires at least one error.")
        self.errors = collected
        first = collected[0]
        super().__init__(
            f"Artifact validation failed with {len(collected)} error(s).",
            source_path=first.source_path,
        )

    def __str__(self) -> str:
        details = "\n".join(f"- {error}" for error in self.errors)
        return f"{super().__str__()}\n{details}"


class ArtifactModelError(ArtifactViewError):
    """Typed model construction would violate source identity invariants."""

    error_code = "artifact-model-error"


class ArtifactCoverageError(ArtifactViewError):
    """Source-to-render ownership is missing, duplicated, or invented."""

    error_code = "artifact-coverage-error"


class ArtifactSecurityError(ArtifactViewError):
    """Untrusted source content violates the output security policy."""

    error_code = "artifact-security-error"


class ArtifactPathError(ArtifactViewError):
    """A source or destination path violates containment requirements."""

    error_code = "artifact-path-error"


class ArtifactWriteError(ArtifactViewError):
    """A validated view could not be replaced securely."""

    error_code = "artifact-write-error"
