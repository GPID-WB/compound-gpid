"""Tests for the canonical c-research output layout contract.

Run from the repository root with:
    python3 -m pytest scripts/tests/test_research_layout.py -q
"""
from __future__ import annotations

from pathlib import Path

import pytest

import cg_migrate_research_layout as migration
from research_layout import (
    COMPOUND_DOC_DIRECTORIES,
    LEGACY_RESEARCH_ROOT,
    RESEARCH_OUTPUT_DIRECTORIES,
    RESEARCH_ROOT,
    destination_for_legacy,
    is_research_output_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("legacy", "expected"),
    [
        ("evidence/provenance-ledger.yaml", "c-research/evidence/provenance-ledger.yaml"),
        ("manuscript/draft.md", "c-research/manuscripts/draft.md"),
        ("normative-decisions/study.md", "c-research/normative-decisions/study.md"),
        ("scoping/study.md", "c-research/scoping/study.md"),
    ],
)
def test_legacy_path_maps_to_artifact_type_destination(legacy: str, expected: str) -> None:
    """Map each current research directory to its canonical destination."""
    assert destination_for_legacy(Path(legacy)) == Path(expected)


def test_research_output_directories_are_complete() -> None:
    """Keep the path contract aligned with all CR output-producing skills."""
    assert RESEARCH_ROOT == Path("c-research")
    assert RESEARCH_OUTPUT_DIRECTORIES == (
        "evidence",
        "manuscripts",
        "normative-decisions",
        "scoping",
        "derivations",
        "specifications",
        "results",
        "replication",
        "eda",
        "measurement",
        "vintages",
    )
    assert LEGACY_RESEARCH_ROOT == Path(".cg-docs/research")


def test_process_directories_remain_outside_research_output_contract() -> None:
    """Keep Compound GPID process records separate from study outputs."""
    assert "brainstorms" in COMPOUND_DOC_DIRECTORIES
    assert "plans" in COMPOUND_DOC_DIRECTORIES
    assert "reviews" in COMPOUND_DOC_DIRECTORIES
    assert "solutions" in COMPOUND_DOC_DIRECTORIES
    assert "evidence-fixtures" in COMPOUND_DOC_DIRECTORIES
    assert "inbox" in COMPOUND_DOC_DIRECTORIES
    assert "views" in COMPOUND_DOC_DIRECTORIES
    assert not is_research_output_path(Path(".cg-docs/evidence-fixtures/fixture-plan.md"))
    assert not is_research_output_path(Path(".cg-docs/inbox/idea.md"))
    assert not is_research_output_path(Path("data/panel.parquet"))


def test_research_readme_states_output_only_boundary() -> None:
    """Document the output-only and separate-data rules for human users."""
    readme = (REPO_ROOT / "c-research" / "README.md").read_text(encoding="utf-8").lower()
    assert "research outputs" in readme
    assert "data/" in readme
    assert "compound gpids" in readme or "compound gpid" in readme
    assert "human researchers" in readme
    assert "cr workflow" in readme


def test_data_is_never_a_research_output_directory() -> None:
    """Reject data paths even when they share a project-level root."""
    assert not is_research_output_path(Path("data"))
    assert not is_research_output_path(Path("data/raw/paper.pdf"))
    assert is_research_output_path(Path("c-research/evidence/claims.yaml"))


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_migration_plan_maps_all_legacy_files_deterministically(tmp_path: Path) -> None:
    """Plan moves in sorted order and applies the manuscript rename."""
    _write(tmp_path / ".cg-docs/research/manuscript/draft.md", "draft\n")
    _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "sources: []\n")

    moves = migration.build_migration_plan(
        tmp_path,
        allowed_paths=(
            Path(".cg-docs/research/evidence/ledger.yaml"),
            Path(".cg-docs/research/manuscript/draft.md"),
        ),
    )

    assert [move.source.relative_to(tmp_path).as_posix() for move in moves] == [
        ".cg-docs/research/evidence/ledger.yaml",
        ".cg-docs/research/manuscript/draft.md",
    ]
    assert [move.destination.relative_to(tmp_path).as_posix() for move in moves] == [
        "c-research/evidence/ledger.yaml",
        "c-research/manuscripts/draft.md",
    ]


def test_migration_reference_scan_distinguishes_historical_and_operational(tmp_path: Path) -> None:
    """Classify old paths in historical records separately from live sources."""
    historical = _write(
        tmp_path / ".cg-docs/plans/old-plan.md",
        "Historical path: .cg-docs/research/evidence/ledger.yaml\n",
    )
    operational = _write(
        tmp_path / ".github/prompts/cr-work.prompt.md",
        "Write to .cg-docs/research/evidence/ledger.yaml\n",
    )

    references = migration.find_old_path_references(tmp_path)

    by_path = {reference.path: reference.classification for reference in references}
    assert by_path[historical] == "historical"
    assert by_path[operational] == "operational"


