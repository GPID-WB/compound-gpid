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

    Automatic HTML is disabled unless ``artifact-html: true`` is explicitly
    configured. Invalid values warn and default disabled.

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
        return ArtifactViewConfig(False)
    except UnicodeDecodeError as error:
        return ArtifactViewConfig(
            False,
            f"Invalid artifact-html configuration; defaulting disabled: {error}",
        )
    frontmatter, _ = parse_frontmatter_with_body(content)
    if "artifact-html" not in frontmatter:
        return ArtifactViewConfig(False)
    value = frontmatter["artifact-html"]
    if type(value) is bool:
        return ArtifactViewConfig(value)
    return ArtifactViewConfig(
        False,
        f"Invalid artifact-html value {value!r}; defaulting disabled.",
    )
