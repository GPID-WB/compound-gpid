"""Created 2026-09-02. Canonical research-output path contract."""
from __future__ import annotations

from pathlib import Path

RESEARCH_ROOT = Path("c-research")
LEGACY_RESEARCH_ROOT = Path(".cg-docs/research")

RESEARCH_OUTPUT_DIRECTORIES = (
    "evidence",
    "manuscripts",
    "normative-decisions",
    "scoping",
    "derivations",
    "specifications",
    "results",
    "replication",
    "eda",
    "measurement",
    "vintages",
)

COMPOUND_DOC_DIRECTORIES = (
    "archive",
    "brainstorms",
    "plans",
    "reviews",
    "solutions",
    "strategy",
    "work-reports",
    "evidence-fixtures",
    "inbox",
    "views",
)

LEGACY_OUTPUT_DIRECTORY_MAP = {
    directory: directory for directory in RESEARCH_OUTPUT_DIRECTORIES
}
LEGACY_OUTPUT_DIRECTORY_MAP["manuscript"] = "manuscripts"


def destination_for_legacy(relative_path: Path) -> Path:
    """Map one legacy research-relative path to its canonical destination.

    Args:
        relative_path: Path relative to the old ``.cg-docs/research/`` root.

    Returns:
        Path relative to the project root under ``c-research/``.

    Raises:
        ValueError: If the path is absolute, traverses upward, or has an
            unknown legacy artifact directory.

    Example:
        ``destination_for_legacy(Path("manuscript/draft.md"))`` returns
        ``Path("c-research/manuscripts/draft.md")``.
    """
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Legacy research path must be a safe relative path: {relative_path}")
    if not candidate.parts or candidate.parts[0] not in LEGACY_OUTPUT_DIRECTORY_MAP:
        raise ValueError(f"Unknown legacy research artifact directory: {relative_path}")
    destination_directory = LEGACY_OUTPUT_DIRECTORY_MAP[candidate.parts[0]]
    return RESEARCH_ROOT / destination_directory / Path(*candidate.parts[1:])


def is_research_output_path(path: Path) -> bool:
    """Return whether a project-relative path belongs to research outputs.

    Args:
        path: Project-relative path to classify.

    Returns:
        ``True`` only for a path below ``c-research/<artifact-type>/``.

    Example:
        ``is_research_output_path(Path("c-research/evidence/claim.yaml"))``
        returns ``True``.
    """
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return False
    parts = candidate.parts
    return len(parts) >= 2 and parts[0] == RESEARCH_ROOT.name and parts[1] in RESEARCH_OUTPUT_DIRECTORIES
