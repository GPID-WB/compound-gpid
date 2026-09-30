"""Created 2026-08-12. Tests for journaled canonical transactions."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from research_evidence.transactions import (
    ArtifactStore,
    RevisionConflictError,
    SimulatedCrash,
)


def test_transaction_commits_multiple_yaml_files_and_review_history(tmp_path: Path) -> None:
    """Commit staged canonical records with one revision and a commit marker."""
    store = ArtifactStore(tmp_path / "evidence")
    with store.transaction(expected_revision=0, actor="researcher", action="approve") as transaction:
        transaction.stage_yaml("evidence-records.yaml", {"records": [{"id": "e-1"}]})
        transaction.stage_yaml("review-history.yaml", {"events": [{"id": "r-1"}]})
        transaction.commit()

    assert store.current_revision() == 1
    assert yaml.safe_load((store.root / "evidence-records.yaml").read_text()) == {
        "records": [{"id": "e-1"}]
    }
    assert list((store.journal_root).glob("*-commit.yaml"))


def test_artifact_store_rejects_symlinked_journal_ancestor(tmp_path: Path) -> None:
    """Do not create transaction state through a linked runs directory."""
    root = tmp_path / "evidence"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "runs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="unsafe component"):
        ArtifactStore(root)


def test_artifact_store_lock_rejects_replaced_journal_ancestor(
    tmp_path: Path,
) -> None:
    """Do not follow a runs symlink introduced after store construction."""
    root = tmp_path / "evidence"
    store = ArtifactStore(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "runs").rename(root / "runs-original")
    (root / "runs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError):
        with store._exclusive_lock():
            pass


def test_revision_conflict_writes_a_deterministic_conflict_record(tmp_path: Path) -> None:
    """Reject stale writers and preserve a machine-readable conflict record."""
    store = ArtifactStore(tmp_path / "evidence")
    with store.transaction(expected_revision=0, actor="one", action="write") as transaction:
        transaction.stage_yaml("one.yaml", {"value": 1})
        transaction.commit()

    with pytest.raises(RevisionConflictError, match="expected revision 0"):
        with store.transaction(expected_revision=0, actor="two", action="write") as transaction:
            transaction.stage_yaml("two.yaml", {"value": 2})
            transaction.commit()
    assert list(store.journal_root.glob("conflict-*.yaml"))


def test_prepare_crash_recovers_without_publishing_partial_state(tmp_path: Path) -> None:
    """Abort an interrupted prepare operation and remove its staged files."""
    store = ArtifactStore(tmp_path / "evidence")
    with pytest.raises(SimulatedCrash):
        with store.transaction(expected_revision=0, actor="researcher", action="write") as transaction:
            transaction.stage_yaml("records.yaml", {"value": 1})
            transaction.commit(failure_at="after_prepare")

    recovery = store.recover()
    assert recovery[0].status == "aborted"
    assert not (store.root / "records.yaml").exists()
    assert list(store.journal_root.glob("*-abort.yaml"))


def test_replace_crash_recovers_commit_and_marks_derived_state_stale(tmp_path: Path) -> None:
    """Finish a replacement-complete operation and preserve stale-index evidence."""
    store = ArtifactStore(tmp_path / "evidence")
    with pytest.raises(SimulatedCrash):
        with store.transaction(expected_revision=0, actor="researcher", action="write") as transaction:
            transaction.stage_yaml("records.yaml", {"value": 1})
            transaction.mark_derived_stale("lexical.sqlite", "canonical write interrupted")
            transaction.commit(failure_at="after_replace")

    recovery = store.recover()
    assert recovery[0].status == "committed"
    assert store.current_revision() == 1
    derived_state = yaml.safe_load((store.root / "derived-state.yaml").read_text())
    assert derived_state["status"] == "stale"
    assert (store.root / "records.yaml").exists()
