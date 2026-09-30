"""Cross-platform regression tests for skill YAML frontmatter parsing."""
from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests/fixtures/frontmatter"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import brain.utils as brain_utils
from brain.utils import parse_frontmatter
from parsing_utils import parse_frontmatter_with_body


ADAPTER_SKILL_ROOTS = (
    ".github/skills",
    ".agents/skills",
    ".kilo/skills",
    ".opencode/skills",
    ".claude/skills",
)
FRONTMATTER_RE = re.compile(
    r"^\ufeff?---[ \t]*(?:\r?\n)(.*?)^---[ \t]*\r?$(?:\r?\n)?",
    re.DOTALL | re.MULTILINE,
)


def _variants(text: str) -> dict[str, str]:
    """Return normalized LF, CRLF, and BOM+LF variants of ``text``."""
    lf = text.replace("\r\n", "\n")
    return {
        "lf": lf,
        "crlf": lf.replace("\n", "\r\n"),
        "bom-lf": "\ufeff" + lf,
    }


def _strict_frontmatter(text: str) -> dict:
    """Parse only the first frontmatter block with strict PyYAML."""
    match = FRONTMATTER_RE.match(text)
    assert match, "frontmatter delimiters were not found"
    parsed = yaml.safe_load(match.group(1))
    assert isinstance(parsed, dict)
    return parsed


def _all_shipped_skills() -> list[Path]:
    paths: list[Path] = []
    for relative in ADAPTER_SKILL_ROOTS:
        root = REPO_ROOT / relative
        if root.is_dir():
            paths.extend(sorted(root.rglob("SKILL.md")))
    return paths


def _all_shipped_agents() -> list[Path]:
    """Return canonical and generated markdown-backed agent definitions."""
    patterns = (
        ".github/agents/*.agent.md",
        ".kilo/agents/*.md",
        ".opencode/agents/*.md",
        ".claude/agents/*.md",
    )
    return [path for pattern in patterns for path in sorted(REPO_ROOT.glob(pattern))]


