"""Trusted default-ref admission worker; never execute target source."""

import hashlib
import os
import time
from pathlib import Path
from urllib.parse import urlsplit

from cg_release.admission import InboxBody, Locator, discover
from cg_release.authority import actor_role
from cg_release.cli import ContractParser
from cg_release.events import ControllerError, emit_event
from cg_release.inbox import GitHubInbox
from cg_release.lifecycle import seal
from cg_release.models import Event, load_record
from cg_release.queue import scan
from cg_release.replay import revalidate
from cg_release.runtime import Context, context_for
from cg_release.stage_router import advance

WORKFLOW = ".github/workflows/release-controller.yml"


def verify_run(
    context: Context, environment: dict[str, str], *, workflow: str = WORKFLOW
) -> tuple[int, str]:
    """Bind execution to exact default-ref workflow/run/actor and installed code pins.

    Example: verify_run(context, dict(os.environ)). Environment alone is not evidence;
    Run API, protected environment, signed writes, and ref rules are required.
    """
    try:
        run_id, actor_id = (
            int(environment["GITHUB_RUN_ID"]),
            int(environment["GITHUB_ACTOR_ID"]),
        )
        if (
            environment["GITHUB_ACTIONS"] != "true"
            or environment["GITHUB_RUN_ATTEMPT"] != "1"
            or environment["GITHUB_SHA"] != context.policy_sha
            or environment["GITHUB_REF"] != "refs/heads/" + context.default
            or environment["GITHUB_WORKFLOW_REF"]
            != f"{context.api.slug}/{workflow}@refs/heads/{context.default}"
            or environment["CG_RELEASE_CONTROLLER_REVISION"]
            != context.policy.controller.revision
            or environment["CG_RELEASE_WHEEL_SHA256"]
            != context.policy.controller.wheel_digest
        ):
            raise ValueError
        run = context.api.get(f"actions/runs/{run_id}")
        if (
            type(run["id"]) is not int
            or run["id"] != run_id
            or run["run_attempt"] != 1
            or run["head_sha"] != context.policy_sha
            or run["head_branch"] != context.default
            or run["path"] != workflow
            or run["event"] not in {"issues", "workflow_dispatch", "schedule"}
            or run["repository"]["id"] != context.policy.repository_id
            or type(run["actor"]["id"]) is not int
            or run["actor"]["id"] != actor_id
            or run["status"] != "in_progress"
        ):
            raise ValueError
        if actor_id != getattr(getattr(context.journal, "store", None), "bot_id", None):
            actor_role(context.api, actor_id)
        return actor_id, run["event"]
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_CONTROLLER_TRUST",
            "Trusted workflow/run/installation identity is not verified.",
        ) from None


def reconcile(
    context: Context,
    request_id: str,
    *,
    inbox=None,
    resuming_actor_id: int | None = None,
) -> Event:
    """Advance one immutable request; publication requires a separate protected job."""
    identity = Locator.decode(request_id)
    if (
        identity.repository_id != context.policy.repository_id
        or identity.host != context.policy.host
    ):
        raise ControllerError("E_REPOSITORY", "Request is for another repository.")
    try:
        record = context.journal.get(request_id)
    except ControllerError as error:
        if error.code != "E_REQUEST_MISSING":
            raise
        actor_role(context.api, identity.requester_id)
        receipt = discover(request_id, inbox or GitHubInbox(context.api))
        record = seal(
            receipt,
            context.journal,
            lambda request: revalidate(
                context, request, resuming_actor_id=resuming_actor_id
            ),
        )
    else:
        from cg_release.stranded_recovery import recovery_grant

        grant = recovery_grant(context, record)
        actor_role(
            context.api, grant.actor_id if grant is not None else identity.requester_id
        )
        if resuming_actor_id is not None:
            from cg_release.recovery_authority import authorize_record

            authorize_record(context, record, resuming_actor_id)
        if context.policy.enabled:
            record = advance(context, record, resuming_actor_id=resuming_actor_id)
    return Event(
        kind="status",
        request_id=request_id,
        version=record.request.version,
        observed=record.state,
        step=record.checkpoint,
        message="Verified durable checkpoint; published and complete remain distinct.",
        next_action="Inspect the next stage or protected approval."
        if context.policy.enabled
        else "Policy is disabled; reviewed setup is required.",
    )


