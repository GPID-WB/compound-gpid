"""Durable build tickets, one-shot dispatch, and trusted pre-source registration."""

import re
from urllib.parse import quote

from cg_release.build_evidence import reuse_key
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_checkpoint import atomic_build_checkpoint
from cg_release.models import canonical_bytes


def ticket(record, nonce: str | None = None) -> tuple[int, dict]:
    """Read a unique current sealed build ticket, e.g. ticket(record, nonce)."""
    matches = [
        (int(key.removeprefix("build-request-")), value)
        for key, value in record.evidence.items()
        if re.fullmatch(r"build-request-[1-9][0-9]*", key)
        and (nonce is None or value.get("dispatch_nonce") == nonce)
    ]
    if not matches or (nonce is not None and len(matches) != 1):
        raise ControllerError(
            "E_BUILD_REQUEST", "Sealed build request is missing or ambiguous."
        )
    number, sealed = max(matches)
    reuse_key(sealed)
    return number, sealed


def register_build(
    context, request_id: str, nonce: str, environment: dict, *, before_write=None
) -> dict:
    """Claim one actual trusted run before source execution, e.g. in registration job.

    Context must be a verified writable protected-control context. The entry point
    separately verifies installed pins and actual workflow authority. Duplicate or
    interrupted claims cannot grant another source job accepted evidence.
    The trusted worker supplies before_write for each separate reconciliation and
    registration operation. Storage-only callers do not supply authorization proof.
    """
    record = context.journal.get(request_id)
    number, sealed = ticket(record, nonce)
    key = f"build-registration-{number}"
    try:
        run_id = int(environment["GITHUB_RUN_ID"])
        run = context.api.get(f"actions/runs/{run_id}")
        if (
            record.state != "building"
            or key in record.evidence
            or environment["GITHUB_ACTIONS"] != "true"
            or environment["GITHUB_RUN_ATTEMPT"] != "1"
            or environment["GITHUB_SHA"] != sealed["controller_sha"]
            or context.policy_sha != sealed["controller_sha"]
            or environment["GITHUB_REF"] != "refs/heads/" + sealed["controller_ref"]
            or environment["GITHUB_WORKFLOW_REF"]
            != (
                f"{context.api.slug}/{sealed['workflow_path']}"
                f"@refs/heads/{sealed['controller_ref']}"
            )
            or run["id"] != run_id
            or type(run["id"]) is not int
            or run_id <= 0
            or type(run["run_attempt"]) is not int
            or run["run_attempt"] != 1
            or run["event"] != "workflow_dispatch"
            or run["head_sha"] != sealed["controller_sha"]
            or run["head_branch"] != sealed["controller_ref"]
            or run["path"] != sealed["workflow_path"]
            or run["repository"]["id"] != sealed["repository_id"]
            or run["status"] != "in_progress"
        ):
            raise ValueError
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ControllerError(
            "E_BUILD_REGISTRATION",
            "Trusted build run or unique claim cannot be verified.",
        ) from None
    evidence = {
        "build_digest": reuse_key(sealed),
        "dispatch_nonce": nonce,
        "run_id": run_id,
        "run_attempt": 1,
        "release_sha": sealed["release_sha"],
    }
    if (
        record.intent is not None
        and record.intent["operation"] == f"build-dispatch-{number}"
    ):
        payload = {
            "ref": sealed["controller_ref"],
            "inputs": {"build_request": request_id, "dispatch_nonce": nonce},
        }
        if before_write is not None:
            before_write()
        context.journal.result(
            request_id,
            f"build-dispatch-{number}",
            digest(payload),
            "building",
            evidence=payload,
        )
    # Dispatch reconciliation can update the record. Re-read before the one-shot
    # claim; the atomic append still compares the complete current checkpoint.
    current = context.journal.get(request_id)
    if (
        current.evidence.get(f"build-request-{number}") != sealed
        or key in current.evidence
    ):
        raise ControllerError(
            "E_BUILD_REGISTRATION", "Build ticket or registration claim changed."
        )
    if before_write is not None:
        before_write()
    atomic_build_checkpoint(context.journal, current, key, evidence, "building")
    return evidence


def dispatch_build(context, record, *, nonce: str | None = None) -> None:
    """Attempt one trusted default-ref dispatch; unknown outcomes are never replayed.

    Example: dispatch_build(context, building_record). Registration is the durable
    proof of remote acceptance. Pending dispatch remains explicit until it arrives.
    """
    number, sealed = ticket(record, nonce)
    operation = f"build-dispatch-{number}"
    if (
        operation in record.evidence
        or f"build-registration-{number}" in record.evidence
    ):
        return
    if record.intent is not None:
        if record.intent["operation"] == operation:
            raise ControllerError(
                "E_DISPATCH_UNKNOWN",
                "Dispatch outcome is unknown; await registration, do not replay.",
            )
        raise ControllerError(
            "E_BUILD_STATE", "Another unresolved intent blocks dispatch."
        )
    payload = {
        "ref": sealed["controller_ref"],
        "inputs": {
            "build_request": record.request_id,
            "dispatch_nonce": sealed["dispatch_nonce"],
        },
    }
    identity = digest(payload)
    context.journal.intent(record.request_id, operation, identity)
    try:
        result = context.api.runner(
            "gh",
            [
                "api",
                "--method",
                "POST",
                "--hostname",
                context.api.host,
                "--include",
                "--input",
                "-",
                f"repos/{context.api.slug}/actions/workflows/"
                f"{quote(sealed['workflow_path'], safe='')}/dispatches",
            ],
            cwd=context.api.cwd,
            timeout=min(context.api.read_seconds, context.api.remaining()),
            allow_failure=True,
            input_text=canonical_bytes(payload).decode(),
        )
        if result.returncode or not re.match(
            r"HTTP/[0-9.]+ 204(?: |\r?\n)", result.stdout
        ):
            raise ValueError
    except (ControllerError, ValueError):
        raise ControllerError(
            "E_DISPATCH_UNKNOWN",
            "Build dispatch requires remote registration reconciliation.",
        ) from None
    context.journal.result(
        record.request_id, operation, identity, "building", evidence=payload
    )
