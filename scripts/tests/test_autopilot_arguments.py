"""Strict invocation, batch grammar and plan validation tests (Phase 2, Step 4).

Run: python -B -m pytest scripts/tests/test_autopilot_arguments.py -q
"""

from pathlib import Path

import pytest

from autopilot.arguments import (
    BatchSegment,
    Invocation,
    expand_single_phase_commands,
    parse_batch_segments,
    parse_ci_timeout,
    parse_invocation,
    validate_base_ref,
)
from autopilot.plan import (
    execution_digest,
    progress_delta,
    read_plan,
    validate_autopilot_plan,
    validate_batches,
)
from autopilot.contracts import ArgumentError, PlanError
from tests.autopilot_plan_fixture import plan_source_valid


# ---------------------------------------------------------------------------
# Batch segment grammar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1", ((1, 1),)),
        ("1,3,5", ((1, 1), (3, 3), (5, 5))),
        ("1-3,5", ((1, 3), (5, 5))),
        (" 1 - 3 , 5 ", None),
        ("1-1", ((1, 1),)),
        ("7-9,10-12", ((7, 9), (10, 12))),
    ],
)
def test_valid_batch_segments(text: str, expected: object) -> None:
    """Valid segments parse; surrounding whitespace is trimmed, internal not."""
    if expected is None:
        with pytest.raises(ArgumentError, match="invalid segment"):
            parse_batch_segments(text)
        return
    segments = parse_batch_segments(text)
    assert tuple((s.start, s.end) for s in segments) == expected


@pytest.mark.parametrize(
    "text,error",
    [
        ("", "empty batches"),
        ("   ", "empty batches"),
        ("1,", "empty segment"),
        (",1", "empty segment"),
        ("1,,2", "empty segment"),
        ("1 2", "invalid segment"),
        ("1-", "invalid segment"),
        ("-1", "invalid segment"),
        ("+1", "invalid segment"),
        ("1-3-5", "invalid segment"),
        ("1--3", "invalid segment"),
        ("a", "invalid segment"),
        ("1.5", "invalid segment"),
        ("1,5b", "invalid segment"),
        ("0", "invalid segment"),
        ("0-2", "invalid segment"),
        ("2-1", "invalid segment"),
        ("1-2,2-3", "overlap"),
        ("1-2,2", "overlap"),
        ("1,1", "overlap"),
        ("3-5,1-2", "overlap"),
        ("1-3,2-4", "overlap"),
        ("1-99999999", "at most"),
        ("1-1001", "at most"),
    ],
)
def test_invalid_batch_segments(text: str, error: str) -> None:
    """Every invalid grammar case is rejected with a typed bounded error."""
    with pytest.raises(ArgumentError, match=error):
        parse_batch_segments(text)


def test_wide_segment_fails_fast_without_allocation() -> None:
    """An astronomical segment is bounded at parse time, before expansion."""
    with pytest.raises(ArgumentError, match="at most"):
        BatchSegment(1, 99999999)


def test_segment_iterates_lazily() -> None:
    segment = BatchSegment(2, 4)
    phases = segment.iter_phases()
    assert next(phases) == 2
    assert tuple(phases) == (3, 4)


def test_segment_expands_phase_list() -> None:
    segment = BatchSegment(2, 4)
    assert segment.phases() == (2, 3, 4)


# ---------------------------------------------------------------------------
# CI timeout grammar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,seconds",
    [
        ("1s", 1),
        ("59s", 59),
        ("1m", 60),
        ("30m", 1800),
        ("1h", 3600),
        ("24h", 86400),
        ("86400s", 86400),
    ],
)
def test_valid_ci_timeout(text: str, seconds: int) -> None:
    assert parse_ci_timeout(text) == seconds


@pytest.mark.parametrize(
    "text,error",
    [
        ("0s", "timeout"),
        ("0m", "timeout"),
        ("86401s", "timeout"),
        ("25h", "timeout"),
        ("1.5m", "timeout"),
        ("5", "timeout"),
        ("m", "timeout"),
        ("60s ", "timeout"),
        ("-5m", "timeout"),
        ("1d", "timeout"),
        ("2h30m", "timeout"),
        ("", "timeout"),
    ],
)
def test_invalid_ci_timeout(text: str, error: str) -> None:
    with pytest.raises(ArgumentError, match=error):
        parse_ci_timeout(text)


# ---------------------------------------------------------------------------
# Invocation forms
# ---------------------------------------------------------------------------


def test_fresh_invocation_full() -> None:
    invocation = parse_invocation(
        ["--plan", ".cg-docs/plans/p.md", "--batches", "1-2", "--base", "origin/dev",
         "--ci-timeout", "45m"]
    )
    assert invocation.form == "fresh"
    assert invocation.plan == ".cg-docs/plans/p.md"
    assert tuple((s.start, s.end) for s in invocation.segments) == ((1, 2),)
    assert invocation.base == "origin/dev"
    assert invocation.ci_timeout_seconds == 2700
    assert invocation.resume_path is None


