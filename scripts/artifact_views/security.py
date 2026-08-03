"""Structured escaping, URL policy, and final HTML security validation."""
from __future__ import annotations

import base64
from dataclasses import dataclass, field
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import posixpath
import re
import struct
from typing import Dict, List, Optional, Tuple
import unicodedata
from urllib.parse import unquote, urlsplit
import zlib

from artifact_views.errors import ArtifactSecurityError
from secure_fs import secure_read_bytes

_SAFE_SCHEMES = frozenset({"http", "https", "mailto"})
_FRAGMENT_RE = re.compile(r"^#[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_INLINE_TOKEN_RE = re.compile(
    r"(?P<escape>\\[^\r\n])"
    r"|(?P<image>!\[(?P<image_alt>[^\]\r\n]*)\]\((?P<image_uri>[^)\r\n]+)\))"
    r"|(?P<link>\[(?P<link_label>[^\]\r\n]+)\]\((?P<link_uri>[^)\r\n]+)\))"
    r"|(?P<code>`(?P<code_text>[^`\r\n]+)`)"
    r"|(?P<strong_ast>\*\*(?P<strong_ast_text>[^*\r\n]+)\*\*)"
    r"|(?P<strong_under>__(?P<strong_under_text>[^_\r\n]+)__ )"
    r"|(?P<em_ast>\*(?P<em_ast_text>[^*\r\n]+)\*)"
    r"|(?P<em_under>_(?P<em_under_text>[^_\r\n]+)_ )"
    r"|(?P<autolink><(?P<autolink_text>[^>\r\n]+)>)",
    re.VERBOSE,
)
_DATA_IMAGE_RE = re.compile(
    r"^data:image/(?P<format>png|jpeg|gif|webp);base64,(?P<payload>[A-Za-z0-9+/]+={0,2})$"
)
_IMAGE_FORMATS = {
    ".png": ("image/png", "png"),
    ".jpg": ("image/jpeg", "jpeg"),
    ".jpeg": ("image/jpeg", "jpeg"),
    ".gif": ("image/gif", "gif"),
    ".webp": ("image/webp", "webp"),
}
_WINDOWS_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
_MAX_BITMAP_PIXELS = 16 * 1024 * 1024
_MAX_DECODED_BITMAP_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class EmbeddedBitmap:
    """One normalized source-relative bitmap ready for safe HTML output."""

    source_relative: Path
    alt_text: str
    data_uri: str


@dataclass
class GenericRenderContext:
    """Document-scoped resource cache and cumulative rendering budgets."""

    project_root: Path
    source_relative: Path
    output_relative: Path
    max_image_bytes: int
    max_total_image_bytes: int
    max_image_count: int
    max_output_bytes: int
    cache: Dict[str, Tuple[EmbeddedBitmap, int]] = field(default_factory=dict)
    total_image_bytes: int = 0
    image_count: int = 0
    output_bytes: int = 0

    def charge_output(self, byte_count: int) -> None:
        """Reserve output bytes before allocating a rendered fragment.

        Args:
            byte_count: Exact UTF-8 byte count of the pending fragment.

        Returns:
            ``None`` after charging the document output budget.

        Example:
            Inline rendering charges escaped text and each emitted data URI.
        """
        if byte_count < 0:
            raise ValueError("Output byte charge cannot be negative.")
        if self.output_bytes + byte_count > self.max_output_bytes:
            raise ArtifactSecurityError(
                "Generic document exceeds the rendered output budget."
            )
        self.output_bytes += byte_count

    def image(self, raw_uri: str, raw_alt_text: str) -> EmbeddedBitmap:
        """Return one cached verified bitmap while charging emission budgets.

        Args:
            raw_uri: Untrusted source-relative image URI.
            raw_alt_text: Untrusted image alternative text.

        Returns:
            Verified bitmap with normalized identity, alt text, and data URI.

        Example:
            Repeated calls for one URI reuse verified bytes but count emissions.
        """
        image_relative = _resolve_image_uri(self.source_relative, raw_uri)
        cache_key = image_relative.as_posix()
        cached = self.cache.get(cache_key)
        if cached is None:
            image, raw_size = _read_local_bitmap(
                self.project_root,
                image_relative,
                raw_alt_text,
                max_bytes=self.max_image_bytes,
            )
            if self.total_image_bytes + raw_size > self.max_total_image_bytes:
                raise ArtifactSecurityError(
                    "Generic document exceeds the cumulative raw image budget."
                )
            self.total_image_bytes += raw_size
            self.cache[cache_key] = (image, raw_size)
        else:
            image, _raw_size = cached
            image = EmbeddedBitmap(
                image.source_relative,
                _normalize_alt_text(raw_alt_text),
                image.data_uri,
            )
        self.image_count += 1
        if self.image_count > self.max_image_count:
            raise ArtifactSecurityError(
                "Generic document exceeds the image count budget."
            )
        return image


