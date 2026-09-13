"""Immutable documentation selection, reviewed adoption and pre-publication capacity."""

import base64
import hashlib
from types import SimpleNamespace

from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.jsonio import _decode
from cg_release.profile_snapshot import verify_snapshot
from cg_release.publication_remote import GitHubPublicationRemote
from cg_release.published_history import published_inputs, verified_records
from cg_release.snapshot_contract import (
    MAX_DEPLOYMENT_BYTES,
    MAX_ENVELOPE_BYTES,
    MAX_FILES,
    validate_paths,
)
from cg_release.versions import parse_version


def selection(context) -> tuple[list[dict], str]:
    """Select sealed identities without downloading bytes, e.g. selection(context).

    Returns: All immutable snapshots and highest stable tag, including reviewed
    policy adoptions. Raises ControllerError on missing stable or conflicting history.
    Only the protected journal is read; no API effects or byte acquisition occur.
    """
    snapshots = {}
    adopted = {row.tag: row for row in context.policy.bootstrap}
    for baseline in context.policy.profile.docs_baselines:
        row = adopted.get(baseline.tag)
        if (
            row is None
            or row.release_id != baseline.release_id
            or row.commit != baseline.sha
            or baseline.tag != "v" + row.version
            or baseline.tag in snapshots
        ):
            raise ControllerError(
                "E_DOCS_SETUP",
                "Documentation baseline must match one reviewed adopted release.",
            )
        snapshots[baseline.tag] = baseline.model_dump()
    for item in context.journal.records():
        if not item.published:
            continue
        inputs = published_inputs(item)
        assets = [f for f in inputs["inventory"] if f["name"] == "release-docs.json"]
        builds = [
            v
            for k, v in item.evidence.items()
            if k.startswith("build-validated-") and digest(v) == inputs["build_digest"]
        ]
        if len(assets) != 1 or len(builds) != 1:
            raise ControllerError(
                "E_HOOK",
                "Published GPID release lacks its approved snapshot and build.",
            )
        gate = builds[0]["gates"][".github/workflows/release-controller-build.yml"]
        receipt = item.evidence["publication-receipt"]
        value = {
            "tag": item.request.tag,
            "sha": receipt["release_sha"],
            "release_id": receipt["release_id"],
            "asset_id": receipt["assets"]["release-docs.json"],
            "sha256": assets[0]["sha256"],
            "size": assets[0]["size"],
            "run_id": gate["run_id"],
            "run_attempt": gate["run_attempt"],
        }
        if item.request.tag in snapshots and snapshots[item.request.tag] != value:
            raise ControllerError(
                "E_DOCS_SETUP", "Adopted and controller snapshot identities conflict."
            )
        snapshots[item.request.tag] = value
    stable = [
        (parse_version(tag[1:]), tag)
        for tag in snapshots
        if parse_version(tag[1:]).prerelease is None
    ]
    adopted_stable = [
        (parse_version(row.version), row.tag)
        for row in context.policy.bootstrap
        if row.legacy_version is None and parse_version(row.version).prerelease is None
    ]
    if adopted_stable and (not stable or max(adopted_stable)[0] > max(stable)[0]):
        raise ControllerError(
            "E_DOCS_STABLE", "Highest adopted stable needs a reviewed docs baseline."
        )
    if not stable:
        raise ControllerError(
            "E_DOCS_STABLE",
            "A reviewed stable documentation baseline is required before submission.",
        )
    if (
        len({tag.lower() for tag in snapshots}) != len(snapshots)
        or len(snapshots) > 100
    ):
        raise ControllerError(
            "E_DOCS_SETUP", "Snapshot selection has aliases or exceeds its bound."
        )
    return sorted(snapshots.values(), key=lambda item: item["tag"]), max(stable)[1]


def acquire(
    api, snapshots: list[dict], *, download=True
) -> list[tuple[dict, bytes | None]]:
    """Verify one fresh inventory, e.g. acquire(api, snapshots, download=False).

    Args: snapshots are sealed selection identities; download additionally checks
    exact approved bytes and registered snapshot metadata once for each asset.
    Returns: Metadata/raw pairs in input order. No remote mutations occur.
    Raises: ControllerError on mutable metadata, identity, capacity or byte conflict.
    """
    remote = GitHubPublicationRemote(
        api, refs=api.refs(), releases=api.pages("releases")
    )
    result, total = [], 0
    for item in snapshots:
        tag, release = (
            remote.observe_tag(item["tag"]),
            remote.observe_release(item["tag"]),
        )
        if (
            tag is None
            or tag["commit"] != item["sha"]
            or release is None
            or release.get("id") != item["release_id"]
            or release.get("draft") is not False
            or not release.get("published_at")
        ):
            raise ControllerError(
                "E_HOOK", "Immutable snapshot publication identity differs."
            )
        assets = [
            asset
            for asset in remote.inventory(item["release_id"])
            if asset.get("name") == "release-docs.json"
        ]
        if (
            len(assets) != 1
            or assets[0].get("id") != item["asset_id"]
            or assets[0].get("size") != item["size"]
            or assets[0].get("state") != "uploaded"
            or not 0 < item["size"] <= MAX_ENVELOPE_BYTES
        ):
            raise ControllerError(
                "E_HOOK", "Immutable snapshot asset identity differs."
            )
        total += item["size"]
        if total > MAX_DEPLOYMENT_BYTES:
            raise ControllerError(
                "E_DOCS_CAPACITY",
                "Complete immutable snapshot acquisition exceeds capacity.",
            )
        raw = remote.download(assets[0]) if download else None
        if raw is not None:
            if (
                len(raw) != item["size"]
                or hashlib.sha256(raw).hexdigest() != item["sha256"]
            ):
                raise ControllerError(
                    "E_HOOK", "Immutable snapshot bytes differ from approved inventory."
                )
            verify_snapshot(
                raw,
                tag=item["tag"],
                sha=item["sha"],
                run_id=item["run_id"],
                run_attempt=item["run_attempt"],
            )
        result.append((item, raw))
    return result