def test_fresh_invocation_default_timeout() -> None:
    invocation = parse_invocation(
        ["--plan", "p.md", "--batches", "1", "--base", "main"]
    )
    assert invocation.ci_timeout_seconds == 1800


def test_resume_invocation() -> None:
    invocation = parse_invocation(
        ["--resume", ".cg-docs/active-state/current.json"]
    )
    assert invocation.form == "resume"
    assert invocation.resume_path == ".cg-docs/active-state/current.json"
    assert invocation.plan is None and invocation.base is None


@pytest.mark.parametrize(
    "argv,error",
    [
        (["--plan", "p.md", "--plan", "q.md", "--batches", "1", "--base", "b"], "repeated flag"),
        (["--plan", "p.md", "--batches", "1", "--batches", "1", "--base", "b"], "repeated flag"),
        (["--plan", "p.md", "--batches", "1", "--base", "b", "--base", "c"], "repeated flag"),
        (["--plan", "p.md", "--batches", "1", "--base", "b", "--ci-timeout", "1m", "--ci-timeout", "2m"], "repeated flag"),
        (["--plan", "p.md", "--batches", "1", "--base", "b", "--unknown", "x"], "unknown flag"),
        (["--plan", "p.md", "--batches", "1", "--base", "b", "-x"], "unknown flag"),
        (["--plan", "p.md", "--batches", "1"], "incomplete fresh form"),
        (["--plan", "p.md", "--base", "b"], "incomplete fresh form"),
        (["--batches", "1", "--base", "b"], "incomplete fresh form"),
        (["--plan", "p.md", "--batches", "1", "--base", "b", "--resume", "c.json"], "mutually exclusive"),
        (["--resume", "c.json", "--base", "b"], "mutually exclusive"),
        ([], "no autopilot form"),
        (["--plan"], "missing value"),
        (["--plan", "p.md", "--batches", "1", "--base"], "missing value"),
        (["positional"], "unexpected positional"),
        (["--plan", "p.md", "--batches", "1", "--base", "b", "extra"], "unexpected positional"),
    ],
)
def test_invalid_invocations(argv: list[str], error: str) -> None:
    with pytest.raises(ArgumentError, match=error):
        parse_invocation(argv)


def test_unknown_flags_never_mutate_state() -> None:
    """A rejected invocation is a pure value; nothing is written."""
    with pytest.raises(ArgumentError):
        parse_invocation(["--plan", "x", "--batches", "1", "--base", "b", "--forge"])


# ---------------------------------------------------------------------------
# Expansion into the exact single-phase work command
# ---------------------------------------------------------------------------


def test_expand_single_phase_commands() -> None:
    segments = parse_batch_segments("1-2,4")
    assert expand_single_phase_commands(segments) == (
        "/cg-work phase1 review:none",
        "/cg-work phase2 review:none",
        "/cg-work phase4 review:none",
    )


@pytest.mark.parametrize(
    "base,error",
    [
        ("origin/dev", None),
        ("main", None),
        ("dev-2026-09", None),
        ("release/v1.2.0", None),
        ("", "invalid base"),
        ("-bad", "invalid base"),
        ("a b", "invalid base"),
        ("a..b", "invalid base"),
        ("/absolute", "invalid base"),
        ("a/", "invalid base"),
        ("a:b", "invalid base"),
        ("a*b", "invalid base"),
    ],
)
def test_base_ref_grammar(base: str, error: object) -> None:
    if error is None:
        assert validate_base_ref(base) == base
    else:
        with pytest.raises(ArgumentError, match=str(error)):
            validate_base_ref(base)


# ---------------------------------------------------------------------------
# Strict control frontmatter and immutable execution digest
# ---------------------------------------------------------------------------


def _plan_source(
    phases: int = 2,
    completed: tuple[int, ...] = (),
    current: int = 1,
    report: str = ".cg-docs/work-reports/example.md",
    status: str = "active",
    extra: str = "",
) -> str:
    return plan_source_valid(
        phases=phases,
        completed=completed,
        current=current,
        report=report,
        status=status,
        extra=extra,
    )


def test_valid_autopilot_plan_parses() -> None:
    plan = validate_autopilot_plan(
        _plan_source(), Path(".cg-docs/plans/example.md")
    )
    assert plan.phases == (1, 2)
    assert plan.current_phase == 1
    assert plan.completed_phases == ()
    assert plan.execution_report == ".cg-docs/work-reports/example.md"
    assert len(plan.digest) == 64


def test_phases_count_field_must_match_real_headings() -> None:
    lying_count = _plan_source().replace("phases: 2", "phases: 9")
    with pytest.raises(PlanError, match="phase-count-mismatch"):
        validate_autopilot_plan(lying_count, Path("p.md"))


def test_fenced_fake_phase_headings_do_not_count() -> None:
    extra = "\n\n```text\n## Phase 9: Fake\n### 99. Fake step\n```\n"
    plan = validate_autopilot_plan(_plan_source(extra=extra), Path("p.md"))
    assert plan.phases == (1, 2)
    lying_count = _plan_source(extra=extra).replace("phases: 2", "phases: 9")
    with pytest.raises(PlanError, match="phase-count-mismatch"):
        validate_autopilot_plan(lying_count, Path("p.md"))


