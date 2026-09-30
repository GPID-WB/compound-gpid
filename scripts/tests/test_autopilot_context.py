"""Measurable parent context limits and read-only resume integration (Phase 5, Step 14).

Covers the parent frame budget: the complete returned frame (closed stage
result bytes plus parent metadata and warnings) is measured against an
8192-byte per-frame ceiling and a 65536-byte cumulative allowance per primary
parent context. Budget exhaustion pauses before another dispatch; it never
truncates and never resets within the same session. Also guards the read-only
``/cg-resume`` autopilot reconciliation wording in the canonical prompts,
templates and the context-loading contract.

Run: python -B -m pytest scripts/tests/test_autopilot_context.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_audit_context as audit
from autopilot.context import (
    CONTEXT_ALLOWANCE_BYTES,
    FRAME_BYTE_LIMIT,
    STAGE_JSON_BYTES,
    ContextBudgetError,
    ParentContextBudget,
    budget_decision,
    charge,
    measure_frame,
    require_stage_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def _norm(text: str) -> str:
    """Collapse whitespace runs so line-wrapped contract prose matches."""
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# Complete stage JSON limit
# ---------------------------------------------------------------------------


class TestStageJsonLimit:
    def test_complete_stage_json_stays_within_4096_bytes(self) -> None:
        payload = {"schema-version": 1, "status": "succeeded", "note": "x" * 3800}
        raw = require_stage_json(payload)
        assert len(raw) <= STAGE_JSON_BYTES

    def test_stage_json_one_byte_over_pauses_instead_of_truncating(self) -> None:
        payload = {"schema-version": 1, "status": "succeeded", "note": "x" * 5000}
        with pytest.raises(ContextBudgetError, match="stage-json-too-large"):
            require_stage_json(payload)


# ---------------------------------------------------------------------------
# Frame measurement
# ---------------------------------------------------------------------------


class TestFrameMeasurement:
    def test_frame_measures_payload_metadata_and_warnings(self) -> None:
        payload = b"{" + b" " * 100 + b"}"
        metadata = {"child-id": "ses-fresh-1"}
        warnings = ("compact-warning",)
        frame = measure_frame(payload, metadata=metadata, warnings=warnings)
        meta_bytes = json.dumps(metadata, sort_keys=True).encode("utf-8")
        warn_bytes = json.dumps(list(warnings), sort_keys=True).encode("utf-8")
        assert frame.total_bytes() == len(payload) + len(meta_bytes) + len(warn_bytes)
        assert frame.total_bytes() > len(payload)

    def test_oversized_header_or_warning_counts_toward_frame(self) -> None:
        payload = json.dumps({"status": "ok"}).encode("utf-8")
        frame = measure_frame(payload, metadata={"header": "h" * 9000}, warnings=())
        assert frame.total_bytes() > FRAME_BYTE_LIMIT


# ---------------------------------------------------------------------------
# Budget decisions before another dispatch
# ---------------------------------------------------------------------------


class TestBudgetDecision:
    def test_default_limits_are_the_documented_ceilings(self) -> None:
        assert FRAME_BYTE_LIMIT == 8192
        assert CONTEXT_ALLOWANCE_BYTES == 65536
        assert STAGE_JSON_BYTES == 4096

    def test_compact_dispatch_within_allowance(self) -> None:
        budget = ParentContextBudget()
        frame = measure_frame(json.dumps({"status": "ok"}).encode("utf-8"))
        decision = budget_decision(frame, budget)
        assert decision["decision"] == "dispatch"
        assert decision["reason"] == "within-budget"
        assert decision["frame-bytes"] == frame.total_bytes()

    def test_repeated_compact_stages_accumulate_and_pause(self) -> None:
        budget = ParentContextBudget()
        frame = measure_frame(json.dumps({"note": "n" * 3000}).encode("utf-8"))
        seen_pause = False
        for _ in range(40):
            decision = budget_decision(frame, budget)
            if decision["decision"] == "dispatch":
                budget = charge(budget, decision["frame-bytes"])
            else:
                seen_pause = True
                assert decision["reason"] == "context-budget-exhausted"
                break
        assert seen_pause

    def test_frame_over_ceiling_pauses_without_truncation(self) -> None:
        budget = ParentContextBudget()
        frame = measure_frame(
            b"x", metadata={"header": "h" * (FRAME_BYTE_LIMIT + 10)}, warnings=()
        )
        decision = budget_decision(frame, budget)
        assert decision["decision"] == "pause"
        assert decision["reason"] == "frame-too-large"

    def test_same_session_resume_does_not_reset_usage(self) -> None:
        budget = ParentContextBudget(used=CONTEXT_ALLOWANCE_BYTES - 10)
        frame = measure_frame(json.dumps({"note": "n" * 100}).encode("utf-8"))
        decision = budget_decision(frame, budget)
        assert decision["decision"] == "pause"
        assert decision["reason"] == "context-budget-exhausted"

    def test_fresh_primary_context_resets_only_the_allowance(self) -> None:
        budget = ParentContextBudget(used=60000, frame_limit=4096, allowance=65536)
        fresh = budget.fresh_primary_context()
        assert fresh.used == 0
        assert fresh.allowance == budget.allowance
        assert fresh.frame_limit == budget.frame_limit

    def test_decision_shape_is_closed(self) -> None:
        decision = budget_decision(measure_frame(b"{}"), ParentContextBudget())
        assert set(decision) == {
            "decision", "reason", "frame-bytes", "remaining-before", "remaining-after",
        }

    def test_charge_is_pure_and_bounded(self) -> None:
        budget = ParentContextBudget()
        charged = charge(budget, 100)
        assert budget.used == 0
        assert charged.used == 100
        assert charged.remaining() == CONTEXT_ALLOWANCE_BYTES - 100


# ---------------------------------------------------------------------------
# Read-only /cg-resume and contract wording guards
# ---------------------------------------------------------------------------


class TestPromptAndContractGuards:
    def test_cg_resume_recommends_exact_autopilot_resume_command(self) -> None:
        content = _read(".github/prompts/cg-resume.prompt.md")
        assert "/cg-autopilot --resume .cg-docs/active-state/current.json" in content

    def test_cg_resume_autopilot_reconciliation_precedes_phase_suggestions(self) -> None:
        content = _read(".github/prompts/cg-resume.prompt.md")
        assert "takes precedence" in content
        assert "phase-only" in content

    def test_cg_resume_never_writes_private_control_event(self) -> None:
        content = _norm(_read(".github/prompts/cg-resume.prompt.md"))
        assert "never writes the private control event" in content
        assert "separately approved parent helper transition" in content
        assert "read-only" in content.lower()

    def test_cg_resume_rejects_auto_and_model_assignment(self) -> None:
        content = _norm(_read(".github/prompts/cg-resume.prompt.md"))
        assert "--auto" in content
        assert "model assignment" in content

    def test_resume_templates_carry_autopilot_reconciliation_block(self) -> None:
        content = _norm(_read(".github/prompts/resume-templates.md"))
        assert "Unfinished Autopilot Run" in content
        assert "/cg-autopilot --resume .cg-docs/active-state/current.json" in content
        assert "never writes the private control event" in content

    def test_context_contract_records_numeric_limits(self) -> None:
        content = _norm(_read(".github/shared/context-loading.contract.md"))
        assert "4096 UTF-8 bytes" in content
        assert "8192 bytes" in content
        assert "65536 returned-frame bytes" in content

    def test_context_contract_pause_not_truncate(self) -> None:
        content = _norm(_read(".github/shared/context-loading.contract.md"))
        assert "pauses before the next dispatch" in content
        assert "never truncates" in content
        assert (
            "fresh primary context resets only that context's returned-frame allowance"
            in content
        )
        assert "extension transition" in content

    def test_stage_contract_forbids_full_logs_in_parent_packets(self) -> None:
        content = _read(".github/shared/autopilot-stage.contract.md")
        assert "never full logs" in content
        assert "65536 cumulative bytes" in content

    def test_audit_registry_registers_the_autopilot_workflow(self) -> None:
        commands = [row["workflow"] for row in audit.WORKFLOW_REGISTRY]
        assert "/cg-autopilot" in commands
