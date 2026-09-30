"""Bounded trusted check/run inventories shared by preparation and build evidence."""

from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES


def inventory(api, endpoint: str, key: str) -> list[dict]:
    """Read a complete REST envelope list, e.g. an actions/runs workflow_runs list."""
    seen, result, expected = set(), [], None
    try:
        for page in range(1, MAX_PAGES + 1):
            payload = api._request(f"repos/{api.slug}/{endpoint}", page)
            total, rows = payload["total_count"], payload[key]
            if (
                type(total) is not int
                or total < 0
                or not isinstance(rows, list)
                or (expected is not None and expected != total)
            ):
                raise ValueError
            expected = total
            for row in rows:
                identity = row["id"]
                if type(identity) is not int or identity <= 0 or identity in seen:
                    raise ValueError
                seen.add(identity)
                result.append(row)
            if len(rows) < 100:
                if len(result) != expected:
                    raise ValueError
                return result
        raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_CHECK_EVIDENCE", "Check/run inventory is incomplete or malformed."
        ) from None


def required_pr_checks(api, policy, sha: str) -> list[dict]:
    """Verify each check's App and actual workflow run, e.g. for a PR head."""
    rows = inventory(api, f"commits/{sha}/check-runs?filter=latest", "check_runs")
    result = []
    try:
        for required in policy.required_checks:
            if required.stage == "release":
                continue
            matches = [r for r in rows if r["name"] == required.name]
            if len(matches) != 1:
                raise ValueError
            check = matches[0]
            suite = check["check_suite"]["id"]
            if (
                type(suite) is not int
                or check["head_sha"] != sha
                or check["app"]["id"] != required.app_id
                or check["status"] != "completed"
                or check["conclusion"] != "success"
            ):
                raise ValueError
            runs = inventory(
                api,
                f"actions/runs?check_suite_id={suite}&head_sha={sha}",
                "workflow_runs",
            )
            if len(runs) != 1:
                raise ValueError
            run = runs[0]
            if (
                run["head_sha"] != sha
                or run["check_suite_id"] != suite
                or run["path"] != required.workflow_path
                or run["status"] != "completed"
                or run["conclusion"] != "success"
                or type(run["run_attempt"]) is not int
                or run["run_attempt"] < 1
            ):
                raise ValueError
            result.append(
                {
                    "id": check["id"],
                    "app_id": required.app_id,
                    "name": required.name,
                    "run_id": run["id"],
                    "run_attempt": run["run_attempt"],
                    "workflow_path": run["path"],
                }
            )
        if not result:
            raise ValueError
        return result
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_CHECK_EVIDENCE", "Required check producer or conclusion does not match."
        ) from None
