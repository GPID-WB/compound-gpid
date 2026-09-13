"""Exact adopted Release/ref checks, including real REST object URL fields."""

import json
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.history import adopted_history
from cg_release.models import Policy, canonical_bytes, load_record


class History:
    """Read-only fixture retaining real REST identity fields."""

    def __init__(self, *, legacy: bool = False) -> None:
        self.tag = "v1.0.0.1" if legacy else "v1.0.0"
        self.release = {
            "id": 1,
            "tag_name": self.tag,
            "draft": False,
            "prerelease": False,
            "published_at": "2026-01-01T00:00:00Z",
        }
        self.ref = {
            "ref": "refs/tags/" + self.tag,
            "object": {"sha": "a" * 40, "type": "commit"},
            "repository_id": 123,
        }
        data = json.loads((Path(__file__).parent / "fixtures/policy.json").read_bytes())
        data["bootstrap"] = [
            {
                "release_id": 1,
                "tag": self.tag,
                "commit": "a" * 40,
                "line": "current",
                "version": "1.0.0",
                "legacy_version": "1.0.0.1" if legacy else None,
                "projections": {},
            }
        ]
        self.policy = load_record(Policy, canonical_bytes(data))

    def pages(self, _endpoint: str) -> list:
        return [self.release]

    def refs(self) -> list:
        return [self.ref]

    def get(self, _endpoint: str) -> dict:
        return {
            "ref": self.ref["ref"],
            "object": {
                **self.ref["object"],
                "url": "https://api.github.com/repos/owner/repo/git/commits/"
                + "a" * 40,
            },
        }


@pytest.mark.parametrize("legacy", [False, True])
def test_adopted_exact_tag_survives_rest_url_fields_and_legacy_mapping(
    legacy: bool,
) -> None:
    api = History(legacy=legacy)
    history, occupied = adopted_history(api, api.policy)
    assert occupied == ["1.0.0"] and history[0]["tag"] == api.tag


@pytest.mark.parametrize(
    "mutation", ["draft", "wrong-id", "wrong-commit", "unpublished", "wrong-repo"]
)
def test_conflicting_or_incomplete_adoption_fails(mutation: str) -> None:
    api = History()
    if mutation == "draft":
        api.release["draft"] = True
    elif mutation == "wrong-id":
        api.release["id"] = 2
    elif mutation == "wrong-commit":
        api.ref["object"]["sha"] = "b" * 40
    elif mutation == "unpublished":
        api.release["published_at"] = None
    else:
        api.ref["repository_id"] = 999
    with pytest.raises(ControllerError):
        adopted_history(api, api.policy)
