"""Exact registered job and Pages deployment proof for published completion."""

from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.journal import digest
from cg_release.profile_dispatch import verify_identity


def verify_deployment(context, record, item, run) -> dict:
    """Verify remote deployment, e.g. verify_deployment(ctx, record, ticket, run).

    Returns: Compact docs HookResult dictionary. Raises ControllerError on missing
    exact job, manifest, run or deployment evidence. Read-only; no cached success.
    """
    api, sealed = context.api, item.ticket
    registration = item.evidence.get("registration")
    if not registration or registration.get("request_digest") != digest(sealed):
        raise ControllerError("E_HOOK", "Composition registration is missing.")
    run_id = registration["run_id"]
    verify_identity(run, sealed, run_id)
    jobs = inventory(api, f"actions/runs/{run_id}/attempts/1/jobs", "jobs")
    required = {"register", "dev-preview", "compose", "deploy"}
    selected = [job for job in jobs if job.get("name") in required]
    if (
        run.get("conclusion") != "success"
        or len(selected) != len(required)
        or {j["name"] for j in selected} != required
        or any(
            j.get("run_id") != run_id
            or j.get("run_attempt") != 1
            or j.get("conclusion") != "success"
            for j in selected
        )
    ):
        raise ControllerError("E_HOOK", "Composition run/job identity is not verified.")
    composed = item.evidence.get("composition")
    if composed is None or composed.get("request_digest") != digest(sealed):
        raise ControllerError(
            "E_HOOK", "Required trusted composition inventory is missing."
        )
    matches = []
    for deployment in api.deployments("github-pages"):
        if (
            deployment.get("sha") != sealed["controller_sha"]
            or deployment.get("environment") != "github-pages"
        ):
            continue
        for status in api.pages(f"deployments/{deployment['id']}/statuses"):
            if status.get("state") == "success" and status.get(
                "log_url", ""
            ).startswith(f"https://{api.host}/{api.slug}/actions/runs/{run_id}/"):
                matches.append(deployment["id"])
    if len(set(matches)) != 1:
        raise ControllerError(
            "E_HOOK", "Exact successful Pages deployment is missing or ambiguous."
        )
    return {
        "stage": "docs",
        "release_sha": record.evidence["publication-receipt"]["release_sha"],
        "evidence_digest": digest(composed),
        "remote_id": matches[0],
        "verified": True,
    }