def embed_local_bitmap(
    project_root: Path,
    source_relative: Path,
    raw_uri: str,
    raw_alt_text: str,
    *,
    max_bytes: int,
) -> EmbeddedBitmap:
    """Resolve, bound, verify, and encode one local bitmap from a pinned handle.

    Args:
        project_root: Existing project root for secure reads.
        source_relative: Project-relative Markdown source identity.
        raw_uri: Untrusted source-relative image URI.
        raw_alt_text: Untrusted image alternative text.
        max_bytes: Maximum accepted image byte count.

    Returns:
        Verified normalized identity, alt text, and deterministic data URI.

    Raises:
        ArtifactSecurityError: If identity, bytes, or text violate the contract.

    Example:
        A PNG at ``docs/assets/a.png`` may be embedded from ``docs/guide.md``.
    """
    image_relative = _resolve_image_uri(source_relative, raw_uri)
    image, _raw_size = _read_local_bitmap(
        project_root,
        image_relative,
        raw_alt_text,
        max_bytes=max_bytes,
    )
    return image


def _read_local_bitmap(
    project_root: Path,
    image_relative: Path,
    raw_alt_text: str,
    *,
    max_bytes: int,
) -> Tuple[EmbeddedBitmap, int]:
    alt_text = _normalize_alt_text(raw_alt_text)
    suffix = image_relative.suffix.casefold()
    format_contract = _IMAGE_FORMATS.get(suffix)
    if format_contract is None:
        raise ArtifactSecurityError(
            "Image suffix is not an allowed bitmap format.",
            corrective_action="Use PNG, JPEG, GIF, or WebP.",
        )
    try:
        content = secure_read_bytes(
            Path(project_root),
            image_relative,
            max_bytes=max_bytes,
            reject_hardlinks=True,
        )
    except (OSError, ValueError) as error:
        raise ArtifactSecurityError(
            f"Local bitmap could not be read securely: {error}",
            source_path=image_relative,
            corrective_action=(
                "Use one regular project-contained bitmap within the byte limit."
            ),
        ) from error
    mime_type, format_name = format_contract
    if not _valid_bitmap_container(format_name, content):
        raise ArtifactSecurityError(
            "Image suffix and bitmap container structure do not match.",
            source_path=image_relative,
            corrective_action="Use a valid PNG, JPEG, GIF, or WebP file.",
        )
    payload = base64.b64encode(content).decode("ascii")
    return (
        EmbeddedBitmap(
            source_relative=image_relative,
            alt_text=alt_text,
            data_uri=f"data:{mime_type};base64,{payload}",
        ),
        len(content),
    )


def render_generic_inline(
    value: str,
    *,
    context: GenericRenderContext,
) -> str:
    """Render safe inline Markdown plus verified local bitmap syntax.

    Args:
        value: Untrusted inline Markdown source.
        context: Document-scoped resource cache and rendering budgets.

    Returns:
        Escaped allowlisted inline HTML with verified bitmap data URIs.

    Example:
        Plain text renders without a project root; image syntax requires one.
    """
    return _render_inline_tokens(value, context=context)


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
    return _render_inline_tokens(value, context=None)


