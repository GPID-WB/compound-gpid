"""Fail-closed authority and protection checks against GitHub response shapes."""

import copy
from pathlib import Path

import pytest

from cg_release.authority import actor_role, verify_controls
from cg_release.events import ControllerError
from cg_release.models import Policy, load_record


def policy_fixture() -> Policy:
    return load_record(
        Policy, (Path(__file__).parent / "fixtures/policy.json").read_bytes()
    )


class Controls:
    host, slug = "github.com", "example/generic"

    def __init__(self):
        self.policy = policy_fixture()
        self.env = {
            "can_admins_bypass": False,
            "protection_rules": [
                {
                    "type": "required_reviewers",
                    "prevent_self_review": True,
                    "reviewers": [{"type": "User", "reviewer": {"id": 99}}],
                }
            ],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
        }
        self.rules = [
            {
                "id": 1,
                "target": "branch",
                "enforcement": "active",
                "conditions": {
                    "ref_name": {
                        "include": ["refs/heads/release-controller-state"],
                        "exclude": [],
                    }
                },
                "bypass_actors": [
                    {
                        "actor_id": 100,
                        "actor_type": "Integration",
                        "bypass_mode": "always",
                    }
                ],
                "rules": [{"type": "update"}],
            },
            {
                "id": 2,
                "target": "tag",
                "enforcement": "active",
                "conditions": {
                    "ref_name": {"include": ["refs/tags/v*"], "exclude": []}
                },
                "bypass_actors": [],
                "rules": [
                    {"type": "update"},
                    {"type": "deletion"},
                    {"type": "non_fast_forward"},
                ],
            },
            {
                "id": 3,
                "target": "branch",
                "enforcement": "active",
                "conditions": {
                    "ref_name": {
                        "include": ["refs/heads/release-controller-state"],
                        "exclude": [],
                    }
                },
                "bypass_actors": [],
                "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}],
            },
        ]
        self.rules.append(
            {
                "id": 4,
                "target": "tag",
                "enforcement": "active",
                "conditions": {
                    "ref_name": {"include": ["refs/tags/v*"], "exclude": []}
                },
                "bypass_actors": [
                    {
                        "actor_id": 200,
                        "actor_type": "Integration",
                        "bypass_mode": "always",
                    }
                ],
                "rules": [{"type": "creation"}],
            }
        )

    def branch(self, name):
        return {"name": name, "protected": True, "commit": {"sha": "a" * 40}}

    def pages(self, endpoint):
        assert endpoint == "rulesets"
        return self.rules

    def _request(self, resource, page):
        if resource.startswith("apps/"):
            return {"id": 100, "slug": "release-control"}
        if resource.startswith("users/"):
            return {"id": 77, "login": "release-control[bot]", "type": "Bot"}
        return {"id": 456, "login": "maintainer"}

    def get(self, endpoint, **kwargs):
        if endpoint == "actions/workflows/release-controller.yml":
            return {
                "id": 10,
                "state": "active",
                "path": ".github/workflows/release-controller.yml",
            }
        if endpoint in {"actions/secrets", "actions/organization-secrets"}:
            return {"total_count": 0, "secrets": []}
        if endpoint.startswith("environments/") and endpoint.endswith("/secrets"):
            names = ["RELEASE_CONTROL_APP_ID", "RELEASE_CONTROL_APP_PRIVATE_KEY"]
            if "release-control/" not in endpoint:
                names += [
                    "RELEASE_PUBLISHING_APP_ID",
                    "RELEASE_PUBLISHING_APP_PRIVATE_KEY",
                ]
            return {
                "total_count": len(names),
                "secrets": [{"name": name} for name in names],
            }
        if endpoint.endswith("/protection"):
            return {
                "enforce_admins": {"enabled": True},
                "allow_force_pushes": {"enabled": False},
                "allow_deletions": {"enabled": False},
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews": True,
                    "bypass_pull_request_allowances": {
                        "apps": [],
                        "users": [],
                        "teams": [],
                    },
                },
            }
        if endpoint == "":
            return {
                "id": 123,
                "full_name": self.slug,
                "default_branch": "main",
                "has_issues": True,
                "fork": False,
            }
        if endpoint.endswith("deployment-branch-policies"):
            return {
                "total_count": 1,
                "branch_policies": [{"name": "main", "type": "branch"}],
            }
        if endpoint.startswith("environments/"):
            return copy.deepcopy(self.env)
        if endpoint.startswith("rulesets/"):
            return copy.deepcopy(self.rules[int(endpoint.split("/")[-1]) - 1])
        if endpoint.endswith("/permission"):
            return {"role_name": "maintain", "permission": "write", "user": {"id": 456}}
        raise AssertionError(endpoint)


def test_verified_controls_and_current_numeric_actor():
    api = Controls()
    assert verify_controls(api, api.policy, "main") == 77
    assert actor_role(api, 456) == "maintain"


@pytest.mark.parametrize(
    "mutation", ["self", "bypass", "reviewers", "ref", "app", "state", "tag"]
)
def test_missing_or_weak_controls_are_rejected(mutation):
    api = Controls()
    if mutation == "self":
        api.env["protection_rules"][0]["prevent_self_review"] = False
    elif mutation == "bypass":
        api.env["can_admins_bypass"] = True
    elif mutation == "reviewers":
        api.env["protection_rules"] = []
    elif mutation == "ref":
        api.env["deployment_branch_policy"]["protected_branches"] = True
    elif mutation == "app":
        api.rules[0]["bypass_actors"][0]["actor_id"] = 200
    elif mutation == "state":
        api.rules[0]["rules"].pop()
    else:
        api.rules[1]["bypass_actors"] = [
            {"actor_type": "RepositoryRole", "actor_id": 5, "bypass_mode": "always"}
        ]
    with pytest.raises(ControllerError):
        verify_controls(api, api.policy, "main")


def test_stale_role_or_changed_user_never_grants_authority():
    api = Controls()
    api.get = lambda endpoint: {
        "role_name": "maintain",
        "permission": "write",
        "user": {"id": 999},
    }
    with pytest.raises(ControllerError):
        actor_role(api, 456)


def test_control_credentials_cannot_fall_back_to_repository_secrets():
    api = Controls()
    original = api.get

    def get(endpoint, **kwargs):
        if endpoint == "actions/secrets":
            return {
                "total_count": 1,
                "secrets": [{"name": "RELEASE_CONTROL_APP_PRIVATE_KEY"}],
            }
        return original(endpoint, **kwargs)

    api.get = get
    with pytest.raises(ControllerError):
        verify_controls(api, api.policy, "main")


def test_control_app_cannot_receive_tag_creation_bypass():
    api = Controls()
    api.rules[3]["bypass_actors"][0]["actor_id"] = 100
    with pytest.raises(ControllerError):
        verify_controls(api, api.policy, "main")
