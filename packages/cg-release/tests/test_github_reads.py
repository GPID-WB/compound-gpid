"""Read transport tests use actual gh --include HTTP response framing."""

import json
import subprocess
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.github import GitHubReads


def response(body: object, status: int = 200) -> subprocess.CompletedProcess:
    """Make gh wire output, e.g. response([], 200), without a network call."""
    return subprocess.CompletedProcess(
        [],
        0 if status == 200 else 1,
        f"HTTP/2.0 {status} Status\r\nContent-Type: application/json\r\n\r\n"
        f"{json.dumps(body)}",
        "",
    )


def test_pagination_after_one_hundred_and_read_only_argv(tmp_path: Path) -> None:
    calls = []

    def run(
        tool: str, args: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess:
        calls.append((tool, args, kwargs))
        return response(
            [{"id": i} for i in range(100)] if len(calls) == 1 else [{"id": 100}]
        )

    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=run)
    assert len(api.pages("releases")) == 101
    assert len(calls) == 2
    for tool, args, kwargs in calls:
        assert tool == "gh"
        assert args[:2] == ["api", "--method"] and args[2] == "GET"
        assert "--include" in args and "--hostname" in args
        assert kwargs["timeout"] <= 20
    assert "page=2" in calls[-1][1][-1]


def test_exact_commit_comparison_does_not_enable_path_traversal(tmp_path):
    calls = []

    def run(tool, args, **kwargs):
        calls.append(args[-1])
        return response({"status": "ahead"})

    api = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=run)
    endpoint = "compare/" + "a" * 40 + "..." + "b" * 40
    assert api.get(endpoint)["status"] == "ahead"
    assert calls == ["repos/owner/repo/" + endpoint]
    for unsafe in [
        "compare/../releases",
        endpoint + "/../releases",
        "compare/main...dev",
    ]:
        with pytest.raises(ControllerError):
            api.get(unsafe)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "status,code", [(401, "E_AUTH"), (403, "E_FORBIDDEN"), (404, "E_NOT_FOUND")]
)
def test_http_errors_are_not_empty_history(
    tmp_path: Path, status: int, code: str
) -> None:
    api = GitHubReads(
        "github.com",
        "owner/repo",
        cwd=tmp_path,
        runner=lambda *_a, **_k: response({"message": "opaque server body"}, status),
    )
    with pytest.raises(ControllerError) as error:
        api.get("releases")
    assert error.value.code == code
    assert "opaque" not in str(error.value)


def test_invalid_json_shape_and_duplicate_page_fail(tmp_path: Path) -> None:
    for body in ({"message": "not a list"}, [1], [{"id": 1}] * 100):
        api = GitHubReads(
            "github.com",
            "owner/repo",
            cwd=tmp_path,
            runner=lambda *_a, **_k: response(body),
        )
        with pytest.raises(ControllerError):
            api.pages("releases")


def test_deadline_prevents_process_and_external_endpoint(tmp_path: Path) -> None:
    calls = []
    api = GitHubReads(
        "github.com",
        "owner/repo",
        cwd=tmp_path,
        runner=lambda *_a, **_k: calls.append(True),
        clock=lambda: 10,
        deadline=9,
    )
    with pytest.raises(ControllerError):
        api.get("releases")
    assert calls == []


def test_read_retry_is_bounded_and_uses_injected_clock(tmp_path: Path) -> None:
    calls, waits = [], []

    def run(*_a: object, **_k: object) -> subprocess.CompletedProcess:
        calls.append(1)
        return response({}, 503)

    api = GitHubReads(
        "github.com",
        "owner/repo",
        cwd=tmp_path,
        runner=run,
        clock=lambda: 0,
        sleep=waits.append,
    )
    with pytest.raises(ControllerError):
        api.get("")
    assert len(calls) == 3 and waits == [0.25, 0.5]
    for endpoint in ("https://evil.example/x", "../issues", "releases?token=secret"):
        with pytest.raises(ControllerError):
            api.get(endpoint)
    assert len(calls) == 3


def test_tag_cursor_pagination_preserves_repository_and_object_identity(
    tmp_path: Path,
) -> None:
    calls = []

    def run(
        _tool: str, args: list[str], **_kwargs: object
    ) -> subprocess.CompletedProcess:
        calls.append(args)
        first = len(calls) == 1
        return response(
            {
                "data": {
                    "repository": {
                        "databaseId": 123,
                        "refs": {
                            "nodes": [
                                {
                                    "name": f"v1.0.{i}",
                                    "target": {"oid": "a" * 40, "__typename": "Commit"},
                                }
                                for i in (range(100) if first else [100])
                            ],
                            "pageInfo": {
                                "hasNextPage": first,
                                "endCursor": "cursor1" if first else "cursor2",
                            },
                        },
                    }
                }
            }
        )

    result = GitHubReads("github.com", "owner/repo", cwd=tmp_path, runner=run).refs()
    assert len(result) == 101 and result[-1]["repository_id"] == 123
    assert result[-1]["ref"] == "refs/tags/v1.0.100"
    assert any("cursor1" in arg for arg in calls[-1]) and calls[-1][2] == "GET"
    assert calls[-1][-1] == "graphql"


@pytest.mark.parametrize(
    "body", [{}, {"data": {"repository": None}}, {"errors": [{"message": "denied"}]}]
)
def test_tag_cursor_wrong_shapes_fail_closed(tmp_path: Path, body: dict) -> None:
    api = GitHubReads(
        "github.com",
        "owner/repo",
        cwd=tmp_path,
        runner=lambda *_a, **_k: response(body),
    )
    with pytest.raises(ControllerError):
        api.refs()