def test_migration_reference_scan_excludes_generated_brain_and_audit_outputs(tmp_path: Path) -> None:
    """Do not report generated indexes or audit snapshots as live consumers."""
    for relative in (
        ".cg-docs/BRAIN.md",
        ".cg-docs/BRAIN-01.md",
        ".cg-docs/BRAIN-log.md",
        ".cg-docs/brain-index.json",
        ".cg-docs/cost/context-audit.md",
        ".cg-docs/token/token-audit.json",
        ".cg-docs/views/plans/plan.html",
    ):
        _write(tmp_path / relative, ".cg-docs/research/evidence/ledger.yaml\n")

    assert migration.find_old_path_references(tmp_path) == []


def test_migration_tool_paths_are_explicitly_allowlisted(tmp_path: Path) -> None:
    """Keep legacy constants in migration code without treating them as consumers."""
    for relative in migration.MIGRATION_TOOL_PATHS:
        _write(tmp_path / relative, ".cg-docs/research/evidence/ledger.yaml\n")

    references = migration.find_old_path_references(tmp_path)

    assert {reference.classification for reference in references} == {"migration-tool"}


def test_migration_rejects_unknown_legacy_directory(tmp_path: Path) -> None:
    """Fail closed instead of moving an unclassified research directory."""
    _write(tmp_path / ".cg-docs/research/unknown/output.md", "content\n")

    with pytest.raises(migration.MigrationError, match="unknown"):
        migration.build_migration_plan(tmp_path)


def test_migration_rejects_different_destination_bytes(tmp_path: Path) -> None:
    """Never overwrite a destination that contains different content."""
    _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    _write(tmp_path / "c-research/evidence/ledger.yaml", "new\n")

    with pytest.raises(migration.MigrationError, match="conflict"):
        migration.build_migration_plan(
            tmp_path,
            allowed_paths=(Path(".cg-docs/research/evidence/ledger.yaml"),),
        )


def test_migration_rejects_symlinked_legacy_ancestor(
    tmp_path: Path,
    require_symlink_support: None,
) -> None:
    """Do not traverse an external tree through a .cg-docs symlink."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "research/evidence").mkdir(parents=True)
    _write(outside / "research/evidence/secret.yaml", "secret\n")
    (tmp_path / ".cg-docs").symlink_to(outside, target_is_directory=True)

    with pytest.raises(migration.MigrationError, match="symbolic link"):
        migration.build_migration_plan(tmp_path)


def test_migration_rejects_dangling_destination_symlink(
    tmp_path: Path,
    require_symlink_support: None,
) -> None:
    """Do not follow a broken destination link during conflict checks."""
    _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    destination = tmp_path / "c-research/evidence/ledger.yaml"
    destination.parent.mkdir(parents=True)
    destination.symlink_to(tmp_path / "outside-victim.yaml")

    with pytest.raises(migration.MigrationError, match="conflict"):
        migration.build_migration_plan(
            tmp_path,
            allowed_paths=(Path(".cg-docs/research/evidence/ledger.yaml"),),
        )


def test_apply_blocks_operational_legacy_references_before_mutation(tmp_path: Path) -> None:
    """Refuse to remove sources while a live file still uses the old path."""
    source = _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    _write(
        tmp_path / "workflow.md",
        "Read .cg-docs/research/evidence/ledger.yaml\n",
    )

    with pytest.raises(migration.MigrationError, match="Operational legacy references"):
        migration.apply_migration(tmp_path)

    assert source.exists()
    assert not (tmp_path / "c-research/evidence/ledger.yaml").exists()


def test_reference_scan_detects_windows_style_legacy_paths(tmp_path: Path) -> None:
    """Detect old paths written with Windows separators on any host."""
    reference = _write(
        tmp_path / "workflow.md",
        r"Read .cg-docs\research\evidence\ledger.yaml\n",
    )

    references = migration.find_old_path_references(tmp_path)

    assert references == [migration.PathReference(reference, "operational")]


def test_migration_rejects_input_like_legacy_files(tmp_path: Path) -> None:
    """Keep source inputs out of the output workspace unless approved."""
    _write(tmp_path / ".cg-docs/research/evidence/source.pdf", "source\n")

    with pytest.raises(migration.MigrationError, match="explicit output approval"):
        migration.build_migration_plan(tmp_path)


def test_migration_rejects_unknown_legacy_file_types(tmp_path: Path) -> None:
    """Require classification for an otherwise unrecognized legacy file."""
    _write(tmp_path / ".cg-docs/research/evidence/source.txt", "source\n")

    with pytest.raises(migration.MigrationError, match="explicit output approval"):
        migration.build_migration_plan(tmp_path)


def test_migration_allows_explicit_input_like_output_approval(tmp_path: Path) -> None:
    """Permit a human-classified non-document research output explicitly."""
    source = _write(tmp_path / ".cg-docs/research/results/table.csv", "value\n1\n")

    moves = migration.build_migration_plan(
        tmp_path,
        allowed_paths=(Path(".cg-docs/research/results/table.csv"),),
    )

    assert moves[0].source == source
    assert moves[0].destination == tmp_path / "c-research/results/table.csv"


def test_migration_rejects_non_directory_destination_ancestor(tmp_path: Path) -> None:
    """Fail clearly when a destination parent is occupied by a regular file."""
    _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    _write(tmp_path / "c-research", "not a directory\n")

    with pytest.raises(migration.MigrationError, match="not a directory"):
        migration.build_migration_plan(
            tmp_path,
            allowed_paths=(Path(".cg-docs/research/evidence/ledger.yaml"),),
        )


def test_migration_preserves_source_when_it_changes_before_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not delete a source that changed after the migration plan."""
    source = _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    original_delete = migration.secure_delete_verified

    def mutate_then_delete(root: Path, relative: str, digest: str) -> None:
        source.write_text("new\n", encoding="utf-8")
        original_delete(root, relative, digest)

    monkeypatch.setattr(migration, "secure_delete_verified", mutate_then_delete)

    with pytest.raises(migration.MigrationError, match="changed"):
        migration.apply_migration(
            tmp_path,
            allowed_paths=(Path(".cg-docs/research/evidence/ledger.yaml"),),
        )

    assert source.read_text(encoding="utf-8") == "new\n"
    assert (tmp_path / "c-research/evidence/ledger.yaml").read_text(encoding="utf-8") == "old\n"


