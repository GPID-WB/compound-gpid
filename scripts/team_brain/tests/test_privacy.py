"""Tests for team_brain.privacy — 3-layer privacy filter.

Run from repo root:
    python -m pytest scripts/team_brain/tests/test_privacy.py -v
"""
from __future__ import annotations

import pytest

from team_brain.privacy import (
    FilterResult,
    Redaction,
    apply_frontmatter_filter,
    apply_llm_redactions,
    apply_regex_filter,
    build_llm_filter_prompt,
    run_privacy_filter,
)
from team_brain.schema import TeamBrainConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_config(**kwargs) -> TeamBrainConfig:
    return TeamBrainConfig(
        manager="wb384996",
        contributors=[{"org": "GPID-WB"}],
        **kwargs,
    )


# ---------------------------------------------------------------------------
# apply_regex_filter — Windows / UNC / Unix paths
# ---------------------------------------------------------------------------


def test_regex_windows_path_redacted():
    content = r"Path: E:\PovcalNet\data\file.dta"
    filtered, redactions = apply_regex_filter(content)
    assert "<REDACTED:path>" in filtered
    assert r"E:\PovcalNet" not in filtered
    assert any(r.redaction_type == "path" for r in redactions)


def test_regex_unix_home_path_redacted():
    content = "File at /home/wb384996/data/file.dta"
    filtered, _ = apply_regex_filter(content)
    assert "<REDACTED:path>" in filtered
    assert "/home/wb384996" not in filtered


def test_regex_unix_users_path_redacted():
    content = "Located in /Users/wb384996/.config/foo"
    filtered, _ = apply_regex_filter(content)
    assert "<REDACTED:path>" in filtered


def test_regex_unc_path_redacted():
    content = r"Share is at \\server\share\docs"
    filtered, _ = apply_regex_filter(content)
    assert "<REDACTED:path>" in filtered


def test_regex_relative_path_not_redacted():
    content = "See ./scripts/brain/utils.py for reference."
    filtered, redactions = apply_regex_filter(content)
    assert "./scripts/brain/utils.py" in filtered
    assert not redactions


def test_regex_email_redacted():
    content = "Contact wb384996@worldbank.org for help."
    filtered, _ = apply_regex_filter(content)
    assert "<REDACTED:email>" in filtered
    assert "worldbank.org" not in filtered


def test_regex_credential_redacted():
    content = "token: ghp_abcdefghijklmnop\npassword=hunter2"
    filtered, redactions = apply_regex_filter(content)
    assert "<REDACTED:credential>" in filtered
    cred_count = sum(1 for r in redactions if r.redaction_type == "credential")
    assert cred_count == 2


def test_regex_no_false_positive_code_snippet():
    content = "Use `data.table::setkey(dt, country_code)` to set the key."
    filtered, redactions = apply_regex_filter(content)
    assert "setkey" in filtered
    assert not redactions


def test_regex_internal_url_with_config():
    config = _minimal_config(internal_url_patterns=["*.worldbank.org"])
    content = "See https://internal.worldbank.org/docs/api"
    filtered, redactions = apply_regex_filter(content, config)
    assert "<REDACTED:url>" in filtered
    assert any(r.redaction_type == "url" for r in redactions)


def test_regex_no_redaction_for_public_url():
    config = _minimal_config(internal_url_patterns=["*.worldbank.org"])
    content = "See https://github.com/GPID-WB/compound-gpid for the source."
    filtered, redactions = apply_regex_filter(content, config)
    assert "github.com" in filtered
    assert not any(r.redaction_type == "url" for r in redactions)


# ---------------------------------------------------------------------------
# apply_regex_filter — redaction metadata
# ---------------------------------------------------------------------------


def test_regex_redaction_has_line_number():
    content = "Line 1\nPath: C:\\Users\\data.txt\nLine 3"
    _, redactions = apply_regex_filter(content)
    assert any(r.line_number == 2 for r in redactions)


# ---------------------------------------------------------------------------
# apply_frontmatter_filter — private: true blocks entry
# ---------------------------------------------------------------------------


