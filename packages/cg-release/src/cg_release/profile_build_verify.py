"""Verify GPID snapshots and deployment capacity at the actual approval boundary."""

import hashlib
import io
import zipfile

from cg_release.events import ControllerError
from cg_release.profile_native import LOCK, NATIVE_ARTIFACT, verify_environment
from cg_release.profile_selection import (
    acquire,
    capacity,
    deployment_capacity,
    selection,
)
from cg_release.source_blobs import read_blobs
from cg_release.versions import parse_version


def verify_profile_artifact(context, record, sealed, registration, raw: bytes) -> dict:
    """Verify approved archive bytes, e.g. verify_profile_artifact(ctx, record, ticket,
    registration, archive). Returns the verified in-memory capacity view, not a
    journal payload. Raises ControllerError on identity or aggregate capacity.
    Read-only; the approved archive digest binds the checked inventory.
    """
    from cg_release.hooks import selected_profile

    declared = next(
        a for a in context.policy.build.artifacts if a.name == "release-docs.json"
    )
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        snapshot = archive.read(declared.path)
        try:
            native = archive.read(NATIVE_ARTIFACT)
        except KeyError:
            raise ControllerError(
                "E_NATIVE_ENVIRONMENT", "Missing native environment receipt."
            ) from None
    lock = read_blobs(context.api, sealed["release_tree"], [LOCK])[LOCK].content
    if hashlib.sha256(lock).hexdigest() != sealed["lock_digests"].get(LOCK):
        raise ControllerError("E_NATIVE_ENVIRONMENT", "Registered native lock changed.")
    verify_environment(
        native,
        lock,
        sha=sealed["release_sha"],
        run_id=registration["run_id"],
        run_attempt=registration["run_attempt"],
    )
    selected_profile(context.policy).verify_snapshot(
        snapshot,
        tag=record.request.tag,
        sha=sealed["release_sha"],
        run_id=registration["run_id"],
        run_attempt=registration["run_attempt"],
    )
    summary = capacity(snapshot)
    records = context.journal.records()
    if (
        not any(r.published for r in records)
        and not context.policy.profile.docs_baselines
    ):
        # First stable supplies its own default. A first pre-release fails selection.
        if parse_version(record.request.version).prerelease is None:
            deployment_capacity([(record.request.tag, summary)], record.request.tag)
            return summary
    snapshots, stable = selection(context)
    if parse_version(record.request.version).prerelease is None and parse_version(
        record.request.version
    ) > parse_version(stable[1:]):
        stable = record.request.tag
    items = [
        (item["tag"], capacity(data)) for item, data in acquire(context.api, snapshots)
    ]
    items.append((record.request.tag, summary))
    deployment_capacity(items, stable)
    return summary
