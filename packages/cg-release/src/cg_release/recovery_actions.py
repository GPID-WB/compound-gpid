"""Trusted maintainer entry points for reviewed, non-destructive journal recovery."""

import re
from urllib.parse import quote

from cg_release.authority import actor_role
from cg_release.events import ControllerError
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal, digest
from cg_release.models import Event, canonical_bytes, load_record
from cg_release.recovery import verify_restore
from cg_release.recovery_audit import record_audit
from cg_release.recovery_models import RecoveryDirective
from cg_release.source_blobs import commit_tree, read_blobs


def require_recovery_authority(context, spec, actor_id, directive_digest):
    """Verify the exact reviewed directive and current maintainer authority."""
    if (
        spec.repository_id != context.policy.repository_id
        or spec.policy_digest != digest(context.policy)
        or digest(spec) != directive_digest
        or actor_role(context.api, actor_id) not in {"maintain", "admin"}
    ):
        raise ControllerError(
            "E_RECOVERY_AUTHORITY",
            "Current maintainer and reviewed recovery digest are required.",
        )


def restore_journal(context, spec, *, actor_id, run_id, directive_digest):
    """Restore a missing/ref-prefix journal without force, e.g. restore_journal(...).

    The immutable reviewed directive is the pre-write intent. A successful restore
    appends a permanent audit through the ordinary signed control-App journal.
    Divergent/corrupt current history is never overwritten: use a separately
    reviewed new state branch and its required protections instead.
    """
    require_recovery_authority(context, spec, actor_id, directive_digest)
    if spec.operation != "journal-restore":
        raise ControllerError("E_RESTORE", "A journal-restore directive is required.")
    api, policy = context.api, context.policy

    class PinnedStore(GitHubJournalStore):
        def head(self):
            return spec.mirror_head

    mirror = Journal(PinnedStore(api, policy, bot_id=context.journal.store.bot_id))
    mirror_events = mirror.events()
    if not mirror_events:
        raise ControllerError(
            "E_RESTORE", "Recovery cannot silently bootstrap an empty journal."
        )
    records = mirror.records()
    expected = {r.request.tag: r for r in records if r.state != "abandoned"}
    bootstrap = {r.tag for r in policy.bootstrap}
    for ref in api.refs():
        tag = ref["ref"].removeprefix("refs/tags/")
        if tag.startswith(policy.tag_prefix) and tag not in bootstrap:
            saved = expected.get(tag)
            if (
                saved is None
                or "publication-tag-object" not in saved.evidence
                or ref["object"].get("type") != "tag"
                or ref["object"].get("sha")
                != saved.evidence["publication-tag-object"]["oid"]
            ):
                raise ControllerError(
                    "E_RESTORE",
                    "Remote tag effects are newer than the reviewed mirror.",
                )
    for release in api.pages("releases"):
        if (
            release["tag_name"].startswith(policy.tag_prefix)
            and release["tag_name"] not in set(expected) | bootstrap
        ):
            raise ControllerError(
                "E_RESTORE",
                "Remote Release effects are absent from the reviewed mirror.",
            )
        record = expected.get(release["tag_name"])
        if record is not None:
            seals = [
                v
                for k, v in record.evidence.items()
                if k.startswith("publication-seal-")
            ]
            if not seals:
                raise ControllerError(
                    "E_RESTORE", "The mirror predates the observed Release approval."
                )
            from cg_release.publication_reconcile import inspect_publication
            from cg_release.publication_remote import GitHubPublicationRemote

            inspect_publication(
                record, seals[-1]["inputs"], GitHubPublicationRemote(api)
            )
    try:
        head = context.journal.store.head()
    except ControllerError as error:
        if error.code != "E_NOT_FOUND":
            raise
        head = None
    complete = False
    if head is not None:
        current_events = context.journal.events()
        if len(current_events) >= len(mirror_events):
            verify_restore(mirror_events, current_events)
            complete = True
        else:
            if current_events:
                verify_restore(current_events, mirror_events)
            elif (
                head != policy.journal_root or spec.expected_head != policy.journal_root
            ):
                raise ControllerError(
                    "E_RESTORE",
                    "An empty journal is not the reviewed restore predecessor.",
                )
    if not complete:
        if head != spec.expected_head:
            raise ControllerError(
                "E_RESTORE", "Journal head differs from the reviewed expected head."
            )
        require_recovery_authority(context, spec, actor_id, directive_digest)
        endpoint = f"repos/{api.slug}/git/refs"
        payload = {"ref": "refs/heads/" + policy.state_branch, "sha": spec.mirror_head}
        method = "POST"
        if head is not None:
            endpoint += "/heads/" + quote(policy.state_branch, safe="")
            payload = {"sha": spec.mirror_head, "force": False}
            method = "PATCH"
        try:
            result = api.runner(
                "gh",
                [
                    "api",
                    "--method",
                    method,
                    "--hostname",
                    api.host,
                    "--include",
                    "--input",
                    "-",
                    endpoint,
                ],
                cwd=api.cwd,
                timeout=min(api.read_seconds, api.remaining()),
                allow_failure=True,
                input_text=canonical_bytes(payload).decode(),
            )
            if result.returncode or not re.match(
                r"HTTP/[0-9.]+ (?:200|201)(?: |\r?\n)", result.stdout
            ):
                raise ControllerError(
                    "E_WRITE_UNKNOWN", "Restore write requires exact read-back."
                )
        except ControllerError:
            verify_restore(mirror_events, context.journal.events())
        verify_restore(mirror_events, context.journal.events())
    record_audit(
        context.journal,
        spec,
        policy_sha=context.policy_sha,
        actor_id=actor_id,
        run_id=run_id,
        before_write=lambda: require_recovery_authority(
            context, spec, actor_id, directive_digest
        ),
    )
    return Event(
        kind="status",
        observed="journal-restored",
        step="audited-recovery",
        message="Verified mirror prefix retained; no history or tag was force-updated.",
    )


def recover(context, *, actor_id, run_id, directive_digest):
    """Read the fixed reviewed recovery file and dispatch one audited operation."""
    if not isinstance(directive_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", directive_digest
    ):
        raise ControllerError(
            "E_RECOVERY_INPUT", "An exact reviewed recovery digest is required."
        )
    if context.api.branch(context.default)["commit"]["sha"] != context.policy_sha:
        raise ControllerError("E_STALE_POLICY", "Protected recovery source advanced.")
    root = commit_tree(context.api, context.policy_sha)
    blob = read_blobs(context.api, root, [".release-recovery.json"])[
        ".release-recovery.json"
    ]
    spec = load_record(RecoveryDirective, blob.content)
    require_recovery_authority(context, spec, actor_id, directive_digest)
    if spec.operation == "journal-restore":
        return restore_journal(
            context,
            spec,
            actor_id=actor_id,
            run_id=run_id,
            directive_digest=directive_digest,
        )
    from cg_release.stranded_recovery import recover_publication

    return recover_publication(
        context,
        spec,
        actor_id=actor_id,
        run_id=run_id,
        directive_digest=directive_digest,
    )
