"""Persistent bounded queue cursors survive dropped wakeups and worker loss."""

import pytest
from journal_store import MemoryStore

from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.queue import QueueCursor, advance_cursor, cursor_for, scan


def test_more_than_one_hundred_requests_and_lost_wakeup_are_revisited():
    journal = Journal(MemoryStore())
    issues = [{"number": i} for i in range(1, 106)]
    processed = []
    for _ in range(12):
        scan(journal, issues, lambda item: processed.append(item["number"]), limit=10)
    assert set(processed) == set(range(1, 106))
    assert processed.count(1) == 2
    assert cursor_for(Journal(journal.store)).cycle == 1


def test_shutdown_before_cursor_write_replays_idempotent_work():
    journal = Journal(MemoryStore())
    attempts = []

    def worker(item):
        attempts.append(item["number"])
        if len(attempts) == 1:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        scan(journal, [{"number": 1}], worker)
    assert cursor_for(journal).after == 0
    scan(Journal(journal.store), [{"number": 1}], worker)
    assert attempts == [1, 1]


def test_corrupt_or_stale_cursor_does_not_overwrite_new_worker():
    journal = Journal(MemoryStore())
    old = cursor_for(journal)
    advance_cursor(journal, old, QueueCursor(after=10, cycle=0, ceiling=20))
    with pytest.raises(ControllerError):
        advance_cursor(journal, old, QueueCursor(after=20, cycle=0, ceiling=20))
    assert cursor_for(journal).after == 10


def test_rejected_request_does_not_starve_queue_but_is_recorded():
    journal = Journal(MemoryStore())

    def reject(item):
        raise ControllerError("E_INBOX", "Edited issue.")

    scan(journal, [{"number": 1}, {"number": 2}], reject, limit=1)
    cursor = cursor_for(journal)
    assert cursor.after == 1 and cursor.failures == {"1": "E_INBOX"}


def test_continuous_arrivals_do_not_prevent_revisiting_old_requests():
    journal = Journal(MemoryStore())
    issues = [{"number": i} for i in range(1, 21)]
    processed = []
    for iteration in range(8):
        scan(journal, issues, lambda item: processed.append(item["number"]), limit=10)
        last = max(item["number"] for item in issues)
        issues.extend({"number": i} for i in range(last + 1, last + 21))
    assert processed.count(1) >= 2
