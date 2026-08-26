"""Shared markdown parsing helpers for Compound GPID scripts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from brain.utils import parse_frontmatter

_FRONTMATTER_RE = re.compile(
    r"^\ufeff?---[ \t]*(?:\r?\n)(.*?)^---[ \t]*\r?$(?:\r?\n)?",
    re.DOTALL | re.MULTILINE,
)

_ASCII_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_ASCII_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_SIMPLE_SCALAR_RE = re.compile(r"^[A-Za-z0-9._/+-]+$")
_ASCII_PRINTABLE_RE = re.compile(r"^[\x20-\x7e]*$")
_CLOSING_FENCE_RE = re.compile(r"^---[ \t]*$")

# Known top-level project-config fields. Unrecognized keys fail with remediation.
KNOWN_CONFIG_FIELDS = frozenset({
    "language",
    "project-type",
    "review-depth",
    "r-syntax",
    "suites",
    "capabilities",
    "created",
    "cg-schema-version",
    "config-schema-version",
})

# Advisory metadata is intentionally non-executable and does not participate in
# suite/capability resolution. It may use nested YAML because its independent
# validator treats malformed advisory preferences as warnings, while this
# parser continues to enforce the restricted grammar for selection fields.
NON_SELECTION_BLOCK_FIELDS = frozenset({"model-advisory"})


def parse_frontmatter_with_body(content: str) -> tuple[dict[str, Any], str]:
    """Split markdown content into parsed frontmatter and body text."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    # Parse only the matched frontmatter document. Passing the entire markdown
    # file lets body-level ``---`` dividers influence permissive YAML parsers.
    return parse_frontmatter(match.group(0)), content[match.end():]


@dataclass
class StrictConfig:
    """Strictly parsed project configuration (R3/R4).

    ``suites`` and ``capabilities`` collect the inline flow-list fields; scalar
    fields like ``language`` and ``project-type`` live in ``settings``.
    ``errors`` is non-empty when the restricted grammar rejected the input.
    """

    suites: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    settings: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def scalar(self, key: str) -> Optional[str]:
        return self.settings.get(key)


def _strip_yaml_comment(value: str) -> str:
    """Strip a trailing YAML ``# comment`` outside of quotes."""
    in_single = in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return value[:index].rstrip()
    return value


def _parse_scalar_value(value: str, line_number: int, errors: list[str], field_name: str) -> None:
    """Validate a quoted or bare simple scalar. Errors appended for invalid forms."""
    if value.startswith("'") or value.startswith('"'):
        if len(value) < 2 or value[-1] != value[0]:
            errors.append(f"line {line_number}: scalar {field_name} has an unterminated quote")
            return
        inner = value[1:-1]
        if not _ASCII_PRINTABLE_RE.fullmatch(inner):
            errors.append(f"line {line_number}: scalar {field_name} contains non-ASCII or control characters")
        return
    if not _SIMPLE_SCALAR_RE.fullmatch(value):
        errors.append(
            f"line {line_number}: scalar {field_name} must be a quoted or simple bare value "
            "(no anchors, tags, block scalars, nested structures, or special punctuation)"
        )


def _parse_flow_list(value: str, line_number: int, errors: list[str], field_name: str) -> list[str]:
    """Parse an inline flow list of quoted or ASCII identifier values."""
    if not (value.startswith("[") and value.endswith("]")):
        errors.append(
            f"line {line_number}: {field_name} must be an inline list, e.g. {field_name}: [cg, cr]"
        )
        return []
    inner = value[1:-1]
    items: list[str] = []
    seen: set[str] = set()
    for raw in inner.split(","):
        item = raw.strip().strip("\"' ")
        if not item:
            errors.append(f"line {line_number}: {field_name} list contains an empty element")
            continue
        if not _ASCII_IDENTIFIER_RE.fullmatch(item):
            errors.append(
                f"line {line_number}: {field_name} element {item!r} is not a lowercase ASCII identifier"
            )
            continue
        if item in seen:
            errors.append(f"line {line_number}: {field_name} contains duplicate value {item!r}")
        seen.add(item)
        items.append(item)
    return items


