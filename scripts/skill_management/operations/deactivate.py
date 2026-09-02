"""Explicit capability deactivation operation."""
from __future__ import annotations

from typing import Any, Mapping

from skill_management.operations._capability_change import handle_change
from skill_management.planning import OperationOutcome


def handle(*, context: Any, request: Mapping[str, Any]) -> OperationOutcome:
    """Plan or apply one explicit capability deactivation."""
    return handle_change(context=context, request=request, activate=False)
