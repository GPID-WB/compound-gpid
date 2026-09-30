"""Direct regressions for the Phase 3 full-review findings."""

from datetime import datetime, timedelta

import pytest
from journal_store import MemoryStore
from test_lifecycle import receipt_fixture
from test_remote_faults import Server

from cg_release.events import emit_event
from cg_release.git_journal import transaction_files
from cg_release.github_journal import GitHubJournalStore
from cg_release.journal import Journal
from cg_release.models import Event, canonical_bytes
from cg_release.progress import stage_timings
from cg_release.queue import scan


@pytest.mark.parametrize("state", ["queued", "failed", "published", "complete"])
def test_human_status_has_state_version_checkpoint_and_expectation(state, capsys):
    emit_event(
        Event(
            kind="status",
            observed=state,
            version="1.0.0",
            step="verified-checkpoint",
            expected="complete",
        ),
        json_output=False,
    )
    text = capsys.readouterr().out
    for value in (
        f"observed: {state}",
        "version: 1.0.0",
        "step: verified-checkpoint",
        "expected: complete",
    ):
        assert value in text


def test_unknown_queue_start_stays_unknown_after_admission():
    journal = Journal(MemoryStore())
    receipt = receipt_fixture()
    journal.admit(receipt.request, receipt=receipt)
    now = datetime.fromisoformat(journal.events()[0]["occurred_at"]) + timedelta(
        seconds=60
    )
    assert stage_timings(journal, receipt.request_id, now=now)["queue"] is None


def test_repeated_empty_scans_make_no_remote_journal_writes(tmp_path):
    server = Server(tmp_path)
    journal = Journal(
        GitHubJournalStore(server, server.policy, bot_id=77, writable=True)
    )
    for _ in range(5):
        scan(
            journal, [], lambda item: pytest.fail("Empty inventory cannot process work")
        )
    assert server.writes == 0 and journal.events() == []


@pytest.mark.parametrize("revision", [10001, 10000000000])
def test_event_revision_is_not_a_lifetime_capacity_limit(revision):
    record = Journal(MemoryStore()).admit(receipt_fixture().request)
    files = transaction_files(canonical_bytes({"revision": revision}), record)
    assert f"events/{revision:010d}.json" in files


def test_admission_and_checkpoint_continue_past_former_event_limit(
    monkeypatch, tmp_path
):
    from cg_release import git_journal

    # Reproduce the review's reduced-bound probe on the old implementation.
    if hasattr(git_journal, "MAX_EVENTS"):
        monkeypatch.setattr(git_journal, "MAX_EVENTS", 2)
    server = Server(tmp_path)
    journal = Journal(
        GitHubJournalStore(server, server.policy, bot_id=77, writable=True)
    )
    record = journal.admit(receipt_fixture().request)
    journal.intent(record.request_id, "validate", "a" * 64)
    journal.result(record.request_id, "validate", "a" * 64, "queued")
    scan(journal, [{"number": 1}], lambda item: None)
    assert len(journal.events()) == 4
    assert journal.get(record.request_id).checkpoint == "validate"
