"""Bind a publication dispatch nonce to one actual run before lengthy seal reads."""

import re

from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.journal_checkpoint import atomic_publication_checkpoint

WORKFLOW = ".github/workflows/release-controller-publish.yml"


def register_publication(context, record, number, run):
    """Persist exact run identity, e.g. register_publication(ctx, r, number, run)."""
    ticket = record.evidence[f"publication-request-{number}"]
    try:
        if (
            type(run["id"]) is not int
            or run["id"] <= 0
            or run["run_attempt"] != 1
            or run["path"] != WORKFLOW
            or run["event"] != "workflow_dispatch"
            or run["head_branch"] != context.default
            or run["repository"]["id"] != context.policy.repository_id
            or not re.fullmatch(r"[0-9a-f]{40}", run["head_sha"])
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise ControllerError(
            "E_APPROVAL", "Publication run registration cannot be verified."
        ) from None
    value = {
        "run_id": run["id"],
        "run_attempt": 1,
        "nonce": ticket["nonce"],
        "controller_sha": run["head_sha"],
    }
    operation = f"publication-registration-{number}"
    if operation in record.evidence:
        if record.evidence[operation] != value:
            raise ControllerError(
                "E_APPROVAL", "Another run already owns this publication dispatch."
            )
        return record
    return atomic_publication_checkpoint(
        context.journal, record, operation, value, record.state
    )


def discover_publication(context, record, number):
    """Resolve a crashed pre-seal job by exact trusted run-name/path/nonce evidence."""
    title = (
        "release-publication "
        + record.evidence[f"publication-request-{number}"]["nonce"]
    )
    runs = inventory(
        context.api,
        "actions/workflows/release-controller-publish.yml/runs",
        "workflow_runs",
    )
    matches = [
        r
        for r in runs
        if r.get("display_title") == title
        and r.get("path") == WORKFLOW
        and r.get("event") == "workflow_dispatch"
    ]
    if len(matches) > 1:
        raise ControllerError(
            "E_APPROVAL", "Multiple trusted runs claim one publication nonce."
        )
    return (
        register_publication(context, record, number, matches[0]) if matches else record
    )
