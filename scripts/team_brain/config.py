"""team_brain.config — Load team brain configuration from compound-gpid.local.md.

Reads the ``team-brain:`` section from the project's local configuration file
and returns a typed ``TeamBrainLocalConfig`` object.  If the section is absent
or ``enabled: false``, all team brain features are silently disabled.

The local config follows the schema defined in ``docs/team-brain-schema.md``:

.. code-block:: yaml

    team-brain:
      repo: "GPID-WB/team-brain"    # owner/repo on GitHub (required)
      project-name: "compound-gpid"  # namespace under entries/ and patterns/
      enabled: true
      llm-filter: true

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default filename for local config
DEFAULT_LOCAL_CONFIG_NAME = "compound-gpid.local.md"

#: Section key for team brain config
TEAM_BRAIN_KEY = "team-brain"

#: Required fields inside the team-brain section
REQUIRED_TEAM_BRAIN_LOCAL_FIELDS = ("repo",)

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class TeamBrainLocalConfig:
    """Typed local team brain configuration.

    Args:
        repo: GitHub owner/repo string (e.g. ``GPID-WB/team-brain``).
        project_name: Namespace under ``entries/`` and ``patterns/`` in the
            central repo. Defaults to the local directory name.
        enabled: Whether team brain features are active for this project.
        llm_filter: Whether to run the LLM privacy layer before pushing.

    Example::

        config = TeamBrainLocalConfig(
            repo="GPID-WB/team-brain",
            project_name="compound-gpid",
        )
        assert config.enabled is True
        assert config.llm_filter is True
    """

    repo: str
    project_name: str
    enabled: bool = True
    llm_filter: bool = True

    def _split_repo(self) -> tuple:
        """Return (owner, name) by splitting ``self.repo`` on the first ``/``.

        Raises:
            ValueError: If ``repo`` is not in ``owner/repo`` format.
        """
        parts = self.repo.split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"team-brain.repo must be in 'owner/repo' format, got: {self.repo!r}"
            )
        return parts[0], parts[1]

    def repo_owner(self) -> str:
        """Return the owner portion of the ``repo`` field.

        Returns:
            Owner string (e.g. ``GPID-WB``).

        Raises:
            ValueError: If ``repo`` is not in ``owner/repo`` format.
        """
        return self._split_repo()[0]

    def repo_name(self) -> str:
        """Return the repository name portion of the ``repo`` field.

        Returns:
            Repository name string (e.g. ``team-brain``).

        Raises:
            ValueError: If ``repo`` is not in ``owner/repo`` format.
        """
        return self._split_repo()[1]


# ---------------------------------------------------------------------------
# Minimal YAML-ish frontmatter parser
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)^---\s*\n", re.DOTALL | re.MULTILINE)
_KV_RE = re.compile(r"^([A-Za-z0-9_\-]+)\s*:\s*(.*?)\s*$")


def _parse_frontmatter_from_text(text: str) -> dict[str, Any]:
    """Extract and parse YAML frontmatter from a markdown file.

    Supports: string scalars, booleans, and simple inline values.
    Does NOT support multi-line values or complex YAML structures —
    sufficient for ``compound-gpid.local.md``.

    Args:
        text: Full content of the markdown file.

    Returns:
        Dictionary of frontmatter key→value pairs, or empty dict.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm_text = m.group(1)
    result: dict[str, Any] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        kv = _KV_RE.match(line)
        if not kv:
            continue
        key = kv.group(1)
        value = kv.group(2).strip()
        # Strip inline comments (space before # avoids truncating URL fragments)
        if " #" in value:
            value = value[: value.index(" #")].strip()
        # Strip quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        # Coerce booleans
        if value.lower() == "true":
            result[key] = True
        elif value.lower() == "false":
            result[key] = False
        else:
            result[key] = value
    return result


