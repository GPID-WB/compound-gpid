"""Closed control-state records: marker packets and versioned cursor records.

Durable marker/checkpoint packet shapes, separated from the transactions.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional, Tuple, Sequence

from autopilot.contracts import (
    ARTIFACT_KINDS,
    MAX_CHECKPOINT_BYTES,
    MAX_MARKER_BYTES,
    PacketError,
    STAGES,
    StateError,
    _check_id,
    _check_int,
    _check_list,
    _check_path,
    _check_sha,
    _check_string,
    parse_closed_json,
    parse_object,
)

RESERVATION_CAPS = {"review-round": 2, "ci-round": 2}
RESERVATION_STATUSES = ("pending", "charged", "released-no-effect", "uncertain")
CURSOR_STATUSES = ("active", "blocked", "completed", "handoff")
DEADLINE_SCHEMA_VERSION = 1
DEADLINE_MAX_HISTORY = 32

_UPDATED_AT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


def _validate_deadline(value: Any, path: str) -> Optional[dict]:
    """Closed-validate one marker deadline dict; shared by parse and write paths.

    Every key is typed and the schema version is enforced, so writers and
    readers can never disagree about the shape and ``extend_ci_deadline`` can
    index required keys without ``KeyError`` leaks.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise PacketError(f"{path} must be null or a closed deadline object.")
    data = parse_object(value, path, "CI deadline", (
        ("schema-version", _check_int, {}),
        ("original-deadline", _check_string, {"max_bytes": 64}),
        ("effective-deadline", _check_string, {"max_bytes": 64}),
        ("request-id", _check_id, {"nullable": True}),
        ("approval-ref", _check_string, {"max_bytes": 512, "nullable": True}),
        ("scope-hash", _check_sha, {}),
        ("history", _check_list, {"max_items": DEADLINE_MAX_HISTORY}),
    ))
    if data["schema-version"] != DEADLINE_SCHEMA_VERSION:
        raise PacketError(
            f"{path}.schema-version enum must be exactly {DEADLINE_SCHEMA_VERSION}."
        )
    for index, item in enumerate(data["history"]):
        sub = f"{path}.history[{index}]"
        entry = parse_object(item, sub, "deadline history entry", (
            ("request-id", _check_id, {}),
            ("approval-ref", _check_string, {"max_bytes": 512}),
            ("duration-seconds", _check_int, {"minimum": 1}),
            ("application-time", _check_string, {"max_bytes": 64}),
            ("old-deadline", _check_string, {"max_bytes": 64}),
            ("new-deadline", _check_string, {"max_bytes": 64}),
        ))
        data["history"][index] = entry
    return data


validate_deadline_dict = _validate_deadline


@dataclass(frozen=True)
class Reservation:
    """One reserved repair attempt with its durable settlement status."""

    reservation_id: str
    operation_id: Optional[str]
    scope: str
    key: str
    attempt: int
    status: str
    folded_revision: Optional[int]
    evidence: Tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "reservation-id": self.reservation_id, "operation-id": self.operation_id,
            "scope": self.scope, "key": self.key, "attempt": self.attempt,
            "status": self.status, "folded-revision": self.folded_revision,
            "evidence": list(self.evidence),
        }

    @classmethod
    def from_dict(cls, value: Any, path: str) -> "Reservation":
        data = parse_object(value, path, "reservation", (
            ("reservation-id", _check_id, {}),
            ("operation-id", _check_id, {"nullable": True}),
            ("scope", _check_string, {"max_bytes": 32}),
            ("key", _check_string, {"max_bytes": 512}),
            ("attempt", _check_int, {"minimum": 1}),
            ("status", _check_string, {"max_bytes": 32}),
            ("folded-revision", _check_int, {"nullable": True}),
            ("evidence", _check_list, {"max_items": 16}),
        ))
        if data["scope"] not in RESERVATION_CAPS:
            raise PacketError(f"{path}.scope must be one of {tuple(RESERVATION_CAPS)}.")
        if data["status"] not in RESERVATION_STATUSES:
            raise PacketError(f"{path}.status must be one of {RESERVATION_STATUSES}.")
        for index, item in enumerate(data["evidence"]):
            _check_string(item, f"{path}.evidence[{index}]")
        return cls(
            data["reservation-id"], data["operation-id"], data["scope"],
            data["key"], data["attempt"], data["status"],
            data["folded-revision"], tuple(data["evidence"]),
        )


@dataclass(frozen=True)
class ReceiptRecord:
    """One persisted receipt identity: effect-start or result."""
    operation_id: str
    kind: str
    sha256: str

    def as_dict(self) -> dict:
        return {"operation-id": self.operation_id, "kind": self.kind,
                "sha256": self.sha256}

    @classmethod
    def from_dict(cls, value: Any, path: str) -> "ReceiptRecord":
        data = parse_object(value, path, "receipt", (
            ("operation-id", _check_id, {}),
            ("kind", _check_string, {"max_bytes": 16}),
            ("sha256", _check_sha, {}),
        ))
        if data["kind"] not in ("effect-start", "result"):
            raise PacketError(f"{path}.kind must be effect-start or result.")
        return cls(**data)