def parse_strict_config(text: str) -> StrictConfig:
    """Parse ``compound-gpid.local.md`` against the strict restricted grammar.

    Accepts only UTF-8 without BOM, a top-level delimited frontmatter block,
    ASCII identifier keys, quoted or simple scalar values, and inline lists of
    quoted or ASCII identifier values. Rejects duplicate keys, anchors, aliases,
    tags, block scalars, nested mappings/sequences, tabs, non-ASCII control
    characters, and any unrecognized key with line/field remediation.

    Note: an absent ``suites:`` field is NOT an error here; the caller decides
    the legacy ``[cg]`` default. Empty/scalar/malformed/unknown suite inputs do
    fail.
    """
    result = StrictConfig()
    if text.startswith("\ufeff"):
        result.errors.append("file must be UTF-8 without BOM")
        return result
    open_idx = text.find("---")
    if open_idx == -1 or text[:open_idx].strip(" \t\r\n") != "":
        result.errors.append("missing top-level frontmatter delimiter '---'")
        return result
    opening_line = text.count("\n", 0, open_idx) + 1
    all_lines = text.split("\n")
    closing = None
    for index in range(opening_line, len(all_lines)):
        if _CLOSING_FENCE_RE.fullmatch(all_lines[index].rstrip("\r")):
            closing = index
            break
    if closing is None:
        result.errors.append("frontmatter block is missing a closing '---' delimiter")
        return result
    lines = [all_lines[index].rstrip("\r") for index in range(opening_line, closing)]
    seen_keys: set[str] = set()
    active_nonselection_block: Optional[str] = None
    for line_number, line in enumerate(lines, start=opening_line + 1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if (
            not line[0].isspace()
            and ":" in line
            and line.split(":", 1)[0].rstrip(" \t") in NON_SELECTION_BLOCK_FIELDS
        ):
            active_nonselection_block = line.split(":", 1)[0].rstrip(" \t")
            continue
        if line[0].isspace() and active_nonselection_block is not None:
            continue
        if "\t" in line:
            result.errors.append(f"line {line_number}: tab characters are not allowed")
            continue
        if line[0].isspace():
            result.errors.append(
                f"line {line_number}: indented/nested values are not allowed; use inline lists"
            )
            continue
        active_nonselection_block = None
        if ":" not in line:
            result.errors.append(f"line {line_number}: expected a 'key: value' line")
            continue
        key, raw_value = line.split(":", 1)
        if not _ASCII_KEY_RE.fullmatch(key):
            result.errors.append(f"line {line_number}: key {key!r} is not an ASCII identifier")
            continue
        if key in seen_keys:
            result.errors.append(f"line {line_number}: duplicate key {key!r}")
            continue
        seen_keys.add(key)
        if key not in KNOWN_CONFIG_FIELDS:
            result.errors.append(
                f"line {line_number}: unrecognized config key {key!r}; remove it or migrate it "
                "before strict resolution"
            )
            continue
        value = _strip_yaml_comment(raw_value.strip())
        if key in ("suites", "capabilities"):
            if not value:
                result.errors.append(f"line {line_number}: {key} must not be empty")
                continue
            items = _parse_flow_list(value, line_number, result.errors, key)
            if key == "suites":
                result.suites = items
            else:
                result.capabilities = items
            continue
        if not value:
            result.errors.append(f"line {line_number}: {key} must have a value")
            continue
        if value.startswith("[") or value.startswith("{"):
            result.errors.append(
                f"line {line_number}: {key} must be a scalar, not a list or mapping"
            )
            continue
        quoted = value.startswith(("'", '"'))
        if not quoted and any(tag in value for tag in ("&", "*", "!", "|", ">", ":", "{")):
            result.errors.append(
                f"line {line_number}: {key} contains anchors, tags, block scalars, or nested values"
            )
            continue
        errors_before = len(result.errors)
        _parse_scalar_value(value, line_number, result.errors, key)
        if len(result.errors) == errors_before:
            result.settings[key] = value.strip("\"' ")
    return result
