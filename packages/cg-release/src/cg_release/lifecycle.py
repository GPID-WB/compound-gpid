"""Admission and bounded observation; no preparation, build, or publication here."""

import time
from collections.abc import Callable

from cg_release.admission import Receipt
from cg_release.events import ControllerError
from cg_release.journal import Journal, Record
from cg_release.models import Event, Request


def seal(
    receipt: Receipt, journal: Journal, revalidate: Callable[[Request], None]
) -> Record:
    """Revalidate before atomic reservation, e.g. seal(receipt, journal, check).

    The trusted controller supplies authority/protection checks before this call.
    An already sealed exact request is reused; edited issues cannot change it.
    """
    try:
        existing = journal.get(receipt.request_id)
    except ControllerError as error:
        if error.code != "E_REQUEST_MISSING":
            raise
    else:
        if existing.request != receipt.request:
            raise ControllerError(
                "E_REQUEST_CONFLICT", "Inbox differs from sealed request."
            )
        return existing
    return journal.admit(receipt.request, receipt=receipt, revalidate=revalidate)


def watch(
    observe: Callable[[], Event],
    emit: Callable[[Event], None],
    *,
    timeout: float,
    interval: float = 5,
    clock: Callable = time.monotonic,
    sleep: Callable = time.sleep,
) -> None:
    """Observe within an injected deadline; never cancel the durable request.

    Example: watch(read_status, emit, timeout=600). Ctrl+C only stops observation.
    """
    deadline = clock() + timeout
    if timeout <= 0 or interval < 5:
        raise ControllerError("E_ARGUMENT", "Invalid observation bounds.")
    try:
        while clock() < deadline:
            event = observe()
            emit(event)
            if event.observed in {"failed", "published", "complete", "abandoned"}:
                return
            sleep(min(interval, max(0, deadline - clock())))
    except KeyboardInterrupt:
        pass
    emit(
        Event(
            kind="status",
            observed="observation-stopped",
            step="watch",
            message="Observation stopped; the durable request is unchanged.",
        )
    )
