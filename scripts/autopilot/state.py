"""Owned control state: marker acquisition, reservations, stage lifecycle.

The private coordination root lives under the absolute Git directory. The run
marker is acquired without replacement and only the matching owner may update
it. Checkpoint transactions and stage receipts live in ``checkpoint.py``.
"""

from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import Optional, Sequence

import secure_fs
from secure_fs import ExpectedFileState
from autopilot.contracts import (
    MAX_CHECKPOINT_BYTES,
    MAX_MARKER_BYTES,
    PacketError,
    StateError,
    _check_id,
    _check_sha,
    sha256_hex,
)
from autopilot.records import (
    RESERVATION_CAPS,
    MarkerState,
    Reservation,
    marker_to_bytes,
    parse_marker,
)

COORDINATION_DIR = "cg-autopilot"
MARKER_NAME = "marker.json"
SETTLEMENT_OUTCOMES = ("charged", "released-no-effect", "uncertain")
GIT_PROBE_TIMEOUT_SECONDS = 30


def resolve_coordination_root(root: Path) -> Path:
    """Resolve the private coordination root under the absolute Git directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        timeout=GIT_PROBE_TIMEOUT_SECONDS,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise StateError(
            "git-unavailable: the coordination root cannot be resolved outside "
            "a Git worktree."
        )
    return Path(result.stdout.strip()) / COORDINATION_DIR


def load_marker(coordination_root: Path) -> Optional[MarkerState]:
    """Load the marker with bounded secure reads; None when absent."""
    if not coordination_root.is_dir():
        return None
    try:
        raw = secure_fs.secure_read_bytes(
            coordination_root, PurePosixPath(MARKER_NAME), max_bytes=MAX_MARKER_BYTES
        )
    except FileNotFoundError:
        return None
    except secure_fs.SecureMutationError as error:
        raise StateError(f"marker cannot be read safely: {error}") from error
    try:
        return parse_marker(raw)
    except PacketError as error:
        raise StateError(f"malformed marker: {error.message}") from error


def write_marker(
    coordination_root: Path,
    marker: MarkerState,
    *,
    expected_state: ExpectedFileState,
) -> None:
    """Write the marker under an expected-byte or expected-absent state."""
    if not coordination_root.is_dir():
        coordination_root.mkdir(parents=True, exist_ok=True)
    raw = marker_to_bytes(marker)
    if len(raw) > MAX_MARKER_BYTES:
        raise StateError("marker-too-large: the marker exceeded 32768 bytes.")
    try:
        secure_fs.secure_write_bytes(
            coordination_root, PurePosixPath(MARKER_NAME), raw,
            expected_state=expected_state,
        )
    except secure_fs.SecureMutationError as error:
        raise StateError(f"marker write rejected: {error}") from error


def check_owner(marker: MarkerState, owner_nonce: str) -> None:
    """Never take over a marker owned by another run."""
    if marker.owner_nonce != owner_nonce:
        raise StateError(
            "foreign-owner: the run marker belongs to another owner; acquire "
            "cooperative ownership without replacement, never by takeover."
        )


def acquire_marker(
    root: Path,
    coordination_root: Path,
    *,
    run_id: str,
    owner_nonce: str,
    worktree: str,
    branch: str,
    plan_digest: str,
    required_base: str,
) -> MarkerState:
    """Acquire an owned run marker exactly once, without replacement."""
    _check_id(run_id, "run-id")
    _check_id(owner_nonce, "owner-nonce")
    _check_sha(plan_digest, "plan-digest")
    marker = MarkerState(
        1, run_id, owner_nonce, 0, str(worktree), branch, plan_digest,
        required_base, None, None, (), (), None, None,
    )
    try:
        write_marker(coordination_root, marker, expected_state=ExpectedFileState.absent())
    except StateError as error:
        existing = load_marker(coordination_root)
        raise StateError(
            "marker-exists: the coordination area already holds run "
            f"{existing.run_id if existing else '?'} at revision "
            f"{existing.revision if existing else '?'}; reservations are never "
            "erased by starting a fresh run."
        ) from error
    return marker


def reserve(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    scope: str,
    key: str,
    reservation_id: str,
) -> MarkerState:
    """Reserve one attempt before mutation; released yields consume no round."""
    check_owner(marker, owner_nonce)
    if scope not in RESERVATION_CAPS:
        raise StateError(f"unknown reservation scope {scope!r}.")
    if any(r.reservation_id == reservation_id for r in marker.reservations):
        raise StateError(
            f"reservation-exists: {reservation_id!r} was already reserved; "
            "reservation IDs are deduplicated, never replayed as new attempts."
        )
    matching = [r for r in marker.reservations if r.scope == scope and r.key == key]
    charged = [r for r in matching if r.status != "released-no-effect"]
    if len(charged) >= RESERVATION_CAPS[scope]:
        raise StateError(
            f"reservation-exhausted: {scope} for {key!r} is limited to "
            f"{RESERVATION_CAPS[scope]} charged attempts; proven zero-effect "
            "releases do not consume rounds."
        )
    reservation = Reservation(
        reservation_id, None, scope, key, len(charged) + 1, "pending", None, ()
    )
    updated = replace(marker, reservations=marker.reservations + (reservation,))
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    return updated


def begin_stage(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    operation_id: str,
    reservation_id: str,
) -> MarkerState:
    """Parent-only: bind one reserved attempt and mark the stage in flight."""
    check_owner(marker, owner_nonce)
    if marker.in_flight_operation not in (None, operation_id):
        raise StateError(
            "stage-in-flight: another stage operation is still in flight; settle "
            "it before beginning a new one."
        )
    reservation = next(
        (r for r in marker.reservations if r.reservation_id == reservation_id), None
    )
    if reservation is None:
        raise StateError(
            f"missing-reservation: {reservation_id!r} must be reserved before "
            "the stage begins."
        )
    if reservation.status != "pending":
        raise StateError(
            f"reservation-status: {reservation_id!r} is {reservation.status!r}, "
            "not 'pending'; a charged, released or uncertain reservation can "
            "never be rebound to a new stage operation."
        )
    reservations = tuple(
        replace(r, operation_id=operation_id)
        if r.reservation_id == reservation_id else r
        for r in marker.reservations
    )
    updated = replace(marker, in_flight_operation=operation_id, reservations=reservations)
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    return updated


def settle_stage(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    operation_id: str,
    outcome: str,
    evidence_refs: Sequence[str] = (),
) -> MarkerState:
    """Parent-only settlement: charged, uncertain or proven zero-effect release."""
    check_owner(marker, owner_nonce)
    if outcome not in SETTLEMENT_OUTCOMES:
        raise StateError(f"unknown settlement outcome {outcome!r}.")
    reservation = next(
        (r for r in marker.reservations if r.operation_id == operation_id), None
    )
    if reservation is None:
        raise StateError("missing-reservation: the stage carries no reservation.")
    if outcome == "released-no-effect":
        if not evidence_refs:
            raise StateError(
                "missing-zero-effect-evidence: released-no-effect requires the "
                "parent's independent zero-effect verification evidence."
            )
        if reservation.status in ("charged", "uncertain"):
            raise StateError(
                "reservation-charged: partial or uncertain effects can never be "
                "refunded as released-no-effect."
            )
        if reservation.status == "released-no-effect":
            return marker
    elif reservation.status == "released-no-effect":
        raise StateError("reservation-charged: a released reservation cannot charge.")
    if marker.in_flight_operation != operation_id:
        raise StateError(
            "operation-not-in-flight: only the in-flight stage can be settled."
        )
    reservations = tuple(
        replace(r, status=outcome, evidence=tuple(evidence_refs))
        if r.reservation_id == reservation.reservation_id else r
        for r in marker.reservations
    )
    updated = replace(marker, in_flight_operation=None, reservations=reservations)
    write_marker(
        coordination_root, updated,
        expected_state=ExpectedFileState.from_bytes(marker_to_bytes(marker)),
    )
    return updated


def read_checkpoint_bytes(cursor_path: Path) -> bytes:
    """Read current cursor bytes within the checkpoint limit."""
    try:
        raw = secure_fs.secure_read_bytes(
            cursor_path.parent,
            PurePosixPath(cursor_path.name),
            max_bytes=MAX_CHECKPOINT_BYTES,
        )
    except FileNotFoundError as error:
        raise StateError("cursor-absent: the checkpoint file does not exist.") from error
    except secure_fs.SecureMutationError as error:
        raise StateError(f"checkpoint-too-large: {error}") from error
    return raw


# Marker/cursor records live in records.py; checkpoint transactions live in
# checkpoint.py. Both are imported directly by callers: the import graph is a
# DAG (contracts -> packets/records -> state -> checkpoint -> recovery) and no
# module re-exports another module's definitions.