def test_frontmatter_private_true_blocks():
    content = "---\nprivate: true\n---\n# Title\n\nBody text."
    filtered, blocked, reason = apply_frontmatter_filter(content, {"private": True})
    assert blocked is True
    assert filtered == ""
    assert "private: true" in reason


def test_frontmatter_private_false_allows():
    content = "---\nprivate: false\n---\n# Title"
    filtered, blocked, _ = apply_frontmatter_filter(content, {"private": False})
    assert blocked is False
    assert "# Title" in filtered


def test_frontmatter_missing_private_defaults_to_false():
    content = "---\ntitle: Something\n---\n# Title"
    _, blocked, _ = apply_frontmatter_filter(content, {})
    assert blocked is False


def test_frontmatter_private_sections_removed():
    content = (
        "---\ntitle: Test\n---\n"
        "# Introduction\n\nPublic content.\n\n"
        "# Internal Notes\n\nSecret stuff here.\n\n"
        "# Conclusion\n\nPublic ending."
    )
    filtered, blocked, _ = apply_frontmatter_filter(
        content, {"private-sections": ["Internal Notes"]}
    )
    assert blocked is False
    assert "Public content" in filtered
    assert "Secret stuff here" not in filtered
    assert "Public ending" in filtered


def test_frontmatter_private_sections_case_insensitive():
    content = (
        "---\ntitle: Test\n---\n"
        "## internal notes\n\nSecret.\n\n"
        "## Conclusion\n\nPublic."
    )
    filtered, _, _ = apply_frontmatter_filter(
        content, {"private-sections": ["Internal Notes"]}
    )
    assert "Secret" not in filtered
    assert "Public" in filtered


# ---------------------------------------------------------------------------
# apply_llm_redactions
# ---------------------------------------------------------------------------


def test_llm_redaction_applied():
    content = "Use the POVCALNET_V3 endpoint for all queries."
    findings = [
        {
            "line": 1,
            "type": "system-name",
            "original": "POVCALNET_V3",
            "replacement": "<internal-endpoint>",
        }
    ]
    filtered, redactions = apply_llm_redactions(content, findings)
    assert "POVCALNET_V3" not in filtered
    assert "<internal-endpoint>" in filtered
    assert any(r.layer == "llm" for r in redactions)


def test_llm_redaction_original_not_found_is_safe():
    content = "No sensitive content here."
    findings = [{"line": 1, "type": "jargon", "original": "MISSING_TEXT", "replacement": "..."}]
    filtered, redactions = apply_llm_redactions(content, findings)
    assert filtered == content
    assert not redactions


# ---------------------------------------------------------------------------
# FilterResult.summary()
# ---------------------------------------------------------------------------


def test_filter_result_summary_no_redactions():
    result = FilterResult(clean_content="hello", redactions=[])
    assert "no redactions" in result.summary()


def test_filter_result_summary_regex_only():
    result = FilterResult(
        clean_content="x",
        redactions=[Redaction("regex", "path", 1, 20)],
    )
    assert "1 regex redaction" in result.summary()


def test_filter_result_summary_llm_auto_applied():
    result = FilterResult(
        clean_content="x",
        redactions=[
            Redaction("regex", "email", 1, 15),
            Redaction("llm", "jargon", 3, 8),
        ],
    )
    s = result.summary()
    assert "1 regex redaction" in s
    assert "1 LLM redaction" in s
    assert "auto-applied" in s


# ---------------------------------------------------------------------------
# run_privacy_filter — full pipeline
# ---------------------------------------------------------------------------


def test_full_pipeline_clean_content():
    content = "# Title\n\nThe solution is to run `fmean(x, by=group)`."
    result = run_privacy_filter(content, frontmatter={})
    assert not result.blocked
    assert result.clean_content == content
    assert not result.redactions


def test_full_pipeline_regex_applied():
    content = r"# Fix\n\nCopy from E:\PovcalNet\data\file.csv"
    result = run_privacy_filter(content, frontmatter={})
    assert not result.blocked
    assert "<REDACTED:path>" in result.clean_content


def test_full_pipeline_blocked_on_private_true():
    content = "---\nprivate: true\n---\n# Secret\n\nDo not share."
    result = run_privacy_filter(content, frontmatter={"private": True})
    assert result.blocked is True
    assert result.clean_content == ""
    assert "private: true" in result.block_reason


