"""Bounded dispatch recovery; the Pages queue does not grant authority."""

import re
import time
from urllib.parse import quote

from cg_release.composition_journal import CompositionJournal
from cg_release.events import ControllerError
from cg_release.hook_authority import authorize_hooks
from cg_release.models import canonical_bytes


def verify_identity(run, sealed, run_id=None) -> None:
    """Check exact remote dispatch identity, e.g. verify_identity(run, ticket, 12)."""
    if (
        not isinstance(run, dict)
        or type(run.get("id")) is not int
        or run["id"] <= 0
        or (run_id is not None and run["id"] != run_id)
        or run.get("path") != sealed["workflow_path"]
        or run.get("event") != "workflow_dispatch"
        or run.get("head_sha") != sealed["controller_sha"]
        or run.get("head_branch") != sealed["controller_ref"]
        or type(run.get("run_attempt")) is not int
        or run["run_attempt"] != 1
        or run.get("repository", {}).get("id") != sealed["repository_id"]
    ):
        raise ControllerError("E_HOOK", "Composition run identity is not verified.")


def recover_dispatch(context, record, item, *, actor_id=None):
    """Discover sealed dispatches, e.g. recover_dispatch(ctx, release, composition).

    Returns: (updated record, run or None, replacement_safe). A missing registration
    is never success. Complete bounded inventories separated by a propagation window
    prove absence; a superseded ticket also rejects all late worker effects.
    Raises ControllerError on ambiguous/unreadable evidence. Only journal writes occur.
    """
    store, api, sealed = CompositionJournal(context.journal), context.api, item.ticket
    actor_id = sealed["authority_actor_id"] if actor_id is None else actor_id
    registration = item.evidence.get("registration")
    run = None
    if registration:
        try:
            run = api.get(f"actions/runs/{registration['run_id']}")
            verify_identity(run, sealed, registration["run_id"])
        except ControllerError as error:
            if error.code != "E_NOT_FOUND":
                raise
    if run is None:
        rows = api.composition_runs(sealed["workflow_path"], since=sealed["created_at"])
        matches = [
            row
            for row in rows
            if row.get("display_title") == "release-docs " + sealed["nonce"]
        ]
        if len(matches) > 1:
            raise ControllerError(
                "E_HOOK", "Composition dispatch discovery is ambiguous."
            )
        run = matches[0] if matches else None
        if run:
            verify_identity(
                run, sealed, registration["run_id"] if registration else None
            )
        else:
            now = time.time()
            if now < sealed["created_at"] + 120:
                return item, None, False
            first = item.evidence.get("absence-first")
            if first is None:
                authorize_hooks(context, record, actor_id, fresh=True)
                # Keep the dispatch intent until absence is confirmed on another pass.
                if item.intent is not None:
                    item = store.save(item, "dispatch", {"uncertain": True})
                    authorize_hooks(context, record, actor_id, fresh=True)
                item = store.save(
                    item,
                    "absence-first",
                    {"observed_at": now, "inventory_count": len(rows)},
                )
                return item, None, False
            if now < first["observed_at"] + 120:
                return item, None, False
            authorize_hooks(context, record, actor_id, fresh=True)
            if "absence" in item.evidence:
                return item, None, True
            item = store.save(
                item,
                "absence",
                {
                    "first": first["observed_at"],
                    "observed_at": now,
                    "inventory_count": len(rows),
                },
            )
            return item, None, True
    if run.get("status") != "completed":
        return item, run, False
    if not isinstance(run.get("conclusion"), str):
        raise ControllerError("E_HOOK", "Terminal dispatch lacks a conclusion.")
    authorize_hooks(context, record, actor_id, fresh=True)
    item = store.save(
        item, "terminal", {"run_id": run["id"], "conclusion": run["conclusion"]}
    )
    return item, run, True


def dispatch(context, record, item) -> None:
    """Write one sealed dispatch, e.g. dispatch(ctx, release, composition).

    Returns None (pending), never completion. Raises E_DISPATCH_UNKNOWN after an
    uncertain response; the next pass uses bounded discovery before replacement.
    Fresh authority precedes intent and remote POST. No source commands execute.
    """
    api, sealed = context.api, item.ticket
    payload = {
        "ref": sealed["controller_ref"],
        "inputs": {"request_id": record.request_id, "nonce": sealed["nonce"]},
    }
    authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    store = CompositionJournal(context.journal)
    item = store.intent(item, payload)
    # Durable intent is an intervening remote operation, not a permission lease.
    authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    result = api.runner(
        "gh",
        [
            "api",
            "--method",
            "POST",
            "--hostname",
            api.host,
            "--include",
            "--input",
            "-",
            f"repos/{api.slug}/actions/workflows/"
            f"{quote(sealed['workflow_path'], safe='')}/dispatches",
        ],
        cwd=api.cwd,
        timeout=min(api.read_seconds, api.remaining()),
        allow_failure=True,
        input_text=canonical_bytes(payload).decode(),
    )
    if result.returncode or not re.match(r"HTTP/[0-9.]+ 204(?: |\r?\n)", result.stdout):
        raise ControllerError(
            "E_DISPATCH_UNKNOWN",
            "Discover the sealed composition run before dispatch replay.",
        )
    authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    store.save(item, "dispatch", payload)
