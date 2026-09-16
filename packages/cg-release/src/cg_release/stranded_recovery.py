"""Audited adoption of an immutable stranded tag and explicit source exceptions."""

import hashlib

from cg_release.admission import Locator
from cg_release.authority import actor_role
from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_checkpoint import atomic_publication_checkpoint
from cg_release.journal_models import Record
from cg_release.metadata import _format_edit
from cg_release.models import Event, canonical_bytes, load_record
from cg_release.policy import approval_route
from cg_release.publication_remote import GitHubPublicationRemote
from cg_release.recovery import check_lineage
from cg_release.recovery_actions import require_recovery_authority
from cg_release.recovery_audit import record_audit
from cg_release.recovery_models import RecoveryAudit
from cg_release.source_blobs import commit_tree, read_blobs


def validate_recovered_admission(record, audit):
    """Validate an audited tagged admission during append and full journal replay."""
    proof = load_record(
        RecoveryAudit, canonical_bytes(record.evidence["publication-recovery"])
    )
    spec = proof.directive
    raw = spec.tag.text.encode()
    if (
        audit
        != {"operation": "recover-admit", "directive_digest": proof.directive_digest}
        or proof.directive_digest != digest(spec)
        or spec.operation != "stranded-publication"
        or record.request != spec.request
        or record.receipt is not None
        or record.state != "building"
        or not record.publication_started
        or record.published
        or record.intent is not None
        or record.checkpoint != "publication-recovery"
        or set(record.evidence)
        != {"publication-recovery", "publication-tag-object", "review-binding"}
        or record.evidence["publication-tag-object"] != spec.tag.model_dump(mode="json")
        or record.evidence["review-binding"]
        != {"release_sha": spec.release_sha, "release_tree": spec.release_tree}
        or hashlib.sha1(b"tag " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        != spec.tag.oid
        or not spec.tag.text.startswith(
            f"object {spec.release_sha}\ntype commit\ntag {spec.request.tag}\n"
        )
    ):
        raise ValueError("audited recovery identity differs from immutable tag")


def recovery_grant(context, record):
    """Return a current, exact-source maintainer grant or None, never infer one."""
    proofs = [
        v
        for k, v in record.evidence.items()
        if k == "publication-recovery" or k.startswith("publication-exception-")
    ]
    if not proofs:
        return None
    latest = proofs[0] if len(proofs) == 1 else None
    if latest is None:
        for event in reversed(context.journal.events()):
            operation = event["audit"]["operation"]
            if event["record"].get("request_id") != record.request_id:
                continue
            key = "publication-recovery" if operation == "recover-admit" else operation
            if key == "publication-recovery" or key.startswith(
                "publication-exception-"
            ):
                value = event["record"]["evidence"].get(key)
                if value in proofs:
                    latest = value
                    break
        if latest is None:
            raise ControllerError(
                "E_RECOVERY_AUTHORITY",
                "Recovery grant order is not present in the verified journal.",
            )
    proof = load_record(RecoveryAudit, canonical_bytes(latest))
    spec = proof.directive
    if (
        proof.directive_digest != digest(spec)
        or spec.request != record.request
        or spec.policy_digest != digest(context.policy)
        or spec.release_sha != record.evidence["review-binding"]["release_sha"]
        or spec.release_tree != record.evidence["review-binding"]["release_tree"]
        or spec.tag.oid != record.evidence["publication-tag-object"]["oid"]
        or actor_role(context.api, proof.actor_id) not in {"maintain", "admin"}
    ):
        raise ControllerError(
            "E_RECOVERY_AUTHORITY",
            "Audited recovery grant is stale or conflicts with source identity.",
        )
    return proof


def source_lineage(context, record, *, tagged):
    """Require normal lineage unless an exact reviewed source exception exists."""
    grant = recovery_grant(context, record)
    if tagged and grant is not None and grant.directive.allow_source_exception:
        return
    check_lineage(
        context.api,
        record.request.source_branch,
        record.evidence["review-binding"]["release_sha"],
        tagged=tagged,
    )


def current_policy_digest(context, record):
    """Use current policy only when it matches the request or an audited exact grant."""
    grant = recovery_grant(context, record)
    return (
        grant.directive.policy_digest
        if grant is not None
        else record.request.policy_digest
    )


def recover_publication(
    context, spec, *, actor_id, run_id, directive_digest, remote=None
):
    """Adopt/reconfirm a stranded immutable tag; rebuild and approval still follow."""
    require_recovery_authority(context, spec, actor_id, directive_digest)
    remote = remote or GitHubPublicationRemote(context.api)
    request, tag = spec.request, spec.tag
    if context.policy.gpid_profile and (
        spec.operation == "stranded-publication" or spec.allow_source_exception
    ):
        base = spec.evidence_base
        if base is None:
            raise ControllerError(
                "E_RECOVERY_INPUT",
                "GPID recovery requires an explicit reviewed evidence PR base.",
            )
        branch = context.api.branch(base.branch)
        if (
            branch.get("protected") is not True
            or branch.get("name") != base.branch
            or branch["commit"]["sha"] != base.sha
        ):
            raise ControllerError(
                "E_RECOVERY_INPUT",
                "Reviewed evidence PR base is not the exact protected branch.",
            )
    if (
        request is None
        or tag is None
        or request.repository_id != context.policy.repository_id
        or request.host != context.policy.host
        or request.repository_slug.casefold() != context.api.slug.casefold()
        or commit_tree(context.api, spec.release_sha) != spec.release_tree
        or (
            tag.fingerprint is not None
            and tag.fingerprint not in context.policy.allowed_signing_fingerprints
        )
        or (context.policy.signing_required or request.sign)
        != (tag.fingerprint is not None)
    ):
        raise ControllerError(
            "E_RECOVERY_INPUT",
            "Recovery source, repository or signing identity differs.",
        )
    observed = remote.observe_tag(request.tag)
    if observed != {"type": "tag", "oid": tag.oid, "commit": spec.release_sha}:
        raise ControllerError(
            "E_TAG_CONFLICT",
            "Only the existing exact annotated object may be recovered.",
        )
    blobs = read_blobs(
        context.api, spec.release_tree, [a.path for a in context.policy.metadata]
    )
    for adapter in context.policy.metadata:
        raw = blobs[adapter.path].content.decode()
        formatted, _ = _format_edit(adapter, raw, request.version, [])
        if formatted != raw:
            raise ControllerError(
                "E_RECOVERY_INPUT",
                "Immutable recovery metadata does not represent the reviewed version.",
            )
    approval_route(
        context.policy,
        request.source_branch,
        request.version,
        actor_role(context.api, actor_id),
        context.default,
        request.override_reason or spec.reason,
    )
    proof = RecoveryAudit(
        directive=spec,
        directive_digest=directive_digest,
        policy_sha=context.policy_sha,
        actor_id=actor_id,
        run_id=run_id,
    )
    locator = Locator.from_request(request).encode()
    if spec.operation == "stranded-publication":
        if any(
            r.publication_started and not r.published and r.request_id != locator
            for r in context.journal.records()
        ):
            raise ControllerError(
                "E_INCOMPLETE_PUBLICATION",
                "Recover the earlier unfinished publication first.",
            )
        candidate = Record(
            request=request,
            request_id=locator,
            state="building",
            checkpoint="publication-recovery",
            publication_started=True,
            evidence={
                "publication-recovery": proof.model_dump(mode="json"),
                "publication-tag-object": tag.model_dump(mode="json"),
                "review-binding": {
                    "release_sha": spec.release_sha,
                    "release_tree": spec.release_tree,
                },
            },
        )

        def change(prior):
            if prior is not None:
                if (
                    prior.evidence.get("publication-recovery", {}).get(
                        "directive_digest"
                    )
                    != directive_digest
                ):
                    raise ControllerError(
                        "E_RECOVERY_CONFLICT",
                        "An existing reservation has another recovery identity.",
                    )
                return prior, {}
            source_lineage(context, candidate, tagged=True)
            require_recovery_authority(context, spec, actor_id, directive_digest)
            return candidate, {
                "operation": "recover-admit",
                "directive_digest": directive_digest,
            }

        record = context.journal._change(locator, change)
    elif spec.operation == "source-exception":
        record = context.journal.get(locator)
        if not record.publication_started or record.evidence[
            "publication-tag-object"
        ] != tag.model_dump(mode="json"):
            raise ControllerError(
                "E_RECOVERY_CONFLICT",
                "Source exception must preserve the original publication tag.",
            )
        operation = f"publication-exception-{run_id}"
        if operation not in record.evidence:
            require_recovery_authority(context, spec, actor_id, directive_digest)
            record = atomic_publication_checkpoint(
                context.journal,
                record,
                operation,
                proof.model_dump(mode="json"),
                record.state,
            )
    else:
        raise ControllerError(
            "E_RECOVERY_INPUT", "Unsupported publication recovery operation."
        )
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
        request_id=locator,
        version=request.version,
        observed=record.state,
        step="audited-recovery",
        message="Exact existing tag retained; isolated build and fresh independent "
        "protected approval remain required.",
    )