def test_migration_rejects_source_changed_after_planning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not publish bytes that differ from the authorized migration plan."""
    source = _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    original_plan = migration.build_migration_plan

    def plan_then_mutate(root: Path, **kwargs: object) -> list[migration.MigrationMove]:
        moves = original_plan(root, **kwargs)
        source.write_text("new\n", encoding="utf-8")
        return moves

    monkeypatch.setattr(migration, "build_migration_plan", plan_then_mutate)

    with pytest.raises(migration.MigrationError, match="changed before migration"):
        migration.apply_migration(
            tmp_path,
            allowed_paths=(Path(".cg-docs/research/evidence/ledger.yaml"),),
        )

    assert source.read_text(encoding="utf-8") == "new\n"
    assert not (tmp_path / "c-research/evidence/ledger.yaml").exists()


def test_migration_restores_source_when_destination_changes_after_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restore the source without clobbering a concurrent destination winner."""
    source = _write(tmp_path / ".cg-docs/research/evidence/ledger.yaml", "old\n")
    destination = tmp_path / "c-research/evidence/ledger.yaml"
    original_verify = migration._verify_destination
    calls = 0

    def alter_after_publish(root: Path, move: migration.MigrationMove) -> None:
        nonlocal calls
        calls += 1
        original_verify(root, move)
        if calls == 2:
            destination.write_text("concurrent winner\n", encoding="utf-8")
            original_verify(root, move)

    monkeypatch.setattr(migration, "_verify_destination", alter_after_publish)

    with pytest.raises(migration.MigrationError, match="verification failed"):
        migration.apply_migration(
            tmp_path,
            allowed_paths=(Path(".cg-docs/research/evidence/ledger.yaml"),),
        )

    assert source.read_text(encoding="utf-8") == "old\n"
    assert destination.read_text(encoding="utf-8") == "concurrent winner\n"
def test_migration_is_idempotent_after_apply(tmp_path: Path) -> None:
    """A second migration run reports no moves after successful application."""
    _write(tmp_path / ".cg-docs/research/scoping/study.md", "scope\n")

    allowed = (Path(".cg-docs/research/scoping/study.md"),)
    first = migration.apply_migration(tmp_path, allowed_paths=allowed)
    second = migration.apply_migration(tmp_path)

    assert first.moved == 1
    assert second.moved == 0
    assert (tmp_path / "c-research/scoping/study.md").read_text(encoding="utf-8") == "scope\n"


def test_migration_creates_complete_research_scaffold(tmp_path: Path) -> None:
    """Create every canonical artifact directory after a sparse migration."""
    _write(tmp_path / ".cg-docs/research/scoping/study.md", "scope\n")

    migration.apply_migration(
        tmp_path,
        allowed_paths=(Path(".cg-docs/research/scoping/study.md"),),
    )

    assert all(
        (tmp_path / "c-research" / directory).is_dir()
        for directory in RESEARCH_OUTPUT_DIRECTORIES
    )


def test_repository_boundary_state_is_preserved() -> None:
    """Keep shared Compound GPID directories outside the research workspace."""
    assert (REPO_ROOT / "c-research").is_dir()
    assert not (REPO_ROOT / ".cg-docs/research").exists()
    for relative in (".cg-docs/evidence-fixtures", ".cg-docs/inbox", ".cg-docs/views"):
        assert (REPO_ROOT / relative).is_dir()


def test_repository_has_no_unallowlisted_legacy_research_references() -> None:
    """Keep operational sources on c-research after the migration."""
    references = migration.find_old_path_references(REPO_ROOT)

    assert not [reference for reference in references if reference.classification == "operational"]