def _parse_markdown_body_key_block(text: str, section_key: str) -> dict[str, Any]:
    """Extract a simple indented YAML block from the markdown body.

    Parses a block of the form::

        team-brain:
          repo: "owner/name"
          project-name: "my-project"
          enabled: true
          llm-filter: true

    when it appears in the body of a markdown file (not frontmatter).

    Args:
        text: Full markdown text.
        section_key: The top-level key to extract (e.g. ``team-brain``).

    Returns:
        Dictionary of the block's key→value pairs, or empty dict.
    """
    result: dict[str, Any] = {}
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(rf"^{re.escape(section_key)}\s*:", stripped):
            in_block = True
            continue
        if in_block:
            # Sub-key lines are indented
            if re.match(r"^\s+", line):
                kv = re.match(r"^\s+([A-Za-z0-9_\-]+)\s*:\s*(.*?)\s*$", line)
                if kv:
                    key = kv.group(1)
                    value = kv.group(2).strip()
                    # Strip inline comments (space before # avoids truncating URL fragments)
                    if " #" in value:
                        value = value[: value.index(" #")].strip()
                    # Strip quotes
                    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    if value.lower() == "true":
                        result[key] = True
                    elif value.lower() == "false":
                        result[key] = False
                    else:
                        result[key] = value
            else:
                if stripped and not stripped.startswith("#"):
                    break  # End of block
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_team_brain_local_config(
    local_config_path: Path | None = None,
) -> TeamBrainLocalConfig | None:
    """Load team brain config from ``compound-gpid.local.md``.

    Returns None (silently) if:
    - The file does not exist.
    - The file exists but has no ``team-brain:`` section.
    - The section has ``enabled: false``.

    Args:
        local_config_path: Override path to the local config file. If None,
            searches upward from ``cwd`` for ``compound-gpid.local.md``.

    Returns:
        Parsed ``TeamBrainLocalConfig``, or None if team brain is disabled.

    Raises:
        ValueError: If the ``team-brain`` section is present and enabled but
            missing required fields (e.g. ``repo``).

    Example::

        config = load_team_brain_local_config(Path("compound-gpid.local.md"))
        if config is None:
            print("Team brain not configured for this project.")
        else:
            print(f"Push to: {config.repo}")
    """
    if local_config_path is None:
        local_config_path = _find_local_config()
    if local_config_path is None or not local_config_path.exists():
        return None

    text = local_config_path.read_text(encoding="utf-8")

    # Prefer body-level `team-brain:` block (intended location per spec)
    tb_data = _parse_markdown_body_key_block(text, TEAM_BRAIN_KEY)

    # Fall back to frontmatter if not found in body
    if not tb_data:
        fm = _parse_frontmatter_from_text(text)
        tb_data = fm.get(TEAM_BRAIN_KEY, {})

    if not tb_data:
        return None  # Section absent — silently disabled

    enabled = tb_data.get("enabled", True)
    if isinstance(enabled, str):
        enabled = enabled.lower() not in ("false", "no", "0")
    if not enabled:
        return None  # Explicitly disabled

    # Validate required fields
    for required in REQUIRED_TEAM_BRAIN_LOCAL_FIELDS:
        if required not in tb_data:
            raise ValueError(
                f"compound-gpid.local.md: team-brain section is missing "
                f"required field '{required}'. Add 'repo: owner/name' under "
                f"'team-brain:' to configure the central brain repo."
            )

    repo = str(tb_data["repo"]).strip()
    if not re.match(r'^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$', repo):
        raise ValueError(
            f"compound-gpid.local.md: team-brain.repo must be 'owner/repo' with "
            f"alphanumeric, hyphen, dot, or underscore only. Got: {repo!r}"
        )

    project_name = str(tb_data.get("project-name", local_config_path.parent.name)).strip()
    if not re.match(r'^[A-Za-z0-9][A-Za-z0-9\-_]*$', project_name):
        raise ValueError(
            f"compound-gpid.local.md: team-brain.project-name must be "
            f"alphanumeric with hyphens/underscores only. Got: {project_name!r}"
        )
    llm_filter = tb_data.get("llm-filter", True)
    if isinstance(llm_filter, str):
        llm_filter = llm_filter.lower() not in ("false", "no", "0")

    return TeamBrainLocalConfig(
        repo=repo,
        project_name=project_name,
        enabled=True,
        llm_filter=bool(llm_filter),
    )


def _find_local_config(start: Path | None = None) -> Path | None:
    """Walk upward from ``start`` to find ``compound-gpid.local.md``.

    Stops at a directory containing ``.git/`` or ``compound-gpid.md`` to
    prevent accidentally picking up a config from an ancestor project.

    Args:
        start: Starting directory; defaults to current working directory.

    Returns:
        Path to the local config file, or None if not found.
    """
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / DEFAULT_LOCAL_CONFIG_NAME
        if candidate.exists():
            return candidate
        # Stop climbing at a repo root — don't pick up ancestor project configs
        if (parent / ".git").exists() or (parent / "compound-gpid.md").exists():
            break
    return None