def _render_inline_tokens(
    value: str,
    *,
    context: Optional[GenericRenderContext],
) -> str:
    rendered: List[str] = []
    position = 0
    for match in _INLINE_TOKEN_RE.finditer(value):
        _append_escaped(
            rendered,
            value[position : match.start()],
            context,
        )
        group = match.lastgroup
        if group == "escape":
            _append_escaped(rendered, match.group()[1:], context)
        elif group == "image":
            if context is None:
                _append_escaped(rendered, match.group(), context)
            else:
                image = context.image(
                    match.group("image_uri"),
                    match.group("image_alt"),
                )
                fragment = (
                    f'<img src="{image.data_uri}" '
                    f'alt="{escape(image.alt_text, quote=True)}">'
                )
                context.charge_output(len(fragment.encode("utf-8")))
                rendered.append(fragment)
        elif group == "link":
            href = safe_url(match.group("link_uri"))
            if context is not None:
                href = _rebase_relative_link(href, context)
            fragment = (
                f'<a href="{escape(href, quote=True)}">'
                f'{escape(match.group("link_label"))}</a>'
            )
            _append_fragment(rendered, fragment, context)
        elif group == "code":
            fragment = f'<code>{escape(match.group("code_text"))}</code>'
            _append_fragment(rendered, fragment, context)
        elif group in {"strong_ast", "strong_under"}:
            fragment = (
                f'<strong>{escape(match.group(f"{group}_text"))}</strong>'
            )
            _append_fragment(rendered, fragment, context)
        elif group in {"em_ast", "em_under"}:
            fragment = f'<em>{escape(match.group(f"{group}_text"))}</em>'
            _append_fragment(rendered, fragment, context)
        elif group == "autolink":
            target = match.group("autolink_text")
            candidate = f"mailto:{target}" if "@" in target and ":" not in target else target
            parsed = urlsplit(candidate)
            if parsed.scheme.casefold() in _SAFE_SCHEMES:
                href = safe_url(candidate)
                fragment = (
                    f'<a href="{escape(href, quote=True)}">{escape(target)}</a>'
                )
                _append_fragment(rendered, fragment, context)
            else:
                _append_escaped(rendered, match.group(), context)
        position = match.end()
    _append_escaped(rendered, value[position:], context)
    return "".join(rendered)


def _append_fragment(
    rendered: List[str],
    fragment: str,
    context: Optional[GenericRenderContext],
) -> None:
    if context is not None:
        context.charge_output(len(fragment.encode("utf-8")))
    rendered.append(fragment)


def _append_escaped(
    rendered: List[str],
    value: str,
    context: Optional[GenericRenderContext],
) -> None:
    if context is not None:
        context.charge_output(_escaped_utf8_length(value))
    rendered.append(escape(value))


def _escaped_utf8_length(value: str) -> int:
    replacements = {"&": 5, "<": 4, ">": 4, '"': 6, "'": 5}
    return sum(
        replacements.get(character, len(character.encode("utf-8")))
        for character in value
    )


def _rebase_relative_link(
    href: str,
    context: GenericRenderContext,
) -> str:
    if href.startswith("#") or urlsplit(href).scheme:
        return href
    source = PurePosixPath(context.source_relative.as_posix())
    output = PurePosixPath(context.output_relative.as_posix())
    target = posixpath.normpath((source.parent / href).as_posix())
    if target == ".." or target.startswith("../"):
        raise ArtifactSecurityError("Relative link escapes the project root.")
    return posixpath.relpath(target, output.parent.as_posix())


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
            if lowered == "src" and tag == "img" and value is not None:
                _validate_data_image(value)
            elif lowered in {"src", "srcset", "poster", "data"}:
                raise ArtifactSecurityError(
                    f"Runtime resource attribute {name!r} is forbidden."
                )
        if tag == "img":
            alt_text = attributes.get("alt")
            if alt_text is None or not _normalize_alt_text(alt_text):
                raise ArtifactSecurityError(
                    "Generated image alt text must be non-empty."
                )
            if attributes.get("src") is None:
                raise ArtifactSecurityError("Generated image src is required.")
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


def _normalize_alt_text(raw_alt_text: str) -> str:
    normalized = unicodedata.normalize("NFC", raw_alt_text)
    if any(
        ord(character) < 32 and not character.isspace()
        for character in normalized
    ):
        raise ArtifactSecurityError("Image alt text contains control characters.")
    normalized = " ".join(normalized.split())
    if not normalized:
        raise ArtifactSecurityError("Image alt text must be non-empty.")
    return normalized


