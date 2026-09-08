"""Bounded public GitHub tree/blob acquisition tests."""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Dict, Tuple

import pytest

from skill_management.providers.github import (
    AcquisitionLimits,
    GitHubAcquisitionError,
    GitHubProvider,
    HttpResponse,
    normalize_public_github_origin,
)


COMMIT = "a" * 40
ROOT_TREE = "b" * 40
SKILL_TREE = "c" * 40


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


class FakeTransport:
    def __init__(self, responses: Dict[str, Tuple[int, Dict[str, str], bytes]]) -> None:
        self.responses = responses
        self.requests = []

    def get(self, url: str, *, accept: str, max_bytes: int) -> HttpResponse:
        self.requests.append((url, accept, max_bytes))
        suffix = url.split("/repos/acme/tools", 1)[1]
        status, headers, body = self.responses[suffix]
        if len(body) > max_bytes:
            raise GitHubAcquisitionError("HTTP body exceeds bounded response limit")
        return HttpResponse(status, headers, body)


def _responses(skill: bytes) -> Dict[str, Tuple[int, Dict[str, str], bytes]]:
    blob_sha = _git_blob(skill)
    metadata = {"content-type": "application/json"}
    return {
        f"/git/commits/{COMMIT}": (200, metadata, json.dumps({"sha": COMMIT, "tree": {"sha": ROOT_TREE}}).encode()),
        f"/git/trees/{ROOT_TREE}": (200, metadata, json.dumps({"truncated": False, "tree": [{"path": "skills", "type": "tree", "mode": "040000", "sha": SKILL_TREE}]}).encode()),
        f"/git/trees/{SKILL_TREE}": (200, metadata, json.dumps({"truncated": False, "tree": [{"path": "demo", "type": "tree", "mode": "040000", "sha": "d" * 40}]}).encode()),
        f"/git/trees/{'d' * 40}": (200, metadata, json.dumps({"truncated": False, "tree": [{"path": "SKILL.md", "type": "blob", "mode": "100644", "sha": blob_sha, "size": len(skill)}]}).encode()),
        f"/git/blobs/{blob_sha}": (200, {"content-type": "application/octet-stream"}, skill),
    }


def test_normalizes_only_credential_free_public_github_https_origins() -> None:
    assert normalize_public_github_origin("https://github.com/Acme/Tools.git") == (
        "https://github.com/acme/tools"
    )
    for origin in (
        "http://github.com/acme/tools",
        "https://user@github.com/acme/tools",
        "https://gitlab.com/acme/tools",
        "https://github.com/acme/tools?token=x",
    ):
        with pytest.raises(GitHubAcquisitionError):
            normalize_public_github_origin(origin)


def test_nonrecursive_tree_walk_declares_all_sizes_before_blob_reads() -> None:
    content = b'---\nname: demo\ndescription: "Demo"\n---\n# Demo\n'
    transport = FakeTransport(_responses(content))

    acquired = GitHubProvider(transport).acquire(
        "https://github.com/acme/tools", COMMIT, "skills/demo", AcquisitionLimits()
    )

    assert acquired.origin == "https://github.com/acme/tools"
    assert acquired.files[0].path == "SKILL.md"
    assert acquired.files[0].content == content
    assert transport.requests[-1][1] == "application/vnd.github.raw+json"


def test_declared_total_limit_blocks_before_any_blob_request() -> None:
    content = b"x" * 20
    responses = _responses(content)
    transport = FakeTransport(responses)

    with pytest.raises(GitHubAcquisitionError, match="declared"):
        GitHubProvider(transport).acquire(
            "https://github.com/acme/tools",
            COMMIT,
            "skills/demo",
            AcquisitionLimits(max_total_bytes=10),
        )

    assert not any("/git/blobs/" in request[0] for request in transport.requests)


