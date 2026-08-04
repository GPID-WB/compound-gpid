"""Shared resource-boundary tests used by generic publication."""
from __future__ import annotations

# pylint: disable=import-error,unexpected-keyword-arg

import base64
import os
from pathlib import Path
import struct
import zlib

import pytest

from secure_fs import (  # pylint: disable=import-error
    SecureMutationError,
    secure_read_bytes,
)
from artifact_views.errors import ArtifactSecurityError
from artifact_views.security import (
    GenericRenderContext,
    embed_local_bitmap,
    render_generic_inline,
    validate_html_security,
)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


PNG = (
    b"\x89PNG\r\n\x1a\n"
    + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
    + _png_chunk(b"IEND", b"")
)
JPEG = (
    b"\xff\xd8"
    b"\xff\xdb\x00C\x00" + bytes([1] * 64)
    + b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
    + b"\xff\xc4\x00\x26"
    + b"\x00\x01" + bytes(15) + b"\x00"
    + b"\x10\x01" + bytes(15) + b"\x00"
    + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"
    + b"\x3f\xff\xd9"
)
GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
    b"\x00\x00\x00\xff\xff\xff"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00"
    b"\x02\x02D\x01\x00;"
)
def _lsb_bytes(bits: list[tuple[int, int]]) -> bytes:
    output = bytearray()
    current = 0
    used = 0
    for value, count in bits:
        for offset in range(count):
            current |= ((value >> offset) & 1) << used
            used += 1
            if used == 8:
                output.append(current)
                current = 0
                used = 0
    if used:
        output.append(current)
    return bytes(output)


def _simple_tree(symbol: int) -> list[tuple[int, int]]:
    return [(1, 1), (0, 1), (1, 1), (symbol, 8)]


_WEBP_BITS = [(0, 1), (0, 1), (0, 1)]
for _symbol in (0, 0, 0, 255, 0):
    _WEBP_BITS.extend(_simple_tree(_symbol))
_WEBP_PAYLOAD = b"/\x00\x00\x00\x00" + _lsb_bytes(_WEBP_BITS)
WEBP = (
    b"RIFF"
    + struct.pack("<I", 4 + 8 + len(_WEBP_PAYLOAD) + (len(_WEBP_PAYLOAD) % 2))
    + b"WEBPVP8L"
    + struct.pack("<I", len(_WEBP_PAYLOAD))
    + _WEBP_PAYLOAD
    + (b"\x00" if len(_WEBP_PAYLOAD) % 2 else b"")
)


def test_resource_read_rejects_oversize_before_returning_bytes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "image.png").write_bytes(b"12345")

    with pytest.raises(SecureMutationError, match="exceeds.*4"):
        secure_read_bytes(
            root,
            "image.png",
            max_bytes=4,
            reject_hardlinks=True,
        )


def test_resource_read_rejects_hard_link_alias(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    original = root / "image.png"
    original.write_bytes(b"png")
    alias = root / "alias.png"
    os.link(original, alias)

    with pytest.raises(SecureMutationError, match="multiple hard links"):
        secure_read_bytes(
            root,
            "alias.png",
            max_bytes=10,
            reject_hardlinks=True,
        )


@pytest.mark.parametrize(
    ("filename", "content", "mime"),
    (
        ("figure.png", PNG, "image/png"),
        ("figure.jpg", JPEG, "image/jpeg"),
        ("figure.jpeg", JPEG, "image/jpeg"),
        ("figure.gif", GIF, "image/gif"),
        ("figure.webp", WEBP, "image/webp"),
    ),
)
def test_local_bitmap_embedding_is_source_relative_and_deterministic(
    tmp_path: Path,
    filename: str,
    content: bytes,
    mime: str,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs/assets" / filename
    image.parent.mkdir(parents=True)
    image.write_bytes(content)

    embedded = embed_local_bitmap(
        root,
        Path("docs/guide.md"),
        f"assets/{filename}",
        "  A useful\n figure  ",
        max_bytes=len(content) + 1,
    )

    assert embedded.alt_text == "A useful figure"
    assert embedded.source_relative.as_posix() == f"docs/assets/{filename}"
    assert embedded.data_uri == (
        f"data:{mime};base64,{base64.b64encode(content).decode('ascii')}"
    )


@pytest.mark.parametrize(
    "uri",
    (
        "https://example.org/a.png",
        "//example.org/a.png",
        "/absolute.png",
        "../escape.png",
        "assets\\a.png",
        "assets/a%2fpng.png",
        "assets/a%5cpng.png",
        "assets/a%252fpng.png",
        "assets/carrier:payload.png",
        "assets/CON.png",
        "assets/trailing./a.png",
        "assets/a.png?query=1",
        "assets/a.png#fragment",
        "data:image/png;base64,AAAA",
        "assets/control\x00.png",
    ),
)
def test_bitmap_uri_rejects_remote_ambiguous_or_escaping_identity(
    tmp_path: Path,
    uri: str,
) -> None:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)

    with pytest.raises(ArtifactSecurityError):
        embed_local_bitmap(root, Path("docs/guide.md"), uri, "Alt", max_bytes=128)


@pytest.mark.parametrize("alt", ("", "   ", "\n\t"))
def test_bitmap_alt_text_must_be_nonempty_after_normalization(
    tmp_path: Path,
    alt: str,
) -> None:
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)

    with pytest.raises(ArtifactSecurityError, match="alt text"):
        embed_local_bitmap(root, Path("docs/guide.md"), "a.png", alt, max_bytes=128)


