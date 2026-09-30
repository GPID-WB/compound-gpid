"""Measurable parent context budgets (Phase 5, Step 14).

The parent measures each complete returned frame — the closed stage result
bytes plus its own metadata and any warnings — against two ceilings: 8192
bytes per frame and 65536 cumulative returned-frame bytes per primary parent
context. The complete stage JSON stays within 4096 UTF-8 bytes. Budget checks
run before another dispatch; exhaustion pauses instead of truncating a frame
or claiming a same-session fresh-context reset. A verified fresh primary
context resets only that context's returned-frame allowance: reservation,
repair-round, CI-round, usage-counter and deadline state live in other
control domains and never reset here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Tuple

from autopilot.contracts import (
    MAX_RESULT_BYTES,
    AutopilotError,
    PacketError,
    dumps_closed,
)

FRAME_BYTE_LIMIT = 8192
CONTEXT_ALLOWANCE_BYTES = 65536
STAGE_JSON_BYTES = MAX_RESULT_BYTES


class ContextBudgetError(AutopilotError):
    """A parent frame budget violation; pause, never truncate."""

    error_code = "autopilot-context-error"


@dataclass(frozen=True)
class ParentFrame:
    """One complete measured frame: payload plus metadata and warnings."""

    payload_bytes: bytes
    metadata: Mapping[str, str]
    warnings: Tuple[str, ...]

    def total_bytes(self) -> int:
        meta = json.dumps(dict(self.metadata), sort_keys=True).encode("utf-8")
        warn = json.dumps(list(self.warnings), sort_keys=True).encode("utf-8")
        return len(self.payload_bytes) + len(meta) + len(warn)


@dataclass(frozen=True)
class ParentContextBudget:
    """Cumulative returned-frame accounting for one primary parent context."""

    used: int = 0
    frame_limit: int = FRAME_BYTE_LIMIT
    allowance: int = CONTEXT_ALLOWANCE_BYTES

    def remaining(self) -> int:
        return max(0, self.allowance - self.used)

    def fresh_primary_context(self) -> "ParentContextBudget":
        """Reset only this context's returned-frame allowance.

        Reservation, repair-round, CI-round, usage-counter and deadline state
        are separate domains and never reset here; deadline changes require
        the explicitly approved extension transition.
        """
        return ParentContextBudget(
            used=0, frame_limit=self.frame_limit, allowance=self.allowance
        )


def measure_frame(
    payload_bytes: bytes,
    *,
    metadata: Mapping[str, str] = (),
    warnings: Tuple[str, ...] = (),
) -> ParentFrame:
    """Build one measured frame from exact returned bytes plus annotations."""
    return ParentFrame(bytes(payload_bytes), dict(metadata), tuple(warnings))


def require_stage_json(payload: Mapping) -> bytes:
    """Serialize the complete stage JSON within 4096 bytes; never truncate."""
    try:
        return dumps_closed(
            dict(payload), max_bytes=STAGE_JSON_BYTES, label="stage-json"
        )
    except PacketError as error:
        raise ContextBudgetError(f"stage-json-too-large: {error}") from error


def budget_decision(
    frame: ParentFrame, budget: ParentContextBudget
) -> dict:
    """Return the closed decision to run before another dispatch.

    The decision is always ``dispatch`` or ``pause``; pausing never truncates
    the frame and never mutates the budget.
    """
    frame_bytes = frame.total_bytes()
    if frame_bytes > budget.frame_limit:
        return {
            "decision": "pause",
            "reason": "frame-too-large",
            "frame-bytes": frame_bytes,
            "remaining-before": budget.remaining(),
            "remaining-after": budget.remaining(),
        }
    if frame_bytes > budget.remaining():
        return {
            "decision": "pause",
            "reason": "context-budget-exhausted",
            "frame-bytes": frame_bytes,
            "remaining-before": budget.remaining(),
            "remaining-after": budget.remaining(),
        }
    return {
        "decision": "dispatch",
        "reason": "within-budget",
        "frame-bytes": frame_bytes,
        "remaining-before": budget.remaining(),
        "remaining-after": budget.remaining() - frame_bytes,
    }


def charge(budget: ParentContextBudget, frame_bytes: int) -> ParentContextBudget:
    """Return the budget after charging one measured frame; pure."""
    return ParentContextBudget(
        used=budget.used + frame_bytes,
        frame_limit=budget.frame_limit,
        allowance=budget.allowance,
    )
