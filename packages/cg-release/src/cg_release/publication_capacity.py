"""Bound the entire remaining publication transaction before irreversible effects."""

from cg_release.events import ControllerError
from cg_release.git_journal import transaction_files
from cg_release.journal import digest
from cg_release.journal_transport import encode_files
from cg_release.models import MAX_RECORD_BYTES, canonical_bytes


def preflight_publication(journal, record, inputs, tag, run_id):
    """Check a conservative complete record and its actual encoded envelope."""
    maximum_id = (1 << 64) - 1
    pending = {
        "publication-tag-object": tag,
        "publication-tag": {
            "oid": tag["oid"],
            "commit": inputs["release_sha"],
            "type": "tag",
        },
        "publication-draft": {
            "tag_name": inputs["tag"],
            "target_commitish": inputs["release_sha"],
            "notes_digest": digest({"notes": inputs["notes"]}),
            "prerelease": False,
        },
        "publication-publish": {"release_id": maximum_id, "make_latest": False},
        "publication-receipt": {
            "run_id": run_id,
            "inputs_digest": digest(inputs),
            "projections": inputs["projections"],
            "release_id": maximum_id,
            "tag_oid": tag["oid"],
            "release_sha": inputs["release_sha"],
            "assets": {f["name"]: maximum_id for f in inputs["inventory"]},
        },
        f"publication-owner-{run_id}": {
            "run_id": run_id,
            "credential_expires_at": maximum_id,
        },
        f"publication-owner-release-{run_id}": {
            "run_id": run_id,
            "released_by": run_id,
            "terminal_proof": None,
        },
        "publication-hooks": {
            "docs": {"verified": True, "release_sha": inputs["release_sha"]},
            "evidence": {"verified": True, "release_sha": inputs["release_sha"]},
        },
        f"publication-resume-{run_id}": {
            "tag_oid": tag["oid"],
            "inputs_digest": digest(inputs),
        },
    }
    pending.update(
        {
            f"publication-asset-{n}": item
            for n, item in enumerate(
                sorted(inputs["inventory"], key=lambda f: f["name"]), 1
            )
        }
    )
    evidence = {**pending, **record.evidence}
    # Reserve the largest in-flight operation as well as all final result data.
    projected = record.model_copy(
        update={
            "state": "complete",
            "published": True,
            "publication_started": True,
            "checkpoint": "publication-owner-release-" + str(run_id),
            "intent": {"operation": "publication-receipt", "digest": "f" * 64},
            "evidence": evidence,
        }
    )
    if len(canonical_bytes(projected)) > MAX_RECORD_BYTES - 1024:
        raise ControllerError(
            "E_JOURNAL_CAPACITY",
            "Remaining publication evidence cannot fit; no new remote "
            "publication write is permitted.",
        )
    event = {
        "schema_version": 1,
        "revision": 9999999999,
        "parent": "f" * 40,
        "previous": "f" * 64,
        "digest": "f" * 64,
        "occurred_at": "9999-12-31T23:59:59.999999+00:00",
        "audit": {"operation": "publication-receipt", "digest": "f" * 64},
        "record": projected.model_dump(mode="json"),
    }
    policy = getattr(journal.store, "policy", None)
    encode_files(
        getattr(
            getattr(journal.store, "api", None), "slug", record.request.repository_slug
        ),
        getattr(policy, "state_branch", "release-controller-state"),
        "f" * 40,
        transaction_files(canonical_bytes(event), projected),
        "Release controller checkpoint",
    )