def work_inventory(journal, issues: list[dict], *, refresh_docs=False) -> list[dict]:
    """Keep unfinished sealed requests schedulable even if their issue is deleted."""
    items = {issue["number"]: issue for issue in issues}
    if len(items) != len(issues):
        raise ControllerError("E_QUEUE", "Duplicate issue number in work inventory.")
    records = journal.records()
    completed = [r for r in records if r.state == "complete"] if refresh_docs else []
    docs_owner = min((r.request_id for r in completed), default=None)
    for record in records:
        if record.state == "abandoned" or (
            record.state == "complete" and record.request_id != docs_owner
        ):
            continue
        if record.receipt is None:
            if "publication-recovery" not in record.evidence:
                raise ControllerError(
                    "E_JOURNAL", "Sealed request lacks its immutable inbox mapping."
                )
            number = 2**52 + int(
                hashlib.sha256(record.request_id.encode()).hexdigest()[:12], 16
            )
            if (
                number in items
                and items[number].get("sealed_request_id") != record.request_id
            ):
                raise ControllerError(
                    "E_QUEUE",
                    "Audited recovery queue identity collides with another item.",
                )
        else:
            number = record.receipt.number
        items[number] = {
            "number": number,
            "sealed_request_id": record.request_id,
        }
    return list(items.values())


def main(argv=None, *, clock=time.monotonic) -> int:
    """Execute a bounded wakeup, e.g. controller.main(['--operation', 'scan'])."""
    try:
        parser = ContractParser(prog="cg-release-controller")
        parser.add_argument(
            "--operation",
            choices=["scan", "reconcile", "abandon", "recover"],
            default="scan",
        )
        parser.add_argument("--request-id")
        parser.add_argument("--reason")
        parser.add_argument("--recovery-digest")
        args = parser.parse_args(argv)
        if os.environ.get("GITHUB_ACTIONS") != "true":
            raise ControllerError(
                "E_CONTROLLER_TRUST", "Controller must run in its trusted GitHub job."
            )
        identity = Locator(
            schema_version=1,
            host=urlsplit(os.environ["GITHUB_SERVER_URL"]).hostname,
            repository_id=int(os.environ["GITHUB_REPOSITORY_ID"]),
            repository_slug=os.environ["GITHUB_REPOSITORY"],
            requester_id=int(os.environ["GITHUB_ACTOR_ID"]),
            nonce="0" * 32,
            proposal_digest="0" * 64,
        )
        context = context_for(
            identity.encode(),
            cwd=Path.cwd(),
            deadline=clock() + 120,
            clock=clock,
            writable=True,
        )
        actor_id, event_name = verify_run(context, dict(os.environ))
        if args.operation != "scan" and event_name != "workflow_dispatch":
            raise ControllerError("E_CONTROLLER_TRUST", "Manual dispatch required.")
        if not context.policy.enabled:
            raise ControllerError(
                "E_DISABLED", "Reviewed policy is disabled; controller makes no writes."
            )
        if args.operation == "recover":
            from cg_release.recovery_actions import recover

            event = recover(
                context,
                actor_id=actor_id,
                run_id=int(os.environ["GITHUB_RUN_ID"]),
                directive_digest=args.recovery_digest,
            )
        elif args.operation == "abandon":
            from cg_release.abandon import abandon_request

            event = abandon_request(
                context,
                args.request_id,
                actor_id,
                args.reason,
                int(os.environ["GITHUB_RUN_ID"]),
            )
        elif args.operation == "reconcile":
            event = reconcile(context, args.request_id, resuming_actor_id=actor_id)
        else:
            inventory = GitHubInbox(context.api).inventory(identity)

            class Inventory:
                def inventory(self, _locator):
                    return inventory

            def process(issue):
                if "sealed_request_id" in issue:
                    reconcile(context, issue["sealed_request_id"])
                    return
                try:
                    body = load_record(InboxBody, issue["body"].encode())
                except ValueError:
                    if "rc1." in issue["body"]:
                        raise ControllerError(
                            "E_INBOX", "Malformed release request body."
                        ) from None
                    return
                reconcile(context, body.locator, inbox=Inventory())

            cursor = scan(
                context.journal,
                work_inventory(
                    context.journal,
                    inventory,
                    refresh_docs=bool(context.policy.gpid_profile),
                ),
                process,
                api=context.api,
            )
            event = Event(
                kind="status",
                observed="scan-checkpoint",
                step="queue",
                message="Bounded scan persisted; unfinished requests remain durable.",
                proposal=cursor.model_dump(mode="json"),
            )
        emit_event(event, json_output=True)
        return 0
    except (ValueError, KeyError, TypeError):
        error = ControllerError(
            "E_CONTROLLER_INPUT", "Trusted controller input is malformed."
        )
    except ControllerError as caught:
        error = caught
    emit_event(
        Event(kind="error", code=error.code, message=error.message), json_output=True
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
