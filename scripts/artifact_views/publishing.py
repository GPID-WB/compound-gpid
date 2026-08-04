"""Deterministic publication mode, ownership, and theme resolution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from artifact_views.provenance import ArtifactProvenance, PublicationProvenance
from artifact_views.themes import ThemeContract, get_theme, resolve_theme


class PublishMode(str, Enum):
    """Supported one-file publication operations."""

    RENDER = "render"
    AUTOMATIC = "automatic"
    VALIDATE_ONLY = "validate-only"
    CHECK = "check"


@dataclass(frozen=True)
class PublicationDecision:
    """Fully resolved pre-mutation publication behavior."""

    theme: ThemeContract
    inspect_output: bool
    mutate: bool
    stale: bool


def resolve_publication(
    *,
    mode: PublishMode,
    source_path: Path,
    output_path: Path,
    document_type: str,
    explicit_theme: Optional[str] = None,
    output_exists: bool,
    existing_provenance: Optional[
        ArtifactProvenance | PublicationProvenance
    ] = None,
    automatic_enabled: bool = True,
) -> PublicationDecision:
    """Resolve theme and ownership before any output mutation or comparison.

    Args:
        mode: Requested render, automatic, validation, or check operation.
        source_path: Normalized source identity.
        output_path: Registered destination identity.
        document_type: Stable strict or generic document type.
        explicit_theme: Optional user-selected registered theme.
        output_exists: Whether a destination currently exists.
        existing_provenance: Valid parsed owner identity when available.
        automatic_enabled: Whether automatic output mutation is enabled.

    Returns:
        Complete pre-mutation theme, inspection, mutation, and stale decision.

    Example:
        Resolve this decision before reading or replacing an existing output.
    """
    mode = PublishMode(mode)
    if mode is PublishMode.VALIDATE_ONLY or (
        mode is PublishMode.AUTOMATIC and not automatic_enabled
    ):
        return PublicationDecision(
            resolve_theme(document_type, explicit_theme),
            inspect_output=False,
            mutate=False,
            stale=False,
        )

    mutating = mode in {PublishMode.RENDER, PublishMode.AUTOMATIC}
    if not output_exists:
        return PublicationDecision(
            resolve_theme(document_type, explicit_theme),
            inspect_output=True,
            mutate=mutating,
            stale=mode is PublishMode.CHECK,
        )

    if existing_provenance is None:
        raise ValueError(
            "Existing output has no valid provenance owner and cannot be replaced."
        )
    if isinstance(existing_provenance, ArtifactProvenance):
        if document_type == "generic-markdown":
            raise ValueError(
                "Legacy provenance does not prove generic output ownership."
            )
        if existing_provenance.source_path != Path(source_path).as_posix():
            raise ValueError(
                "Legacy output provenance belongs to a different typed source."
            )
        theme = resolve_theme(document_type, explicit_theme)
        return PublicationDecision(theme, True, mutating, True)

    expected_source = Path(source_path).as_posix()
    expected_output = Path(output_path).as_posix()
    if (
        existing_provenance.source_path != expected_source
        or existing_provenance.output_path != expected_output
        or existing_provenance.document_type != document_type
    ):
        raise ValueError(
            "Existing output provenance belongs to a different source, document "
            "type, or output identity."
        )
    if explicit_theme is not None:
        theme = get_theme(explicit_theme)
    else:
        theme = get_theme(existing_provenance.theme_name)
    return PublicationDecision(
        theme=theme,
        inspect_output=True,
        mutate=mutating,
        stale=existing_provenance.theme_version != theme.contract_version,
    )