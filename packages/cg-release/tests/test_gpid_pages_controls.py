"""Verify the Pages credential environment through the real GitHub reader."""

import json
from types import SimpleNamespace

import pytest
from test_authority import Controls

from cg_release.authority import verify_controls
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.models import ProfilePolicy


@pytest.mark.parametrize(
    "mutation", ["valid", "dev-ref", "bypass", "secrets", "reviewers", "publishing-key"]
)
def test_pages_control_key_cannot_be_exposed_to_source_refs(tmp_path, mutation):
    fixture = Controls()
    profile = ProfilePolicy(
        bridge=None,
        payload_directory="releases",
        latest_payload="releases/latest.json",
        attestation_directory=".github/shared/skill-management/release-attestations",
        docs_workflow=".github/workflows/release-controller-docs.yml",
    )
    policy = fixture.policy.model_copy(
        update={"gpid_profile": "v1", "profile": profile}
    )

    def transport(executable, argv, **kwargs):
        assert executable == "gh" and argv[:3] == ["api", "--method", "GET"]
        resource = argv[-1].partition("?")[0]
        if resource.startswith("repos/example/generic"):
            endpoint = resource.removeprefix("repos/example/generic").lstrip("/")
            value = (
                fixture.rules
                if endpoint == "rulesets"
                else (
                    fixture.branch("main")
                    if endpoint == "branches/main"
                    else fixture.get(endpoint)
                )
            )
            if (
                endpoint == "environments/github-pages/deployment-branch-policies"
                and mutation == "dev-ref"
            ):
                value["branch_policies"][0]["name"] = "dev"
            if endpoint == "environments/github-pages/secrets":
                if mutation != "publishing-key":
                    names = (
                        []
                        if mutation == "secrets"
                        else [
                            "RELEASE_CONTROL_APP_ID",
                            "RELEASE_CONTROL_APP_PRIVATE_KEY",
                        ]
                    )
                    value = {
                        "total_count": len(names),
                        "secrets": [{"name": name} for name in names],
                    }
            if endpoint == "environments/github-pages":
                if mutation == "bypass":
                    value["can_admins_bypass"] = True
                if mutation == "reviewers":
                    value["protection_rules"] = []
        else:
            value = fixture._request(resource, None)
        return SimpleNamespace(
            returncode=0, stdout="HTTP/2.0 200 OK\n\n" + json.dumps(value)
        )

    api = GitHubReads("github.com", "example/generic", cwd=tmp_path, runner=transport)
    if mutation == "valid":
        assert verify_controls(api, policy, "main") == 77
    else:
        with pytest.raises(ControllerError, match="protections"):
            verify_controls(api, policy, "main")
