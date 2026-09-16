"""Owned control transactions, reservations and checkpoints (Step 6).

Run: python -B -m pytest scripts/tests/test_autopilot_state.py -q
"""

import hashlib
import json
from pathlib import Path

import pytest

import secure_fs
from autopilot.contracts import MAX_CHECKPOINT_BYTES, PacketError, StateError
from autopilot.checkpoint import (
    begin_effect,
    build_cursor_record,
    checkpoint,
    record_result,
)
from autopilot.records import marker_to_bytes, validate_cursor_record
from autopilot.state import (
    acquire_marker,
    begin_stage,
    load_marker,
    reserve,
    settle_stage,
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


_NONCE = "nonce-a"
_RUN = "run-1"


def _marker_bytes(coordination: Path) -> bytes:
    return (coordination / "marker.json").read_bytes()


def _acquired(tmp_path: Path) -> tuple[Path, Path]:
    coordination = tmp_path / "git" / "cg-autopilot"
    marker = acquire_marker(
        Path("unused-root"),
        coordination,
        run_id=_RUN,
        owner_nonce=_NONCE,
        worktree="C:/worktree",
        branch="cg-autopilot",
        plan_digest=_sha(b"plan"),
        required_base="origin/dev",
    )
    return coordination, marker


def _cursor(tmp_path: Path, revision: int = 1) -> Path:
    path = tmp_path / ".cg-docs/active-state/current.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        build_cursor_record(
            run_id=_RUN,
            revision=revision,
            worktree="C:/worktree",
            branch="cg-autopilot",
            required_base="origin/dev",
            plan_digest=_sha(b"plan"),
            next_action="/cg-work phase1 review:none",
        updated_at="2026-01-01T00:00:00Z",
        )
    )
    return path


def _result_packet(operation_id: str = "op-1", run_id: str = _RUN) -> bytes:
    artifact = {
        "kind": "report",
        "path": ".cg-docs/work-reports/r.md",
        "byte-count": 1,
        "sha256": _sha(b"r"),
        "operation-id": operation_id,
        "content-identity": None,
    }
    payload = {
        "schema-version": 1,
        "stage": "work",
        "status": "succeeded",
        "run-id": run_id,
        "operation-id": operation_id,
        "artifacts": [artifact],
        "head-before": _sha(b"a"),
        "head-after": _sha(b"b"),
        "change-manifest-hash": _sha(b"m"),
        "tests": [],
        "next-stage": None,
    }
    return json.dumps(payload).encode("utf-8")


# ---------------------------------------------------------------------------
# Marker acquisition and ownership
# ---------------------------------------------------------------------------


def test_acquire_marker_without_replacement(tmp_path: Path) -> None:
    coordination = tmp_path / "git" / "cg-autopilot"
    marker = acquire_marker(
        Path("root"), coordination, run_id=_RUN, owner_nonce=_NONCE,
        worktree="C:/w", branch="b", plan_digest=_sha(b"p"), required_base="main",
    )
    assert marker.run_id == _RUN
    assert marker.revision == 0
    assert load_marker(coordination).run_id == _RUN
    with pytest.raises(StateError, match="marker-exists"):
        acquire_marker(
            Path("root"), coordination, run_id="run-2", owner_nonce="nonce-b",
            worktree="C:/w", branch="b", plan_digest=_sha(b"p2"), required_base="main",
        )
    still = load_marker(coordination)
    assert still.run_id == _RUN and still.owner_nonce == _NONCE


def test_load_marker_absent_and_malformed(tmp_path: Path) -> None:
    coordination = tmp_path / "git" / "cg-autopilot"
    assert load_marker(coordination) is None
    coordination.mkdir(parents=True)
    (coordination / "marker.json").write_bytes(b"{not json")
    with pytest.raises(StateError, match="malformed"):
        load_marker(coordination)


def test_foreign_owner_never_takes_over(tmp_path: Path) -> None:
    coordination, _ = _acquired(tmp_path)
    with pytest.raises(StateError, match="foreign-owner"):
        begin_stage(
            load_marker(coordination), coordination,
            owner_nonce="nonce-b", operation_id="op-1", reservation_id="res-1",
        )


# ---------------------------------------------------------------------------
# Reservations: caps, dedupe, released do not consume rounds
# ---------------------------------------------------------------------------


