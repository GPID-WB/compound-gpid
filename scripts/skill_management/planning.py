"""Side-effect-free result and digest primitives shared by operation modules."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple

from .contracts import ContractFinding, EXIT_CONTRACT, EXIT_SUCCESS, canonical_json_bytes


@dataclass(frozen=True)
class OperationOutcome:
    """Handler output before the dispatcher adds the common result envelope."""

    changed: bool = False
    data: Mapping[str, Any] = field(default_factory=dict)
    actions: Tuple[Mapping[str, Any], ...] = ()
    findings: Tuple[ContractFinding, ...] = ()
    plan_digest: Optional[str] = None
    manifest_health: Optional[str] = None
    exit_code: Optional[int] = None


def plan_digest(bound_inputs: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of deterministic normalized plan inputs."""
    return hashlib.sha256(canonical_json_bytes(bound_inputs)).hexdigest()


def result_envelope(
    operation: str,
    phase: str,
    role: str,
    outcome: OperationOutcome,
) -> dict:
    """Build one deterministic common result envelope from a handler outcome."""
    findings = tuple(sorted(outcome.findings, key=lambda item: (item.path, item.code)))
    has_error = any(item.severity == "error" for item in findings)
    exit_code = outcome.exit_code
    if exit_code is None or (has_error and exit_code == EXIT_SUCCESS):
        exit_code = EXIT_CONTRACT if has_error else EXIT_SUCCESS
    result = {
        "schema": "cg-skill-result-v1",
        "ok": exit_code == EXIT_SUCCESS,
        "exitCode": exit_code,
        "operation": operation,
        "phase": phase,
        "role": role,
        "changed": outcome.changed,
        "actions": [dict(action) for action in outcome.actions],
        "findings": [item.to_dict() for item in findings],
        "data": dict(outcome.data),
    }
    if outcome.plan_digest is not None:
        result["planDigest"] = outcome.plan_digest
    if outcome.manifest_health is not None:
        result["manifestHealth"] = outcome.manifest_health
    return result
