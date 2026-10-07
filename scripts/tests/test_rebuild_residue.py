"""Slice 2 component proofs and explicit limits, using synthetic 9021 receipts.

These fixtures never run a full linker or use a real installation. Passing gap
tests describe current limitations, not a completed copy-to-projection migration.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import cg_generate_targets as generation
import cg_kilo_copy as copy_worker
import cg_project_manifest as manifest_module
import cg_project_projection as projection
from scripts.tests.test_project_projection import _repo_root, _write_json
from scripts.tests.test_target_ownership import _write


RETIRED = (
    ".kilo/commands/cg-autopilot.md",
    ".kilo/commands/cg-help.md",
    ".kilo/agents/cg-autopilot.md",
    ".kilo/agents/cg-bootstrap-leaf.md",
    ".kilo/agents/cg-workflow-stage.md",
    ".kilo/shared/autopilot-stage.contract.md",
    ".kilo/shared/help-catalog.json",
    ".kilo/shared/release-controller.contract.md",
    ".kilo/shared/shell-commands.json",
)
MIRROR_ROOT = ".compound-gpid/kilo-compat-skills/codex"
MIRROR_RETIRED = tuple(
    f"{MIRROR_ROOT}/{name}.md"
    for name in ("cg-autopilot", "cg-bootstrap-leaf", "cg-workflow-stage")
)
RETAINED = ".kilo/commands/cg-release.md"
OLD_BYTES = b"9021 managed controller/autopilot fixture\n"
OLD_HASH = hashlib.sha256(OLD_BYTES).hexdigest()
JOURNAL = projection.TRANSACTION_JOURNAL_PATH
SENTINELS = (
    ".compound-gpid/release/receipt.json",
    ".compound-gpid/release/publication-journal.json",
    ".kilo/shared/skill-management/release-attestations/v1.2.0.9020.json",
    ".kilo/commands/private.md",
    JOURNAL,
)
COPY_UNITS = (
    (".kilo/commands", ".kilo/commands", "cg-release.md"),
    (".kilo/agents", ".kilo/agents", "cg-review.md"),
    (".kilo/shared", ".kilo/shared", "runtime.contract.md"),
    (MIRROR_ROOT, ".agents/skills", "cg-skill-live/SKILL.md"),
)


def _snapshot(root: Path) -> dict[str, bytes]:
    """Capture all regular fixture files, for example before a blocked publish."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


def _sentinels(root: Path) -> dict[str, bytes]:
    """Seed unrelated evidence and unowned content, for example in a consumer."""
    for relative in SENTINELS:
        _write(root / relative, b'{"evidence":"9021: do not retire"}\n')
    _write_json(root / JOURNAL, {
        "schemaVersion": 1, "state": "committed", "transactionId": "a" * 32,
        "legacyEvidence": "9021 journal sentinel",
    })
    return {relative: (root / relative).read_bytes() for relative in SENTINELS}


def _legacy_entries(root: Path) -> dict[str, dict[str, str]]:
    """Seed exact native retired paths plus the retained old release command."""
    records = {}
    for relative in (*RETIRED, RETAINED):
        path = Path(relative)
        category = path.parts[1]
        kind = {"commands": "command", "agents": "agent", "shared": "shared"}[
            category
        ]
        source = {
            "commands": f".github/prompts/{path.stem}.prompt.md",
            "agents": f".github/agents/{path.stem}.agent.md",
            "shared": f".github/shared/{path.name}",
        }[category]
        _write(root / relative, OLD_BYTES)
        records[relative] = {"source": source, "kind": kind, "sha256": OLD_HASH}
    return records


@pytest.fixture
def candidate(tmp_path: Path) -> tuple[Path, projection.ProjectionPlan]:
    """Use the baseline minimal Kilo repository with a retained simple release."""
    root, _ = _repo_root(tmp_path)
    _write(root / ".github/prompts/cg-release.prompt.md",
           '---\ndescription: "Simple release"\n---\nPublish with PowerShell.\n')
    manifest = manifest_module.resolve_active_manifest(root, platforms=["kilo"])
    _write_json(root / projection.ACTIVE_MANIFEST_PATH, manifest)
    plan = projection.build_projection_plan(root, manifest)
    destinations = {entry.destination for entry in plan.entries}
    assert RETAINED in destinations
    assert not set(RETIRED) & destinations
    _sentinels(root)
    return root, plan


