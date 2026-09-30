"""Atomic one-run seals and repository-wide publication owner claims."""

import pytest

from cg_release.events import ControllerError
from cg_release.journal import digest
from cg_release.journal_checkpoint import atomic_publication_checkpoint
from cg_release.publication_control import (
    acquire_owner,
    active_owner,
    release_owner,
    store_seal,
)


def test_one_run_one_seal_and_atomic_lost_response(publication):
    journal, record, *_ = publication
    seal = {
        "run_id": 41,
        "run_attempt": 1,
        "digest": digest({"ok": True}),
        "inputs": {"ok": True},
        "nonce": "a" * 32,
    }
    journal.store.lose_response = True
    saved = store_seal(journal, record, seal)
    assert saved.evidence["publication-seal-41"] == seal
    with pytest.raises(ControllerError):
        store_seal(journal, saved, seal)
    assert (
        len(
            [
                e
                for e in journal.events()
                if e["audit"]["operation"] == "publication-seal-41"
            ]
        )
        == 1
    )


def test_two_runs_cannot_seal_one_dispatch_nonce(publication):
    journal, record, *_ = publication
    seal = {
        "run_id": 41,
        "run_attempt": 1,
        "digest": digest({"ok": True}),
        "inputs": {"ok": True},
        "nonce": "a" * 32,
    }
    saved = store_seal(journal, record, seal)
    with pytest.raises(ControllerError):
        store_seal(journal, saved, {**seal, "run_id": 42})


def test_recovery_owner_metadata_preserves_unresolved_effect(publication):
    journal, record, *_ = publication
    record = acquire_owner(journal, record, run_id=41, expires_at=3700, now=100)
    record = journal.intent(record.request_id, "publication-tag", "a" * 64)
    proof = {
        "run": {"id": 41, "run_attempt": 1, "status": "completed"},
        "effects_reconciled": True,
    }
    released = release_owner(journal, record, run_id=42, terminal_proof=proof, now=4000)
    assert released.intent == record.intent
    acquired = acquire_owner(journal, released, run_id=42, expires_at=7600, now=4000)
    assert acquired.intent == record.intent


def test_owner_claim_and_release_are_immutable(publication):
    journal, record, *_ = publication
    acquired = acquire_owner(journal, record, run_id=41, expires_at=3700, now=100)
    assert active_owner(journal.records())[1]["run_id"] == 41
    with pytest.raises(ControllerError):
        acquire_owner(journal, acquired, run_id=42, expires_at=3700, now=100)
    released = release_owner(journal, acquired, run_id=41)
    assert active_owner(journal.records()) is None
    acquired2 = acquire_owner(journal, released, run_id=42, expires_at=3700, now=100)
    assert (
        acquired2.evidence["publication-owner-41"]
        == acquired.evidence["publication-owner-41"]
    )


def test_other_request_cannot_claim_repository_owner(publication):
    journal, record, *_ = publication
    other_request = record.request.model_copy(
        update={"nonce": "d" * 32, "version": "1.6.0", "tag": "v1.6.0"}
    )
    other = journal.admit(other_request)
    acquire_owner(journal, record, run_id=41, expires_at=3700, now=100)
    with pytest.raises(ControllerError):
        acquire_owner(journal, other, run_id=42, expires_at=3700, now=100)


def test_restore_cannot_insert_two_live_owners(publication):
    journal, record, *_ = publication
    acquired = acquire_owner(journal, record, run_id=41, expires_at=3700, now=100)
    with pytest.raises(ControllerError):
        atomic_publication_checkpoint(
            journal,
            acquired,
            "publication-owner-42",
            {"run_id": 42, "credential_expires_at": 3700},
            acquired.state,
        )
