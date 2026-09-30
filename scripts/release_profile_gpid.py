"""Trusted GPID v1 hooks, bundled in the pinned controller wheel.

Example: selected_profile(policy).prepare(snapshot, tag=tag, version=version,
created_at=receipt.created_at). No target scripts run in the control job.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime

from cg_release.events import ControllerError
from cg_release.github import decode_json
from cg_release.metadata import Edit
from cg_release.models import canonical_bytes
from cg_release.profile_bridge import verify_bridge
from cg_release.profile_process import resource
from cg_release.profile_snapshot import verify_snapshot
from cg_release.profile_source import REQUIRED_FILES, source_blobs
from cg_release.versions import parse_version

VERSION = "v1"
__all__ = [
    "REQUIRED_FILES",
    "VERSION",
    "attestation",
    "complete",
    "prepare",
    "resource",
    "source_blobs",
    "validate_policy",
    "verify_bridge",
    "verify_snapshot",
]
REQUIRED_CHECKS = {
    ("release-controller-ci", ".github/workflows/release-controller-ci.yml"),
    ("gpid-native-profile", ".github/workflows/release-controller-build.yml"),
}


def validate_policy(policy) -> None:
    """Check the validated Policy's optional GPID installation contract.

    Returns None only for resolved bridge identities, both registered producers,
    declared native lock evidence and bounded docs output. Raises ControllerError
    for missing or incompatible fields. Example: validate_policy(policy) at preview.
    This is structural and read-only; verify_bridge separately rechecks remote proof.
    """
    if policy.profile is None or policy.profile.bridge is None:
        raise ControllerError(
            "E_BRIDGE_REQUIRED",
            "GPID profile requires reviewed bridge delivery evidence.",
        )
    if policy.host != "github.com" or policy.tag_prefix != "v":
        raise ControllerError(
            "E_PROFILE", "GPID v1 requires github.com and the v tag prefix."
        )
    bridge = policy.profile.bridge
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?", bridge.tag):
        raise ControllerError(
            "E_BRIDGE_REQUIRED", "Bridge must use the old updater release grammar."
        )
    if bridge.windows_run_id == bridge.unix_run_id:
        raise ControllerError(
            "E_BRIDGE_REQUIRED",
            "Bridge needs separate Windows and Unix clean-client runs.",
        )
    checks = {(c.name, c.workflow_path) for c in policy.required_checks}
    if not REQUIRED_CHECKS.issubset(checks):
        raise ControllerError(
            "E_PROFILE",
            "GPID profile requires source-bound six-cell CI and native/profile checks.",
        )
    if (
        policy.required_checks[0].workflow_path
        != ".github/workflows/release-controller-build.yml"
    ):
        raise ControllerError(
            "E_PROFILE", "The declared GPID build must own release artifacts."
        )
    if policy.build.argv != ["python", "scripts/release_profile_build.py"]:
        raise ControllerError(
            "E_PROFILE",
            "GPID build must use the declared unprivileged profile builder.",
        )
    artifacts = {a.name: a for a in policy.build.artifacts}
    if (
        not {
            "packages/cg-release/uv.lock",
            "packages/cg-release/pyproject.toml",
        }.issubset(policy.build.lock_paths)
        or "native-environment.json" not in artifacts
        or not artifacts["native-environment.json"].required
        or artifacts["native-environment.json"].path
        != "release-output/native-environment.json"
        or artifacts["native-environment.json"].max_bytes > 65536
    ):
        raise ControllerError(
            "E_PROFILE", "GPID requires exact locked native dependency evidence."
        )
    if (
        "release-docs.json" not in artifacts
        or not artifacts["release-docs.json"].required
        or artifacts["release-docs.json"].max_bytes > 67108864
    ):
        raise ControllerError(
            "E_PROFILE",
            "Approval must include the immutable release documentation snapshot.",
        )


def prepare(snapshot, *, tag: str, version: str, created_at: str) -> tuple[Edit, ...]:
    """Prepare exact payloads, e.g. prepare(snapshot, tag=tag, version=version,
    created_at=receipt.created_at).

    Args: verified source blobs, SemVer identity and bound UTC preparation time.
    Returns: Two exact edits for immutable payload and byte-identical latest.json.
    Raises: ControllerError for missing inputs, duplicate payload or invalid notes.
    No writes occur; publishedAt intentionally records the preparation timestamp.
    """
    parse_version(version)
    path = f"releases/{tag}.json"
    if (
        len(tag) > 200
        or tag != "v" + version
        or not set(REQUIRED_FILES).issubset(snapshot.blobs)
        or path in snapshot.blobs
    ):
        raise ControllerError(
            "E_PROFILE", "Required GPID inputs are missing or payload already exists."
        )
    try:
        datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except (ValueError, TypeError):
        raise ControllerError(
            "E_PROFILE", "A bound preparation timestamp is required."
        ) from None
    notes = snapshot.notes.strip()
    if (
        not notes
        or len(notes) > 16000
        or any((ord(c) < 32 and c not in "\n\t") or ord(c) == 127 for c in notes)
    ):
        raise ControllerError(
            "E_PROFILE", "Bound release notes are empty or exceed their limit."
        )
    url = f"https://{snapshot.host}/{snapshot.slug}"
    entries = [notes[index : index + 500] for index in range(0, len(notes), 500)]
    payload = {
        "schemaVersion": 1,
        "tag": tag,
        "publishedAt": created_at,
        "releaseDate": created_at[:10],
        "name": tag,
        "url": f"{url}/releases/tag/{tag}",
        "sourceUrl": f"{url}/tree/{tag}",
        "sections": [
            {"kind": "internal", "title": "Reviewed changes", "entries": entries}
        ],
    }
    raw = canonical_bytes(payload) + b"\n"
    return tuple(
        Edit(
            name,
            hashlib.sha256(snapshot.blobs[name].content).hexdigest()
            if name in snapshot.blobs
            else None,
            hashlib.sha256(raw).hexdigest(),
            raw,
        )
        for name in (path, "releases/latest.json")
    )


def attestation(record, payload: bytes, deprecations: dict, *, evidence_inputs=None) -> dict:
    """Create data after publication, e.g. attestation(record, payload, digests).

    Args: published record, exact reviewed payload bytes, verified deprecation hashes.
    evidence_inputs is the caller's exact sealed attempt view when a reviewed
    recovery uses a separate evidence PR; it supplies reviewed recovery provenance.
    Returns: A raw schema-v1 attestation dictionary, never a success flag or model.
    Raises: ControllerError for missing publication or payload identity. No writes.
    """
    if record.state not in {"published", "complete"} or not record.published:
        raise ControllerError("E_HOOK", "Attestation requires published release first.")
    receipt = record.evidence["publication-receipt"]
    if decode_json(payload.decode()).get("tag") != record.request.tag:
        raise ControllerError("E_HOOK", "Attestation payload identifies another tag.")
    return {
        "schema": "cg-skill-release-attestation-v1",
        "schemaVersion": 1,
        "releaseTag": record.request.tag,
        "tagRefObjectSha": receipt["tag_oid"],
        "peeledCommitSha": receipt["release_sha"],
        "releasePayloadSha256": hashlib.sha256(payload).hexdigest(),
        "deprecationRecordDigests": deprecations,
        "reviewReference": (evidence_inputs or record.evidence.get("profile-evidence-inputs", {})).get("recovery_review")
        or f"release preparation PR #{record.evidence['review-binding']['pr_number']}",
    }


def complete(context, record, *, resuming_actor_id=None) -> dict:
    """Advance hooks, e.g. complete(ctx, record, resuming_actor_id=7).

    Returns: A mapping of verified raw HookResult dictionaries; absent keys mean
    pending, never success. Raises ControllerError on stale authority or evidence.
    The keyword carries the applicable actor through all delayed effects. Writes
    only declared evidence PR/journal/dispatch changes after fresh authorization;
    it never changes the published tag, payload or release asset bytes.
    """
    from cg_release.profile_docs import docs_step
    from cg_release.profile_evidence import evidence_step

    if "publication-receipt" not in record.evidence:
        raise ControllerError(
            "E_HOOK", "Source success flags cannot prove publication."
        )
    results = {}
    evidence = evidence_step(
        context, record, attestation, resuming_actor_id=resuming_actor_id
    )
    if evidence is not None:
        results["evidence"] = evidence
    record = context.journal.get(record.request_id)
    docs = docs_step(context, record, resuming_actor_id=resuming_actor_id)
    if docs is not None:
        results["docs"] = docs
    return results
