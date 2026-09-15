"""Protected worker functions use the real journal, gate verifier and publisher."""

import base64

import pytest
from journal_store import MemoryStore
from test_publisher import PublicationRemote

from cg_release.git_journal import blob_id
from cg_release.journal import Journal
from cg_release.journal_checkpoint import (
    atomic_build_checkpoint,
    atomic_publication_checkpoint,
)
from cg_release.prepare_stage import checkpoint
from cg_release.publish_worker import execute_publication, seal_publication


@pytest.fixture
def publication_context(ready_build):
    context, record, metadata, jobs = ready_build
    journal = Journal(MemoryStore())
    current = journal.admit(record.request)
    current = checkpoint(journal, current, "prepare", {"ok": True}, "awaiting-review")
    current = checkpoint(
        journal,
        current,
        "review-binding",
        record.evidence["review-binding"],
        "building",
    )
    current = atomic_build_checkpoint(
        journal,
        current,
        "build-request-1",
        record.evidence["build-request-1"],
        "building",
    )
    current = atomic_build_checkpoint(
        journal,
        current,
        "build-registration-1",
        record.evidence["build-registration-1"],
        "building",
    )
    current = checkpoint(
        journal,
        current,
        "build-evidence-1",
        record.evidence["build-evidence-1"],
        "building",
    )
    current = checkpoint(
        journal,
        current,
        "build-validated-1",
        record.evidence["build-validated-1"],
        "awaiting-approval",
    )
    current = atomic_publication_checkpoint(
        journal,
        current,
        "publication-request-1",
        {"nonce": "a" * 32, "mode": "initial", "reconfirmers": [8]},
        "awaiting-approval",
    )
    context.journal = journal
    context.default = "main"
    context.policy_sha = "d" * 40
    remote = PublicationRemote()
    context.api.pages = lambda endpoint: (
        [remote.release] if remote.release is not None else []
    )
    context.api.refs = lambda: (
        [
            {
                "repository_id": 123,
                "ref": "refs/tags/" + record.request.tag,
                "object": {"type": "tag", "sha": remote.tag["oid"]},
            }
        ]
        if remote.tag
        else []
    )
    run = {
        "id": 41,
        "run_attempt": 1,
        "path": ".github/workflows/release-controller-publish.yml",
        "event": "workflow_dispatch",
        "head_sha": context.policy_sha,
        "head_branch": "main",
        "repository": {"id": 123},
        "status": "in_progress",
        "created_at": "2026-09-12T00:00:00Z",
    }
    environment = {
        "id": 17,
        "name": "release-publish",
        "can_admins_bypass": False,
        "protection_rules": [
            {
                "type": "required_reviewers",
                "prevent_self_review": True,
                "reviewers": [{"type": "User", "reviewer": {"id": 9}}],
            }
        ],
    }
    reviews = [
        {
            "state": "approved",
            "user": {"id": 9},
            "environments": [{"id": 17, "name": "release-publish"}],
        }
    ]
    raw = b"# Reviewed release notes\n"
    oid = blob_id(raw)
    get_original = context.api.get

    def get(endpoint, **kwargs):
        if endpoint.startswith("git/ref/tags/"):
            return {
                "ref": "refs/tags/" + record.request.tag,
                "object": {"type": "tag", "sha": remote.tag["oid"]},
            }
        if endpoint.startswith("git/tags/"):
            return {
                "sha": remote.tag["oid"],
                "tag": record.request.tag,
                "object": {"type": "commit", "sha": remote.tag["commit"]},
            }
        if endpoint == "actions/runs/41":
            return run
        if endpoint == "environments/release-publish":
            return environment
        if endpoint == "actions/runs/41/approvals":
            return reviews
        if endpoint == "actions/runs/41/attempts/1/jobs":
            return {
                "total_count": 2,
                "jobs": [
                    {
                        "id": 61,
                        "name": "seal",
                        "run_id": 41,
                        "run_attempt": 1,
                        "status": "completed",
                        "conclusion": "success",
                    },
                    {
                        "id": 62,
                        "name": "publish",
                        "run_id": 41,
                        "run_attempt": 1,
                        "status": "in_progress",
                        "conclusion": None,
                    },
                ],
            }
        if endpoint.startswith("collaborators/"):
            uid = int(endpoint.split("/")[1].removeprefix("user"))
            return {"role_name": "maintain", "permission": "write", "user": {"id": uid}}
        if endpoint.startswith("git/trees/"):
            return {
                "sha": "e" * 40,
                "truncated": False,
                "tree": [
                    {
                        "path": "CHANGELOG.md",
                        "type": "blob",
                        "mode": "100644",
                        "sha": oid,
                        "size": len(raw),
                    }
                ],
            }
        if endpoint == "git/blobs/" + oid:
            return {
                "sha": oid,
                "encoding": "base64",
                "size": len(raw),
                "content": base64.b64encode(raw).decode(),
            }
        return get_original(endpoint, **kwargs)

    def request(resource, page=None, **kwargs):
        if resource.startswith("user/"):
            uid = int(resource.removeprefix("user/"))
            return {"id": uid, "login": f"user{uid}"}
        return get(
            resource.removeprefix("repos/owner/repo/").removesuffix("?recursive=1")
        )

    context.api.get = get
    context.api._request = request
    context.api.branch = lambda name: {"name": name, "commit": {"sha": "d" * 40}}
    env = {"GITHUB_RUN_ID": "41", "CG_RELEASE_TOKEN_EXPIRES_AT": "2026-09-12T01:00:00Z"}
    return context, current, remote, env, reviews


