"""Fresh registered-build validation and bounded publication inputs."""

import hashlib
import io
import re
import zipfile
from datetime import datetime

from cg_release.artifact_download import download_archive, retained_archive
from cg_release.artifacts import verify_archive
from cg_release.authority import actor_role
from cg_release.build_evidence import reuse_key, verify_build
from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.journal import digest
from cg_release.metadata import project_version
from cg_release.policy import approval_route
from cg_release.publication_provenance import provenance_asset, tagger_identity
from cg_release.publication_reconcile import inspect_publication
from cg_release.recovery_authority import authorize_record
from cg_release.source_blobs import read_blobs
from cg_release.stranded_recovery import (
    current_policy_digest,
    recovery_grant,
    source_lineage,
)


def verify_release_gates(context, record, *, need_bytes=True, verified_artifacts=None):
    """Return rechecked gates and bytes, e.g. verify_release_gates(ctx, record).
    Raises ControllerError for stale/expired inputs. Published recovery requires
    separate complete Release byte verification.
    """
    try:
        choices = [
            (int(k.removeprefix("build-validated-")), v)
            for k, v in record.evidence.items()
            if re.fullmatch(r"build-validated-[1-9][0-9]*", k)
        ]
        if not choices:
            raise ValueError
        final = max(choices)[1]
        policy, api = context.policy, context.api
        if digest(policy) != current_policy_digest(context, record) or set(
            final["gates"]
        ) != {c.workflow_path for c in policy.required_checks}:
            raise ValueError
        data, found_inventory = {}, False
        if record.publication_started and any(
            record.evidence[f"build-request-{g['request']}"]["policy_digest"]
            != digest(policy)
            for g in final["gates"].values()
        ):
            raise ControllerError(
                "E_REBUILD_REQUIRED",
                "Audited policy recovery requires new exact-source build evidence.",
            )
        for workflow, gate in final["gates"].items():
            number, run_id = gate["request"], gate["run_id"]
            sealed = record.evidence[f"build-request-{number}"]
            registration = record.evidence[f"build-registration-{number}"]
            if (
                sealed["workflow_path"] != workflow
                or sealed["policy_digest"] != digest(policy)
                or sealed["controller_digest"] != digest(policy.controller)
                or sealed["build_inputs_digest"] != digest(policy.build)
                or sealed["request_digest"] != record.request.proposal_digest
                or sealed["release_sha"]
                != record.evidence["review-binding"]["release_sha"]
                or sealed["release_tree"]
                != record.evidence["review-binding"]["release_tree"]
                or sealed["required_checks_digest"]
                != digest(
                    {
                        "checks": [
                            c.model_dump(mode="json") for c in policy.required_checks
                        ]
                    }
                )
            ):
                raise ValueError
            expected = record.evidence[f"build-evidence-{number}"]
            checked = {k: v for k, v in expected.items() if k != "inventory"}
            if need_bytes:
                if (
                    api.get(f"actions/runs/{run_id}")["run_attempt"]
                    != registration["run_attempt"]
                ):
                    raise ValueError
                run = api.get(
                    f"actions/runs/{run_id}/attempts/{registration['run_attempt']}"
                )
                jobs = inventory(
                    api,
                    f"actions/runs/{run_id}/attempts/{registration['run_attempt']}/jobs",
                    "jobs",
                )
                checked = verify_build(
                    sealed,
                    registration,
                    run,
                    jobs,
                    api.get(f"check-suites/{run['check_suite_id']}"),
                )
            if (
                checked != {k: v for k, v in expected.items() if k != "inventory"}
                or checked["reuse_key"] != reuse_key(sealed)
                or registration["build_digest"] != checked["reuse_key"]
                or registration["run_id"] != run_id
                or checked["reuse_key"] != gate["reuse_key"]
                or checked["run_id"] != run_id
                or checked["run_attempt"] != gate["run_attempt"]
            ):
                raise ValueError
            if sealed["produces_artifacts"]:
                if found_inventory or expected["inventory"] != final["inventory"]:
                    raise ValueError
                found_inventory = True
                if not need_bytes:
                    continue
                metadata = retained_archive(
                    api,
                    run_id,
                    sealed["controller_sha"],
                    expected_id=final["inventory"]["artifact_id"],
                )
                if metadata is None:
                    raise ControllerError(
                        "E_REBUILD_REQUIRED",
                        "Pre-publication artifact bytes expired; rebuild exact inputs "
                        "and obtain fresh approval.",
                    )
                key = digest(
                    {
                        "sealed": sealed,
                        "registration": registration,
                        "metadata": metadata,
                    }
                )
                cached = (
                    None if verified_artifacts is None else verified_artifacts.get(key)
                )
                if cached is None:
                    raw = download_archive(api, metadata)
                    verified = verify_archive(
                        raw,
                        metadata,
                        run_id=run_id,
                        controller_sha=sealed["controller_sha"],
                        declared=policy.build.artifacts,
                        max_total_bytes=policy.build.max_total_bytes,
                        max_artifacts=policy.build.max_artifacts,
                    )
                    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                        data = {
                            f["name"]: archive.read(f["path"])
                            for f in verified["files"]
                        }
                    if verified_artifacts is not None:
                        verified_artifacts.clear()
                        verified_artifacts[key] = (verified, data)
                else:
                    verified, data = cached
                if verified != final["inventory"]:
                    raise ValueError
        if not found_inventory:
            raise ValueError
        return final, dict(data)
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ControllerError(
            "E_PUBLICATION_INPUT",
            "Publication build inputs or exact gate evidence differ.",
        ) from None