def _resolve_image_uri(source_relative: Path, raw_uri: str) -> Path:
    if not raw_uri or "\\" in raw_uri:
        raise ArtifactSecurityError("Image URI contains an ambiguous separator.")
    decoded = raw_uri
    for _ in range(3):
        if re.search(r"%2f|%5c", decoded, re.IGNORECASE):
            raise ArtifactSecurityError("Image URI contains an encoded separator.")
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    if "%" in decoded:
        raise ArtifactSecurityError("Image URI contains malformed encoding.")
    if any(ord(character) < 32 or ord(character) == 127 for character in decoded):
        raise ArtifactSecurityError("Image URI contains control characters.")
    parsed = urlsplit(decoded)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ArtifactSecurityError(
            "Image URI must have no scheme, authority, query, or fragment."
        )
    if decoded.startswith("/"):
        raise ArtifactSecurityError("Image URI must be source-relative.")
    source = PurePosixPath(Path(source_relative).as_posix())
    if source.is_absolute() or ".." in source.parts:
        raise ArtifactSecurityError("Image source identity must be project-relative.")
    normalized = posixpath.normpath((source.parent / decoded).as_posix())
    if normalized in {"", ".", ".."} or normalized.startswith("../"):
        raise ArtifactSecurityError("Image URI escapes the project root.")
    image = PurePosixPath(normalized)
    if any(part in {"", ".", ".."} for part in image.parts):
        raise ArtifactSecurityError("Image URI has ambiguous path identity.")
    for part in image.parts:
        if (
            ":" in part
            or part.endswith((" ", "."))
            or part.split(".", 1)[0].upper() in _WINDOWS_DEVICE_NAMES
            or any(ord(character) < 32 for character in part)
        ):
            raise ArtifactSecurityError(
                "Image URI contains a nonportable path component."
            )
    return Path(*image.parts)


def _validate_data_image(value: str) -> None:
    match = _DATA_IMAGE_RE.fullmatch(value)
    if match is None:
        raise ArtifactSecurityError(
            "Only renderer-generated bitmap data image sources are allowed."
        )
    try:
        content = base64.b64decode(match.group("payload"), validate=True)
    except ValueError as error:
        raise ArtifactSecurityError("Generated bitmap data URI is malformed.") from error
    suffix = ".jpg" if match.group("format") == "jpeg" else f".{match.group('format')}"
    _mime_type, format_name = _IMAGE_FORMATS[suffix]
    if not _valid_bitmap_container(format_name, content):
        raise ArtifactSecurityError(
            "Generated bitmap data URI container does not match its media type."
        )


def _valid_bitmap_container(format_name: str, content: bytes) -> bool:
    validators = {
        "png": _valid_png,
        "jpeg": _valid_jpeg,
        "gif": _valid_gif,
        "webp": _valid_webp,
    }
    return validators[format_name](content)


def _valid_png(content: bytes) -> bool:
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    position = 8
    seen_ihdr = False
    seen_idat = False
    image_data = bytearray()
    width = 0
    height = 0
    bit_depth = 0
    color_type = 0
    interlace = 0
    while position + 12 <= len(content):
        length = struct.unpack(">I", content[position : position + 4])[0]
        chunk_type = content[position + 4 : position + 8]
        chunk_end = position + 12 + length
        if chunk_end > len(content):
            return False
        data = content[position + 8 : position + 8 + length]
        expected_crc = struct.unpack(">I", content[position + 8 + length : chunk_end])[0]
        if zlib.crc32(chunk_type + data) & 0xFFFFFFFF != expected_crc:
            return False
        if not seen_ihdr:
            if chunk_type != b"IHDR" or length != 13:
                return False
            width, height = struct.unpack(">II", data[:8])
            if width == 0 or height == 0:
                return False
            bit_depth, color_type, compression, filter_method, interlace = data[8:13]
            valid_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            if (
                bit_depth not in valid_depths.get(color_type, set())
                or compression != 0
                or filter_method != 0
                or interlace not in {0, 1}
            ):
                return False
            seen_ihdr = True
        elif chunk_type == b"IDAT":
            seen_idat = True
            image_data.extend(data)
        elif chunk_type == b"IEND":
            return (
                length == 0
                and seen_idat
                and chunk_end == len(content)
                and _valid_png_scanlines(
                    bytes(image_data),
                    width,
                    height,
                    bit_depth,
                    color_type,
                    interlace,
                )
            )
        position = chunk_end
    return False


