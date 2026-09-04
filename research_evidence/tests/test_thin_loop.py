"""Created 2026-08-12. End-to-end Markdown evidence-loop fixture."""
from __future__ import annotations

from pathlib import Path

import yaml

from research_evidence.config import RuntimeSettings
from research_evidence.schemas import ReviewState, VerificationStatus
from research_evidence.workbench import LocalEvidenceWorkbench


def test_markdown_resource_to_verified_decision_survives_restart(tmp_path: Path) -> None:
    """Persist a verified claim/evidence decision and reload it in a new process object."""
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "findings.md").write_text(
        "# Findings\n\nWeighted poverty fell by four percentage points.\n\n"
        "The appendix describes the survey weights.",
        encoding="utf-8",
    )
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    workbench = LocalEvidenceWorkbench(settings)
    parsed = workbench.scan_markdown("findings.md")
    assert len(parsed.units) == 3
    matches = workbench.search("weighted poverty")
    assert matches and matches[0].text == "Weighted poverty fell by four percentage points."

    decision = workbench.create_and_verify(
        matches[0].source_unit_id,
        "Weighted poverty fell by four percentage points.",
        "Weighted poverty fell by four percentage points.",
    )
    assert decision.evidence.verification_status == VerificationStatus.VERIFIED_HIGH
    assert decision.evidence.review_state == ReviewState.APPROVED
    assert (settings.evidence_root / "evidence-records.yaml").exists()
    assert (settings.evidence_root / "claim-evidence-matrix.yaml").exists()
    assert list((settings.evidence_root / "runs" / "journal").glob("*-commit.yaml"))

    restarted = LocalEvidenceWorkbench(settings)
    approvals = restarted.load_approved_decisions()
    assert len(approvals) == 1
    assert approvals[0].claim.statement == decision.claim.statement
    assert approvals[0].evidence.quote == decision.evidence.quote


def test_empty_corpus_and_unknown_source_unit_are_explicit(tmp_path: Path) -> None:
    """Make empty search and fabricated source IDs explicit local failures."""
    resources = tmp_path / "resources"
    resources.mkdir()
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    workbench = LocalEvidenceWorkbench(settings)
    assert workbench.search("anything") == []
    try:
        workbench.create_and_verify("source-unit:missing", "Claim", "Quote")
    except KeyError as error:
        assert "source-unit:missing" in str(error)
    else:
        raise AssertionError("Unknown source unit was accepted")


def test_changed_original_is_stale_until_rescanned(tmp_path: Path) -> None:
    """Reject approval when the authoritative Markdown changed after indexing."""
    resources = tmp_path / "resources"
    resources.mkdir()
    source_path = resources / "findings.md"
    source_path.write_text("The original finding.", encoding="utf-8")
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    workbench = LocalEvidenceWorkbench(settings)
    unit = workbench.scan_markdown("findings.md").units[0]
    source_path.write_text("The revised finding.", encoding="utf-8")

    try:
        workbench.create_and_verify(
            unit.source_unit_id,
            "The original finding.",
            "The original finding.",
        )
    except ValueError as error:
        assert "stale" in str(error).lower()
    else:
        raise AssertionError("Changed original source was approved without rescan")


def test_rescan_invalidates_prior_approval_before_restart(tmp_path: Path) -> None:
    """Rescanning a revised source stales prior evidence and downstream approval."""
    resources = tmp_path / "resources"
    resources.mkdir()
    source_path = resources / "findings.md"
    source_path.write_text("The original finding.", encoding="utf-8")
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    workbench = LocalEvidenceWorkbench(settings)
    unit = workbench.scan_markdown("findings.md").units[0]
    decision = workbench.create_and_verify(unit.source_unit_id, unit.text, unit.text)
    source_path.write_text("The revised finding.", encoding="utf-8")

    workbench.scan_markdown("findings.md")
    evidence = yaml.safe_load(
        (settings.evidence_root / "evidence-records.yaml").read_text(encoding="utf-8")
    )["records"][0]
    assert evidence["evidence_id"] == decision.evidence.evidence_id
    assert evidence["stale"] is True
    assert LocalEvidenceWorkbench(settings).load_approved_decisions() == []


def test_existing_cr_matrix_is_preserved_in_separate_workbench_file(tmp_path: Path) -> None:
    """Never overwrite a predecessor CR matrix with the workbench schema."""
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "findings.md").write_text("The finding.", encoding="utf-8")
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    settings.evidence_root.mkdir(parents=True)
    original = {"claims": [{"id": "CR-C1", "status": "verified", "evidence": []}]}
    matrix_path = settings.evidence_root / "claim-evidence-matrix.yaml"
    matrix_path.write_text(yaml.safe_dump(original), encoding="utf-8")
    workbench = LocalEvidenceWorkbench(settings)
    unit = workbench.scan_markdown("findings.md").units[0]

    workbench.create_and_verify(unit.source_unit_id, unit.text, unit.text)

    assert yaml.safe_load(matrix_path.read_text(encoding="utf-8")) == original
    assert (settings.evidence_root / "workbench-claim-evidence-matrix.yaml").exists()
    restarted = LocalEvidenceWorkbench(settings)
    assert yaml.safe_load(matrix_path.read_text(encoding="utf-8")) == original
    assert restarted.search("CR-C1") == []
    assert all(
        decision.claim.statement != "CR-C1"
        for decision in restarted.load_approved_decisions()
    )
