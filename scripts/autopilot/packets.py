"""Closed protocol packets: stage envelopes, results, artifacts and decisions.

All packets are bounded before parsing, reject duplicate JSON keys and wrong
types (Booleans are not integers), and carry exactly their declared fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from autopilot.contracts import (
    ARTIFACT_KINDS,
    EVENT_KINDS,
    MAX_ARTIFACT_REFS,
    MAX_ENVELOPE_BYTES,
    MAX_RESULT_BYTES,
    PacketError,
    STAGES,
    RESULT_STATUSES,
    TEST_STATUSES,
    _check_id,
    _check_int,
    _check_list,
    _check_path,
    _check_sha,
    _check_string,
    _check_content_identity,
    parse_closed_json,
    parse_object,
)


@dataclass(frozen=True)
class ArtifactReference:
    """One bounded content-linked artifact reference."""

    kind: str
    path: str
    byte_count: int
    sha256: str
    operation_id: str
    content_identity: Optional[str]

    @classmethod
    def from_json(cls, value: Any, path: str) -> "ArtifactReference":
        data = parse_object(value, path, "artifact reference", (
            ("kind", _check_string, {"max_bytes": 32}),
            ("path", _check_path, {}),
            ("byte-count", _check_int, {}),
            ("sha256", _check_sha, {}),
            ("operation-id", _check_id, {}),
            ("content-identity", _check_content_identity, {}),
        ))
        if data["kind"] not in ARTIFACT_KINDS:
            raise PacketError(f"{path}.kind must be one of {ARTIFACT_KINDS}.")
        return cls(
            kind=data["kind"], path=data["path"],
            byte_count=data["byte-count"], sha256=data["sha256"],
            operation_id=data["operation-id"],
            content_identity=data["content-identity"],
        )

    def as_dict(self) -> dict:
        return {
            "kind": self.kind, "path": self.path, "byte-count": self.byte_count,
            "sha256": self.sha256, "operation-id": self.operation_id,
            "content-identity": self.content_identity,
        }


@dataclass(frozen=True)
class TestReference:
    """One frozen operation-specific test result reference."""

    command_id: str
    started_at: str
    ended_at: str
    scope_digest: str
    exit_status: int
    result_ref: str
    status: str

    @classmethod
    def from_json(cls, value: Any, path: str) -> "TestReference":
        data = parse_object(value, path, "test reference", (
            ("command-id", _check_id, {}),
            ("started-at", _check_string, {"max_bytes": 64}),
            ("ended-at", _check_string, {"max_bytes": 64}),
            ("scope-digest", _check_sha, {}),
            ("exit-status", _check_int, {"maximum": 255}),
            ("result-ref", _check_path, {}),
            ("status", _check_string, {"max_bytes": 32}),
        ))
        if data["status"] not in TEST_STATUSES:
            raise PacketError(f"{path}.status enum must be one of {TEST_STATUSES}.")
        return cls(
            command_id=data["command-id"], started_at=data["started-at"],
            ended_at=data["ended-at"], scope_digest=data["scope-digest"],
            exit_status=data["exit-status"], result_ref=data["result-ref"],
            status=data["status"],
        )

    def as_dict(self) -> dict:
        return {
            "command-id": self.command_id, "started-at": self.started_at,
            "ended-at": self.ended_at, "scope-digest": self.scope_digest,
            "exit-status": self.exit_status, "result-ref": self.result_ref,
            "status": self.status,
        }


@dataclass(frozen=True)
class Decision:
    """One scoped semantic decision with exact advertised option labels."""

    request_id: str
    summary: str
    options: Tuple[str, ...]
    scope_digest: str
    approval_refs: Tuple[str, ...]

    @classmethod
    def from_json(cls, value: Any, path: str) -> "Decision":
        data = parse_object(value, path, "decision", (
            ("request-id", _check_id, {}),
            ("summary", _check_string, {"max_bytes": 512}),
            ("options", _check_list, {"max_items": 8}),
            ("scope-digest", _check_sha, {}),
            ("approval-refs", _check_list, {"max_items": 8}),
        ))
        if not data["options"]:
            raise PacketError(f"{path}.options must contain 1..8 items.")
        for index, option in enumerate(data["options"]):
            _check_string(option, f"{path}.options[{index}]", max_bytes=128)
        for index, reference in enumerate(data["approval-refs"]):
            _check_string(reference, f"{path}.approval-refs[{index}]", max_bytes=512)
        return cls(
            data["request-id"], data["summary"], tuple(data["options"]),
            data["scope-digest"], tuple(data["approval-refs"]),
        )

    def as_dict(self) -> dict:
        return {
            "request-id": self.request_id, "summary": self.summary,
            "options": list(self.options), "scope-digest": self.scope_digest,
            "approval-refs": list(self.approval_refs),
        }


@dataclass(frozen=True)
class CursorUpdateRequest:
    """A child's bounded cursor publication request; never cursor bytes."""

    expected_revision: int
    event_kind: str
    plan_ref: str
    report_ref: str

    @classmethod
    def from_json(cls, value: Any, path: str) -> "CursorUpdateRequest":
        data = parse_object(value, path, "cursor-update-request", (
            ("expected-revision", _check_int, {}),
            ("event-kind", _check_string, {"max_bytes": 32}),
            ("plan-ref", _check_path, {}),
            ("report-ref", _check_path, {}),
        ))
        if data["event-kind"] not in EVENT_KINDS:
            raise PacketError(f"{path}.event-kind enum must be one of {EVENT_KINDS}.")
        return cls(
            expected_revision=data["expected-revision"],
            event_kind=data["event-kind"], plan_ref=data["plan-ref"],
            report_ref=data["report-ref"],
        )

    def as_dict(self) -> dict:
        return {
            "expected-revision": self.expected_revision,
            "event-kind": self.event_kind, "plan-ref": self.plan_ref,
            "report-ref": self.report_ref,
        }