def test_full_pipeline_llm_findings_applied():
    content = "Use the ALPHA_PLATFORM for data access."
    findings = [
        {
            "line": 1,
            "type": "system-name",
            "original": "ALPHA_PLATFORM",
            "replacement": "<internal-platform>",
        }
    ]
    result = run_privacy_filter(content, frontmatter={}, llm_findings=findings)
    assert "ALPHA_PLATFORM" not in result.clean_content
    assert "<internal-platform>" in result.clean_content
    assert any(r.layer == "llm" for r in result.redactions)


def test_full_pipeline_no_llm_findings_none():
    content = "Use the ALPHA_PLATFORM for data access."
    result = run_privacy_filter(content, frontmatter={}, llm_findings=None)
    # Without findings, LLM layer is skipped — original text preserved
    assert "ALPHA_PLATFORM" in result.clean_content
    assert not any(r.layer == "llm" for r in result.redactions)


# ---------------------------------------------------------------------------
# New tests added by cg-review (P1.10, P2.4, P1.2 Windows forward-slash)
# ---------------------------------------------------------------------------


def test_frontmatter_private_sections_non_list_warns_and_skips():
    """P1.10 — private-sections as string should warn and skip stripping."""
    content = "---\ntitle: T\n---\n## Internal Notes\n\nSecret.\n\n## End\n\nPublic."
    with pytest.warns(UserWarning, match="not a list"):
        filtered, _, _ = apply_frontmatter_filter(
            content, {"private-sections": "Internal Notes"}
        )
    assert "Secret" in filtered  # stripping skipped — warned only


def test_frontmatter_atx_closed_heading_stripped():
    """P2.4 — ATX closed heading (## Title ##) must still be stripped."""
    content = (
        "---\ntitle: Test\n---\n"
        "# Introduction\n\nPublic.\n\n"
        "# Internal Notes ##\n\nSecret.\n\n"
        "# Conclusion\n\nPublic end."
    )
    filtered, _, _ = apply_frontmatter_filter(
        content, {"private-sections": ["Internal Notes"]}
    )
    assert "Secret" not in filtered
    assert "Public" in filtered


def test_frontmatter_private_section_at_end_of_document():
    """P2.7 testing — trailing private section (no following heading) stripped."""
    content = (
        "---\ntitle: Test\n---\n"
        "# Introduction\n\nPublic content.\n\n"
        "# Internal Notes\n\nSecret at the very end."
    )
    filtered, _, _ = apply_frontmatter_filter(
        content, {"private-sections": ["Internal Notes"]}
    )
    assert "Secret at the very end" not in filtered
    assert "Public content" in filtered


def test_regex_windows_forward_slash_path_redacted():
    """P1.2 — forward-slash Windows path (Git Bash, WSL, R) must be redacted."""
    content = "Loaded from E:/PovcalNet/data/file.dta"
    filtered, _ = apply_regex_filter(content)
    assert "<REDACTED:path>" in filtered
    assert "E:/PovcalNet" not in filtered


def test_build_llm_filter_prompt_includes_content():
    """P2.15 — build_llm_filter_prompt must embed the content."""
    content = "Use ALPHA_PLATFORM for data access."
    prompt = build_llm_filter_prompt(content)
    assert content in prompt
    assert "privacy filter" in prompt.lower()
    assert "JSON object" in prompt


def test_full_pipeline_rerun_regex_catches_llm_injected_path():
    """P2.5 verify — if LLM redaction itself injects a file path, the second-pass
    regex must catch it so no paths leak through the filter pipeline."""
    content = "Use the ALPHA_PLATFORM endpoint."
    # Adversarial LLM: instead of a placeholder, it injects a real Windows path
    findings = [
        {
            "line": 1,
            "type": "system-name",
            "original": "ALPHA_PLATFORM",
            "replacement": r"C:\Users\wb384996\internal\endpoint",
        }
    ]
    result = run_privacy_filter(content, frontmatter={}, llm_findings=findings)
    assert r"C:\Users\wb384996" not in result.clean_content
    assert "<REDACTED:path>" in result.clean_content
