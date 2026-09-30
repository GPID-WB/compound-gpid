"""Interrupted-run reconciliation and idempotent checkpoint recovery (Step 6).

Run: python -B -m pytest scripts/tests/test_autopilot_recovery.py -q
"""

import hashlib
from pathlib import Path

import pytest

from autopilot.contracts import RecoveryBlocked, StateError
from autopilot.recovery import (
    find_quarantined,
    finish_checkpoint,
    reconcile,
)
from autopilot.checkpoint import (
    build_cursor_record,
    checkpoint,
    record_result,
)
from autopilot.records import validate_cursor_record
from autopilot.state import (
    acquire_marker,
    begin_stage,
    load_marker,
    reserve,
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


_NONCE = "nonce-a"
_RUN = "run-1"


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    coordination = tmp_path / "git" / "cg-autopilot"
    acquire_marker(
        Path("root"), coordination, run_id=_RUN, owner_nonce=_NONCE,
        worktree="C:/worktree", branch="cg-autopilot",
        plan_digest=_sha(b"plan"), required_base="origin/dev",
    )
    cursor = tmp_path / ".cg-docs/active-state/current.json"
    cursor.parent.mkdir(parents=True, exist_ok=True)
    return coordination, cursor


def _cursor_bytes(revision: int) -> bytes:
    return build_cursor_record(
        run_id=_RUN, revision=revision, worktree="C:/worktree",
        branch="cg-autopilot", required_base="origin/dev",
        plan_digest=_sha(b"plan"), next_action="/cg-work phase2 review:none",
        updated_at="2026-01-01T00:00:00Z",
    )


def _result_packet() -> bytes:
    return (
        b'{"schema-version": 1, "stage": "work", "status": "succeeded", '
        b'"run-id": "run-1", "operation-id": "op-1", "artifacts": [], '
        b'"head-before": null, "head-after": null, '
        b'"change-manifest-hash": null, "tests": [], "next-stage": null}'
    )


def test_fresh_state_without_marker_or_cursor(tmp_path: Path) -> None:
    coordination = tmp_path / "git" / "cg-autopilot"
    cursor = tmp_path / ".cg-docs/active-state/current.json"
    reconciliation = reconcile(Path("root"), coordination, cursor)
    assert reconciliation.status == "fresh"


def test_orphan_cursor_blocks_with_diagnostics(tmp_path: Path) -> None:
    coordination = tmp_path / "git" / "cg-autopilot"
    cursor = tmp_path / ".cg-docs/active-state/current.json"
    cursor.parent.mkdir(parents=True)
    cursor.write_bytes(_cursor_bytes(0))
    reconciliation = reconcile(Path("root"), coordination, cursor)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "orphan-cursor"
    assert any("current.json" in d for d in reconciliation.diagnostics)
    assert cursor.exists()


def test_foreign_owner_blocks(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce="nonce-z")
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "foreign-owner"


def test_noop_complete_when_revisions_match(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "noop-complete"


def test_noop_complete_detects_tampered_cursor_digest(tmp_path: Path) -> None:
    from autopilot.checkpoint import bind_initial_cursor

    coordination, cursor = _setup(tmp_path)
    original = _cursor_bytes(0)
    cursor.write_bytes(original)
    marker = load_marker(coordination)
    marker = bind_initial_cursor(
        marker, coordination, owner_nonce=_NONCE, cursor_bytes=original
    )
    assert marker.cursor_digest is not None
    # Tamper while staying structurally valid: the next-action string changes,
    # so the cursor parses but no longer matches the marker-bound digest.
    tampered = original.replace(b"review:none", b"review:gone")
    assert tampered != original
    cursor.write_bytes(tampered)
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "checkpoint-diverged"
    assert cursor.read_bytes() == tampered


def test_interrupted_effect_without_result_blocks(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    marker = load_marker(coordination)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    begin_stage(marker, coordination, owner_nonce=_NONCE,
                operation_id="op-1", reservation_id="res-1")
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "interrupted-effect"
    assert any("op-1" in d for d in reconciliation.diagnostics)


def test_unacknowledged_result_blocks(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    marker = load_marker(coordination)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    begin_stage(marker, coordination, owner_nonce=_NONCE,
                operation_id="op-1", reservation_id="res-1")
    record_result(coordination, "op-1", _result_packet())
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "unacknowledged-result"


def test_intent_with_old_cursor_reports_redo_publish_and_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    marker = load_marker(coordination)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    payload = _cursor_bytes(1)
    monkeypatch.setattr(
        "secure_fs.secure_write_bytes",
        _fail_on_call(2, "crash before cursor publication"),
    )
    with pytest.raises(OSError, match="crash before cursor publication"):
        checkpoint(marker, coordination, cursor, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=("res-1",), transaction_id="tx-1")
    monkeypatch.undo()
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "redo-publish"
    finished = finish_checkpoint(
        Path("root"), coordination, cursor, owner_nonce=_NONCE,
        transaction_id="tx-1", payload=payload,
    )
    assert finished.revision == 1
    assert finished.transaction is None
    assert finished.reservations[0].folded_revision == 1
    assert validate_cursor_record(cursor.read_bytes())["autopilot"]["revision"] == 1


def test_intent_with_target_cursor_acknowledges_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    marker = load_marker(coordination)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    payload = _cursor_bytes(1)
    monkeypatch.setattr(
        "secure_fs.secure_write_bytes",
        _fail_on_call(3, "crash before acknowledgement"),
    )
    with pytest.raises(OSError, match="crash before acknowledgement"):
        checkpoint(marker, coordination, cursor, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=("res-1",), transaction_id="tx-1")
    monkeypatch.undo()
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "redo-acknowledge"
    finished = finish_checkpoint(
        Path("root"), coordination, cursor, owner_nonce=_NONCE,
        transaction_id="tx-1", payload=payload,
    )
    assert finished.revision == 1
    again = finish_checkpoint(
        Path("root"), coordination, cursor, owner_nonce=_NONCE,
        transaction_id="tx-1", payload=payload,
    )
    assert again.revision == 1


def _fail_on_call(index: int, message: str):
    import secure_fs

    original = secure_fs.secure_write_bytes
    state = {"count": 0}

    def failing(*args, **kwargs):
        state["count"] += 1
        if state["count"] == index:
            raise OSError(message)
        return original(*args, **kwargs)

    return failing


def test_checkpoint_diverged_blocks_and_preserves_files(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    marker = load_marker(coordination)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    payload = _cursor_bytes(1)
    import secure_fs

    original = secure_fs.secure_write_bytes
    state = {"count": 0}

    def replace_cursor_with_unknown_bytes(*args, **kwargs):
        state["count"] += 1
        if state["count"] == 2:
            cursor.write_bytes(b"unknown competing writer bytes")
            raise OSError("lost the publication race")
        return original(*args, **kwargs)

    secure_fs.secure_write_bytes = replace_cursor_with_unknown_bytes
    try:
        with pytest.raises(OSError, match="lost the publication race"):
            checkpoint(marker, coordination, cursor, payload, owner_nonce=_NONCE,
                       fold_reservation_ids=("res-1",), transaction_id="tx-1")
    finally:
        secure_fs.secure_write_bytes = original
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "checkpoint-diverged"
    with pytest.raises(RecoveryBlocked):
        finish_checkpoint(Path("root"), coordination, cursor, owner_nonce=_NONCE,
                          transaction_id="tx-1", payload=payload)
    assert cursor.read_bytes() == b"unknown competing writer bytes"
    assert load_marker(coordination).transaction is not None


def test_quarantined_state_blocks_without_removal(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(0))
    coordination.mkdir(parents=True, exist_ok=True)
    quarantine = coordination / ".marker.json.deadbeef.previous"
    quarantine.write_bytes(b"preserved quarantine bytes")
    found = find_quarantined(coordination, cursor)
    assert ".marker.json.deadbeef.previous" in found[0]
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "quarantined-state"
    assert any("deadbeef.previous" in d for d in reconciliation.diagnostics)
    assert quarantine.exists()
    with pytest.raises(RecoveryBlocked, match="quarantined-state"):
        finish_checkpoint(Path("root"), coordination, cursor, owner_nonce=_NONCE,
                          transaction_id="tx-1")


def test_revision_diverged_blocks(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    cursor.write_bytes(_cursor_bytes(3))
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "revision-diverged"


def test_missing_cursor_after_marker_blocks(tmp_path: Path) -> None:
    coordination, cursor = _setup(tmp_path)
    reconciliation = reconcile(Path("root"), coordination, cursor, owner_nonce=_NONCE)
    assert reconciliation.status == "blocked"
    assert reconciliation.reason == "cursor-absent"
