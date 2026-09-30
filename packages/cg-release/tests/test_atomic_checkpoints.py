"""Atomic build data cannot bypass intents for external or publication actions."""

from pathlib import Path

import pytest
from journal_store import MemoryStore
from test_builds import inputs

from cg_release.events import ControllerError
from cg_release.journal import Journal, digest
from cg_release.journal_checkpoint import atomic_build_checkpoint
from cg_release.models import Request, load_record


def ready():
    journal = Journal(MemoryStore())
    request = load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )
    record = journal.admit(request)
    sealed, *_ = inputs()
    for operation, state, evidence in [
        ("prepare", "awaiting-review", {}),
        (
            "review-binding",
            "building",
            {
                "release_sha": sealed["release_sha"],
                "release_tree": sealed["release_tree"],
            },
        ),
    ]:
        journal.intent(record.request_id, operation, digest(evidence))
        record = journal.result(
            record.request_id, operation, digest(evidence), state, evidence=evidence
        )
    return journal, record, sealed


def test_lost_atomic_response_reconciles_complete_ticket_once():
    journal, record, sealed = ready()
    before = journal.store.revision
    journal.store.lose_response = True
    result = atomic_build_checkpoint(
        journal, record, "build-request-1", sealed, "building"
    )
    assert result.intent is None and result.evidence["build-request-1"] == sealed
    assert journal.store.revision == before + 1
    assert journal.events()[-1]["audit"]["atomic"] is True


@pytest.mark.parametrize(
    "operation,state",
    [
        ("publish", "publishing"),
        ("build-dispatch-1", "building"),
        ("build-request-1", "awaiting-approval"),
    ],
)
def test_external_effects_cannot_use_atomic_build_checkpoint(operation, state):
    journal, record, sealed = ready()
    with pytest.raises(ControllerError):
        atomic_build_checkpoint(journal, record, operation, sealed, state)
    assert journal.get(record.request_id) == record


def test_opaque_existing_intent_is_not_cleared_or_replaced():
    journal, record, sealed = ready()
    retained = journal.intent(record.request_id, "build-request-1", "0" * 64)
    with pytest.raises(ControllerError):
        atomic_build_checkpoint(
            journal, retained, "build-request-1", sealed, "building"
        )
    assert journal.get(record.request_id) == retained


def test_atomic_ticket_sequence_and_registration_binding_are_enforced():
    journal, record, sealed = ready()
    with pytest.raises(ControllerError):
        atomic_build_checkpoint(journal, record, "build-request-2", sealed, "building")
    _, registration, *_ = inputs()
    with pytest.raises(ControllerError):
        atomic_build_checkpoint(
            journal, record, "build-registration-1", registration, "building"
        )
