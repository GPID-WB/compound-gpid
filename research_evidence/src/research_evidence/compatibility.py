"""Created 2026-08-12. Read-only compatibility handling for legacy records."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


class MigrationDisposition(str, Enum):
    """Classify how one predecessor record is handled in v1.

    Args:
        value: Serialized migration disposition.

    Returns:
        A validated migration disposition.

    Example:
        ``MigrationDisposition.EXTERNAL_QUARANTINE`` blocks external activation.
    """

    LOCAL_IMPORT = "local-import"
    EXTERNAL_QUARANTINE = "external-quarantine"
    LOCAL_REVIEW_REQUIRED = "local-review-required"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class MigrationResult:
    """Return a preserved legacy record and its safe activation state.

    Args:
        disposition: Compatibility classification.
        preserved_record: Deep-copied original record fields.
        eligible_for_approval: Whether v1 may approve the record directly.
        requires_local_verification: Whether a new local verification is required.
        reason: Stable machine-readable reason.

    Returns:
        An immutable migration result.

    Example:
        ``MigrationResult(MigrationDisposition.UNRESOLVED, {}, False, True, "missing-origin")``.
    """

    disposition: MigrationDisposition
    preserved_record: dict[str, Any]
    eligible_for_approval: bool
    requires_local_verification: bool
    reason: str


def _safe_local_path(value: object, resources_root: Path) -> bool:
    """Return whether a legacy local path remains under the resource root."""
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    candidate = (resources_root / path).resolve(strict=False)
    return candidate.is_relative_to(resources_root.resolve())


def migrate_legacy_record(
    record: Mapping[str, Any],
    resources_root: Path,
) -> MigrationResult:
    """Classify a predecessor record without fetching or rewriting its fields.

    Args:
        record: Untrusted legacy mapping to preserve exactly.
        resources_root: Configured local resource root for path validation.

    Returns:
        A migration result whose preserved record is a deep copy of ``record``.

    Example:
        ``migrate_legacy_record({"origin": "external-opt-in"}, root)`` quarantines it.
    """
    preserved = deepcopy(dict(record))
    origin = preserved.get("origin")
    if origin == "external-opt-in":
        return MigrationResult(
            MigrationDisposition.EXTERNAL_QUARANTINE,
            preserved,
            False,
            True,
            "external-opt-in-quarantined",
        )
    if origin != "repo-local":
        return MigrationResult(
            MigrationDisposition.UNRESOLVED,
            preserved,
            False,
            True,
            "missing-origin" if origin is None else "invalid-origin",
        )
    if not _safe_local_path(preserved.get("original_path"), resources_root):
        return MigrationResult(
            MigrationDisposition.UNRESOLVED,
            preserved,
            False,
            True,
            "invalid-local-path",
        )
    if preserved.get("verification_basis") == "converted-text":
        return MigrationResult(
            MigrationDisposition.LOCAL_REVIEW_REQUIRED,
            preserved,
            False,
            True,
            "legacy-converted-authority",
        )
    return MigrationResult(
        MigrationDisposition.LOCAL_IMPORT,
        preserved,
        True,
        False,
        "local-record-preserved",
    )
