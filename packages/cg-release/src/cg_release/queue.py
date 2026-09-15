"""Durable scan cursor events; duplicate execution is safe, lost work is not."""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import Field

from cg_release.events import ControllerError
from cg_release.models import VersionedRecord, canonical_bytes, load_record

if TYPE_CHECKING:
    from cg_release.journal import Journal


class QueueCursor(VersionedRecord):
    """Round-robin issue-number cursor; every cycle revisits unresolved work."""

    schema_version: Literal[1] = 1
    kind: Literal["queue"] = "queue"
    after: Annotated[int, Field(ge=0)] = 0
    cycle: Annotated[int, Field(ge=0)] = 0
    ceiling: Annotated[int, Field(ge=0)] = 0
    failures: dict[str, str] = Field(default_factory=dict, max_length=100)


def validate_cursor(previous: QueueCursor, current: QueueCursor, audit: dict) -> None:
    """Validate cursor replay, e.g. validate_cursor(old, new, audit)."""
    from cg_release.journal import digest

    if audit != {"operation": "scan", "previous_cursor": digest(previous)}:
        raise ValueError("cursor predecessor mismatch")
    if not (
        (current.cycle == previous.cycle and current.after > previous.after)
        or (current.cycle == previous.cycle + 1 and current.after == 0)
    ):
        raise ValueError("invalid queue advancement")
    if (
        current.after > current.ceiling
        or (
            current.cycle == previous.cycle
            and previous.ceiling != 0
            and current.ceiling != previous.ceiling
        )
        or (current.cycle != previous.cycle and current.ceiling != 0)
    ):
        raise ValueError("queue snapshot ceiling changed")
    if any(
        not re.fullmatch(r"[1-9][0-9]*", key) or not re.fullmatch(r"E_[A-Z0-9_]+", code)
        for key, code in current.failures.items()
    ):
        raise ValueError("invalid queue failure record")


def cursor_for(journal: "Journal") -> QueueCursor:
    """Read the last verified cursor, e.g. cursor_for(journal)."""
    events = journal.events()
    for event in reversed(events):
        if event["record"].get("kind") == "queue":
            return load_record(QueueCursor, canonical_bytes(event["record"]))
    return QueueCursor()


def advance_cursor(
    journal: "Journal", previous: QueueCursor, current: QueueCursor
) -> None:
    """Commit cursor only after work; CAS loss leaves completed work replayable."""
    from cg_release.journal import digest

    parent, events, _ = journal._read()
    if cursor_for(journal) != previous:
        raise ControllerError("E_STALE_STATE", "A different worker advanced the queue.")
    audit = {"operation": "scan", "previous_cursor": digest(previous)}
    try:
        validate_cursor(previous, current, audit)
    except ValueError:
        raise ControllerError(
            "E_QUEUE", "Queue cursor transition is invalid."
        ) from None
    event = {
        "schema_version": 1,
        "revision": len(events) + 1,
        "parent": parent,
        "previous": events[-1]["digest"] if events else "0" * 64,
        "record": current.model_dump(mode="json"),
        "audit": audit,
    }
    event["occurred_at"] = datetime.now(UTC).isoformat()
    event["digest"] = digest(event)
    try:
        journal.store.append(parent, canonical_bytes(event), current)
    except ControllerError:
        if cursor_for(journal) != current:
            raise
    if cursor_for(journal) != current:
        raise ControllerError("E_QUEUE", "Queue checkpoint did not read back.")


def scan(
    journal: "Journal",
    issues: list[dict],
    process: Callable[[dict], None],
    *,
    limit: int = 20,
    api=None,
    item_seconds: float = 20,
    checkpoint_seconds: float = 40,
) -> QueueCursor:
    """Perform bounded issue work and persist position; no chat/runner wait.

    Args: issues is a complete verified inventory; process is idempotent admission.
    Returns: Durable cursor, e.g. scan(journal, issues, admit_issue, limit=20).
    Raises: ControllerError for corrupt inventory or checkpoint; interrupts propagate.
    """
    previous = cursor_for(journal)
    if item_seconds <= 0 or checkpoint_seconds <= 0:
        raise ControllerError("E_QUEUE", "Queue deadline budgets must be positive.")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ControllerError("E_QUEUE", "Queue work limit is invalid.")
    numbers = [issue.get("number") for issue in issues if isinstance(issue, dict)]
    if (
        len(numbers) != len(issues)
        or any(type(n) is not int or n <= 0 for n in numbers)
        or len(set(numbers)) != len(numbers)
    ):
        raise ControllerError("E_QUEUE", "Queue issue inventory is malformed.")
    if not numbers and previous.after == 0 and previous.ceiling == 0:
        return previous
    ceiling = previous.ceiling or max(numbers, default=0)
    pending = sorted(
        (i for i in issues if previous.after < i["number"] <= ceiling),
        key=lambda i: i["number"],
    )
    failures = {}
    completed = []
    for item in pending[:limit]:
        parent_deadline = api.deadline if api is not None else None
        if api is not None:
            available = parent_deadline - api.clock() - checkpoint_seconds
            if available <= 0:
                break
            api.deadline = min(
                parent_deadline - checkpoint_seconds, api.clock() + item_seconds
            )
        try:
            process(item)
        except ControllerError as error:
            failures[str(item["number"])] = (
                "E_ITEM_DEADLINE"
                if api is not None and api.clock() >= api.deadline
                else error.code
            )
        finally:
            if api is not None:
                api.deadline = parent_deadline
        completed.append(item)
    if pending and not completed:
        return previous
    current = (
        QueueCursor(
            after=completed[-1]["number"],
            cycle=previous.cycle,
            ceiling=ceiling,
            failures=failures,
        )
        if completed and (len(completed) < len(pending) or len(completed) == limit)
        else QueueCursor(cycle=previous.cycle + 1, failures=failures)
    )
    advance_cursor(journal, previous, current)
    return current
