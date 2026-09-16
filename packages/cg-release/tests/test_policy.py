"""Policy semantics, line membership, and current actor eligibility."""

import json
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.models import Policy, canonical_bytes, load_record
from cg_release.policy import approval_route, select_line, validate_policy

FIXTURE = Path(__file__).parent / "fixtures/policy.json"


def policy(**changes: object) -> Policy:
    """Load the strict fixture with explicit test changes, e.g. enabled=False."""
    data = json.loads(FIXTURE.read_bytes())
    data.update(changes)
    return load_record(Policy, canonical_bytes(data))


def test_policy_identity_and_unique_line_are_required() -> None:
    p = policy()
    validate_policy(p, repository_id=123, host="github.com")
    assert select_line(p, "main", None).id == "current"
    for repository_id, host in [(124, "github.com"), (123, "other.example")]:
        with pytest.raises(ControllerError):
            validate_policy(p, repository_id=repository_id, host=host)
    with pytest.raises(ControllerError):
        select_line(p, "feature", None)
    with pytest.raises(ControllerError):
        select_line(p, "feature", "current")


def test_ambiguous_membership_needs_explicit_eligible_line() -> None:
    data = json.loads(FIXTURE.read_bytes())
    data["release_lines"].append({**data["release_lines"][0], "id": "other"})
    p = load_record(Policy, canonical_bytes(data))
    with pytest.raises(ControllerError):
        select_line(p, "main", None)
    assert select_line(p, "main", "other").id == "other"


@pytest.mark.parametrize(
    "field,value",
    [
        (
            "apps",
            {"control": 100, "control_slug": "release-control", "publishing": 100},
        ),
        ("tag_prefix", "--bad"),
        ("state_branch", "main"),
        ("signing_required", True),
        ("metadata", [{"kind": "json", "path": "../x", "pointer": "/version"}]),
    ],
)
def test_policy_rejects_unsafe_semantics(field: str, value: object) -> None:
    with pytest.raises(ControllerError):
        validate_policy(policy(**{field: value}), repository_id=123, host="github.com")


@pytest.mark.parametrize("role", ["read", "triage", "unknown"])
def test_read_access_cannot_propose_publication(role: str) -> None:
    with pytest.raises(ControllerError):
        approval_route(policy(), "main", "1.1.0", role, "main", None)


def test_prerelease_branch_and_stable_override_rules() -> None:
    p = policy()
    assert (
        approval_route(p, "feature", "1.1.0-rc.1", "write", "main", None)
        == "release-publish"
    )
    assert (
        approval_route(p, "main", "1.1.0", "write", "main", None) == "release-publish"
    )
    with pytest.raises(ControllerError):
        approval_route(p, "feature", "1.1.0", "write", "main", "emergency")
    with pytest.raises(ControllerError):
        approval_route(p, "feature", "1.1.0", "maintain", "main", None)
    assert (
        approval_route(p, "feature", "1.1.0", "maintain", "main", "emergency")
        == "release-override"
    )
    assert (
        approval_route(
            policy(production_branches=[]), "default", "1.1.0", "admin", "default", None
        )
        == "release-publish"
    )
