"""Preserve exact public provenance independently of later approval/controller runs."""

import hashlib
import re

from cg_release.events import ControllerError
from cg_release.models import canonical_bytes


def tagger_identity(tag, timestamp):
    """Read the actual immutable tagger or the initial controller identity."""
    if tag is None:
        return {
            "tagger_name": "Release Controller",
            "tagger_email": "release-controller@users.noreply.github.com",
            "tagger_timestamp": timestamp,
            "tagger_timezone": "+0000",
        }
    lines = tag["text"].splitlines()
    match = (
        re.fullmatch(
            r"tagger ([^<\n]{1,100}) <([^>\n]{1,200})> ([0-9]+) ([+-][0-9]{4})",
            lines[3],
        )
        if len(lines) > 3
        else None
    )
    if not match:
        raise ControllerError("E_SIGNING", "Immutable tagger identity is malformed.")
    return {
        "tagger_name": match[1],
        "tagger_email": match[2],
        "tagger_timestamp": int(match[3]),
        "tagger_timezone": match[4],
    }


def provenance_asset(inputs, record, remote, release):
    """Return exact provenance bytes and metadata, e.g. provenance_asset(...)."""
    name = "release-provenance.json"
    if any(f["name"] == name for f in inputs["inventory"]):
        raise ControllerError(
            "E_ASSET", "Build inventory collides with public provenance asset."
        )
    observed = (
        []
        if release is None
        else [a for a in remote.inventory(release["id"]) if a["name"] == name]
    )
    existing = None
    if observed:
        if (
            len(observed) != 1
            or observed[0].get("state") != "uploaded"
            or observed[0].get("content_type") != "application/json"
            or type(observed[0].get("size")) is not int
            or not 0 < observed[0]["size"] <= 65536
        ):
            raise ControllerError("E_ASSET", "Existing provenance metadata is invalid.")
        existing = remote.download(observed[0])
    candidates = [
        v["inputs"]
        for k, v in record.evidence.items()
        if k.startswith("publication-seal-")
    ]
    raw = None
    for candidate in candidates:
        files = [f for f in candidate["inventory"] if f["name"] != name]
        manifests = [f for f in candidate["inventory"] if f["name"] == name]
        if (
            files != inputs["inventory"]
            or len(manifests) != 1
            or any(
                candidate.get(k) != inputs.get(k)
                for k in (
                    "tag",
                    "version",
                    "release_sha",
                    "release_tree",
                    "notes_digest",
                    "tagger_name",
                    "tagger_email",
                    "tagger_timestamp",
                    "tagger_timezone",
                )
            )
        ):
            continue
        proposed = canonical_bytes(
            {"schema_version": 1, "publication": {**candidate, "inventory": files}}
        )
        if hashlib.sha256(proposed).hexdigest() == manifests[0]["sha256"] and (
            existing is None or proposed == existing
        ):
            raw = proposed
            break
    if raw is None:
        if existing is not None:
            raise ControllerError(
                "E_PUBLICATION_CONFLICT",
                "Existing provenance differs from the newly verified release bytes.",
            )
        raw = canonical_bytes({"schema_version": 1, "publication": inputs})
    return {
        "name": name,
        "path": name,
        "media_type": "application/json",
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }, raw
