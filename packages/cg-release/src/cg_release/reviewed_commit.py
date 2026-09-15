"""Read-only exact reviewed-head and merged-release-tree admission."""

import re
from urllib.parse import quote

from cg_release.events import ControllerError


def verify_merge(
    api, request, prepared: dict, *, checks, role, require_tip=True
) -> dict | None:
    """Verify GitHub records, e.g. verify_merge(api, req, prep, ...).

    Args: checks verifies required producer identities for the reviewed head; role
        reads current numeric-reviewer authority. Neither uses source-written claims.
    Returns: Immutable release binding, or None while the unchanged PR is open.
    Raises: ControllerError on changed inputs, missing approval, or malformed data.
    """
    try:
        pr = api.get(f"pulls/{prepared['number']}")
        if (
            pr["number"] != prepared["number"]
            or pr["id"] != prepared["id"]
            or pr["head"]["sha"] != prepared["head"]
            or pr["head"]["ref"] != prepared["branch"]
            or pr["head"]["repo"]["id"] != request.repository_id
            or pr["base"]["ref"] != request.source_branch
            or pr["base"]["repo"]["id"] != request.repository_id
            or type(pr["merged"]) is not bool
            or pr["draft"] is not False
        ):
            raise ValueError
        if not pr["merged"]:
            if pr["state"] != "open":
                raise ValueError
            if api.branch(request.source_branch)["commit"]["sha"] != request.source_sha:
                raise ControllerError(
                    "E_STALE_PROPOSAL", "Preparation base advanced before merge."
                )
            return None
        sha = pr["merge_commit_sha"]
        if pr["state"] != "closed" or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError
        commit = api.get("git/commits/" + sha)
        parents = [p["sha"] for p in commit["parents"]]
        if (
            commit["sha"] != sha
            or commit["tree"]["sha"] != prepared["tree"]
            or parents
            not in ([request.source_sha], [request.source_sha, prepared["head"]])
            or (
                require_tip
                and api.branch(request.source_branch)["commit"]["sha"] != sha
            )
        ):
            raise ValueError
        latest, ids = {}, set()
        base = api.branch(request.source_branch)
        if type(base.get("protected")) is not bool or (
            require_tip and base["commit"]["sha"] != sha
        ):
            raise ValueError
        if not require_tip:
            from cg_release.recovery import check_lineage

            check_lineage(api, request.source_branch, sha, tagged=True)
        minimum_reviews = 1
        if base["protected"]:
            protection = api.get(
                "branches/" + quote(request.source_branch, safe="") + "/protection"
            )
            requirement = protection.get("required_pull_request_reviews")
            if requirement is not None:
                count = requirement["required_approving_review_count"]
                if type(count) is not int or count < 0:
                    raise ValueError
                minimum_reviews = max(1, count)
        for review in api.pages(f"pulls/{prepared['number']}/reviews"):
            uid, rid = review["user"]["id"], review["id"]
            if (
                type(uid) is not int
                or type(rid) is not int
                or uid <= 0
                or rid <= 0
                or rid in ids
            ):
                raise ValueError
            ids.add(rid)
            if review["state"] not in {
                "APPROVED",
                "CHANGES_REQUESTED",
                "DISMISSED",
                "COMMENTED",
                "PENDING",
            }:
                raise ValueError
            if review["state"] not in {"COMMENTED", "PENDING"} and rid > latest.get(
                uid, {}
            ).get("id", 0):
                latest[uid] = review
        approvals = []
        for uid, review in latest.items():
            if review["state"] == "CHANGES_REQUESTED":
                raise ValueError
            if (
                uid != request.requester_id
                and review["state"] == "APPROVED"
                and review["commit_id"] == prepared["head"]
                and role(uid) in {"write", "maintain", "admin"}
            ):
                approvals.append(review["id"])
        check_evidence = checks(prepared["head"])
        if len(approvals) < minimum_reviews or not check_evidence:
            raise ValueError
        return {
            "pr_number": prepared["number"],
            "pr_id": prepared["id"],
            "reviewed_head": prepared["head"],
            "release_sha": sha,
            "release_tree": prepared["tree"],
            "review_ids": sorted(approvals),
            "required_reviews": minimum_reviews,
            "checks": check_evidence,
        }
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ControllerError(
            "E_REVIEW_BINDING",
            "Reviewed PR, approval, checks, or final commit identity differs.",
        ) from None
