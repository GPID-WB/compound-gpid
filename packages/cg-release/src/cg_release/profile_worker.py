"""Trusted composition worker. Source execution belongs only to the dev-preview job."""

import argparse
import hashlib
import json
import os
import re
import time
from pathlib import Path

from cg_release.composition_journal import CompositionJournal
from cg_release.context import context_for
from cg_release.controller import verify_run
from cg_release.events import ControllerError, emit_event
from cg_release.hook_authority import authorize_hooks
from cg_release.journal import digest
from cg_release.models import Event, canonical_bytes
from cg_release.profile_deploy import authorize_deployment
from cg_release.profile_dev_input import acquire_dev
from cg_release.profile_docs import selection
from cg_release.profile_process import run_snapshot
from cg_release.profile_selection import acquire


def current_composition(record, nonce, *, journal):
    """Read one current record, e.g. current_composition(r, nonce, journal=j).

    Returns: One exact Composition. Raises ControllerError for an absent,
    superseded, malformed or foreign ticket. Reads verified history only.
    """
    records = CompositionJournal(journal).records()
    matches = [
        item
        for item in records[-1:]
        if item.ticket.get("nonce") == nonce and item.request_id == record.request_id
    ]
    if (
        len(matches) != 1
        or record.state not in {"published", "complete"}
        or not record.published
    ):
        raise ControllerError(
            "E_HOOK", "A unique published composition request is required."
        )
    sealed = matches[0].ticket
    if (
        type(sealed.get("authority_actor_id")) is not int
        or sealed["authority_actor_id"] <= 0
        or not isinstance(sealed.get("policy_digest"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", sealed.get("policy_digest", ""))
    ):
        raise ControllerError(
            "E_HOOK_POLICY", "Composition lacks sealed policy and actor authority."
        )
    return matches[0]


def current_ticket(record, nonce, *, journal):
    """Return (number, ticket), e.g. current_ticket(r, n, journal=j)."""
    item = current_composition(record, nonce, journal=journal)
    return item.number, item.ticket


def register(context, record, nonce, environment):
    """Register a run before source work, e.g. register(ctx, record, nonce, env).

    Args: trusted context, published parent, nonce and actual GitHub environment.
    Returns: Sealed ticket. Raises ControllerError on authority, policy, run or
    repeated claim conflict. Appends dispatch reconciliation and registration only.
    """
    item = current_composition(record, nonce, journal=context.journal)
    sealed = item.ticket
    store = CompositionJournal(context.journal)
    authorize_hooks(context, record, sealed.get("authority_actor_id"), fresh=True)
    if sealed.get("policy_digest") != digest(context.policy):
        raise ControllerError("E_HOOK_POLICY", "Composition policy binding changed.")
    verify_run(context, environment, workflow=sealed["workflow_path"])
    run_id = int(environment["GITHUB_RUN_ID"])
    run = context.api.get(f"actions/runs/{run_id}")
    if (
        run.get("event") != "workflow_dispatch"
        or environment["GITHUB_RUN_ATTEMPT"] != "1"
        or context.policy_sha != sealed["controller_sha"]
        or "registration" in item.evidence
    ):
        raise ControllerError(
            "E_HOOK", "Composition run was substituted or already registered."
        )
    payload = {
        "ref": context.default,
        "inputs": {"request_id": record.request_id, "nonce": nonce},
    }
    authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    if item.intent is not None:
        if item.intent != payload:
            raise ControllerError("E_HOOK", "Composition dispatch intent changed.")
        item = store.save(item, "dispatch", payload)
        authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    store.save(
        item, "registration", {"run_id": run_id, "request_digest": digest(sealed)}
    )
    return sealed


def compose(context, record, nonce, root: Path):
    """Compose approved data, e.g. compose(ctx, record, nonce, isolated_root).

    Returns: Exact manifest/run/selection identity. All inputs are verified before
    local output creation. Raises ControllerError on authority, data or freshness
    changes. Only installed data helpers execute, with bounded credential-free I/O;
    the final composition identity is appended to the independent journal.
    """
    item = current_composition(record, nonce, journal=context.journal)
    sealed = item.ticket
    store = CompositionJournal(context.journal)
    authorize_hooks(context, record, sealed.get("authority_actor_id"), fresh=True)
    if sealed["policy_digest"] != digest(context.policy):
        raise ControllerError("E_HOOK_POLICY", "Composition policy binding changed.")
    run_id = int(os.environ["GITHUB_RUN_ID"])
    registration = item.evidence.get("registration")
    if registration != {"run_id": run_id, "request_digest": digest(sealed)}:
        raise ControllerError(
            "E_HOOK", "Composition lacks exact source/run registration."
        )
    selected, stable = selection(context)
    if (
        selected != sealed["releases"]
        or stable != sealed["stable_tag"]
        or context.api.branch("dev")["commit"]["sha"] != sealed["dev_sha"]
    ):
        raise ControllerError(
            "E_DOCS_STALE",
            "Refresh mutable composition only; release assets remain frozen.",
        )
    roots = []
    dev_raw = acquire_dev(context, sealed, run_id, root)
    acquired = acquire(context.api, selected)
    current_ticket(record, nonce, journal=context.journal)
    authorize_hooks(context, record, sealed["authority_actor_id"], fresh=True)
    root.mkdir(parents=True, exist_ok=False)
    for index, (snapshot, raw) in enumerate(acquired):
        source = root / f"release-{index}.json"
        source.write_bytes(raw)
        target = root / f"release-{index}"
        run_snapshot(
            "import",
            [str(source), str(target)],
            cwd=root,
            timeout=min(120, context.api.remaining()),
        )
        manifest = json.loads((target / ".docs-snapshot.json").read_text())
        if (
            manifest["tag"] != snapshot["tag"]
            or manifest["sha"] != snapshot["sha"]
            or manifest["kind"] != "release"
        ):
            raise ControllerError(
                "E_HOOK", "Snapshot source differs from published release."
            )
        roots.append(str(target))
    dev = root / "dev"
    source = root / "dev.json"
    source.write_bytes(dev_raw)
    run_snapshot(
        "import",
        [str(source), str(dev)],
        cwd=root,
        timeout=min(120, context.api.remaining()),
    )
    manifest = json.loads((dev / ".docs-snapshot.json").read_text())
    if (
        manifest["sha"] != sealed["dev_sha"]
        or manifest["runId"] != run_id
        or manifest["runAttempt"] != 1
        or manifest["kind"] != "dev"
    ):
        raise ControllerError("E_HOOK", "Mutable preview source/run identity differs.")
    options = {
        "releases": roots,
        "dev": str(dev),
        "out": str(root / "deployment"),
        "composerRevision": sealed["controller_sha"],
        "currentDevSha": sealed["dev_sha"],
        "stableTag": stable,
    }
    config = root / "compose.json"
    config.write_bytes(canonical_bytes(options))
    run_snapshot(
        "compose", [str(config)], cwd=root, timeout=min(120, context.api.remaining())
    )
    raw = (root / "deployment/.docs-deployment.json").read_bytes()
    result = {
        "request_digest": digest(sealed),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "run_id": run_id,
        "dev_sha": sealed["dev_sha"],
        "stable_tag": stable,
    }
    current_ticket(record, nonce, journal=context.journal)
    authorize_hooks(context, record, sealed.get("authority_actor_id"), fresh=True)
    store.save(item, "composition", result)
    return result


def main(argv=None):
    """Run a trusted worker, e.g. profile_worker register --request-id ID --nonce NONCE.

    All operations require --request-id, --nonce, verified GITHUB_ACTIONS,
    GITHUB_RUN_ID/ATTEMPT, GITHUB_SHA/REF/WORKFLOW_REF/ACTOR_ID and the installed
    CG_RELEASE_CONTROLLER_REVISION/CG_RELEASE_WHEEL_SHA256 pin. Context uses the
    read/control GitHub credential channel, never a publishing token. register
    appends one source-run binding; compose additionally requires --root (new
    isolated output directory) and reads exact dev and release artifacts before
    writing static output and composition evidence. authorize-deploy is read-only
    and requires EXPECTED_MANIFEST from the trusted composer after artifact upload.
    Success appends available dev_sha/stable_tag/manifest_sha256 to GITHUB_OUTPUT
    and exits 0. Validation/I/O failures emit a redacted JSON error and exit 1;
    invalid arguments exit 2. No operation deploys Pages or publishes a release.
    """
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "operation", choices=["register", "compose", "authorize-deploy"]
        )
        parser.add_argument("--request-id", required=True)
        parser.add_argument("--nonce", required=True)
        parser.add_argument("--root", type=Path)
        args = parser.parse_args(argv)
        context = context_for(
            args.request_id,
            deadline=time.monotonic() + 120,
            writable=args.operation != "authorize-deploy",
        )
        verify_run(
            context, dict(os.environ), workflow=context.policy.profile.docs_workflow
        )
        record = context.journal.get(args.request_id)
        if args.operation == "authorize-deploy":
            result = authorize_deployment(context, record, args.nonce, dict(os.environ))
        elif args.operation == "register":
            result = register(context, record, args.nonce, dict(os.environ))
        else:
            if args.root is None:
                raise ControllerError(
                    "E_HOOK", "Composition requires an isolated root."
                )
            result = compose(context, record, args.nonce, args.root.absolute())
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            for name in ("dev_sha", "stable_tag", "manifest_sha256"):
                if name in result:
                    output.write(f"{name}={result[name]}\n")
        return 0
    except (ControllerError, ValueError, OSError, KeyError) as error:
        emit_event(
            Event(
                kind="error",
                code=getattr(error, "code", "E_HOOK"),
                message="GPID trusted hook failed; inspect exact evidence.",
            ),
            json_output=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
