"""Dispatch result serialization (mirrors ``issues.render`` for readiness)."""
from __future__ import annotations

import json

from .dispatch_contract import DispatchResult, EXIT_REASONS_DISPATCH


def result_to_dict(result: DispatchResult) -> dict:
    """Convert a dispatcher result to the stable JSON schema.

    Args:
        result: The dispatcher result to serialize.

    Returns:
        A JSON-compatible dictionary with outcome, exit metadata, the ordered
        mutation log, and messages.

    Example:
        ``payload = result_to_dict(result)`` exposes ``payload["exitCode"]``.
    """
    return {
        "issue": result.issue,
        "outcome": result.outcome,
        "dryRun": result.dry_run,
        "exitCode": result.exit_code,
        "exitReason": EXIT_REASONS_DISPATCH.get(result.exit_code, "unknown"),
        "mutations": list(result.mutation_log),
        "messages": list(result.messages),
    }


def render_json(result: DispatchResult) -> str:
    """Render a dispatcher result as indented JSON text.

    Args:
        result: Dispatcher result to serialize.

    Returns:
        An indented JSON object string without a trailing newline.

    Example:
        ``render_json(result).startswith("{")`` is ``True``.
    """
    return json.dumps(result_to_dict(result), indent=2, sort_keys=False)


def render_human(result: DispatchResult) -> str:
    """Render a dispatcher result as concise human-readable text.

    Args:
        result: The dispatcher result to render.

    Returns:
        Human-readable outcome, exit code, mutation log, and messages.

    Example:
        ``print(render_human(result))`` prints the structured dispatch verdict.
    """
    lines = [
        f"Issue #{result.issue}: {result.outcome}"
        if result.issue is not None
        else f"Dispatch: {result.outcome}",
        f"Exit code: {result.exit_code} ({EXIT_REASONS_DISPATCH.get(result.exit_code, 'unknown')})",
        f"Dry-run: {result.dry_run}",
    ]
    if result.mutation_log:
        lines.append("Mutations: " + ", ".join(result.mutation_log))
    lines.extend(result.messages)
    return "\n".join(lines)
