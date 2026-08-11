"""Markdown parsing, path validation, and fence-aware helpers."""
from __future__ import annotations

import re
from typing import Optional, Sequence

from .contract_path_helpers import (  # noqa: F401 -- public re-exports
    _brackets_unbalanced,
    _is_overbroad_allowed_path,
    _section_detail,
    _section_nonempty,
    validate_path_entry,
)


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
    """Yield each line with its Markdown fence state and delimiter flags.

    Args:
        lines: Raw Markdown lines.

    Yields:
        ``(line, in_fence, opens, closes)`` tuples. ``in_fence`` is ``True``
        when the line begins inside an open fenced code block. ``opens`` and
        ``closes`` mark delimiter lines that start or end a fence.
    """
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
    """Yield lines outside fenced Markdown blocks.

    Args:
        lines: Raw Markdown lines.

    Yields:
        Lines that are not fenced content, fence delimiters, or inside a fence.
    """
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
    """Return the first tracked feature marker outside a fence, if present.

    Args:
        body: Untrusted issue Markdown.

    Returns:
        The marker identifier, or ``None`` if not found.
    """
    for line in _non_fence_lines(body.splitlines()):
        match = MARKER_RE.search(line)
        if match:
            return match.group(1)
    return None


def find_feature_id(body: str) -> tuple[Optional[str], int]:
    """Return the first declared feature id and its body-wide occurrence count.

    Args:
        body: Untrusted issue Markdown.

    Returns:
        A ``(feature_id, count)`` tuple. ``feature_id`` is ``None`` when no
        declaration exists.
    """
    found: Optional[str] = None
    count = 0
    for line in _non_fence_lines(body.splitlines()):
        match = FEATURE_ID_LINE_RE.search(line)
        if match:
            count += 1
            if found is None:
                found = match.group(1).strip()
    return found, count


def pr_closes_issue(pr_body: str, issue_number: int) -> bool:
    """Return whether a PR body uses a closing keyword for an issue.

    Args:
        pr_body: The pull request body text.
        issue_number: The issue number to check against.

    Returns:
        ``True`` if the body contains a closing keyword for the issue.

    Example:
        ``pr_closes_issue("Closes #42", 42)`` returns ``True``.
    """
    number = str(issue_number)
    patterns = (
        rf"\b{CLOSE_KEYWORDS}\s+#{number}\b",
        rf"\b{CLOSE_KEYWORDS}\s+https?://\S+/issues/{number}\b",
    )
    return any(re.search(pattern, pr_body, re.IGNORECASE) for pattern in patterns)


# Canonical Copilot coding-agent logins accepted by the validator.
COPILOT_LOGINS: frozenset[str] = frozenset({"copilot-swe-agent[bot]"})


def is_copilot_assignee(login: str) -> bool:
    """Return whether a login identifies the Copilot coding agent.

    Only the canonical login ``copilot-swe-agent[bot]`` is accepted.  Prefix
    lookalikes such as ``copilot``, ``copilot-x``, or ``copilotbot`` are
    rejected.

    Args:
        login: A GitHub assignee login string.

    Returns:
        ``True`` if the login is in the canonical allowlist.

    Example:
        ``is_copilot_assignee("copilot-swe-agent[bot]")`` returns ``True``.
    """
    return login in COPILOT_LOGINS


def copilot_assignees(assignees: Sequence[str]) -> list[str]:
    """Return assignee logins recognized as the Copilot coding agent.

    Args:
        assignees: Normalized GitHub assignee logins.

    Returns:
        The subset of ``assignees`` accepted by :func:`is_copilot_assignee`.

    Example:
        ``copilot_assignees(["copilot-swe-agent[bot]", "octocat"])`` returns
        ``["copilot-swe-agent[bot]"]``.
    """
    return [login for login in assignees if is_copilot_assignee(login)]
