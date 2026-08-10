"""Pure data types and parsing helpers for the readiness contract."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Optional, Sequence


EXIT_READY = 0
EXIT_NOT_READY = 2
EXIT_CONFIG = 3
EXIT_API = 4

EXIT_REASONS = {
    EXIT_READY: "ready",
    EXIT_NOT_READY: "validation_failure",
    EXIT_CONFIG: "config_error",
    EXIT_API: "api_error",
}

MARKER_RE = re.compile(
    r"<!--\s*compound-gpid-tracked:\s*([A-Za-z0-9][A-Za-z0-9-]*)\s*-->"
)
FEATURE_ID_LINE_RE = re.compile(
    r"\*\*\s*Feature\s+ID\s*:\s*\*\*\s*`([^`]+)`", re.IGNORECASE
)
FEATURE_ID_FORMAT_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RISK_CLASSES = ("low", "medium", "high")
REQUIRED_SECTIONS: tuple[str, ...] = (
    "Roadmap linkage",
    "Ready for Copilot",
    "Outcome",
    "Acceptance criteria",
    "Scope",
    "Non-goals",
    "Expected allowed paths",
    "Prohibited paths",
    "Verification commands",
    "Dependencies / blockers",
    "Risk class",
    "Human review instructions",
    "Blocked-stop conditions",
)
SECTION_HEADER_RE = re.compile(r"^##\s+(.+?)\s*#*\s*$")
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[([ xX])\](?:\s+|$)")
UNCHECKED_BOX_RE = re.compile(r"^\s*[-*]\s*\[\s\](?:\s+|$)")
LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(.*)$")
CODE_SPAN_RE = re.compile(r"`([^`]+)`")
CLOSE_KEYWORDS = r"(?:closes?|closed|fixes?|fixed|resolves?|resolved)"


class ReadinessError(Exception):
    """Base class for readiness validator failures."""


class ConfigError(ReadinessError):
    """Local configuration failure such as bad arguments or missing ``gh``."""


class ApiError(ReadinessError):
    """GitHub API, network, truncation, or malformed-response failure."""


@dataclass
class RuleResult:
    """Result for one stable readiness rule."""

    id: str
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ReadinessResult:
    """Complete validator result, including rules, state, and errors."""

    issue: Optional[int]
    ready: bool
    exit_code: int
    exit_reason: str
    rules: list[RuleResult] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)
    dry_run: bool = True


def strip_bom(text: str) -> str:
    """Remove one leading UTF-8 BOM from text.

    Args:
        text: Text that may begin with ``U+FEFF``.

    Returns:
        ``text`` without its first BOM, or the original text when none exists.

    Example:
        ``strip_bom("\\ufefftitle")`` returns ``"title"``.
    """
    return text[1:] if text and text[0] == "\ufeff" else text


def _iter_fence_state(lines: Sequence[str]):
    """Yield each line with its Markdown fence state and delimiter flags."""
    in_fence = False
    fence: Optional[str] = None
    for line in lines:
        stripped = line.lstrip()
        opens = False
        closes = False
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = "```" if stripped.startswith("```") else "~~~"
                opens = True
        elif fence is not None and stripped.startswith(fence):
            closes = True
        yield line, in_fence, opens, closes
        if opens:
            in_fence = True
        elif closes:
            in_fence = False
            fence = None


def _non_fence_lines(lines: Sequence[str]):
    """Yield lines outside fenced Markdown blocks."""
    for line, in_fence, opens, closes in _iter_fence_state(lines):
        if not in_fence and not opens and not closes:
            yield line


def parse_sections(body: str) -> list[tuple[str, list[str]]]:
    """Split a body into ordered ``##`` sections outside fenced blocks.

    Args:
        body: Untrusted issue Markdown.

    Returns:
        Ordered ``(section_name, content_lines)`` pairs. Preamble lines are not
        returned, and fenced content cannot create a section.

    Example:
        ``parse_sections("## Scope\\ncode")`` returns ``[("Scope", ["code"])]``.
    """
    sections: list[tuple[str, list[str]]] = []
    current_name: Optional[str] = None
    current: list[str] = []
    for line, in_fence, opens, closes in _iter_fence_state(body.splitlines()):
        if in_fence or opens or closes:
            if current_name is not None:
                current.append(line)
            continue
        header = SECTION_HEADER_RE.match(line)
        if header:
            if current_name is not None:
                sections.append((current_name, current))
            current_name = header.group(1).strip()
            current = []
        elif current_name is not None:
            current.append(line)
    if current_name is not None:
        sections.append((current_name, current))
    return sections


def find_marker(body: str) -> Optional[str]:
    """Return the first tracked feature marker outside a fence, if present."""
    for line in _non_fence_lines(body.splitlines()):
        match = MARKER_RE.search(line)
        if match:
            return match.group(1)
    return None


def find_feature_id(body: str) -> tuple[Optional[str], int]:
    """Return the first declared feature id and its body-wide occurrence count."""
    found: Optional[str] = None
    count = 0
    for line in _non_fence_lines(body.splitlines()):
        match = FEATURE_ID_LINE_RE.search(line)
        if match:
            count += 1
            if found is None:
                found = match.group(1).strip()
    return found, count


def _section_nonempty(content_lines: Sequence[str]) -> bool:
    """Return whether a section has non-fenced, non-whitespace content."""
    return any(line.strip() for line in _non_fence_lines(content_lines))


def _section_detail(content_lines: Sequence[str] | None) -> str:
    """Describe a section as absent, empty, or non-empty."""
    if content_lines is None:
        return "section absent"
    return "empty" if not _section_nonempty(content_lines) else "non-empty"


def validate_path_entry(entry: str) -> Optional[str]:
    """Return an unsafe-path error, or ``None`` for a valid git pathspec.

    Args:
        entry: Repository-relative path or glob from the issue contract.

    Returns:
        A short validation error, or ``None`` when ``entry`` is safe.

    Example:
        ``validate_path_entry("docs/guide.md")`` returns ``None``.
    """
    if not entry:
        return "empty path entry"
    if entry != entry.strip():
        return "path entry has surrounding whitespace"
    if re.search(r"[\x00-\x1f\x7f]", entry):
        return "control character in path entry"
    if entry.startswith("//") or entry.startswith("\\\\"):
        return "UNC path"
    if entry.startswith("/"):
        return "absolute path"
    if re.match(r"^[A-Za-z]:", entry):
        return "Windows drive path"
    if "\\" in entry:
        return "backslash not allowed in git pathspec"
    for part in entry.split("/"):
        if not part:
            return "empty path segment (consecutive or trailing slash)"
        if part == "..":
            return "traversal segment '..'"
        if _brackets_unbalanced(part):
            return f"malformed glob (unbalanced brackets) in {part!r}"
    return None


def _brackets_unbalanced(segment: str) -> bool:
    """Return whether a path segment has unbalanced glob brackets."""
    depth = 0
    for char in segment:
        if char == "[":
            depth += 1
        elif char == "]":
            if depth == 0:
                return True
            depth -= 1
    return depth != 0


def _is_overbroad_allowed_path(entry: str) -> bool:
    """Return whether an allowed path has no literal scope component."""
    if entry in ("", ".", ".."):
        return True
    for part in entry.split("/"):
        literal = re.sub(r"[*?\[\]]", "", part)
        if literal and literal not in (".", ".."):
            return False
    return True


def pr_closes_issue(pr_body: str, issue_number: int) -> bool:
    """Return whether a PR body uses a closing keyword for an issue."""
    number = str(issue_number)
    patterns = (
        rf"\b{CLOSE_KEYWORDS}\s+#{number}\b",
        rf"\b{CLOSE_KEYWORDS}\s+https?://\S+/issues/{number}\b",
    )
    return any(re.search(pattern, pr_body, re.IGNORECASE) for pattern in patterns)


def is_copilot_assignee(login: str) -> bool:
    """Return whether a login identifies the Copilot coding agent."""
    if not login:
        return False
    lower = login.lower()
    return lower == "copilot" or lower.startswith("copilot")


def copilot_assignees(assignees: Sequence[str]) -> list[str]:
    """Return assignee logins recognized as the Copilot coding agent.

    Args:
        assignees: Normalized GitHub assignee logins.

    Returns:
        The subset of ``assignees`` accepted by :func:`is_copilot_assignee`.

    Example:
        ``copilot_assignees(["Copilot", "octocat"])`` returns ``["Copilot"]``.
    """
    return [login for login in assignees if is_copilot_assignee(login)]
