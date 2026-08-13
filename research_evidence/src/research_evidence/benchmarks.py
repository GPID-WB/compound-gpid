"""Created 2026-08-13. Deterministic lexical benchmark corpus and manifests."""
from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import os
from pathlib import Path
import platform
import sys
import time
import tracemalloc

try:
    import resource as resource_module
except ImportError:
    resource_module = None

from .identity import make_source_unit_id, text_fingerprint
from .retrieval.lexical import LexicalIndex
from .schemas import SourceUnit, TypedLocator


@dataclass(frozen=True)
class BenchmarkCorpusSpec:
    """Declare one fixed benchmark corpus size and acceptance thresholds.

    Args:
        name: Stable corpus profile name.
        documents: Number of logical documents.
        source_units: Number of generated source units.
        query_p95_ms: Maximum acceptable p95 lexical query latency.
        incremental_update_seconds: Maximum single-resource update cost.
        rebuild_seconds: Maximum full rebuild cost.
        memory_bytes: Maximum measured process allocation budget.

    Returns:
        An immutable benchmark specification.

    Example:
        ``BenchmarkCorpusSpec("small", 25, 2500, 250, 10, 60, 1_000_000_000)``.
    """

    name: str
    documents: int
    source_units: int
    query_p95_ms: float = 250.0
    incremental_update_seconds: float = 10.0
    rebuild_seconds: float = 60.0
    memory_bytes: int = 1_000_000_000


FIXED_CORPORA = {
    "small": BenchmarkCorpusSpec("small", 25, 2_500),
    "medium": BenchmarkCorpusSpec("medium", 100, 20_000),
}


@dataclass(frozen=True)
class BenchmarkResult:
    """Capture deterministic lexical metrics and environment provenance.

    Args:
        profile: Retrieval profile name.
        corpus: Corpus counts used by the run.
        environment: Machine and package metadata.
        metrics: Measured latency, rebuild, update, and memory values.
        thresholds: Declared acceptance thresholds.
        passed: Whether every declared threshold was met.

    Returns:
        An immutable benchmark result suitable for JSON/YAML serialization.

    Example:
        ``result.to_manifest()`` produces a machine-readable benchmark artifact.
    """

    profile: str
    corpus: dict[str, int]
    environment: dict[str, object]
    metrics: dict[str, float | int]
    thresholds: dict[str, float | int]
    passed: bool

    def to_manifest(self) -> dict[str, object]:
        """Serialize the result without raw corpus text or query strings.

        Args:
            None.

        Returns:
            Machine-readable benchmark manifest.

        Example:
            ``manifest = result.to_manifest()`` can be committed as evidence.
        """
        return {
            "schema_version": "research-evidence-benchmark-v1",
            "profile": self.profile,
            "corpus": self.corpus,
            "environment": self.environment,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "passed": self.passed,
            "raw_text": False,
        }


def make_fixed_corpus(
    name: str,
    *,
    documents: int | None = None,
    source_units: int | None = None,
) -> list[SourceUnit]:
    """Generate deterministic typed units for a declared benchmark profile.

    Args:
        name: Key in ``FIXED_CORPORA``.
        documents: Optional test-sized document override.
        source_units: Optional test-sized unit override.

    Returns:
        Deterministically generated source units with no random state.

    Raises:
        KeyError: If ``name`` is not a declared corpus.
        ValueError: If counts are non-positive or units are fewer than documents.

    Example:
        ``make_fixed_corpus("small", documents=2, source_units=20)``.
    """
    spec = FIXED_CORPORA[name]
    document_count = documents if documents is not None else spec.documents
    unit_count = source_units if source_units is not None else spec.source_units
    if document_count <= 0 or unit_count <= 0 or unit_count < document_count:
        raise ValueError("Benchmark corpus counts must be positive with units >= documents")
    units: list[SourceUnit] = []
    for index in range(unit_count):
        document_index = index % document_count
        block = index // document_count + 1
        version_id = f"benchmark:{name}:document-{document_index:04d}"
        text = f"Document {document_index} weighted poverty finding {index}."
        fingerprint = text_fingerprint(text)
        locator = TypedLocator(
            kind="markdown_block",
            block=block,
            unit_fingerprint=fingerprint,
        )
        units.append(
            SourceUnit(
                source_unit_id=make_source_unit_id(version_id, locator, fingerprint),
                source_version_id=version_id,
                locator=locator,
                text=text,
                heading_path=[f"Document {document_index}"],
                parser_metadata={"benchmark_profile": name},
            )
        )
    return units


