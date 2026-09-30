"""Replay validation for immutable publication records and global writer ownership."""

import hashlib
import re

from cg_release.models import canonical_bytes


def active_owner(records):
    """Return one unreleased owner, e.g. active_owner(journal.records()), or None."""
    active = []
    for record in records:
        for key, value in record.evidence.items():
            match = re.fullmatch(r"publication-owner-([1-9][0-9]*)", key)
            if match and f"publication-owner-release-{match[1]}" not in record.evidence:
                active.append((record.request_id, value))
    if len(active) > 1:
        raise ValueError("multiple repository publication owners")
    return active[0] if active else None


def validate_publication(records, prior, record, audit, additions):
    """Validate one atomic public-data checkpoint during append and full replay."""
    operation = audit["operation"]
    if re.fullmatch(r"publication-rebuild-[1-9][0-9]*", operation):
        value = record.evidence[operation]
        if (
            set(audit) != {"operation", "digest", "publication_atomic"}
            or additions != {operation}
            or record.checkpoint != operation
            or prior.state not in {"publishing", "awaiting-approval"}
            or record.state != "building"
            or not prior.publication_started
            or prior.published
            or record.intent is not None
            or value["suspended_intent"] != prior.intent
            or active_owner(records.values()) is not None
            or type(value["actor_id"]) is not int
            or value["actor_id"] <= 0
            or type(value["run_id"]) is not int
            or value["run_id"] <= 0
            or value["release_sha"] != prior.evidence["review-binding"]["release_sha"]
            or value["release_tree"] != prior.evidence["review-binding"]["release_tree"]
        ):
            raise ValueError("invalid suspended publication rebuild")
        return
    if (
        set(audit) != {"operation", "digest", "publication_atomic"}
        or record.intent != prior.intent
        or additions != {operation}
        or record.checkpoint != operation
    ):
        raise ValueError("invalid atomic publication checkpoint")
    value = record.evidence[operation]
    registration = re.fullmatch(r"publication-registration-([1-9][0-9]*)", operation)
    if registration:
        if (
            record.state != prior.state
            or set(value) != {"run_id", "run_attempt", "nonce", "controller_sha"}
            or type(value["run_id"]) is not int
            or value["run_id"] <= 0
            or value["run_attempt"] != 1
            or value["nonce"]
            != prior.evidence[f"publication-request-{registration[1]}"]["nonce"]
            or not re.fullmatch(r"[0-9a-f]{40}", value["controller_sha"])
            or any(
                v.get("run_id") == value["run_id"]
                for r in records.values()
                for k, v in r.evidence.items()
                if k.startswith("publication-registration-")
            )
        ):
            raise ValueError("invalid unique publication run registration")
        return
    dispatch = re.fullmatch(
        r"publication-(dispatch|dispatch-intent)-([1-9][0-9]*)", operation
    )
    if dispatch:
        if (
            record.state != prior.state
            or value["inputs"]
            != {
                "request_id": record.request_id,
                "nonce": prior.evidence[f"publication-request-{dispatch[2]}"]["nonce"],
            }
            or (
                dispatch[1] == "dispatch"
                and prior.evidence.get(f"publication-dispatch-intent-{dispatch[2]}")
                != value
            )
        ):
            raise ValueError("publication dispatch differs from its immutable ticket")
        return
    if re.fullmatch(r"publication-exception-[1-9][0-9]*", operation):
        from cg_release.models import load_record
        from cg_release.recovery_models import RecoveryAudit

        proof = load_record(RecoveryAudit, canonical_bytes(value))
        if (
            not prior.publication_started
            or record.state != prior.state
            or proof.directive.operation != "source-exception"
            or proof.directive.request != prior.request
            or proof.directive.tag.oid
            != prior.evidence["publication-tag-object"]["oid"]
            or proof.directive_digest
            != hashlib.sha256(canonical_bytes(proof.directive)).hexdigest()
        ):
            raise ValueError(
                "source exception changed the immutable publication identity"
            )
        return
    if re.fullmatch(r"publication-resume-[1-9][0-9]*", operation):
        if (
            prior.state != "awaiting-approval"
            or record.state != "publishing"
            or prior.intent is not None
            or prior.published
            or value["tag_oid"] != prior.evidence["publication-tag-object"]["oid"]
            or not re.fullmatch(r"[0-9a-f]{64}", value["inputs_digest"])
        ):
            raise ValueError("invalid publication resume checkpoint")
        return
    if operation == "publication-tag-object":
        raw = value["text"].encode()
        if (
            prior.state != "awaiting-approval"
            or prior.intent is not None
            or record.state != "publishing"
            or set(value) != {"text", "oid", "fingerprint"}
            or len(raw) > 16384
            or hashlib.sha1(b"tag " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            != value["oid"]
        ):
            raise ValueError("invalid public tag bytes")
        return
    if record.state != prior.state:
        raise ValueError("publication data cannot change lifecycle state")
    if prior.intent is not None and not re.fullmatch(
        r"publication-(?:tag|draft|publish|asset-[1-9][0-9]*)",
        prior.intent["operation"],
    ):
        raise ValueError("only publication effects may coexist with recovery metadata")
    match = re.fullmatch(
        r"publication-(seal|owner|owner-release|request)-([1-9][0-9]*)", operation
    )
    if not match:
        raise ValueError("unknown publication checkpoint")
    if match[1] == "seal":
        if (
            value["run_id"] != int(match[2])
            or value["run_attempt"] != 1
            or value["digest"]
            != hashlib.sha256(canonical_bytes(value["inputs"])).hexdigest()
            or any(operation in r.evidence for r in records.values())
            or not re.fullmatch(r"[0-9a-f]{32}", value["nonce"])
            or any(
                v.get("nonce") == value["nonce"]
                for k, v in prior.evidence.items()
                if k.startswith("publication-seal-")
            )
        ):
            raise ValueError("one run must identify one immutable seal")
    elif match[1] == "owner":
        if (
            set(value) != {"run_id", "credential_expires_at"}
            or type(value["run_id"]) is not int
            or value["run_id"] != int(match[2])
            or type(value["credential_expires_at"]) is not int
            or value["credential_expires_at"] <= 0
            or active_owner(records.values()) is not None
        ):
            raise ValueError("publication owner already exists or is invalid")
    elif match[1] == "owner-release":
        if (
            value["run_id"] != int(match[2])
            or f"publication-owner-{match[2]}" not in prior.evidence
        ):
            raise ValueError("owner release lacks its immutable claim")
    elif (
        not re.fullmatch(r"[0-9a-f]{32}", value["nonce"])
        or value["mode"] not in {"initial", "recovery"}
        or not isinstance(value["reconfirmers"], list)
    ):
        raise ValueError("invalid publication request")
