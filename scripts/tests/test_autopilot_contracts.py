"""Static bootstrap contract guards, not native runtime qualification.

Also closed-packet validation for the implemented Python protocol records
(Phase 2, Step 4).

Run: python -B -m pytest scripts/tests/test_autopilot_contracts.py -q
"""

import json
from pathlib import Path

import pytest

from autopilot import contracts
from autopilot.contracts import (
    MAX_ENVELOPE_BYTES,
    MAX_RESULT_BYTES,
    PacketError,
)
from autopilot import packets
from autopilot.packets import StageEnvelope, StageResult


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / ".github/shared/autopilot-stage.contract.md"


@pytest.mark.parametrize(
    "clause",
    [
        "probe-only",
        "unsupported-adapter",
        "arbitrary document flag",
        "missing marker",
        "missing operation",
        "malformed result",
        "undeclared agent",
        "instruction-like report text",
        "parent-only",
        "cursor-update-request",
        "begin-effect",
        "prepare-publication",
        "extend-ci-deadline",
        "released-no-effect",
        "4096",
        "16384",
        "32768",
    ],
)
def test_source_contract_defines_required_boundary(clause: str) -> None:
    """Each required boundary must exist; e.g. missing operation must stop."""
    assert CONTRACT.is_file(), "Missing canonical autopilot stage contract"
    assert clause in CONTRACT.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "relative",
    [
        ".github/prompts/cg-autopilot.prompt.md",
        ".github/agents/cg-autopilot.agent.md",
        ".github/agents/cg-workflow-stage.agent.md",
        ".github/agents/cg-bootstrap-leaf.agent.md",
    ],
)
def test_bootstrap_assets_reference_contract_without_model_assignment(relative: str) -> None:
    """Bootstrap assets share authority; e.g. the stage loads the contract."""
    path = ROOT / relative
    assert path.is_file(), f"Missing bootstrap asset: {relative}"
    source = path.read_text(encoding="utf-8")
    assert "autopilot-stage.contract.md" in source
    assert "probe-only" in source
    frontmatter = source.split("---", 2)[1]
    assert not any(line.startswith("model:") for line in frontmatter.splitlines())


def test_contract_restricted_leaf_replaces_builtin_general_for_probe_edges() -> None:
    """The probe leaf is the restricted cg-bootstrap-leaf, not built-in general."""
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "cg-bootstrap-leaf" in contract
    assert "The general leaf executes only those" not in contract
    assert "read-only Git probes" in contract
    assert "does not delegate" in contract


def test_contract_stage_uses_restricted_leaf_for_stage_general_edge() -> None:
    """stage-general probe receipt text names the restricted leaf explicitly."""
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "`cg-bootstrap-leaf`" in contract
    assert "built-in `general`" in contract or "built-in general" in contract


def test_contract_leaf_verifies_caller_via_native_identity() -> None:
    """The leaf verifies its native caller through cg_native_identity before probes,
    treating evidence-only unverified qualification as the expected pass condition."""
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "cg_native_identity" in contract
    assert "evidence-only" in contract
    assert "unverifiable" in contract
    assert "native-identity-unverified" in contract


def test_contract_states_run_id_charset() -> None:
    """The stage contract states the run-id charset; the example and the
    validator agree that digit-leading IDs like 20260915-103000 are valid."""
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "20260915-103000" in contract
    assert "lowercase ASCII letters, digits and hyphens" in contract
    assert contracts._check_id("20260915-103000", "run-id") == "20260915-103000"
    assert contracts._check_id("run-1", "run-id") == "run-1"
    with pytest.raises(PacketError):
        contracts._check_id("-leading-hyphen", "run-id")
    with pytest.raises(PacketError):
        contracts._check_id("UPPERCASE", "run-id")


# ---------------------------------------------------------------------------
# Closed packet validation (implemented protocol records)
# ---------------------------------------------------------------------------

_SHA = "a" * 64


def _envelope() -> dict:
    return {
        "schema-version": 1,
        "run-id": "run-1",
        "operation-id": "op-1",
        "stage": "work",
        "root": "C:/repo",
        "branch": "cg-autopilot",
        "plan": ".cg-docs/plans/p.md",
        "plan-execution-digest": _SHA,
        "contract-digest": _SHA,
        "command-digest": _SHA,
        "expected-revision": 0,
        "scope": [".cg-docs/plans/p.md"],
        "approval-refs": [],
        "reservation-id": None,
    }