def capacity(raw: bytes) -> dict:
    """Describe already verified bytes, e.g. capacity(raw); read-only fixed decoder."""
    files = _decode(raw.decode("utf-8"), MAX_ENVELOPE_BYTES)["files"]
    return {
        "envelope_bytes": len(raw),
        "paths": sorted(files),
        "files": len(files),
        "directories": len(
            {p.rsplit("/", n)[0] for p in files for n in range(1, p.count("/") + 1)}
        ),
        "bytes": sum(len(base64.b64decode(v)) for v in files.values()),
        "depth": max(p.count("/") + 1 for p in files),
        "path": max(map(len, files)),
    }


def deployment_capacity(items: list[tuple[str, dict]], stable: str) -> None:
    """Reject incompatible output before approval, e.g. deployment_capacity(items, tag).

    Args: exact verified snapshot summaries and selected stable tag. Reserve the
    declared maximum 1,000-file/32 MiB dev preview; never omit historical paths.
    Raises: ControllerError on count, bytes, path/depth overflow. No writes occur.
    """
    from cg_release.snapshot_contract import MAX_SNAPSHOT_BYTES

    if (
        len(items) > 100
        or sum(value["envelope_bytes"] for _, value in items) > MAX_DEPLOYMENT_BYTES
    ):
        raise ControllerError(
            "E_DOCS_CAPACITY", "Immutable snapshot selection exceeds capacity."
        )
    files, size, directories = 1000, MAX_SNAPSHOT_BYTES, 1003
    destinations = []
    for tag, value in items:
        destinations.extend(f"releases/{tag}/{name}" for name in value["paths"])
        if tag == stable:
            destinations.extend(value["paths"])
        copies = 2 if tag == stable else 1
        files += value["files"] * copies
        size += value["bytes"] * copies
        directories += value["directories"] * copies + 1
        if (
            value["depth"] + 2 > 33
            or value["path"] + len("releases//") + len(tag) > 255
        ):
            raise ControllerError(
                "E_DOCS_CAPACITY",
                "Versioned documentation path exceeds deployment capacity.",
            )
    try:
        if len(set(destinations)) != len(destinations):
            raise ValueError("duplicate destination")
        validate_paths(destinations, deployment=True)
    except ValueError:
        raise ControllerError(
            "E_DOCS_CAPACITY",
            "Snapshot destination graph has aliases or exceeds capacity.",
        ) from None
    if files > MAX_FILES or directories > MAX_FILES or size > MAX_DEPLOYMENT_BYTES:
        raise ControllerError(
            "E_DOCS_CAPACITY",
            "Retained documentation and dev reserve exceed deployment capacity.",
        )


def preflight(api, policy, version: str) -> None:
    """Check stable setup before submission/preparation; no mutations.

    Example: preflight(api, policy, '1.5.0-rc.1'). A first stable release may
    supply its own root, but a pre-release requires existing immutable evidence.
    Returns None; raises ControllerError with a setup remedy, never after publication.
    """
    records = verified_records(api, policy)
    adopted_stable = [
        parse_version(row.version)
        for row in policy.bootstrap
        if row.legacy_version is None and parse_version(row.version).prerelease is None
    ]
    if (
        not any(r.published for r in records)
        and not policy.profile.docs_baselines
        and parse_version(version).prerelease is None
        and (not adopted_stable or parse_version(version) > max(adopted_stable))
    ):
        return
    context = SimpleNamespace(
        policy=policy, journal=SimpleNamespace(records=lambda: records)
    )
    snapshots, stable = selection(context)
    if len(snapshots) >= 100:
        raise ControllerError(
            "E_DOCS_CAPACITY", "No capacity remains for another immutable snapshot."
        )
    acquired = acquire(api, snapshots)
    deployment_capacity(
        [(item["tag"], capacity(raw)) for item, raw in acquired], stable
    )
