"""Portable request identity and bounded, read-back-verified durable submission."""

import base64
import binascii
import re
from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Protocol

from pydantic import Field, field_validator

from cg_release.events import ControllerError
from cg_release.models import (
    Digest,
    Event,
    Host,
    Positive,
    Request,
    StrictRecord,
    VersionedRecord,
    canonical_bytes,
    load_record,
)


class Locator(VersionedRecord):
    """Portable routing data, not a credential or an admission grant."""

    host: Host
    repository_id: Positive
    repository_slug: Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")]
    requester_id: Positive
    nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    proposal_digest: Digest

    @classmethod
    def from_request(cls, request: Request) -> "Locator":
        """Select only portable identity fields, e.g. Locator.from_request(request)."""
        return load_record(
            cls,
            canonical_bytes(
                {key: request.model_dump(mode="json")[key] for key in cls.model_fields}
            ),
        )

    def encode(self) -> str:
        """Return canonical unpadded base64url, e.g. locator.encode()."""
        return "rc1." + base64.urlsafe_b64encode(canonical_bytes(self)).decode().rstrip(
            "="
        )

    @classmethod
    def decode(cls, value: str) -> "Locator":
        """Decode a strict canonical locator without local files.

        Args: value is the retained rc1 locator emitted before submission.
        Returns: Validated identity; no authority is implied.
        Raises: ControllerError on size, schema, or encoding failure.
        Example: Locator.decode(locator.encode()).
        """
        try:
            if (
                not isinstance(value, str)
                or len(value) > 4096
                or not re.fullmatch(r"rc1\.[A-Za-z0-9_-]+", value)
            ):
                raise ValueError
            raw = base64.b64decode(
                value[4:] + "=" * (-len(value[4:]) % 4), altchars=b"-_", validate=True
            )
            locator = load_record(cls, raw)
            if locator.encode() != value or any(
                p in {".", ".."} for p in locator.repository_slug.split("/")
            ):
                raise ValueError
            return locator
        except (ValueError, binascii.Error):
            raise ControllerError(
                "E_LOCATOR", "Invalid portable request locator."
            ) from None


class InboxBody(VersionedRecord):
    """Exact immutable request envelope; issue labels/comments are not inputs."""

    locator: Annotated[str, Field(max_length=4096)]
    request: Request


class Receipt(StrictRecord):
    """Verified durable inbox receipt, not approval or publication evidence."""

    request_id: str
    number: Positive
    node_id: Annotated[str, Field(min_length=1, max_length=255)]
    url: str
    request: Request
    created_at: Annotated[str, Field(max_length=64)] | None = None

    @field_validator("created_at")
    @classmethod
    def timestamp_is_zoned(cls, value: str | None) -> str | None:
        """Validate remote timestamp text, e.g. 2026-09-11T00:00:00Z."""
        if (
            value is not None
            and datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is None
        ):
            raise ValueError("receipt timestamp lacks timezone")
        return value


class Inbox(Protocol):
    """Provider contract; inventory must be complete or raise, never partial."""

    def create(self, locator: str, body: bytes) -> None:
        """Attempt one issue write; never retry internally."""
        ...

    def inventory(self, locator: Locator) -> list[dict]:
        """Read paginated issue bodies plus authenticated author/edit evidence."""
        ...


