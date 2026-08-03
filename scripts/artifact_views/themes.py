"""Closed presentation-theme registry for artifact and document views."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from artifact_views.reference_theme import reference_css


@dataclass(frozen=True)
class ThemeContract:
    """Stable registered presentation identity."""

    name: str
    contract_version: int
    stylesheet: str


_THEMES = {"reference": ThemeContract("reference", 1, reference_css())}
_DEFAULTS = {
    "brainstorm": "reference",
    "plan": "reference",
    "generic-markdown": "reference",
}


def get_theme(name: str) -> ThemeContract:
    """Return one registered theme or fail without fallback.

    Args:
        name: Exact registered theme name.

    Returns:
        Immutable theme contract.

    Example:
        ``get_theme('reference').contract_version`` returns 1.
    """
    try:
        return _THEMES[name]
    except KeyError as error:
        raise ValueError(f"Unknown theme {name!r}.") from error


def resolve_theme(
    document_type: str,
    explicit_theme: Optional[str] = None,
) -> ThemeContract:
    """Resolve an explicit theme or the document-type default.

    Args:
        document_type: Stable strict or generic document type.
        explicit_theme: Optional exact registered theme name.

    Returns:
        Resolved immutable theme contract.

    Example:
        ``resolve_theme('generic-markdown').name`` is ``reference``.
    """
    if explicit_theme is not None:
        return get_theme(explicit_theme)
    try:
        return get_theme(_DEFAULTS[document_type])
    except KeyError as error:
        raise ValueError(f"Unknown document type {document_type!r}.") from error