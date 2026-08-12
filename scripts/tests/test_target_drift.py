"""Drift tests — detect stale or orphaned generated platform trees.

Builds the generator's structured plan against the current .github/ source and
compares its entries and ownership manifests against committed HEAD bytes.
Paths ignored by git are excluded from the committed parity gate.

Run from repo root:
    python3 -m pytest scripts/tests/test_target_drift.py -v
"""
from __future__ import annotations

import functools
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import cg_generate_targets as gen

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_SKILL_ROOTS = (".claude/skills", ".agents/skills", ".opencode/skills", ".kilo/skills")
OWNERSHIP_MANIFESTS = {
    ".claude/.compound-gpid-generated.json",
    ".agents/.compound-gpid-generated.json",
    ".opencode/.compound-gpid-generated.json",
    ".kilo/.compound-gpid-generated.json",
}


def _build_structured_plan(root: Path) -> gen.GenerationPlan:
    """Build and return the validated in-memory generation plan."""
    try:
        mapping = gen.load_target_mapping(root)
        assets = gen.scan_canonical_assets(root)
        return gen.build_generation_plan(root, mapping, assets)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        pytest.fail(f"Generator failed while building structured plan: {exc}")


@functools.lru_cache(maxsize=8)
def _expected_paths(root: Path) -> frozenset[str]:
    plan = _build_structured_plan(root)
    return frozenset({entry.destination for entry in plan.entries} | OWNERSHIP_MANIFESTS)


def _committed_generated_files(root: Path, tree_paths: list[str]) -> set[str]:
    """Return the set of committed files in generated tree directories."""
    result = subprocess.run(
        ["git", "ls-files", "--", *tree_paths],
        capture_output=True, text=True, cwd=str(root), timeout=30, check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"Could not list committed generated files: {result.stderr}")
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
        pytest.fail(f"Could not read committed blob for {rel_path}: {stderr}")
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
    pytest.fail(f"Could not evaluate git ignore state for {rel_path}")


@pytest.mark.parametrize(
    ("helper", "returncode"),
    [(_committed_generated_files, 128)],
)
def test_required_command_failures_fail_instead_of_skip(
    monkeypatch: pytest.MonkeyPatch, helper: object, returncode: int
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode, "", "forced failure"),
    )
    with pytest.raises(pytest.fail.Exception, match="failed|Could not list"):
        _committed_generated_files(REPO_ROOT, [".claude"])


def test_generator_plan_failure_fails_instead_of_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_mapping(root: Path) -> dict[str, object]:
        raise ValueError("forced failure")

    monkeypatch.setattr(gen, "load_target_mapping", fail_mapping)
    with pytest.raises(pytest.fail.Exception, match="structured plan"):
        _build_structured_plan(REPO_ROOT)


def test_git_blob_failure_fails_instead_of_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128, b"", b"forced failure"),
    )
    with pytest.raises(pytest.fail.Exception, match="Could not read committed blob"):
        _read_git_blob_bytes(REPO_ROOT, ".claude/missing")


def test_git_ignore_failure_fails_instead_of_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128),
    )
    with pytest.raises(pytest.fail.Exception, match="ignore state"):
        _is_git_ignored(REPO_ROOT, ".claude/missing")


