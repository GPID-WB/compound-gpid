"""Explicit reviewed recovery adopts existing exact tags without publishing them."""

import base64
import hashlib

import pytest

from cg_release.events import ControllerError
from cg_release.git_journal import blob_id
from cg_release.journal import digest
from cg_release.recovery_models import PublicTag, RecoveryDirective
from cg_release.signing import create_tag
from cg_release.stranded_recovery import recover_publication


def test_existing_reviewed_directive_without_evidence_base_keeps_its_digest():
    from test_lifecycle import receipt_fixture

    from cg_release.models import canonical_bytes, load_record

    spec = RecoveryDirective(
        operation="source-exception",
        repository_id=123,
        policy_digest="b" * 64,
        reason="Previously reviewed source exception",
        request=receipt_fixture().request,
        tag=PublicTag(
            **create_tag("v1.0.0", "d" * 40, "Fixture", "f@example.invalid", 1720000000)
        ),
        release_sha="d" * 40,
        release_tree="e" * 40,
    )
    archived = spec.model_dump(mode="json")
    archived.pop("evidence_base", None)
    raw = canonical_bytes(archived)
    assert (
        digest(load_record(RecoveryDirective, raw)) == hashlib.sha256(raw).hexdigest()
    )


@pytest.fixture
def stranded_case(publication_context):
    context, original, remote, _, _ = publication_context
    request = original.request.model_copy(
        update={
            "nonce": "e" * 32,
            "requester_id": 8,
            "version": "1.1.0",
            "tag": "v1.1.0",
            "source_sha": "d" * 40,
            "repository_slug": context.api.slug,
        }
    )
    tag = create_tag(
        request.tag, "d" * 40, "Fixture", "fixture@example.invalid", 1720000000
    )
    spec = RecoveryDirective(
        operation="stranded-publication",
        repository_id=123,
        policy_digest=digest(context.policy),
        reason="Reviewed immutable stranded tag",
        request=request,
        tag=PublicTag(**tag),
        release_tree="e" * 40,
        release_sha="d" * 40,
    )
    get = context.api.get
    raw = b'{"version":"1.1.0"}\n'
    oid = blob_id(raw)

    def recovery_get(path, **kwargs):
        if path == "git/commits/" + "d" * 40:
            return {"sha": "d" * 40, "tree": {"sha": "e" * 40}}
        if path.startswith("git/trees/"):
            return {
                "sha": "e" * 40,
                "truncated": False,
                "tree": [
                    {
                        "path": "package.json",
                        "type": "blob",
                        "mode": "100644",
                        "sha": oid,
                    }
                ],
            }
        if path == "git/blobs/" + oid:
            return {
                "sha": oid,
                "encoding": "base64",
                "size": len(raw),
                "content": base64.b64encode(raw).decode(),
            }
        return get(path, **kwargs)

    context.api.get = recovery_get
    old_request = context.api._request
    context.api._request = lambda resource, page=None, **kw: (
        recovery_get(
            resource.removeprefix("repos/owner/repo/").removesuffix("?recursive=1")
        )
        if "/git/trees/" in resource
        else old_request(resource, page, **kw)
    )
    context.api.refs = lambda: [
        {
            "repository_id": 123,
            "ref": "refs/tags/" + request.tag,
            "object": {"type": "tag", "sha": tag["oid"]},
        }
    ]
    remote.tag = {"type": "tag", "oid": tag["oid"], "commit": "d" * 40}
    return context, spec, remote, tag


def test_audited_stranded_tag_enters_builds_and_keeps_exact_tag(stranded_case):
    context, spec, remote, tag = stranded_case
    result = recover_publication(
        context,
        spec,
        actor_id=8,
        run_id=91,
        directive_digest=digest(spec),
        remote=remote,
    )
    recovered = context.journal.get(result.request_id)
    assert recovered.state == "building" and recovered.publication_started
    assert recovered.evidence["publication-tag-object"] == tag
    assert not remote.writes and not recovered.published
    again = recover_publication(
        context,
        spec,
        actor_id=8,
        run_id=91,
        directive_digest=digest(spec),
        remote=remote,
    )
    assert again == result
    from cg_release.stranded_recovery import recovery_grant

    changed = spec.model_copy(
        update={"operation": "source-exception", "allow_source_exception": True}
    )
    recover_publication(
        context,
        changed,
        actor_id=8,
        run_id=90,
        directive_digest=digest(changed),
        remote=remote,
    )
    grant = recovery_grant(context, context.journal.get(result.request_id))
    assert grant.run_id == 90 and grant.directive.allow_source_exception


def test_stranded_recovery_digest_or_actor_mismatch_denies_writes(publication_context):
    context, record, remote, _, _ = publication_context
    tag = create_tag(
        record.request.tag, "d" * 40, "Fixture", "fixture@example.invalid", 1720000000
    )
    spec = RecoveryDirective(
        operation="stranded-publication",
        repository_id=123,
        policy_digest=digest(context.policy),
        reason="Inspected recovery",
        request=record.request,
        tag=PublicTag(**tag),
        release_tree="e" * 40,
        release_sha="d" * 40,
    )
    with pytest.raises(ControllerError):
        recover_publication(
            context,
            spec,
            actor_id=8,
            run_id=91,
            directive_digest="0" * 64,
            remote=remote,
        )
    assert not remote.writes
