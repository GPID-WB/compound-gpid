"""Bounded build lifecycle with exact-input tickets and independently verified bytes."""

import hashlib
import re
import secrets

from cg_release.artifact_download import download_archive, retained_archive
from cg_release.artifacts import verify_archive
from cg_release.build_control import dispatch_build
from cg_release.build_evidence import (
    MATRIX_JOBS,
    registered_run,
    reuse_key,
    verify_build,
)
from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.hook_authority import seal_required_hooks
from cg_release.journal import digest
from cg_release.prepare_stage import checkpoint
from cg_release.recovery_authority import authorize_record
from cg_release.source_blobs import commit_tree, read_blobs
from cg_release.stranded_recovery import current_policy_digest


def make_ticket(
    context, record, *, nonce: str, workflow: str | None = None, resuming_actor_id=None
) -> dict:
    """Acquire immutable inputs, e.g. make_ticket(ctx, record, nonce=nonce).

    Metadata-only movement of the protected default branch is permitted only when
    the policy digest stays identical. Workflow SHA stays distinct from source SHA.
    """
    request, policy, api = record.request, context.policy, context.api
    original_profile = record.evidence.get("required-hooks", {}).get("stages") or any(
        value.get("profile_version") == "v1"
        for key, value in record.evidence.items()
        if re.fullmatch(r"build-request-[1-9][0-9]*", key)
    )
    if original_profile and policy.gpid_profile != "v1":
        raise ControllerError(
            "E_HOOK_POLICY", "Recovery cannot remove original required profile hooks."
        )
    binding = record.evidence["review-binding"]
    if (
        not policy.enabled
        or digest(policy) != current_policy_digest(context, record)
        or api.branch(context.default)["commit"]["sha"] != context.policy_sha
        or (
            not record.publication_started
            and api.branch(request.source_branch)["commit"]["sha"]
            != binding["release_sha"]
        )
        or commit_tree(api, binding["release_sha"]) != binding["release_tree"]
    ):
        raise ControllerError(
            "E_BUILD_INPUT", "Current policy or reviewed source binding changed."
        )
    authorize_record(context, record, resuming_actor_id)
    if record.publication_started:
        from cg_release.publication_rebuild import verify_rebuild_source

        verify_rebuild_source(context, record)
    workflows = {check.workflow_path for check in policy.required_checks}
    primary = (
        ".github/workflows/release-controller-build.yml"
        if ".github/workflows/release-controller-build.yml" in workflows
        else sorted(workflows)[0]
    )
    workflow = primary if workflow is None else workflow
    checks = [c for c in policy.required_checks if c.workflow_path == workflow]
    if not checks or len({c.app_id for c in checks}) != 1:
        raise ControllerError(
            "E_BUILD_POLICY", "Each release workflow needs one verifiable App producer."
        )
    produces_artifacts = workflow == primary
    jobs = {c.name for c in checks} | ({"build"} if produces_artifacts else set())
    if workflow == ".github/workflows/release-controller-ci.yml":
        jobs.update(MATRIX_JOBS)
    locks = read_blobs(api, binding["release_tree"], policy.build.lock_paths)
    result = {
        "repository_id": policy.repository_id,
        "request_digest": request.proposal_digest,
        "dispatch_nonce": nonce,
        "workflow_path": workflow,
        "controller_sha": context.policy_sha,
        "controller_ref": context.default,
        "release_sha": binding["release_sha"],
        "release_tree": binding["release_tree"],
        "policy_digest": current_policy_digest(context, record),
        "controller_digest": digest(policy.controller),
        "required_checks_digest": digest(
            {"checks": [c.model_dump(mode="json") for c in policy.required_checks]}
        ),
        "build_inputs_digest": digest(policy.build),
        "lock_digests": {
            p: hashlib.sha256(b.content).hexdigest() for p, b in locks.items()
        },
        "toolchain": "python-3.11-3.12-six-cell-v1"
        if workflow.endswith("release-controller-ci.yml")
        else "ubuntu-24.04-python-3.12-v1",
        "profile_version": policy.gpid_profile,
        "app_id": checks[0].app_id,
        "required_jobs": sorted(jobs),
        "build_spec": policy.build.model_dump(mode="json"),
        "produces_artifacts": produces_artifacts,
    }
    reuse_key(result)
    return result


