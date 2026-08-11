"""Human and JSON renderers for readiness results."""
from __future__ import annotations

import json

from .contract import EXIT_API, EXIT_CONFIG, EXIT_NOT_READY, EXIT_READY, ReadinessResult


def result_to_dict(result: ReadinessResult) -> dict:
    """Convert a result to the stable machine-readable JSON schema.

    Args:
        result: Validator result to serialize.

    Returns:
        A JSON-compatible dictionary with rules, failed rules, state, and
        documented exit metadata.

    Example:
        ``payload = result_to_dict(result)`` exposes ``payload["exitCode"]``.
    """
    failed = [
        {"id": rule.id, "name": rule.name, "detail": rule.detail}
        for rule in result.rules if not rule.passed
    ]
    if result.exit_code == EXIT_READY:
        summary = "READY"
    elif result.exit_code == EXIT_NOT_READY:
        summary = f"NOT READY — {len(failed)} rule(s) failed"
    else:
        summary = f"CANNOT COMPLETE — {result.exit_reason}"
    return {
        "issue": result.issue,
        "ready": result.ready,
        "dryRun": result.dry_run,
        "exitCode": result.exit_code,
        "exitReason": result.exit_reason,
        "summary": summary,
        "rules": [
            {"id": rule.id, "name": rule.name, "passed": rule.passed, "detail": rule.detail}
            for rule in result.rules
        ],
        "failedRules": failed,
        "state": result.state,
        "errors": result.errors,
    }


def render_json(result: ReadinessResult) -> str:
    """Render one result as indented JSON text.

    Args:
        result: Validator result to render.

    Returns:
        A JSON object string without a trailing newline.

    Example:
        ``render_json(result).startswith("{")`` is ``True``.
    """
    return json.dumps(result_to_dict(result), indent=2, sort_keys=False)


def render_human(result: ReadinessResult) -> str:
    """Render one result as concise human-readable text.

    Args:
        result: Validator result to render.

    Returns:
        Human-readable status, exit code, errors, failed rules, and state.

    Example:
        ``print(render_human(result))`` prints the read-only verdict.
    """
    label = "READY" if result.ready else {
        EXIT_NOT_READY: "NOT READY",
        EXIT_CONFIG: "CANNOT COMPLETE (config)",
        EXIT_API: "CANNOT COMPLETE (api/network)",
    }.get(result.exit_code, "NOT READY")
    lines = [label if result.issue is None else f"Issue #{result.issue}: {label}"]
    lines.append(f"Exit code: {result.exit_code} ({result.exit_reason})")
    lines.append(f"Dry-run: {result.dry_run} (validator is read-only)")
    if result.errors:
        lines.extend(["", "Errors:"])
        lines.extend(f"  [{error['type']}] {error['message']}" for error in result.errors)
    failed = [rule for rule in result.rules if not rule.passed]
    if failed:
        lines.extend(["", "Failed rules:"])
        lines.extend(f"  {rule.id}  {rule.name}  - {rule.detail}" for rule in failed)
    if result.state:
        lines.extend([
            "", "State:",
            f"  issue state: {result.state.get('issueState')}",
            f"  project status: {result.state.get('projectStatus')}",
            f"  open closing PRs: {len(result.state.get('openClosingPRs', []))}",
            f"  copilot assigned: {result.state.get('copilotAssigned')}",
            f"  assignees: {result.state.get('assignees')}",
        ])
    lines.extend(["", "Passing validation does NOT assign Copilot or change Project status."])
    return "\n".join(lines)