@dataclass(frozen=True)
class TransactionIntent:
    """Expected-byte checkpoint intent: old, target and reservations to fold."""
    transaction_id: str
    old_checkpoint_digest: str
    target_checkpoint_digest: str
    fold_reservation_ids: Tuple[str, ...]

    def as_dict(self) -> dict:
        return {
            "transaction-id": self.transaction_id,
            "old-checkpoint-digest": self.old_checkpoint_digest,
            "target-checkpoint-digest": self.target_checkpoint_digest,
            "fold-reservation-ids": list(self.fold_reservation_ids),
        }

    @classmethod
    def from_dict(cls, value: Any, path: str) -> "TransactionIntent":
        data = parse_object(value, path, "transaction intent", (
            ("transaction-id", _check_id, {}),
            ("old-checkpoint-digest", _check_sha, {}),
            ("target-checkpoint-digest", _check_sha, {}),
            ("fold-reservation-ids", _check_list, {"max_items": 32}),
        ))
        for index, item in enumerate(data["fold-reservation-ids"]):
            _check_id(item, f"{path}.fold-reservation-ids[{index}]")
        return cls(
            data["transaction-id"], data["old-checkpoint-digest"],
            data["target-checkpoint-digest"], tuple(data["fold-reservation-ids"]),
        )


@dataclass(frozen=True)
class MarkerState:
    """The private run marker: ownership, revision, reservations, receipts."""
    schema_version: int
    run_id: str
    owner_nonce: str
    revision: int
    worktree: str
    branch: str
    plan_digest: str
    required_base: str
    cursor_digest: Optional[str]
    in_flight_operation: Optional[str]
    reservations: Tuple[Reservation, ...]
    receipts: Tuple[ReceiptRecord, ...]
    deadline: Optional[dict]
    transaction: Optional[TransactionIntent]


def marker_to_bytes(marker: MarkerState) -> bytes:
    """Serialize the marker packet deterministically."""
    payload = {
        "schema-version": marker.schema_version, "kind": "marker",
        "run-id": marker.run_id, "owner-nonce": marker.owner_nonce,
        "revision": marker.revision, "worktree": marker.worktree,
        "branch": marker.branch, "plan-execution-digest": marker.plan_digest,
        "required-base": marker.required_base, "cursor-digest": marker.cursor_digest,
        "in-flight-operation": marker.in_flight_operation,
        "reservations": [r.as_dict() for r in marker.reservations],
        "receipts": [r.as_dict() for r in marker.receipts],
        "deadline": marker.deadline,
        "transaction": marker.transaction.as_dict() if marker.transaction else None,
    }
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def parse_marker(raw: bytes) -> MarkerState:
    """Parse one bounded marker packet into its closed record."""
    payload = parse_closed_json(raw, max_bytes=MAX_MARKER_BYTES, label="marker")
    data = parse_object(payload, "marker", "run marker", (
        ("schema-version", _check_int, {}),
        ("kind", _check_string, {"max_bytes": 16}),
        ("run-id", _check_id, {}),
        ("owner-nonce", _check_id, {}),
        ("revision", _check_int, {}),
        ("worktree", _check_string, {"max_bytes": 1024}),
        ("branch", _check_string, {"max_bytes": 256}),
        ("plan-execution-digest", _check_sha, {}),
        ("required-base", _check_string, {"max_bytes": 256}),
        ("cursor-digest", _check_sha, {"nullable": True}),
        ("in-flight-operation", _check_id, {"nullable": True}),
        ("reservations", _check_list, {"max_items": 32}),
        ("receipts", _check_list, {"max_items": 32}),
        ("deadline", _validate_deadline, {}),
        ("transaction", lambda value, path: value, {}),
    ))
    if data["schema-version"] != 1 or data["kind"] != "marker":
        raise StateError("marker must be schema-version 1 with kind 'marker'.")
    return MarkerState(
        data["schema-version"], data["run-id"], data["owner-nonce"],
        data["revision"], data["worktree"], data["branch"],
        data["plan-execution-digest"], data["required-base"],
        data["cursor-digest"], data["in-flight-operation"],
        tuple(
            Reservation.from_dict(item, f"reservations[{i}]")
            for i, item in enumerate(data["reservations"])
        ),
        tuple(
            ReceiptRecord.from_dict(item, f"receipts[{i}]")
            for i, item in enumerate(data["receipts"])
        ),
        data["deadline"],
        (
            TransactionIntent.from_dict(data["transaction"], "transaction")
            if data["transaction"] is not None else None
        ),
    )


