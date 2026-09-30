"""Parent transition loop and decision handoff tests (Phase 3, Step 7).

Run: python -B -m pytest scripts/tests/test_autopilot_pipeline.py -q
"""

import hashlib
import json
from pathlib import Path

import pytest

from autopilot.contracts import (
    PacketError,
)
from autopilot.packets import StageEnvelope, StageResult
from autopilot.context import (
    CONTEXT_ALLOWANCE_BYTES,
    FRAME_BYTE_LIMIT,
    ParentContextBudget,
)
from autopilot.pipeline import (
    PHASE_4_STAGES,
    PREPARATION_BEFORE,
    STAGE_COMMANDS,
    PipelineError,
    assert_fresh_operation,
    correlate,
    decision_handoff,
    effect_receipt_exists,
    preparation_required_for,
    propose_settlement,
    render_command,
    require_begin_effect,
    resolve_activation,
    run_foreground,
    select_transition,
    settle_operation,
    validate_approval_refs,
)
from autopilot.checkpoint import begin_effect, record_result
from autopilot.state import (
    acquire_marker,
    begin_stage,
    reserve,
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


_SHA = "a" * 64
_NONCE = "nonce-a"
_RUN = "run-1"


def _envelope(stage: str = "work", operation_id: str = "op-1",
              approval_refs: list = None) -> StageEnvelope:
    payload = {
        "schema-version": 1,
        "run-id": _RUN,
        "operation-id": operation_id,
        "stage": stage,
        "root": "C:/repo",
        "branch": "cg-autopilot",
        "plan": ".cg-docs/plans/p.md",
        "plan-execution-digest": _SHA,
        "contract-digest": _SHA,
        "command-digest": _SHA,
        "expected-revision": 0,
        "scope": [".cg-docs/plans/p.md"],
        "approval-refs": approval_refs if approval_refs is not None else [],
        "reservation-id": None,
    }
    return StageEnvelope.parse(json.dumps(payload).encode("utf-8"))


def _result_payload(
    stage: str = "work",
    status: str = "succeeded",
    operation_id: str = "op-1",
    *,
    manifest: object = None,
    decision: object = None,
    tests: list = None,
    next_stage: object = None,
) -> dict:
    return {
        "schema-version": 1,
        "stage": stage,
        "status": status,
        "run-id": _RUN,
        "operation-id": operation_id,
        "artifacts": [],
        "head-before": None,
        "head-after": None,
        "change-manifest-hash": manifest,
        "tests": tests if tests is not None else [],
        "next-stage": next_stage,
        **({"decision": decision} if decision is not None else {}),
    }


def _result(stage: str = "work", status: str = "succeeded",
            operation_id: str = "op-1", **kwargs) -> StageResult:
    return StageResult.parse(
        json.dumps(_result_payload(stage, status, operation_id, **kwargs)).encode("utf-8")
    )


class RecordingDispatcher:
    """Recording fake foreground dispatcher; outcomes per operation ID."""

    def __init__(self, outcomes: dict) -> None:
        self.outcomes = outcomes
        self.calls: list = []

    def __call__(self, command: str, envelope: StageEnvelope):
        self.calls.append((command, envelope))
        outcome = self.outcomes[envelope.operation_id]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


# ---------------------------------------------------------------------------
# Exact canonical commands and stage activation
# ---------------------------------------------------------------------------


def test_render_command_exact_canonical_strings() -> None:
    assert render_command("work", phase=2) == "/cg-work phase2 review:none"
    assert render_command("prepare-publication") == "/cg-commit-push-pr"
    assert render_command("review") == "/cg-review"
    assert render_command("triage") == "/cg-fix-triage"
    assert render_command("verify-review") == "/cg-review mode:verify"
    assert render_command("compound") == "/cg-compound"
    assert set(STAGE_COMMANDS) == set(
        ("work", "prepare-publication", "review", "triage",
         "verify-review", "compound", "publish", "verify-pr")
    )
    with pytest.raises(PipelineError, match="unknown-stage"):
        render_command("invented-stage")
    with pytest.raises(PipelineError, match="phase"):
        render_command("work")


def test_preparation_required_before_reviews_only() -> None:
    assert preparation_required_for("review")
    assert preparation_required_for("verify-review")
    assert not preparation_required_for("work")
    assert not preparation_required_for("prepare-publication")
    assert not preparation_required_for("compound")
    assert PREPARATION_BEFORE == frozenset({"review", "verify-review"})
    with pytest.raises(PipelineError, match="unknown-stage"):
        preparation_required_for("nope")


def test_resolve_activation_requires_fresh_preparation() -> None:
    resolve_activation("work")
    resolve_activation("prepare-publication", previous="work")
    resolve_activation("review", previous="prepare-publication")
    resolve_activation("verify-review", previous="prepare-publication")
    resolve_activation("triage", previous="review")
    resolve_activation("compound", previous="verify-review")
    resolve_activation("publish")
    resolve_activation("verify-pr", previous="publish")
    with pytest.raises(PipelineError, match="prepare-required"):
        resolve_activation("review", previous="work")
    with pytest.raises(PipelineError, match="prepare-required"):
        resolve_activation("verify-review")
    with pytest.raises(PipelineError, match="publish-required"):
        resolve_activation("verify-pr")
    with pytest.raises(PipelineError, match="publish-required"):
        resolve_activation("verify-pr", previous="compound")
    with pytest.raises(PipelineError, match="unknown-stage"):
        resolve_activation("review", previous="ghost")
    assert PHASE_4_STAGES == frozenset({"publish", "verify-pr"})


# ---------------------------------------------------------------------------
# Closed transition table
# ---------------------------------------------------------------------------


def test_transition_table_successful_phase_progression() -> None:
    assert select_transition("work", _result("work")).next_stage == "prepare-publication"
    assert select_transition("prepare-publication", _result("prepare-publication")).next_stage == "review"
    assert select_transition(
        "prepare-publication", _result("prepare-publication"), verify_context=True
    ).next_stage == "verify-review"
    assert select_transition("review", _result("review"), has_findings=True).next_stage == "triage"
    assert select_transition("review", _result("review"), has_findings=False).next_stage == "compound"
    assert select_transition("triage", _result("triage")).next_stage == "prepare-publication"
    assert select_transition("verify-review", _result("verify-review")).next_stage == "compound"
    compound = select_transition("compound", _result("compound"))
    assert compound.next_stage == "publish"
    assert compound.kind == "phase-4"
    assert select_transition("publish", _result("publish")).next_stage == "verify-pr"
    finished = select_transition("verify-pr", _result("verify-pr"))
    assert finished.next_stage is None
    assert finished.kind == "batch-complete"


def test_transition_stops_on_failed_blocked_cancelled() -> None:
    for status in ("failed", "blocked"):
        transition = select_transition("work", _result("work", status))
        assert transition.next_stage is None
        assert transition.kind == "stop"
        assert transition.reason == status


def test_transition_needs_input_yields_decision() -> None:
    decision = {
        "request-id": "req-1",
        "summary": "Choose the base.",
        "options": ["origin/dev", "main"],
        "scope-digest": _SHA,
        "approval-refs": [],
    }
    result = _result("triage", "needs-input", decision=decision)
    transition = select_transition("triage", result)
    assert transition.kind == "needs-input"
    assert transition.next_stage is None
    handoff = decision_handoff(result)
    assert handoff is not None and handoff.options == ("origin/dev", "main")
    assert decision_handoff(_result("work")) is None


def test_automatic_approval_attempt_rejected() -> None:
    decision = {
        "request-id": "req-1",
        "summary": "self-approved",
        "options": ["yes"],
        "scope-digest": _SHA,
        "approval-refs": [],
    }
    with pytest.raises(PipelineError, match="automatic-approval-rejected"):
        select_transition("triage", _result("triage", "succeeded", decision=decision))


def test_needs_input_without_decision_rejected() -> None:
    with pytest.raises(PipelineError, match="needs-input-without-decision"):
        decision_handoff(_result("triage", "needs-input"))


def test_transition_rejects_result_stage_mismatch() -> None:
    with pytest.raises(PipelineError, match="stage-mismatch"):
        select_transition("work", _result("review"))


def test_transition_blocks_succeeded_result_with_non_passed_tests() -> None:
    """Exceptions are not passes: a succeeded result carrying failed or
    accepted-exception test entries can never advance the pipeline."""
    for status in ("failed", "accepted-exception"):
        result = _result("work", tests=[{
            "command-id": "pytest",
            "started-at": "2026-09-15T10:00:00Z",
            "ended-at": "2026-09-15T10:01:00Z",
            "scope-digest": _SHA,
            "exit-status": 0,
            "result-ref": "tests/last-run.json",
            "status": status,
        }])
        with pytest.raises(PipelineError, match="exceptions-are-not-passes"):
            select_transition("work", result)


# ---------------------------------------------------------------------------
# Correlation and foreground dispatch
# ---------------------------------------------------------------------------


def test_correlate_valid_child() -> None:
    envelope = _envelope("work", "op-1")
    correlated = correlate("ses-child-1", envelope=envelope, result=_result("work", operation_id="op-1"))
    assert correlated.child_id == "ses-child-1"
    assert correlated.operation_id == "op-1"


@pytest.mark.parametrize("child_id,error", [
    ("", "native-child-missing"),
    (None, "native-child-missing"),
])
def test_correlate_missing_child(child_id: object, error: str) -> None:
    with pytest.raises(PipelineError, match=error):
        correlate(child_id, envelope=_envelope("work"), result=_result("work"))


def test_correlate_operation_run_and_stage_mismatch() -> None:
    envelope = _envelope("work", "op-1")
    with pytest.raises(PipelineError, match="operation-mismatch"):
        correlate("c", envelope=envelope, result=_result("work", operation_id="op-2"))
    other_run = StageResult.parse(
        json.dumps({**_result_payload("work", operation_id="op-1"), "run-id": "run-9"}).encode()
    )
    with pytest.raises(PipelineError, match="run-mismatch"):
        correlate("c", envelope=envelope, result=other_run)
    with pytest.raises(PipelineError, match="stage-mismatch"):
        correlate("c", envelope=envelope, result=_result("review", operation_id="op-1"))


def test_run_foreground_records_exact_single_dispatch() -> None:
    envelope = _envelope("prepare-publication", "op-1")
    raw = json.dumps(_result_payload("prepare-publication", operation_id="op-1")).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-fresh-1", raw)})
    correlated = run_foreground(
        command="/cg-commit-push-pr", envelope=envelope, dispatcher=dispatcher
    )
    assert len(dispatcher.calls) == 1
    command, seen_envelope = dispatcher.calls[0]
    assert command == "/cg-commit-push-pr"
    assert seen_envelope.operation_id == "op-1"
    assert correlated.child_id == "ses-fresh-1"
    assert correlated.result.status == "succeeded"


def test_run_foreground_rejects_malformed_result() -> None:
    dispatcher = RecordingDispatcher({"op-1": ("ses-1", b"{not json")})
    with pytest.raises(PacketError):
        run_foreground(command="/cg-review", envelope=_envelope("review", "op-1"),
                       dispatcher=dispatcher)


def test_run_foreground_rejects_forged_result_without_fallback() -> None:
    raw = json.dumps(_result_payload("review", operation_id="other-op")).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-1", raw)})
    with pytest.raises(PipelineError, match="operation-mismatch"):
        run_foreground(command="/cg-review", envelope=_envelope("review", "op-1"),
                       dispatcher=dispatcher)
    assert len(dispatcher.calls) == 1


def test_run_foreground_requires_begin_effect_for_substantive_result() -> None:
    raw = json.dumps(_result_payload("work", manifest=_SHA)).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-1", raw)})
    with pytest.raises(PipelineError, match="missing-begin-effect"):
        run_foreground(command="/cg-work phase1 review:none",
                       envelope=_envelope("work", "op-1"), dispatcher=dispatcher)
    dispatcher = RecordingDispatcher({"op-1": ("ses-1", raw)})
    correlated = run_foreground(
        command="/cg-work phase1 review:none", envelope=_envelope("work", "op-1"),
        dispatcher=dispatcher, effect_started=True,
    )
    assert correlated.result.change_manifest_hash == _SHA


def test_run_foreground_zero_effect_needs_input_needs_no_effect_receipt() -> None:
    decision = {
        "request-id": "req-1", "summary": "pick scope", "options": ["a", "b"],
        "scope-digest": _SHA, "approval-refs": [],
    }
    raw = json.dumps(_result_payload("triage", "needs-input", decision=decision)).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-1", raw)})
    correlated = run_foreground(
        command="/cg-fix-triage", envelope=_envelope("triage", "op-1"),
        dispatcher=dispatcher,
    )
    assert correlated.result.status == "needs-input"


def test_assert_fresh_operation_rejects_reuse() -> None:
    assert_fresh_operation(frozenset({"op-1"}), "op-2")
    with pytest.raises(PipelineError, match="operation-reused"):
        assert_fresh_operation(frozenset({"op-1"}), "op-1")


def test_validate_approval_refs_stale_or_current() -> None:
    validate_approval_refs(_envelope("review", approval_refs=["app-1"]),
                           frozenset({"app-1", "app-2"}))
    validate_approval_refs(_envelope("review"), frozenset())
    with pytest.raises(PipelineError, match="stale-approval"):
        validate_approval_refs(_envelope("review", approval_refs=["app-old"]),
                               frozenset({"app-1"}))


def test_no_unverified_model_override() -> None:
    forged = {
        "schema-version": 1, "run-id": _RUN, "operation-id": "op-1",
        "stage": "work", "root": "C:/repo", "branch": "cg-autopilot",
        "plan": "p.md", "plan-execution-digest": _SHA, "contract-digest": _SHA,
        "command-digest": _SHA, "expected-revision": 0, "scope": [],
        "approval-refs": [], "reservation-id": None, "model": "gpt-5",
    }
    with pytest.raises(PacketError, match="unexpected field"):
        StageEnvelope.parse(json.dumps(forged).encode())
    envelope = _envelope("work")
    assert envelope.stage == "work"
    for command in STAGE_COMMANDS.values():
        assert "model" not in command and "--model" not in command
    assert not any(hasattr(_envelope("work"), field) for field in
                   ("model", "provider", "reasoning-variant", "variant"))


# ---------------------------------------------------------------------------
# Zero-effect versus partial-effect settlement
# ---------------------------------------------------------------------------


def _marker_rig(tmp_path: Path):
    coordination = tmp_path / "git" / "cg-autopilot"
    marker = acquire_marker(
        Path("root"), coordination, run_id=_RUN, owner_nonce=_NONCE,
        worktree="C:/w", branch="cg-autopilot",
        plan_digest=_sha(b"plan"), required_base="origin/dev",
    )
    return coordination, marker


def _needs_input_packet(operation_id: str, *, manifest: object = None) -> bytes:
    decision = {
        "request-id": "req-1", "summary": "ask", "options": ["go", "stop"],
        "scope-digest": _SHA, "approval-refs": [],
    }
    payload = _result_payload(
        "triage", "needs-input", operation_id, manifest=manifest, decision=decision
    )
    return json.dumps(payload).encode("utf-8")


def test_zero_effect_yield_releases_and_replays_without_consuming_round(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="r1")
    record_result(coordination, "op-1", _needs_input_packet("op-1"))
    result = _result("triage", "needs-input")
    assert propose_settlement(result, effect_started=False) == "released-no-effect"
    assert not effect_receipt_exists(coordination, "op-1")
    marker = settle_operation(
        marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
        result=result, zero_effect_evidence=("tests/last-run.json",),
    )
    assert marker.reservations[0].status == "released-no-effect"
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r2")
    # Attempt display counts charged attempts only: the released round
    # proved zero effect, so this is charged attempt 1 of the cap.
    assert marker.reservations[-1].attempt == 1


def test_partial_effect_yield_is_charged_and_never_refunded(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="r1")
    begin_effect(coordination, "op-1", recorded_at="2026-09-15T00:00:00Z")
    record_result(coordination, "op-1", _needs_input_packet("op-1", manifest=_SHA))
    result = _result("triage", "needs-input", manifest=_SHA)
    assert propose_settlement(result, effect_started=True) == "charged"
    assert effect_receipt_exists(coordination, "op-1")
    marker = settle_operation(
        marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
        result=result, zero_effect_evidence=(),
    )
    assert marker.reservations[0].status == "charged"
    from autopilot.state import settle_stage

    with pytest.raises(Exception, match="reservation-charged"):
        settle_stage(
            marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
            outcome="released-no-effect", evidence_refs=("e",),
        )
    with pytest.raises(Exception, match="operation-not-in-flight"):
        settle_operation(
            marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
            result=result, zero_effect_evidence=(),
        )


def test_zero_effect_release_requires_evidence(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r1")
    begin_stage(marker, coordination, owner_nonce=_NONCE,
                operation_id="op-1", reservation_id="r1")
    with pytest.raises(PipelineError, match="missing-zero-effect-evidence"):
        settle_operation(
            marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
            result=_result("triage", "needs-input"), zero_effect_evidence=(),
        )


def test_interruption_after_answer_resumes_with_new_operation(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="r1")
    record_result(coordination, "op-1", _needs_input_packet("op-1"))
    marker = settle_operation(
        marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
        result=_result("triage", "needs-input"),
        zero_effect_evidence=("tests/last-run.json",),
    )
    previous = frozenset({"op-1"})
    with pytest.raises(PipelineError, match="operation-reused"):
        assert_fresh_operation(previous, "op-1")
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r2")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-2", reservation_id="r2")
    assert marker.in_flight_operation == "op-2"
    assert marker.reservations[-1].operation_id == "op-2"


def test_begin_effect_substantive_guard_pure() -> None:
    substantive = _result("work", manifest=_SHA)
    with pytest.raises(PipelineError, match="missing-begin-effect"):
        require_begin_effect(substantive, effect_started=False)
    require_begin_effect(substantive, effect_started=True)
    quiet = _result("triage", "needs-input")
    require_begin_effect(quiet, effect_started=False)


# ---------------------------------------------------------------------------
# Parent frame budget integration (Phase 5, Step 14)
# ---------------------------------------------------------------------------


def _charged_budget(used: int) -> ParentContextBudget:
    return ParentContextBudget(used=used)


def test_run_foreground_budget_check_pauses_before_next_dispatch() -> None:
    envelope = _envelope("prepare-publication", "op-1")
    raw = json.dumps(_result_payload("prepare-publication", operation_id="op-1")).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-fresh-1", raw)})
    budget = ParentContextBudget(used=CONTEXT_ALLOWANCE_BYTES - 64)
    with pytest.raises(PipelineError, match="context-pause"):
        run_foreground(
            command="/cg-commit-push-pr", envelope=envelope,
            dispatcher=dispatcher, context_budget=budget,
        )
    assert len(dispatcher.calls) == 1


def test_run_foreground_compact_frames_dispatch_within_budget() -> None:
    envelope = _envelope("prepare-publication", "op-1")
    raw = json.dumps(_result_payload("prepare-publication", operation_id="op-1")).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-fresh-1", raw)})
    correlated = run_foreground(
        command="/cg-commit-push-pr", envelope=envelope,
        dispatcher=dispatcher, context_budget=ParentContextBudget(),
    )
    assert correlated.child_id == "ses-fresh-1"


def test_run_foreground_oversized_frame_pauses_instead_of_truncating() -> None:
    envelope = _envelope("prepare-publication", "op-1")
    raw = json.dumps(_result_payload("prepare-publication", operation_id="op-1")).encode()
    dispatcher = RecordingDispatcher({"op-1": ("ses-fresh-1", raw)})
    with pytest.raises(PipelineError, match="context-pause.*frame-too-large"):
        run_foreground(
            command="/cg-commit-push-pr", envelope=envelope, dispatcher=dispatcher,
            context_budget=ParentContextBudget(),
            frame_metadata={"header": "h" * (FRAME_BYTE_LIMIT + 10)},
        )
    assert len(dispatcher.calls) == 1


def test_complete_stage_json_stays_within_packet_limit() -> None:
    base = _result_payload("work", operation_id="op-1")
    base["note"] = "x" * 5000
    with pytest.raises(PacketError):
        StageResult.parse(json.dumps(base).encode("utf-8"))
