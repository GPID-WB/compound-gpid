"""Journal transition, hash-chain, nonce, and reservation invariants."""

from pathlib import Path

import pytest
from journal_store import MemoryStore

from cg_release.events import ControllerError
from cg_release.journal import Journal
from cg_release.models import Request, load_record


@pytest.fixture
def release_request() -> Request:
    return load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )


def test_admission_is_atomic_idempotent_and_reserves_normalized_version(
    release_request: Request,
) -> None:
    request = release_request
    store = MemoryStore()
    journal = Journal(store)
    record = journal.admit(request)
    assert journal.admit(request) == record
    assert store.revision == 1
    assert journal.reservations() == [request.version.split("+")[0]]
    other = request.model_copy(update={"nonce": "b" * 32})
    with pytest.raises(ControllerError) as caught:
        journal.admit(other)
    assert caught.value.code == "E_RESERVATION"
    assert store.revision == 1


def test_same_nonce_different_content_is_not_idempotent(
    release_request: Request,
) -> None:
    request = release_request
    journal = Journal(MemoryStore())
    journal.admit(request)
    with pytest.raises(ControllerError) as caught:
        journal.admit(request.model_copy(update={"proposal_digest": "f" * 64}))
    assert caught.value.code == "E_REQUEST_CONFLICT"


def test_conflict_retry_preserves_concurrent_winner(release_request: Request) -> None:
    request = release_request
    store = MemoryStore()
    journal = Journal(store)
    other = request.model_copy(
        update={"nonce": "b" * 32, "version": "2.0.0", "tag": "v2.0.0"}
    )
    store.before_write = lambda: Journal(store).admit(other)
    journal.admit(request)
    assert len(journal.records()) == 2
    assert set(journal.reservations()) == {request.version.split("+")[0], "2.0.0"}


def test_lost_update_response_is_reconciled_without_duplicate_event(
    release_request: Request,
) -> None:
    request = release_request
    store = MemoryStore()
    store.lose_response = True
    journal = Journal(store)
    journal.admit(request)
    assert store.revision == 1
    assert len(journal.events()) == 1


def test_intent_result_checkpoint_survives_new_worker(release_request: Request) -> None:
    request = release_request
    store = MemoryStore()
    first = Journal(store)
    record = first.admit(request)
    first.intent(record.request_id, "prepare", "a" * 64)
    restarted = Journal(store)
    pending = restarted.get(record.request_id)
    assert pending.intent == {"operation": "prepare", "digest": "a" * 64}
    restarted.result(record.request_id, "prepare", "a" * 64, "awaiting-review")
    assert restarted.get(record.request_id).state == "awaiting-review"
    assert restarted.get(record.request_id).intent is None
    with pytest.raises(ControllerError):
        restarted.result(record.request_id, "prepare", "b" * 64, "complete")


@pytest.mark.parametrize(
    "tamper", ["event", "record", "reservation", "writer", "parent"]
)
def test_corruption_blocks_recovery(release_request: Request, tamper: str) -> None:
    request = release_request
    store = MemoryStore()
    journal = Journal(store)
    journal.admit(request)
    store.corrupt(tamper)
    with pytest.raises(ControllerError):
        journal.records()


def test_abandon_requires_audited_absence_and_retains_history(
    release_request: Request,
) -> None:
    request = release_request
    journal = Journal(MemoryStore())
    record = journal.admit(request)
    with pytest.raises(ControllerError):
        journal.abandon(
            record.request_id,
            actor_id=7,
            role="write",
            reason="stop",
            effects_absent=True,
        )
    with pytest.raises(ControllerError):
        journal.abandon(
            record.request_id,
            actor_id=7,
            role="maintain",
            reason="stop",
            effects_absent=False,
        )
    journal.abandon(
        record.request_id,
        actor_id=7,
        role="maintain",
        reason="stop",
        effects_absent=True,
    )
    assert journal.get(record.request_id).state == "abandoned"
    assert journal.reservations() == []
    assert len(journal.events()) == 2


def test_failed_result_retains_checkpoint_and_retryability(
    release_request: Request,
) -> None:
    journal = Journal(MemoryStore())
    record = journal.admit(release_request)
    journal.intent(record.request_id, "prepare", "a" * 64)
    failed = journal.result(
        record.request_id,
        "prepare",
        "a" * 64,
        "failed",
        error_code="E_PREPARATION",
        retryable=True,
    )
    assert failed.state == "failed" and failed.failed_step == "prepare"
    assert failed.checkpoint == "admitted" and failed.retryable is True
    assert failed.error == "E_PREPARATION" and journal.reservations()
