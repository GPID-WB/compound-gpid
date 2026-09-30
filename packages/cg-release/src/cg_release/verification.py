"""Bound verification time without imposing a total retained-event capacity."""

import time
from collections.abc import Callable

from cg_release.events import ControllerError

VERIFICATION_SECONDS = 120.0


def verification_guard(store) -> Callable[[], float]:
    """Return a read-budget guard; expiry never deletes or truncates history.

    Example: check = verification_guard(store); remaining = check(). Remote stores
    also use the active command/item deadline, including during cached replay.
    """
    api = getattr(store, "api", None)
    clock = getattr(api, "clock", getattr(store, "clock", time.monotonic))
    deadline = clock() + VERIFICATION_SECONDS
    if api is not None and getattr(api, "deadline", None) is not None:
        deadline = min(deadline, api.deadline)

    def check() -> float:
        remaining = deadline - clock()
        if remaining <= 0:
            raise ControllerError(
                "E_VERIFICATION_BUDGET",
                "Journal read budget expired; retained history is unchanged.",
            )
        return remaining

    return check