@dataclass(frozen=True)
class StageEnvelope:
    """Correlation envelope for one authorized stage operation."""

    schema_version: int
    run_id: str
    operation_id: str
    stage: str
    root: str
    branch: str
    plan: str
    plan_execution_digest: str
    contract_digest: str
    command_digest: str
    expected_revision: int
    scope: Tuple[str, ...]
    approval_refs: Tuple[str, ...]
    reservation_id: Optional[str]

    @classmethod
    def parse(cls, raw: bytes) -> "StageEnvelope":
        payload = parse_closed_json(raw, max_bytes=MAX_ENVELOPE_BYTES, label="envelope")
        data = parse_object(payload, "envelope", "stage envelope", (
            ("schema-version", _check_int, {}),
            ("run-id", _check_id, {}),
            ("operation-id", _check_id, {}),
            ("stage", _check_string, {"max_bytes": 32}),
            ("root", _check_string, {"max_bytes": 1024}),
            ("branch", _check_string, {"max_bytes": 256}),
            ("plan", _check_path, {}),
            ("plan-execution-digest", _check_sha, {}),
            ("contract-digest", _check_sha, {}),
            ("command-digest", _check_sha, {}),
            ("expected-revision", _check_int, {}),
            ("scope", _check_list, {"max_items": 16}),
            ("approval-refs", _check_list, {"max_items": 8}),
            ("reservation-id", _check_id, {"nullable": True}),
        ))
        if data["schema-version"] != 1:
            raise PacketError("schema-version enum must be exactly 1.")
        if data["stage"] not in STAGES:
            raise PacketError(f"stage enum must be one of {STAGES}.")
        for index, item in enumerate(data["scope"]):
            _check_path(item, f"scope[{index}]")
        for index, item in enumerate(data["approval-refs"]):
            _check_string(item, f"approval-refs[{index}]")
        return cls(
            data["schema-version"], data["run-id"], data["operation-id"],
            data["stage"], data["root"], data["branch"], data["plan"],
            data["plan-execution-digest"], data["contract-digest"],
            data["command-digest"], data["expected-revision"],
            tuple(data["scope"]), tuple(data["approval-refs"]),
            data["reservation-id"],
        )


@dataclass(frozen=True)
class StageResult:
    """Closed production stage result; cancellation is non-success."""

    schema_version: int
    stage: str
    status: str
    run_id: str
    operation_id: str
    artifacts: Tuple[ArtifactReference, ...]
    head_before: Optional[str]
    head_after: Optional[str]
    change_manifest_hash: Optional[str]
    tests: Tuple[TestReference, ...]
    next_stage: Optional[str]
    decision: Optional[Decision]
    cursor_update_requests: Tuple[CursorUpdateRequest, ...]

    @classmethod
    def parse(cls, raw: bytes) -> "StageResult":
        payload = parse_closed_json(raw, max_bytes=MAX_RESULT_BYTES, label="result")
        required = {
            "schema-version", "stage", "status", "run-id", "operation-id",
            "artifacts", "head-before", "head-after", "change-manifest-hash",
            "tests", "next-stage",
        }
        allowed = required | {"decision", "cursor-update-requests"}
        if set(payload) < required or not set(payload) <= allowed:
            raise PacketError("result has unexpected field or missing fields.")
        data = parse_object(
            {key: payload[key] for key in required}, "result", "stage result", (
                ("schema-version", _check_int, {}),
                ("stage", _check_string, {"max_bytes": 32}),
                ("status", _check_string, {"max_bytes": 16}),
                ("run-id", _check_id, {}),
                ("operation-id", _check_id, {}),
                ("artifacts", _check_list, {"max_items": MAX_ARTIFACT_REFS}),
                ("head-before", _check_content_identity, {}),
                ("head-after", _check_content_identity, {}),
                ("change-manifest-hash", _check_content_identity, {}),
                ("tests", _check_list, {"max_items": 8}),
                ("next-stage", _check_string, {"max_bytes": 32, "nullable": True}),
            ),
        )
        if data["schema-version"] != 1:
            raise PacketError("schema-version enum must be exactly 1.")
        if data["stage"] not in STAGES:
            raise PacketError(f"stage enum must be one of {STAGES}.")
        if data["status"] not in RESULT_STATUSES:
            raise PacketError(f"status enum must be one of {RESULT_STATUSES}.")
        if data["next-stage"] is not None and data["next-stage"] not in STAGES:
            raise PacketError(
                f"next-stage enum must be null or one of {STAGES}; never a command."
            )
        decision = (
            Decision.from_json(payload["decision"], "decision")
            if "decision" in payload else None
        )
        requests = ()
        if "cursor-update-requests" in payload:
            requests = tuple(
                CursorUpdateRequest.from_json(item, f"cursor-update-requests[{index}]")
                for index, item in enumerate(payload["cursor-update-requests"])
            )
        return cls(
            data["schema-version"], data["stage"], data["status"],
            data["run-id"], data["operation-id"],
            tuple(
                ArtifactReference.from_json(item, f"artifacts[{index}]")
                for index, item in enumerate(data["artifacts"])
            ),
            data["head-before"], data["head-after"], data["change-manifest-hash"],
            tuple(
                TestReference.from_json(item, f"tests[{index}]")
                for index, item in enumerate(data["tests"])
            ),
            data["next-stage"], decision, requests,
        )