def make_inputs(
    context,
    record,
    run: dict,
    ticket: dict,
    *,
    remote,
    fingerprint=None,
    verified_artifacts=None,
):
    """Acquire exact approval inputs, e.g. make_inputs(ctx, record, run, ticket, ...).
    Changed inputs cannot reuse approval; immutable source blobs are never executed.
    """
    policy, api, request = context.policy, context.api, record.request
    grant = recovery_grant(context, record)
    if not policy.enabled or digest(policy) != current_policy_digest(context, record):
        raise ControllerError(
            "E_STALE_POLICY",
            "Current policy differs; reviewed maintainer recovery is required.",
        )
    if api.branch(context.default)["commit"]["sha"] != context.policy_sha:
        raise ControllerError("E_STALE_POLICY", "Protected workflow revision advanced.")
    current_actor = grant.actor_id if grant is not None else request.requester_id
    for uid in {current_actor, *ticket["reconfirmers"]}:
        authorize_record(context, record, uid)
    route = approval_route(
        policy,
        request.source_branch,
        request.version,
        actor_role(api, current_actor),
        context.default,
        request.override_reason
        or (grant.directive.reason if grant is not None else None),
    )
    if grant is not None:
        route = policy.environments.override
    environment = api.get("environments/" + route)
    if type(environment.get("id")) is not int or environment["id"] <= 0:
        raise ControllerError(
            "E_APPROVAL", "Protected environment numeric identity is unavailable."
        )
    saved_tag = record.evidence.get("publication-tag-object")
    observed_tag = remote.observe_tag(request.tag)
    if observed_tag is not None and (
        saved_tag is None
        or observed_tag
        != {
            "oid": saved_tag["oid"],
            "type": "tag",
            "commit": record.evidence["review-binding"]["release_sha"],
        }
    ):
        raise ControllerError(
            "E_TAG_CONFLICT",
            "A stranded or conflicting tag requires audited maintainer recovery.",
        )
    release_sha = record.evidence["review-binding"]["release_sha"]
    source_lineage(context, record, tagged=observed_tag is not None)
    released = remote.observe_release(request.tag)
    already_published = released is not None and released.get("draft") is False
    final, data = verify_release_gates(
        context,
        record,
        need_bytes=not already_published,
        verified_artifacts=verified_artifacts,
    )
    signing = policy.signing_required or request.sign
    if (signing and fingerprint not in policy.allowed_signing_fingerprints) or (
        not signing and fingerprint is not None
    ):
        raise ControllerError(
            "E_SIGNING", "Required allowlisted signing fingerprint is unavailable."
        )
    notes = read_blobs(
        api, record.evidence["review-binding"]["release_tree"], [policy.changelog.path]
    )[policy.changelog.path].content.decode()
    if len(notes.encode()) > 16384:
        raise ControllerError(
            "E_PUBLICATION_INPUT", "Reviewed notes exceed the publication record bound."
        )
    timestamp = int(
        datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")).timestamp()
    )
    inputs = {
        "repository_id": policy.repository_id,
        "request_id": record.request_id,
        "line": request.line,
        "version": request.version,
        "tag": request.tag,
        "source_sha": request.source_sha,
        "release_sha": release_sha,
        "release_tree": record.evidence["review-binding"]["release_tree"],
        "policy_digest": current_policy_digest(context, record),
        "confirmed_policy_sha": request.policy_sha,
        "controller_sha": context.policy_sha,
        "controller_digest": digest(policy.controller),
        "build_digest": digest(final),
        "inventory": final["inventory"]["files"],
        "override_reason": request.override_reason,
        "recovery_digest": grant.directive_digest if grant is not None else None,
        "recovery_actor": grant.actor_id if grant is not None else None,
        "recovery_run_id": grant.run_id if grant is not None else None,
        "environment": route,
        "environment_id": environment["id"],
        "fingerprint": fingerprint,
        **tagger_identity(saved_tag, timestamp),
        "notes": notes,
        "notes_digest": hashlib.sha256(notes.encode()).hexdigest(),
        "projections": {
            a.path: project_version(request.version, [])
            if a.kind == "python-project"
            else request.version
            for a in policy.metadata
        },
    }
    manifest, provenance = provenance_asset(inputs, record, remote, released)
    inputs["inventory"] = [*inputs["inventory"], manifest]
    if not already_published:
        data[manifest["name"]] = provenance
    else:
        # Only complete matching public bytes can use retained CI evidence after
        # Actions retention. The execution adapter then denies every remote write.
        inspect_publication(record, inputs, remote)
    return inputs, data
