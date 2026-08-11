"""Path validation and section-content helpers for the readiness contract.

These helpers are pure functions with no I/O.  They are split from
``contract_parsing`` to keep that module under the repository's 300-line
limit while preserving all existing imports and behaviour.
"""
from __future__ import annotations

import re
from typing import Optional, Sequence


def validate_path_entry(entry: str) -> Optional[str]:
    """Return an unsafe-path error, or ``None`` for a valid git pathspec.

    Args:
        entry: Repository-relative path or glob from the issue contract.

    Returns:
        A short validation error string, or ``None`` when ``entry`` is safe.

    Example:
        ``validate_path_entry("docs/guide.md")`` returns ``None``.
        ``validate_path_entry("/etc/passwd")`` returns ``"absolute path"``.
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
    """Return whether a path segment has unbalanced glob brackets.

    Args:
        segment: A single ``/``-delimited path component that may contain
            glob brackets.

    Returns:
        ``True`` if brackets are unbalanced (an opening ``[`` has no matching
        ``]``, or a closing ``]`` appears without a prior ``[``).

    Example:
        ``_brackets_unbalanced("[a-z")`` returns ``True``.
        ``_brackets_unbalanced("[a-z]")`` returns ``False``.
    """
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
    """Return whether an allowed path has no literal scope component.

    Rejects bare ``*``, ``**``, ``.``, and any entry whose every segment is
    empty after removing glob metacharacters (no literal path component).  Such
    entries make the ``Exact allowed-path closure`` contract meaningless.

    Args:
        entry: An allowed-path entry from the issue contract.

    Returns:
        ``True`` if the entry is overbroad (no literal path component).

    Example:
        ``_is_overbroad_allowed_path("**")`` returns ``True``.
        ``_is_overbroad_allowed_path("docs/foo.md")`` returns ``False``.
    """
    if entry in ("", ".", ".."):
        return True
    for part in entry.split("/"):
        literal = re.sub(r"[*?\[\]]", "", part)
        if literal and literal not in (".", ".."):
            return False
    return True


def _section_nonempty(content_lines: Sequence[str]) -> bool:
    """Return whether a section has non-fenced, non-whitespace content.

    Args:
        content_lines: The raw lines belonging to one ``##`` section,
            including any fenced blocks within it.

    Returns:
        ``True`` if at least one non-fence, non-whitespace line exists.

    Example:
        ``_section_nonempty(["", "## Scope"])`` returns ``True``.
        ``_section_nonempty(["", "  "])`` returns ``False``.
    """
    in_fence = False
    fence: Optional[str] = None
    for line in content_lines:
        stripped = line.lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = "```" if stripped.startswith("```") else "~~~"
                in_fence = True
                continue
        elif fence is not None and stripped.startswith(fence):
            in_fence = False
            fence = None
            continue
        if not in_fence and line.strip():
            return True
    return False


def _section_detail(content_lines: Sequence[str] | None) -> str:
    """Describe a section as absent, empty, or non-empty.

    Args:
        content_lines: The raw lines of a ``##`` section, or ``None`` when the
            section was not present in the body.

    Returns:
        One of ``"section absent"``, ``"empty"``, or ``"non-empty"``.

    Example:
        ``_section_detail(None)`` returns ``"section absent"``.
        ``_section_detail([""])`` returns ``"empty"``.
    """
    if content_lines is None:
        return "section absent"
    return "empty" if not _section_nonempty(content_lines) else "non-empty"
