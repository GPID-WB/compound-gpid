"""Evidence acquisition, reference verification and frozen receipts (Step 5).

Run: python -B -m pytest scripts/tests/test_autopilot_evidence.py -q
"""

import hashlib
import json
from pathlib import Path

import pytest

from autopilot.contracts import EvidenceError
from autopilot.packets import ArtifactReference
from autopilot.evidence import (
    AGGREGATE_LIMIT,
    PLAN_REPORT_LIMIT,
    RECEIPT_LIMIT,
    AcquisitionBudget,
    acquire_document,
    allocate_report_path,
    freeze_test_result,
    read_test_result,
    verify_artifact_reference,
    verify_frozen_test_result,
    verify_plan_linked_report,
    verify_review_report,
)
from autopilot.manifest import (
    MANIFEST_INPUT_LIMIT,
    capture_change_manifest,
    resolve_exclusions,
    verify_change_manifest,
)
from autopilot.plan import validate_autopilot_plan
from tests.autopilot_plan_fixture import plan_source_valid


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    return root


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
# Bounded secure acquisition
# ---------------------------------------------------------------------------


def test_acquire_document_exact_limit_and_identity(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    budget = AcquisitionBudget()
    content = b"x" * PLAN_REPORT_LIMIT
    (root / "big.md").write_bytes(content)
    document = acquire_document(root, "big.md", kind="plan", budget=budget)
    assert document.byte_count == PLAN_REPORT_LIMIT
    assert document.sha256 == _sha(content)
    assert document.content == content


def test_acquire_document_one_byte_over_limit(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    budget = AcquisitionBudget()
    (root / "big.md").write_bytes(b"x" * (PLAN_REPORT_LIMIT + 1))
    with pytest.raises(EvidenceError, match="evidence-too-large"):
        acquire_document(root, "big.md", kind="plan", budget=budget)


def test_acquire_document_kind_limits(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    budget = AcquisitionBudget()
    (root / "r.json").write_bytes(b"x" * (RECEIPT_LIMIT + 1))
    with pytest.raises(EvidenceError, match="evidence-too-large"):
        acquire_document(root, "r.json", kind="receipt", budget=budget)
    (root / "m.bin").write_bytes(b"x" * (MANIFEST_INPUT_LIMIT + 1))
    with pytest.raises(EvidenceError, match="evidence-too-large"):
        acquire_document(root, "m.bin", kind="manifest-input", budget=budget)


def test_aggregate_limit_exhaustion(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    budget = AcquisitionBudget(limit=10)
    (root / "a.bin").write_bytes(b"123456")
    acquire_document(root, "a.bin", kind="manifest-input", budget=budget)
    (root / "b.bin").write_bytes(b"123456")
    with pytest.raises(EvidenceError, match="aggregate"):
        acquire_document(root, "b.bin", kind="manifest-input", budget=budget)


def test_hard_linked_evidence_rejected(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "a.md").write_text("shared", encoding="utf-8")
    try:
        (root / "b.md").hardlink_to(root / "a.md")
    except OSError as error:
        pytest.skip(f"hardlinks unavailable: {error}")
    budget = AcquisitionBudget()
    with pytest.raises(EvidenceError, match="hard link"):
        acquire_document(root, "b.md", kind="report", budget=budget)


def test_out_of_root_and_link_paths_rejected(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    budget = AcquisitionBudget()
    with pytest.raises(EvidenceError, match="contain"):
        acquire_document(root, "../escape.md", kind="plan", budget=budget)
    with pytest.raises(EvidenceError, match="contain"):
        acquire_document(root, "a/b/../../x.md", kind="plan", budget=budget)


# ---------------------------------------------------------------------------
# Reference verification
# ---------------------------------------------------------------------------


def _reference(path: str, content: bytes, operation_id: str = "op-1") -> ArtifactReference:
    return ArtifactReference(
        kind="report",
        path=path,
        byte_count=len(content),
        sha256=_sha(content),
        operation_id=operation_id,
        content_identity=None,
    )


def test_verify_artifact_reference_matches(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    content = b"report body"
    (root / "r.md").write_bytes(content)
    budget = AcquisitionBudget()
    document = verify_artifact_reference(
        root, _reference("r.md", content), budget=budget
    )
    assert document.sha256 == _sha(content)


def test_verify_artifact_reference_detects_replacement(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    content = b"original"
    (root / "r.md").write_bytes(content)
    reference = _reference("r.md", content)
    budget = AcquisitionBudget()
    (root / "r.md").write_bytes(b"replaced after capture")
    with pytest.raises(EvidenceError, match="content-changed"):
        verify_artifact_reference(root, reference, budget=budget)


def test_verify_artifact_reference_detects_missing_and_byte_count(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    content = b"body"
    (root / "r.md").write_bytes(content)
    budget = AcquisitionBudget()
    reference = ArtifactReference("report", "missing.md", 4, _sha(content), "op-1", None)
    with pytest.raises(EvidenceError, match="missing"):
        verify_artifact_reference(root, reference, budget=budget)
    wrong = ArtifactReference("report", "r.md", 99, _sha(content), "op-1", None)
    with pytest.raises(EvidenceError, match="byte-count"):
        verify_artifact_reference(root, wrong, budget=budget)


def test_verify_artifact_reference_rejects_self_reference(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    content = b"self"
    (root / "self.md").write_bytes(content)
    budget = AcquisitionBudget()
    with pytest.raises(EvidenceError, match="self-reference"):
        verify_artifact_reference(
            root, _reference("self.md", content), budget=budget,
            referencing_path="self.md",
        )


def test_plan_linked_report_not_newest_file(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    linked = ".cg-docs/work-reports/linked.md"
    newest = ".cg-docs/work-reports/zzz-newest.md"
    Path(root / linked).parent.mkdir(parents=True, exist_ok=True)
    Path(root / newest).parent.mkdir(parents=True, exist_ok=True)
    linked_bytes = b"the linked report"
    Path(root / linked).write_bytes(linked_bytes)
    Path(root / newest).write_bytes(b"the newer unrelated report")
    plan = validate_autopilot_plan(
        plan_source_valid(report=linked), root / "plan.md"
    )
    budget = AcquisitionBudget()
    document = verify_plan_linked_report(root, plan, budget=budget)
    assert document.path == linked
    assert document.sha256 == _sha(linked_bytes)


def test_plan_linked_report_missing_or_renamed(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    plan = validate_autopilot_plan(
        plan_source_valid(report=".cg-docs/work-reports/gone.md"), root / "plan.md"
    )
    with pytest.raises(EvidenceError, match="missing-work-report"):
        verify_plan_linked_report(root, plan, budget=AcquisitionBudget())


# ---------------------------------------------------------------------------
# Collision-safe review report identities
# ---------------------------------------------------------------------------


def test_allocate_report_path_first_and_collision(tmp_path: Path) -> None:
    reports = tmp_path / "reviews"
    reports.mkdir()
    first = allocate_report_path(reports, "2026-09-15-plan", "review")
    assert first.path.endswith("-review.md")
    assert first.parent_report == "2026-09-15-plan"
    assert first.report_type == "review"
    assert not (reports / first.path).exists()
    verify = allocate_report_path(reports, "2026-09-15-plan", "verify-review")
    assert verify.path.endswith("-verify-review.md")
    (reports / first.path).write_text("taken", encoding="utf-8")
    second = allocate_report_path(reports, "2026-09-15-plan", "review")
    assert second.path != first.path
    assert second.path.endswith("-review.md")


def test_allocate_report_path_rejects_bad_identity(tmp_path: Path) -> None:
    reports = tmp_path / "reviews"
    reports.mkdir()
    with pytest.raises(EvidenceError, match="parent-identity"):
        allocate_report_path(reports, "../escape", "review")
    with pytest.raises(EvidenceError, match="report-type"):
        allocate_report_path(reports, "parent", "invented")


def test_verify_review_report_identity(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "r.md").write_text(
        "---\nreport-type: review\nparent-report: 2026-09-15-plan\n---\n# Review\n",
        encoding="utf-8",
    )
    budget = AcquisitionBudget()
    document = verify_review_report(
        root, "r.md", expected_type="review",
        expected_parent="2026-09-15-plan", budget=budget,
    )
    assert document.sha256


def test_verify_review_report_wrong_parent_or_type(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "r.md").write_text(
        "---\nreport-type: review\nparent-report: other-plan\n---\n# Review\n",
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="wrong-parent-report"):
        verify_review_report(
            root, "r.md", expected_type="review",
            expected_parent="2026-09-15-plan", budget=AcquisitionBudget(),
        )
    (root / "r2.md").write_text(
        "---\nreport-type: verify-review\nparent-report: 2026-09-15-plan\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="wrong-report-type"):
        verify_review_report(
            root, "r2.md", expected_type="review",
            expected_parent="2026-09-15-plan", budget=AcquisitionBudget(),
        )
    (root / "r3.md").write_text("# No identity frontmatter\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="report-type"):
        verify_review_report(
            root, "r3.md", expected_type="review",
            expected_parent="2026-09-15-plan", budget=AcquisitionBudget(),
        )


def test_duplicate_frontmatter_field_is_rejected(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "r.md").write_text(
        "---\nreport-type: review\nreport-type: verify-review\n"
        "parent-report: 2026-09-15-plan\n---\n# Review\n",
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="duplicate-report-type"):
        verify_review_report(
            root, "r.md", expected_type="review",
            expected_parent="2026-09-15-plan", budget=AcquisitionBudget(),
        )
    (root / "p.md").write_text(
        "---\nreport-type: review\nparent-report: 2026-09-15-plan\n"
        "parent-report: 2026-09-16-plan\n---\n# Review\n",
        encoding="utf-8",
    )
    with pytest.raises(EvidenceError, match="duplicate-parent-report"):
        verify_review_report(
            root, "p.md", expected_type="review",
            expected_parent="2026-09-15-plan", budget=AcquisitionBudget(),
        )


# ---------------------------------------------------------------------------
# Test-result freshness and frozen receipts
# ---------------------------------------------------------------------------


def _last_run() -> dict:
    return {
        "totalCount": 2,
        "passedCount": 2,
        "failedCount": 0,
        "skippedCount": 0,
        "filteredFiles": None,
        "ranAt": "2026-09-15T00:01:00Z",
    }


def test_read_test_result_reuses_summary_narrowly(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "last-run.json").write_text(json.dumps(_last_run()), encoding="utf-8")
    result = read_test_result(root, "last-run.json", budget=AcquisitionBudget())
    assert result["summary"]["passed"] == 2
    assert result["sha256"] == _sha(
        json.dumps(_last_run()).encode("utf-8")
    )


def test_read_test_result_missing_and_stale_note(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with pytest.raises(EvidenceError, match="missing"):
        read_test_result(root, "last-run.json", budget=AcquisitionBudget())
    (root / "bad.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(EvidenceError, match="json"):
        read_test_result(root, "bad.json", budget=AcquisitionBudget())


def test_freeze_and_verify_test_receipt(tmp_path: Path) -> None:
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    content = json.dumps(_last_run()).encode("utf-8")
    digest = freeze_test_result(receipts, "op-1", content)
    assert digest == _sha(content)
    frozen = verify_frozen_test_result(receipts, "op-1", digest)
    assert frozen == content
    (receipts / "op-1.test-result.json").write_bytes(b"tampered")
    with pytest.raises(EvidenceError, match="receipt-changed"):
        verify_frozen_test_result(receipts, "op-1", digest)


def test_freeze_test_receipt_conflict_and_replay(tmp_path: Path) -> None:
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    content = b"first run bytes"
    freeze_test_result(receipts, "op-1", content)
    assert freeze_test_result(receipts, "op-1", content) == _sha(content)
    with pytest.raises(EvidenceError, match="receipt-exists"):
        freeze_test_result(receipts, "op-1", b"different run bytes")


# ---------------------------------------------------------------------------
# Change-manifest capture and verification
# ---------------------------------------------------------------------------


def test_capture_change_manifest_present_and_deleted(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "a.py").write_bytes(b"aaa")
    (root / "gone.py").write_bytes(b"was here")
    budget = AcquisitionBudget()
    first = capture_change_manifest(root, ("a.py", "gone.py"), budget=budget)
    (root / "gone.py").unlink()
    (root / "a.py").write_bytes(b"aab")
    second = capture_change_manifest(root, ("a.py", "gone.py"), budget=budget)
    assert first.digest != second.digest
    assert second.entries[1].status == "deleted"
    drifted = verify_change_manifest(root, first, budget=AcquisitionBudget())
    assert drifted == ("a.py", "gone.py")


def test_capture_change_manifest_applies_exclusions(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "a.py").write_bytes(b"aaa")
    (root / "own-review.md").write_bytes(b"mine")
    manifest = capture_change_manifest(
        root, ("a.py", "own-review.md"),
        budget=AcquisitionBudget(), exclusions=frozenset({"own-review.md"}),
    )
    assert [e.path for e in manifest.entries] == ["a.py"]


def test_resolve_exclusions_rules(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    views = root / ".cg-docs/views"
    views.mkdir(parents=True)
    (views / "a.html").write_bytes(b"html")
    (views / "b.md").write_bytes(b"md")
    resolved = resolve_exclusions(
        root, (".cg-docs/views/**/*.html", "tests/last-run.json"),
        own_report=".cg-docs/work-reports/own.md",
    )
    assert ".cg-docs/views/a.html" in resolved
    assert ".cg-docs/views/b.md" not in resolved
    assert "tests/last-run.json" in resolved
    assert ".cg-docs/work-reports/own.md" in resolved
    for bad in ("tests/", ".github/", "scripts/", "a/*.py", ".cg-docs/views/"):
        with pytest.raises(EvidenceError, match="directory-wide"):
            resolve_exclusions(root, (bad,), own_report="r.md")


def test_manifest_input_limit_enforced(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "big.bin").write_bytes(b"x" * (MANIFEST_INPUT_LIMIT + 1))
    with pytest.raises(EvidenceError, match="evidence-too-large"):
        capture_change_manifest(
            root, ("big.bin",), budget=AcquisitionBudget(limit=AGGREGATE_LIMIT)
        )
