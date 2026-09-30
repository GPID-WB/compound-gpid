"""Deadline-aware CI classification and approved-extension tests (Step 11).

Fake clocks and runners only; no sleeps, network calls or live remote effects.
Recorded-wire fixtures live under ``scripts/tests/fixtures/autopilot/``.
"""

import json
from pathlib import Path

import pytest

from autopilot import ci, queries as q
from autopilot.recovery import extend_ci_deadline, record_ci_deadline
from autopilot.state import acquire_marker, begin_stage, reserve

FIXTURES = Path(__file__).resolve().parents[0] / "fixtures" / "autopilot"
SHA = "a" * 64
NONCE = "nonce-a"
RUN = "run-1"


def _check(name, status="COMPLETED", conclusion="SUCCESS", url=None):
    return q.Check(name, status, conclusion, url)


# --- clipped timing and pagination --------------------------------------


def test_clipped_request_and_poll_timing() -> None:
    assert ci.clip_request_timeout(100) == 30
    assert ci.clip_request_timeout(10) == 10
    assert ci.clip_request_timeout(0) == 0
    assert ci.clip_request_timeout(-5) == 0
    assert ci.clip_poll_seconds(100) == 15
    assert ci.clip_poll_seconds(4) == 4
    assert ci.clip_poll_seconds(0) == 0


def test_merged_pages_reject_ambiguous_duplicates() -> None:
    assert ci.merged_checks(
        [[_check("a")], [_check("b")]]
    ) == (_check("a"), _check("b"))
    with pytest.raises(ci.CiError, match="ambiguous-check"):
        ci.merged_checks([[_check("a")], [_check("a", conclusion="FAILURE")]])


# -- classification policy table ----------------------------------------


def test_eligible_requires_complete_success() -> None:
    assert ci.classify_observation([_check("a")]).status == "eligible"
    assert ci.classify_observation([_check("a")], required=[ci.RequiredContext("a", None)]).status == "eligible"


def test_failure_and_timeout_are_diagnosed() -> None:
    obs = ci.classify_observation([_check("a", conclusion="FAILURE")])
    assert obs.status == "diagnose"
    assert obs.failing[0].name == "a"
    assert ci.classify_observation([_check("a", conclusion="TIMED_OUT")]).failing[0].conclusion == "TIMED_OUT"


def test_missing_expected_context_waits_not_success() -> None:
    obs = ci.classify_observation([_check("a")], required=[ci.RequiredContext("b", None)])
    assert obs.status == "wait"
    assert obs.reason == "missing-context"


def test_pending_waits() -> None:
    obs = ci.classify_observation([_check("a", status="IN_PROGRESS", conclusion=None)])
    assert obs.status == "wait"
    assert obs.reason == "pending"


def test_blockers_dominate_mixed_results() -> None:
    obs = ci.classify_observation([
        _check("a", conclusion="FAILURE"), _check("b", conclusion="ACTION_REQUIRED"),
    ])
    assert obs.status == "block"
    assert obs.reason == "action-required"


def test_neutral_and_skipped_require_policy() -> None:
    assert ci.classify_observation([_check("a", conclusion="NEUTRAL")]).reason == "neutral-policy-required"
    obs = ci.classify_observation(
        [_check("a", conclusion="NEUTRAL")], non_applicable=frozenset({"a"})
    )
    assert obs.status == "eligible"
    assert ci.classify_observation([_check("a", conclusion="SKIPPED")]).reason == "neutral-policy-required"


def test_cancelled_blocks_without_approved_rerun() -> None:
    assert ci.classify_observation([_check("a", conclusion="CANCELLED")]).reason == "cancelled"
    # Approval alone is never enough: a cancelled required check is redeemable
    # only when a SUCCESS check of the SAME name exists in the same observation.
    obs = ci.classify_observation(
        [_check("a", conclusion="CANCELLED")], cancelled_rerun_approved=frozenset({"a"})
    )
    assert obs.status == "block"
    assert obs.reason == "cancelled"
    obs = ci.classify_observation(
        [
            _check("a", conclusion="SUCCESS"),
            _check("a", conclusion="CANCELLED"),
        ],
        cancelled_rerun_approved=frozenset({"a"}),
    )
    assert obs.status == "eligible"
    # A different-name success never redeems the cancellation.
    obs = ci.classify_observation(
        [
            _check("b", conclusion="SUCCESS"),
            _check("a", conclusion="CANCELLED"),
        ],
        cancelled_rerun_approved=frozenset({"a"}),
    )
    assert obs.status == "block"
    assert obs.reason == "cancelled"
    # More than RERUNS_PER_BATCH redeemed cancellations stay blocked.
    obs = ci.classify_observation(
        [
            _check("a", conclusion="SUCCESS"),
            _check("a", conclusion="CANCELLED"),
            _check("b", conclusion="SUCCESS"),
            _check("b", conclusion="CANCELLED"),
        ],
        cancelled_rerun_approved=frozenset({"a", "b"}),
    )
    assert obs.status == "block"
    assert obs.reason == "cancelled-approval-exceeded"


