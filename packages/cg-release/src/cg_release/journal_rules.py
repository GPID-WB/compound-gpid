"""Pure journal transition validation, reused by append and complete replay."""

import hashlib
import re
from typing import TYPE_CHECKING

from cg_release.admission import Locator
from cg_release.build_evidence import reuse_key
from cg_release.build_models import BuildRegistration, BuildTicket
from cg_release.events import ControllerError
from cg_release.models import MAX_RECORD_BYTES, canonical_bytes, load_record


def retained_evidence(
    prior, operation: str, input_digest: str, evidence: dict | None
) -> dict:
    """Append bounded result evidence without replacement, e.g. for prepare/tree IDs."""
    retained = dict(prior.evidence)
    if evidence is not None:
        try:
            raw = canonical_bytes(evidence)
            if (
                not isinstance(evidence, dict)
                or len(raw) > 32768
                or hashlib.sha256(raw).hexdigest() != input_digest
                or (operation in retained and retained[operation] != evidence)
            ):
                raise ValueError
            retained[operation] = evidence
            if (
                len(
                    canonical_bytes(
                        {**prior.model_dump(mode="json"), "evidence": retained}
                    )
                )
                > MAX_RECORD_BYTES - 1024
            ):
                raise ValueError
        except (ValueError, TypeError, RecursionError):
            raise ControllerError(
                "E_EVIDENCE", "Stage evidence conflicts or exceeds journal limits."
            ) from None
    return retained


if TYPE_CHECKING:
    from cg_release.journal import Record


