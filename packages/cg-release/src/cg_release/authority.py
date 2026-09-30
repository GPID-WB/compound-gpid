"""Current actor identity and minimum enforceable GitHub protection requirements."""

from urllib.parse import quote

from cg_release.events import ControllerError
from cg_release.github import MAX_PAGES, GitHubReads
from cg_release.models import Policy, Request
from cg_release.policy import approval_route


def authorize_resume(
    api: GitHubReads, policy: Policy, default: str, request: Request, actor_id: int
) -> None:
    """Check original and manual resumer authority at the mutation boundary."""
    role = actor_role(api, request.requester_id)
    resuming_role = actor_role(api, actor_id)
    approval_route(
        policy,
        request.source_branch,
        request.version,
        role,
        default,
        request.override_reason,
    )
    if request.override_reason is not None and resuming_role not in {
        "maintain",
        "admin",
    }:
        raise ControllerError(
            "E_AUTHORITY", "Override recovery requires current maintainer authority."
        )


def secret_names(api: GitHubReads, endpoint: str) -> set[str]:
    """Read complete secret-name metadata only; never secret values."""
    names = set()
    for page in range(1, MAX_PAGES + 1):
        value = api.get(endpoint, page=page)
        if type(value["total_count"]) is not int or not isinstance(
            value["secrets"], list
        ):
            raise ValueError
        for secret in value["secrets"]:
            name = secret["name"]
            if not isinstance(name, str) or name in names:
                raise ValueError
            names.add(name)
        if len(value["secrets"]) < 100:
            if len(names) != value["total_count"]:
                raise ValueError
            return names
    raise ValueError("secret inventory bound exceeded")


def actor_role(api: GitHubReads, actor_id: int) -> str:
    """Resolve current authority by immutable user ID, e.g. actor_role(api, 123).

    Returns a standard write/maintain/admin role. Unknown/custom roles fail closed.
    """
    try:
        user = api._request(f"user/{actor_id}", None)
        if type(actor_id) is not int or actor_id <= 0 or user["id"] != actor_id:
            raise ValueError
        login = user["login"]
        if not isinstance(login, str) or not login or len(login) > 255:
            raise ValueError
        value = api.get("collaborators/" + quote(login, safe="") + "/permission")
        role = value["role_name"]
        if (
            role not in {"write", "maintain", "admin"}
            or type(value["user"]["id"]) is not int
            or value["user"]["id"] != actor_id
            or value["permission"]
            != {"write": "write", "maintain": "write", "admin": "admin"}[role]
        ):
            raise ValueError
        return role
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_AUTHORITY",
            "Current numeric actor authority is unavailable or insufficient.",
        ) from None


