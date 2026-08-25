"""Regression tests for manifest projection ordering in the link wrappers."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_CONFIG = """---
language: "both"
project-type: "tool"
review-depth: "thorough"
suites: [cg]
---
# Test project
"""
REQUIRED_KILO_ROOTS = ("commands", "skills", "agents", "instructions", "shared")


def _assert_order(content: str, earlier: str, later: str) -> None:
    """Assert that two unique pipeline markers occur in lifecycle order."""
    earlier_index = content.index(earlier)
    later_index = content.index(later)
    assert earlier_index < later_index, f"Expected {earlier!r} before {later!r}"


def test_powershell_projects_before_local_kilo_preflight() -> None:
    """The Windows wrapper must materialize roots before validating them."""
    content = (REPO_ROOT / "scripts/link.ps1").read_text(encoding="utf-8")
    _assert_order(
        content,
        "Resolve-CgActiveManifest -ProjectRoot",
        "\nRemove-CgLegacyModelMappingFiles -Manifest",
    )
    _assert_order(
        content,
        "Invoke-CgProjection -ProjectRoot",
        "Invoke-CgKiloPreflight -ProjectRoot $ProjectRoot -LocalOnly",
    )


def test_shell_projects_before_local_kilo_preflight() -> None:
    """The macOS/Linux wrapper must materialize roots before validating them."""
    content = (REPO_ROOT / "scripts/link.sh").read_text(encoding="utf-8")
    _assert_order(content, "cg_project_manifest.py", "\ncleanup_legacy_model_mapping_files\n")
    _assert_order(content, "cg_project_projection.py", "run_kilo_preflight local")


@pytest.mark.skipif(os.name == "nt", reason="macOS/Linux link.sh integration")
def test_shell_links_fresh_manifest_driven_kilo_project(tmp_path: Path) -> None:
    """A fresh manifest consumer must not need manually precreated Kilo roots."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is unavailable")

    project = tmp_path / "consumer"
    profile = tmp_path / "profile"
    project.mkdir()
    profile.mkdir()
    (project / "compound-gpid.local.md").write_text(LOCAL_CONFIG, encoding="utf-8")

    environment = os.environ.copy()
    environment.update({"CG_SKIP_UPDATE": "1", "HOME": str(profile)})
    result = subprocess.run(
        [bash, str(REPO_ROOT / "scripts/link.sh"), "--platforms", "kilo", "--yes"],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "Platforms: kilo" in output
    assert "local-projection-missing" not in output
    assert "Kilo preflight (local): ok" in output
    for root_name in REQUIRED_KILO_ROOTS:
        root = project / ".kilo" / root_name
        assert root.is_dir(), f"Missing projected root: {root}\n{output}"
        assert not root.is_symlink(), f"Projected root is a symlink: {root}"
    assert (project / ".kilo/commands/cg-plan.md").is_file()
    assert (project / ".compound-gpid/active-manifest.json").is_file()


@pytest.mark.skipif(os.name == "nt", reason="macOS/Linux link.sh integration")
def test_shell_rejects_invalid_manifest_before_project_mutation(tmp_path: Path) -> None:
    """Strict config failure must stop before install, preflight, or success."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is unavailable")

    project = tmp_path / "invalid-consumer"
    profile = tmp_path / "profile"
    project.mkdir()
    profile.mkdir()
    sentinel = project / "user-content.txt"
    sentinel.write_text("preserve me\n", encoding="utf-8")
    (project / "compound-gpid.local.md").write_text(
        "---\nunknown-key: invalid\n---\n# Invalid test config\n",
        encoding="utf-8",
    )

    environment = os.environ.copy()
    environment.update({"CG_SKIP_UPDATE": "1", "HOME": str(profile)})
    result = subprocess.run(
        [bash, str(REPO_ROOT / "scripts/link.sh"), "--platforms", "kilo", "--yes"],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert sentinel.read_text(encoding="utf-8") == "preserve me\n"
    assert not (project / ".kilo").exists()
    assert "Kilo preflight" not in output
    assert "Linked!" not in output