def _generation_plan(root: Path) -> generation.GenerationPlan:
    """Seed the 9021 generation receipt and build the new Kilo generation."""
    records = _legacy_entries(root)
    _write_json(root / ".kilo" / generation.OWNERSHIP_MANIFEST_NAME, {
        "schemaVersion": 1, "target": "kilo", "policyVersion": 1,
        "files": [dict(path=path, **record, executable=False)
                  for path, record in records.items()],
    })
    mapping = generation.load_target_mapping(root)
    mapping["targets"] = [t for t in mapping["targets"] if t["id"] == "kilo"]
    return generation.build_generation_plan(
        root, mapping, generation.scan_canonical_assets(root)
    )


def _projection_receipt(root: Path) -> None:
    """Seed a 9021 projection receipt, for example before stale cleanup."""
    _write_json(root / projection.OWNERSHIP_STATE_PATH, {
        "schemaVersion": 1,
        "entries": {
            path: dict(**record, platform="kilo", preserved=False,
                       origin="plugin-canonical",
                       provenanceIdentity="canonical/.github")
            for path, record in _legacy_entries(root).items()
        },
    })


def test_generation_deletes_unchanged_9021_residue_and_replaces_release(
    candidate: tuple[Path, projection.ProjectionPlan],
) -> None:
    """The generated receipt authorizes exact stale deletion, not evidence deletion."""
    root, _ = candidate
    plan = _generation_plan(root)
    protected = {p: (root / p).read_bytes() for p in SENTINELS}
    generation.commit_generation_plan(root, plan, ("kilo",))
    assert all(not (root / p).exists() for p in RETIRED)
    release = next(e for e in plan.entries if e.destination == RETAINED)
    assert (root / RETAINED).read_bytes() == release.content != OLD_BYTES
    receipt = json.loads(
        (root / ".kilo" / generation.OWNERSHIP_MANIFEST_NAME).read_bytes()
    )
    assert not set(RETIRED) & {e["path"] for e in receipt["files"]}
    assert all((root / p).read_bytes() == data for p, data in protected.items())


def test_generation_modified_9021_stale_file_blocks_without_losing_evidence(
    candidate: tuple[Path, projection.ProjectionPlan],
) -> None:
    """A modified retired command stops generation before any fixture mutation."""
    root, _ = candidate
    plan = _generation_plan(root)
    _write(root / RETIRED[0], b"user-modified autopilot\n")
    before = _snapshot(root)
    with pytest.raises(ValueError, match="Modified stale owned file"):
        generation.commit_generation_plan(root, plan, ("kilo",))
    assert _snapshot(root) == before


@pytest.fixture(params=COPY_UNITS, ids=("commands", "agents", "shared", "mirror"))
def copy_unit(request: pytest.FixtureRequest, tmp_path: Path) -> tuple:
    """Seed an old copy unit; the mirror case tests the worker, not shell dispatch."""
    target_relative, source_relative, live = request.param
    root = tmp_path / "consumer"
    source = tmp_path / "new-source" / source_relative
    target = root / target_relative
    retired = tuple(Path(p).name for p in (*RETIRED, *MIRROR_RETIRED)
                    if Path(p).parent.as_posix() == target_relative)
    _write(source / live, b"new retained source\n")
    for name in (*retired, live):
        _write(target / name, OLD_BYTES)
    _write_json(target / copy_worker.MARKER_NAME, {
        "schemaVersion": 1, "source": source_relative,
        "files": {name: OLD_HASH for name in (*retired, live)},
    })
    protected = _sentinels(root)
    private = _write(target / "private.md", b"unowned local content\n")
    protected[private.relative_to(root).as_posix()] = private.read_bytes()
    return root, source, target, source_relative, retired, live, protected


def test_copy_refresh_deletes_only_unchanged_9021_owned_residue(copy_unit: tuple) -> None:
    """Matching category/mirror markers permit stale cleanup and retained refresh."""
    root, source, target, source_relative, retired, live, protected = copy_unit
    copy_worker.sync_directory(source, target, source_relative)
    assert all(not (target / name).exists() for name in retired)
    assert (target / live).read_bytes() == (source / live).read_bytes() != OLD_BYTES
    marker = json.loads((target / copy_worker.MARKER_NAME).read_bytes())
    assert set(marker["files"]) == {live}
    assert all((root / p).read_bytes() == data for p, data in protected.items())


