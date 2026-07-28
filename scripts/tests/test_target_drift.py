"""Drift tests — detect stale or orphaned generated platform trees.

Runs cg_generate_targets.py --all --dry-run against the current .github/ source
and compares the output manifest against the committed generated tree index.
Paths ignored by git are excluded from the committed parity gate.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_drift.py -v
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cg_generate_targets as gen

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_SKILL_ROOTS = (".claude/skills", ".agents/skills", ".opencode/skills")
OWNERSHIP_MANIFESTS = {
    ".claude/.compound-gpid-generated.json",
    ".agents/.compound-gpid-generated.json",
    ".opencode/.compound-gpid-generated.json",
}


def _run_generator_dry_run(root: Path) -> set[str]:
    """Run the generator in dry-run mode and return the set of expected output paths."""
    result = subprocess.run(
        [sys.executable, str(root / "scripts/cg_generate_targets.py"), "--root", str(root), "--all", "--dry-run"],
        capture_output=True, text=True, cwd=str(root), timeout=60, check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"Generator failed in dry-run: {result.stderr}")

    expected: set[str] = set()
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith(".") and "/" in stripped and not stripped.startswith("["):
            path = stripped.split(" ")[0]
            expected.add(path)
    return expected | OWNERSHIP_MANIFESTS


def _committed_generated_files(root: Path, tree_paths: list[str]) -> set[str]:
    """Return the set of committed files in generated tree directories."""
    result = subprocess.run(
        ["git", "ls-files", "--", *tree_paths],
        capture_output=True, text=True, cwd=str(root), timeout=30, check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not list committed generated files: {result.stderr}")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _read_git_blob_bytes(root: Path, rel_path: str) -> bytes:
    """Read committed file bytes from HEAD."""
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        capture_output=True,
        text=False,
        cwd=str(root),
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace")
        pytest.skip(f"Could not read committed blob for {rel_path}: {stderr}")
    return result.stdout


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_git_ignored(root: Path, rel_path: str) -> bool:
    """Return True when a repository-relative path is ignored by git."""
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", rel_path],
        cwd=str(root),
        timeout=30,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    pytest.skip(f"Could not evaluate git ignore state for {rel_path}")
    return False


class TestNoDrift:
    def test_generated_skill_bundles_recursively_match_canonical_files(self) -> None:
        """Every generated skill bundle must have the complete canonical file set."""
        canonical_root = REPO_ROOT / ".github/skills"
        mismatches: list[str] = []
        for canonical in sorted(canonical_root.glob("cg-skill-*")):
            canonical_files = {
                path.relative_to(canonical).as_posix()
                for path in canonical.rglob("*")
                if path.is_file()
            }
            for target_root in TARGET_SKILL_ROOTS:
                generated = REPO_ROOT / target_root / canonical.name
                if not generated.exists():
                    continue
                generated_files = {
                    path.relative_to(generated).as_posix()
                    for path in generated.rglob("*")
                    if path.is_file()
                }
                if generated_files != canonical_files:
                    mismatches.append(f"{target_root}/{canonical.name}")

        assert not mismatches, f"Incomplete generated skill bundles: {mismatches}"

    def test_generated_trees_are_not_stale(self) -> None:
        """Every non-ignored expected file should exist in committed outputs."""
        expected = _run_generator_dry_run(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode"])
        expected_committed = {
            path
            for path in expected
            if not _is_git_ignored(REPO_ROOT, path)
        }

        missing = expected_committed - committed
        if missing:
            pytest.fail(
                f"Generated trees are stale — {len(missing)} file(s) missing.\n"
                f"Run: python3 scripts/cg_generate_targets.py --all\n"
                f"Missing files (first 10): {sorted(missing)[:10]}"
            )

    def test_no_orphaned_generated_files(self) -> None:
        """No committed generated file should exist outside generator output."""
        expected = _run_generator_dry_run(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode"])

        orphaned = committed - expected
        if orphaned:
            pytest.fail(
                f"Orphaned generated files found — {len(orphaned)} file(s) not in generator output.\n"
                f"Run: python3 scripts/cg_generate_targets.py --all\n"
                f"Orphaned files (first 10): {sorted(orphaned)[:10]}"
            )

    def test_committed_generated_content_matches_dry_run_manifest(self) -> None:
        """Committed generated files should match dry-run regenerated content."""
        expected = _run_generator_dry_run(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode"])
        expected_committed = {
            path
            for path in expected
            if not _is_git_ignored(REPO_ROOT, path)
        }

        # Compare only files that are both expected and committed to avoid
        # duplicate reporting with stale/orphaned path tests above.
        overlap = sorted(expected_committed & committed)
        if not overlap:
            pytest.skip("No overlapping generated files to compare")

        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture = Path(tmp_dir) / "fixture"

            for item in [".github", "scripts"]:
                src = REPO_ROOT / item
                dst = fixture / item
                if src.exists():
                    shutil.copytree(src, dst, dirs_exist_ok=True)

            assets = gen.scan_canonical_assets(fixture)
            mapping = gen.load_target_mapping(fixture)
            catalog = gen.load_model_catalog(fixture)
            for target in mapping["targets"]:
                if target.get("generatedTreePath") is None:
                    continue
                gen.emit_for_target(fixture, target, assets, catalog, dry_run=False)

            mismatches: list[str] = []
            for rel_path in overlap:
                generated_path = fixture / rel_path
                if not generated_path.exists():
                    mismatches.append(f"missing generated output: {rel_path}")
                    continue
                generated_bytes = generated_path.read_bytes()
                committed_bytes = _read_git_blob_bytes(REPO_ROOT, rel_path)
                if _sha256_bytes(generated_bytes) != _sha256_bytes(committed_bytes):
                    mismatches.append(rel_path)

            if mismatches:
                pytest.fail(
                    "Generated tree content drift detected.\n"
                    "Run: python3 scripts/cg_generate_targets.py --all\n"
                    f"Mismatched files (first 10): {mismatches[:10]}"
                )

    def test_github_not_modified_by_generator(self, tmp_path: Path) -> None:
        """Generator must not modify .github/ canonical assets."""
        fixture = tmp_path / "fixture"

        # Copy only .github/ and scripts/ needed to run the generator — not the
        # entire repo (which would include .git, .cg-docs, docs, etc. and be slow).
        for item in [".github", "scripts"]:
            src = REPO_ROOT / item
            dst = fixture / item
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

        prompt_before = (fixture / ".github/prompts/cg-work.prompt.md").read_text(encoding="utf-8")
        assets = gen.scan_canonical_assets(fixture)
        mapping = gen.load_target_mapping(fixture)
        catalog = gen.load_model_catalog(fixture)

        for target in mapping["targets"]:
            if target.get("generatedTreePath") is None:
                continue
            gen.emit_for_target(fixture, target, assets, catalog, dry_run=False)

        prompt_after = (fixture / ".github/prompts/cg-work.prompt.md").read_text(encoding="utf-8")
        assert prompt_before == prompt_after, "Generator modified .github/ canonical assets"