def test_completed_check_without_conclusion_is_malformed_blocker() -> None:
    check = q.Check("a", "COMPLETED", None, None)
    obs = ci.classify_observation([check])
    assert obs.status == "block"
    assert obs.reason == "malformed-check"


# -- exact run/job identity and safe diagnostics ------------------------


def test_parse_job_url_exact_shape() -> None:
    run_job = ci.parse_job_url("https://github.com/o/r/actions/runs/1001/job/2001")
    assert (run_job.run_id, run_job.job_id) == ("1001", "2001")
    for bad in ("https://github.com/o/r/actions/runs/1001", "../runs/1/job/2",
                "https://example.com/o/r/actions/runs/1/job/2"):
        with pytest.raises(ci.CiError, match="job-url"):
            ci.parse_job_url(bad)


def test_redaction_removes_secret_sentinels_before_output() -> None:
    raw = (
        b"ghp_" + b"a" * 36 + b" token used\n"
        b"github_pat_" + b"ab" * 11 + b"_\n"
        b"xoxb-1234567890abcd\n"
        b"AKIAIOSFODNN7EXAMPLE\n"
        b"ASIAIOSFODNN7EXAMPLE\n"
        b"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature\n"
        b"normal text\n"
    )
    redacted = ci.redact_diagnostic(raw)
    assert b"ghp_" + b"a" * 36 not in redacted
    assert b"github_pat_" + b"ab" * 11 not in redacted
    assert b"xoxb-1234567890abcd" not in redacted
    assert b"AKIAIOSFODNN7EXAMPLE" not in redacted
    assert b"ASIAIOSFODNN7EXAMPLE" not in redacted
    assert b"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature" not in redacted
    assert b"normal text" in redacted
    assert b"<redacted>" in redacted


def test_redaction_matches_case_insensitively() -> None:
    redacted = ci.redact_diagnostic(b"lower ghp_" + b"b" * 36 + b" done")
    assert b"ghp_" + b"b" * 36 not in redacted


def test_bound_diagnostic_size_limits_and_flags_truncation() -> None:
    identity = ci.RunJob("1", "2")
    small = ci.bound_diagnostic(identity, b"token=secret ok")
    assert small.truncated is False
    assert b"secret" not in small.redacted
    big = ci.bound_diagnostic(identity, b"x" * (ci.MAX_DIAGNOSTIC_BYTES + 10))
    assert big.truncated is True
    assert len(big.redacted) == ci.MAX_DIAGNOSTIC_BYTES


# -- recorded-wire fixtures ----------------------------------------------


def test_recorded_rollup_fixture_normalizes() -> None:
    payload = json.loads((FIXTURES / "status-check-rollup.json").read_text(encoding="utf-8"))
    checks = q.normalize_rollup(payload, "rollup")
    assert {c.name for c in checks} == {"native-targets", "pester-prompt-tools", "continuous-integration/legacy"}
    assert checks[0].conclusion == "SUCCESS"


def test_recorded_pr_view_fixture_parses() -> None:
    payload = json.loads((FIXTURES / "pr-view-open.json").read_text(encoding="utf-8"))
    pr = q.parse_pr_view(payload, "pr")
    assert pr.number == 42
    assert pr.base_ref_name == "origin/dev"


# -- parent-only deadline extension ---------------------------------------


def _marker_rig(tmp_path: Path):
    coordination = tmp_path / "git" / "cg-autopilot"
    marker = acquire_marker(
        Path("root"), coordination, run_id=RUN, owner_nonce=NONCE,
        worktree="C:/w", branch="cg-autopilot", plan_digest=SHA,
        required_base="origin/dev",
    )
    return coordination, marker


