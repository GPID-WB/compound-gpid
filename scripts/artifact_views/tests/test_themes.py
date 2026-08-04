"""Tests for the closed presentation-theme registry."""
from __future__ import annotations

import pytest

from artifact_views.editorial_theme import editorial_css  # pylint: disable=import-error
from artifact_views.reference_theme import reference_css  # pylint: disable=import-error
from artifact_views.themes import get_theme, resolve_theme  # pylint: disable=import-error


def test_reference_and_editorial_are_registered_versioned_themes() -> None:
    ref = get_theme("reference")
    assert ref.name == "reference"
    assert ref.contract_version == 1
    assert ref.stylesheet == reference_css()

    ed = get_theme("editorial")
    assert ed.name == "editorial"
    assert ed.contract_version == 1
    assert len(ed.stylesheet) > 0


def test_reference_is_default_for_strict_and_generic_documents() -> None:
    for document_type in ("brainstorm", "plan", "generic-markdown"):
        assert resolve_theme(document_type).name == "reference"


def test_unknown_theme_fails_without_fallback() -> None:
    with pytest.raises(ValueError, match="Unknown theme"):
        resolve_theme("generic-markdown", "nonexistent")


def test_editorial_theme_can_be_resolved_explicitly() -> None:
    theme = resolve_theme("generic-markdown", "editorial")
    assert theme.name == "editorial"
    assert theme.contract_version == 1
    assert theme.stylesheet == editorial_css()


def test_editorial_css_contains_required_design_tokens() -> None:
    css = editorial_css()
    required_tokens = [
        "--ink",
        "--muted",
        "--paper",
        "--coral",
        "--teal",
        "--blue",
        "--yellow",
        "--success",
        "--danger",
        "--content",
        "--radius",
        "--header-height",
    ]
    for token in required_tokens:
        assert token in css, f"Missing design token: {token}"


def test_editorial_css_contains_required_breakpoints() -> None:
    css = editorial_css()
    assert "@media (max-width: 980px)" in css
    assert "@media (max-width: 720px)" in css


def test_editorial_css_contains_accessibility_contract() -> None:
    css = editorial_css()
    assert ".skip-link" in css
    assert ":focus-visible" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_editorial_css_contains_print_contract() -> None:
    css = editorial_css()
    assert "@media print" in css


def test_editorial_css_is_self_contained_no_external_references() -> None:
    css = editorial_css()
    assert "@import" not in css
    assert "url(http" not in css.lower()


def test_cross_theme_stylesheets_are_distinct() -> None:
    ref_css = reference_css()
    ed_css = editorial_css()
    assert ref_css != ed_css


def test_cross_theme_both_have_required_structural_selectors() -> None:
    """Both themes must support the shared HTML shell structure."""
    ref_css = reference_css()
    ed_css = editorial_css()
    structural_selectors = [
        ".skip-link",
        ".masthead",
        ".layout",
        ".sidebar",
        ".provenance",
    ]
    for selector in structural_selectors:
        assert selector in ref_css, f"Reference missing: {selector}"
        assert selector in ed_css, f"Editorial missing: {selector}"