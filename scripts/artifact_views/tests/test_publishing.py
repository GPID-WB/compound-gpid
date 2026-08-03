"""Tests for deterministic mode, ownership, and theme resolution."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from artifact_views.provenance import PublicationProvenance  # pylint: disable=import-error
from artifact_views.publishing import (  # pylint: disable=import-error
    PublishMode,
    resolve_publication,
)

SOURCE = Path("docs/guide.md")
OUTPUT = Path(".cg-docs/views/documents/docs/guide.html")


def _owned(*, theme: str = "reference", version: int = 1) -> PublicationProvenance:
    return PublicationProvenance.from_source(
        source_path=SOURCE,
        source_bytes=b"# Guide\n",
        output_path=OUTPUT,
        document_type="generic-markdown",
        renderer_version="0.2.0",
        theme_name=theme,
        theme_version=version,
        generated_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize("mode", (PublishMode.RENDER, PublishMode.AUTOMATIC))
def test_mutating_modes_default_missing_output_to_reference(mode: PublishMode) -> None:
    decision = resolve_publication(
        mode=mode,
        source_path=SOURCE,
        output_path=OUTPUT,
        document_type="generic-markdown",
        output_exists=False,
    )

    assert decision.theme.name == "reference"
    assert decision.mutate is True
    assert decision.inspect_output is True


def test_owned_v2_reuses_recorded_theme_at_current_contract_version() -> None:
    decision = resolve_publication(
        mode=PublishMode.RENDER,
        source_path=SOURCE,
        output_path=OUTPUT,
        document_type="generic-markdown",
        output_exists=True,
        existing_provenance=_owned(version=0),
    )

    assert decision.theme.contract_version == 1
    assert decision.stale is True


@pytest.mark.parametrize("mode", (PublishMode.VALIDATE_ONLY, PublishMode.AUTOMATIC))
def test_nonmutating_validation_does_not_inspect_output(mode: PublishMode) -> None:
    decision = resolve_publication(
        mode=mode,
        source_path=SOURCE,
        output_path=OUTPUT,
        document_type="generic-markdown",
        explicit_theme="reference",
        output_exists=True,
        automatic_enabled=mode is not PublishMode.AUTOMATIC,
    )

    assert decision.inspect_output is False
    assert decision.mutate is False


def test_check_without_output_is_stale_and_nonmutating() -> None:
    decision = resolve_publication(
        mode=PublishMode.CHECK,
        source_path=SOURCE,
        output_path=OUTPUT,
        document_type="generic-markdown",
        output_exists=False,
    )

    assert decision.stale is True
    assert decision.mutate is False


@pytest.mark.parametrize(
    "provenance",
    (
        None,
        _owned(),
    ),
)
def test_explicit_registered_theme_never_bypasses_destination_ownership(
    provenance: PublicationProvenance | None,
) -> None:
    kwargs = {}
    if provenance is not None:
        kwargs["existing_provenance"] = PublicationProvenance(
            **{**provenance.__dict__, "source_path": "docs/other.md"}
        )
    with pytest.raises(ValueError, match="owned|provenance"):
        resolve_publication(
            mode=PublishMode.RENDER,
            source_path=SOURCE,
            output_path=OUTPUT,
            document_type="generic-markdown",
            explicit_theme="reference",
            output_exists=True,
            **kwargs,
        )


def test_unknown_recorded_theme_fails_until_explicit_registered_theme() -> None:
    unknown = _owned(theme="removed-theme")
    with pytest.raises(ValueError, match="unknown|Unknown"):
        resolve_publication(
            mode=PublishMode.RENDER,
            source_path=SOURCE,
            output_path=OUTPUT,
            document_type="generic-markdown",
            output_exists=True,
            existing_provenance=unknown,
        )

    recovered = resolve_publication(
        mode=PublishMode.RENDER,
        source_path=SOURCE,
        output_path=OUTPUT,
        document_type="generic-markdown",
        explicit_theme="reference",
        output_exists=True,
        existing_provenance=unknown,
    )
    assert recovered.theme.name == "reference"


def test_output_identity_mismatch_fails_before_mutation() -> None:
    provenance = _owned()
    mismatched = PublicationProvenance(
        **{**provenance.__dict__, "output_path": ".cg-docs/views/documents/other.html"}
    )

    with pytest.raises(ValueError, match="owner|identity|output"):
        resolve_publication(
            mode=PublishMode.RENDER,
            source_path=SOURCE,
            output_path=OUTPUT,
            document_type="generic-markdown",
            output_exists=True,
            existing_provenance=mismatched,
        )


def test_case_distinct_posix_source_is_not_the_same_owner() -> None:
    provenance = _owned()
    case_distinct = PublicationProvenance(
        **{**provenance.__dict__, "source_path": "docs/Guide.md"}
    )

    with pytest.raises(ValueError, match="different source"):
        resolve_publication(
            mode=PublishMode.RENDER,
            source_path=Path("docs/guide.md"),
            output_path=OUTPUT,
            document_type="generic-markdown",
            output_exists=True,
            existing_provenance=case_distinct,
        )


def test_explicit_theme_check_still_validates_owner_identity() -> None:
    foreign = PublicationProvenance(
        **{**_owned().__dict__, "source_path": "docs/other.md"}
    )

    with pytest.raises(ValueError, match="different source"):
        resolve_publication(
            mode=PublishMode.CHECK,
            source_path=SOURCE,
            output_path=OUTPUT,
            document_type="generic-markdown",
            explicit_theme="reference",
            output_exists=True,
            existing_provenance=foreign,
        )