"""Bind merge/squash/rebase results to reviewed head, expected tree and checks."""

import copy
from types import SimpleNamespace

import pytest

from cg_release.events import ControllerError
from cg_release.reviewed_commit import verify_merge


def fixture():
    request = SimpleNamespace(
        repository_id=123, requester_id=7, source_sha="a" * 40, source_branch="feature"
    )
    prepared = {
        "number": 42,
        "id": 99,
        "head": "b" * 40,
        "tree": "c" * 40,
        "branch": "release-controller/nonce",
        "source_sha": request.source_sha,
    }
    pr = {
        "number": 42,
        "id": 99,
        "merged": True,
        "state": "closed",
        "draft": False,
        "merge_commit_sha": "d" * 40,
        "head": {
            "sha": prepared["head"],
            "ref": prepared["branch"],
            "repo": {"id": 123},
        },
        "base": {"ref": "feature", "repo": {"id": 123}},
    }
    commit = {
        "sha": "d" * 40,
        "tree": {"sha": prepared["tree"]},
        "parents": [{"sha": "a" * 40}, {"sha": "b" * 40}],
    }
    reviews = [
        {"id": 10, "user": {"id": 8}, "state": "APPROVED", "commit_id": "b" * 40}
    ]
    api = SimpleNamespace(
        get=lambda endpoint: pr if endpoint == "pulls/42" else commit,
        pages=lambda endpoint: reviews,
        branch=lambda name: {"commit": {"sha": "d" * 40}, "protected": False},
    )
    return request, prepared, pr, commit, reviews, api


@pytest.mark.parametrize("parents", [["a", "b"], ["a"]])
def test_exact_merge_and_single_commit_squash_or_rebase(parents):
    request, prepared, _, commit, _, api = fixture()
    commit["parents"] = [{"sha": p * 40} for p in parents]
    result = verify_merge(
        api,
        request,
        prepared,
        checks=lambda sha: [{"id": 21}],
        role=lambda uid: "write",
    )
    assert result["release_sha"] == "d" * 40 and result["review_ids"] == [10]


@pytest.mark.parametrize(
    "case",
    [
        "head",
        "tree",
        "parent",
        "self",
        "stale",
        "changes",
        "revoked",
        "checks",
        "shape",
    ],
)
def test_unreviewed_or_changed_release_is_rejected(case):
    request, prepared, pr, commit, reviews, api = fixture()

    def role(uid):
        return "read" if case == "revoked" else "write"

    def checks(sha):
        return [] if case == "checks" else [{"id": 21}]

    if case == "head":
        pr["head"]["sha"] = "e" * 40
    elif case == "tree":
        commit["tree"]["sha"] = "e" * 40
    elif case == "parent":
        commit["parents"][0]["sha"] = "e" * 40
    elif case == "self":
        reviews[0]["user"]["id"] = 7
    elif case == "stale":
        reviews[0]["commit_id"] = "e" * 40
    elif case == "changes":
        reviews.append(
            {**copy.deepcopy(reviews[0]), "id": 11, "state": "CHANGES_REQUESTED"}
        )
    elif case == "shape":
        commit["parents"] = "invalid"
    with pytest.raises(ControllerError):
        verify_merge(api, request, prepared, checks=checks, role=role)


def test_open_pr_is_waiting_not_release_evidence():
    request, prepared, pr, _, _, api = fixture()
    pr.update(merged=False, state="open", merge_commit_sha=None)
    api.branch = lambda name: {
        "commit": {"sha": request.source_sha},
        "protected": False,
    }
    assert (
        verify_merge(
            api, request, prepared, checks=lambda sha: [], role=lambda uid: "write"
        )
        is None
    )


def test_current_protected_branch_review_count_is_required():
    request, prepared, _, _, reviews, api = fixture()
    original = api.get
    api.branch = lambda name: {"commit": {"sha": "d" * 40}, "protected": True}
    api.get = lambda endpoint: (
        {"required_pull_request_reviews": {"required_approving_review_count": 2}}
        if endpoint.endswith("/protection")
        else original(endpoint)
    )
    with pytest.raises(ControllerError):
        verify_merge(
            api,
            request,
            prepared,
            checks=lambda sha: [{"id": 21}],
            role=lambda uid: "write",
        )
    reviews.append(
        {"id": 11, "user": {"id": 9}, "state": "APPROVED", "commit_id": "b" * 40}
    )
    assert verify_merge(
        api,
        request,
        prepared,
        checks=lambda sha: [{"id": 21}],
        role=lambda uid: "write",
    )["review_ids"] == [10, 11]