def test_copy_refresh_preserves_modified_bytes_but_drops_9021_stale_claim(
    copy_unit: tuple,
) -> None:
    """Known evidence gap: a rewritten copy marker forgets preserved stale ownership."""
    root, source, target, source_relative, retired, _, protected = copy_unit
    modified = _write(target / retired[0], b"user-modified retired asset\n")
    marker_path = target / copy_worker.MARKER_NAME
    assert retired[0] in json.loads(marker_path.read_bytes())["files"]
    copy_worker.sync_directory(source, target, source_relative)
    assert modified.read_bytes() == b"user-modified retired asset\n"
    assert retired[0] not in json.loads(marker_path.read_bytes())["files"]
    assert all((root / p).read_bytes() == data for p, data in protected.items())


def test_projection_deletes_unchanged_9021_owned_residue_and_replaces_release(
    candidate: tuple[Path, projection.ProjectionPlan],
) -> None:
    """A matching projection receipt supports native cleanup and release refresh."""
    root, plan = candidate
    _projection_receipt(root)
    protected = {p: (root / p).read_bytes() for p in SENTINELS if p != JOURNAL}
    ownership = projection.publish_projection(root, plan)
    assert all(not (root / p).exists() for p in RETIRED)
    release = next(e for e in plan.entries if e.destination == RETAINED)
    assert (root / RETAINED).read_bytes() == release.content != OLD_BYTES
    assert not set(RETIRED) & set(ownership["entries"])
    assert projection.verify_projection(root, plan) == []
    assert all((root / p).read_bytes() == data for p, data in protected.items())
    assert json.loads((root / JOURNAL).read_bytes())["state"] == "committed"


def test_projection_preserves_modified_bytes_but_drops_9021_stale_claim(
    candidate: tuple[Path, projection.ProjectionPlan],
) -> None:
    """Known evidence gap: preserved stale bytes are absent from replacement ownership."""
    root, plan = candidate
    _projection_receipt(root)
    modified = _write(root / RETIRED[0], b"user-modified autopilot\n")
    protected = {p: (root / p).read_bytes() for p in SENTINELS if p != JOURNAL}
    ownership = projection.publish_projection(root, plan)
    assert modified.read_bytes() == b"user-modified autopilot\n"
    assert RETIRED[0] not in ownership["entries"]
    assert any(RETIRED[0] in w and "user-modified" in w for w in ownership["warnings"])
    assert all((root / p).read_bytes() == data for p, data in protected.items())


def test_copy_only_9021_receipts_are_invisible_and_retained_release_blocks_projection(
    candidate: tuple[Path, projection.ProjectionPlan],
) -> None:
    """Stop at the existing release collision, with all residue and evidence intact."""
    root, plan = candidate
    _legacy_entries(root)
    for target_relative, source_relative, _ in COPY_UNITS:
        paths = [p for p in (*RETIRED, RETAINED, *MIRROR_RETIRED)
                 if Path(p).parent.as_posix() == target_relative]
        for path in paths:
            _write(root / path, OLD_BYTES)
        _write_json(root / target_relative / copy_worker.MARKER_NAME, {
            "schemaVersion": 1, "source": source_relative,
            "files": {Path(p).name: OLD_HASH for p in paths},
        })
    _write(root / RETIRED[2], b"user-modified retired agent\n")
    before = _snapshot(root)
    assert projection._previous_ownership(root) == {}
    with pytest.raises(projection.ProjectionError, match=f"collision: {RETAINED}"):
        projection.publish_projection(root, plan)
    assert _snapshot(root) == before


def test_projection_overwrites_incompatible_non_prepared_journal_evidence(
    candidate: tuple[Path, projection.ProjectionPlan],
) -> None:
    """Known journal gap, exercised only on an isolated fixture with no stale files."""
    root, plan = candidate
    journal = {"schemaVersion": 2, "state": "legacy-unknown",
               "transactionId": "a" * 32, "legacyEvidence": "must be reviewed"}
    _write_json(root / JOURNAL, journal)
    before = (root / JOURNAL).read_bytes()
    protected = {p: (root / p).read_bytes() for p in SENTINELS if p != JOURNAL}
    assert manifest_module.validate_transaction_journal(journal)
    projection.recover_projection(root)
    assert (root / JOURNAL).read_bytes() == before
    projection.publish_projection(root, plan)
    assert (root / JOURNAL).read_bytes() != before
    assert "legacyEvidence" not in json.loads((root / JOURNAL).read_bytes())
    assert all((root / p).read_bytes() == data for p, data in protected.items())