def test_duplicate_frontmatter_keys_rejected() -> None:
    source = _plan_source()
    source = source.replace("phases: 2", "phases: 2\nphases: 2")
    with pytest.raises(PlanError, match="duplicate-key"):
        validate_autopilot_plan(source, Path("p.md"))


@pytest.mark.parametrize(
    "source,error",
    [
        (_plan_source(completed=(2,), current=1), "completed-prefix"),
        (_plan_source(completed=(1, 1), current=2), "completed-prefix"),
        (_plan_source(completed=(2, 1), current=2), "completed-prefix"),
        (_plan_source(completed=(1,), current=3), "unknown-phase"),
        (_plan_source(completed=(1, 2), current=3), "unknown-phase"),
        (_plan_source(completed=(1,), current=9), "unknown-phase"),
    ],
)
def test_malformed_completion_metadata(source: str, error: str) -> None:
    with pytest.raises(PlanError, match=error):
        validate_autopilot_plan(source, Path("p.md"))


def test_completed_prefix_progress_is_valid() -> None:
    plan = validate_autopilot_plan(
        _plan_source(completed=(1,), current=2), Path("p.md")
    )
    assert plan.completed_phases == (1,)
    assert plan.current_phase == 2


def test_execution_report_path_containment() -> None:
    for bad in ("/absolute.md", "../escape.md", "a\\b.md", "[x](y)", "a b.md"):
        with pytest.raises(PlanError, match="execution-report"):
            validate_autopilot_plan(_plan_source(report=bad), Path("p.md"))


def test_yaml_anchors_and_tags_rejected() -> None:
    source = _plan_source().replace(
        "completed-phases: []", "completed-phases: &anchor [1]"
    )
    with pytest.raises(PlanError, match="control"):
        validate_autopilot_plan(source, Path("p.md"))
    source = _plan_source().replace("phases: 2", "phases: *alias")
    with pytest.raises(PlanError, match="control"):
        validate_autopilot_plan(source, Path("p.md"))


def test_execution_digest_ignores_only_progress_fields() -> None:
    base = _plan_source()
    progress_changed = _plan_source(completed=(1,), current=2)
    assert execution_digest(base) == execution_digest(progress_changed)
    assert execution_digest(base) != execution_digest(base + "\n# changed body\n")


def test_progress_delta_valid_progress_only() -> None:
    changed = progress_delta(_plan_source(), _plan_source(completed=(1,), current=2))
    assert set(changed) == {"completed-phases", "current-phase"}


def test_progress_delta_rejects_changed_body() -> None:
    with pytest.raises(PlanError, match="plan-body-changed"):
        progress_delta(_plan_source(), _plan_source() + "\nbody changed\n")


def test_progress_delta_unchanged() -> None:
    assert progress_delta(_plan_source(), _plan_source()) == ()


def test_read_plan_uses_bounded_secure_read(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    plan_dir = root / ".cg-docs/plans"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / "example.md"
    plan_file.write_text(_plan_source(), encoding="utf-8")
    plan = read_plan(root, ".cg-docs/plans/example.md")
    assert plan.phases == (1, 2)
    assert plan.digest == execution_digest(plan.source)


def test_read_plan_rejects_oversize(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    plan_file = root / "plan.md"
    plan_file.write_bytes(b"a" * (2 * 1024 * 1024 + 1))
    with pytest.raises(PlanError, match="plan-too-large"):
        read_plan(root, "plan.md")


# ---------------------------------------------------------------------------
# Batch validation against the plan
# ---------------------------------------------------------------------------


def _read(tmp_path: Path, source: str):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "plan.md").write_text(source, encoding="utf-8")
    return validate_autopilot_plan(source, root / "plan.md")


def test_validate_batches_singletons_and_ranges() -> None:
    plan = validate_autopilot_plan(_plan_source(), Path("p.md"))
    assert validate_batches(plan, parse_batch_segments("1")) == (1,)
    assert validate_batches(plan, parse_batch_segments("1-2")) == (1, 2)


def test_validate_batches_unknown_phase() -> None:
    plan = validate_autopilot_plan(_plan_source(), Path("p.md"))
    with pytest.raises(PlanError, match="unknown-phase"):
        validate_batches(plan, parse_batch_segments("2-3"))


def test_validate_batches_gap_over_incomplete_prerequisite() -> None:
    plan = validate_autopilot_plan(
        _plan_source(phases=3, completed=(1,), current=2), Path("p.md")
    )
    with pytest.raises(PlanError, match="phase-gap"):
        validate_batches(plan, parse_batch_segments("3"))
    assert validate_batches(plan, parse_batch_segments("2-3")) == (2, 3)


def test_validate_batches_starts_at_current_phase() -> None:
    plan = validate_autopilot_plan(
        _plan_source(completed=(1,), current=2), Path("p.md")
    )
    with pytest.raises(PlanError, match="phase-gap"):
        validate_batches(plan, parse_batch_segments("1"))
