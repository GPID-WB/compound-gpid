"""Parent transition loop, stage activation and decision handoff (Phase 3, Step 7).

A closed state machine over the canonical stage table. The parent never
implements a stage and never executes a child-returned command: every
transition is one named stage, semantic decisions become ``needs-input`` with
exact options/scope, and only the parent settles a reservation under the
zero-effect rule. Dispatch is one fresh foreground child per operation;
``task_id`` is never reused and no background writer is permitted. Phase 5
adds the measurable parent frame budget: every returned frame is
budget-checked before another dispatch and pauses instead of truncating.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping, Optional, Sequence, Tuple

import secure_fs
from autopilot.context import (
    ParentContextBudget,
    budget_decision,
    measure_frame,
)
from autopilot.contracts import (
    AutopilotError,
    MAX_MARKER_BYTES,
    STAGES,
)
from autopilot.packets import Decision, StageEnvelope, StageResult
from autopilot.state import MarkerState, settle_stage


class PipelineError(AutopilotError):
    """A transition, activation, correlation or handoff violation."""

    error_code = "autopilot-pipeline-error"


# Exact canonical commands per stage; the work command is phase-expanded and no
# other string is ever emitted by the parent.
STAGE_COMMANDS: Mapping[str, str] = {
    "work": "/cg-work phase{phase} review:none",
    "prepare-publication": "/cg-commit-push-pr",
    "review": "/cg-review",
    "triage": "/cg-fix-triage",
    "verify-review": "/cg-review mode:verify",
    "compound": "/cg-compound",
    "publish": "/cg-commit-push-pr",
    "verify-pr": "/cg-verify-pr",
}

# These stages require a fresh preparation-only run first (changed work or
# changed fixes precede the applicable review/verification).
PREPARATION_BEFORE = frozenset({"review", "verify-review"})

# Phase 3 never dispatches these stages; they belong to Phase 4.
PHASE_4_STAGES = frozenset({"publish", "verify-pr"})

# One-way effect receipt location shared with checkpoint.py's stage writes.
EFFECT_RELATIVE = "operations/{op}/effect.json"

RESULT_BYTES = 4096


@dataclass(frozen=True)
class Transition:
    """One closed transition decision; ``next_stage`` is None on stop/needs."""

    next_stage: Optional[str]
    kind: str
    reason: str = ""


@dataclass(frozen=True)
class CorrelatedChild:
    """A native child correlated with its reserved operation result."""

    child_id: str
    operation_id: str
    result: StageResult


# A foreground dispatcher: given the exact command and a validated envelope,
# return (native_child_id, raw_result_bytes). No background flag exists here.
Dispatcher = Callable[[str, StageEnvelope], Tuple[str, bytes]]


def _require_stage(stage: str) -> None:
    if stage not in STAGES:
        raise PipelineError(f"unknown-stage: {stage!r} is not one of {STAGES}.")


def render_command(stage: str, *, phase: Optional[int] = None) -> str:
    """Return the exact canonical command for one stage, nothing invented."""
    _require_stage(stage)
    if stage == "work":
        if not isinstance(phase, int) or phase < 1:
            raise PipelineError("work stage requires a positive phase number.")
        return STAGE_COMMANDS["work"].format(phase=phase)
    return STAGE_COMMANDS[stage]


def preparation_required_for(stage: str) -> bool:
    """Whether a stage requires a fresh preparation-only run first."""
    _require_stage(stage)
    return stage in PREPARATION_BEFORE


def resolve_activation(stage: str, previous: Optional[str] = None) -> None:
    """Stage activation guard: fresh preparation precedes applicable reviews."""
    _require_stage(stage)
    if previous is not None:
        _require_stage(previous)
    if stage in PREPARATION_BEFORE and previous != "prepare-publication":
        raise PipelineError(
            f"prepare-required: {stage!r} cannot activate directly; a fresh "
            "preparation-only stage must precede it."
        )
    if stage == "verify-pr" and previous != "publish":
        raise PipelineError(
            "publish-required: verify-pr follows the publication stage only; "
            "it never opens a batch on its own."
        )


def select_transition(
    stage: str,
    result: StageResult,
    *,
    has_findings: bool = False,
    verify_context: bool = False,
) -> Transition:
    """Closed transition table from one stage and result to the next decision."""
    _require_stage(stage)
    if result.stage != stage:
        raise PipelineError(
            f"stage-mismatch: result names {result.stage!r}, expected {stage!r}."
        )
    if result.decision is not None and result.status != "needs-input":
        raise PipelineError(
            "automatic-approval-rejected: a decision may ride only a needs-input "
            "result; a child can never self-approve."
        )
    if result.status == "needs-input":
        return Transition(None, "needs-input")
    if result.status != "succeeded":
        return Transition(None, "stop", reason=result.status)
    for test in result.tests:
        if test.status != "passed":
            raise PipelineError(
                f"exceptions-are-not-passes: test entry {test.command_id!r} "
                f"reported status {test.status!r} on a succeeded result; only "
                "passed test entries may advance the pipeline."
            )
    if stage == "work":
        return Transition("prepare-publication", "advance")
    if stage == "prepare-publication":
        return Transition("verify-review" if verify_context else "review", "advance")
    if stage == "review":
        return Transition("triage" if has_findings else "compound", "advance")
    if stage == "triage":
        return Transition("prepare-publication", "advance")
    if stage == "verify-review":
        return Transition("compound", "advance")
    if stage == "compound":
        return Transition("publish", "phase-4")
    if stage == "publish":
        return Transition("verify-pr", "advance")
    if stage == "verify-pr":
        return Transition(None, "batch-complete")
    return Transition(None, "stop", reason="no transition defined for this stage")


def assert_fresh_operation(previous_operations: frozenset, operation_id: str) -> None:
    """One fresh operation per dispatch; a reused operation ID stops."""
    if operation_id in previous_operations:
        raise PipelineError(
            f"operation-reused: {operation_id!r} was already dispatched; every "
            "stage runs under a fresh operation ID."
        )


def validate_approval_refs(envelope: StageEnvelope, known_refs: frozenset) -> None:
    """Every envelope approval reference must be current; stale refs stop."""
    unknown = sorted(set(envelope.approval_refs) - set(known_refs))
    if unknown:
        raise PipelineError(
            f"stale-approval: envelope carries unverified approval references "
            f"{unknown}; re-check identity and scope before effects."
        )


def correlate(
    child_id: str,
    *,
    envelope: StageEnvelope,
    result: StageResult,
) -> CorrelatedChild:
    """Correlate the returned child with the reserved operation, or stop."""
    if not isinstance(child_id, str) or not child_id:
        raise PipelineError("native-child-missing: the child ID is required.")
    if result.run_id != envelope.run_id:
        raise PipelineError(f"run-mismatch: {result.run_id!r} vs {envelope.run_id!r}.")
    if result.operation_id != envelope.operation_id:
        raise PipelineError(f"operation-mismatch: {result.operation_id!r} expected {envelope.operation_id!r}.")
    if result.stage != envelope.stage:
        raise PipelineError(f"stage-mismatch: {result.stage!r} differs from envelope {envelope.stage!r}.")
    return CorrelatedChild(child_id, result.operation_id, result)


def decision_handoff(result: StageResult) -> Optional[Decision]:
    """Convert a semantic decision to ``needs-input`` with exact options/scope."""
    if result.status != "needs-input":
        return None
    if result.decision is None:
        raise PipelineError(
            "needs-input-without-decision: needs-input must carry exact "
            "option labels and scope."
        )
    return result.decision


def substantiveness(result: StageResult) -> bool:
    """Whether the result reports content changes or executed tests."""
    return (
        result.change_manifest_hash is not None
        or result.head_before != result.head_after
        or bool(result.tests)
    )


def require_begin_effect(result: StageResult, *, effect_started: bool) -> None:
    """Require the one-way effect receipt before any substantive action."""
    if substantiveness(result) and not effect_started:
        raise PipelineError(
            "missing-begin-effect: substantive result without its one-way "
            "effect receipt."
        )


def propose_settlement(result: StageResult, *, effect_started: bool) -> str:
    """Zero-effect rule: only an effect-free acknowledged needs-input releases."""
    if result.status == "needs-input" and not effect_started and not substantiveness(result):
        return "released-no-effect"
    return "charged"


def effect_receipt_exists(coordination_root: Path, operation_id: str) -> bool:
    """Read-only probe of the one-way effect receipt for an operation."""
    try:
        secure_fs.secure_read_bytes(
            coordination_root,
            PurePosixPath(EFFECT_RELATIVE.format(op=operation_id)),
            max_bytes=MAX_MARKER_BYTES,
        )
    except (FileNotFoundError, secure_fs.SecureMutationError, OSError):
        return False
    return True


def run_foreground(
    *,
    command: str,
    envelope: StageEnvelope,
    dispatcher: Dispatcher,
    effect_started: bool = False,
    context_budget: Optional[ParentContextBudget] = None,
    frame_metadata: Optional[Mapping[str, str]] = None,
    frame_warnings: Sequence[str] = (),
) -> CorrelatedChild:
    """Dispatch one fresh foreground child and correlate its closed result.

    When a ``context_budget`` is supplied, the complete returned frame — the
    exact result bytes plus the parent's metadata and warnings — is measured
    and budget-checked before the result is accepted. A frame over the
    per-frame ceiling or a cumulative allowance that would be exceeded pauses
    with a typed error instead of truncating the frame or dispatching again.
    """
    child_id, raw = dispatcher(command, envelope)
    result = StageResult.parse(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
    if context_budget is not None:
        frame = measure_frame(
            raw if isinstance(raw, bytes) else raw.encode("utf-8"),
            metadata=frame_metadata or {},
            warnings=tuple(frame_warnings),
        )
        decision = budget_decision(frame, context_budget)
        if decision["decision"] != "dispatch":
            raise PipelineError(
                f"context-pause: {decision['reason']} (frame {decision['frame-bytes']} "
                f"bytes; remaining {decision['remaining-before']}). Pause before "
                "another dispatch; never truncate the returned frame."
            )
    correlated = correlate(child_id, envelope=envelope, result=result)
    require_begin_effect(result, effect_started=effect_started)
    return correlated


def settle_operation(
    marker: MarkerState,
    coordination_root: Path,
    *,
    owner_nonce: str,
    operation_id: str,
    result: StageResult,
    zero_effect_evidence: Sequence[str],
) -> MarkerState:
    """Settle the operation under the zero-effect rule through owned state."""
    started = effect_receipt_exists(coordination_root, operation_id)
    outcome = propose_settlement(result, effect_started=started)
    if outcome == "released-no-effect" and not zero_effect_evidence:
        raise PipelineError(
            "missing-zero-effect-evidence: a released reservation needs the "
            "parent's independent unchanged-state evidence."
        )
    return settle_stage(
        marker, coordination_root, owner_nonce=owner_nonce,
        operation_id=operation_id, outcome=outcome,
        evidence_refs=zero_effect_evidence,
    )
