"""Retained history crosses the former cap; verification budgets do not erase it."""

import hashlib

import pytest
from journal_store import MemoryStore
from test_lifecycle import receipt_fixture

from cg_release import verification
from cg_release.events import ControllerError
from cg_release.journal import Journal, digest
from cg_release.journal_models import Transaction
from cg_release.models import canonical_bytes
from cg_release.queue import QueueCursor, cursor_for, scan


def test_existing_ten_thousand_events_allow_new_admission_and_cursor(monkeypatch):
    store = MemoryStore()
    parent, previous_hash, previous_cursor = "a" * 40, "0" * 64, QueueCursor()
    # Reconstruct valid retained idle events written by the previous implementation.
    for revision in range(1, 10001):
        cursor = QueueCursor(cycle=revision)
        event = {
            "schema_version": 1,
            "revision": revision,
            "parent": parent,
            "previous": previous_hash,
            "record": cursor.model_dump(mode="json"),
            "audit": {"operation": "scan", "previous_cursor": digest(previous_cursor)},
            "occurred_at": "2026-09-11T00:00:00+00:00",
        }
        event["digest"] = digest(event)
        raw = canonical_bytes(event)
        oid = hashlib.sha1(parent.encode() + raw).hexdigest()
        store.transactions.append(Transaction(oid, parent, store.writer, raw))
        parent, previous_hash, previous_cursor = oid, event["digest"], cursor
    store.revision = 10000
    original_first = store.transactions[0]
    journal = Journal(store)
    receipt = receipt_fixture()
    journal.admit(receipt.request, receipt=receipt)
    scan(journal, [{"number": 1}], lambda item: None)
    assert store.revision == 10002
    assert journal.get(receipt.request_id).receipt == receipt
    assert cursor_for(journal).cycle == 10001
    assert store.transactions[0] == original_first

    ticks = iter([0.0, 2.0])
    store.clock = lambda: next(ticks)
    monkeypatch.setattr(verification, "VERIFICATION_SECONDS", 1.0)
    with pytest.raises(ControllerError) as caught:
        journal.records()
    assert caught.value.code == "E_VERIFICATION_BUDGET"
    assert store.revision == 10002
    store.clock = lambda: 0.0
    assert Journal(store).get(receipt.request_id).receipt == receipt
