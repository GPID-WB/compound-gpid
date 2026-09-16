"""Persisted stage timestamps remain distinct; absent measurements stay unknown."""

from datetime import UTC, datetime

from journal_store import MemoryStore
from test_lifecycle import receipt_fixture

from cg_release.journal import Journal
from cg_release.progress import stage_timings


def test_durable_queue_timing_does_not_invent_future_stage_durations():
    journal = Journal(MemoryStore())
    receipt = receipt_fixture().model_copy(
        update={"created_at": "2026-09-11T00:00:00+00:00"}
    )
    journal.admit(receipt.request, receipt=receipt)
    times = stage_timings(
        journal, receipt.request_id, now=datetime(2026, 9, 12, tzinfo=UTC)
    )
    assert times["queue"] == 86400
    assert times["review"] is None and times["publication"] is None


def test_missing_receipt_timestamp_is_not_zero():
    journal = Journal(MemoryStore())
    receipt = receipt_fixture()
    journal.admit(receipt.request)
    assert stage_timings(journal, receipt.request_id)["submission"] is None
