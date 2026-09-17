"""Interrupted-run reconciliation and idempotent checkpoint recovery.

Recovery never removes another owner's files. Quarantined, foreign, unknown or
diverged bytes block with exact diagnostics; the only completed recovery paths
re-publish the exact target or acknowledge it idempotently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Callable, Optional, Sequence, Tuple

import secure_fs
from secure_fs import ExpectedFileState
from autopilot.checkpoint import acknowledge_checkpoint, result_receipt_exists
from autopilot.contracts import (
    MAX_CHECKPOINT_BYTES,
    RecoveryBlocked,
    StateError,
    _check_id,
    _check_string,
    sha256_hex,
)
from autopilot.records import (
    MarkerState,
    marker_to_bytes,
    validate_cursor_record,
    validate_deadline_dict,
)
from autopilot.state import (
    check_owner,
    load_marker,
    write_marker,
)

_QUARANTINE_SUFFIX_RE = re.compile(r"\.(previous|stale|tmp)$")
_STATES = ("fresh", "noop-complete", "redo-publish", "redo-acknowledge", "blocked")

MAX_EXTENSION_SECONDS = 7 * 24 * 60 * 60
CLOCK_TOLERANCE_SECONDS = 60

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class Reconciliation:
    """One read-only reconciliation decision with exact diagnostics."""

    status: str
    reason: Optional[str]
    diagnostics: Tuple[str, ...]
    marker: Optional[MarkerState]


def find_quarantined(coordination_root: Path, cursor_path: Path) -> Tuple[str, ...]:
    """Detect leftover quarantine publications without touching them."""
    found: list[str] = []
    if coordination_root.is_dir():
        for path in sorted(coordination_root.rglob("*")):
            if path.is_file() and _QUARANTINE_SUFFIX_RE.search(path.name):
                found.append(str(path))
    if cursor_path.parent.is_dir():
        prefix = f".{cursor_path.name}."
        for path in sorted(cursor_path.parent.glob(f"{prefix}*")):
            if path.is_file() and _QUARANTINE_SUFFIX_RE.search(path.name):
                found.append(str(path))
    return tuple(found)


def _cursor_bytes(cursor_path: Path) -> Optional[bytes]:
    try:
        return secure_fs.secure_read_bytes(
            cursor_path.parent,
            PurePosixPath(cursor_path.name),
            max_bytes=MAX_CHECKPOINT_BYTES,
        )
    except FileNotFoundError:
        return None
    except secure_fs.SecureMutationError:
        return None


def reconcile(
    root: Path,
    coordination_root: Path,
    cursor_path: Path,
    *,
    owner_nonce: Optional[str] = None,
) -> Reconciliation:
    """Classify current marker/cursor state without any mutation.

    Diagnostics name exact paths, digests and operation identities; they never
    include file bodies, secrets or another owner's files removed.
    """
    quarantined = find_quarantined(coordination_root, cursor_path)
    if quarantined:
        return Reconciliation(
            "blocked",
            "quarantined-state",
            tuple(f"quarantine publication present and preserved: {p}" for p in quarantined),
            None,
        )
    marker = load_marker(coordination_root)
    cursor = _cursor_bytes(cursor_path)
    if marker is None:
        if cursor is not None:
            return Reconciliation(
                "blocked",
                "orphan-cursor",
                (f"cursor exists without a marker: {cursor_path} "
                 f"({sha256_hex(cursor)}); it is preserved and never deleted.",),
                None,
            )
        return Reconciliation("fresh", None, (), None)
    if owner_nonce is not None and marker.owner_nonce != owner_nonce:
        return Reconciliation(
            "blocked",
            "foreign-owner",
            ("the marker belongs to another owner; takeover is never attempted.",),
            marker,
        )
    if marker.transaction is not None:
        if marker.in_flight_operation is not None and result_receipt_exists(
            coordination_root, marker.in_flight_operation
        ) is None:
            return Reconciliation(
                "blocked",
                "unsettled-operation",
                (f"operation {marker.in_flight_operation} is in flight without a "
                 "recorded result; settle it before checkpoint recovery.",),
                marker,
            )
        if cursor is None:
            return Reconciliation(
                "blocked",
                "cursor-absent",
                ("a checkpoint transaction is open but the cursor is absent.",),
                marker,
            )
        digest = sha256_hex(cursor)
        if digest == marker.transaction.target_checkpoint_digest:
            return Reconciliation("redo-acknowledge", None, (), marker)
        if digest == marker.transaction.old_checkpoint_digest:
            return Reconciliation("redo-publish", None, (), marker)
        return Reconciliation(
            "blocked",
            "checkpoint-diverged",
            (f"cursor digest {digest} matches neither the recorded old "
             f"({marker.transaction.old_checkpoint_digest}) nor target "
             f"({marker.transaction.target_checkpoint_digest}) checkpoint; "
             "the foreign bytes are preserved.",),
            marker,
        )
    if marker.in_flight_operation is not None:
        if result_receipt_exists(coordination_root, marker.in_flight_operation):
            return Reconciliation(
                "blocked",
                "unacknowledged-result",
                (f"operation {marker.in_flight_operation} recorded a result but "
                 "no checkpoint acknowledged it; validate before continuing.",),
                marker,
            )
        effect = next(
            (r for r in marker.receipts if r.operation_id == marker.in_flight_operation
             and r.kind == "effect-start"),
            None,
        )
        return Reconciliation(
            "blocked",
            "interrupted-effect",
            (f"operation {marker.in_flight_operation} was interrupted without a "
             f"recorded result"
             + (f"; its one-way effect receipt is {effect.sha256}." if effect else "."),),
            marker,
        )
    if cursor is None:
        return Reconciliation(
            "blocked",
            "cursor-absent",
            (f"marker revision {marker.revision} exists but the cursor file "
             f"{cursor_path} is absent.",),
            marker,
        )
    try:
        payload = validate_cursor_record(cursor)
    except Exception as error:
        return Reconciliation(
            "blocked",
            "cursor-invalid",
            (f"cursor bytes do not form a valid checkpoint: {error}",),
            marker,
        )
    section = payload["autopilot"]
    if section["run-id"] == marker.run_id and section["revision"] == marker.revision:
        if marker.cursor_digest is not None and sha256_hex(cursor) != marker.cursor_digest:
            return Reconciliation(
                "blocked",
                "checkpoint-diverged",
                (f"cursor digest {sha256_hex(cursor)} does not match the "
                 f"marker-bound checkpoint digest {marker.cursor_digest}; the "
                 "cursor bytes were tampered with or directly overwritten after "
                 "acknowledgement and are preserved.",),
                marker,
            )
        return Reconciliation("noop-complete", None, (), marker)
    return Reconciliation(
        "blocked",
        "revision-diverged",
        (f"cursor names run {section['run-id']} revision {section['revision']} "
         f"but the marker owns run {marker.run_id} revision {marker.revision}; "
         "a direct cursor write or competing owner is present.",),
        marker,
    )


def finish_checkpoint(
    root: Path,
    coordination_root: Path,
    cursor_path: Path,
    *,
    owner_nonce: str,
    transaction_id: str,
    payload: Optional[bytes] = None,
) -> MarkerState:
    """Complete an interrupted checkpoint exactly, or block without effects.

    With the old cursor present the exact target payload must be supplied and
    is republished over the expected old bytes. With the target present the
    acknowledgement is applied idempotently. Any other state blocks.
    """
    reconciliation = reconcile(
        root, coordination_root, cursor_path, owner_nonce=owner_nonce
    )
    marker = reconciliation.marker
    if reconciliation.status == "noop-complete":
        assert marker is not None
        return marker
    if marker is None or marker.transaction is None:
        raise RecoveryBlocked(
            f"recovery blocked ({reconciliation.reason or reconciliation.status}); "
            "no checkpoint transaction is open."
        )
    if marker.transaction.transaction_id != transaction_id:
        raise RecoveryBlocked(
            f"recovery blocked: transaction {marker.transaction.transaction_id} "
            f"is open, not {transaction_id}."
        )
    if reconciliation.status == "redo-acknowledge":
        if payload is not None and sha256_hex(payload) != (
            marker.transaction.target_checkpoint_digest
        ):
            raise RecoveryBlocked(
                "recovery blocked: the supplied payload does not match the "
                "recorded target checkpoint."
            )
        return acknowledge_checkpoint(
            marker, coordination_root,
            expected_marker_bytes=marker_to_bytes(marker),
        )
    if reconciliation.status == "redo-publish":
        if payload is None:
            raise RecoveryBlocked(
                "recovery blocked: the old checkpoint is still present and the "
                "exact target payload must be supplied again."
            )
        if sha256_hex(payload) != marker.transaction.target_checkpoint_digest:
            raise RecoveryBlocked(
                "recovery blocked: the supplied payload does not match the "
                "recorded target checkpoint digest."
            )
        old_bytes = _cursor_bytes(cursor_path)
        if old_bytes is None or sha256_hex(old_bytes) != (
            marker.transaction.old_checkpoint_digest
        ):
            raise RecoveryBlocked(
                "recovery blocked: the cursor changed since reconciliation."
            )
        try:
            secure_fs.secure_write_bytes(
                cursor_path.parent,
                PurePosixPath(cursor_path.name),
                payload,
                expected_state=ExpectedFileState.from_bytes(old_bytes),
            )
        except secure_fs.SecureMutationError as error:
            raise RecoveryBlocked(
                f"recovery blocked: cursor publication rejected: {error}"
            ) from error
        readback = _cursor_bytes(cursor_path)
        if readback is None or sha256_hex(readback) != (
            marker.transaction.target_checkpoint_digest
        ):
            raise RecoveryBlocked(
                "recovery blocked: the published cursor failed read-back."
            )
        return acknowledge_checkpoint(
            marker, coordination_root,
            expected_marker_bytes=marker_to_bytes(marker),
        )
    raise RecoveryBlocked(
        f"recovery blocked ({reconciliation.reason or reconciliation.status}); "
        "recovery files are preserved."
    )


# ---------------------------------------------------------------------------
# Parent-only CI deadline observation and approved extension (Step 11)
# ---------------------------------------------------------------------------


def _as_utc(value: str, label: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise StateError(f"{label} must be an ISO-8601 UTC timestamp.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StateError(
            f"{label} must be a timezone-aware ISO-8601 UTC timestamp; naive "
            "wall-clock values are never trusted for deadline math."
        )
    return parsed


def _shift(value: str, seconds: int) -> str:
    moved = _as_utc(value, "timestamp") + timedelta(seconds=seconds)
    return moved.isoformat().replace("+00:00", "Z")


def record_ci_deadline(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    original_deadline: str,
    scope_hash: str,
) -> MarkerState:
    """Record the immutable original CI observation deadline in the marker."""
    check_owner(marker, owner_nonce)
    if marker.deadline is not None:
        if marker.deadline.get("scope-hash") != scope_hash:
            raise StateError(
                "deadline-scope-changed: the recorded observation belongs to a "
                "different scope; a new decision is required, never silent "
                "rebasing of the deadline."
            )
        return marker
    _as_utc(original_deadline, "original-deadline")
    deadline = {
        "schema-version": 1,
        "original-deadline": original_deadline,
        "effective-deadline": original_deadline,
        "request-id": None,
        "approval-ref": None,
        "scope-hash": scope_hash,
        "history": [],
    }
    validate_deadline_dict(deadline, "deadline")
    updated = replace(marker, deadline=deadline)
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    return updated


def extend_ci_deadline(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    request_id: str,
    duration_seconds: int,
    approval_ref: str,
    scope_hash: str,
    application_time: str,
    clock: Optional[Clock] = None,
) -> MarkerState:
    """Apply one explicitly approved extension; only waiting time changes.

    Replay of the same request ID returns the stored deadline without adding
    time. Changed scope, a missing original observation, a missing or unsettled
    writer and a clock that would move the deadline backwards all block. Repair
    slots, reservations, reruns and other usage counters are never reset.
    """
    check_owner(marker, owner_nonce)
    _check_id(request_id, "request-id")
    if not isinstance(duration_seconds, int) or duration_seconds < 1:
        raise StateError("duration must be a positive integer number of seconds.")
    if duration_seconds > MAX_EXTENSION_SECONDS:
        raise StateError(
            f"duration must not exceed {MAX_EXTENSION_SECONDS} seconds "
            f"({MAX_EXTENSION_SECONDS // 86400} days); longer waits require a "
            "new decision."
        )
    approval_ref = _check_string(approval_ref, "approval-ref", max_bytes=512)
    if marker.in_flight_operation is not None:
        raise StateError(
            "writer-in-flight: the effective deadline cannot change while a "
            "stage operation is active or unsettled."
        )
    if marker.deadline is None:
        raise StateError(
            "no-observation: an original CI deadline has not been recorded; "
            "extension requires the prior observation."
        )
    deadline = validate_deadline_dict(marker.deadline, "deadline")
    assert deadline is not None
    if deadline.get("request-id") == request_id:
        return marker
    if deadline.get("scope-hash") != scope_hash:
        raise StateError(
            "deadline-scope-changed: a changed scope requires a new decision, "
            "never silent rebasing of the deadline."
        )
    original = deadline["original-deadline"]
    current = deadline.get("effective-deadline", original)
    _as_utc(application_time, "application-time")
    if clock is not None:
        now = clock()
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() is None
        ):
            raise StateError(
                "clock-untrusted: the injected clock must return a timezone-aware "
                "datetime; the application time is never taken from raw caller "
                "input alone."
            )
        drift = now - _as_utc(application_time, "application-time")
        if abs(drift.total_seconds()) > CLOCK_TOLERANCE_SECONDS:
            raise StateError(
                "clock-mismatch: the supplied application time differs from the "
                f"trusted clock by more than {CLOCK_TOLERANCE_SECONDS} seconds; "
                "a new decision is required."
            )
    try:
        new_deadline = _shift(application_time, duration_seconds)
    except OverflowError as error:
        raise StateError(
            "deadline-overflow: the proposed deadline exceeds the supported "
            "datetime range; a new decision is required."
        ) from error
    if _as_utc(new_deadline, "new-deadline") <= _as_utc(current, "effective-deadline"):
        raise StateError(
            "clock-rollback: the proposed deadline is not later than the current "
            "effective deadline; a new decision is required."
        )
    history = list(deadline.get("history", []))
    entry = {
        "request-id": request_id,
        "approval-ref": approval_ref,
        "duration-seconds": duration_seconds,
        "application-time": application_time,
        "old-deadline": current,
        "new-deadline": new_deadline,
    }
    built = {
        "schema-version": 1,
        "original-deadline": original,
        "effective-deadline": new_deadline,
        "request-id": request_id,
        "approval-ref": approval_ref,
        "scope-hash": scope_hash,
        "history": history + [entry],
    }
    validate_deadline_dict(built, "deadline")
    updated = replace(marker, deadline=built)
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    return updated
