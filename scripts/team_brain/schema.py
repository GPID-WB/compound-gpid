"""team_brain.schema — Schema definitions, constants, and validation.

Defines the canonical structure for:
- ``TEAM-BRAIN.yml`` configuration files in the central team brain repo
- Pattern JSONL entries (``patterns/<project>.jsonl``)
- Entry markdown files (``entries/<project>/<filename>.md``)

All validation functions raise ``ValueError`` with a descriptive message on
invalid input. They never silently ignore missing required fields.

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

#: Required top-level fields in TEAM-BRAIN.yml
REQUIRED_TEAM_BRAIN_YML_FIELDS = ("schema-version", "manager", "contributors")

#: Required fields in a pattern JSONL line
REQUIRED_PATTERN_FIELDS = (
    "id",
    "date",
    "source-project",
    "topic",
    "tags",
    "pattern",
    "entry-path",
    "confidence",
)

#: Valid curation schedule presets
VALID_SCHEDULES = ("daily", "weekly", "monthly")

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TeamBrainConfig:
    """Parsed and validated TEAM-BRAIN.yml configuration.

    Args:
        manager: GitHub username of the team brain manager.
        contributors: List of contributor specs (org or team references).
        curation_schedule: Cron preset or expression for curation runs.
        auto_supersede: Whether the curation bot auto-applies supersession.
        internal_url_patterns: Hostname patterns to redact in privacy filter.
        schema_version: Schema version string from the config file.

    Example::

        config = TeamBrainConfig(
            manager="wb384996",
            contributors=[{"org": "GPID-WB"}],
        )
    """

    manager: str
    contributors: list[dict[str, str]]
    curation_schedule: str = "weekly"
    auto_supersede: bool = False
    internal_url_patterns: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION


@dataclass
class PatternEntry:
    """A single line in a ``patterns/<project>.jsonl`` file.

    Args:
        id: Unique slug (filename stem of the source solution).
        date: ISO date string (YYYY-MM-DD) of when the entry was pushed.
        source_project: Project namespace (folder name under ``entries/``).
        topic: Primary topic extracted from the solution.
        tags: List of searchable tag strings.
        pattern: One-liner distilled pattern (≤ 200 chars).
        entry_path: Relative path to the full entry markdown file.
        confidence: Confidence score (base 1.0, boosted by cross-validation).
        superseded_by: Slug of the entry that supersedes this one, or None.

    Example::

        entry = PatternEntry(
            id="2026-05-20-pester-safety",
            date="2026-05-20",
            source_project="compound-gpid",
            topic="PowerShell testing",
            tags=["pester", "powershell", "testing"],
            pattern="Always use -Quiet with Pester 4 instead of -Output Minimal.",
            entry_path="entries/compound-gpid/2026-05-20-pester-safety.md",
            confidence=1.0,
        )
    """

    id: str
    date: str
    source_project: str
    topic: str
    tags: list[str]
    pattern: str
    entry_path: str
    confidence: float = 1.0
    superseded_by: str | None = None

    def __post_init__(self) -> None:
        """Validate fields on construction to catch write-path bypasses.

        Raises:
            ValueError: If any required field violates the schema constraints.
        """
        if not self.id.strip():
            raise ValueError("PatternEntry: 'id' must be a non-empty string.")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", self.date.strip()):
            raise ValueError(
                f"PatternEntry: 'date' must be ISO format YYYY-MM-DD, got: {self.date!r}"
            )
        if not self.source_project.strip():
            raise ValueError("PatternEntry: 'source_project' must be a non-empty string.")
        if not self.topic.strip():
            raise ValueError("PatternEntry: 'topic' must be a non-empty string.")
        if not self.pattern.strip():
            raise ValueError("PatternEntry: 'pattern' must be a non-empty string.")
        ep = Path(self.entry_path.strip())
        if ".." in ep.parts or ep.is_absolute():
            raise ValueError(
                f"PatternEntry: 'entry_path' must be a relative path inside entries/, "
                f"got: {self.entry_path!r}"
            )
        if not (0.0 <= self.confidence <= 2.0):
            raise ValueError(
                f"PatternEntry: 'confidence' must be in [0.0, 2.0], got {self.confidence}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-serializable dictionary.

        Returns:
            Dictionary with all fields in the canonical JSONL schema.
        """
        return {
            "id": self.id,
            "date": self.date,
            "source-project": self.source_project,
            "topic": self.topic,
            "tags": self.tags,
            "pattern": self.pattern,
            "entry-path": self.entry_path,
            "confidence": self.confidence,
            "superseded-by": self.superseded_by,
        }

    def to_jsonl_line(self) -> str:
        """Serialize to a single JSONL line (no trailing newline).

        Returns:
            JSON string representation of this entry.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ---------------------------------------------------------------------------
# TEAM-BRAIN.yml parsing
# ---------------------------------------------------------------------------

#: Minimal YAML key-value parser (no third-party deps)
_KV_RE = re.compile(r"^(\s*)([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*-\s+(.*?)\s*$")
_MAPPING_ITEM_RE = re.compile(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")


def _parse_team_brain_yml(text: str) -> dict[str, Any]:
    """Parse a TEAM-BRAIN.yml file into a dictionary.

    Uses a minimal line-by-line parser (no third-party YAML library).
    Supports: scalar values, simple lists, and one-level nested mappings.

    Args:
        text: Raw content of a TEAM-BRAIN.yml file.

    Returns:
        Dictionary of parsed configuration values.

    Raises:
        ValueError: If the YAML structure is malformed or unrecognisable.
    """
    result: dict[str, Any] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        m = _KV_RE.match(line)
        if not m:
            i += 1
            continue
        indent, key, value = m.group(1), m.group(2), m.group(3)
        if indent:
            # Nested key — skip (handled by parent)
            i += 1
            continue
        if value == "" or value == "|" or value == ">":
            # Could be a list or nested mapping
            items: list[Any] = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip() or next_line.strip().startswith("#"):
                    i += 1
                    continue
                list_m = _LIST_ITEM_RE.match(next_line)
                if list_m:
                    item_text = list_m.group(1)
                    # Check if next lines are sub-mapping
                    mapping: dict[str, str] = {}
                    # Parse inline key: value pairs on list item line
                    if ": " in item_text:
                        for pair in item_text.split(","):
                            pair = pair.strip()
                            if ": " in pair:
                                k2, v2 = pair.split(": ", 1)
                                mapping[k2.strip()] = v2.strip()
                    # Check following lines for indented sub-mapping
                    j = i + 1
                    while j < len(lines):
                        sub = lines[j]
                        if not sub.strip():
                            j += 1
                            continue
                        sub_m = _MAPPING_ITEM_RE.match(sub)
                        if sub_m and sub.startswith("    "):
                            mapping[sub_m.group(1)] = sub_m.group(2)
                            j += 1
                        else:
                            break
                    i = j
                    items.append(mapping if mapping else item_text)
                else:
                    break
            result[key] = items if items else []
        else:
            # Remove inline comment — require a space before '#' to avoid
            # truncating URL fragments like https://github.com/org/repo#readme
            if " #" in value:
                value = value.split(" #")[0].rstrip()
            # Strip quotes
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key] = value
            i += 1
    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_team_brain_yml(data: dict[str, Any]) -> TeamBrainConfig:
    """Validate parsed TEAM-BRAIN.yml data and return a ``TeamBrainConfig``.

    Args:
        data: Dictionary from ``_parse_team_brain_yml()``.

    Returns:
        Validated ``TeamBrainConfig`` instance.

    Raises:
        ValueError: If any required field is missing or malformed.

    Example::

        data = {
            "schema-version": "1.0",
            "manager": "wb384996",
            "contributors": [{"org": "GPID-WB"}],
        }
        config = validate_team_brain_yml(data)
        assert config.manager == "wb384996"
    """
    for field_name in REQUIRED_TEAM_BRAIN_YML_FIELDS:
        if field_name not in data:
            raise ValueError(
                f"TEAM-BRAIN.yml is missing required field: '{field_name}'. "
                f"Required fields: {list(REQUIRED_TEAM_BRAIN_YML_FIELDS)}"
            )
    manager = str(data["manager"]).strip()
    if not manager:
        raise ValueError("TEAM-BRAIN.yml: 'manager' must be a non-empty GitHub username.")

    contributors = data.get("contributors", [])
    if not isinstance(contributors, list) or not contributors:
        raise ValueError(
            "TEAM-BRAIN.yml: 'contributors' must be a non-empty list of org or team entries."
        )

    curation = data.get("curation", {})
    if isinstance(curation, str):
        curation = {}
    schedule = str(curation.get("schedule", "weekly")).strip() if curation else "weekly"
    if schedule not in VALID_SCHEDULES:
        raise ValueError(
            f"TEAM-BRAIN.yml: 'curation.schedule' must be one of {list(VALID_SCHEDULES)}, "
            f"got {schedule!r}"
        )
    auto_supersede_raw = curation.get("auto-supersede", "false") if curation else "false"
    auto_supersede = str(auto_supersede_raw).lower() in ("true", "yes", "1")
    internal_url_patterns = data.get("internal-url-patterns", [])
    if not isinstance(internal_url_patterns, list):
        internal_url_patterns = []

    return TeamBrainConfig(
        manager=manager,
        contributors=[c if isinstance(c, dict) else {"org": str(c)} for c in contributors],
        curation_schedule=schedule,
        auto_supersede=auto_supersede,
        internal_url_patterns=[str(p) for p in internal_url_patterns],
        schema_version=str(data.get("schema-version", SCHEMA_VERSION)),
    )


def parse_pattern_jsonl_line(line: str) -> PatternEntry:
    """Parse a single JSONL line into a ``PatternEntry``.

    Args:
        line: A single JSON line from a ``patterns/<project>.jsonl`` file.

    Returns:
        Parsed ``PatternEntry`` instance.

    Raises:
        ValueError: If the line is not valid JSON or missing required fields.

    Example::

        line = '{"id": "slug", "date": "2026-01-01", "source-project": "p",
                 "topic": "t", "tags": [], "pattern": "x",
                 "entry-path": "entries/p/slug.md", "confidence": 1.0}'
        entry = parse_pattern_jsonl_line(line)
        assert entry.id == "slug"
    """
    try:
        data = json.loads(line.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSONL line (not valid JSON): {exc}") from exc
    missing = [f for f in REQUIRED_PATTERN_FIELDS if f not in data]
    if missing:
        raise ValueError(
            f"JSONL pattern entry missing required fields: {missing}. "
            f"Line: {line[:80]}..."
        )
    # Validate id (non-empty)
    entry_id = str(data["id"]).strip()
    if not entry_id:
        raise ValueError("JSONL pattern entry: 'id' must be a non-empty string.")
    # Validate date (ISO 8601 YYYY-MM-DD)
    date_str = str(data["date"]).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError(
            f"JSONL pattern entry: 'date' must be ISO format YYYY-MM-DD, got: {date_str!r}"
        )
    # Validate tags (must be a list, not a string)
    raw_tags = data.get("tags", [])
    if not isinstance(raw_tags, list):
        raise ValueError(
            f"JSONL pattern entry: 'tags' must be a JSON array, "
            f"got {type(raw_tags).__name__}: {raw_tags!r}"
        )
    # Validate topic (non-empty)
    topic_str = str(data["topic"]).strip()
    if not topic_str:
        raise ValueError("JSONL pattern entry: 'topic' must be a non-empty string.")
    # Validate source-project (non-empty)
    source_project_str = str(data["source-project"]).strip()
    if not source_project_str:
        raise ValueError("JSONL pattern entry: 'source-project' must be a non-empty string.")
    # Validate pattern (non-empty)
    pattern_text = str(data["pattern"]).strip()
    if not pattern_text:
        raise ValueError("JSONL pattern entry: 'pattern' must be a non-empty string.")
    # Validate entry-path (relative, no traversal)
    ep = str(data["entry-path"]).strip()
    if ".." in Path(ep).parts or Path(ep).is_absolute():
        raise ValueError(
            f"JSONL pattern entry: 'entry-path' must be a relative path inside entries/, got: {ep!r}"
        )
    # Validate confidence (must be in [0.0, 2.0])
    confidence = float(data.get("confidence", 1.0))
    if not (0.0 <= confidence <= 2.0):
        raise ValueError(
            f"JSONL pattern entry: 'confidence' must be in [0.0, 2.0], got {confidence}"
        )
    return PatternEntry(
        id=entry_id,
        date=date_str,
        source_project=source_project_str,
        topic=topic_str,
        tags=[str(t) for t in raw_tags],
        pattern=pattern_text,
        entry_path=ep,
        confidence=confidence,
        superseded_by=data.get("superseded-by") or None,
    )


def load_patterns_from_jsonl(path: Path) -> list[PatternEntry]:
    """Load all pattern entries from a JSONL file.

    Skips blank lines and comment lines (starting with ``#``).
    Emits a warning (not an error) for malformed lines.

    Args:
        path: Path to a ``patterns/<project>.jsonl`` file.

    Returns:
        List of ``PatternEntry`` objects (may be empty).

    Raises:
        FileNotFoundError: If the path does not exist.

    Example::

        >>> from pathlib import Path
        >>> entries = load_patterns_from_jsonl(Path("patterns/compound-gpid.jsonl"))
        >>> print(len(entries), "patterns loaded")
    """
    if not path.exists():
        raise FileNotFoundError(f"Pattern JSONL file not found: {path}")
    entries: list[PatternEntry] = []
    for i, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            entries.append(parse_pattern_jsonl_line(line))
        except ValueError as exc:
            warnings.warn(f"{path}:{i}: Skipping malformed JSONL line — {exc}")
    return entries
