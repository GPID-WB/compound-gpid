"""Structured escaping, URL policy, and final HTML security validation."""
from __future__ import annotations

from html import escape, unescape
from html.parser import HTMLParser
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlsplit

from artifact_views.errors import ArtifactSecurityError

_SAFE_SCHEMES = frozenset({"http", "https", "mailto"})
_FRAGMENT_RE = re.compile(r"^#[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_INLINE_DELIMITERS = ("`", "**", "__", "*", "_", "](", ")", ">")


def safe_url(raw_url: str) -> str:
    """Validate a source-derived link URL against the offline-safe policy.

    Relative paths and valid fragments are allowed. Explicit ``http``,
    ``https``, and ``mailto`` links are allowed as user-initiated navigation,
    never as runtime resources.

    Args:
        raw_url: Untrusted URL text from canonical Markdown.

    Returns:
        The stripped original URL when it is safe for an ``href`` attribute.

    Raises:
        ArtifactSecurityError: If the URL is malformed or uses an unsafe scheme.

    Example:
        >>> safe_url("../plans/example.md")
        '../plans/example.md'
    """
    candidate = unescape(raw_url).strip()
    if not candidate:
        raise ArtifactSecurityError("Link URL must be non-empty.")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in candidate):
        raise ArtifactSecurityError("Link URL contains control characters.")
    decoded = candidate
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    compact_prefix = re.sub(r"\s+", "", decoded.split("/", 1)[0]).casefold()
    if compact_prefix.startswith(("javascript:", "vbscript:", "data:", "file:")):
        raise ArtifactSecurityError(
            "Link URL scheme is unsafe.",
            corrective_action="Use a relative URL, fragment, http, https, or mailto link.",
        )
    if candidate.startswith("#"):
        if not _FRAGMENT_RE.fullmatch(candidate):
            raise ArtifactSecurityError("Link fragment is malformed.")
        return candidate
    if candidate.startswith(("//", "/")) or "\\" in candidate:
        raise ArtifactSecurityError("Link URL must be relative, not protocol-relative or absolute.")

    parsed = urlsplit(decoded)
    scheme = parsed.scheme.casefold()
    if not scheme:
        if ":" in decoded.split("/", 1)[0]:
            raise ArtifactSecurityError("Link URL has an unrecognized scheme.")
        return candidate
    if scheme not in _SAFE_SCHEMES:
        raise ArtifactSecurityError(
            f"Link URL scheme {scheme!r} is not allowed.",
            corrective_action="Use a relative URL, fragment, http, https, or mailto link.",
        )
    if scheme in {"http", "https"} and not parsed.netloc:
        raise ArtifactSecurityError("HTTP link URL must include a host.")
    if scheme == "mailto" and not parsed.path:
        raise ArtifactSecurityError("mailto link URL must include an address.")
    return candidate


def render_safe_inline(value: str) -> str:
    """Render the closed inline grammar using structured escaped fragments.

    Args:
        value: Untrusted source inline text.

    Returns:
        HTML containing only escaped text and allowlisted inline elements.

    Raises:
        ArtifactSecurityError: If a source-derived link is unsafe.

    Example:
        >>> render_safe_inline("Use `code`.")
        'Use <code>code</code>.'
    """
    next_positions = {
        delimiter: _next_delimiter_positions(value, delimiter)
        for delimiter in _INLINE_DELIMITERS
    }
    rendered: List[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value) and value[index + 1] != "\n":
            rendered.append(escape(value[index + 1]))
            index += 2
            continue

        delimiter = None
        tag = None
        if value.startswith("**", index):
            delimiter, tag = "**", "strong"
        elif value.startswith("__", index):
            delimiter, tag = "__", "strong"
        elif value[index] == "*":
            delimiter, tag = "*", "em"
        elif value[index] == "_":
            delimiter, tag = "_", "em"
        if delimiter is not None:
            closing = next_positions[delimiter][index + len(delimiter)]
            if closing >= 0:
                inner = value[index + len(delimiter) : closing]
                if inner and "\n" not in inner:
                    rendered.append(f"<{tag}>{escape(inner)}</{tag}>")
                    index = closing + len(delimiter)
                    continue

        if value[index] == "`":
            closing = next_positions["`"][index + 1]
            if closing >= 0:
                inner = value[index + 1 : closing]
                if inner and "\n" not in inner:
                    rendered.append(f"<code>{escape(inner)}</code>")
                    index = closing + 1
                    continue

        if value[index] == "[":
            label_end = next_positions["]("][index + 1]
            if label_end >= 0:
                url_end = next_positions[")"][label_end + 2]
                if url_end >= 0:
                    label = value[index + 1 : label_end]
                    url = value[label_end + 2 : url_end]
                    if label and url and "\n" not in label and "\n" not in url:
                        href = safe_url(url)
                        rendered.append(
                            f'<a href="{escape(href, quote=True)}">'
                            f"{escape(label)}</a>"
                        )
                        index = url_end + 1
                        continue

        if value[index] == "<":
            closing = next_positions[">"][index + 1]
            if closing >= 0:
                target = value[index + 1 : closing]
                if target and "\n" not in target:
                    candidate = (
                        f"mailto:{target}"
                        if "@" in target and ":" not in target
                        else target
                    )
                    parsed = urlsplit(candidate)
                    if parsed.scheme.casefold() in _SAFE_SCHEMES:
                        href = safe_url(candidate)
                        rendered.append(
                            f'<a href="{escape(href, quote=True)}">'
                            f"{escape(target)}</a>"
                        )
                        index = closing + 1
                        continue

        rendered.append(escape(value[index]))
        index += 1
    return "".join(rendered)


def _next_delimiter_positions(value: str, delimiter: str) -> List[int]:
    """Build constant-time next-occurrence lookups for one delimiter."""
    positions = [-1] * (len(value) + 1)
    next_position = -1
    for index in range(len(value) - 1, -1, -1):
        if value.startswith(delimiter, index):
            next_position = index
        positions[index] = next_position
    return positions


def validate_html_security(html_text: str) -> None:
    """Validate final HTML structure before bytes are returned or written.

    Args:
        html_text: Complete generated HTML document.

    Returns:
        None after successful structural validation.

    Raises:
        ArtifactSecurityError: If IDs, attributes, scripts, resource URLs, or
            executable elements violate the frozen output policy.

    Example:
        ``validate_html_security('<main id="content"></main>')`` returns None.
    """
    parser = _SecurityParser()
    try:
        parser.feed(html_text)
        parser.close()
    except ArtifactSecurityError:
        raise
    except Exception as error:
        raise ArtifactSecurityError(
            f"Generated HTML could not be structurally validated: {error}."
        ) from error
    if parser.provenance_scripts > 1:
        raise ArtifactSecurityError("Generated HTML contains duplicate provenance scripts.")


class _SecurityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.provenance_scripts = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attributes: Dict[str, Optional[str]] = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                raise ArtifactSecurityError(f"Duplicate HTML id {element_id!r}.")
            self.ids.add(element_id)
        for name, value in attrs:
            lowered = name.casefold()
            if lowered.startswith("on"):
                raise ArtifactSecurityError(
                    f"Event handler attribute {name!r} is forbidden."
                )
            if lowered == "style":
                raise ArtifactSecurityError(
                    "Source-derived style attributes are forbidden."
                )
            if lowered == "href" and value is not None:
                safe_url(value)
            if lowered in {"src", "srcset", "poster", "data"}:
                raise ArtifactSecurityError(
                    f"Runtime resource attribute {name!r} is forbidden."
                )
        if tag in {"iframe", "object", "embed", "base", "form"}:
            raise ArtifactSecurityError(f"Executable or navigational element <{tag}> is forbidden.")
        if tag == "script":
            if not (
                attributes.get("id") == "artifact-provenance"
                and attributes.get("type") == "application/json"
                and "src" not in attributes
            ):
                raise ArtifactSecurityError("Executable script elements are forbidden.")
            self.provenance_scripts += 1
        if tag == "meta" and (attributes.get("http-equiv") or "").casefold() == "refresh":
            raise ArtifactSecurityError("Meta refresh is forbidden.")