def _p95(values: list[float]) -> float:
    """Compute an inclusive nearest-rank p95 in milliseconds."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
    return ordered[index] * 1000.0


def _environment() -> dict[str, object]:
    """Capture stable machine/runtime metadata without corpus content."""
    try:
        package_version = importlib.metadata.version("compound-research-evidence")
    except importlib.metadata.PackageNotFoundError:
        package_version = "editable-unknown"
    memory_peak = 0
    if resource_module is not None:
        memory_peak = int(
            resource_module.getrusage(resource_module.RUSAGE_SELF).ru_maxrss
        )
    return {
        "os": platform.platform(),
        "cpu": platform.processor() or "unknown",
        "cpu_count": os.cpu_count() or 0,
        "python": sys.version.split()[0],
        "package_version": package_version,
        "memory_peak_bytes": memory_peak,
    }


def run_lexical_benchmark(
    units: list[SourceUnit],
    *,
    queries: list[str],
    index_path: Path,
    profile: str,
) -> BenchmarkResult:
    """Measure lexical rebuild, query, and incremental-update performance.

    Args:
        units: Fixed deterministic source units to benchmark.
        queries: Queries used only for measurement; never written to the manifest.
        index_path: Derived SQLite index path.
        profile: Named retrieval profile under evaluation.

    Returns:
        Benchmark result with threshold status and environment metadata.

    Raises:
        ValueError: If no units or queries are supplied.

    Example:
        ``run_lexical_benchmark(units, queries=["poverty"], index_path=path, profile="lexical-baseline")``.
    """
    if not units or not queries:
        raise ValueError("Lexical benchmark requires units and queries")
    spec = FIXED_CORPORA["small"]
    tracemalloc.start()
    index = LexicalIndex(index_path)
    rebuild_start = time.perf_counter()
    index.rebuild(units)
    rebuild_seconds = time.perf_counter() - rebuild_start
    query_latencies: list[float] = []
    for query in queries:
        query_start = time.perf_counter()
        index.search(query)
        query_latencies.append(time.perf_counter() - query_start)
    incremental_start = time.perf_counter()
    index.upsert([units[0]])
    incremental_seconds = time.perf_counter() - incremental_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    index.close()
    metrics: dict[str, float | int] = {
        "p95_query_ms": _p95(query_latencies),
        "rebuild_seconds": rebuild_seconds,
        "incremental_update_seconds": incremental_seconds,
        "peak_memory_bytes": peak_bytes,
    }
    thresholds: dict[str, float | int] = {
        "p95_query_ms": spec.query_p95_ms,
        "rebuild_seconds": spec.rebuild_seconds,
        "incremental_update_seconds": spec.incremental_update_seconds,
        "memory_bytes": spec.memory_bytes,
    }
    passed = (
        metrics["p95_query_ms"] <= thresholds["p95_query_ms"]
        and metrics["rebuild_seconds"] <= thresholds["rebuild_seconds"]
        and metrics["incremental_update_seconds"] <= thresholds["incremental_update_seconds"]
        and metrics["peak_memory_bytes"] <= thresholds["memory_bytes"]
    )
    return BenchmarkResult(
        profile=profile,
        corpus={
            "documents": len({unit.source_version_id for unit in units}),
            "source_units": len(units),
        },
        environment=_environment(),
        metrics=metrics,
        thresholds=thresholds,
        passed=passed,
    )