def _result() -> dict:
    artifact = {
        "kind": "report",
        "path": ".cg-docs/work-reports/r.md",
        "byte-count": 12,
        "sha256": _SHA,
        "operation-id": "op-1",
        "content-identity": None,
    }
    test = {
        "command-id": "cmd-1",
        "started-at": "2026-09-15T00:00:00Z",
        "ended-at": "2026-09-15T00:01:00Z",
        "scope-digest": _SHA,
        "exit-status": 0,
        "result-ref": "tests/last-run.json",
        "status": "passed",
    }
    return {
        "schema-version": 1,
        "stage": "work",
        "status": "succeeded",
        "run-id": "run-1",
        "operation-id": "op-1",
        "artifacts": [artifact],
        "head-before": _SHA,
        "head-after": _SHA,
        "change-manifest-hash": _SHA,
        "tests": [test],
        "next-stage": None,
    }


def _raw(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


def test_stage_envelope_accepts_complete_packet() -> None:
    envelope = StageEnvelope.parse(_raw(_envelope()))
    assert envelope.operation_id == "op-1"
    assert envelope.stage == "work"
    assert envelope.expected_revision == 0


def test_stage_result_accepts_complete_packet() -> None:
    result = StageResult.parse(_raw(_result()))
    assert result.status == "succeeded"
    assert len(result.artifacts) == 1
    assert result.tests[0].status == "passed"


def test_result_heads_accept_sha256_and_git_identities() -> None:
    """Head/digest fields accept 64-hex SHA-256 and git:<40|64 hex> identities."""
    for identity in (_SHA, "git:" + "a" * 40, "git:" + "a" * 64, None):
        result = _result()
        result["head-before"] = identity
        result["head-after"] = identity
        result["change-manifest-hash"] = identity
        parsed = StageResult.parse(_raw(result))
        assert parsed.head_before == identity
    with pytest.raises(PacketError, match="SHA-256"):
        result = _result()
        result["head-before"] = "git:xyz"
        StageResult.parse(_raw(result))


@pytest.mark.parametrize("field,value,error", [
    ("schema-version", True, "type"),
    ("schema-version", "1", "type"),
    ("schema-version", 2, "enum"),
    ("run-id", 5, "type"),
    ("stage", "unknown", "enum"),
    ("expected-revision", -1, "range"),
    ("expected-revision", True, "type"),
    ("contract-digest", "bad", "pattern"),
    ("reservation-id", 5, "type"),
    ("scope", ["a"] * 17, "items"),
])
def test_malformed_envelope_fields(field: str, value: object, error: str) -> None:
    envelope = _envelope()
    envelope[field] = value
    with pytest.raises(PacketError, match=error):
        StageEnvelope.parse(_raw(envelope))


def test_envelope_rejects_missing_unknown_fields() -> None:
    envelope = _envelope()
    for key in list(envelope):
        with pytest.raises(PacketError, match="fields"):
            StageEnvelope.parse(_raw({k: v for k, v in envelope.items() if k != key}))
    with pytest.raises(PacketError, match="unexpected field"):
        StageEnvelope.parse(_raw({**envelope, "extra": 1}))


def test_envelope_byte_limit_is_16384() -> None:
    envelope = _envelope()
    raw = _raw(envelope)
    padded = raw + b" " * (MAX_ENVELOPE_BYTES - len(raw))
    assert StageEnvelope.parse(padded).run_id == "run-1"
    with pytest.raises(PacketError, match="packet-too-large"):
        StageEnvelope.parse(padded + b" ")


def test_envelope_rejects_duplicate_json_keys() -> None:
    raw = _raw(_envelope())
    with pytest.raises(PacketError, match="duplicate-key"):
        StageEnvelope.parse(raw[:-1] + b', "stage": "work"}')


@pytest.mark.parametrize("field,value,error", [
    ("status", "complete", "enum"),
    ("status", 1, "type"),
        ("artifacts", {}, "type"),
        ("head-before", "zz", "SHA-256"),
        ("head-before", 1, "type"),
        ("change-manifest-hash", _SHA + "a", "SHA-256"),
    ("next-stage", "/cg-work", "enum"),
    ("run-id", None, "type"),
])
def test_malformed_result_fields(field: str, value: object, error: object) -> None:
    result = _result()
    result[field] = value
    with pytest.raises(PacketError, match=error or "next-stage"):
        StageResult.parse(_raw(result))


def test_result_optional_fields_are_decision_and_cursor_updates_only() -> None:
    result = _result()
    result["decision"] = {
        "request-id": "req-1",
        "summary": "Choose a base.",
        "options": ["dev", "main"],
        "scope-digest": _SHA,
        "approval-refs": [],
    }
    result["cursor-update-requests"] = [{
        "expected-revision": 0,
        "event-kind": "phase-boundary",
        "plan-ref": ".cg-docs/plans/p.md",
        "report-ref": ".cg-docs/work-reports/r.md",
    }]
    parsed = StageResult.parse(_raw(result))
    assert parsed.decision is not None and parsed.decision.request_id == "req-1"
    assert parsed.cursor_update_requests[0].event_kind == "phase-boundary"
    result["other"] = 1
    with pytest.raises(PacketError, match="unexpected field"):
        StageResult.parse(_raw(result))


def test_result_byte_limit_is_4096() -> None:
    result = _result()
    raw = _raw(result)
    padded = raw + b" " * (MAX_RESULT_BYTES - len(raw))
    assert StageResult.parse(padded).status == "succeeded"
    with pytest.raises(PacketError, match="packet-too-large"):
        StageResult.parse(padded + b" ")


def test_artifact_reference_closed_fields() -> None:
    artifact = _result()["artifacts"][0]
    reference = packets.ArtifactReference.from_json(artifact, "artifacts[0]")
    assert reference.kind == "report"
    for key in list(artifact):
        with pytest.raises(PacketError, match="fields"):
            packets.ArtifactReference.from_json(
                {k: v for k, v in artifact.items() if k != key}, "ref"
            )
    for key, value in [
        ("kind", "unknown"), ("byte-count", True), ("byte-count", -1),
        ("sha256", None), ("operation-id", ""),
        ("content-identity", "git:zzz"), ("path", "/abs"),
    ]:
        with pytest.raises(PacketError):
            packets.ArtifactReference.from_json({**artifact, key: value}, "ref")


def test_test_reference_closed_fields_and_status_enum() -> None:
    test = _result()["tests"][0]
    reference = packets.TestReference.from_json(test, "tests[0]")
    assert reference.status == "passed"
    with pytest.raises(PacketError, match="enum"):
        packets.TestReference.from_json({**test, "status": "skipped"}, "t")


def test_decision_bounds() -> None:
    decision = {
        "request-id": "req-1",
        "summary": "s",
        "options": ["a"],
        "scope-digest": _SHA,
        "approval-refs": [],
    }
    packets.Decision.from_json(decision, "decision")
    with pytest.raises(PacketError, match="bytes"):
        packets.Decision.from_json({**decision, "summary": "x" * 513}, "d")
    with pytest.raises(PacketError, match="items"):
        packets.Decision.from_json({**decision, "options": []}, "d")
    with pytest.raises(PacketError, match="items"):
        packets.Decision.from_json(
            {**decision, "options": [str(i) for i in range(9)]}, "d"
        )


def test_cursor_update_request_event_kinds() -> None:
    request = {
        "expected-revision": 1,
        "event-kind": "blocked-stop",
        "plan-ref": "p.md",
        "report-ref": "r.md",
    }
    parsed = packets.CursorUpdateRequest.from_json(request, "req")
    assert parsed.event_kind == "blocked-stop"
    with pytest.raises(PacketError, match="enum"):
        packets.CursorUpdateRequest.from_json(
            {**request, "event-kind": "invented"}, "req"
        )


def test_parse_closed_json_rejects_non_object_and_bad_utf8() -> None:
    with pytest.raises(PacketError, match="object"):
        contracts.parse_closed_json(b"[]", max_bytes=128, label="x")
    with pytest.raises(PacketError):
        contracts.parse_closed_json(b'{"a": "\xff"}', max_bytes=128, label="x")