def test_metadata_entry_and_per_file_ceilings_block_before_blob_reads() -> None:
    content = b"0123456789"
    with pytest.raises(GitHubAcquisitionError, match="bounded|metadata"):
        GitHubProvider(FakeTransport(_responses(content))).acquire(
            "https://github.com/acme/tools",
            COMMIT,
            "skills/demo",
            AcquisitionLimits(max_metadata_bytes=10),
        )

    transport = FakeTransport(_responses(content))
    with pytest.raises(GitHubAcquisitionError, match="per-file"):
        GitHubProvider(transport).acquire(
            "https://github.com/acme/tools",
            COMMIT,
            "skills/demo",
            AcquisitionLimits(max_file_bytes=5),
        )
    assert not any("/git/blobs/" in request[0] for request in transport.requests)

    responses = _responses(content)
    selected_key = f"/git/trees/{'d' * 40}"
    responses[selected_key] = (
        200,
        {"content-type": "application/json"},
        json.dumps(
            {
                "truncated": False,
                "tree": [
                    {
                        "path": "nested",
                        "type": "tree",
                        "mode": "040000",
                        "sha": "e" * 40,
                    }
                ],
            }
        ).encode(),
    )
    responses[f"/git/trees/{'e' * 40}"] = (
        200,
        {"content-type": "application/json"},
        json.dumps(
            {
                "truncated": False,
                "tree": [
                    {
                        "path": "deeper",
                        "type": "tree",
                        "mode": "040000",
                        "sha": "f" * 40,
                    }
                ],
            }
        ).encode(),
    )
    transport = FakeTransport(responses)
    with pytest.raises(GitHubAcquisitionError, match="depth"):
        GitHubProvider(transport).acquire(
            "https://github.com/acme/tools",
            COMMIT,
            "skills/demo",
            AcquisitionLimits(max_tree_depth=1),
        )
    assert not any("/git/blobs/" in request[0] for request in transport.requests)

    responses = _responses(content)
    tree_key = f"/git/trees/{'d' * 40}"
    tree = json.loads(responses[tree_key][2])
    second = dict(tree["tree"][0])
    second["path"] = "guide.md"
    second["sha"] = _git_blob(b"guide")
    second["size"] = 5
    tree["tree"].append(second)
    responses[tree_key] = (
        200,
        {"content-type": "application/json"},
        json.dumps(tree).encode(),
    )
    transport = FakeTransport(responses)
    with pytest.raises(GitHubAcquisitionError, match="entry"):
        GitHubProvider(transport).acquire(
            "https://github.com/acme/tools",
            COMMIT,
            "skills/demo",
            AcquisitionLimits(max_entries=1),
        )
    assert not any("/git/blobs/" in request[0] for request in transport.requests)


def test_redirect_outside_path_and_oversized_raw_body_fail_closed() -> None:
    content = b"safe"
    responses = _responses(content)
    responses[f"/git/commits/{COMMIT}"] = (
        302,
        {"location": "https://example.invalid"},
        b"redirect",
    )
    with pytest.raises(GitHubAcquisitionError):
        GitHubProvider(FakeTransport(responses)).acquire(
            "https://github.com/acme/tools", COMMIT, "skills/demo", AcquisitionLimits()
        )

    with pytest.raises(GitHubAcquisitionError, match="component"):
        GitHubProvider(FakeTransport(_responses(content))).acquire(
            "https://github.com/acme/tools", COMMIT, "outside/demo", AcquisitionLimits()
        )

    responses = _responses(content)
    blob_key = next(key for key in responses if "/git/blobs/" in key)
    responses[blob_key] = (
        200,
        {"content-type": "application/octet-stream"},
        b"x" * 300000,
    )
    with pytest.raises(GitHubAcquisitionError, match="bounded"):
        GitHubProvider(FakeTransport(responses)).acquire(
            "https://github.com/acme/tools", COMMIT, "skills/demo", AcquisitionLimits()
        )


def test_truncated_tree_missing_size_submodule_and_object_mismatch_fail_closed() -> None:
    content = b"safe"
    mutations = ("truncated", "missing-size", "submodule", "executable", "mismatch")
    for mutation in mutations:
        responses = _responses(content)
        tree_key = f"/git/trees/{'d' * 40}"
        tree = json.loads(responses[tree_key][2])
        if mutation == "truncated":
            tree["truncated"] = True
        elif mutation == "missing-size":
            tree["tree"][0].pop("size")
        elif mutation == "submodule":
            tree["tree"][0].update(type="commit", mode="160000")
        elif mutation == "executable":
            tree["tree"][0].update(mode="100755")
        else:
            blob_key = next(key for key in responses if "/git/blobs/" in key)
            responses[blob_key] = (200, {"content-type": "application/octet-stream"}, b"changed")
        responses[tree_key] = (200, {"content-type": "application/json"}, json.dumps(tree).encode())

        with pytest.raises(GitHubAcquisitionError):
            GitHubProvider(FakeTransport(responses)).acquire(
                "https://github.com/acme/tools", COMMIT, "skills/demo", AcquisitionLimits()
            )
