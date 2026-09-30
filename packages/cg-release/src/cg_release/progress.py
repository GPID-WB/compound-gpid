"""Stage timing from retained issue receipt and immutable journal event timestamps."""

from datetime import UTC, datetime

from cg_release.events import ControllerError
from cg_release.journal import Journal


def stage_timings(
    journal: Journal, request_id: str, *, now: datetime | None = None
) -> dict[str, float | None]:
    """Return separate known intervals; never substitute zeros for unobserved stages.

    Example: stage_timings(journal, locator). Wall-clock inversions yield unknown time.
    """
    result = dict.fromkeys(
        [
            "submission",
            "queue",
            "review",
            "build",
            "approval",
            "publication",
            "recovery",
        ]
    )
    names = {
        "queued": "queue",
        "awaiting-review": "review",
        "building": "build",
        "awaiting-approval": "approval",
        "publishing": "publication",
    }
    record = journal.get(request_id)
    current, started = "queue", None
    try:
        if record.receipt is not None and record.receipt.created_at is not None:
            started = datetime.fromisoformat(
                record.receipt.created_at.replace("Z", "+00:00")
            )
        for event in journal.events():
            if event["record"].get("request_id") != request_id:
                continue
            timestamp = datetime.fromisoformat(event["occurred_at"])
            state = names.get(event["record"]["state"])
            if state == current:
                continue
            if current is not None and started is not None:
                duration = (timestamp - started).total_seconds()
                result[current] = duration if duration >= 0 else None
            current, started = state, timestamp
        if current is not None and started is not None:
            duration = ((now or datetime.now(UTC)) - started).total_seconds()
            result[current] = duration if duration >= 0 else None
    except (ValueError, TypeError, KeyError):
        raise ControllerError(
            "E_TIMING", "Persisted stage timestamps are invalid."
        ) from None
    return result
