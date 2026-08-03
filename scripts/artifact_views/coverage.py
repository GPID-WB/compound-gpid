"""Exact-once source ownership checks for semantic artifact rendering."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from artifact_views.errors import ArtifactCoverageError
from artifact_views.model import SourceLedgerDocument


@dataclass(frozen=True)
class RenderedOwner:
    """One rendered element claiming one substantive source block."""

    owner_id: str
    source_block_id: str
    derived: bool = False

    def __post_init__(self) -> None:
        if not self.owner_id.strip():
            raise ArtifactCoverageError("Rendered owner ID must be non-empty.")
        if not self.source_block_id.strip():
            raise ArtifactCoverageError("Rendered source block ID must be non-empty.")
        if self.derived:
            raise ArtifactCoverageError(
                f"Derived owner {self.owner_id!r} cannot satisfy source coverage.",
                corrective_action="Keep derived elements outside the source-owner ledger.",
            )


class CoverageLedger:
    """Validate a bijection between substantive blocks and rendered owners."""

    def __init__(self, document: SourceLedgerDocument) -> None:
        self._document = document

    def validate(self, owners: Sequence[RenderedOwner]) -> None:
        """Require every substantive block exactly once and no invented IDs.

        Args:
            owners: Complete rendered-owner sequence before serialization.

        Returns:
            ``None`` after all source ownership checks pass.

        Raises:
            ArtifactCoverageError: If ownership is missing, duplicated, or unknown.

        Example:
            ``ledger.validate(rendered_owners)`` verifies exact-once coverage.
        """
        owner_ids = [owner.owner_id for owner in owners]
        duplicate_owner = _first_duplicate(owner_ids)
        if duplicate_owner is not None:
            raise ArtifactCoverageError(
                f"Duplicate rendered owner ID {duplicate_owner!r}.",
                source_path=self._document.identity.source_path,
                corrective_action="Assign every rendered wrapper a unique owner ID.",
            )

        expected = {
            block.source_id for block in self._document.substantive_blocks
        }
        source_ids = [owner.source_block_id for owner in owners]
        unknown = sorted(set(source_ids) - expected)
        if unknown:
            raise ArtifactCoverageError(
                f"Rendered owner references unknown source block(s): {unknown}.",
                source_path=self._document.identity.source_path,
                corrective_action="Remove invented source ownership references.",
            )
        duplicate_source = _first_duplicate(source_ids)
        if duplicate_source is not None:
            raise ArtifactCoverageError(
                f"Duplicate rendered owner for source block {duplicate_source!r}.",
                source_path=self._document.identity.source_path,
                corrective_action="Render each substantive block exactly once.",
            )
        missing = sorted(expected - set(source_ids))
        if missing:
            raise ArtifactCoverageError(
                f"Missing rendered owner for source block(s): {missing}.",
                source_path=self._document.identity.source_path,
                corrective_action="Render every substantive source block once.",
            )


def _first_duplicate(values: Sequence[str]):
    seen = set()
    for value in values:
        if value in seen:
            return value
        seen.add(value)
    return None
