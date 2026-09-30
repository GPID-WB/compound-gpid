"""Immutable phase evidence must survive journal replay and uncertain writes."""

from pathlib import Path

import pytest
from journal_store import MemoryStore

from cg_release.events import ControllerError
from cg_release.journal import Journal, digest
from cg_release.models import Request, load_record


def admitted():
    """Return a real journal over a fault-injected offline store."""
    store = MemoryStore()
    journal = Journal(store)
    request = load_record(
        Request, (Path(__file__).parent / "fixtures/request.json").read_bytes()
    )
    return store, journal, journal.admit(request)


def test_stage_evidence_is_retained_across_loss_and_replay():
    store, journal, record = admitted()
    evidence = {"source_sha": record.request.source_sha, "tree": "b" * 40, "pr": 42}
    identity = digest(evidence)
    journal.intent(record.request_id, "prepare", identity)
    store.lose_response = True
    journal.result(
        record.request_id, "prepare", identity, "awaiting-review", evidence=evidence
    )
    assert Journal(store).get(record.request_id).evidence == {"prepare": evidence}
    assert store.revision == 3


def test_new_result_cannot_replace_prior_evidence():
    _, journal, record = admitted()
    for value in [1, 2]:
        evidence = {"pr": value}
        identity = digest(evidence)
        journal.intent(record.request_id, "prepare", identity)
        if value == 1:
            journal.result(
                record.request_id,
                "prepare",
                identity,
                "awaiting-review",
                evidence=evidence,
            )
        else:
            with pytest.raises(ControllerError):
                journal.result(
                    record.request_id,
                    "prepare",
                    identity,
                    "awaiting-review",
                    evidence=evidence,
                )
    assert journal.get(record.request_id).evidence == {"prepare": {"pr": 1}}


def test_evidence_cannot_be_added_by_an_intent_or_forged_admission():
    _, journal, record = admitted()
    from cg_release.journal_rules import validate_transition

    bad = record.model_copy(update={"evidence": {"prepare": {"pr": 1}}})
    with pytest.raises(ValueError):
        validate_transition({}, bad, {"operation": "admit"})
    bad = bad.model_copy(
        update={"intent": {"operation": "prepare", "digest": "c" * 64}}
    )
    with pytest.raises(ValueError):
        validate_transition({record.request_id: record}, bad, bad.intent)


def test_evidence_must_be_bounded_and_match_intent_digest():
    _, journal, record = admitted()
    journal.intent(record.request_id, "prepare", "c" * 64)
    for payload in [{"pr": 42}, {"raw_log": "x" * 65537}]:
        with pytest.raises(ControllerError):
            journal.result(
                record.request_id,
                "prepare",
                "c" * 64,
                "awaiting-review",
                evidence=payload,
            )


def test_evidence_record_size_limit_fails_before_a_journal_write():
    store, journal, record = admitted()
    first = {"data": "a" * 32000}
    journal.intent(record.request_id, "prepare", digest(first))
    journal.result(
        record.request_id, "prepare", digest(first), "awaiting-review", evidence=first
    )
    second = {"data": "b" * 32000}
    journal.intent(record.request_id, "review", digest(second))
    before = store.revision
    with pytest.raises(ControllerError) as caught:
        journal.result(
            record.request_id, "review", digest(second), "building", evidence=second
        )
    assert caught.value.code == "E_EVIDENCE"
    assert store.revision == before
