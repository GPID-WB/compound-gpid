"""Verify adopted Releases against exact refs; incomplete publications fail closed."""

import re
from urllib.parse import quote

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.models import Policy
from cg_release.versions import parse_version


def adopted_history(
    api: GitHubReads, policy: Policy, *, records=None, current=None
) -> tuple[list[dict], list[str]]:
    """Read complete release identity inventory, e.g. adopted_history(api, policy).

    Args:
        api: Bounded read adapter with paginated Releases and refs.
        policy: Trusted bootstrap/adoption records and managed tag prefix.
    Returns:
        Verified adopted records and globally occupied versions.
    Raises:
        ControllerError: Unadopted, duplicate, malformed, or incomplete managed history.
    """
    from cg_release.publication_reconcile import inspect_publication
    from cg_release.publication_remote import GitHubPublicationRemote
    from cg_release.published_history import (
        journal_adoptions,
        published_inputs,
        verified_records,
    )

    if records is None:
        records = verified_records(api, policy) if policy.enabled else []
    rows, tag_objects = journal_adoptions(policy, records, current=current)
    remote = GitHubPublicationRemote(api)
    for record in records:
        if record.published and (
            current is None or record.request_id != current.request_id
        ):
            inspect_publication(record, published_inputs(record), remote)
    releases, refs = api.pages("releases"), api.refs()
    if current is not None:
        own = [r for r in refs if r["ref"] == "refs/tags/" + current.request.tag]
        if own and (
            len(own) != 1
            or own[0]["object"].get("type") != "tag"
            or own[0]["object"].get("sha")
            != current.evidence["publication-tag-object"]["oid"]
        ):
            raise ControllerError(
                "E_TAG_CONFLICT",
                "Current publication tag conflicts with sealed object.",
            )
        releases = [r for r in releases if r["tag_name"] != current.request.tag]
        refs = [r for r in refs if r["ref"] != "refs/tags/" + current.request.tag]
    adopted = {row.tag: row for row in rows}
    if len(adopted) != len(rows) or len({r.release_id for r in rows}) != len(adopted):
        raise ControllerError("E_HISTORY", "Duplicate adopted tag or Release ID.")
    by_tag, occupied, identities = {}, [], set()
    for release in releases:
        if (
            type(release.get("id")) is not int
            or not isinstance(release.get("tag_name"), str)
            or type(release.get("draft")) is not bool
            or type(release.get("prerelease")) is not bool
        ):
            raise ControllerError(
                "E_RESPONSE", "Malformed Release identity or classification."
            )
        tag = release["tag_name"]
        if not tag.startswith(policy.tag_prefix) and tag not in adopted:
            continue
        if tag in by_tag:
            raise ControllerError("E_HISTORY", "Multiple Releases use one managed tag.")
        by_tag[tag] = release
    observed = set()
    for ref in refs:
        try:
            if ref["repository_id"] != policy.repository_id or not ref[
                "ref"
            ].startswith("refs/tags/"):
                raise ValueError
            tag = ref["ref"][len("refs/tags/") :]
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ControllerError(
                "E_REPOSITORY",
                "Tag inventory belongs to a different repository or namespace.",
            ) from None
        if not tag.startswith(policy.tag_prefix) and tag not in adopted:
            continue
        row = adopted.get(tag)
        version = parse_version(row.version if row else tag[len(policy.tag_prefix) :])
        if version in identities:
            raise ControllerError(
                "E_COLLISION", "Managed tag identities collide ignoring build metadata."
            )
        identities.add(version)
        occupied.append(str(version))
        release = by_tag.get(tag)
        if release is None or release["draft"]:
            raise ControllerError(
                "E_INCOMPLETE_PUBLICATION",
                "Managed tag lacks a published Release; explicit recovery is required.",
            )
        if (
            row is None
            or release["id"] != row.release_id
            or not release.get("published_at")
        ):
            raise ControllerError(
                "E_HISTORY",
                "Published managed Release needs an exact audited adoption record.",
            )
        # Legacy classification belongs to its original identity, not the baseline.
        if row.legacy_version is None and release["prerelease"] != (
            version.prerelease is not None
        ):
            raise ControllerError(
                "E_HISTORY", "Release classification differs from its adopted SemVer."
            )
        exact = api.get("git/ref/tags/" + quote(tag, safe=""))
        if tag in tag_objects and (
            ref["object"].get("type") != "tag"
            or ref["object"].get("sha") != tag_objects[tag]
        ):
            raise ControllerError(
                "E_HISTORY", "Published annotated tag object changed."
            )
        if (
            not isinstance(exact, dict)
            or exact.get("ref") != ref["ref"]
            or not isinstance(exact.get("object"), dict)
            or any(
                exact["object"].get(k) != ref["object"].get(k) for k in ("sha", "type")
            )
        ):
            raise ControllerError(
                "E_HISTORY", "Exact tag identity changed during inventory."
            )
        obj, seen = exact["object"], set()
        for _ in range(16):
            if not isinstance(obj, dict) or not re.fullmatch(
                r"[0-9a-f]{40}", str(obj.get("sha", ""))
            ):
                raise ControllerError("E_HISTORY", "Malformed peeled tag object.")
            if obj["sha"] in seen:
                raise ControllerError("E_HISTORY", "Cyclic tag object identity.")
            seen.add(obj["sha"])
            if obj.get("type") == "commit":
                if obj["sha"] != row.commit:
                    raise ControllerError(
                        "E_HISTORY",
                        "Adopted tag no longer points to its audited commit.",
                    )
                break
            if obj.get("type") != "tag":
                raise ControllerError(
                    "E_HISTORY", "Managed tag does not resolve to a commit."
                )
            value = api.get("git/tags/" + obj["sha"])
            if not isinstance(value, dict) or value.get("sha") != obj["sha"]:
                raise ControllerError(
                    "E_HISTORY", "Annotated tag identity cannot be verified."
                )
            obj = value.get("object")
        else:
            raise ControllerError(
                "E_HISTORY", "Tag indirection exceeds the safety limit."
            )
        observed.add(tag)
    if observed != set(adopted) or set(by_tag) != observed:
        raise ControllerError(
            "E_INCOMPLETE_PUBLICATION",
            "Adopted Release, draft, or managed ref inventory is incomplete.",
        )
    return [r.model_dump(mode="json") for r in rows], occupied
