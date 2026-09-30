"""Digest-bound lifecycle transaction and recovery tests."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from skill_management import planning


def _plan(project: Path, *, before: bytes = b"old", after: bytes = b"new") -> planning.LifecyclePlan:
    return planning.LifecyclePlan(
        operation="activate",
        role="consumer",
        arguments={"capability": "project-skill-demo", "token": "secret-value"},
        bindings=planning.PlanBindings.fixture(),
        actions=(
            planning.PlannedAction(
                "update-config",
                "compound-gpid.local.md",
                "Select the explicit capability.",
                planning.ExpectedMutation("compound-gpid.local.md", before, after, "config"),
            ),
        ),
    )


def test_plan_record_is_deterministic_redacted_and_has_no_live_write(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "compound-gpid.local.md").write_bytes(b"old")
    plan = _plan(project)

    first = planning.store_plan(project, plan)
    second = planning.store_plan(project, plan)

    assert first.digest == second.digest
    assert (project / "compound-gpid.local.md").read_bytes() == b"old"
    stored = (project / planning.PLAN_ROOT / f"{first.digest}.json").read_text("utf-8")
    assert "secret-value" not in stored
    assert "<redacted>" in stored
    assert "bmV3" not in stored


def test_apply_revalidates_digest_writes_expected_bytes_and_rejects_replay(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "compound-gpid.local.md"
    target.write_bytes(b"old")
    plan = _plan(project)
    record = planning.store_plan(project, plan)

    result = planning.apply_plan(project, plan, record.digest)

    assert result.state == "committed"
    assert target.read_bytes() == b"new"
    with pytest.raises(planning.PlanReplayError):
        planning.apply_plan(project, plan, record.digest)


def test_changed_arguments_or_expected_bytes_are_stale(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "compound-gpid.local.md"
    target.write_bytes(b"old")
    original = _plan(project)
    record = planning.store_plan(project, original)
    changed = planning.LifecyclePlan(
        operation=original.operation,
        role=original.role,
        arguments={"capability": "project-skill-other"},
        bindings=original.bindings,
        actions=original.actions,
    )

    with pytest.raises(planning.StalePlanError):
        planning.apply_plan(project, changed, record.digest)

    target.write_bytes(b"concurrent")
    with pytest.raises(planning.ConcurrentMutationError):
        planning.apply_plan(project, original, record.digest)
    assert target.read_bytes() == b"concurrent"


def test_wrong_role_sensitive_approval_and_digest_fail_closed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "compound-gpid.local.md").write_bytes(b"old")
    plan = _plan(project)
    record = planning.store_plan(project, plan)

    with pytest.raises(planning.PlanRoleError):
        planning.apply_plan(project, replace(plan, role="maintainer"), record.digest)
    with pytest.raises(planning.StalePlanError):
        planning.apply_plan(
            project,
            replace(
                plan,
                arguments={
                    "capability": "project-skill-demo",
                    "token": "different-approval",
                },
            ),
            record.digest,
        )
    with pytest.raises(planning.StalePlanError):
        planning.apply_plan(project, plan, "f" * 64)


def test_noop_transaction_commits_without_live_mutation(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    plan = planning.LifecyclePlan(
        "activate",
        "consumer",
        {"capability": "project-skill-demo", "noop": True},
        planning.PlanBindings.fixture(),
        (),
    )
    record = planning.store_plan(project, plan)

    result = planning.apply_plan(project, plan, record.digest)

    assert result.state == "committed"
    assert not (project / "compound-gpid.local.md").exists()


def test_lifecycle_plan_rejects_portable_unicode_mutation_aliases() -> None:
    actions = tuple(
        planning.PlannedAction(
            "apply-migration",
            path,
            "Apply a reviewed reference migration.",
            planning.ExpectedMutation(path, b"old", b"new", "source"),
        )
        for path in ("docs/Caf\u00e9.md", "DOCS/Cafe\u0301.md")
    )
    plan = planning.LifecyclePlan(
        "remove",
        "consumer",
        {"skillId": "demo-skill"},
        planning.PlanBindings.fixture(),
        actions,
    )

    with pytest.raises(planning.PlanningError, match="more than once"):
        planning._ordered_mutations(plan)  # pylint: disable=protected-access


def test_crash_before_commit_point_discards_staging_on_recovery(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "compound-gpid.local.md"
    target.write_bytes(b"old")
    plan = _plan(project)
    record = planning.store_plan(project, plan)

    def crash(boundary: str) -> None:
        if boundary == "after-prepared":
            raise RuntimeError("before commit point")

    with pytest.raises(RuntimeError, match="before commit"):
        planning.apply_plan(project, plan, record.digest, fault_hook=crash)
    assert target.read_bytes() == b"old"

    recovered = planning.recover_transactions(project)

    assert recovered[0].state == "aborted"
    assert not list((project / planning.TRANSACTION_ROOT).glob("*.staging"))
    assert planning.apply_plan(project, plan, record.digest).state == "committed"


def test_staged_validation_failure_has_no_journal_or_live_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "compound-gpid.local.md"
    target.write_bytes(b"old")
    plan = _plan(project)
    record = planning.store_plan(project, plan)
    original = planning.secure_fs.secure_read_bytes

    def corrupt_stage(root, relative, **kwargs):
        content = original(root, relative, **kwargs)
        return b"corrupt" if ".staging" in str(relative) else content

    monkeypatch.setattr(planning.secure_fs, "secure_read_bytes", corrupt_stage)

    with pytest.raises(planning.JournalValidationError, match="Staged"):
        planning.apply_plan(project, plan, record.digest)

    assert target.read_bytes() == b"old"
    assert not list((project / planning.TRANSACTION_ROOT).glob("*.json"))


def test_forward_recovery_converges_after_crash_at_publish_boundary(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "compound-gpid.local.md"
    target.write_bytes(b"old")
    plan = _plan(project)
    record = planning.store_plan(project, plan)

    def crash(boundary: str) -> None:
        if boundary == "after-action:0":
            raise RuntimeError("simulated process crash")

    with pytest.raises(RuntimeError, match="simulated"):
        planning.apply_plan(project, plan, record.digest, fault_hook=crash)

    assert target.read_bytes() == b"new"
    recovered = planning.recover_transactions(project)
    assert recovered[0].state == "committed"
    assert target.read_bytes() == b"new"


def test_recovery_preserves_concurrent_non_lifecycle_bytes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "compound-gpid.local.md"
    target.write_bytes(b"old")
    plan = _plan(project)
    record = planning.store_plan(project, plan)

    def crash(boundary: str) -> None:
        if boundary == "after-publishing":
            raise RuntimeError("stop before first action")

    with pytest.raises(RuntimeError):
        planning.apply_plan(project, plan, record.digest, fault_hook=crash)
    target.write_bytes(b"outside writer")

    with pytest.raises(planning.ConcurrentMutationError):
        planning.recover_transactions(project)
    assert target.read_bytes() == b"outside writer"
    journals = list((project / planning.TRANSACTION_ROOT).glob("*.json"))
    assert json.loads(journals[0].read_text("utf-8"))["state"] == "blocked"


def test_recovery_blocks_if_an_applied_path_changes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    first = project / "compound-gpid.local.md"
    second = project / ".compound-gpid/active-manifest.json"
    first.write_bytes(b"old-one")
    second.parent.mkdir(parents=True)
    second.write_bytes(b"old-two")
    plan = planning.LifecyclePlan(
        "activate",
        "consumer",
        {"capability": "project-skill-demo"},
        planning.PlanBindings.fixture(),
        (
            planning.PlannedAction(
                "update-config",
                "compound-gpid.local.md",
                "Update config.",
                planning.ExpectedMutation(
                    "compound-gpid.local.md", b"old-one", b"new-one", "config"
                ),
            ),
            planning.PlannedAction(
                "update-manifest",
                ".compound-gpid/active-manifest.json",
                "Update manifest.",
                planning.ExpectedMutation(
                    ".compound-gpid/active-manifest.json",
                    b"old-two",
                    b"new-two",
                    "manifest",
                ),
            ),
        ),
    )
    record = planning.store_plan(project, plan)

    def crash(boundary: str) -> None:
        if boundary == "after-status:0":
            raise RuntimeError("first action durable")

    with pytest.raises(RuntimeError):
        planning.apply_plan(project, plan, record.digest, fault_hook=crash)
    first.write_bytes(b"outside")

    with pytest.raises(planning.ConcurrentMutationError, match="Previously applied"):
        planning.recover_transactions(project)
    assert first.read_bytes() == b"outside"
    assert second.read_bytes() == b"old-two"


def test_invalid_journal_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    journal = project / planning.TRANSACTION_ROOT / ("a" * 32 + ".json")
    journal.parent.mkdir(parents=True)
    journal.write_text('{"state":"publishing"}\n', encoding="utf-8")

    with pytest.raises(planning.JournalValidationError):
        planning.recover_transactions(project)