def _valid_png_scanlines(
    compressed: bytes,
    width: int,
    height: int,
    bit_depth: int,
    color_type: int,
    interlace: int,
) -> bool:
    expected_size = _png_expected_scanline_bytes(
        width,
        height,
        bit_depth,
        color_type,
        interlace,
    )
    if (
        expected_size <= 0
        or width * height > _MAX_BITMAP_PIXELS
        or expected_size > _MAX_DECODED_BITMAP_BYTES
    ):
        return False
    try:
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(compressed, expected_size + 1)
    except zlib.error:
        return False
    if (
        len(raw) != expected_size
        or not decompressor.eof
        or decompressor.unconsumed_tail
        or decompressor.unused_data
    ):
        return False
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    passes = (
        ((0, 0, 1, 1),)
        if interlace == 0
        else (
            (0, 0, 8, 8),
            (4, 0, 8, 8),
            (0, 4, 4, 8),
            (2, 0, 4, 4),
            (0, 2, 2, 4),
            (1, 0, 2, 2),
            (0, 1, 1, 2),
        )
    )
    position = 0
    for start_x, start_y, step_x, step_y in passes:
        pass_width = _pass_extent(width, start_x, step_x)
        pass_height = _pass_extent(height, start_y, step_y)
        if pass_width == 0 or pass_height == 0:
            continue
        row_bytes = (pass_width * channels * bit_depth + 7) // 8
        for _row in range(pass_height):
            if position + 1 + row_bytes > len(raw) or raw[position] > 4:
                return False
            position += 1 + row_bytes
    return position == len(raw)


