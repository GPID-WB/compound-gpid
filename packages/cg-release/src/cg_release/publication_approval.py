"""Acquire approval from the exact run and configured independent reviewers."""

from urllib.parse import quote

from cg_release.approval import verify_approval
from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES
from cg_release.github_checks import inventory


def excluded_reviewers(record, run, control_bot_id):
    """Exclude every historical reconfirmer and any direct human run trigger."""
    users = {
        uid
        for key, value in record.evidence.items()
        if key.startswith("publication-request-")
        for uid in value["reconfirmers"]
    }
    users |= {
        value["actor_id"]
        for key, value in record.evidence.items()
        if key == "publication-recovery" or key.startswith("publication-exception-")
    }
    trigger = run.get("actor", {}).get("id")
    if type(trigger) is int and trigger > 0 and trigger != control_bot_id:
        users.add(trigger)
    return sorted(users)


def approved_run(context, seal: dict) -> list[int]:
    """Read run/gate/reviewer evidence, e.g. approved_run(context, seal)."""
    api = context.api
    run_id = seal["run_id"]
    run = api.get(f"actions/runs/{run_id}")
    environment = api.get("environments/" + quote(seal["environment"], safe=""))
    try:
        rules = [
            r
            for r in environment["protection_rules"]
            if r["type"] == "required_reviewers"
        ]
        if len(rules) != 1:
            raise ValueError
        permitted = set()
        for row in rules[0]["reviewers"]:
            uid = row["reviewer"]["id"]
            if type(uid) is not int or uid <= 0:
                raise ValueError
            if row["type"] == "User":
                permitted.add(uid)
            elif row["type"] == "Team":
                for page in range(1, MAX_PAGES + 1):
                    members = api._request(f"teams/{uid}/members", page)
                    if not isinstance(members, list):
                        raise ValueError
                    for member in members:
                        if type(member["id"]) is not int or member["id"] <= 0:
                            raise ValueError
                        permitted.add(member["id"])
                    if len(members) < 100:
                        break
                else:
                    raise ValueError
            else:
                raise ValueError
        reviews = []
        for page in range(1, MAX_PAGES + 1):
            batch = api.get(f"actions/runs/{run_id}/approvals", page=page)
            if not isinstance(batch, list):
                raise ValueError
            reviews.extend(batch)
            if len(batch) < 100:
                break
        else:
            raise ValueError
        jobs = inventory(api, f"actions/runs/{run_id}/attempts/1/jobs", "jobs")
        sealing = [j for j in jobs if j["name"] == "seal"]
        protected = [j for j in jobs if j["name"] == "publish"]
        if (
            len(sealing) != 1
            or sealing[0]["status"] != "completed"
            or sealing[0]["conclusion"] != "success"
            or len(protected) != 1
        ):
            raise ValueError
        return verify_approval(
            seal, run, environment, reviews, protected[0], permitted_reviewers=permitted
        )
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_APPROVAL",
            "Exact pre-approval job, reviewers or protected job cannot be verified.",
        ) from None
