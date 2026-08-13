"""Created 2026-08-13. Repeatability and lockfile provenance manifests."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .identity import sha256_file
from .retrieval.lexical import LexicalIndex
from .schemas import SourceUnit, canonical_yaml
from .transactions import ArtifactStore, SimulatedCrash


def _hash_bytes(payload: bytes) -> str:
    """Return a lowercase SHA-256 digest for one deterministic payload."""
    return sha256(payload).hexdigest()


def _run_index(
    units: list[SourceUnit],
    queries: list[str],
    path: Path,
) -> tuple[list[str], dict[str, list[str]]]:
    """Build one derived index and capture IDs/rankings without raw text."""
    index = LexicalIndex(path)
    index.rebuild(units)
    source_ids = [unit.source_unit_id for unit in units]
    rankings = {
        query: [unit.source_unit_id for unit in index.search(query)]
        for query in queries
    }
    index.close()
    return source_ids, rankings


def _check_transaction_recovery(output_dir: Path) -> bool:
    """Exercise a replacement-complete journal recovery boundary."""
    store = ArtifactStore(output_dir / "transaction-recovery")
    try:
        with store.transaction(expected_revision=0, actor="benchmark", action="repeatability") as transaction:
            transaction.stage_yaml("record.yaml", {"value": "deterministic"})
            transaction.commit(failure_at="after_replace")
    except SimulatedCrash:
        results = store.recover()
        return bool(results and results[0].status == "committed")
    return False


def build_reproducibility_manifest(
    units: list[SourceUnit],
    *,
    queries: list[str],
    lockfile: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Compare repeated lexical, YAML, and transaction outputs with lock provenance.

    Args:
        units: Deterministic typed source units to repeat.
        queries: Query strings used only to compare ranking IDs.
        lockfile: Committed project lockfile to hash.
        output_dir: Disposable directory for derived repeat-run artifacts.

    Returns:
        Machine-readable manifest without raw source text or query strings.

    Raises:
        ValueError: If units, queries, or lockfile are missing.

    Example:
        ``build_reproducibility_manifest(units, queries=["term"], lockfile=Path("uv.lock"), output_dir=tmp_path)``.
    """
    if not units or not queries:
        raise ValueError("Reproducibility checks require units and queries")
    if not lockfile.is_file():
        raise ValueError(f"Lockfile is missing: {lockfile}")
    output_dir.mkdir(parents=True, exist_ok=True)
    source_ids_a, rankings_a = _run_index(units, queries, output_dir / "run-a.sqlite")
    source_ids_b, rankings_b = _run_index(units, queries, output_dir / "run-b.sqlite")
    yaml_a = canonical_yaml([unit.model_dump(mode="json", exclude_none=True) for unit in units])
    yaml_b = canonical_yaml([unit.model_dump(mode="json", exclude_none=True) for unit in units])
    source_ids_match = source_ids_a == source_ids_b
    rankings_match = rankings_a == rankings_b
    canonical_yaml_match = yaml_a == yaml_b
    transaction_recovery_checked = _check_transaction_recovery(output_dir)
    return {
        "schema_version": "research-evidence-reproducibility-v1",
        "profile": "lexical-baseline",
        "corpus": {"source_units": len(units)},
        "lockfile_sha256": sha256_file(lockfile),
        "source_ids_hash": _hash_bytes(json.dumps(source_ids_a, sort_keys=True).encode("utf-8")),
        "rankings_hash": _hash_bytes(json.dumps(rankings_a, sort_keys=True).encode("utf-8")),
        "canonical_yaml_sha256": _hash_bytes(yaml_a.encode("utf-8")),
        "source_ids_match": source_ids_match,
        "rankings_match": rankings_match,
        "canonical_yaml_match": canonical_yaml_match,
        "transaction_recovery_checked": transaction_recovery_checked,
        "passed": source_ids_match and rankings_match and canonical_yaml_match and transaction_recovery_checked,
        "raw_text": False,
    }