@pytest.mark.parametrize("skill_path", _all_shipped_skills(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
@pytest.mark.parametrize("variant", ("lf", "crlf", "bom-lf"))
def test_every_shipped_skill_parses_with_both_parsers(skill_path: Path, variant: str) -> None:
    """Every adapter view parses under LF, CRLF, and BOM+LF."""
    text = skill_path.read_text(encoding="utf-8-sig")
    candidate = _variants(text)[variant]
    hand = parse_frontmatter(candidate, source=skill_path)
    strict = _strict_frontmatter(candidate)
    for parsed in (hand, strict):
        assert isinstance(parsed.get("name"), str) and parsed["name"]
        assert isinstance(parsed.get("description"), str) and parsed["description"]


@pytest.mark.parametrize("agent_path", _all_shipped_agents(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_every_shipped_agent_is_strict_yaml_and_byte_clean(agent_path: Path) -> None:
    """Every shipped agent has LF, no BOM, ASCII frontmatter, and quoted description."""
    raw = agent_path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    text = raw.decode("utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match
    assert match.group(1).isascii()
    parsed = _strict_frontmatter(text)
    assert isinstance(parsed.get("description"), str) and parsed["description"]
    description_line = next(
        line for line in match.group(1).splitlines() if line.startswith("description:")
    )
    assert description_line.partition(":")[2].strip().startswith('"')


def test_multiline_quoted_scalars_continue_across_colons() -> None:
    """Colon-bearing continuation lines remain inside open quoted scalars."""
    text = (FIXTURES / "multiline-quoted.txt").read_text(encoding="utf-8")
    for candidate in _variants(text).values():
        parsed = parse_frontmatter(candidate)
        assert parsed["description"] == (
            "A folded double-quoted scalar whose continuation contains a colon: "
            "still part of the scalar."
        )
        assert parsed["single-note"] == (
            "A folded single-quoted scalar whose continuation also contains a colon: "
            "still part of the scalar."
        )


def test_body_dividers_do_not_extend_frontmatter() -> None:
    """The second delimiter closes frontmatter even when the body has dividers."""
    text = (FIXTURES / "body-dividers.txt").read_text(encoding="utf-8")
    parsed, body = parse_frontmatter_with_body(text)
    assert parsed["name"] == "body-dividers"
    assert body.startswith("# Body")
    assert body.count("\n---\n") == 2


@pytest.mark.parametrize(
    "fixture",
    ("whole-file-crlf.base64", "bom-crlf.base64"),
)
def test_encoded_line_ending_fixtures_parse(fixture: str) -> None:
    """Committed binary fixtures preserve CRLF and BOM+CRLF byte layouts."""
    raw = base64.b64decode((FIXTURES / fixture).read_text(encoding="ascii"))
    assert b"\r\n" in raw
    if fixture.startswith("bom"):
        assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    parsed = parse_frontmatter(text)
    strict = _strict_frontmatter(text)
    expected_name = "bom-crlf" if fixture.startswith("bom") else "whole-file-crlf"
    assert parsed["name"] == strict["name"] == expected_name
    assert parsed["description"] == strict["description"]
    parsed_with_body, body = parse_frontmatter_with_body(text)
    assert parsed_with_body == parsed
    assert body.startswith("# Body")


def test_optional_pyyaml_fallback_recovers_required_metadata() -> None:
    """Complex valid YAML falls back with a source-naming warning."""
    fixture = FIXTURES / "pyyaml-fallback.txt"
    with pytest.warns(UserWarning, match=re.escape(str(fixture))):
        parsed = parse_frontmatter(fixture.read_text(encoding="utf-8"), source=fixture)
    assert parsed == {"name": "fallback", "description": "Recovered by strict YAML."}


def test_normal_document_does_not_invoke_yaml_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plans without skill metadata stay on the lightweight parser path."""
    def fail_fallback(*_args: object, **_kwargs: object) -> dict:
        raise AssertionError("fallback should not run")

    monkeypatch.setattr(brain_utils, "_fallback_yaml", fail_fallback)
    parsed = parse_frontmatter("---\ntitle: Normal plan\nstatus: active\n---\n")
    assert parsed == {"title": "Normal plan", "status": "active"}


def test_double_quoted_yaml_escapes_are_decoded_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Canonical escaped quotes retain their semantic value for generation."""
    def fail_fallback(*_args: object, **_kwargs: object) -> dict:
        raise AssertionError("escape decoding must not require PyYAML")

    monkeypatch.setattr(brain_utils, "_fallback_yaml", fail_fallback)
    parsed = parse_frontmatter(
        '---\nname: escaped\ndescription: "A \\"quoted\\" value."\n---\n'
    )
    assert parsed["description"] == 'A "quoted" value.'

    yaml_only = parse_frontmatter(
        '---\nname: escaped\ndescription: "A \\x22quoted\\x22 value."\n---\n'
    )
    assert yaml_only["description"] == 'A "quoted" value.'


def test_empty_onedrive_placeholder_is_safe() -> None:
    """A zero-byte cloud placeholder returns an empty mapping without raising."""
    raw = (FIXTURES / "empty-placeholder.bin").read_bytes()
    assert raw == b""
    assert parse_frontmatter(raw.decode("utf-8")) == {}
    assert parse_frontmatter_with_body("") == ({}, "")


def test_broken_skill_link_is_detectable_without_parse_wrapper(tmp_path: Path) -> None:
    """A broken directory link is an I/O condition, not a parse failure."""
    target = tmp_path / "target"
    target.mkdir()
    skill = target / "SKILL.md"
    skill.write_text("---\nname: broken\ndescription: \"Broken.\"\n---\n", encoding="utf-8")
    link = tmp_path / "broken"
    _create_directory_link(link, target)
    skill.unlink()
    target.rmdir()
    assert not link.exists()
    with pytest.raises(FileNotFoundError):
        (link / "SKILL.md").read_text(encoding="utf-8")


def _create_directory_link(link: Path, target: Path) -> None:
    """Create a directory symlink on POSIX or a junction on Windows."""
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            pytest.skip(f"junction creation unavailable: {result.stderr or result.stdout}")
    else:
        link.symlink_to(target, target_is_directory=True)


def test_junction_or_symlink_matches_real_copy(tmp_path: Path) -> None:
    """Linked and copied fixture trees return identical frontmatter mappings."""
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy2(FIXTURES / "valid.txt", source / "SKILL.md")
    copied = tmp_path / "copied"
    shutil.copytree(source, copied)
    linked = tmp_path / "linked"
    _create_directory_link(linked, source)
    linked_parsed = parse_frontmatter((linked / "SKILL.md").read_text(encoding="utf-8"))
    copied_parsed = parse_frontmatter((copied / "SKILL.md").read_text(encoding="utf-8"))
    assert linked_parsed == copied_parsed
