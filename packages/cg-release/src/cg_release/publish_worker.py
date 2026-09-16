"""Trusted pre-approval and protected publisher entry points in separate jobs."""

import hashlib
import os
import re
import time
from datetime import datetime
from pathlib import Path

from cg_release.cli import ContractParser
from cg_release.context import context_for
from cg_release.controller import verify_run
from cg_release.events import ControllerError, emit_event
from cg_release.github import GitHubReads
from cg_release.history import adopted_history
from cg_release.hook_authority import required_hooks
from cg_release.journal import digest
from cg_release.journal_checkpoint import atomic_publication_checkpoint
from cg_release.models import Event
from cg_release.publication_approval import approved_run, excluded_reviewers
from cg_release.publication_control import (
    acquire_owner,
    active_owner,
    publication_ticket,
    release_owner,
    store_seal,
)
from cg_release.publication_credentials import role_runner
from cg_release.publication_inputs import make_inputs
from cg_release.publication_output import error_event, write_seal_summary
from cg_release.publication_reconcile import inspect_publication
from cg_release.publication_registration import register_publication
from cg_release.publication_remote import GitHubPublicationRemote, ReadOnlyPublication
from cg_release.publication_stage import dispatch_payload
from cg_release.publisher import publish, should_be_latest
from cg_release.recovery import finish_hooks
from cg_release.signing import create_tag, verify_tag

WORKFLOW = ".github/workflows/release-controller-publish.yml"


def seal_publication(context, record, nonce, environment, remote):
    """Persist gate inputs, e.g. seal_publication(ctx, record, nonce, env, api)."""
    run_id = int(environment["GITHUB_RUN_ID"])
    number, ticket = publication_ticket(record, nonce)
    run = context.api.get(f"actions/runs/{run_id}")
    record = register_publication(context, record, number, run)
    dispatch = f"publication-dispatch-{number}"
    payload = dispatch_payload(context, record, ticket)
    if (
        record.evidence.get(f"publication-dispatch-intent-{number}") == payload
        and dispatch not in record.evidence
    ):
        record = atomic_publication_checkpoint(
            context.journal, record, dispatch, payload, record.state
        )
    if record.intent is not None and not re.fullmatch(
        r"publication-(?:tag|draft|publish|asset-[1-9][0-9]*)",
        record.intent["operation"],
    ):
        raise ControllerError(
            "E_PUBLICATION_REQUEST",
            "An earlier effect needs reconciliation before sealing.",
        )
    run = context.api.get(f"actions/runs/{run_id}")
    inputs, _ = make_inputs(
        context,
        record,
        run,
        ticket,
        remote=remote,
        fingerprint=environment.get("CG_RELEASE_SIGNING_FINGERPRINT") or None,
    )
    seal = {
        "inputs": inputs,
        "digest": digest(inputs),
        "run_id": run_id,
        "run_attempt": 1,
        "workflow_path": WORKFLOW,
        "controller_sha": context.policy_sha,
        "controller_ref": context.default,
        "repository_id": context.policy.repository_id,
        "environment_id": inputs["environment_id"],
        "environment": inputs["environment"],
        "requester_id": record.request.requester_id,
        "reconfirmers": excluded_reviewers(
            record, run, getattr(context.journal.store, "bot_id", None)
        ),
        "mode": ticket["mode"],
        "nonce": nonce,
    }
    saved = store_seal(context.journal, record, seal)
    head = context.journal._read()[0]
    key = hashlib.sha256(record.request_id.encode()).hexdigest()
    url = (
        f"https://{context.api.host}/{context.api.slug}/blob/{head}/requests/{key}.json"
    )
    return saved, seal, url