def test_record_and_extend_deadline_retains_original_and_history(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    assert marker.deadline["original-deadline"] == "2026-09-15T13:00:00Z"
    before_note = tuple(r.status for r in marker.reservations)
    marker = extend_ci_deadline(
        marker, coordination, owner_nonce=NONCE, request_id="ext-1",
        duration_seconds=1800, approval_ref="approval-1", scope_hash=SHA,
        application_time="2026-09-15T13:30:00Z",
    )
    assert marker.deadline["effective-deadline"] == "2026-09-15T14:00:00Z"
    assert marker.deadline["original-deadline"] == "2026-09-15T13:00:00Z"
    assert len(marker.deadline["history"]) == 1
    assert tuple(r.status for r in marker.reservations) == before_note
    assert marker.revision == 0


def test_extend_deadline_replay_is_idempotent(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    marker = extend_ci_deadline(
        marker, coordination, owner_nonce=NONCE, request_id="ext-1",
        duration_seconds=1800, approval_ref="a", scope_hash=SHA,
        application_time="2026-09-15T13:30:00Z",
    )
    replayed = extend_ci_deadline(
        marker, coordination, owner_nonce=NONCE, request_id="ext-1",
        duration_seconds=9999, approval_ref="a", scope_hash=SHA,
        application_time="2026-09-15T14:00:00Z",
    )
    assert replayed.deadline["effective-deadline"] == marker.deadline["effective-deadline"]
    assert len(replayed.deadline["history"]) == 1


def test_extend_blocks_on_missing_observation_writer_and_scope(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    from autopilot.contracts import StateError

    with pytest.raises(StateError, match="no-observation"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-1",
            duration_seconds=60, approval_ref="a", scope_hash=SHA,
            application_time="2026-09-15T13:30:00Z",
        )
    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    with pytest.raises(StateError, match="scope-changed"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-1",
            duration_seconds=60, approval_ref="a", scope_hash="b" * 64,
            application_time="2026-09-15T13:30:00Z",
        )
    marker = reserve(marker, coordination, owner_nonce=NONCE,
                     scope="ci-round", key="host/repo/pr-1", reservation_id="c1")
    marker = begin_stage(marker, coordination, owner_nonce=NONCE,
                         operation_id="op-1", reservation_id="c1")
    with pytest.raises(StateError, match="writer-in-flight"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-2",
            duration_seconds=60, approval_ref="a", scope_hash=SHA,
            application_time="2026-09-15T13:30:00Z",
        )


def test_extend_blocks_on_clock_rollback(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    from autopilot.contracts import StateError

    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    with pytest.raises(StateError, match="clock-rollback"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-1",
            duration_seconds=60, approval_ref="a", scope_hash=SHA,
            application_time="2026-09-15T12:30:00Z",
        )


def test_extend_rejects_unbounded_duration_and_naive_time(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    from autopilot.contracts import StateError

    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    with pytest.raises(StateError, match="must not exceed"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-1",
            duration_seconds=8 * 24 * 60 * 60, approval_ref="a", scope_hash=SHA,
            application_time="2026-09-15T13:30:00Z",
        )
    with pytest.raises(StateError, match="timezone-aware"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-1",
            duration_seconds=60, approval_ref="a", scope_hash=SHA,
            application_time="2026-09-15T13:30:00",
        )


def test_extend_accepts_trusted_clock_with_tolerance(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    coordination, marker = _marker_rig(tmp_path)
    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    clock = lambda: datetime(2026, 9, 15, 13, 30, 0, tzinfo=timezone.utc)
    marker = extend_ci_deadline(
        marker, coordination, owner_nonce=NONCE, request_id="ext-1",
        duration_seconds=1800, approval_ref="a", scope_hash=SHA,
        application_time="2026-09-15T13:30:00Z", clock=clock,
    )
    assert marker.deadline["effective-deadline"] == "2026-09-15T14:00:00Z"
    from autopilot.contracts import StateError

    stale_clock = lambda: datetime(2026, 9, 16, 13, 30, 0, tzinfo=timezone.utc)
    with pytest.raises(StateError, match="clock-mismatch"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-2",
            duration_seconds=1800, approval_ref="a", scope_hash=SHA,
            application_time="2026-09-15T13:30:00Z", clock=stale_clock,
        )


def test_record_deadline_scope_mismatch_raises(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    from autopilot.contracts import StateError

    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    with pytest.raises(StateError, match="deadline-scope-changed"):
        record_ci_deadline(
            marker, coordination, owner_nonce=NONCE,
            original_deadline="2026-09-15T13:00:00Z", scope_hash="b" * 64,
        )
    replayed = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    assert replayed.deadline["original-deadline"] == "2026-09-15T13:00:00Z"


def test_overflow_duration_raises_typed_state_error(tmp_path: Path) -> None:
    coordination, marker = _marker_rig(tmp_path)
    from autopilot.contracts import StateError

    marker = record_ci_deadline(
        marker, coordination, owner_nonce=NONCE,
        original_deadline="2026-09-15T13:00:00Z", scope_hash=SHA,
    )
    with pytest.raises(StateError, match="deadline-overflow"):
        extend_ci_deadline(
            marker, coordination, owner_nonce=NONCE, request_id="ext-1",
            duration_seconds=1800, approval_ref="a", scope_hash=SHA,
            application_time="9999-12-31T23:59:59Z",
        )