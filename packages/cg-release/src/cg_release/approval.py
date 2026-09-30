"""Exact publication-run approval checks; environment names alone grant no authority."""

from cg_release.events import ControllerError
from cg_release.journal import digest


def verify_approval(
    seal: dict,
    run: dict,
    environment: dict,
    reviews: list,
    job: dict,
    *,
    permitted_reviewers: set[int],
) -> list[int]:
    """Require the exact active protected job and independent permitted approval.

    Args: seal is read from the immutable journal; other records come from the
        corresponding GitHub run, review history, environment and jobs APIs.
    Returns: Sorted independent reviewer IDs, e.g. ``[123]``.
    Raises: ControllerError for missing, ambiguous, stale or self approval.
    """
    try:
        if (
            seal["digest"] != digest(seal["inputs"])
            or type(seal["run_id"]) is not int
            or seal["run_id"] <= 0
            or type(run["run_attempt"]) is not int
            or run["run_attempt"] != 1
            or seal["run_attempt"] != 1
            or run["id"] != seal["run_id"]
            or run["event"] != "workflow_dispatch"
            or run["path"] != seal["workflow_path"]
            or run["head_sha"] != seal["controller_sha"]
            or run["head_branch"] != seal["controller_ref"]
            or run["repository"]["id"] != seal["repository_id"]
            or run["status"] != "in_progress"
            or environment["id"] != seal["environment_id"]
            or environment["name"] != seal["environment"]
            or environment["can_admins_bypass"] is not False
            or type(job["id"]) is not int
            or job["id"] <= 0
            or job["run_id"] != seal["run_id"]
            or job["run_attempt"] != 1
            or job["name"] != "publish"
            or job["status"] != "in_progress"
            or job["conclusion"] is not None
            or seal["mode"] not in {"initial", "recovery"}
            or not isinstance(reviews, list)
            or not reviews
        ):
            raise ValueError
        rules = [
            r
            for r in environment["protection_rules"]
            if r["type"] == "required_reviewers"
        ]
        if (
            len(rules) != 1
            or rules[0]["prevent_self_review"] is not True
            or not rules[0]["reviewers"]
        ):
            raise ValueError
        excluded = {seal["requester_id"], *seal["reconfirmers"]}
        approved = set()
        for review in reviews:
            if not isinstance(review["environments"], list):
                raise ValueError
            matching = [
                e for e in review["environments"] if e["id"] == seal["environment_id"]
            ]
            if not matching:
                continue
            if (
                len(matching) != 1
                or matching[0]["name"] != seal["environment"]
                or review["state"] != "approved"
            ):
                raise ValueError
            uid = review["user"]["id"]
            if type(uid) is not int or uid <= 0:
                raise ValueError
            if uid in permitted_reviewers and uid not in excluded:
                approved.add(uid)
        if not approved:
            raise ValueError
        return sorted(approved)
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_APPROVAL", "Bound independent protected approval is not verified."
        ) from None
