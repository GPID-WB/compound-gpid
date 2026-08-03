"""Tests for the closed presentation-theme registry."""
from __future__ import annotations

import pytest

from artifact_views.reference_theme import reference_css  # pylint: disable=import-error
from artifact_views.themes import get_theme, resolve_theme  # pylint: disable=import-error


def test_reference_is_the_only_registered_versioned_theme() -> None:
    theme = get_theme("reference")

    assert theme.name == "reference"
    assert theme.contract_version == 1
    assert theme.stylesheet == reference_css()


def test_reference_is_default_for_strict_and_generic_documents() -> None:
    for document_type in ("brainstorm", "plan", "generic-markdown"):
        assert resolve_theme(document_type).name == "reference"


def test_unknown_theme_fails_without_fallback() -> None:
    with pytest.raises(ValueError, match="Unknown theme"):
        resolve_theme("generic-markdown", "editorial")