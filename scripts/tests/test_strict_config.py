"""Tests for the strict project-configuration grammar (Step 4, R3/R4).

Run from repo root:
    python -m pytest scripts/tests/test_strict_config.py -q
"""
from __future__ import annotations

import pytest

from parsing_utils import parse_strict_config

VALID_CONFIG = """---
language: "both"
project-type: "tool"
review-depth: "thorough"
r-syntax: "data.table-collapse"
suites: [cg, cr]
capabilities: [python]
created: "2026-03-04"
cg-schema-version: "2026-04-07-r-syntax-dialect"
---
# Body
"""


def _config(lines: list[str]) -> str:
    return "---\n" + "\n".join(lines) + "\n---\n# Body\n"


class TestValidGrammar:
    def test_valid_config_parses(self) -> None:
        parsed = parse_strict_config(VALID_CONFIG)
        assert parsed.valid, parsed.errors
        assert parsed.suites == ["cg", "cr"]
        assert parsed.capabilities == ["python"]
        assert parsed.settings["language"] == "both"
        assert parsed.settings["review-depth"] == "thorough"

    def test_absent_suites_is_not_an_error(self) -> None:
        lines = ['language: "r"', 'project-type: "tool"', 'created: "2026-01-01"']
        parsed = parse_strict_config(_config(lines))
        assert parsed.valid, parsed.errors
        assert parsed.suites == []

    def test_bare_simple_scalars_accepted(self) -> None:
        lines = ["language: both", "project-type: tool"]
        parsed = parse_strict_config(_config(lines))
        assert parsed.valid, parsed.errors
        assert parsed.settings["language"] == "both"

    def test_trailing_inline_comment_accepted(self) -> None:
        lines = ['language: "both"  # both languages', "suites: [cg, cr]  # mixed"]
        parsed = parse_strict_config(_config(lines))
        assert parsed.valid, parsed.errors
        assert parsed.suites == ["cg", "cr"]


class TestInvalidGrammar:
    @pytest.mark.parametrize("bad_line", [
        "language: [x]",            # list where scalar required
        "language: {a: b}",         # nested mapping
        "language: |",              # block scalar
        "language: &anchor x",      # anchor
        "language: *alias",         # alias
        "language: !tag x",         # tag
        "language: a: b",           # nested value separator
    ])
    def test_scalar_invalid_forms_fail(self, bad_line: str) -> None:
        parsed = parse_strict_config(_config([bad_line]))
        assert not parsed.valid
        assert parsed.errors

    def test_unterminated_quote_fails(self) -> None:
        parsed = parse_strict_config(_config(['language: "both']))
        assert not parsed.valid
        assert any("unterminated" in error for error in parsed.errors)

    def test_missing_frontmatter_fails(self) -> None:
        parsed = parse_strict_config("# no frontmatter\n")
        assert not parsed.valid
        assert any("frontmatter" in error for error in parsed.errors)

    def test_unclosed_frontmatter_fails(self) -> None:
        parsed = parse_strict_config("---\nlanguage: 'both'\n")
        assert not parsed.valid

    def test_utf8_bom_fails(self) -> None:
        parsed = parse_strict_config("\ufeff" + VALID_CONFIG)
        assert not parsed.valid
        assert any("BOM" in error for error in parsed.errors)

    def test_tabs_fail_with_line(self) -> None:
        text = "---\nlanguage:\t'both'\n---\n"
        parsed = parse_strict_config(text)
        assert not parsed.valid
        assert any("tab" in error and "line 2" in error for error in parsed.errors)

    def test_non_ascii_key_fails(self) -> None:
        parsed = parse_strict_config(_config(["languagé: 'both'"]))
        assert not parsed.valid
        assert any("not an ASCII identifier" in error for error in parsed.errors)

    def test_duplicate_key_fails_with_line_and_field(self) -> None:
        lines = ["language: 'both'", "language: 'r'"]
        parsed = parse_strict_config(_config(lines))
        assert not parsed.valid
        assert any("duplicate key 'language'" in error and "line 3" in error for error in parsed.errors)

    def test_unrecognized_key_fails_with_remediation(self) -> None:
        parsed = parse_strict_config(_config(["mystery: 'x'"]))
        assert not parsed.valid
        assert any("unrecognized config key 'mystery'" in error for error in parsed.errors)

    def test_block_sequence_fails(self) -> None:
        text = "---\nsuites:\n  - cg\n  - cr\n---\n"
        parsed = parse_strict_config(text)
        assert not parsed.valid
        assert any("indented/nested" in error or "block" in error for error in parsed.errors)

    def test_empty_suites_fails(self) -> None:
        parsed = parse_strict_config(_config(["suites:"]))
        assert not parsed.valid
        assert any("suites must not be empty" in error for error in parsed.errors)

    def test_scalar_suites_fails(self) -> None:
        parsed = parse_strict_config(_config(['suites: "cg"']))
        assert not parsed.valid
        assert any("inline list" in error for error in parsed.errors)

    def test_duplicate_suite_values_fail(self) -> None:
        parsed = parse_strict_config(_config(["suites: [cg, cr, cg]"]))
        assert not parsed.valid
        assert any("duplicate value 'cg'" in error for error in parsed.errors)

    def test_non_ascii_suite_value_fails(self) -> None:
        parsed = parse_strict_config(_config(["suites: [cg, rés]"]))
        assert not parsed.valid

    def test_duplicate_capabilities_fail(self) -> None:
        parsed = parse_strict_config(_config(["capabilities: [python, python]"]))
        assert not parsed.valid
        assert any("duplicate value 'python'" in error for error in parsed.errors)

    def test_uppercase_suite_value_fails(self) -> None:
        parsed = parse_strict_config(_config(["suites: [CG]"]))
        assert not parsed.valid
        assert any("lowercase ASCII identifier" in error for error in parsed.errors)

    def test_embedded_delimiter_in_value_does_not_truncate(self) -> None:
        parsed = parse_strict_config(_config(["project-type: foo---bar", "review-depth: standard"]))
        assert parsed.valid, parsed.errors
        assert parsed.settings.get("project-type") == "foo---bar"
        assert "review-depth" in parsed.settings


class TestErrorsCarryLineNumbers:
    def test_errors_report_exact_line(self) -> None:
        text = "---\nlanguage: 'both'\ncreated: '2026-01-01'\nbad key: 'x'\n---\n"
        parsed = parse_strict_config(text)
        assert not parsed.valid
        assert any(error.startswith("line 4") for error in parsed.errors)