@pytest.mark.parametrize(
    ("filename", "content"),
    (
        ("fake.png", b"<svg><script/></svg>"),
        ("wrong.jpg", PNG),
        ("vector.svg", b"<svg></svg>"),
    ),
)
def test_bitmap_suffix_and_magic_must_match(
    tmp_path: Path,
    filename: str,
    content: bytes,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs" / filename
    image.parent.mkdir(parents=True)
    image.write_bytes(content)

    with pytest.raises(ArtifactSecurityError, match="format|signature|suffix"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            filename,
            "Alt",
            max_bytes=128,
        )


@pytest.mark.parametrize(
    ("filename", "content"),
    (
        ("truncated.png", PNG[:-12]),
        ("truncated.jpg", JPEG[:-2]),
        ("truncated.gif", GIF[:-1]),
        ("bad-length.webp", WEBP[:-2]),
        ("polyglot.png", PNG + b"<script>"),
    ),
)
def test_bitmap_container_must_be_complete(
    tmp_path: Path,
    filename: str,
    content: bytes,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs" / filename
    image.parent.mkdir(parents=True)
    image.write_bytes(content)

    with pytest.raises(ArtifactSecurityError, match="container|structure|signature"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            filename,
            "Alt",
            max_bytes=len(content) + 1,
        )


def test_png_rejects_invalid_compressed_scanlines(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    image = root / "docs/bad.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + _png_chunk(b"IDAT", b"not-zlib")
        + _png_chunk(b"IEND", b"")
    )

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "bad.png",
            "Bad",
            max_bytes=1024,
        )


def test_webp_rejects_invalid_lossless_dimensions(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    image = root / "docs/bad.webp"
    image.parent.mkdir(parents=True)
    invalid_payload = b"/\xff\xff\xff\xff"
    image.write_bytes(
        b"RIFF"
        + struct.pack("<I", 4 + 8 + len(invalid_payload) + 1)
        + b"WEBPVP8L"
        + struct.pack("<I", len(invalid_payload))
        + invalid_payload
        + b"\x00"
    )

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "bad.webp",
            "Bad",
            max_bytes=1024,
        )


def test_png_rejects_dimensions_over_preinflate_budget(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    image = root / "docs/huge.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", 0xFFFFFFFF, 0xFFFFFFFF, 8, 6, 0, 0, 0),
        )
        + _png_chunk(b"IDAT", zlib.compress(b"\x00"))
        + _png_chunk(b"IEND", b"")
    )

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "huge.png",
            "Huge",
            max_bytes=1024,
        )


def test_png_rejects_decoded_bytes_over_fixed_budget(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    image = root / "docs/large-row.png"
    image.parent.mkdir(parents=True)
    width = 16_000_000
    image.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, 1, 16, 6, 0, 0, 0),
        )
        + _png_chunk(b"IDAT", zlib.compress(b"\x00"))
        + _png_chunk(b"IEND", b"")
    )

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "large-row.png",
            "Large",
            max_bytes=2048,
        )


def test_jpeg_rejects_zero_quantization_coefficient(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    image = root / "docs/bad.jpg"
    image.parent.mkdir(parents=True)
    malformed = bytearray(JPEG)
    dqt = malformed.index(b"\xff\xdb")
    malformed[dqt + 5] = 0
    image.write_bytes(bytes(malformed))

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "bad.jpg",
            "Bad",
            max_bytes=2048,
        )


def test_jpeg_rejects_oversubscribed_huffman_table() -> None:
    import artifact_views.security as security

    segment = b"\x00" + bytes((3,)) + bytes(15) + b"\x00\x01\x02"

    assert security._jpeg_huffman_tables(  # pylint: disable=protected-access
        segment
    ) is None