def _reserve(tmp_path: Path, scope: str, key: str, reservation_id: str):
    coordination, marker = _acquired(tmp_path)
    new_marker = reserve(
        marker, coordination, owner_nonce=_NONCE, scope=scope, key=key,
        reservation_id=reservation_id,
    )
    return coordination, new_marker


def test_review_round_cap_is_two(tmp_path: Path) -> None:
    coordination, marker = _reserve(tmp_path, "review-round", "batch-1", "r1")
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r2")
    assert marker.reservations[-1].attempt == 2
    with pytest.raises(StateError, match="reservation-exhausted"):
        reserve(marker, coordination, owner_nonce=_NONCE,
                scope="review-round", key="batch-1", reservation_id="r3")


def test_ci_round_cap_independent_per_pr_key(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE, scope="ci-round",
                     key="host/repo/pr-1", reservation_id="c1")
    marker = reserve(marker, coordination, owner_nonce=_NONCE, scope="ci-round",
                     key="host/repo/pr-1", reservation_id="c2")
    with pytest.raises(StateError, match="reservation-exhausted"):
        reserve(marker, coordination, owner_nonce=_NONCE, scope="ci-round",
                key="host/repo/pr-1", reservation_id="c3")
    marker = reserve(marker, coordination, owner_nonce=_NONCE, scope="ci-round",
                     key="host/repo/pr-2", reservation_id="c4")
    assert marker.reservations[-1].attempt == 1


def test_released_reservation_does_not_consume_round(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="r1")
    record_result(coordination, "op-1", _result_packet())
    marker = settle_stage(
        marker, coordination, owner_nonce=_NONCE, operation_id="op-1",
        outcome="released-no-effect", evidence_refs=("tests/last-run.json",),
    )
    assert marker.reservations[0].status == "released-no-effect"
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r2")
    # Attempt display counts charged attempts only: the released round
    # proved zero effect, so this is charged attempt 1 of the cap.
    assert marker.reservations[-1].attempt == 1
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="r3")
    assert marker.reservations[-1].attempt == 2
    with pytest.raises(StateError, match="reservation-exhausted"):
        reserve(marker, coordination, owner_nonce=_NONCE,
                scope="review-round", key="batch-1", reservation_id="r4")


def test_duplicate_reservation_id_rejected(tmp_path: Path) -> None:
    coordination, marker = _reserve(tmp_path, "review-round", "batch-1", "r1")
    with pytest.raises(StateError, match="reservation-exists"):
        reserve(marker, coordination, owner_nonce=_NONCE,
                scope="review-round", key="batch-1", reservation_id="r1")


def test_fresh_run_cannot_bypass_existing_caps(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE, scope="ci-round",
                     key="host/repo/pr-1", reservation_id="c1")
    reserve(marker, coordination, owner_nonce=_NONCE, scope="ci-round",
            key="host/repo/pr-1", reservation_id="c2")
    with pytest.raises(StateError, match="marker-exists"):
        acquire_marker(
            Path("root"), coordination, run_id="fresh-run", owner_nonce="nonce-x",
            worktree="C:/w", branch="b", plan_digest=_sha(b"p"), required_base="main",
        )
    still = load_marker(coordination)
    assert len([r for r in still.reservations if r.key == "host/repo/pr-1"]) == 2


# ---------------------------------------------------------------------------
# Stage lifecycle: begin-stage, begin-effect, record-result, settle
# ---------------------------------------------------------------------------


