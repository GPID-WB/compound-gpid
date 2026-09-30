"""Strict, immutable project skill provenance snapshots."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

import secure_fs

from skill_management import contracts
from skill_management import paths as path_policy
from skill_management.services import bundles


PROVENANCE_ROOT = ".compound-gpid/skill-provenance"
CANONICAL_PROVENANCE_ROOT = ".github/shared/skill-management/provenance"
_REPARSE_POINT_FLAG = 0x400
_IMMUTABLE_REFERENCE = re.compile(
    r"(?<![0-9a-f])(?:[0-9a-f]{40}|[0-9a-f]{64})(?![0-9a-f])"
)


class ProvenanceValidationError(ValueError):
    """Raised when committed project provenance is absent, unsafe, or invalid."""


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class ProvenanceSnapshot:
    """One validated immutable project provenance inventory.

    Args:
        digest: Stable digest of every provenance path and exact file digest.
        records: Provenance records ordered by skill identifier.

    Example:
        ``snapshot.record_by_id("project-tool")``
    """

    digest: str
    records: Tuple[Mapping[str, Any], ...]

    def record_by_id(self, identifier: str) -> Dict[str, Any]:
        """Return a detached provenance record for one project skill.

        Args:
            identifier: Immutable project skill identifier.

        Returns:
            A mutable copy of the provenance record.

        Raises:
            KeyError: If no record has the requested identifier.

        Example:
            ``snapshot.record_by_id("project-tool")``
        """
        for record in self.records:
            if record.get("skillId") == identifier:
                return _thaw(record)
        raise KeyError(identifier)


def validate_audit_metadata(approver: str, review_reference: str) -> None:
    """Validate required audit metadata without treating it as authorization.

    Args:
        approver: Non-empty reviewer label recorded for audit.
        review_reference: Reference containing one immutable full digest.

    Raises:
        ProvenanceValidationError: If either field is absent or mutable-looking.

    Example:
        ``validate_audit_metadata("maintainer", "reviewed=" + "a" * 40)``
    """
    if not isinstance(approver, str) or not approver.strip() or "\n" in approver:
        raise ProvenanceValidationError(
            "Maintainer approver audit metadata is required"
        )
    if (
        not isinstance(review_reference, str)
        or not review_reference.strip()
        or "\n" in review_reference
        or _IMMUTABLE_REFERENCE.search(review_reference.casefold()) is None
    ):
        raise ProvenanceValidationError(
            "Review reference must contain one immutable full SHA or SHA-256 digest"
        )


def redacted_inventory_diff(
    before: "bundles.BundleInventory",
    after: "bundles.BundleInventory",
) -> Tuple[Dict[str, Any], ...]:
    """Compare atomic inventories without exposing candidate content.

    Args:
        before: Current approved bundle inventory.
        after: Newly admitted bundle inventory with the same identifier.

    Returns:
        Deterministic path, change, size, and digest records.

    Raises:
        ProvenanceValidationError: If immutable bundle identity changed.

    Example:
        ``changes = redacted_inventory_diff(current, candidate)``
    """
    if before.identifier != after.identifier:
        raise ProvenanceValidationError("Imported skill identifier is immutable")
    before_files = {item.bundle_path: item for item in before.files}
    after_files = {item.bundle_path: item for item in after.files}
    changes = []
    for path in sorted(set(before_files) | set(after_files)):
        old = before_files.get(path)
        new = after_files.get(path)
        if old is not None and new is not None and old.sha256 == new.sha256:
            continue
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        else:
            change = "modified"
        record = {"path": path, "change": change}  # type: Dict[str, Any]
        if old is not None:
            record["beforeSha256"] = old.sha256
            record["beforeSize"] = len(old.content)
        if new is not None:
            record["afterSha256"] = new.sha256
            record["afterSize"] = len(new.content)
        changes.append(record)
    return tuple(changes)


def redacted_diff_digest(changes: Sequence[Mapping[str, Any]]) -> str:
    """Return the stable digest of one deterministic redacted diff."""
    return hashlib.sha256(
        contracts.canonical_json_bytes([dict(item) for item in changes])
    ).hexdigest()


def provenance_record(
    identifier: str,
    origin: str,
    repository: str,
    source_path: str,
    commit: str,
    bundle_digest: str,
    event: str,
    approver: str,
    review_reference: str,
    *,
    policy_digest: str = "",
    review_evidence_digest: str = "",
) -> Dict[str, Any]:
    """Build one initial immutable-source provenance record."""
    validate_audit_metadata(approver, review_reference)
    history = {
        "sequence": 1,
        "event": event,
        "commit": commit,
        "bundleDigest": bundle_digest,
        "approval": {
            "actor": approver,
            "reviewReference": review_reference,
        },
    }
    if policy_digest:
        history["policyDigest"] = policy_digest
    if review_evidence_digest:
        history["reviewEvidenceDigest"] = review_evidence_digest
    return {
        "schema": "cg-skill-provenance-v1",
        "schemaVersion": 1,
        "skillId": identifier,
        "origin": origin,
        "admission": "approved",
        "lifecycle": "current",
        "source": {
            "repository": repository,
            "path": source_path,
            "commit": commit,
            "bundleDigest": bundle_digest,
        },
        "history": [history],
        "migrations": [],
    }


def append_update(
    record: Mapping[str, Any],
    commit: str,
    bundle_digest: str,
    approver: str,
    review_reference: str,
    policy_digest: str,
    review_evidence_digest: str,
    changes: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Append one full-SHA source transition while preserving prior history."""
    validate_audit_metadata(approver, review_reference)
    updated = json.loads(json.dumps(_thaw(record)))
    if updated.get("lifecycle") != "current" or updated.get("admission") != "approved":
        raise ProvenanceValidationError(
            "Only approved current imported skills can update"
        )
    history = updated.get("history")
    source = updated.get("source")
    if not isinstance(history, list) or not history or not isinstance(source, dict):
        raise ProvenanceValidationError("Imported skill provenance history is invalid")
    if source.get("commit") == commit:
        raise ProvenanceValidationError("Imported skill update requires a new full SHA")
    event = {
        "sequence": len(history) + 1,
        "event": "updated",
        "commit": commit,
        "bundleDigest": bundle_digest,
        "policyDigest": policy_digest,
        "reviewEvidenceDigest": review_evidence_digest,
        "diffDigest": redacted_diff_digest(changes),
        "diff": [dict(item) for item in changes],
        "approval": {
            "actor": approver,
            "reviewReference": review_reference,
        },
    }
    history.append(event)
    source["commit"] = commit
    source["bundleDigest"] = bundle_digest
    return updated


