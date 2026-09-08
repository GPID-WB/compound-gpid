"""Source-span strict project capability edit planning."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Tuple

from parsing_utils import parse_strict_config


_CAPABILITY_ID = re.compile(r"^[a-z][a-z0-9-]*$")
_OPENING = re.compile(br"\A---[ \t]*(\r?\n)")
_CLOSING = re.compile(br"(?m)^---[ \t]*(?:\r?\n|\Z)")
_CAPABILITIES = re.compile(
    br"(?m)^capabilities:[ \t]*(\[[^\r\n]*\])([ \t]*(?:#[^\r\n]*)?)(\r?\n|\Z)"
)


class ConfigEditError(ValueError):
    """Raised when a strict byte-preserving capability edit is not possible."""


@dataclass(frozen=True)
class ConfigEdit:
    """Exact prior/new config bytes and semantic explicit capabilities."""

    before: bytes
    after: bytes
    before_digest: str
    after_digest: str
    capabilities: Tuple[str, ...]

    @property
    def changed(self) -> bool:
        """Return whether publication changes any config byte."""
        return self.before != self.after


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _raw_items(value: bytes) -> Tuple[Tuple[str, bytes], ...]:
    try:
        text = value.decode("ascii")
    except UnicodeDecodeError as error:
        raise ConfigEditError("capabilities inline list must be ASCII") from error
    inner = text[1:-1]
    if not inner.strip():
        return ()
    result = []
    for raw in inner.split(","):
        token = raw.strip()
        semantic = token.strip("\"'")
        if _CAPABILITY_ID.fullmatch(semantic) is None:
            raise ConfigEditError(
                f"capabilities contains an invalid identifier: {semantic!r}"
            )
        result.append((semantic, token.encode("ascii")))
    return tuple(result)


def plan_capability_edit(
    content: bytes,
    capability: str,
    *,
    activate: bool,
) -> ConfigEdit:
    """Plan one exact top-level inline ``capabilities`` source-span edit.

    Every byte outside the inline-list value (or one inserted field) remains
    unchanged, including line endings, comments, quoting, field order, and body.
    """
    if _CAPABILITY_ID.fullmatch(capability) is None:
        raise ConfigEditError("Capability must be a lowercase ASCII identifier")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConfigEditError("Project config must be valid UTF-8") from error
    parsed = parse_strict_config(text)
    if parsed.errors:
        raise ConfigEditError("; ".join(parsed.errors[:5]))
    opening = _OPENING.search(content)
    if opening is None:
        raise ConfigEditError("Project config has no exact opening frontmatter delimiter")
    closing = _CLOSING.search(content, opening.end())
    if closing is None:
        raise ConfigEditError("Project config has no closing frontmatter delimiter")
    block = content[opening.end():closing.start()]
    matches = list(_CAPABILITIES.finditer(block))
    if len(matches) > 1:
        raise ConfigEditError("Project config has duplicate capabilities fields")

    if matches:
        match = matches[0]
        raw_items = list(_raw_items(match.group(1)))
        semantic = [item[0] for item in raw_items]
        if activate:
            if capability in semantic:
                after = content
            else:
                raw_items.append((capability, capability.encode("ascii")))
                after = _replace_value(content, opening.end(), match, raw_items)
        else:
            if capability not in semantic:
                after = content
            else:
                raw_items = [item for item in raw_items if item[0] != capability]
                after = _replace_value(content, opening.end(), match, raw_items)
    elif activate:
        newline = opening.group(1)
        insertion = b"capabilities: [" + capability.encode("ascii") + b"]" + newline
        after = content[:closing.start()] + insertion + content[closing.start():]
    else:
        after = content

    try:
        after_text = after.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConfigEditError("Planned config bytes are not valid UTF-8") from error
    after_parsed = parse_strict_config(after_text)
    if after_parsed.errors:
        raise ConfigEditError("Planned config does not pass strict resolution: " + "; ".join(after_parsed.errors[:5]))
    return ConfigEdit(
        content,
        after,
        _digest(content),
        _digest(after),
        tuple(after_parsed.capabilities),
    )


def _replace_value(
    content: bytes,
    block_offset: int,
    match: re.Match,
    raw_items: list,
) -> bytes:
    value = b"[" + b", ".join(item[1] for item in raw_items) + b"]"
    start = block_offset + match.start(1)
    end = block_offset + match.end(1)
    return content[:start] + value + content[end:]