def validate_transition(
    records: dict[str, "Record"], record: "Record", audit: dict
) -> None:
    """Reject invalid state, nonce, or reservation changes before persistence.

    Args: records are verified prior states; record/audit is one proposed update.
    Returns: None, e.g. validate_transition(prior, proposed, {'operation': 'admit'}).
    Raises: ValueError for corrupt transitions, ControllerError for identity conflicts.
    """
    if Locator.from_request(
        record.request
    ).encode() != record.request_id or not isinstance(audit, dict):
        raise ValueError("invalid identity")
    prior = records.get(record.request_id)
    if record.receipt is not None and (
        record.receipt.request != record.request
        or record.receipt.request_id != record.request_id
    ):
        raise ValueError("immutable receipt mapping differs from request")
    if record.state == "failed":
        if (
            not isinstance(record.error, str)
            or not re.fullmatch(r"E_[A-Z0-9_]+", record.error)
            or not record.failed_step
        ):
            raise ValueError("failure lacks structured checkpoint evidence")
    elif record.state != "abandoned" and (
        record.error is not None or record.failed_step is not None or record.retryable
    ):
        raise ValueError("failure fields disagree with state")
    if prior is None:
        if audit.get("operation") == "recover-admit":
            from cg_release.stranded_recovery import validate_recovered_admission

            validate_recovered_admission(record, audit)
        elif (
            record.state != "queued"
            or record.intent is not None
            or record.checkpoint != "admitted"
            or audit != {"operation": "admit"}
            or record.publication_started
            or record.published
            or record.evidence
        ):
            raise ValueError("invalid admission")
    else:
        additions = set(record.evidence) - set(prior.evidence)
        if (
            any(
                record.evidence.get(key) != value
                for key, value in prior.evidence.items()
            )
            or (
                record.intent is not None
                and record.evidence != prior.evidence
                and audit.get("publication_atomic") is not True
            )
            or (
                additions
                and (
                    record.state in {"failed", "abandoned"}
                    or additions != {audit.get("operation")}
                    or hashlib.sha256(
                        canonical_bytes(record.evidence[audit["operation"]])
                    ).hexdigest()
                    != audit.get("digest")
                )
            )
        ):
            raise ValueError("stage evidence must append once against its exact intent")
        if (
            prior.request != record.request
            or prior.receipt != record.receipt
            or prior.state == "abandoned"
            or (
                prior.state == "complete"
                and not (
                    record.state == "complete"
                    and record.published
                    and prior.published
                    and set(prior.evidence.get("publication-hooks", {}))
                    == {"docs", "evidence"}
                    and re.fullmatch(
                        r"profile-docs-(?:(request|dispatch|registration|composition)-[1-9][0-9]*|journal)",
                        audit.get("operation", ""),
                    )
                )
            )
        ):
            raise ValueError("immutable or terminal request")
        allowed = {
            "queued": "awaiting-review",
            "awaiting-review": "building",
            "building": "awaiting-approval",
            "awaiting-approval": "publishing",
            "publishing": "published",
            "published": "complete",
        }
        rebuild = (
            prior.state == "awaiting-approval"
            and record.state == "building"
            and not prior.publication_started
            and not prior.published
            and isinstance(
                prior.evidence.get("review-binding", {}).get("release_sha"), str
            )
            and isinstance(
                prior.evidence.get("review-binding", {}).get("release_tree"), str
            )
            and re.fullmatch(r"build-request-[1-9][0-9]*", audit.get("operation", ""))
            and set(record.evidence) - set(prior.evidence) == {audit["operation"]}
            and record.evidence[audit["operation"]].get("release_sha")
            == prior.evidence.get("review-binding", {}).get("release_sha")
            and record.evidence[audit["operation"]].get("release_tree")
            == prior.evidence.get("review-binding", {}).get("release_tree")
        )
        recovery_build = (
            prior.publication_started
            and not prior.published
            and prior.state in {"publishing", "awaiting-approval"}
            and record.state == "building"
            and audit.get("publication_atomic") is True
            and re.fullmatch(
                r"publication-rebuild-[1-9][0-9]*", audit.get("operation", "")
            )
        )
        if (
            record.state != prior.state
            and not rebuild
            and not recovery_build
            and record.state
            not in {
                allowed.get(prior.state),
                "failed",
                "abandoned",
            }
        ):
            raise ValueError("invalid transition")
        if record.state == "abandoned":
            if (
                prior.publication_started
                or prior.published
                or prior.intent is not None
                or audit.get("effects_absent") is not True
                or audit.get("role") not in {"maintain", "admin"}
                or type(audit.get("actor_id")) is not int
                or audit["actor_id"] <= 0
                or not isinstance(audit.get("reason"), str)
                or not 1 <= len(audit["reason"].strip()) <= 1024
            ):
                raise ValueError("abandon requires audited maintainer evidence")
        elif audit.get("publication_atomic") is True:
            from cg_release.publication_rules import validate_publication

            validate_publication(records, prior, record, audit, additions)
        elif audit.get("atomic") is True:
            operation = audit.get("operation", "")
            match = re.fullmatch(
                r"build-(request|registration)-([1-9][0-9]*)", operation
            )
            if (
                not match
                or set(audit) != {"operation", "digest", "atomic"}
                or prior.intent is not None
                or record.intent is not None
                or record.state != "building"
                or prior.state not in {"building", "awaiting-approval"}
                or record.checkpoint != operation
                or additions != {operation}
                or (
                    prior.publication_started
                    and "publication-recovery" not in prior.evidence
                    and not any(
                        re.fullmatch(r"publication-rebuild-[1-9][0-9]*", k)
                        for k in prior.evidence
                    )
                )
                or prior.published
            ):
                raise ValueError("invalid atomic build checkpoint")
            evidence = record.evidence[operation]
            if match[1] == "request":
                load_record(BuildTicket, canonical_bytes(evidence))
                previous = [
                    int(k.removeprefix("build-request-"))
                    for k in prior.evidence
                    if re.fullmatch(r"build-request-[1-9][0-9]*", k)
                ]
                if (
                    int(match[2]) != max(previous, default=0) + 1
                    or evidence["request_digest"] != prior.request.proposal_digest
                ):
                    raise ValueError("build ticket identity or sequence differs")
            else:
                load_record(BuildRegistration, canonical_bytes(evidence))
                sealed = prior.evidence.get("build-request-" + match[2])
                if (
                    prior.state != "building"
                    or not isinstance(sealed, dict)
                    or evidence["build_digest"] != reuse_key(sealed)
                    or evidence["dispatch_nonce"] != sealed["dispatch_nonce"]
                    or evidence["release_sha"] != sealed["release_sha"]
                ):
                    raise ValueError("registration differs from sealed ticket")
        elif record.intent is not None:
            if (
                prior.intent not in (None, record.intent)
                or record.state != prior.state
                or set(record.intent) != {"operation", "digest"}
                or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", record.intent["operation"])
                or not re.fullmatch(r"[0-9a-f]{64}", record.intent["digest"])
                or audit != record.intent
                or record.checkpoint != prior.checkpoint
            ):
                raise ValueError("unreconciled intent")
        elif (
            prior.intent is None
            or audit != prior.intent
            or record.checkpoint
            != (
                prior.checkpoint
                if record.state == "failed"
                else prior.intent["operation"]
            )
        ):
            raise ValueError("result without matching intent")
        if record.publication_started != (
            prior.publication_started or record.state == "publishing"
        ) or record.published != (prior.published or record.state == "published"):
            raise ValueError("publication history cannot change")
    for existing in records.values():
        if (existing.request.host, existing.request.repository_id) != (
            record.request.host,
            record.request.repository_id,
        ):
            raise ValueError("journal cannot mix repository identities")
        if existing.request_id == record.request_id:
            continue
        if existing.request.nonce == record.request.nonce:
            raise ControllerError(
                "E_REQUEST_CONFLICT", "Nonce already has different sealed inputs."
            )
        if (
            existing.state != "abandoned"
            and record.state != "abandoned"
            and existing.request.version.split("+")[0]
            == record.request.version.split("+")[0]
        ):
            raise ControllerError(
                "E_RESERVATION", "Version identity is already reserved."
            )