def append_deprecation(
    record: Mapping[str, Any],
    successor_id: str,
    approver: str,
    review_reference: str,
    revision: str,
) -> Dict[str, Any]:
    """Append one immutable successor-bound deprecation record."""
    validate_audit_metadata(approver, review_reference)
    updated = json.loads(json.dumps(_thaw(record)))
    if updated.get("lifecycle") != "current":
        raise ProvenanceValidationError("Only a current skill can be deprecated")
    if successor_id == updated.get("skillId"):
        raise ProvenanceValidationError("A skill cannot succeed itself")
    history = updated.get("history")
    source = updated.get("source")
    if not isinstance(history, list) or not history or not isinstance(source, dict):
        raise ProvenanceValidationError("Skill provenance history is invalid")
    deprecation_record = {
        "schema": "cg-skill-deprecation-record-v1",
        "skillId": updated["skillId"],
        "origin": updated["origin"],
        "successorId": successor_id,
        "bundleDigest": source["bundleDigest"],
        "revision": revision,
        "approval": {
            "actor": approver,
            "reviewReference": review_reference,
        },
    }
    record_digest = hashlib.sha256(
        contracts.canonical_json_bytes(deprecation_record)
    ).hexdigest()
    history.append(
        {
            "sequence": len(history) + 1,
            "event": "deprecated",
            "commit": revision,
            "bundleDigest": source["bundleDigest"],
            "successorId": successor_id,
            "recordDigest": record_digest,
            "approval": {
                "actor": approver,
                "reviewReference": review_reference,
            },
        }
    )
    updated["lifecycle"] = "deprecated"
    updated["successorId"] = successor_id
    updated["deprecatedRecordDigest"] = record_digest
    return updated


