"""Created 2026-08-13. Tests for lexical benchmark manifests and fixed corpora."""
from __future__ import annotations

from pathlib import Path

from research_evidence.benchmarks import (
    FIXED_CORPORA,
    make_fixed_corpus,
    run_lexical_benchmark,
)


def test_fixed_corpora_have_declared_sizes() -> None:
    """Expose the plan's reproducible small and medium corpus contracts."""
    assert FIXED_CORPORA["small"].documents == 25
    assert FIXED_CORPORA["small"].source_units == 2_500
    assert FIXED_CORPORA["medium"].documents == 100
    assert FIXED_CORPORA["medium"].source_units == 20_000


def test_benchmark_manifest_captures_environment_without_raw_text(tmp_path: Path) -> None:
    """Record latency, rebuild, memory, versions, and profile without corpus text."""
    units = make_fixed_corpus("small", documents=2, source_units=20)
    result = run_lexical_benchmark(
        units,
        queries=["poverty", "weighted"],
        index_path=tmp_path / "benchmark.sqlite",
        profile="lexical-baseline",
    )
    manifest = result.to_manifest()

    assert manifest["profile"] == "lexical-baseline"
    assert manifest["corpus"]["source_units"] == 20
    assert manifest["environment"]["python"]
    assert manifest["metrics"]["p95_query_ms"] >= 0
    assert manifest["raw_text"] is False
    assert "poverty" not in str(manifest)
