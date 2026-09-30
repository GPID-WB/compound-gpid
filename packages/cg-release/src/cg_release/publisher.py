"""Reconcile each immutable publication effect before a single non-clobbering write."""

import hashlib

from semver import Version

from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_checkpoint import atomic_publication_checkpoint
from cg_release.prepare_stage import checkpoint
from cg_release.publication_capacity import preflight_publication
from cg_release.signing import verify_tag


def should_be_latest(version: str, history: list[str]) -> bool:
    """Select only the highest stable identity, e.g. should_be_latest('2.1.0', history).

    Args: history contains verified adopted versions across every release line.
    Returns: False for all pre-releases and older maintenance stable releases.
    Raises: ControllerError if any version is invalid rather than guessing order.
    """
    try:
        candidate = Version.parse(version)
        parsed = [Version.parse(value) for value in history]
        return candidate.prerelease is None and all(
            candidate >= v for v in parsed if v.prerelease is None
        )
    except (ValueError, TypeError):
        raise ControllerError(
            "E_HISTORY", "Latest selection requires valid adopted history."
        ) from None


def publish(
    journal,
    record,
    inputs: dict,
    tag: dict,
    remote,
    *,
    data: dict[str, bytes],
    recheck,
    make_latest: bool,
    expected_latest: int | None,
    run_id: int,
):
    """Publish exact verified bytes under a caller-verified protected owner and seal.

    Args: remote has publication-App operations only. journal uses the control App.
        recheck verifies owner, current authority, policy, approval and build gates
        before effects. data comes from a separately verified registered artifact.
    Returns: Remotely verified published record, not project-hook completion.
    Raises: ControllerError for conflicting or uncertain effects; never rolls back.
    Example: ``publish(journal, record, sealed_inputs, tag, remote, ...)``.
    """
    request_id = record.request_id
    version = Version.parse(inputs["version"])
    if (inputs["tag"], inputs["version"]) != (
        record.request.tag,
        record.request.version,
    ):
        raise ControllerError(
            "E_PUBLICATION", "Publication differs from reserved identity."
        )
    # Signature verification is the trusted worker's responsibility with its
    # allowlisted key. The primitive still requires exact persisted object bytes.
    if tag["fingerprint"] is None:
        verify_tag(tag, inputs["tag"], inputs["release_sha"])
    expected_tag = {"oid": tag["oid"], "commit": inputs["release_sha"], "type": "tag"}
    files = {f["name"]: f for f in inputs["inventory"]}
    if len(files) != len(inputs["inventory"]) or not files:
        raise ControllerError("E_ASSET", "Publication inventory is empty or ambiguous.")
    for name, raw in data.items():
        if (
            name not in files
            or len(raw) != files[name]["size"]
            or hashlib.sha256(raw).hexdigest() != files[name]["sha256"]
        ):
            raise ControllerError(
                "E_ASSET", "Upload bytes differ from approved inventory."
            )
    recheck()
    preflight_publication(journal, record, inputs, tag, run_id)
    if "publication-tag-object" not in record.evidence:
        record = atomic_publication_checkpoint(
            journal, record, "publication-tag-object", tag, "publishing"
        )
    elif record.evidence["publication-tag-object"] != tag:
        raise ControllerError(
            "E_TAG_CONFLICT", "The persisted public tag object cannot change."
        )
    elif record.state == "awaiting-approval":
        record = atomic_publication_checkpoint(
            journal,
            record,
            f"publication-resume-{run_id}",
            {"tag_oid": tag["oid"], "inputs_digest": digest(inputs)},
            "publishing",
        )

    def effect(operation, desired, observe, matching, write):
        nonlocal record
        record = journal.get(request_id)
        observed = observe()
        if observed is not None and not matching(observed):
            raise ControllerError(
                "E_PUBLICATION_CONFLICT",
                "Observed publication object differs from approval.",
            )
        identity = digest(desired)
        if operation in record.evidence:
            if record.evidence[operation] != desired or observed is None:
                raise ControllerError(
                    "E_PUBLICATION_CONFLICT",
                    "A completed publication object is missing or changed.",
                )
            return observed
        if record.published and observed is None:
            raise ControllerError(
                "E_PUBLICATION_CONFLICT",
                "Published bytes must never be restored by replacement.",
            )
        if record.intent not in (None, {"operation": operation, "digest": identity}):
            raise ControllerError(
                "E_PUBLICATION_CONFLICT", "Another effect needs reconciliation first."
            )
        record = journal.intent(request_id, operation, identity)
        if observed is None:
            recheck()
            preflight_publication(journal, record, inputs, tag, run_id)
            try:
                write()
            except ControllerError as error:
                observed = observe()
                if observed is None:
                    if error.code in {"E_AUTH", "E_FORBIDDEN", "E_NOT_FOUND"}:
                        raise error
                    raise ControllerError(
                        "E_WRITE_UNKNOWN",
                        "Publication write is unresolved; inspect remote state "
                        "before resume.",
                    ) from None
            else:
                observed = observe()
            if observed is None or not matching(observed):
                raise ControllerError(
                    "E_PUBLICATION_CONFLICT",
                    "Written publication result failed exact read-back.",
                )
        record = journal.result(
            request_id, operation, identity, record.state, evidence=desired
        )
        return observed

    effect(
        "publication-tag",
        expected_tag,
        lambda: remote.observe_tag(inputs["tag"]),
        lambda value: value == expected_tag,
        lambda: remote.push_tag(inputs["tag"], tag, inputs["release_sha"]),
    )
    desired_release = {
        "tag_name": inputs["tag"],
        "target_commitish": inputs["release_sha"],
        "notes_digest": digest({"notes": inputs["notes"]}),
        "prerelease": version.prerelease is not None,
    }

    def matching_release(value):
        return (
            value.get("body") == inputs["notes"]
            and all(
                value.get(k) == v
                for k, v in desired_release.items()
                if k != "notes_digest"
            )
            and type(value.get("id")) is int
            and 0 < value["id"] < (1 << 64)
            and type(value.get("draft")) is bool
        )

    release = effect(
        "publication-draft",
        desired_release,
        lambda: remote.observe_release(inputs["tag"]),
        matching_release,
        lambda: remote.create_draft(
            inputs["tag"],
            inputs["release_sha"],
            inputs["notes"],
            version.prerelease is not None,
        ),
    )
    release_id = release["id"]

    def inventory():
        values = remote.inventory(release_id)
        if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
            raise ControllerError("E_ASSET", "Remote asset inventory is invalid.")
        result = {v["name"]: v for v in values}
        if len(result) != len(values) or set(result) - set(files):
            raise ControllerError(
                "E_ASSET", "Remote assets contain unapproved or duplicate names."
            )
        return result

    for index, (name, item) in enumerate(sorted(files.items()), 1):

        def match_asset(asset, item=item):
            if (
                type(asset.get("size")) is not int
                or asset["size"] != item["size"]
                or asset.get("content_type") != item["media_type"]
                or asset.get("state") != "uploaded"
            ):
                return False
            raw = remote.download(asset)
            return (
                type(asset.get("id")) is int
                and 0 < asset["id"] < (1 << 64)
                and asset.get("state") == "uploaded"
                and asset.get("size") == item["size"]
                and asset.get("content_type") == item["media_type"]
                and len(raw) == item["size"]
                and hashlib.sha256(raw).hexdigest() == item["sha256"]
            )

        def upload(item=item, name=name):
            if release["draft"] is not True or name not in data:
                raise ControllerError(
                    "E_ASSET_MISSING",
                    "Missing bytes require a new exact build and approval, "
                    "not asset replacement.",
                )
            remote.upload(release_id, item, data[name])

        effect(
            f"publication-asset-{index}",
            item,
            lambda name=name: inventory().get(name),
            match_asset,
            upload,
        )
    if set(inventory()) != set(files):
        raise ControllerError("E_ASSET", "Required assets are incomplete.")

    def published():
        observed = remote.observe_release(inputs["tag"])
        if not matching_release(observed) or observed["id"] != release_id:
            raise ControllerError(
                "E_PUBLICATION_CONFLICT", "Release changed before publication."
            )
        return observed if observed["draft"] is False else None

    effect(
        "publication-publish",
        {"release_id": release_id, "make_latest": make_latest},
        published,
        lambda value: matching_release(value) and value["draft"] is False,
        lambda: remote.publish(release_id, make_latest),
    )
    if remote.latest_id() != (release_id if make_latest else expected_latest):
        raise ControllerError(
            "E_LATEST",
            "Published latest classification does not match the approved selection.",
        )
    receipt = {
        "run_id": run_id,
        "inputs_digest": digest(inputs),
        "projections": inputs["projections"],
        "release_id": release_id,
        "tag_oid": tag["oid"],
        "release_sha": inputs["release_sha"],
        "assets": {n: a["id"] for n, a in inventory().items()},
    }
    if "publication-receipt" in record.evidence:
        original = record.evidence["publication-receipt"]
        if any(
            original.get(k) != value
            for k, value in receipt.items()
            if k not in {"run_id", "inputs_digest"}
        ):
            raise ControllerError(
                "E_PUBLICATION_CONFLICT", "Published receipt identities changed."
            )
        return record
    return checkpoint(journal, record, "publication-receipt", receipt, "published")
