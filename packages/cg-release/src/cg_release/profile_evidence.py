"""Declared post-tag evidence PR using the existing exact-tree preparation protocol."""

import hashlib
import re

from cg_release.authority import actor_role
from cg_release.events import ControllerError
from cg_release.github import decode_json
from cg_release.github_checks import required_pr_checks
from cg_release.hook_authority import authorize_hooks
from cg_release.journal import digest
from cg_release.models import canonical_bytes
from cg_release.preparation import apply_edits
from cg_release.preparation_remote import PreparationRemote
from cg_release.prepare_stage import checkpoint, source_inventory
from cg_release.profile_attestations import attestation_edits
from cg_release.profile_evidence_inputs import authorize_attempt, evidence_inputs
from cg_release.reviewed_commit import verify_merge
from cg_release.source_blobs import read_blobs


def evidence_step(context, record, make_attestation, *, resuming_actor_id=None):
    """Create/reconcile one reviewed evidence PR, never move the published tag.

    Example: evidence_step(context, published_record, profile.attestation).
    All writes use the control App and are preceded by durable input/intent records.
    make_attestation(record, exact_payload_bytes, deprecation_digest_map,
    evidence_inputs=sealed_attempt_view) must return
    a raw attestation dictionary; it is the installed trusted callback, not source
    code or a verification result. The applicable requester/resumer (or admitted
    maintainer grant) supplies actor provenance and is rechecked before effects.
    Returns None while the PR/reviews/checks are pending, or the verified evidence
    HookResult dictionary only after exact merged bytes pass. Raises ControllerError
    on stale bases, invalid provenance, authority or byte conflicts. Creates only
    the declared evidence branch/PR and immutable journal checkpoints, not releases.
    """
    api, journal, request = context.api, context.journal, record.request
    actor_id = authorize_hooks(context, record, resuming_actor_id, fresh=True)
    receipt = record.evidence["publication-receipt"]
    path = f"{context.policy.profile.attestation_directory}/{request.tag}.json"
    prefix, inputs, record = evidence_inputs(context, record, actor_id, path)
    evidence_request = request.model_copy(
        update={
            "source_sha": inputs["base"],
            "source_branch": inputs["branch"],
            "nonce": inputs["nonce"],
        }
    )
    root, entries = source_inventory(api, inputs["base"])
    _, tagged_entries = source_inventory(api, receipt["release_sha"])
    provenance_paths = [
        e.path
        for e in tagged_entries
        if e.path.startswith(".github/shared/skill-management/provenance/")
        and e.path.endswith(".json")
    ]
    payload_path = f"releases/{request.tag}.json"
    tagged_root, _ = source_inventory(api, receipt["release_sha"])
    tagged = read_blobs(api, tagged_root, [payload_path, *provenance_paths])
    deprecations = {}
    for name in provenance_paths:
        value = decode_json(tagged[name].content.decode())
        if value.get("lifecycle") != "deprecated":
            continue
        identifier, value_digest = (
            value.get("skillId"),
            value.get("deprecatedRecordDigest"),
        )
        if (
            not isinstance(identifier, str)
            or re.fullmatch(r"[a-z][a-z0-9-]*", identifier) is None
            or not isinstance(value_digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", value_digest)
            or identifier in deprecations
        ):
            raise ControllerError(
                "E_HOOK", "Tagged deprecation provenance is ambiguous."
            )
        deprecations[identifier] = value_digest
    raw = (
        canonical_bytes(
            make_attestation(
                record,
                tagged[payload_path].content,
                deprecations,
                evidence_inputs=inputs,
            )
        )
        + b"\n"
    )
    blobs, edits = attestation_edits(api, root, path, raw)
    prepared = apply_edits(
        root,
        entries,
        blobs,
        edits,
        {e.path for e in edits},
        clock=api.clock,
        deadline=api.deadline,
        create_paths={e.path for e in edits if e.input_digest is None},
    )

    def fresh():
        if api.branch(inputs["branch"])["commit"]["sha"] != inputs["base"]:
            raise ControllerError(
                "E_HOOK",
                "Evidence base moved; preserve the sealed PR for reviewed recovery.",
            )
        authorize_attempt(context, record.request_id, inputs, actor_id)

    operation, binding_key = prefix + "-pr", prefix + "-binding"

    def authorize_write():
        authorize_attempt(context, record.request_id, inputs, actor_id)

    if operation not in record.evidence:
        expected = {
            "tree": prepared.tree,
            "base": inputs["base"],
            "digest": hashlib.sha256(raw).hexdigest(),
            "edits": [
                {"path": e.path, "input": e.input_digest, "output": e.output_digest}
                for e in edits
            ],
        }
        fresh()
        journal.intent(record.request_id, operation, digest(expected))
        pr = PreparationRemote(api, fresh=fresh).ensure(
            evidence_request,
            prepared,
            root,
            {e.path: e.mode for e in entries},
            inputs["created_at"],
        )
        # Persist the PR result separately from the sealed operation input.
        authorize_write()
        record = journal.result(
            record.request_id,
            operation,
            digest(expected),
            "published",
            evidence=expected,
        )
        record = checkpoint(
            journal, record, binding_key, pr, "published", before_write=authorize_write
        )
    elif binding_key not in record.evidence:
        pr = PreparationRemote(api, fresh=fresh).ensure(
            evidence_request,
            prepared,
            root,
            {e.path: e.mode for e in entries},
            inputs["created_at"],
        )
        record = checkpoint(
            journal, record, binding_key, pr, "published", before_write=authorize_write
        )
    binding = verify_merge(
        api,
        evidence_request,
        record.evidence[binding_key],
        checks=lambda sha: required_pr_checks(api, context.policy, sha),
        role=lambda uid: actor_role(api, uid),
        require_tip=False,
    )
    if binding is None:
        return None
    actual = read_blobs(api, binding["release_tree"], [e.path for e in edits])
    if any(actual[e.path].content != e.content for e in edits):
        raise ControllerError(
            "E_HOOK", "Reviewed evidence commit does not contain the exact attestation."
        )
    authorize_attempt(context, record.request_id, inputs, actor_id)
    return {
        "stage": "evidence",
        "release_sha": receipt["release_sha"],
        "evidence_digest": digest(binding),
        "remote_id": binding["pr_id"],
        "verified": True,
    }