def test_begin_stage_requires_reservation_and_sets_in_flight(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    with pytest.raises(StateError, match="missing-reservation"):
        begin_stage(marker, coordination, owner_nonce=_NONCE,
                    operation_id="op-1", reservation_id="res-1")
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    assert marker.in_flight_operation == "op-1"
    assert load_marker(coordination).in_flight_operation == "op-1"
    with pytest.raises(StateError, match="stage-in-flight"):
        begin_stage(marker, coordination, owner_nonce=_NONCE,
                    operation_id="op-2", reservation_id="res-2")


def test_begin_effect_is_one_way(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    begin_stage(marker, coordination, owner_nonce=_NONCE,
                operation_id="op-1", reservation_id="res-1")
    digest = begin_effect(coordination, "op-1", recorded_at="2026-09-15T00:00:00Z")
    assert len(digest) == 64
    with pytest.raises(StateError, match="effect-already-started"):
        begin_effect(coordination, "op-1", recorded_at="2026-09-15T00:01:00Z")
    begin_effect(coordination, "op-2", recorded_at="2026-09-15T00:01:00Z")


def test_record_result_validates_packet_and_is_idempotent(tmp_path: Path) -> None:
    coordination, _ = _acquired(tmp_path)
    packet = _result_packet()
    receipt = record_result(coordination, "op-1", packet)
    assert receipt.sha256 == _sha(packet)
    assert record_result(coordination, "op-1", packet).sha256 == receipt.sha256
    different = _result_packet().replace(b'"head-after": "' + _sha(b"b").encode() + b'"',
                                         b'"head-after": "' + _sha(b"c").encode() + b'"')
    with pytest.raises(StateError, match="receipt-conflict"):
        record_result(coordination, "op-1", different)
    with pytest.raises(PacketError):
        record_result(coordination, "op-2", b'{"schema-version": "bad"}')
    with pytest.raises(StateError, match="operation-mismatch"):
        record_result(coordination, "op-3", _result_packet("op-1"))


def test_settle_stage_outcomes_and_replay(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    record_result(coordination, "op-1", _result_packet())
    with pytest.raises(StateError, match="zero-effect"):
        settle_stage(marker, coordination, owner_nonce=_NONCE,
                     operation_id="op-1", outcome="released-no-effect")
    marker = settle_stage(marker, coordination, owner_nonce=_NONCE,
                          operation_id="op-1", outcome="charged")
    assert marker.reservations[0].status == "charged"
    with pytest.raises(StateError, match="reservation-charged"):
        settle_stage(marker, coordination, owner_nonce=_NONCE,
                     operation_id="op-1", outcome="released-no-effect",
                     evidence_refs=("e",))
    assert load_marker(coordination).in_flight_operation is None


def test_settle_zero_effect_replay_is_idempotent(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    record_result(coordination, "op-1", _result_packet())
    marker = settle_stage(marker, coordination, owner_nonce=_NONCE,
                          operation_id="op-1", outcome="released-no-effect",
                          evidence_refs=("tests/last-run.json",))
    before = _marker_bytes(coordination)
    marker = settle_stage(marker, coordination, owner_nonce=_NONCE,
                          operation_id="op-1", outcome="released-no-effect",
                          evidence_refs=("tests/last-run.json",))
    assert _marker_bytes(coordination) == before
    assert marker.reservations[0].status == "released-no-effect"


def test_uncertain_settlement_keeps_charge(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    marker = settle_stage(marker, coordination, owner_nonce=_NONCE,
                          operation_id="op-1", outcome="uncertain")
    assert marker.reservations[0].status == "uncertain"
    with pytest.raises(StateError, match="reservation-charged"):
        settle_stage(marker, coordination, owner_nonce=_NONCE,
                     operation_id="op-1", outcome="released-no-effect",
                     evidence_refs=("e",))


# ---------------------------------------------------------------------------
# Cursor shape and checkpoint transactions
# ---------------------------------------------------------------------------


def test_cursor_record_closed_shape(tmp_path: Path) -> None:
    raw = build_cursor_record(
        run_id=_RUN, revision=0, worktree="C:/w", branch="b",
        required_base="main", plan_digest=_sha(b"p"), next_action="next",
        updated_at="2026-01-01T00:00:00Z",
    )
    payload = validate_cursor_record(raw)
    assert payload["autopilot"]["run-id"] == _RUN
    assert payload["autopilot"]["revision"] == 0
    bad = json.loads(raw.decode("utf-8"))
    bad["autopilot"]["extra"] = 1
    with pytest.raises(PacketError, match="unexpected field"):
        validate_cursor_record(json.dumps(bad).encode("utf-8"))


def test_checkpoint_happy_path_folds_reservations(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    payload = build_cursor_record(
        run_id=_RUN, revision=1, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"),
        next_action="/cg-work phase2 review:none",
        updated_at="2026-01-01T00:00:00Z",
    )
    marker = checkpoint(
        marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
        fold_reservation_ids=("res-1",), transaction_id="tx-1",
    )
    assert marker.revision == 1
    assert marker.transaction is None
    assert marker.reservations[0].folded_revision == 1
    assert validate_cursor_record(cursor_path.read_bytes())["autopilot"]["revision"] == 1


def test_checkpoint_rejects_wrong_revision_and_unsettled_stage(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    payload = build_cursor_record(
        run_id=_RUN, revision=5, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"), next_action="n",
        updated_at="2026-01-01T00:00:00Z",
    )
    with pytest.raises(StateError, match="cursor-revision"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=(), transaction_id="tx-1")
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    with pytest.raises(StateError, match="unsettled-operation"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=("res-1",), transaction_id="tx-1")


def test_checkpoint_requires_settlement_even_with_receipt(tmp_path: Path) -> None:
    """A recorded result receipt alone never satisfies the checkpoint gate:
    the marker's in-flight operation must be settled first."""
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    record_result(coordination, "op-1", _result_packet())
    payload = build_cursor_record(
        run_id=_RUN, revision=1, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"), next_action="n",
        updated_at="2026-01-01T00:00:00Z",
    )
    with pytest.raises(StateError, match="unsettled-operation"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=("res-1",), transaction_id="tx-1")


def test_begin_stage_rejects_non_pending_reservation(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    marker = begin_stage(marker, coordination, owner_nonce=_NONCE,
                         operation_id="op-1", reservation_id="res-1")
    record_result(coordination, "op-1", _result_packet())
    marker = settle_stage(marker, coordination, owner_nonce=_NONCE,
                          operation_id="op-1", outcome="charged",
                          evidence_refs=("e",))
    with pytest.raises(StateError, match="reservation-status"):
        begin_stage(marker, coordination, owner_nonce=_NONCE,
                    operation_id="op-2", reservation_id="res-1")


def test_digit_leading_run_id_is_valid(tmp_path: Path) -> None:
    coordination = tmp_path / "git" / "cg-autopilot"
    marker = acquire_marker(
        Path("unused-root"), coordination, run_id="20260915-103000",
        owner_nonce=_NONCE, worktree="C:/worktree", branch="cg-autopilot",
        plan_digest=_sha(b"plan"), required_base="origin/dev",
    )
    assert marker.run_id == "20260915-103000"


def test_marker_deadline_is_closed_validated(tmp_path: Path) -> None:
    from autopilot.records import parse_marker

    coordination, marker = _acquired(tmp_path)
    payload = json.loads(marker_to_bytes(marker).decode("utf-8"))
    payload["deadline"] = {
        "schema-version": 1,
        "original-deadline": "2026-09-15T13:00:00Z",
        "effective-deadline": "2026-09-15T13:00:00Z",
        "request-id": None,
        "approval-ref": None,
        "scope-hash": _sha(b"s"),
        "history": [],
    }
    parsed = parse_marker(json.dumps(payload).encode("utf-8"))
    assert parsed.deadline is not None
    for mutation, error in [
        ({"schema-version": 2}, "schema-version"),
        ({"original-deadline": 5}, "str type"),
        ({"scope-hash": "zz"}, "SHA-256"),
        ({"request-id": "UPPER"}, "lowercase ID"),
        ({"history": [{
            "request-id": "ext-1",
            "approval-ref": "a",
            "duration-seconds": 0,
            "application-time": "2026-09-15T13:30:00Z",
            "old-deadline": "2026-09-15T13:00:00Z",
            "new-deadline": "2026-09-15T13:30:00Z",
        }]}, "duration-seconds"),
    ]:
        bad = json.loads(marker_to_bytes(marker).decode("utf-8"))
        base = {
            "schema-version": 1,
            "original-deadline": "2026-09-15T13:00:00Z",
            "effective-deadline": "2026-09-15T13:00:00Z",
            "request-id": None,
            "approval-ref": None,
            "scope-hash": _sha(b"s"),
            "history": [],
        }
        bad["deadline"] = {**base, **mutation}
        with pytest.raises(PacketError, match=error):
            parse_marker(json.dumps(bad).encode("utf-8"))


def test_cursor_record_requires_updated_at_and_typed_artifact_refs() -> None:
    payload = json.loads(build_cursor_record(
        run_id=_RUN, revision=0, worktree="C:/w", branch="b",
        required_base="main", plan_digest=_sha(b"p"), next_action="next",
        updated_at="2026-09-15T10:30:00Z",
    ).decode("utf-8"))
    assert validate_cursor_record(json.dumps(payload).encode("utf-8"))
    for missing in ("2026/09/15 10:30", "yesterday", None, 5):
        bad = dict(payload)
        bad["updatedAt"] = missing
        with pytest.raises(PacketError, match="updatedAt"):
            validate_cursor_record(json.dumps(bad).encode("utf-8"))
    for bad_refs in ("not-a-list", [{"kind": 1, "path": "p", "status": "open"}]):
        bad = dict(payload)
        bad["artifactRefs"] = bad_refs
        with pytest.raises(PacketError, match="artifactRefs"):
            validate_cursor_record(json.dumps(bad).encode("utf-8"))
    good_refs = dict(payload)
    good_refs["artifactRefs"] = [
        {"kind": "review", "path": ".cg-docs/reviews/r.md", "status": "open"},
    ]
    assert validate_cursor_record(json.dumps(good_refs).encode("utf-8"))
    for field in ("plan", "executionReport"):
        bad = dict(payload)
        bad[field] = 5
        with pytest.raises(PacketError, match=field):
            validate_cursor_record(json.dumps(bad).encode("utf-8"))
    bad = dict(payload)
    bad["currentPhase"] = "two"
    with pytest.raises(PacketError, match="currentPhase"):
        validate_cursor_record(json.dumps(bad).encode("utf-8"))


def test_checkpoint_crash_after_intent_leaves_recoverable_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    payload = build_cursor_record(
        run_id=_RUN, revision=1, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"), next_action="n",
        updated_at="2026-01-01T00:00:00Z",
    )
    calls = {"count": 0}
    original = secure_fs.secure_write_bytes

    def fail_cursor_publish(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("injected crash before publish")
        return original(*args, **kwargs)

    monkeypatch.setattr(secure_fs, "secure_write_bytes", fail_cursor_publish)
    with pytest.raises(OSError, match="injected crash"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=("res-1",), transaction_id="tx-1")
    marker_after = load_marker(coordination)
    assert marker_after.transaction is not None
    assert marker_after.transaction.transaction_id == "tx-1"
    assert marker_after.revision == 0
    assert validate_cursor_record(cursor_path.read_bytes())["autopilot"]["revision"] == 0


def test_checkpoint_crash_after_publish_before_ack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    marker = reserve(marker, coordination, owner_nonce=_NONCE,
                     scope="review-round", key="batch-1", reservation_id="res-1")
    payload = build_cursor_record(
        run_id=_RUN, revision=1, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"), next_action="n",
        updated_at="2026-01-01T00:00:00Z",
    )
    calls = {"count": 0}
    original = secure_fs.secure_write_bytes

    def fail_ack(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 3:
            raise OSError("injected crash before acknowledgement")
        return original(*args, **kwargs)

    monkeypatch.setattr(secure_fs, "secure_write_bytes", fail_ack)
    with pytest.raises(OSError, match="injected crash"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=("res-1",), transaction_id="tx-1")
    marker_after = load_marker(coordination)
    assert marker_after.transaction is not None
    assert validate_cursor_record(cursor_path.read_bytes())["autopilot"]["revision"] == 1


def test_direct_child_cursor_write_is_detected(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    from autopilot.checkpoint import bind_initial_cursor

    marker = bind_initial_cursor(
        marker, coordination, owner_nonce=_NONCE,
        cursor_bytes=cursor_path.read_bytes(),
    )
    cursor_path.write_bytes(b"forged cursor bytes without a marker transaction")
    payload = build_cursor_record(
        run_id=_RUN, revision=1, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"), next_action="n",
        updated_at="2026-01-01T00:00:00Z",
    )
    with pytest.raises(StateError, match="cursor-changed"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=(), transaction_id="tx-1")
    assert cursor_path.read_bytes() == b"forged cursor bytes without a marker transaction"


def test_checkpoint_cursor_byte_limit(tmp_path: Path) -> None:
    coordination, marker = _acquired(tmp_path)
    cursor_path = _cursor(tmp_path, revision=0)
    cursor_path.write_bytes(b"x" * (MAX_CHECKPOINT_BYTES + 1))
    payload = build_cursor_record(
        run_id=_RUN, revision=1, worktree="C:/worktree", branch="cg-autopilot",
        required_base="origin/dev", plan_digest=_sha(b"plan"), next_action="n",
        updated_at="2026-01-01T00:00:00Z",
    )
    with pytest.raises(StateError, match="checkpoint-too-large"):
        checkpoint(marker, coordination, cursor_path, payload, owner_nonce=_NONCE,
                   fold_reservation_ids=(), transaction_id="tx-1")
