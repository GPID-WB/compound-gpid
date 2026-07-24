"""brain.utils — Shared utilities for the Compound GPID brain engine.

Promotes parse_frontmatter(), write_atomic(), extract_summary(), and
_coerce() from cg_index.py into a shared module accessible by all brain
sub-modules and the legacy cg_index.py CLI.

All functions are stdlib-only (Python 3.8+, no third-party packages) and
cross-platform (Windows + macOS).
"""
from __future__ import annotations

import csv
import io
import os
import re
import tempfile
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Scalar coercion
# ---------------------------------------------------------------------------

_BARE_TRUE = re.compile(r"^(true|yes)$", re.IGNORECASE)
_BARE_FALSE = re.compile(r"^(false|no)$", re.IGNORECASE)
# P1.2 fix: return None for YAML null values so edge detector can null-guard
_BARE_NULL = re.compile(r"^(null|~|none)$", re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INT_RE = re.compile(r"^-?\d+$")

# Inline list: [a, b, c] or ["a", "b"]
_INLINE_LIST_RE = re.compile(r"^\[([^\]]*)\]$")


def _coerce(value: str) -> Any:
    """Coerce a YAML scalar string to a Python type.

    Handles booleans, YAML null values, dates, integers, and quoted strings.
    Returns ``None`` for YAML null values (``null``, ``~``, ``none``) rather
    than treating them as path strings — critical for edge detection null-guards
    (P1.2 fix: 6+ plan files in the corpus use ``brainstorm: ~`` or
    ``brainstorm: null``).

    Args:
        value: Raw YAML scalar string to coerce.

    Returns:
        Coerced Python value: ``True``/``False``, ``None``, ``int``, or ``str``.

    Example:
        >>> _coerce("true")
        True
        >>> _coerce("null") is None
        True
        >>> _coerce("~") is None
        True
        >>> _coerce("2026-05-19")
        '2026-05-19'
        >>> _coerce("42")
        42
    """
    v = value.strip()
    if _BARE_TRUE.match(v):
        return True
    if _BARE_FALSE.match(v):
        return False
    if _BARE_NULL.match(v):
        return None
    if _DATE_RE.match(v):
        return v  # Keep dates as ISO 8601 strings
    if _INT_RE.match(v):
        return int(v)
    # Strip optional surrounding quotes
    if (
        (v.startswith('"') and v.endswith('"'))
        or (v.startswith("'") and v.endswith("'"))
    ):
        return v[1:-1]
    return v


def _parse_inline_list(raw: str) -> Optional[List[Any]]:
    """Parse an inline YAML list like ``[a, b]`` or ``["x", "y"]``.

    Args:
        raw: Raw YAML value string to test and parse.

    Returns:
        A Python list if the string looks like an inline list, otherwise ``None``.

    Example:
        >>> _parse_inline_list("[pester, powershell]")
        ['pester', 'powershell']
        >>> _parse_inline_list("not-a-list") is None
        True
    """
    m = _INLINE_LIST_RE.match(raw.strip())
    if not m:
        return None
    inner = m.group(1).strip()
    if not inner:
        return []
    items: List[Any] = []
    # csv.reader handles quoted fields in O(N) — avoids ReDoS on adversarial input
    for item in next(csv.reader(io.StringIO(inner), skipinitialspace=True), []):
        items.append(_coerce(item.strip()))
    return items


# ---------------------------------------------------------------------------
# Frontmatter parser (regex-based, best-effort, no PyYAML dependency)
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> Dict[str, Any]:
    """Extract YAML frontmatter from markdown text.

    Handles only the simple key: value pairs used in .cg-docs/ files:

    - Scalars (strings, booleans, integers, dates)
    - Inline lists: ``[a, b, c]``
    - Quoted strings: ``"value"`` or ``'value'``
    - Multi-line arrays (dash-prefixed) — emits a warning, collects items

    Strips a leading UTF-8 BOM (``\\ufeff``) and any leading blank lines before
    the frontmatter delimiter, since PowerShell here-strings add a leading
    ``\\r\\n`` before the first line of content.

    Args:
        text: Full markdown file content (including frontmatter).

    Returns:
        Dict of frontmatter key/value pairs, or ``{}`` if no frontmatter found.

    Example:
        >>> fm = parse_frontmatter("---\\ndate: 2026-05-19\\ntitle: Test\\n---\\n# Body")
        >>> fm["date"]
        '2026-05-19'
    """
    clean = text.lstrip("\ufeff\r\n")
    if not clean.startswith("---"):
        return {}

    end = clean.find("\n---", 3)
    if end == -1:
        return {}

    block = clean[3:end].strip()
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Continuation of a block list (  - item)
        if stripped.startswith("- ") and current_key is not None and current_list is not None:
            current_list.append(_coerce(stripped[2:].strip()))
            continue

        # Flush any in-progress block list before processing new key
        if current_list is not None and current_key is not None:
            if current_list:  # only store non-empty block lists
                result[current_key] = current_list
            current_key = None
            current_list = None

        if ":" not in stripped:
            continue

        key, _, raw_value = stripped.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()
        # Strip inline YAML comments (e.g. "status: active # deprecated" → "active")
        if " #" in raw_value:
            raw_value = raw_value.split(" #")[0].rstrip()

        if not raw_value:
            # Possibly a block-list key (next lines start with "- ")
            current_key = key
            current_list = []
            warnings.warn(
                f"Frontmatter key '{key}' has a multi-line value; "
                "only simple scalars and inline lists are fully supported.",
                stacklevel=2,
            )
            continue

        if key in result:
            warnings.warn(f"Duplicate frontmatter key '{key}'", stacklevel=2)
        inline = _parse_inline_list(raw_value)
        if inline is not None:
            result[key] = inline
        else:
            result[key] = _coerce(raw_value)

    # Flush trailing block list
    if current_list is not None and current_key is not None and current_list:
        result[current_key] = current_list

    return result


# ---------------------------------------------------------------------------
# Body parser: extract a plain-text summary (~100 words)
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,6}\s+")
_FENCED_RE = re.compile(r"^```")
_PROBLEM_HEADING_RE = re.compile(r"^#{1,2}\s+Problem\b", re.IGNORECASE)