def test_jpeg_rejects_scan_without_exact_frame_components(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    image = root / "docs/bad.jpg"
    image.parent.mkdir(parents=True)
    malformed = bytearray(JPEG)
    sos = malformed.index(b"\xff\xda")
    malformed[sos + 5] = 2
    image.write_bytes(bytes(malformed))

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "bad.jpg",
            "Bad",
            max_bytes=2048,
        )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda data: data.__setitem__(data.index(b"\xff\xc0") + 1, 0xC2),
        lambda data: data.__setitem__(-3, 0x00),
        lambda data: data.__setitem__(-3, 0x7E),
    ),
)
def test_jpeg_rejects_progressive_entropy_and_padding_corruption(
    tmp_path: Path,
    mutate,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs/bad.jpg"
    image.parent.mkdir(parents=True)
    malformed = bytearray(JPEG)
    mutate(malformed)
    image.write_bytes(bytes(malformed))

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "bad.jpg",
            "Bad",
            max_bytes=2048,
        )


@pytest.mark.parametrize(
    ("compressed", "declared_width"),
    ((b"D\x01", 2), (b"\x04\x0a", 1)),
)
def test_gif_rejects_lzw_under_or_overproduction(
    tmp_path: Path,
    compressed: bytes,
    declared_width: int,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs/bad.gif"
    image.parent.mkdir(parents=True)
    malformed = bytearray(GIF)
    malformed[6:8] = struct.pack("<H", declared_width)
    descriptor = malformed.index(b",")
    malformed[descriptor + 5 : descriptor + 7] = struct.pack("<H", declared_width)
    data_start = malformed.index(b"\x02\x02D\x01\x00")
    malformed[data_start : data_start + 5] = b"\x02\x02" + compressed + b"\x00"
    image.write_bytes(bytes(malformed))

    with pytest.raises(ArtifactSecurityError, match="container structure"):
        embed_local_bitmap(
            root,
            Path("docs/guide.md"),
            "bad.gif",
            "Bad",
            max_bytes=1024,
        )


def test_webp_rejects_unknown_and_repeated_image_chunks(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    chunk = WEBP[12:]
    invalid_payload = b"/\xff\xff\xff\xff"
    invalid_chunk = (
        b"VP8L"
        + struct.pack("<I", len(invalid_payload))
        + invalid_payload
        + b"\x00"
    )
    for name, chunks in (
        ("unknown.webp", chunk + b"JUNK\x00\x00\x00\x00"),
        ("repeated.webp", chunk + chunk),
        ("invalid-then-valid.webp", invalid_chunk + chunk),
    ):
        content = b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WEBP" + chunks
        image = root / name
        image.write_bytes(content)
        with pytest.raises(ArtifactSecurityError, match="container structure"):
            embed_local_bitmap(
                root,
                Path("guide.md"),
                name,
                "Bad",
                max_bytes=2048,
            )


def test_render_context_caches_resource_but_budgets_each_emission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    image = root / "docs/figure.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(PNG)
    import artifact_views.security as security

    calls = 0
    original_read = security.secure_read_bytes

    def counted_read(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original_read(*args, **kwargs)

    monkeypatch.setattr(security, "secure_read_bytes", counted_read)
    context = GenericRenderContext(
        project_root=root,
        source_relative=Path("docs/guide.md"),
        output_relative=Path(".cg-docs/views/documents/docs/guide.html"),
        max_image_bytes=len(PNG) + 1,
        max_total_image_bytes=len(PNG) + 1,
        max_image_count=2,
        max_output_bytes=10_000,
    )

    rendered = render_generic_inline(
        "![One](figure.png) ![Two](figure.png)",
        context=context,
    )

    assert rendered.count("data:image/png;base64,") == 2
    assert calls == 1
    with pytest.raises(ArtifactSecurityError, match="image count|output budget"):
        render_generic_inline("![Three](figure.png)", context=context)


def test_inline_renderer_has_no_dense_tables_or_prefix_rescans() -> None:
    import inspect
    import artifact_views.security as security

    implementation = inspect.getsource(security)

    assert "_next_delimiter_positions" not in implementation
    assert "_inside_inline_code" not in implementation


def test_final_html_accepts_only_bitmap_data_image_with_alt() -> None:
    encoded = base64.b64encode(PNG).decode("ascii")
    validate_html_security(
        f'<main><img src="data:image/png;base64,{encoded}" alt="Figure"></main>'
    )

    for html in (
        '<img src="https://example.org/a.png" alt="Figure">',
        '<img src="data:image/svg+xml;base64,AAAA" alt="Figure">',
        '<img src="data:image/png;base64,AAAA" alt="">',
        '<img src="data:image/png;base64,AAAA">',
    ):
        with pytest.raises(ArtifactSecurityError):
            validate_html_security(html)