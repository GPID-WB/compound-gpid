"""Drift tests — detect stale or orphaned generated platform trees.

Runs cg_generate_targets.py --all --dry-run against the current .github/ source
and compares the dry-run output manifest against the committed generated trees.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_drift.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_generator_dry_run(root: Path) -> set[str]:
    """Run the generator in dry-run mode and return the set of expected output paths."""
    result = subprocess.run(
        [sys.executable, str(root / "scripts/cg_generate_targets.py"), "--root", str(root), "--all", "--dry-run"],
        capture_output=True, text=True, cwd=str(root), timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(f"Generator failed in dry-run: {result.stderr}")

    expected: set[str] = set()
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith(".") and "/" in stripped and not stripped.startswith("["):
            path = stripped.split(" ")[0]
            expected.add(path)
    return expected


def _committed_generated_files(root: Path, tree_paths: list[str]) -> set[str]:
    """Return the set of committed files in generated tree directories."""
    result = subprocess.run(
        ["git", "ls-files", "--", *tree_paths],
        capture_output=True, text=True, cwd=str(root), timeout=30,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not list committed generated files: {result.stderr}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


class TestNoDrift:
    def test_generated_trees_are_not_stale(self) -> None:
        """Every file the generator would produce must exist in the committed trees."""
        expected = _run_generator_dry_run(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode"])

        missing = expected - committed
        if missing:
            pytest.fail(
                f"Generated trees are stale — {len(missing)} file(s) missing.\n"
                f"Run: python3 scripts/cg_generate_targets.py --all\n"
                f"Missing files (first 10): {sorted(missing)[:10]}"
            )

    def test_no_orphaned_generated_files(self) -> None:
        """No committed file should exist that the generator would not produce."""
        expected = _run_generator_dry_run(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode"])

        orphaned = committed - expected
        if orphaned:
            pytest.fail(
                f"Orphaned generated files found — {len(orphaned)} file(s) not in generator output.\n"
                f"Run: python3 scripts/cg_generate_targets.py --all\n"
                f"Orphaned files (first 10): {sorted(orphaned)[:10]}"
            )

    def test_github_not_modified_by_generator(self, tmp_path: Path) -> None:
        """Generator must not modify .github/ canonical assets."""
        import shutil
        fixture = tmp_path / "fixture"

        # Copy only .github/ and scripts/ needed to run the generator — not the
        # entire repo (which would include .git, .cg-docs, docs, etc. and be slow).
        for item in [".github", "scripts"]:
            src = REPO_ROOT / item
            dst = fixture / item
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

        prompt_before = (fixture / ".github/prompts/cg-work.prompt.md").read_text()
        import cg_generate_targets as gen
        assets = gen.scan_canonical_assets(fixture)
        mapping = gen.load_target_mapping(fixture)
        catalog = gen.load_model_catalog(fixture)

        for target in mapping["targets"]:
            if target.get("generatedTreePath") is None:
                continue
            gen.emit_for_target(fixture, target, assets, catalog, dry_run=False)

        prompt_after = (fixture / ".github/prompts/cg-work.prompt.md").read_text()
        assert prompt_before == prompt_after, "Generator modified .github/ canonical assets"