def extract_summary(text: str, max_words: int = 100) -> str:
    """Extract a ~100-word plain-text summary from markdown body.

    Strategy (in order of preference):

    1. Content immediately following a ``## Problem`` heading.
    2. First non-heading, non-empty prose paragraph after frontmatter.

    Skips heading lines, fenced code blocks, and blank lines at the start.
    Truncates to ``max_words`` words, appending ``"..."`` if truncated.

    Args:
        text: Full markdown file content.
        max_words: Maximum number of words in the returned summary.

    Returns:
        Plain-text summary string, or ``""`` if no suitable paragraph found.

    Example:
        >>> extract_summary("---\\ndate: x\\n---\\n## Problem\\nThis is the problem.")
        'This is the problem.'
    """
    clean = text.lstrip("\ufeff\r\n")

    # Strip frontmatter
    body = clean
    if clean.startswith("---"):
        end = clean.find("\n---", 3)
        if end != -1:
            body = clean[end + 4:].lstrip("\n")

    lines = body.splitlines()

    # --- Pass 1: look for ## Problem section ---
    problem_lines: List[str] = []
    in_problem = False
    in_fence = False

    for line in lines:
        if _FENCED_RE.match(line):
            in_fence = not in_fence
            continue  # skip fence delimiter lines (both opening and closing)
        if in_fence:
            continue
        if _HEADING_RE.match(line):
            if in_problem:
                break
            if _PROBLEM_HEADING_RE.match(line):
                in_problem = True
            continue
        if in_problem and line.strip():
            problem_lines.append(line.strip())

    if problem_lines:
        return _truncate(" ".join(problem_lines), max_words)

    # --- Pass 2: first non-heading prose paragraph ---
    prose_lines: List[str] = []
    in_fence = False
    in_prose = False

    for line in lines:
        if _FENCED_RE.match(line):
            in_fence = not in_fence
            continue  # skip fence delimiter lines (both opening and closing)
        if in_fence:
            continue
        if _HEADING_RE.match(line):
            if in_prose:
                break
            continue
        stripped = line.strip()
        if stripped:
            in_prose = True
            prose_lines.append(stripped)
        elif in_prose:
            break

    if prose_lines:
        return _truncate(" ".join(prose_lines), max_words)

    return ""


def _truncate(text: str, max_words: int) -> str:
    """Truncate text to at most ``max_words`` words, appending ``'...'`` if truncated.

    Args:
        text: Input text string.
        max_words: Maximum number of whitespace-delimited words to keep.

    Returns:
        Truncated string with ``'...'`` appended if truncation occurred.

    Example:
        >>> _truncate("one two three four five", 3)
        'one two three...'
    """
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


# ---------------------------------------------------------------------------
# Atomic file writer
# ---------------------------------------------------------------------------


def write_atomic(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically via a temp file + ``os.replace()``.

    Prevents partially written files on process kill or other interruptions.
    Uses a temp file in the same directory as ``path`` to ensure the rename
    is atomic on the same filesystem.

    Args:
        path: Destination file path. Parent directory must already exist.
        content: Text content to write (UTF-8 encoded).

    Raises:
        OSError: If the temp file or final rename fails.

    Example:
        >>> from pathlib import Path
        >>> import tempfile, os
        >>> with tempfile.TemporaryDirectory() as d:
        ...     write_atomic(Path(d) / "out.txt", "hello")
    """
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)

        # OneDrive/AV/indexers can transiently lock destination files on Windows.
        # Retry replace a few times, then fall back to in-place overwrite.
        retries = 6
        replaced = False
        for attempt in range(retries):
            try:
                os.replace(tmp_path, path)
                replaced = True
                break
            except PermissionError:
                if os.name != "nt" or attempt == retries - 1:
                    break
                time.sleep(0.05 * (attempt + 1))

        if not replaced:
            if os.name == "nt":
                with path.open("w", encoding="utf-8", newline="\n") as fh:
                    fh.write(content)
                os.unlink(tmp_path)
            else:
                os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
