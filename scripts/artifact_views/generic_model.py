"""Independent immutable models for generic Markdown publication."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from artifact_views.errors import ArtifactModelError
from artifact_views.model import (
    Frontmatter,
    LexicalBlock,
    SubstantiveBlock,
    validate_source_ledger,
)

GENERIC_DOCUMENT_TYPE = "generic-markdown"
SUPPORTED_CALLOUTS = frozenset(
    {"NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION", "DECISION", "PROS", "CONS"}
)


@dataclass(frozen=True)
class GenericIdentity:
    """Canonical source identity without typed artifact schema authority."""

    source_path: Path
    title: str
    document_type: str = GENERIC_DOCUMENT_TYPE

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Generic document title must be non-empty.")
        if self.document_type != GENERIC_DOCUMENT_TYPE:
            raise ValueError("Generic document type must remain stable.")


@dataclass(frozen=True)
class GenericHeading:
    """One source-backed heading used for generic navigation."""

    level: int
    title: str
    source_block_id: str

    def __post_init__(self) -> None:
        if self.level < 1 or self.level > 6:
            raise ValueError("Generic heading level must be between one and six.")
        if not self.title.strip():
            raise ValueError("Generic heading title must be non-empty.")


@dataclass(frozen=True)
class GenericCallout:
    """One exact source-backed generic callout marker."""

    kind: str
    source_block_id: str

    def __post_init__(self) -> None:
        if self.kind not in SUPPORTED_CALLOUTS:
            raise ValueError(f"Unsupported generic callout kind {self.kind!r}.")


@dataclass(frozen=True)
class GenericDocument:
    """Generic source state with complete lexical and semantic ownership."""

    identity: GenericIdentity
    frontmatter: Frontmatter
    lexical_blocks: Tuple[LexicalBlock, ...]
    substantive_blocks: Tuple[SubstantiveBlock, ...]
    source_length_bytes: int
    headings: Tuple[GenericHeading, ...] = ()
    callouts: Tuple[GenericCallout, ...] = ()

    def __post_init__(self) -> None:
        validate_source_ledger(self)
        known = {block.source_id for block in self.substantive_blocks}
        relation_ids = [heading.source_block_id for heading in self.headings]
        relation_ids.extend(callout.source_block_id for callout in self.callouts)
        unknown = sorted(set(relation_ids) - known)
        if unknown:
            raise ArtifactModelError(
                f"Generic relationships reference unknown source blocks: {unknown}.",
                source_path=self.identity.source_path,
                corrective_action=(
                    "Reference only substantive source blocks from this document."
                ),
            )