def validate_cursor_record(raw: bytes) -> dict:
    """Validate the closed versioned cursor record (active-state JSON)."""
    payload = parse_closed_json(raw, max_bytes=MAX_CHECKPOINT_BYTES, label="checkpoint")
    if payload.get("schemaVersion") != "compound-gpid-active-state-v1":
        raise PacketError("checkpoint must carry schemaVersion 'compound-gpid-active-state-v1'.")
    if payload.get("workflow") != "/cg-autopilot":
        raise PacketError("checkpoint workflow must be '/cg-autopilot'.")
    if payload.get("status") not in CURSOR_STATUSES:
        raise PacketError(f"checkpoint status must be one of {CURSOR_STATUSES}.")
    updated_at = payload.get("updatedAt")
    if not isinstance(updated_at, str) or not _UPDATED_AT_RE.fullmatch(updated_at):
        raise PacketError(
            "checkpoint updatedAt must be an ISO-8601 timestamp such as "
            "'2026-09-15T10:30:00Z'."
        )
    for field in ("plan", "executionReport"):
        value = payload.get(field)
        if value is not None and (not isinstance(value, str) or not value):
            raise PacketError(f"checkpoint {field} must be null or a path string.")
    _check_string(payload.get("nextCommand"), "nextCommand", max_bytes=1024)
    current_phase = payload.get("currentPhase")
    if current_phase is not None:
        _check_int(current_phase, "currentPhase", minimum=1)
    for field in ("evidenceStatus", "unresolvedDecisions"):
        value = payload.get(field)
        if value is not None and not isinstance(value, list):
            raise PacketError(f"checkpoint {field} must be null or an array.")
    refs = payload.get("artifactRefs")
    if not isinstance(refs, list):
        raise PacketError("checkpoint artifactRefs must be a list (possibly empty).")
    for index, item in enumerate(refs):
        data = parse_object(item, f"artifactRefs[{index}]", "artifact ref", (
            ("kind", _check_string, {"max_bytes": 32}),
            ("path", _check_path, {}),
            ("status", _check_string, {"max_bytes": 16}),
        ))
    section = payload.get("autopilot")
    allowed = {
        "schema-version", "run-id", "revision", "worktree", "branch",
        "required-base", "plan-execution-digest", "installed-command-digest",
        "installed-contract-digest", "batch-pointer", "stage-pointer",
        "artifact-refs", "folded-attempt-ids", "next-action",
    }
    if not isinstance(section, dict) or set(section) != allowed:
        raise PacketError("checkpoint 'autopilot' section has unexpected field or missing fields.")
    _check_int(section["schema-version"], "autopilot.schema-version")
    if section["schema-version"] != 1:
        raise PacketError("autopilot.schema-version enum must be exactly 1.")
    _check_id(section["run-id"], "autopilot.run-id")
    _check_int(section["revision"], "autopilot.revision")
    _check_string(section["worktree"], "autopilot.worktree", max_bytes=1024)
    _check_string(section["branch"], "autopilot.branch", max_bytes=256)
    _check_string(section["required-base"], "autopilot.required-base", max_bytes=256)
    _check_sha(section["plan-execution-digest"], "autopilot.plan-execution-digest")
    _check_sha(section["installed-command-digest"], "autopilot.installed-command-digest", nullable=True)
    _check_sha(section["installed-contract-digest"], "autopilot.installed-contract-digest", nullable=True)
    batch = section["batch-pointer"]
    if batch is not None:
        data = parse_object(batch, "batch-pointer", "batch pointer", (
            ("phase", _check_int, {"minimum": 1}),
            ("segment-start", _check_int, {"minimum": 1}),
            ("segment-end", _check_int, {"minimum": 1}),
        ))
        if data["segment-end"] < data["segment-start"]:
            raise PacketError("batch-pointer segment range must be ascending.")
    stage = section["stage-pointer"]
    if stage is not None:
        data = parse_object(stage, "stage-pointer", "stage pointer", (
            ("stage", _check_string, {"max_bytes": 32}),
            ("operation-id", _check_id, {"nullable": True}),
        ))
        if data["stage"] not in STAGES:
            raise PacketError(f"stage-pointer.stage enum must be one of {STAGES}.")
    refs = _check_list(section["artifact-refs"], "autopilot.artifact-refs", max_items=16)
    for index, item in enumerate(refs):
        data = parse_object(item, f"artifact-refs[{index}]", "artifact ref", (
            ("kind", _check_string, {"max_bytes": 32}),
            ("path", _check_path, {}),
            ("sha256", _check_sha, {}),
        ))
        if data["kind"] not in ARTIFACT_KINDS:
            raise PacketError(f"artifact-refs[{index}].kind must be one of {ARTIFACT_KINDS}.")
    folded = _check_list(section["folded-attempt-ids"], "autopilot.folded-attempt-ids", max_items=32)
    for index, item in enumerate(folded):
        _check_id(item, f"folded-attempt-ids[{index}]")
    _check_string(section["next-action"], "autopilot.next-action", max_bytes=256)
    return payload
