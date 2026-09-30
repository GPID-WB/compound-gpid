"""Actual gh wire envelopes and complete cursor inventory, with no live writes."""

import json
import subprocess
from pathlib import Path

import pytest

from cg_release.admission import Locator, discover, submit
from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.inbox import GitHubInbox
from cg_release.models import Request, load_record


def fixture_request() -> Request:
    return load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )


def test_real_wire_one_post_body_stdin_and_graphql_readback(tmp_path: Path) -> None:
    request = fixture_request()
    calls, bodies = [], []

    def runner(tool, argv, **kwargs):
        calls.append((tool, argv, kwargs))
        method = argv[argv.index("--method") + 1]
        if method == "POST":
            assert "--input" in argv
            body = json.loads(kwargs["input_text"])
            bodies.append(body["body"])
            return subprocess.CompletedProcess(
                argv, 0, "HTTP/2.0 201 Created\n\n{}", ""
            )
        if argv[-1].endswith(request.repository_slug):
            payload = {
                "id": request.repository_id,
                "full_name": request.repository_slug,
                "has_issues": True,
            }
        else:
            assert argv[-1] == "graphql"
            payload = {
                "data": {
                    "repository": {
                        "databaseId": request.repository_id,
                        "issues": {
                            "nodes": [
                                {
                                    "id": "I_wire",
                                    "number": 7,
                                    "body": bodies[0],
                                    "url": f"https://{request.host}/{request.repository_slug}/issues/7",
                                    "author": {
                                        "__typename": "User",
                                        "databaseId": request.requester_id,
                                    },
                                    "lastEditedAt": None,
                                    "userContentEdits": {"totalCount": 0},
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    }
                }
            }
        return subprocess.CompletedProcess(
            argv, 0, "HTTP/2.0 200 OK\n\n" + json.dumps(payload), ""
        )

    api = GitHubReads(
        request.host, request.repository_slug, cwd=tmp_path, runner=runner
    )
    receipt = submit(request, GitHubInbox(api), lambda event: None)
    assert receipt.node_id == "I_wire"
    assert sum("POST" in argv for _, argv, _ in calls) == 1
    assert all("--hostname" in argv for _, argv, _ in calls)


def test_cursor_scan_exceeds_one_hundred_and_rejects_corruption(tmp_path: Path) -> None:
    request = fixture_request()
    api = GitHubReads(request.host, request.repository_slug, cwd=tmp_path)
    locator = Locator.from_request(request)
    api.get = lambda endpoint: {
        "id": request.repository_id,
        "full_name": request.repository_slug,
        "has_issues": True,
    }
    cursors = []

    def query(resource, page, *, query):
        cursors.append(query)
        first = len(cursors) == 1
        nodes = [
            {
                "id": f"I_{i}",
                "number": i + 1,
                "body": "unrelated",
                "url": "unused",
                "author": None,
                "lastEditedAt": None,
                "userContentEdits": {"totalCount": 0},
            }
            for i in (range(100) if first else range(100, 101))
        ]
        return {
            "data": {
                "repository": {
                    "databaseId": request.repository_id,
                    "issues": {
                        "nodes": nodes,
                        "pageInfo": {
                            "hasNextPage": first,
                            "endCursor": "cursor-100" if first else None,
                        },
                    },
                }
            }
        }

    api._request = query
    assert len(GitHubInbox(api).inventory(locator)) == 101
    assert 'after:"cursor-100"' in cursors[-1]
    api._request = lambda *args, **kwargs: {
        "data": {
            "repository": {
                "databaseId": request.repository_id,
                "issues": {
                    "nodes": [],
                    "pageInfo": {"hasNextPage": True, "endCursor": "bad"},
                },
            }
        }
    }
    with pytest.raises(ControllerError):
        discover(locator.encode(), GitHubInbox(api))


@pytest.mark.parametrize(
    "response",
    [None, [], {"id": 999, "has_issues": True}, {"id": 123, "has_issues": False}],
)
def test_inbox_repository_identity_and_issue_capability_fail_closed(
    tmp_path: Path, response: object
) -> None:
    request = fixture_request()
    api = GitHubReads(request.host, request.repository_slug, cwd=tmp_path)
    api.get = lambda endpoint: response
    with pytest.raises(ControllerError):
        GitHubInbox(api).inventory(Locator.from_request(request))
