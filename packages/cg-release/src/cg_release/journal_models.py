"""Strict request state and journal storage boundary types."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from pydantic import Field

from cg_release.admission import Receipt
from cg_release.models import Request, StrictRecord, canonical_bytes


def digest(value: dict | StrictRecord) -> str:
    """Return canonical SHA-256, e.g. digest({'revision': 1})."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_event_header(
    event: dict,
    transaction: "Transaction",
    *,
    revision: int,
    parent: str,
    previous: str,
    writer: str,
) -> str:
    """Validate an event envelope, e.g. validate_event_header(...)."""
    if not isinstance(event, dict) or set(event) != {
        "schema_version",
        "revision",
        "parent",
        "previous",
        "record",
        "audit",
        "digest",
        "occurred_at",
    }:
        raise ValueError("invalid event envelope")
    if datetime.fromisoformat(event["occurred_at"]).utcoffset() is None:
        raise ValueError("event time must include its timezone")
    unsigned = {k: v for k, v in event.items() if k != "digest"}
    if (
        type(event["schema_version"]) is not int
        or event["schema_version"] != 1
        or type(event["revision"]) is not int
        or event["revision"] != revision
        or transaction.parent != parent
        or event["parent"] != parent
        or transaction.writer != writer
        or event["previous"] != previous
        or event["digest"] != hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    ):
        raise ValueError("invalid event predecessor or writer")
    return event["digest"]


STATES = Literal[
    "queued",
    "awaiting-review",
    "building",
    "awaiting-approval",
    "publishing",
    "published",
    "complete",
    "failed",
    "abandoned",
]


class Record(StrictRecord):
    """Current request state derived from verified journal events."""

    request_id: str
    request: Request
    state: STATES = "queued"
    checkpoint: str = "admitted"
    intent: dict[str, str] | None = None
    error: str | None = None
    failed_step: str | None = None
    retryable: bool = False
    receipt: Receipt | None = None
    publication_started: bool = False
    published: bool = False
    evidence: dict[str, dict] = Field(default_factory=dict)


@dataclass(frozen=True)
class Transaction:
    """One verified Git commit and its single immutable event blob."""

    commit: str
    parent: str
    writer: str
    event: bytes


class Store(Protocol):
    """A store proves ancestry/writer and atomically appends against expected head."""

    writer: str

    def history(self) -> tuple[str, list[Transaction]]:
        """Return bootstrap anchor and chronological verified transactions."""
        ...

    def append(self, parent: str, event: bytes, record: Record) -> None:
        """Non-force sibling update; uncertain outcomes must be reconciled."""
        ...