def _png_expected_scanline_bytes(
    width: int,
    height: int,
    bit_depth: int,
    color_type: int,
    interlace: int,
) -> int:
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    passes = (
        ((0, 0, 1, 1),)
        if interlace == 0
        else (
            (0, 0, 8, 8),
            (4, 0, 8, 8),
            (0, 4, 4, 8),
            (2, 0, 4, 4),
            (0, 2, 2, 4),
            (1, 0, 2, 2),
            (0, 1, 1, 2),
        )
    )
    total = 0
    for start_x, start_y, step_x, step_y in passes:
        pass_width = _pass_extent(width, start_x, step_x)
        pass_height = _pass_extent(height, start_y, step_y)
        if pass_width and pass_height:
            total += pass_height * (1 + (pass_width * channels * bit_depth + 7) // 8)
    return total


def _pass_extent(total: int, start: int, step: int) -> int:
    if total <= start:
        return 0
    return (total - start + step - 1) // step


def _valid_jpeg(content: bytes) -> bool:
    if len(content) < 8 or not content.startswith(b"\xff\xd8") or not content.endswith(b"\xff\xd9"):
        return False
    position = 2
    width = 0
    height = 0
    components: Dict[int, Tuple[int, int, int]] = {}
    quantization_tables: set[int] = set()
    huffman_tables: Dict[Tuple[int, int], Dict[Tuple[int, int], int]] = {}
    while position < len(content) - 2:
        if content[position] != 0xFF or position + 1 >= len(content):
            return False
        marker = content[position + 1]
        position += 2
        if marker == 0xD9:
            return False
        if marker in range(0xD0, 0xD8) or marker == 0x01:
            continue
        if position + 2 > len(content):
            return False
        length = struct.unpack(">H", content[position : position + 2])[0]
        if length < 2 or position + length > len(content):
            return False
        segment = content[position + 2 : position + length]
        if marker == 0xDB:
            tables = _jpeg_quantization_table_ids(segment)
            if tables is None:
                return False
            quantization_tables.update(tables)
        elif marker == 0xC0:
            frame = _jpeg_baseline_frame(segment)
            if frame is None:
                return False
            width, height, components = frame
        elif marker in {0xC1, 0xC2}:
            return False
        elif marker == 0xC4:
            tables = _jpeg_huffman_tables(segment)
            if tables is None:
                return False
            huffman_tables.update(tables)
        elif marker == 0xDA:
            scan = _jpeg_baseline_scan(segment, components, huffman_tables)
            if (
                scan is None
                or not components
                or any(component[2] not in quantization_tables for component in components.values())
            ):
                return False
            entropy = content[position + length : -2]
            return _decode_jpeg_baseline_entropy(
                entropy,
                width,
                height,
                components,
                scan,
                huffman_tables,
            )
        position += length
    return False


def _jpeg_quantization_table_ids(segment: bytes) -> Optional[set[int]]:
    position = 0
    result: set[int] = set()
    while position < len(segment):
        header = segment[position]
        position += 1
        precision = header >> 4
        table_id = header & 0x0F
        table_bytes = 64 * (2 if precision else 1)
        if precision not in {0, 1} or table_id > 3 or position + table_bytes > len(segment):
            return None
        table_data = segment[position : position + table_bytes]
        if not table_data or any(value == 0 for value in table_data):
            return None
        position += table_bytes
        result.add(table_id)
    return result if position == len(segment) else None


def _jpeg_baseline_frame(
    segment: bytes,
) -> Optional[Tuple[int, int, Dict[int, Tuple[int, int, int]]]]:
    if len(segment) < 6 or segment[0] != 8:
        return None
    height = struct.unpack(">H", segment[1:3])[0]
    width = struct.unpack(">H", segment[3:5])[0]
    count = segment[5]
    if width == 0 or height == 0 or count == 0 or len(segment) != 6 + 3 * count:
        return None
    components: Dict[int, Tuple[int, int, int]] = {}
    for index in range(count):
        component_id, sampling, table_id = segment[6 + 3 * index : 9 + 3 * index]
        horizontal = sampling >> 4
        vertical = sampling & 0x0F
        if component_id in components or not (1 <= horizontal <= 4 and 1 <= vertical <= 4) or table_id > 3:
            return None
        components[component_id] = (horizontal, vertical, table_id)
    return width, height, components


def _jpeg_huffman_tables(
    segment: bytes,
) -> Optional[Dict[Tuple[int, int], Dict[Tuple[int, int], int]]]:
    position = 0
    result: Dict[Tuple[int, int], Dict[Tuple[int, int], int]] = {}
    while position < len(segment):
        table = segment[position]
        position += 1
        table_class = table >> 4
        table_id = table & 0x0F
        if table_class not in {0, 1} or table_id > 3 or position + 16 > len(segment):
            return None
        counts = segment[position : position + 16]
        position += 16
        symbol_count = sum(counts)
        if symbol_count == 0 or symbol_count > 256 or position + symbol_count > len(segment):
            return None
        symbols = segment[position : position + symbol_count]
        position += symbol_count
        codes: Dict[Tuple[int, int], int] = {}
        code = 0
        symbol_index = 0
        for bit_length, count in enumerate(counts, start=1):
            if code + count > (1 << bit_length):
                return None
            for _entry in range(count):
                symbol = symbols[symbol_index]
                symbol_index += 1
                if table_class == 0 and symbol > 11:
                    return None
                codes[(bit_length, code)] = symbol
                code += 1
            code <<= 1
        result[(table_class, table_id)] = codes
    return result if position == len(segment) else None


def _jpeg_baseline_scan(
    segment: bytes,
    components: Dict[int, Tuple[int, int, int]],
    huffman_tables: Dict[Tuple[int, int], Dict[Tuple[int, int], int]],
) -> Optional[Tuple[Tuple[int, int, int], ...]]:
    if len(segment) < 6:
        return None
    count = segment[0]
    if count == 0 or len(segment) != 1 + 2 * count + 3:
        return None
    if segment[-3:] != b"\x00\x3f\x00":
        return None
    scan: List[Tuple[int, int, int]] = []
    seen_components: set[int] = set()
    for index in range(count):
        component_id = segment[1 + 2 * index]
        tables = segment[2 + 2 * index]
        dc_table = tables >> 4
        ac_table = tables & 0x0F
        if (
            component_id not in components
            or (0, dc_table) not in huffman_tables
            or (1, ac_table) not in huffman_tables
            or component_id in seen_components
        ):
            return None
        seen_components.add(component_id)
        scan.append((component_id, dc_table, ac_table))
    return tuple(scan) if seen_components == set(components) else None


def _decode_jpeg_baseline_entropy(
    entropy: bytes,
    width: int,
    height: int,
    components: Dict[int, Tuple[int, int, int]],
    scan: Tuple[Tuple[int, int, int], ...],
    huffman_tables: Dict[Tuple[int, int], Dict[Tuple[int, int], int]],
) -> bool:
    unstuffed = bytearray()
    position = 0
    while position < len(entropy):
        value = entropy[position]
        position += 1
        if value != 0xFF:
            unstuffed.append(value)
            continue
        if position >= len(entropy) or entropy[position] != 0x00:
            return False
        unstuffed.append(0xFF)
        position += 1
    max_horizontal = max(value[0] for value in components.values())
    max_vertical = max(value[1] for value in components.values())
    mcu_columns = (width + 8 * max_horizontal - 1) // (8 * max_horizontal)
    mcu_rows = (height + 8 * max_vertical - 1) // (8 * max_vertical)
    reader = _JpegBitReader(bytes(unstuffed))
    for _mcu in range(mcu_columns * mcu_rows):
        for component_id, dc_table, ac_table in scan:
            horizontal, vertical, _quantization = components[component_id]
            for _block in range(horizontal * vertical):
                if not _decode_jpeg_block(
                    reader,
                    huffman_tables[(0, dc_table)],
                    huffman_tables[(1, ac_table)],
                ):
                    return False
    return reader.remaining_padding_is_ones()


@dataclass
class _JpegBitReader:
    data: bytes
    position: int = 0

    def bit(self) -> Optional[int]:
        if self.position >= len(self.data) * 8:
            return None
        byte = self.data[self.position // 8]
        value = (byte >> (7 - self.position % 8)) & 1
        self.position += 1
        return value

    def skip(self, count: int) -> bool:
        if count < 0 or self.position + count > len(self.data) * 8:
            return False
        self.position += count
        return True

    def symbol(self, table: Dict[Tuple[int, int], int]) -> Optional[int]:
        code = 0
        for length in range(1, 17):
            bit = self.bit()
            if bit is None:
                return None
            code = (code << 1) | bit
            if (length, code) in table:
                return table[(length, code)]
        return None

    def remaining_padding_is_ones(self) -> bool:
        while self.position < len(self.data) * 8:
            if self.bit() != 1:
                return False
        return True


def _decode_jpeg_block(
    reader: _JpegBitReader,
    dc_table: Dict[Tuple[int, int], int],
    ac_table: Dict[Tuple[int, int], int],
) -> bool:
    dc_size = reader.symbol(dc_table)
    if dc_size is None or dc_size > 11 or not reader.skip(dc_size):
        return False
    coefficient = 1
    while coefficient < 64:
        symbol = reader.symbol(ac_table)
        if symbol is None:
            return False
        if symbol == 0:
            return True
        if symbol == 0xF0:
            if coefficient + 16 > 64:
                return False
            coefficient += 16
            continue
        run = symbol >> 4
        size = symbol & 0x0F
        if size == 0 or size > 10:
            return False
        coefficient += run
        if coefficient >= 64 or not reader.skip(size):
            return False
        coefficient += 1
    return True


def _valid_gif(content: bytes) -> bool:
    if len(content) < 14 or content[:6] not in {b"GIF87a", b"GIF89a"}:
        return False
    width, height, packed = struct.unpack("<HHB", content[6:11])
    if width == 0 or height == 0 or width * height > _MAX_BITMAP_PIXELS:
        return False
    position = 13
    if packed & 0x80:
        position += 3 * (2 ** ((packed & 0x07) + 1))
    seen_image = False
    while position < len(content):
        introducer = content[position]
        position += 1
        if introducer == 0x3B:
            return seen_image and position == len(content)
        if introducer == 0x2C:
            if position + 9 > len(content):
                return False
            left, top, image_width, image_height = struct.unpack(
                "<HHHH",
                content[position : position + 8],
            )
            if (
                image_width == 0
                or image_height == 0
                or image_width * image_height > _MAX_BITMAP_PIXELS
                or left + image_width > width
                or top + image_height > height
            ):
                return False
            image_packed = content[position + 8]
            position += 9
            if image_packed & 0x80:
                position += 3 * (2 ** ((image_packed & 0x07) + 1))
            if position >= len(content):
                return False
            minimum_code_size = content[position]
            if minimum_code_size < 2 or minimum_code_size > 8:
                return False
            position += 1
            seen_image = True
        elif introducer == 0x21:
            if position >= len(content):
                return False
            position += 1
        else:
            return False
        compressed = bytearray()
        while position < len(content):
            block_length = content[position]
            position += 1
            if block_length == 0:
                break
            if introducer == 0x2C:
                compressed.extend(content[position : position + block_length])
            position += block_length
            if position > len(content):
                return False
        else:
            return False
        if introducer == 0x2C and not _gif_lzw_has_pixels(
            bytes(compressed),
            minimum_code_size,
            image_width * image_height,
        ):
            return False
    return False


def _gif_lzw_has_pixels(
    data: bytes,
    minimum_code_size: int,
    required_pixels: int,
) -> bool:
    clear_code = 1 << minimum_code_size
    end_code = clear_code + 1
    code_size = minimum_code_size + 1
    next_code = end_code + 1
    bit_position = 0
    dictionary = {index: bytes((index,)) for index in range(clear_code)}
    previous: Optional[bytes] = None
    produced = 0
    while bit_position + code_size <= len(data) * 8:
        code = 0
        for offset in range(code_size):
            byte_index = (bit_position + offset) // 8
            bit_index = (bit_position + offset) % 8
            code |= ((data[byte_index] >> bit_index) & 1) << offset
        bit_position += code_size
        if code == clear_code:
            dictionary = {index: bytes((index,)) for index in range(clear_code)}
            code_size = minimum_code_size + 1
            next_code = end_code + 1
            previous = None
            continue
        if code == end_code:
            return produced == required_pixels
        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code and previous is not None:
            prior = bytes(previous)
            entry = prior + prior[:1]
        else:
            return False
        produced += len(entry)
        if produced > required_pixels:
            return False
        if previous is not None and next_code < 4096:
            dictionary[next_code] = previous + entry[:1]
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        previous = entry
    return False


def _valid_webp(content: bytes) -> bool:
    if len(content) < 20 or content[:4] != b"RIFF" or content[8:12] != b"WEBP":
        return False
    if struct.unpack("<I", content[4:8])[0] != len(content) - 8:
        return False
    position = 12
    seen_image = False
    seen_vp8l = False
    while position + 8 <= len(content):
        chunk_type = content[position : position + 4]
        chunk_length = struct.unpack("<I", content[position + 4 : position + 8])[0]
        position += 8
        end = position + chunk_length
        if end > len(content):
            return False
        payload = content[position:end]
        if chunk_type == b"VP8L":
            if seen_vp8l:
                return False
            seen_vp8l = True
            seen_image = _valid_vp8l_literal_payload(payload)
        else:
            return False
        position = end + (chunk_length % 2)
    return seen_image and position == len(content)


@dataclass
class _LsbBitReader:
    data: bytes
    position: int = 0

    def bits(self, count: int) -> Optional[int]:
        if count < 0 or self.position + count > len(self.data) * 8:
            return None
        result = 0
        for offset in range(count):
            byte = self.data[(self.position + offset) // 8]
            result |= ((byte >> ((self.position + offset) % 8)) & 1) << offset
        self.position += count
        return result

    def padding_is_zero(self) -> bool:
        while self.position < len(self.data) * 8:
            if self.bits(1) != 0:
                return False
        return True


@dataclass(frozen=True)
class _SimpleHuffman:
    first: int
    second: Optional[int] = None

    def symbol(self, reader: _LsbBitReader) -> Optional[int]:
        if self.second is None:
            return self.first
        bit = reader.bits(1)
        if bit is None:
            return None
        return self.second if bit else self.first


def _valid_vp8l_literal_payload(payload: bytes) -> bool:
    if len(payload) <= 5 or payload[0] != 0x2F:
        return False
    dimensions = int.from_bytes(payload[1:5], "little")
    width = (dimensions & 0x3FFF) + 1
    height = ((dimensions >> 14) & 0x3FFF) + 1
    version = (dimensions >> 29) & 0x07
    if width * height > _MAX_BITMAP_PIXELS or version != 0:
        return False
    reader = _LsbBitReader(payload[5:])
    if reader.bits(1) != 0:  # no transforms in the supported literal subset
        return False
    if reader.bits(1) != 0:  # no color cache
        return False
    if reader.bits(1) != 0:  # one global Huffman group
        return False
    alphabets = (280, 256, 256, 256, 40)
    trees: List[_SimpleHuffman] = []
    for alphabet_size in alphabets:
        tree = _read_simple_vp8l_huffman(reader, alphabet_size)
        if tree is None:
            return False
        trees.append(tree)
    if len(trees) != 5:
        return False
    green = trees[0]
    red = trees[1]
    blue = trees[2]
    alpha = trees[3]
    for _pixel in range(width * height):
        green_symbol = green.symbol(reader)
        red_symbol = red.symbol(reader)
        blue_symbol = blue.symbol(reader)
        alpha_symbol = alpha.symbol(reader)
        if (
            green_symbol is None
            or green_symbol >= 256
            or red_symbol is None
            or red_symbol >= 256
            or blue_symbol is None
            or blue_symbol >= 256
            or alpha_symbol is None
            or alpha_symbol >= 256
        ):
            return False
    return reader.padding_is_zero()


def _read_simple_vp8l_huffman(
    reader: _LsbBitReader,
    alphabet_size: int,
) -> Optional[_SimpleHuffman]:
    if reader.bits(1) != 1:
        return None
    second_present = reader.bits(1)
    first_is_eight_bits = reader.bits(1)
    if second_present is None or first_is_eight_bits is None:
        return None
    first = reader.bits(8 if first_is_eight_bits else 1)
    if first is None or first >= alphabet_size:
        return None
    if second_present == 0:
        return _SimpleHuffman(first)
    second = reader.bits(8)
    if second is None or second >= alphabet_size or second == first:
        return None
    return _SimpleHuffman(first, second)
