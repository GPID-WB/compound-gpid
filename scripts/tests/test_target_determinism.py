"""Determinism checks for structured native-target generation plans."""

from pathlib import Path

import cg_generate_targets as gen


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_structured_generation_plan_is_byte_deterministic() -> None:
    """Repeated planning from identical canonical inputs emits identical entries."""
    mapping = gen.load_target_mapping(REPO_ROOT)
    assets = gen.scan_canonical_assets(REPO_ROOT)

    first = gen.build_generation_plan(REPO_ROOT, mapping, assets)
    second = gen.build_generation_plan(REPO_ROOT, mapping, assets)

    assert first.entries == second.entries