def append_removal(
    record: Mapping[str, Any],
    removed_revision: str,
    approver: str,
    review_reference: str,
    migrations: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Append one terminal tombstone while preserving deprecation evidence."""
    validate_audit_metadata(approver, review_reference)
    updated = json.loads(json.dumps(_thaw(record)))
    if updated.get("lifecycle") != "deprecated":
        raise ProvenanceValidationError("Only a deprecated skill can be removed")
    record_digest = updated.get("deprecatedRecordDigest")
    successor_id = updated.get("successorId")
    if not isinstance(record_digest, str) or not isinstance(successor_id, str):
        raise ProvenanceValidationError(
            "Removal requires an immutable deprecation record and successor"
        )
    history = updated.get("history")
    source = updated.get("source")
    if not isinstance(history, list) or not history or not isinstance(source, dict):
        raise ProvenanceValidationError("Skill provenance history is invalid")
    summaries = []
    for migration in sorted(migrations, key=lambda item: str(item.get("id", ""))):
        summaries.append(
            {
                "id": str(migration["id"]),
                "status": "applied",
                "digest": str(migration["digest"]),
            }
        )
    existing = list(updated.get("migrations", []))
    existing_ids = {item.get("id") for item in existing if isinstance(item, dict)}
    if any(item["id"] in existing_ids for item in summaries):
        raise ProvenanceValidationError("Migration identifier was already recorded")
    updated["migrations"] = existing + summaries
    event = {
        "sequence": len(history) + 1,
        "event": "removed",
        "bundleDigest": source["bundleDigest"],
        "recordDigest": record_digest,
        "approval": {
            "actor": approver,
            "reviewReference": review_reference,
        },
    }
    if re.fullmatch(r"[0-9a-f]{40}", removed_revision):
        event["commit"] = removed_revision
    history.append(event)
    updated["lifecycle"] = "removed"
    updated["tombstone"] = {
        "skillId": updated["skillId"],
        "removedRevision": removed_revision,
        "successorId": successor_id,
        "recordDigest": record_digest,
    }
    return updated


def _empty_snapshot() -> ProvenanceSnapshot:
    digest = hashlib.sha256(contracts.canonical_json_bytes([])).hexdigest()
    return ProvenanceSnapshot(digest, ())


def _validate_history(record: Mapping[str, Any]) -> None:
    history = record.get("history")
    source = record.get("source")
    if not isinstance(history, list) or not history or not isinstance(source, Mapping):
        raise ProvenanceValidationError("Provenance source history is missing")
    for index, event in enumerate(history, start=1):
        if not isinstance(event, Mapping) or event.get("sequence") != index:
            raise ProvenanceValidationError(
                "Provenance history sequence must be append-only and contiguous"
            )
    source_events = [
        item
        for item in history
        if isinstance(item, Mapping)
        and item.get("event") in {"created", "imported", "updated"}
    ]
    if not source_events:
        raise ProvenanceValidationError("Provenance source history is missing")
    latest = source_events[-1]
    if (
        latest.get("bundleDigest") != source.get("bundleDigest")
        or latest.get("commit") != source.get("commit")
    ):
        raise ProvenanceValidationError(
            "Provenance current source must match the latest history event"
        )


def _provenance_schema() -> Dict[str, Any]:
    return contracts.load_contract(
        Path(__file__).resolve().parents[3],
        contracts.CONTRACTS_ROOT / "provenance-v1.schema.json",
    )


def build_provenance_snapshot(
    records: Sequence[Mapping[str, Any]],
    record_bytes: Mapping[str, bytes],
    inventories: Sequence[bundles.BundleInventory],
    *,
    origin: str,
    root_name: str,
) -> ProvenanceSnapshot:
    """Validate future provenance records and exact serialized bytes in memory."""
    schema = _provenance_schema()
    inventory_by_id = {item.identifier: item for item in inventories}
    by_id = {str(item.get("skillId")): _thaw(item) for item in records}
    if len(by_id) != len(records):
        raise ProvenanceValidationError("Future provenance identifiers are duplicated")
    digest_rows = []
    for identifier in sorted(by_id):
        record = by_id[identifier]
        content = record_bytes.get(identifier)
        inventory = inventory_by_id.get(identifier)
        if content is None:
            raise ProvenanceValidationError(
                f"Future provenance input is incomplete: {identifier}"
            )
        parsed = contracts.load_contract_bytes(
            content, source=f"{root_name}/{identifier}.json"
        )
        if parsed != record:
            raise ProvenanceValidationError(
                f"Future provenance bytes disagree with record: {identifier}"
            )
        findings = contracts.validate_instance(record, schema)
        if findings:
            raise ProvenanceValidationError(
                f"Future provenance is invalid: {identifier}: {findings[0].code}"
            )
        _validate_history(record)
        source = record.get("source", {})
        if record.get("origin") != origin:
            raise ProvenanceValidationError(
                f"Future provenance identity or digest mismatch: {identifier}"
            )
        if inventory is None:
            if record.get("lifecycle") != "removed" or not isinstance(
                record.get("tombstone"), dict
            ):
                raise ProvenanceValidationError(
                    f"Only a removed tombstone may outlive its bundle: {identifier}"
                )
        elif source.get("bundleDigest") != inventory.digest:
            raise ProvenanceValidationError(
                f"Future provenance identity or digest mismatch: {identifier}"
            )
        digest_rows.append(
            {
                "path": f"{root_name}/{identifier}.json",
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return ProvenanceSnapshot(
        hashlib.sha256(contracts.canonical_json_bytes(digest_rows)).hexdigest(),
        tuple(_freeze(by_id[identifier]) for identifier in sorted(by_id)),
    )


def load_canonical_provenance_snapshot(
    source_root: Path,
    inventories: Sequence[bundles.BundleInventory],
) -> ProvenanceSnapshot:
    """Load optional committed plugin provenance without requiring legacy migration."""
    root = Path(source_root).resolve()
    directory = root / CANONICAL_PROVENANCE_ROOT
    try:
        metadata = os.lstat(str(directory))
    except FileNotFoundError:
        return _empty_snapshot()
    except OSError as error:
        raise ProvenanceValidationError(
            f"Cannot inspect {CANONICAL_PROVENANCE_ROOT} safely: {error}"
        ) from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise ProvenanceValidationError(
            f"{CANONICAL_PROVENANCE_ROOT} must be one real directory"
        )
    records = []
    record_bytes = {}
    with os.scandir(str(directory)) as entries:
        ordered = sorted(entries, key=lambda item: item.name)
    for entry in ordered:
        relative = f"{CANONICAL_PROVENANCE_ROOT}/{entry.name}"
        metadata = entry.stat(follow_symlinks=False)
        if (
            _is_link_or_reparse(metadata)
            or not stat.S_ISREG(metadata.st_mode)
            or not entry.name.endswith(".json")
        ):
            raise ProvenanceValidationError(
                f"Canonical provenance entry must be regular JSON: {relative}"
            )
        content = secure_fs.secure_read_bytes(
            root,
            PurePosixPath(relative),
            reject_hardlinks=True,
            max_bytes=contracts.MAX_CONTRACT_BYTES,
        )
        value = contracts.load_contract_bytes(content, source=relative)
        identifier = str(value.get("skillId", ""))
        if entry.name != f"{identifier}.json":
            raise ProvenanceValidationError(
                f"Canonical provenance filename must match skillId: {relative}"
            )
        records.append(value)
        record_bytes[identifier] = content
    return build_provenance_snapshot(
        records,
        record_bytes,
        inventories,
        origin="plugin-canonical",
        root_name=CANONICAL_PROVENANCE_ROOT,
    )


def load_provenance_snapshot(
    project_root: Path,
    project_records: Sequence[Mapping[str, Any]],
) -> ProvenanceSnapshot:
    """Load exact project provenance without following filesystem links.

    Args:
        project_root: Consumer project root.
        project_records: Validated project registry records.

    Returns:
        Immutable provenance snapshot.

    Raises:
        ProvenanceValidationError: If files, contracts, or identities disagree.

    Example:
        ``load_provenance_snapshot(project, registry_records)``
    """
    root = Path(project_root).resolve()
    expected = {
        str(record.get("provenanceId")): record
        for record in project_records
        if isinstance(record.get("provenanceId"), str)
    }
    directory = root / PROVENANCE_ROOT
    try:
        metadata = os.lstat(str(directory))
    except FileNotFoundError:
        if expected:
            raise ProvenanceValidationError(
                f"{PROVENANCE_ROOT} is missing for registered project skills."
            )
        return _empty_snapshot()
    except OSError as error:
        raise ProvenanceValidationError(
            f"Cannot inspect {PROVENANCE_ROOT} safely: {error}"
        ) from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise ProvenanceValidationError(
            f"{PROVENANCE_ROOT} must be one real directory, not a link or reparse point."
        )

    schema = contracts.load_contract(
        Path(__file__).resolve().parents[3],
        contracts.CONTRACTS_ROOT / "provenance-v1.schema.json",
    )
    loaded = []
    digest_rows = []
    seen_paths = {}
    try:
        with os.scandir(str(directory)) as entries:
            ordered = sorted(entries, key=lambda item: item.name)
    except OSError as error:
        raise ProvenanceValidationError(
            f"Cannot enumerate {PROVENANCE_ROOT} safely: {error}"
        ) from error
    for entry in ordered:
        relative = f"{PROVENANCE_ROOT}/{entry.name}"
        entry_metadata = entry.stat(follow_symlinks=False)
        if (
            _is_link_or_reparse(entry_metadata)
            or not stat.S_ISREG(entry_metadata.st_mode)
            or not entry.name.endswith(".json")
        ):
            raise ProvenanceValidationError(
                f"Provenance entry must be one regular JSON file: {relative}"
            )
        errors = path_policy.validate_repo_relative_path("provenance path", relative)
        if errors:
            raise ProvenanceValidationError("; ".join(errors))
        portable = path_policy.portable_path_key(relative)
        if portable in seen_paths:
            raise ProvenanceValidationError(
                f"Provenance paths collide portably: {seen_paths[portable]} and {relative}"
            )
        seen_paths[portable] = relative
        try:
            content = secure_fs.secure_read_bytes(
                root,
                PurePosixPath(relative),
                reject_hardlinks=True,
                max_bytes=contracts.MAX_CONTRACT_BYTES,
            )
            value = contracts.load_contract_bytes(content, source=relative)
        except (OSError, UnicodeError, ValueError) as error:
            raise ProvenanceValidationError(
                f"Cannot load provenance safely: {relative}: {error}"
            ) from error
        findings = contracts.validate_instance(value, schema)
        if findings:
            detail = "; ".join(
                f"{item.path}: {item.code}: {item.message}" for item in findings
            )
            raise ProvenanceValidationError(
                f"Project provenance is invalid: {relative}: {detail}"
            )
        identifier = value.get("skillId")
        if entry.name != f"{identifier}.json":
            raise ProvenanceValidationError(
                f"Provenance filename must match skillId: {relative}"
            )
        _validate_history(value)
        record = expected.get(str(identifier))
        if record is None and not (
            value.get("lifecycle") == "removed"
            and isinstance(value.get("tombstone"), dict)
        ):
            raise ProvenanceValidationError(
                f"Provenance has no project registry record: {relative}"
            )
        source = value.get("source", {})
        if record is not None and (
            value.get("origin") != record.get("origin")
            or value.get("admission") != record.get("admission")
            or value.get("lifecycle") != record.get("lifecycle")
            or source.get("bundleDigest") != record.get("bundleDigest")
        ):
            raise ProvenanceValidationError(
                f"Project provenance identity or digest disagrees with registry: {identifier}"
            )
        loaded.append(value)
        digest_rows.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    loaded_ids = {str(item.get("skillId")) for item in loaded}
    missing = sorted(set(expected) - loaded_ids)
    if missing:
        raise ProvenanceValidationError(
            "Project provenance is missing for: " + ", ".join(missing)
        )
    digest = hashlib.sha256(contracts.canonical_json_bytes(digest_rows)).hexdigest()
    return ProvenanceSnapshot(digest, tuple(_freeze(item) for item in loaded))