def test_seal_visible_then_exact_publication_and_complete(publication_context):
    context, record, remote, env, _ = publication_context
    saved, seal, url = seal_publication(context, record, "a" * 32, env, remote)
    assert "/blob/" in url and "/requests/" in url and url.endswith(".json")
    assert seal["inputs"]["inventory"][-1]["name"] == "release-provenance.json"
    assert not remote.writes
    result = execute_publication(context, saved, "a" * 32, env, remote, now=1789171200)
    assert result.state == "complete" and result.published
    assert remote.tag["commit"] == "d" * 40
    assert remote.release["draft"] is False and remote.latest == 71
    assert set(remote.assets) == {"package.whl", "release-provenance.json"}


def test_requester_approval_stops_before_owner_or_tag(publication_context):
    context, record, remote, env, reviews = publication_context
    saved, _, _ = seal_publication(context, record, "a" * 32, env, remote)
    reviews[0]["user"]["id"] = record.request.requester_id
    from cg_release.events import ControllerError

    with pytest.raises(ControllerError):
        execute_publication(context, saved, "a" * 32, env, remote, now=1789171200)
    assert not remote.writes
    assert not any(
        k.startswith("publication-owner-")
        for k in context.journal.get(record.request_id).evidence
    )


@pytest.mark.parametrize("failure", ["asset-package.whl", "publish"])
def test_fresh_approved_run_recovers_partial_upload_after_owner_expires(
    publication_context,
    failure,
):
    context, record, remote, env, _ = publication_context
    saved, _, _ = seal_publication(context, record, "a" * 32, env, remote)
    remote.fail = (failure, "before")
    from cg_release.events import ControllerError

    with pytest.raises(ControllerError, match="unresolved"):
        execute_publication(context, saved, "a" * 32, env, remote, now=1789171200)
    pending = context.journal.get(record.request_id)
    assert pending.state == "publishing" and pending.intent["operation"] == (
        "publication-asset-1" if failure.startswith("asset") else "publication-publish"
    )
    old_get = context.api.get
    if failure == "publish":
        context.policy_sha = "9" * 40
        context.api.branch = lambda name: {"name": name, "commit": {"sha": "9" * 40}}

    def get(endpoint, **kwargs):
        if endpoint == "actions/runs/41":
            return {**old_get(endpoint), "status": "completed"}
        if endpoint == "actions/runs/42":
            return {
                **old_get("actions/runs/41"),
                "id": 42,
                "head_sha": context.policy_sha,
                "created_at": "2026-09-12T02:00:00Z",
            }
        if endpoint == "actions/runs/42/approvals":
            return old_get("actions/runs/41/approvals")
        if endpoint == "actions/runs/42/attempts/1/jobs":
            return {
                "total_count": 2,
                "jobs": [
                    {**j, "run_id": 42}
                    for j in old_get("actions/runs/41/attempts/1/jobs")["jobs"]
                ],
            }
        if endpoint.startswith("compare/"):
            return {
                "status": "ahead",
                "merge_base_commit": {"sha": "d" * 40},
                "base_commit": {"sha": "d" * 40},
            }
        return old_get(endpoint, **kwargs)

    context.api.get = get
    old_request = context.api._request
    context.api._request = lambda resource, page=None, **kwargs: (
        get(resource.removeprefix("repos/owner/repo/"))
        if "/actions/runs/42/" in resource
        else old_request(resource, page, **kwargs)
    )
    record = atomic_publication_checkpoint(
        context.journal,
        pending,
        "publication-request-2",
        {"nonce": "b" * 32, "mode": "recovery", "reconfirmers": [8]},
        "publishing",
    )
    env.update(GITHUB_RUN_ID="42", CG_RELEASE_TOKEN_EXPIRES_AT="2026-09-12T03:00:00Z")
    saved, _, _ = seal_publication(context, record, "b" * 32, env, remote)
    result = execute_publication(context, saved, "b" * 32, env, remote, now=1789178400)
    assert result.state == "complete"
    assert remote.writes.count("tag") == 1 and remote.writes.count("draft") == 1
    assert len(remote.assets) == 2 and remote.writes.count("publish") == (
        2 if failure == "publish" else 1
    )
