"""Read-only reconciliation of partial publication before any owner reassignment."""

import hashlib

from semver import Version

from cg_release.events import ControllerError


def inspect_publication(record, inputs, remote):
    """Verify every observed effect, e.g. inspect_publication(record, inputs, remote).

    Missing objects are a resumable checkpoint, not a rollback instruction. Any
    differing tag, draft, asset, published byte or record blocks reassignment.
    """
    try:
        tag = remote.observe_tag(inputs["tag"])
        saved = record.evidence.get("publication-tag-object")
        if tag is not None and (
            saved is None
            or tag
            != {"type": "tag", "oid": saved["oid"], "commit": inputs["release_sha"]}
        ):
            raise ValueError
        release = remote.observe_release(inputs["tag"])
        if release is None:
            if record.published or "publication-draft" in record.evidence:
                raise ValueError
            return {"tag": tag, "release": None, "assets": {}}
        if (
            tag is None
            or release["target_commitish"] != inputs["release_sha"]
            or release["tag_name"] != inputs["tag"]
            or release["body"] != inputs["notes"]
            or type(release["draft"]) is not bool
            or type(release["id"]) is not int
            or release["id"] <= 0
            or release["prerelease"]
            is not (Version.parse(inputs["version"]).prerelease is not None)
        ):
            raise ValueError
        allowed = {f["name"]: f for f in inputs["inventory"]}
        assets = {}
        for asset in remote.inventory(release["id"]):
            name = asset["name"]
            if (
                name not in allowed
                or name in assets
                or asset["size"] != allowed[name]["size"]
                or asset["content_type"] != allowed[name]["media_type"]
                or asset["state"] != "uploaded"
            ):
                raise ValueError
            raw = remote.download(asset)
            if (
                len(raw) != allowed[name]["size"]
                or hashlib.sha256(raw).hexdigest() != allowed[name]["sha256"]
            ):
                raise ValueError
            assets[name] = asset["id"]
        if (not release["draft"] and set(assets) != set(allowed)) or (
            record.published and release["draft"]
        ):
            raise ValueError
        if record.published:
            receipt = record.evidence["publication-receipt"]
            if receipt["release_id"] != release["id"] or receipt["assets"] != assets:
                raise ValueError
        return {"tag": tag, "release": release["id"], "assets": assets}
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ControllerError(
            "E_PUBLICATION_CONFLICT",
            "Partial publication conflicts with immutable approved identities.",
        ) from None
