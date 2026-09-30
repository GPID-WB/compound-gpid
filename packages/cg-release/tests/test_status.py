"""Read-only status and bounded observation never govern request lifetime."""

import pytest

from cg_release.lifecycle import watch
from cg_release.models import Event


def test_watch_uses_injected_deadline_and_preserves_remote_request():
    now, events, reads = [0.0], [], []

    def observe():
        reads.append(1)
        return Event(kind="status", observed="queued")

    watch(
        observe,
        events.append,
        timeout=11,
        interval=5,
        clock=lambda: now[0],
        sleep=lambda seconds: now.__setitem__(0, now[0] + seconds),
    )
    assert len(reads) == 3 and now[0] == 11
    assert events[-1].observed == "observation-stopped"


def test_watch_ctrl_c_stops_only_observation():
    events = []

    def observe():
        raise KeyboardInterrupt

    watch(observe, events.append, timeout=10)
    assert events[-1].observed == "observation-stopped"


@pytest.mark.parametrize("state", ["failed", "published", "complete", "abandoned"])
def test_terminal_snapshot_ends_bounded_watch(state):
    events = []
    watch(lambda: Event(kind="status", observed=state), events.append, timeout=10)
    assert len(events) == 1
