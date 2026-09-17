"""Checkpoint protocol: stage receipts and expected-byte cursor transactions.

Stage operations hold rights to their own effect/result receipts only. The
versioned cursor changes exclusively through the parent's three-step
expected-byte checkpoint protocol documented in
``.github/shared/autopilot-stage.contract.md``.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import Any, Optional, Sequence

import secure_fs
from secure_fs import ExpectedFileState
from autopilot.contracts import (
    MAX_CHECKPOINT_BYTES,
    StateError,
    _check_id,
    sha256_hex,
)
from autopilot.records import (
    MarkerState,
    ReceiptRecord,
    TransactionIntent,
    marker_to_bytes,
    validate_cursor_record,
)
from autopilot.state import check_owner, read_checkpoint_bytes, write_marker


def build_cursor_record(
    *,
    run_id: str,
    revision: int,
    worktree: str,
    branch: str,
    required_base: str,
    plan_digest: str,
    next_action: str,
    updated_at: str,
    installed_command_digest: Optional[str] = None,
    installed_contract_digest: Optional[str] = None,
    batch_pointer: Optional[dict] = None,
    stage_pointer: Optional[dict] = None,
    artifact_refs: Sequence[dict] = (),
    folded_attempt_ids: Sequence[str] = (),
    status: str = "active",
    plan: Optional[str] = None,
    execution_report: Optional[str] = None,
    current_phase: Optional[int] = None,
) -> bytes:
    """Build one closed checkpoint payload and return exact JSON bytes."""
    payload: dict[str, Any] = {
        "schemaVersion": "compound-gpid-active-state-v1",
        "updatedAt": updated_at,
        "workflow": "/cg-autopilot",
        "status": status,
        "branch": branch,
        "plan": plan,
        "executionReport": execution_report,
        "currentPhase": current_phase,
        "evidenceStatus": [],
        "unresolvedDecisions": [],
        "artifactRefs": [],
        "nextCommand": "/cg-autopilot --resume .cg-docs/active-state/current.json",
        "autopilot": {
            "schema-version": 1, "run-id": run_id, "revision": revision,
            "worktree": worktree, "branch": branch,
            "required-base": required_base,
            "plan-execution-digest": plan_digest,
            "installed-command-digest": installed_command_digest,
            "installed-contract-digest": installed_contract_digest,
            "batch-pointer": batch_pointer, "stage-pointer": stage_pointer,
            "artifact-refs": list(artifact_refs),
            "folded-attempt-ids": list(folded_attempt_ids),
            "next-action": next_action,
        },
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    validate_cursor_record(raw)
    return raw


def begin_effect(
    coordination_root: Path, operation_id: str, *, recorded_at: str
) -> str:
    """Stage-only one-way effect receipt persisted before the first effect."""
    _check_id(operation_id, "operation-id")
    if not coordination_root.is_dir():
        coordination_root.mkdir(parents=True, exist_ok=True)
    relative = PurePosixPath(f"operations/{operation_id}/effect.json")
    payload = {
        "schema-version": 1, "kind": "effect-start",
        "operation-id": operation_id, "recorded-at": recorded_at, "one-way": True,
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    try:
        secure_fs.secure_write_bytes(
            coordination_root, relative, raw, expected_state=ExpectedFileState.absent()
        )
    except secure_fs.SecureMutationError as error:
        raise StateError(
            "effect-already-started: the effect receipt is one-way and cannot "
            "be cleared or replaced."
        ) from error
    return sha256_hex(raw)


def record_result(
    coordination_root: Path, operation_id: str, result_bytes: bytes
) -> ReceiptRecord:
    """Stage-only: validate a closed result packet and persist its receipt."""
    from autopilot.packets import StageResult

    _check_id(operation_id, "operation-id")
    result = StageResult.parse(result_bytes)
    if result.operation_id != operation_id:
        raise StateError(
            "operation-mismatch: the result packet names "
            f"{result.operation_id!r}, not this operation {operation_id!r}."
        )
    if not coordination_root.is_dir():
        coordination_root.mkdir(parents=True, exist_ok=True)
    relative = PurePosixPath(f"operations/{operation_id}/result.json")
    digest = sha256_hex(result_bytes)
    try:
        existing = secure_fs.secure_read_bytes(
            coordination_root, relative, max_bytes=MAX_CHECKPOINT_BYTES
        )
    except FileNotFoundError:
        existing = None
    except secure_fs.SecureMutationError as error:
        raise StateError(f"result receipt unreadable: {error}") from error
    if existing is not None:
        if sha256_hex(existing) == digest:
            return ReceiptRecord(operation_id, "result", digest)
        raise StateError(
            "receipt-conflict: the operation already recorded different result bytes."
        )
    try:
        secure_fs.secure_write_bytes(
            coordination_root, relative, result_bytes,
            expected_state=ExpectedFileState.absent(),
        )
    except secure_fs.SecureMutationError as error:
        raise StateError(f"result receipt write rejected: {error}") from error
    return ReceiptRecord(operation_id, "result", digest)


def bind_initial_cursor(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    cursor_bytes: bytes,
) -> MarkerState:
    """Parent-only: bind the initial reference checkpoint digest at prepare."""
    check_owner(marker, owner_nonce)
    section = validate_cursor_record(cursor_bytes)["autopilot"]
    if section["run-id"] != marker.run_id:
        raise StateError("cursor-run-mismatch: the cursor names a different run.")
    if section["revision"] != marker.revision:
        raise StateError(
            f"cursor-revision: the initial checkpoint must be revision "
            f"{marker.revision}, got {section['revision']}."
        )
    if marker.cursor_digest is not None:
        raise StateError("cursor-already-bound: the cursor digest binds once.")
    updated = replace(marker, cursor_digest=sha256_hex(cursor_bytes))
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    return updated


def acknowledge_checkpoint(
    marker: MarkerState, coordination_root: Path, *, expected_marker_bytes: bytes
) -> MarkerState:
    """Idempotently fold exact reservations and retire the transaction intent."""
    assert marker.transaction is not None
    revision = marker.revision + 1
    reservations = tuple(
        replace(
            r, folded_revision=revision if r.folded_revision is None else r.folded_revision
        )
        if r.reservation_id in marker.transaction.fold_reservation_ids else r
        for r in marker.reservations
    )
    updated = replace(
        marker, revision=revision,
        cursor_digest=marker.transaction.target_checkpoint_digest,
        transaction=None, reservations=reservations,
    )
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(expected_marker_bytes),
    )
    return updated


def checkpoint(
    marker: MarkerState,
    coordination_root: Path,
    cursor_path: Path,
    payload: bytes,
    *,
    owner_nonce: str,
    fold_reservation_ids: Sequence[str],
    transaction_id: str,
    before_publish: Any = None,
) -> MarkerState:
    """Parent-only three-step expected-byte checkpoint protocol.

    1. Marker intent records transaction ID, old/target digests and the exact
    reservations to fold. 2. The cursor is published only over the expected
    previous bytes, then read back to verify the target digest. 3. The marker
    acknowledges the target and folds exactly those reservations.
    """
    check_owner(marker, owner_nonce)
    if marker.transaction is not None:
        raise StateError(
            "transaction-in-progress: a checkpoint transaction is already open; "
            "reconcile before starting a new one."
        )
    if marker.in_flight_operation is not None:
        raise StateError(
            "unsettled-operation: the in-flight stage must be settled (cleared "
            "from the marker) and its result recorded before a checkpoint; "
            "settlement precedes every checkpoint acknowledgement."
        )
    section = validate_cursor_record(payload)["autopilot"]
    if section["run-id"] != marker.run_id:
        raise StateError("cursor-run-mismatch: the cursor names a different run.")
    if section["revision"] != marker.revision + 1:
        raise StateError(
            f"cursor-revision: expected revision {marker.revision + 1}, got "
            f"{section['revision']}."
        )
    for reservation_id in fold_reservation_ids:
        reservation = next(
            (r for r in marker.reservations if r.reservation_id == reservation_id), None
        )
        if reservation is None:
            raise StateError(f"unknown-reservation: {reservation_id!r}.")
        if reservation.status == "released-no-effect":
            raise StateError(
                f"released-reservation-not-foldable: {reservation_id!r} was "
                "released with zero effect and never enters a checkpoint."
            )
    old_bytes = read_checkpoint_bytes(cursor_path)
    old_digest = sha256_hex(old_bytes)
    if marker.cursor_digest is not None and old_digest != marker.cursor_digest:
        raise StateError(
            "cursor-changed: the cursor bytes no longer match the marker-bound "
            "checkpoint digest; a direct or competing write is present and the "
            "foreign bytes are preserved."
        )
    target_digest = sha256_hex(payload)
    intent = TransactionIntent(
        transaction_id, old_digest, target_digest, tuple(fold_reservation_ids)
    )
    intent_marker = replace(marker, transaction=intent)
    write_marker(
        coordination_root, intent_marker,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    try:
        secure_fs.secure_write_bytes(
            cursor_path.parent,
            PurePosixPath(cursor_path.name),
            payload,
            expected_state=ExpectedFileState.from_bytes(old_bytes),
            before_replace=before_publish,
        )
    except secure_fs.SecureMutationError as error:
        raise StateError(
            f"cursor-changed: checkpoint publication rejected: {error}"
        ) from error
    if sha256_hex(read_checkpoint_bytes(cursor_path)) != target_digest:
        raise StateError(
            "checkpoint-readback-failed: the published cursor no longer matches "
            "the target digest."
        )
    return acknowledge_checkpoint(
        intent_marker, coordination_root,
        expected_marker_bytes=marker_to_bytes(intent_marker),
    )


def result_receipt_exists(coordination_root: Path, operation_id: str) -> Optional[str]:
    """Return the recorded result receipt digest for an operation, if present."""
    relative = PurePosixPath(f"operations/{operation_id}/result.json")
    try:
        raw = secure_fs.secure_read_bytes(
            coordination_root, relative, max_bytes=MAX_CHECKPOINT_BYTES
        )
    except (FileNotFoundError, secure_fs.SecureMutationError):
        return None
    return sha256_hex(raw)
