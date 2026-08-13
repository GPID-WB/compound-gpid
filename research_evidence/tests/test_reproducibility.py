"""Created 2026-08-13. Tests for final reproducibility manifests."""
from __future__ import annotations

from pathlib import Path
import json

from research_evidence.benchmarks import make_fixed_corpus
from research_evidence.reproducibility import build_reproducibility_manifest


def test_committed_reproducibility_manifest_matches_recomputed_result(tmp_path: Path) -> None:
    """Reject a checked-in reproducibility artifact that no longer matches code."""
    artifact_path = (
        Path(__file__).resolve().parents[1]
        / "benchmarks"
        / "reproducibility-2026-08-13.json"
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    expected = build_reproducibility_manifest(
        make_fixed_corpus("small", documents=3, source_units=30),
        queries=["poverty", "weighted"],
        lockfile=Path(__file__).resolve().parents[1] / "uv.lock",
        output_dir=tmp_path,
    )
    assert all(artifact[key] == value for key, value in expected.items())


def test_repeatability_manifest_compares_ids_rankings_yaml_and_lockfile(tmp_path: Path) -> None:
    """Verify deterministic repeated output without persisting source text."""
    lockfile = Path(__file__).resolve().parents[1] / "uv.lock"
    units = make_fixed_corpus("small", documents=3, source_units=30)
    manifest = build_reproducibility_manifest(
        units,
        queries=["poverty", "weighted"],
        lockfile=lockfile,
        output_dir=tmp_path,
    )

    assert manifest["passed"] is True
    assert manifest["raw_text"] is False
    assert manifest["lockfile_sha256"]
    assert manifest["pyproject_sha256"]
    assert manifest["input_hash"]
    assert manifest["query_hash"]
    assert manifest["environment"]["python"]
    assert manifest["source_ids_match"] is True
    assert manifest["rankings_match"] is True
    assert manifest["canonical_yaml_match"] is True
    assert manifest["transaction_recovery_checked"] is True
    assert not (tmp_path / "run-a.sqlite").exists()
    assert "poverty" not in str(manifest)