def discover(request_id: str, inbox: Inbox) -> Receipt:
    """Resolve a locator by exact content and author without any mutation.

    Args: request_id is portable; inbox reads the verified repository inventory.
    Returns: One verified receipt, e.g. discover(locator, provider).
    Raises: ControllerError for absent, edited, malformed, or ambiguous evidence.
    """
    locator = Locator.decode(request_id)
    matches = []
    for issue in inbox.inventory(locator):
        if not isinstance(issue, dict) or not isinstance(issue.get("body"), str):
            raise ControllerError("E_INBOX", "Inbox inventory is unverifiable.")
        raw = issue["body"]
        try:
            body = load_record(InboxBody, raw.encode("utf-8"))
        except ValueError:
            if request_id in raw or locator.nonce in raw:
                raise ControllerError(
                    "E_REQUEST_CONFLICT", "Matching inbox data is malformed."
                ) from None
            continue
        if body.request.nonce != locator.nonce:
            continue
        if body.locator != request_id or Locator.from_request(body.request) != locator:
            raise ControllerError(
                "E_REQUEST_CONFLICT", "Request nonce has conflicting content."
            )
        if (
            type(issue.get("author_id")) is not int
            or issue["author_id"] != locator.requester_id
            or type(issue.get("repository_id")) is not int
            or issue["repository_id"] != locator.repository_id
            or "last_edited_at" not in issue
            or issue["last_edited_at"] is not None
            or type(issue.get("edit_count")) is not int
            or issue["edit_count"] != 0
            or type(issue.get("number")) is not int
            or issue["number"] <= 0
        ):
            raise ControllerError(
                "E_INBOX", "Issue identity or unedited-body evidence is invalid."
            )
        slug = issue.get("repository_slug", locator.repository_slug)
        if (
            not isinstance(slug, str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug)
            or any(part in {".", ".."} for part in slug.split("/"))
        ):
            raise ControllerError("E_INBOX", "Resolved repository routing is invalid.")
        expected_url = f"https://{locator.host}/{slug}/issues/{issue['number']}"
        if issue.get("url") != expected_url:
            raise ControllerError(
                "E_INBOX", "Issue status URL does not match verified repository."
            )
        try:
            matches.append(
                Receipt(
                    request_id=request_id,
                    number=issue["number"],
                    node_id=issue.get("node_id"),
                    url=expected_url,
                    request=body.request,
                    created_at=issue.get("created_at"),
                )
            )
        except ValueError:
            raise ControllerError("E_INBOX", "Issue receipt is malformed.") from None
    if len(matches) > 1:
        raise ControllerError(
            "E_REQUEST_CONFLICT", "Multiple issues match the request nonce."
        )
    if not matches:
        raise ControllerError(
            "E_SUBMISSION_UNKNOWN",
            "Request is unresolved; retain locator and use status. "
            "Do not repeat start.",
        )
    return matches[0]


def submit(request: Request, inbox: Inbox, emit: Callable[[Event], None]) -> Receipt:
    """Emit intent, attempt one write, and reconcile by exact read-back.

    Args: request has freshly confirmed inputs; inbox is the admission transport;
        emit flushes stdout before the first write, e.g. events.append in tests.
    Returns: Verified queued/pending-validation receipt, never approved execution.
    Raises: ControllerError; caller emits the final error retaining the locator.
    """
    request = load_record(Request, canonical_bytes(request))
    locator = Locator.from_request(request).encode()
    body = canonical_bytes(
        InboxBody(schema_version=1, locator=locator, request=request)
    )
    load_record(InboxBody, body)
    emit(
        Event(
            kind="submission-intent",
            request_id=locator,
            version=request.version,
            step="submission",
            observed="provisional",
            next_action="Retain this locator; status resolves it without resubmission.",
            message="Provisional identity; not a queued receipt.",
        )
    )
    try:
        inbox.create(locator, body)
    except ControllerError:
        # Even an error response cannot establish that no remote acceptance occurred.
        pass
    try:
        receipt = discover(locator, inbox)
    except ControllerError as error:
        if error.code in {"E_REQUEST_CONFLICT", "E_INBOX"}:
            raise
        raise ControllerError(
            "E_SUBMISSION_UNKNOWN",
            "Submission cannot be verified; retain locator and use status. "
            "Do not repeat start.",
        ) from None
    if receipt.request != request:
        raise ControllerError(
            "E_REQUEST_CONFLICT", "Issue read-back differs from the submitted request."
        )
    emit(
        Event(
            kind="receipt",
            request_id=locator,
            version=request.version,
            step="pending-validation",
            observed="queued",
            expected="pending-validation",
            message="Durable submission verified; admission is pending.",
            next_action=f"Status: {receipt.url}",
            proposal={
                "issue_number": receipt.number,
                "issue_node_id": receipt.node_id,
                "status_url": receipt.url,
            },
        )
    )
    return receipt
