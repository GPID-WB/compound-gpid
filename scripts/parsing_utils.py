"""Shared markdown parsing helpers for Compound GPID scripts."""
from __future__ import annotations

import re
from typing import Any

from brain.utils import parse_frontmatter

_FRONTMATTER_RE = re.compile(r"^\ufeff?---\s*\n(.*?)^---\s*\n?", re.DOTALL | re.MULTILINE)


def parse_frontmatter_with_body(content: str) -> tuple[dict[str, Any], str]:
    """Split markdown content into parsed frontmatter and body text."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    return parse_frontmatter(content), content[match.end():]