class TestNoDrift:
    def test_ownership_manifests_are_well_formed_and_match_head(self) -> None:
        for rel_path in sorted(OWNERSHIP_MANIFESTS):
            committed = _read_git_blob_bytes(REPO_ROOT, rel_path)
            try:
                manifest = json.loads(committed)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                pytest.fail(f"Malformed ownership manifest {rel_path}: {exc}")
            assert isinstance(manifest.get("files"), list), rel_path
            for entry in manifest["files"]:
                assert set(entry) >= {"path", "sha256"}, (rel_path, entry)
                blob = _read_git_blob_bytes(REPO_ROOT, entry["path"])
                assert _sha256_bytes(blob) == entry["sha256"], entry["path"]

    def test_dirty_generated_files_fail_drift_gate(self) -> None:
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", ".claude", ".agents", ".opencode", ".kilo"],
            cwd=str(REPO_ROOT), timeout=30, check=False,
        )
        assert result.returncode == 0, "Dirty generated target tree must fail drift"

    def test_generated_skill_bundles_recursively_match_canonical_files(self) -> None:
        """Every generated skill bundle must have the complete canonical file set."""
        canonical_root = REPO_ROOT / ".github/skills"
        mismatches: list[str] = []
        for canonical in sorted(canonical_root.glob("*")):
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
        expected = _expected_paths(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode", ".kilo"])
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
        expected = _expected_paths(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode", ".kilo"])

        orphaned = committed - expected
        if orphaned:
            pytest.fail(
                f"Orphaned generated files found — {len(orphaned)} file(s) not in generator output.\n"
                f"Run: python3 scripts/cg_generate_targets.py --all\n"
                f"Orphaned files (first 10): {sorted(orphaned)[:10]}"
            )

    def test_committed_generated_content_matches_dry_run_manifest(self) -> None:
        """Committed generated files should match dry-run regenerated content."""
        expected = _expected_paths(REPO_ROOT)
        committed = _committed_generated_files(REPO_ROOT, [".claude", ".agents", ".opencode", ".kilo"])
        expected_committed = {
            path
            for path in expected
            if not _is_git_ignored(REPO_ROOT, path)
        }

        # Compare only files that are both expected and committed to avoid
        # duplicate reporting with stale/orphaned path tests above.
        overlap = sorted(expected_committed & committed)
        assert overlap, "No overlapping generated files to compare"

        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture = Path(tmp_dir) / "fixture"

            for item in [".github", "scripts"]:
                src = REPO_ROOT / item
                dst = fixture / item
                if src.exists():
                    shutil.copytree(src, dst, dirs_exist_ok=True)

            assets = gen.scan_canonical_assets(fixture)
            mapping = gen.load_target_mapping(fixture)
            for target in mapping["targets"]:
                if target.get("generatedTreePath") is None:
                    continue
                gen.emit_for_target(fixture, target, assets, dry_run=False)

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

        # Copy only .github/ and scripts/ needed to run the generator â€” not the
        # entire repo (which would include .git, .cg-docs, docs, etc. and be slow).
        for item in [".github", "scripts"]:
            src = REPO_ROOT / item
            dst = fixture / item
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

        prompt_before = (fixture / ".github/prompts/cg-work.prompt.md").read_text(encoding="utf-8")
        assets = gen.scan_canonical_assets(fixture)
        mapping = gen.load_target_mapping(fixture)

        for target in mapping["targets"]:
            if target.get("generatedTreePath") is None:
                continue
            gen.emit_for_target(fixture, target, assets, dry_run=False)

        prompt_after = (fixture / ".github/prompts/cg-work.prompt.md").read_text(encoding="utf-8")
        assert prompt_before == prompt_after, "Generator modified .github/ canonical assets"


class TestCrCgParity:
    """CG/CR generated-target parity across all 5 platforms (R5).

    Uses synthetic cr-* fixtures in tmp_path (never committed) to prove the
    discovery + parity pipeline before real CR content is imported in Phase 3.
    Generation runs once per module so the drill-time stays within release-gate
    subprocess limits.
    """

    TARGET_SKILL_ROOTS = (".claude/skills", ".agents/skills", ".opencode/skills", ".kilo/skills")
    TARGET_COMMAND_ROOTS = (".claude/commands", ".agents/commands", ".opencode/commands", ".kilo/commands")
    TARGET_AGENT_ROOTS = (".claude/agents", ".agents/subagents", ".opencode/agents", ".kilo/agents")
    TARGET_INSTRUCTION_ROOTS = (".claude/instructions", ".agents/instructions", ".opencode/instructions", ".kilo/instructions")

    @pytest.fixture(scope="class")
    def fixture_root(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        fixture = tmp_path_factory.mktemp("cr-parity") / "fixture"
        for item in [".github", "scripts"]:
            src = REPO_ROOT / item
            dst = fixture / item
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        # Synthetic CR assets (never committed).
        (fixture / ".github/prompts/cr-work.prompt.md").parent.mkdir(parents=True, exist_ok=True)
        (fixture / ".github/prompts/cr-work.prompt.md").write_text(
            "---\ndescription: cr work\n---\n\n# CR Work\n", encoding="utf-8"
        )
        (fixture / ".github/agents/cr-analysis.agent.md").parent.mkdir(parents=True, exist_ok=True)
        (fixture / ".github/agents/cr-analysis.agent.md").write_text(
            "---\ndescription: cr analysis\ntools: [read]\n---\n\n# CR Analysis\n", encoding="utf-8"
        )
        skill = fixture / ".github/skills/cr-skill-identification/SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("---\ndescription: identification\n---\n\n# Identification\n", encoding="utf-8")
        (fixture / ".github/instructions/latex.instructions.md").write_text(
            "# LaTeX\n", encoding="utf-8"
        )
        # Register CR assets in the module registry so discovery includes them.
        registry_path = fixture / ".github/shared/module-registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        existing = {m.get("id") for m in registry["modules"]}
        if "suite-cr" not in existing:
            registry["modules"].append({
                "id": "suite-cr",
                "layer": "suite",
                "displayName": "Research suite",
                "description": "cr-* orchestration",
                "dependsOn": ["kernel", "cap-language-r"],
                "ownedAssets": [
                    ".github/prompts/cr-*.prompt.md",
                    ".github/agents/cr-*.agent.md",
                    ".github/skills/cr-skill-identification/",
                    ".github/instructions/latex.instructions.md",
                ],
                "ambiguous": [],
            })
        else:
            # Real registry already owns suite-cr; ensure the synthetic skill is
            # discoverable for the isolated parity proof.
            suite_cr = next(m for m in registry["modules"] if m.get("id") == "suite-cr")
            if ".github/skills/cr-skill-identification/" not in suite_cr.get("ownedAssets", []):
                suite_cr["ownedAssets"].append(".github/skills/cr-skill-identification/")
        registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        assets = gen.scan_canonical_assets(fixture)
        mapping = gen.load_target_mapping(fixture)
        for target in mapping["targets"]:
            if target.get("generatedTreePath") is None:
                continue
            gen.emit_for_target(fixture, target, assets, dry_run=False)
        return fixture

    def test_cr_skill_reaches_every_platform_tree(self, fixture_root: Path) -> None:
        for root_name in self.TARGET_SKILL_ROOTS:
            assert (fixture_root / root_name / "cr-skill-identification" / "SKILL.md").exists(), root_name

    def test_cr_prompt_reaches_every_platform_tree(self, fixture_root: Path) -> None:
        for root_name in self.TARGET_COMMAND_ROOTS:
            assert (fixture_root / root_name / "cr-work.md").exists(), root_name

    def test_cr_agent_reaches_every_platform_tree(self, fixture_root: Path) -> None:
        for root_name in self.TARGET_AGENT_ROOTS:
            agent_dir = fixture_root / root_name
            found = list(agent_dir.glob("cr-analysis.*"))
            assert found, f"No cr-analysis agent in {root_name}: {sorted(p.name for p in agent_dir.glob('*'))}"

    def test_cr_instruction_reaches_every_platform_tree(self, fixture_root: Path) -> None:
        for root_name in self.TARGET_INSTRUCTION_ROOTS:
            assert (fixture_root / root_name / "latex.instructions.md").exists(), root_name

    def test_cr_assets_owned_and_dependency_closure_valid(self, fixture_root: Path) -> None:
        """Cross-suite gate stays green for the synthetic CR import (R4)."""
        import cg_validate_modules as module_validator
        errors = module_validator.check_dependencies(fixture_root)
        assert errors == [], f"Unexpected dependency errors: {errors}"
