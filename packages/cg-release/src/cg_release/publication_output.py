"""Bounded workflow summaries and context-preserving errors without recovery reads."""

import time
from pathlib import Path

from cg_release.admission import Locator
from cg_release.events import ControllerError
from cg_release.models import Event, canonical_bytes


def write_seal_summary(environment, seal, url):
    """Expose approval evidence, e.g. write_seal_summary(env, seal, url)."""
    with Path(environment["GITHUB_STEP_SUMMARY"]).open(
        "a", encoding="utf-8", newline="\n"
    ) as output:
        output.write(
            "## Sealed Publication\n\n"
            + url
            + "\n\nDigest: `"
            + seal["digest"]
            + "`\n\n```json\n"
            + canonical_bytes(seal["inputs"]).decode()
            + "\n```\n"
        )
    with Path(environment["GITHUB_OUTPUT"]).open(
        "a", encoding="utf-8", newline="\n"
    ) as output:
        output.write(f"environment={seal['environment']}\nevidence_url={url}\n")


def error_event(args, context, record, error, started):
    """Return only safe identity and the last fully verified local observation."""
    request_id = None
    if args is not None:
        try:
            Locator.decode(args.request_id)
            request_id = args.request_id
        except ControllerError:
            pass
    if context is not None and request_id is not None:
        record = context.journal.last_verified_records.get(request_id, record)
    operation = getattr(args, "operation", None)
    return Event(
        kind="error",
        code=error.code,
        message=error.message,
        request_id=request_id,
        version=record.request.version if record is not None else None,
        step=(record.intent["operation"] if record.intent else record.checkpoint)
        if record is not None
        else operation,
        expected="awaiting-approval"
        if operation == "seal"
        else "published"
        if operation == "publish"
        else None,
        observed=record.state if record is not None else "unknown",
        elapsed_seconds=max(0.0, time.monotonic() - started),
        next_action=(
            "Run cg-release status for this request, then cg-release resume "
            "to reconcile verified remote state; do not replay a write blindly."
        )
        if request_id
        else "Correct the invocation and check trusted workflow inputs.",
    )
