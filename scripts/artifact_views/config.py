"""Project-local automatic artifact HTML configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from parsing_utils import parse_frontmatter_with_body


@dataclass(frozen=True)
class ArtifactViewConfig:
    """Resolved automatic HTML setting and optional warning."""

    automatic_html: bool
    warning: Optional[str] = None


def load_artifact_view_config(project_root: Path) -> ArtifactViewConfig:
    """Read ``artifact-html`` from project-local frontmatter.

    Missing configuration enables automatic HTML. Invalid values warn and also
    default enabled so configuration drift cannot silently disable generation.

    Args:
        project_root: Project root containing ``compound-gpid.local.md``.

    Returns:
        Resolved immutable configuration.

    Example:
        ``load_artifact_view_config(Path('.')).automatic_html`` returns a bool.
    """
    path = Path(project_root) / "compound-gpid.local.md"
    if not path.is_file():
        return ArtifactViewConfig(True)
    try:
        frontmatter, _ = parse_frontmatter_with_body(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        return ArtifactViewConfig(
            True,
            f"Invalid artifact-html configuration; defaulting enabled: {error}",
        )
    value = frontmatter.get("artifact-html")
    if value is None:
        return ArtifactViewConfig(True)
    if type(value) is bool:
        return ArtifactViewConfig(value)
    return ArtifactViewConfig(
        True,
        f"Invalid artifact-html value {value!r}; defaulting enabled.",
    )
