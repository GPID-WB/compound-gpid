"""Project-local automatic artifact HTML configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from parsing_utils import parse_frontmatter_with_body
from secure_fs import secure_read_bytes

_MAX_CONFIG_BYTES = 256 * 1024


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
    root = Path(project_root)
    try:
        content = secure_read_bytes(
            root,
            "compound-gpid.local.md",
            reject_hardlinks=True,
            max_bytes=_MAX_CONFIG_BYTES,
        ).decode("utf-8", errors="strict")
    except FileNotFoundError:
        return ArtifactViewConfig(True)
    except UnicodeDecodeError as error:
        return ArtifactViewConfig(
            True,
            f"Invalid artifact-html configuration; defaulting enabled: {error}",
        )
    frontmatter, _ = parse_frontmatter_with_body(content)
    value = frontmatter.get("artifact-html")
    if value is None:
        return ArtifactViewConfig(True)
    if type(value) is bool:
        return ArtifactViewConfig(value)
    return ArtifactViewConfig(
        True,
        f"Invalid artifact-html value {value!r}; defaulting enabled.",
    )
