"""Trusted preparation coordinator: exact edits, reconciled PR, reviewed release SHA."""

import hashlib
import re
from dataclasses import replace

from cg_release.authority import actor_role, authorize_resume
from cg_release.events import ControllerError
from cg_release.github import decode_json
from cg_release.github_checks import required_pr_checks
from cg_release.journal import digest
from cg_release.journal_checkpoint import atomic_build_checkpoint
from cg_release.journal_rules import retained_evidence
from cg_release.manifest import validate_manifest
from cg_release.models import canonical_bytes
from cg_release.preparation import TreeEntry, apply_edits
from cg_release.preparation_remote import PreparationRemote, commit_spec
from cg_release.reviewed_commit import verify_merge
from cg_release.source_blobs import commit_tree


def checkpoint(
    journal, record, operation: str, evidence: dict, state: str, *, before_write=None
):
    """Persist evidence; e.g. checkpoint(j, r, op, data, state, before_write=guard).

    Phase6 callers supply current authority before each separate journal operation.
    The callback may reject continuation after intent; the intent is not erased.
    Each operation's internal CAS/read-back is still non-atomic with permission I/O.
    """
    if before_write is not None:
        before_write()
    if re.fullmatch(r"build-request-[1-9][0-9]*", operation):
        return atomic_build_checkpoint(journal, record, operation, evidence, state)
    identity = digest(evidence)
    retained_evidence(record, operation, identity, evidence)
    journal.intent(record.request_id, operation, identity)
    if before_write is not None:
        before_write()
    return journal.result(
        record.request_id, operation, identity, state, evidence=evidence
    )


def source_inventory(api, source_sha: str) -> tuple[str, list[TreeEntry]]:
    """Read the exact source tree, e.g. source_inventory(api, sha); no checkout."""
    root = commit_tree(api, source_sha)
    value = api._request(f"repos/{api.slug}/git/trees/{root}?recursive=1", None)
    try:
        if (
            value["sha"] != root
            or value["truncated"] is not False
            or not isinstance(value["tree"], list)
        ):
            raise ValueError
        entries = []
        for row in value["tree"]:
            if row["type"] == "tree" and row["mode"] == "040000":
                continue
            if row["type"] != ("commit" if row["mode"] == "160000" else "blob"):
                raise ValueError
            entries.append(TreeEntry(row["path"], row["mode"], row["sha"]))
        return root, entries
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ControllerError(
            "E_TREE", "Preparation source inventory is incomplete or malformed."
        ) from None


def prepare_step(context, record, *, resuming_actor_id=None):
    """Advance queued/review states, e.g. prepare_step(context, record).

    Caller must have verified the protected worker run and writable journal context.
    All metadata parsing comes from the revalidated Phase 2 proposal. No source code
    or publisher operation runs here; awaiting-review returns without polling.
    """
    request, api, journal = record.request, context.api, context.journal

    def fresh():
        if (
            not context.policy.enabled
            or api.branch(context.default)["commit"]["sha"] != request.policy_sha
            or api.branch(request.source_branch)["commit"]["sha"] != request.source_sha
        ):
            raise ControllerError(
                "E_STALE_PROPOSAL", "Preparation policy or source tip changed."
            )
        authorize_resume(
            api,
            context.policy,
            context.default,
            request,
            resuming_actor_id or request.requester_id,
        )
        api.remaining()

    if record.state == "awaiting-review":
        if (
            api.branch(context.default)["commit"]["sha"] != context.policy_sha
            or digest(context.policy) != request.policy_digest
        ):
            raise ControllerError(
                "E_STALE_PROPOSAL", "Trusted policy changed before review binding."
            )
        authorize_resume(
            api,
            context.policy,
            context.default,
            request,
            resuming_actor_id or request.requester_id,
        )
        binding = verify_merge(
            api,
            request,
            record.evidence["prepare-pr"],
            checks=lambda sha: required_pr_checks(api, context.policy, sha),
            role=lambda uid: actor_role(api, uid),
        )
        return (
            record
            if binding is None
            else checkpoint(journal, record, "review-binding", binding, "building")
        )
    if record.state != "queued":
        return record
    from cg_release.controller import revalidate

    proposal, snapshot = revalidate(
        context, request, sealed=True, resuming_actor_id=resuming_actor_id
    )
    edits = []
    for edit in proposal.edits:
        if edit.path == ".release-manifest.json":
            manifest = decode_json(edit.content.decode())
            manifest["request_id"] = record.request_id
            raw = canonical_bytes(manifest) + b"\n"
            validate_manifest(raw)
            edit = replace(
                edit, content=raw, output_digest=hashlib.sha256(raw).hexdigest()
            )
        edits.append(edit)
    root, entries = source_inventory(api, request.source_sha)
    allowed = {a.path for a in context.policy.metadata} | {
        context.policy.changelog.path,
        ".release-manifest.json",
    }
    if context.policy.gpid_profile:
        from cg_release.hooks import selected_profile

        extra = selected_profile(context.policy).prepare(
            snapshot,
            tag=request.tag,
            version=request.version,
            created_at=record.receipt.created_at if record.receipt else None,
        )
        if allowed.intersection(e.path for e in extra):
            raise ControllerError("E_PROFILE", "Profile edits overlap core metadata.")
        edits.extend(extra)
        allowed.update(e.path for e in extra)
    prepared = apply_edits(
        root,
        entries,
        snapshot.blobs,
        tuple(edits),
        allowed,
        create_paths={".release-manifest.json"}
        | ({f"releases/{request.tag}.json"} if context.policy.gpid_profile else set()),
        clock=api.clock,
        deadline=api.deadline,
    )
    created_at = record.receipt.created_at if record.receipt else None
    head, _ = commit_spec(request, prepared.tree, created_at)
    inputs = {
        "source_sha": request.source_sha,
        "source_tree": root,
        "tree": prepared.tree,
        "head": head,
        "branch": "release-controller/" + request.nonce,
        "edits": [
            {"path": e.path, "input": e.input_digest, "output": e.output_digest}
            for e in prepared.edits
        ],
    }
    identity = digest(inputs)
    retained_evidence(record, "prepare", identity, inputs)
    # Recovery after the first result reuses its immutable evidence, never reopens
    # the completed intent. The PR read-back still runs before binding its ID.
    if "prepare" not in record.evidence:
        fresh()
        journal.intent(record.request_id, "prepare", identity)
    elif record.evidence["prepare"] != inputs:
        raise ControllerError(
            "E_PREPARATION_CONFLICT", "Preparation input evidence changed."
        )

    def write_fresh():
        if "prepare" in record.evidence:
            raise ControllerError(
                "E_PREPARATION_CONFLICT",
                "Completed preparation lost an object; inspected recovery is required.",
            )
        fresh()

    remote = PreparationRemote(api, fresh=write_fresh)
    pr = remote.ensure(
        request, prepared, root, {e.path: e.mode for e in entries}, created_at
    )
    if "prepare" not in record.evidence:
        record = journal.result(
            record.request_id, "prepare", identity, "queued", evidence=inputs
        )
    return checkpoint(journal, record, "prepare-pr", pr, "awaiting-review")
