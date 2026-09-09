"""Created 2026-08-12. Read-only compatibility handling for legacy records."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import yaml

from .transactions import ArtifactStore, TransactionResult

SUPPORTED_LOCAL_EXTENSIONS = frozenset(
    {".pdf", ".docx", ".md", ".markdown", ".tex", ".latex", ".html", ".htm"}
)


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
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    candidate = resources_root / path
    if candidate.is_symlink() or not candidate.is_file():
        return False
    if candidate.suffix.lower() not in SUPPORTED_LOCAL_EXTENSIONS:
        return False
    resolved = candidate.resolve(strict=True)
    return resolved.is_relative_to(resources_root.resolve())


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


def persist_quarantine_result(
    result: MigrationResult,
    store: ArtifactStore,
    *,
    expected_revision: int,
) -> TransactionResult:
    """Persist a quarantined legacy record without enabling or rewriting it.

    Args:
        result: Migration result to preserve.
        store: Canonical evidence artifact store.
        expected_revision: Aggregate revision read by the caller.

    Returns:
        Journaled transaction result for the quarantine artifact.

    Raises:
        ValueError: If the result is not quarantine-eligible or lacks an ID.

    Example:
        ``persist_quarantine_result(result, store, expected_revision=0)``.
    """
    if result.disposition not in {
        MigrationDisposition.EXTERNAL_QUARANTINE,
        MigrationDisposition.UNRESOLVED,
        MigrationDisposition.LOCAL_REVIEW_REQUIRED,
    }:
        raise ValueError("Only non-activatable migration results may be quarantined")
    record_id = result.preserved_record.get("id")
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("Quarantined records require a stable legacy id")
    path = store.root / "external-quarantine.yaml"
    if path.exists():
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("External quarantine must be a YAML mapping")
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("External quarantine records must be a list")
    retained = {
        str(item.get("id")): item
        for item in records
        if isinstance(item, dict) and item.get("id")
    }
    retained[record_id] = {
        **result.preserved_record,
        "quarantine_disposition": result.disposition.value,
        "quarantine_reason": result.reason,
        "eligible_for_approval": False,
        "requires_local_verification": True,
    }
    payload = {
        "schema_version": "research-evidence-external-quarantine-v1",
        "records": [retained[key] for key in sorted(retained)],
    }
    with store.transaction(
        expected_revision=expected_revision,
        actor="migration",
        action="quarantine-legacy-record",
    ) as transaction:
        transaction.stage_yaml("external-quarantine.yaml", payload)
        return transaction.commit()


def migrate_and_persist_legacy_record(
    record: Mapping[str, Any],
    resources_root: Path,
    store: ArtifactStore,
    *,
    expected_revision: int,
) -> MigrationResult:
    """Classify one legacy record and persist any non-activatable outcome.

    Args:
        record: Untrusted predecessor record to preserve.
        resources_root: Configured local resource root for path validation.
        store: Canonical evidence artifact store.
        expected_revision: Aggregate revision read by the caller.

    Returns:
        The classification returned by :func:`migrate_legacy_record`.

    Example:
        ``migrate_and_persist_legacy_record(record, root, store, expected_revision=0)``.
    """
    result = migrate_legacy_record(record, resources_root)
    if not result.eligible_for_approval:
        persist_quarantine_result(
            result,
            store,
            expected_revision=expected_revision,
        )
    return result
