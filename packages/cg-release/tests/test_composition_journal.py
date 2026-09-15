"""Composition records preserve lifetime history without expanding release records."""

import pytest
from journal_store import MemoryStore
from test_publisher import invoke

from cg_release.journal import Journal, digest
from cg_release.models import canonical_bytes
from cg_release.prepare_stage import checkpoint


def published(publication):
    """Build a published fixture with the production journal and publisher."""
    journal = Journal(MemoryStore())
    record = journal.admit(publication[1].request)
    for name, state in [
        ("prepare", "awaiting-review"),
        ("review", "building"),
        ("build", "awaiting-approval"),
    ]:
        record = checkpoint(journal, record, name, {"ok": True}, state)
    return journal, invoke((journal, record, *publication[2:]))


def test_separate_composition_records_exceed_old_lifetime_limit(publication):
    from cg_release.composition_journal import CompositionJournal

    journal, record = published(publication)
    before = canonical_bytes(record)
    compositions = CompositionJournal(journal)
    for number in range(1, 65):
        ticket = {
            "nonce": f"{number:032x}",
            "policy_digest": "a" * 64,
            "authority_actor_id": 7,
            "releases": [{"tag": "v1.0.0", "sha": "b" * 40}],
            "dev_sha": f"{number:040x}",
            "padding": "x" * 1400,
        }
        item = compositions.create(record, ticket)
        assert item.number == number
        item = compositions.intent(
            item, {"ref": "main", "inputs": {"nonce": ticket["nonce"]}}
        )
        item = compositions.save(item, "dispatch", {"accepted": True})
        item = compositions.save(
            item, "registration", {"run_id": number, "request_digest": digest(ticket)}
        )
        item = compositions.save(item, "composition", {"manifest_sha256": "c" * 64})
        compositions.save(item, "terminal", {"run_id": number, "conclusion": "success"})
    assert canonical_bytes(journal.get(record.request_id)) == before
    assert len(compositions.records()) == 64
    assert sum(len(canonical_bytes(item)) for item in compositions.records()) > 65536
    assert all(len(canonical_bytes(item)) < 65536 for item in compositions.records())
    assert journal.reservations() == [record.request.version]
    assert len(journal.events()) > 64 * 4


def test_composition_append_rejects_changed_ticket_and_lost_cas(publication):
    from cg_release.composition_journal import CompositionJournal
    from cg_release.events import ControllerError

    journal, record = published(publication)
    compositions = CompositionJournal(journal)
    item = compositions.create(record, {"nonce": "f" * 32})
    item = compositions.save(
        item, "registration", {"run_id": 10, "request_digest": digest(item.ticket)}
    )
    with pytest.raises(ControllerError):
        compositions.save(item, "registration", {"run_id": 11})
    assert compositions.records()[0] == item


def test_registration_must_identify_its_own_ticket(publication):
    from cg_release.composition_journal import CompositionJournal
    from cg_release.events import ControllerError

    journal, record = published(publication)
    compositions = CompositionJournal(journal)
    item = compositions.create(record, {"nonce": "1" * 32})
    with pytest.raises(ControllerError):
        compositions.save(
            item, "registration", {"run_id": 12, "request_digest": "a" * 64}
        )
    assert compositions.records() == [item]


def test_composition_append_reuses_one_authenticated_operation_view(publication):
    from cg_release.composition_journal import CompositionJournal

    journal, record = published(publication)
    history, calls = journal.store.history, []

    def counted_history():
        calls.append(1)
        return history()

    journal.store.history = counted_history
    CompositionJournal(journal).create(record, {"nonce": "1" * 32})
    # Number selection, exact CAS input, and post-write read-back. No duplicate
    # full history acquisition to derive compositions from that same CAS input.
    assert len(calls) == 3