def build_step(context, record, *, resuming_actor_id=None):
    """Perform bounded dispatch or evidence collection, e.g. build_step(ctx, record).

    A waiting run returns immediately. Reuse is verified again against remote run
    and artifact metadata, never a cached success bit. No approval/publication runs.
    """
    if record.state not in {"building", "awaiting-approval"}:
        return record
    journal, api = context.journal, context.api
    record = seal_required_hooks(context, record, actor_id=resuming_actor_id)
    requests = [
        (int(key.removeprefix("build-request-")), value)
        for key, value in record.evidence.items()
        if re.fullmatch(r"build-request-[1-9][0-9]*", key)
    ]
    latest = {}
    for number, sealed in sorted(requests):
        latest[sealed["workflow_path"]] = (number, sealed)
    next_number = max((n for n, _ in requests), default=0) + 1
    workflows = {c.workflow_path for c in context.policy.required_checks}
    for workflow in sorted(workflows - set(latest)):
        sealed = make_ticket(
            context,
            record,
            nonce=secrets.token_hex(16),
            workflow=workflow,
            resuming_actor_id=resuming_actor_id,
        )
        record = checkpoint(
            journal, record, f"build-request-{next_number}", sealed, "building"
        )
        latest[workflow] = (next_number, sealed)
        next_number += 1
    # One request-level intent is active at a time. Do not contend with a pending
    # registration; privileged workflow jobs also share a control concurrency group.
    if any(
        f"build-dispatch-{n}" in record.evidence
        and f"build-registration-{n}" not in record.evidence
        for n, _ in latest.values()
    ):
        return record
    verified, asset_inventory = {}, None
    waiting = False
    for workflow, (number, sealed) in sorted(latest.items()):
        fresh = make_ticket(
            context,
            record,
            nonce=sealed["dispatch_nonce"],
            workflow=workflow,
            resuming_actor_id=resuming_actor_id,
        )
        if reuse_key(fresh) != reuse_key(sealed):
            fresh = {**fresh, "dispatch_nonce": secrets.token_hex(16)}
            return checkpoint(
                journal, record, f"build-request-{next_number}", fresh, "building"
            )
        registration = record.evidence.get(f"build-registration-{number}")
        if registration is None:
            if f"build-dispatch-{number}" not in record.evidence:
                dispatch_build(context, record, nonce=sealed["dispatch_nonce"])
                return journal.get(record.request_id)
            waiting = True
            continue
        run_id = registration["run_id"]
        latest_run = api.get(f"actions/runs/{run_id}")
        if (
            latest_run.get("id") != run_id
            or type(latest_run.get("run_attempt")) is not int
            or latest_run["run_attempt"] != registration["run_attempt"]
        ):
            raise ControllerError(
                "E_BUILD_EVIDENCE",
                "A later run attempt invalidates the registered build.",
            )
        run = api.get(f"actions/runs/{run_id}/attempts/{registration['run_attempt']}")
        if run.get("status") in {
            "queued",
            "in_progress",
            "waiting",
            "pending",
            "requested",
        }:
            waiting = True
            continue
        suite = api.get(f"check-suites/{run['check_suite_id']}")
        if (
            record.state == "building"
            and resuming_actor_id is not None
            and run.get("status") == "completed"
            and run.get("conclusion")
            in {
                "failure",
                "cancelled",
                "timed_out",
                "startup_failure",
                "action_required",
            }
        ):
            # A committed claim is never granted twice. An authorized manual
            # resume may instead start one fresh run after the claimed run failed.
            registered_run(sealed, registration, run, suite)
            replacement = make_ticket(
                context,
                record,
                nonce=secrets.token_hex(16),
                workflow=workflow,
                resuming_actor_id=resuming_actor_id,
            )
            return checkpoint(
                journal, record, f"build-request-{next_number}", replacement, "building"
            )
        jobs = inventory(
            api,
            f"actions/runs/{run_id}/attempts/{registration['run_attempt']}/jobs",
            "jobs",
        )
        evidence = verify_build(sealed, registration, run, jobs, suite)
        if sealed["produces_artifacts"]:
            previous = record.evidence.get(f"build-evidence-{number}", {}).get(
                "inventory", {}
            )
            metadata = retained_archive(
                api,
                run_id,
                sealed["controller_sha"],
                expected_id=previous.get("artifact_id"),
            )
            if metadata is None:
                replacement = make_ticket(
                    context,
                    record,
                    nonce=secrets.token_hex(16),
                    workflow=workflow,
                    resuming_actor_id=resuming_actor_id,
                )
                return checkpoint(
                    journal,
                    record,
                    f"build-request-{next_number}",
                    replacement,
                    "building",
                )
            raw = download_archive(api, metadata)
            evidence["inventory"] = verify_archive(
                raw,
                metadata,
                run_id=run_id,
                controller_sha=sealed["controller_sha"],
                declared=context.policy.build.artifacts,
                max_total_bytes=context.policy.build.max_total_bytes,
                max_artifacts=context.policy.build.max_artifacts,
            )
            if context.policy.gpid_profile:
                from cg_release.profile_build_verify import verify_profile_artifact

                verify_profile_artifact(context, record, sealed, registration, raw)
            if asset_inventory is not None:
                raise ControllerError(
                    "E_BUILD_EVIDENCE",
                    "Only one authoritative artifact producer is allowed.",
                )
            asset_inventory = evidence["inventory"]
        operation = f"build-evidence-{number}"
        if operation in record.evidence:
            if record.evidence[operation] != evidence:
                raise ControllerError(
                    "E_BUILD_EVIDENCE", "Previously verified build evidence changed."
                )
        else:
            record = checkpoint(journal, record, operation, evidence, "building")
        verified[workflow] = {
            "request": number,
            "reuse_key": evidence["reuse_key"],
            "run_id": run_id,
            "run_attempt": registration["run_attempt"],
        }
    if waiting:
        return record
    if set(verified) != workflows or asset_inventory is None:
        raise ControllerError(
            "E_BUILD_EVIDENCE", "Complete workflow and artifact evidence is required."
        )
    final = {"gates": verified, "inventory": asset_inventory}
    final_operation = f"build-validated-{max(n for n, _ in latest.values())}"
    if final_operation in record.evidence:
        if record.evidence[final_operation] != final:
            raise ControllerError("E_BUILD_EVIDENCE", "Final build evidence changed.")
        return record
    return checkpoint(journal, record, final_operation, final, "awaiting-approval")
