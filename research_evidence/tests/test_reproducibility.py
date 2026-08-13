"""Created 2026-08-13. Tests for final reproducibility manifests."""
from __future__ import annotations

from pathlib import Path

from research_evidence.benchmarks import make_fixed_corpus
from research_evidence.reproducibility import build_reproducibility_manifest


def test_repeatability_manifest_compares_ids_rankings_yaml_and_lockfile(tmp_path: Path) -> None:
    """Verify deterministic repeated output without persisting source text."""
    lockfile = Path("research_evidence/uv.lock")
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
    assert manifest["source_ids_match"] is True
    assert manifest["rankings_match"] is True
    assert manifest["canonical_yaml_match"] is True
    assert manifest["transaction_recovery_checked"] is True
    assert "poverty" not in str(manifest)