def verify_controls(api: GitHubReads, policy: Policy, default: str) -> int:
    """Verify App mapping, exact ref rules, and protected environment controls.

    Args: policy comes only from the protected default commit; default is verified.
    Returns: Numeric control bot ID, e.g. verify_controls(api, policy, 'main').
    Raises: ControllerError when required API evidence is absent or weaker.
    """
    try:
        repo = api.get("")
        if (
            type(repo["id"]) is not int
            or repo["id"] != policy.repository_id
            or repo["default_branch"] != default
            or repo["fork"] is not False
            or repo["has_issues"] is not True
            or api.host != policy.host
            or repo["full_name"].casefold() != api.slug.casefold()
            or api.branch(default)["protected"] is not True
        ):
            raise ValueError
        workflow = api.get("actions/workflows/release-controller.yml")
        if (
            type(workflow["id"]) is not int
            or workflow["id"] <= 0
            or workflow["state"] != "active"
            or workflow["path"] != ".github/workflows/release-controller.yml"
        ):
            raise ValueError
        protection = api.get("branches/" + quote(default, safe="") + "/protection")
        review = protection["required_pull_request_reviews"]
        if (
            protection["enforce_admins"]["enabled"] is not True
            or protection["allow_force_pushes"]["enabled"] is not False
            or protection["allow_deletions"]["enabled"] is not False
            or type(review["required_approving_review_count"]) is not int
            or review["required_approving_review_count"] < 1
            or review["dismiss_stale_reviews"] is not True
            or any(review["bypass_pull_request_allowances"].values())
        ):
            raise ValueError
        app = api._request("apps/" + policy.apps.control_slug, None)
        bot = api._request(
            "users/" + quote(policy.apps.control_slug + "[bot]", safe=""), None
        )
        if (
            type(app["id"]) is not int
            or app["id"] != policy.apps.control
            or app["slug"] != policy.apps.control_slug
            or bot["type"] != "Bot"
            or bot["login"] != policy.apps.control_slug + "[bot]"
            or type(bot["id"]) is not int
            or bot["id"] <= 0
        ):
            raise ValueError
        control_names = {"RELEASE_CONTROL_APP_ID", "RELEASE_CONTROL_APP_PRIVATE_KEY"}
        publish_names = {
            "RELEASE_PUBLISHING_APP_ID",
            "RELEASE_PUBLISHING_APP_PRIVATE_KEY",
        }
        for endpoint in ("actions/secrets", "actions/organization-secrets"):
            if secret_names(api, endpoint) & (control_names | publish_names):
                raise ValueError
        for name in (
            policy.environments.control,
            policy.environments.publish,
            policy.environments.override,
            *(("github-pages",) if policy.gpid_profile else ()),
        ):
            endpoint = "environments/" + quote(name, safe="")
            environment = api.get(endpoint)
            required_secrets = (
                control_names
                if name in {policy.environments.control, "github-pages"}
                else control_names | publish_names
            )
            names = secret_names(api, endpoint + "/secrets")
            if not required_secrets <= names or (
                name == "github-pages" and names & publish_names
            ):
                raise ValueError
            if environment["deployment_branch_policy"] != {
                "protected_branches": False,
                "custom_branch_policies": True,
            }:
                raise ValueError
            branches = api.get(endpoint + "/deployment-branch-policies", page=1)
            if (
                branches["total_count"] != 1
                or len(branches["branch_policies"]) != 1
                or branches["branch_policies"][0]["name"] != default
                or branches["branch_policies"][0]["type"] != "branch"
            ):
                raise ValueError
            if name != policy.environments.control or name == "github-pages":
                reviewers = [
                    r
                    for r in environment["protection_rules"]
                    if r["type"] == "required_reviewers"
                ]
                if (
                    environment["can_admins_bypass"] is not False
                    or len(reviewers) != 1
                    or reviewers[0]["prevent_self_review"] is not True
                    or not reviewers[0]["reviewers"]
                ):
                    raise ValueError
                for reviewer in reviewers[0]["reviewers"]:
                    if (
                        reviewer["type"] not in {"User", "Team"}
                        or type(reviewer["reviewer"]["id"]) is not int
                        or reviewer["reviewer"]["id"] <= 0
                    ):
                        raise ValueError
        required = {
            ("branch", "refs/heads/" + policy.state_branch): [
                {
                    "actor_id": policy.apps.control,
                    "actor_type": "Integration",
                    "bypass_mode": "always",
                }
            ],
            ("tag", "refs/tags/" + policy.tag_prefix + "*"): [],
        }
        verified = set()
        immutable_state = False
        controlled_tag_creation = False
        for summary in api.pages("rulesets"):
            rule = api.get("rulesets/" + str(summary["id"]))
            if rule["enforcement"] != "active":
                continue
            refs = rule["conditions"]["ref_name"]
            kinds = {r["type"] for r in rule["rules"]}
            if (
                rule["target"] == "tag"
                and refs
                == {"include": ["refs/tags/" + policy.tag_prefix + "*"], "exclude": []}
                and "creation" in kinds
                and rule["bypass_actors"]
                == [
                    {
                        "actor_id": policy.apps.publishing,
                        "actor_type": "Integration",
                        "bypass_mode": "always",
                    }
                ]
            ):
                controlled_tag_creation = True
            if (
                rule["target"] == "branch"
                and refs
                == {"include": ["refs/heads/" + policy.state_branch], "exclude": []}
                and not rule["bypass_actors"]
                and {"deletion", "non_fast_forward"} <= kinds
            ):
                immutable_state = True
            for key, bypass in required.items():
                if rule["target"] == key[0] and refs == {
                    "include": [key[1]],
                    "exclude": [],
                }:
                    needed = (
                        {"update"}
                        if key[0] == "branch"
                        else {"update", "deletion", "non_fast_forward"}
                    )
                    if rule["bypass_actors"] == bypass and needed <= kinds:
                        verified.add(key)
        if (
            verified != set(required)
            or not immutable_state
            or not controlled_tag_creation
        ):
            raise ValueError
        return bot["id"]
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_PROTECTIONS",
            "Required App, ref, or environment protections are unverifiable.",
        ) from None