def execute_publication(context, record, nonce, environment, remote, *, now):
    """Run only after current protected approval, e.g. execute_publication(...)."""
    run_id = int(environment["GITHUB_RUN_ID"])
    _, ticket = publication_ticket(record, nonce)
    seal = record.evidence.get(f"publication-seal-{run_id}")
    if seal is None or seal.get("nonce") != nonce:
        raise ControllerError(
            "E_APPROVAL", "A prior immutable pre-approval seal is required."
        )
    approved_run(context, seal)
    verified_artifacts = {}
    run = context.api.get(f"actions/runs/{run_id}")
    inputs, data = make_inputs(
        context,
        record,
        run,
        ticket,
        remote=remote,
        fingerprint=seal["inputs"]["fingerprint"],
        verified_artifacts=verified_artifacts,
    )
    if digest(inputs) != seal["digest"]:
        raise ControllerError(
            "E_APPROVAL", "Publication inputs changed after the protected approval."
        )
    if not data:
        remote = ReadOnlyPublication(remote)
    expiry = int(
        datetime.fromisoformat(
            environment["CG_RELEASE_TOKEN_EXPIRES_AT"].replace("Z", "+00:00")
        ).timestamp()
    )
    owner = active_owner(context.journal.records())
    if owner is not None and owner[1]["run_id"] != run_id:
        inspect_publication(record, inputs, remote)
        proof = {
            "run": context.api.get(f"actions/runs/{owner[1]['run_id']}"),
            "effects_reconciled": True,
        }
        record = release_owner(
            context.journal, record, run_id=run_id, terminal_proof=proof, now=now
        )
    record = acquire_owner(
        context.journal, record, run_id=run_id, expires_at=expiry, now=now
    )
    fingerprint = inputs["fingerprint"]
    key = Path(environment["CG_RELEASE_SIGNING_KEY_FILE"]) if fingerprint else None
    tag = record.evidence.get("publication-tag-object")
    if tag is None:
        tag = create_tag(
            inputs["tag"],
            inputs["release_sha"],
            inputs["tagger_name"],
            inputs["tagger_email"],
            inputs["tagger_timestamp"],
            key_file=key,
            fingerprint=fingerprint,
        )
    verify_tag(
        tag, inputs["tag"], inputs["release_sha"], key_file=key, fingerprint=fingerprint
    )
    rows, _ = adopted_history(
        context.api, context.policy, records=context.journal.records(), current=record
    )
    history = [r["version"] for r in rows]
    latest = should_be_latest(inputs["version"], history)
    old_latest = remote.latest_id()
    prior_latest = record.evidence.get("publication-publish")
    if prior_latest is not None:
        latest = prior_latest["make_latest"]

    def recheck():
        current = context.journal.get(record.request_id)
        owner = active_owner(context.journal.records())
        if (
            owner is None
            or owner[0] != record.request_id
            or owner[1]["run_id"] != run_id
        ):
            raise ControllerError("E_OWNER", "Publication owner changed.")
        approved_run(context, seal)
        fresh, _ = make_inputs(
            context,
            current,
            run,
            ticket,
            remote=remote,
            fingerprint=fingerprint,
            verified_artifacts=verified_artifacts,
        )
        if digest(fresh) != seal["digest"]:
            raise ControllerError(
                "E_APPROVAL", "Publication inputs changed before an effect."
            )

    record = publish(
        context.journal,
        record,
        inputs,
        tag,
        remote,
        data=data,
        recheck=recheck,
        make_latest=latest,
        expected_latest=old_latest,
        run_id=run_id,
    )
    record = release_owner(context.journal, record, run_id=run_id)
    return finish_hooks(
        context.journal,
        record,
        required=required_hooks(record),
        verified={},
    )


def main(argv=None) -> int:
    """Execute the trusted job, e.g. main(['seal', '--request-id', ...])."""
    started = time.monotonic()
    args = context = record = None
    try:
        parser = ContractParser(prog="cg-release-publisher")
        parser.add_argument("operation", choices=["seal", "publish"])
        parser.add_argument("--request-id", required=True)
        parser.add_argument("--nonce", required=True)
        args = parser.parse_args(argv)
        env = dict(os.environ)
        if env.get("GITHUB_ACTIONS") != "true" or env.get("GITHUB_RUN_ATTEMPT") != "1":
            raise ControllerError(
                "E_CONTROLLER_TRUST",
                "Only an initial trusted workflow attempt may use "
                "publisher credentials.",
            )
        control = role_runner("control")

        def factory(host, slug, **kwargs):
            return GitHubReads(host, slug, runner=control, **kwargs)

        context = context_for(
            args.request_id,
            deadline=time.monotonic() + 120,
            writable=True,
            api_factory=factory,
        )
        _, event = verify_run(context, env, workflow=WORKFLOW)
        if event != "workflow_dispatch":
            raise ControllerError(
                "E_CONTROLLER_TRUST", "Publication requires one dedicated dispatch run."
            )
        record = context.journal.get(args.request_id)
        if args.operation == "seal":
            # Publication credentials do not exist in the pre-approval job.
            record, seal, url = seal_publication(
                context, record, args.nonce, env, GitHubPublicationRemote(context.api)
            )
            write_seal_summary(env, seal, url)
        else:
            api = GitHubReads(
                context.api.host,
                context.api.slug,
                cwd=Path.cwd(),
                deadline=context.api.deadline,
                runner=role_runner("publishing"),
            )
            record = execute_publication(
                context,
                record,
                args.nonce,
                env,
                GitHubPublicationRemote(api),
                now=int(time.time()),
            )
        emit_event(
            Event(
                kind="status",
                request_id=args.request_id,
                version=record.request.version,
                observed=record.state,
                step=record.checkpoint,
            ),
            json_output=True,
        )
        return 0
    except (KeyError, TypeError, ValueError, OSError):
        error = ControllerError(
            "E_PUBLICATION_INPUT", "Trusted publication input or output is malformed."
        )
    except ControllerError as caught:
        error = caught
    emit_event(error_event(args, context, record, error, started), json_output=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
