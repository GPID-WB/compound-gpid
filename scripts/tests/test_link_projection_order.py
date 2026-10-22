"""Regression tests for manifest projection ordering in the link wrappers."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

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
PYTHON_LOCAL_CONFIG = """---
language: "python"
project-type: "tool"
review-depth: "thorough"
suites: [cg]
model-advisory:
  enabled: true
  examples:
    planning: strong-planning-example
---
# Python test project
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
        "--sync-projection",
        "Invoke-CgKiloPreflight -ProjectRoot $ProjectRoot -LocalOnly",
    )


def test_shell_projects_before_local_kilo_preflight() -> None:
    """The macOS/Linux wrapper must materialize roots before validating them."""
    content = (REPO_ROOT / "scripts/link.sh").read_text(encoding="utf-8")
    _assert_order(content, "cg_project_manifest.py", "\ncleanup_legacy_model_mapping_files\n")
    calls = list(re.finditer(
        r"(?m)(?:^|[;)])[ \t]*run_kilo_preflight[ \t]*(?=;|$)", content,
    ))
    assert calls, "Missing runtime run_kilo_preflight invocation"
    assert all(content.index("--sync-projection") < call.start() for call in calls)
    assert 'projection_root="$(platform_generated_tree "$platform")"' in content


def test_both_link_wrappers_leave_copilot_skills_to_projection() -> None:
    powershell = (REPO_ROOT / "scripts/link.ps1").read_text(encoding="utf-8")
    shell = (REPO_ROOT / "scripts/link.sh").read_text(encoding="utf-8")

    assert "projectedCategories" in powershell
    assert "projectedCategories" in shell
    assert "Copilot skills" in powershell
    assert "Copilot skills" in shell


@pytest.mark.parametrize("newline", ("\n", "\r\n"), ids=("lf", "crlf"))
def test_shell_gitignore_block_preserves_user_lines_and_converges(
    tmp_path: Path, newline: str,
) -> None:
    """Exercise only the production heredoc, never the link lifecycle."""
    content = (REPO_ROOT / "scripts/link.sh").read_text(encoding="utf-8")
    function = content.split("\nupdate_gitignore_block() {\n", 1)[1].split("\n}\n", 1)[0]
    writer = function.split("<<'PYEOF'\n", 1)[1].split("\nPYEOF", 1)[0]
    marker = "# Compound GPID managed items (junctions + copied file - do not commit)"
    path = tmp_path / ".gitignore"
    entries_file = tmp_path / "entries"
    entries = (".kilo", ".compound-gpid/active/", "custom-managed/item")
    entries_file.write_text("\n".join(entries) + "\n", encoding="utf-8")
    before = f"# user before  {newline}*.log{newline}{newline}"
    after = newline.join((
        ".kilo-other", ".KILO", " .kilo", ".kilo ", "!.kilo/keep",
        ".cg-docs/user", "# user after\t ", "", "  \t", "",
    ))
    old = newline.join((
        marker, ".github", ".claude", ".agents", ".opencode", ".kilo",
        ".compound-gpid", ".kilo/old/", "",
    ))
    cases = (
        (before + f".kilo{newline}custom-managed/item{newline}" + old + old
         + after + f".compound-gpid/active/{newline}", before + after),
        ("", ""),
        ("*.log  \n\n\t \n", "*.log  \n\n\t \n"),
        (marker + "\n.kilo\n.kilo/old/", ""),
    )
    block = marker + "\n" + "\n".join(sorted(entries)) + "\n"
    for initial, prefix in cases:
        path.write_bytes(initial.encode("utf-8"))
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, "-", str(path), str(entries_file), marker],
                input=writer, capture_output=True, text=True, timeout=30, check=False,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert path.read_bytes() == (prefix + block).encode("utf-8")


def test_snapshot_awk_escapes_delimiters_in_character_classes() -> None:
    """BSD awk ends a regex at an unescaped slash even inside a character class."""
    shell = (REPO_ROOT / "scripts/ci/upgrade-matrix.sh").read_text(encoding="utf-8")
    assert "[^/" not in shell


@pytest.mark.skipif(os.name == "nt", reason="native bash parity")
@pytest.mark.parametrize("case", (
    "metadata", "copy-only", "copy-change", "user-change", "generation-content",
    "other-state", "extra-generation", "staging", "nested-pointer", "pointer-link",
))
def test_shell_repeat_snapshot_enforces_logical_contents(tmp_path: Path, case: str) -> None:
    """Run only the existing comparison helpers against synthetic records."""
    shell = (REPO_ROOT / "scripts/ci/upgrade-matrix.sh").read_text(encoding="utf-8")
    helpers = "\n".join(re.search(rf"(?ms)^{name}\(\) \{{\n.*?^\}}", shell).group(0)
                        for name in ("assert_snapshot", "assert_repeat_snapshot"))
    first, second = "a" * 32, "b" * 32
    before = [
        ".gitignore|file|same",
        ".compound-gpid/active/kilo.json|file|old",
        ".compound-gpid/projection-ownership.json|file|old",
        ".compound-gpid/projection-transaction.json|file|old",
        ".compound-gpid/managed-files.json|file|same",
        f".compound-gpid/generations/{first}|directory",
        f".compound-gpid/generations/{first}/.kilo/file.md|file|same",
        ".compound-gpid/staging|directory",
    ]
    after = [line.replace(first, second).replace("|old", "|new") for line in before]
    mode = "kilo-project"
    if case.startswith("copy-"):
        before, after, mode = ["user.txt|file|same"], ["user.txt|file|same"], "project"
        if case == "copy-change":
            after[0] = "user.txt|file|modified"
    elif case in ("user-change", "generation-content", "other-state"):
        target = {"user-change": ".gitignore", "generation-content": f".compound-gpid/generations/{second}/.kilo/file.md",
                  "other-state": ".compound-gpid/managed-files.json"}[case]
        after = [f"{target}|file|modified" if line.startswith(target + "|") else line for line in after]
    elif case == "extra-generation":
        after.append(f".compound-gpid/generations/{first}|directory")
    elif case == "staging":
        after.append(f".compound-gpid/staging/{second}|directory")
    elif case == "nested-pointer":
        after.append(".compound-gpid/active/nested/other.json|file|new")
    elif case == "pointer-link":
        after = [line.replace("kilo.json|file|new", "kilo.json|link|outside") for line in after]
    left, right = tmp_path / "before", tmp_path / "after"
    left.write_text("\n".join(before) + "\n", encoding="utf-8")
    right.write_text("\n".join(after) + "\n", encoding="utf-8")
    script = ('set -euo pipefail\nroot=$1\nstage=unit\nsnapshot_diffs=""\n' + helpers
              + '\nassert_repeat_snapshot "$2" "$3" unit "$4"\n')
    result = subprocess.run(["bash", "-c", script, "--", str(tmp_path), str(left), str(right), mode],
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == (0 if case in ("metadata", "copy-only") else 1), result.stdout + result.stderr


def test_both_update_wrappers_sync_the_exact_projection_plan() -> None:
    powershell = (REPO_ROOT / "scripts/update.ps1").read_text(encoding="utf-8")
    shell = (REPO_ROOT / "scripts/update.sh").read_text(encoding="utf-8")

    assert "Invoke-CgProjection" in powershell
    assert "-Mode sync" in powershell
    assert "cg_project_projection.py" in shell
    assert "--sync" in shell
    assert "synced and verified" in powershell
    assert "synced and verified" in shell


@pytest.mark.parametrize("name", ("link.ps1", "link.sh", "update.ps1", "update.sh"))
def test_lifecycle_preflight_is_local_only_and_note_is_nonblocking(name: str) -> None:
    """Lifecycle validation never selects host/coexistence mode or certification."""
    content = (REPO_ROOT / "scripts" / name).read_text(encoding="utf-8")
    assert "--host-only" not in content
    assert "--require-coexistence" not in content
    assert "-HostOnly" not in content
    assert "-RequireCoexistence" not in content
    assert "Certified launch required" not in content
    assert content.count("Note: Kilo and compatibility skills coexist.") == 1
    assert ".compound-gpid-managed-copy.json" in content
    if name.startswith("update"):
        assert "CG_INTERNAL_CALL" in content
    if name.endswith("ps1"):
        calls = [line for line in content.splitlines() if "Invoke-CgKiloPreflight" in line]
        assert calls and all("-LocalOnly" in line for line in calls)
    else:
        calls = [line for line in content.splitlines()
                 if "cg_kilo_preflight.py" in line and "--root" in line]
        assert calls and all("--local-only" in line for line in calls)


@pytest.mark.skipif(os.name == "nt", reason="macOS/Linux link.sh integration")
@pytest.mark.parametrize(
    ("local_config", "required_instruction", "excluded_instruction"),
    [
        (LOCAL_CONFIG, None, None),
        (
            PYTHON_LOCAL_CONFIG,
            "python.instructions.md",
            "r.instructions.md",
        ),
    ],
    ids=("both-languages", "python-only-with-advisory"),
)
def test_shell_links_fresh_manifest_driven_kilo_project(
    tmp_path: Path,
    local_config: str,
    required_instruction: str | None,
    excluded_instruction: str | None,
) -> None:
    """A fresh manifest consumer must not need manually precreated Kilo roots."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is unavailable")

    project = tmp_path / "consumer"
    profile = tmp_path / "profile"
    project.mkdir()
    profile.mkdir()
    (project / "compound-gpid.local.md").write_text(local_config, encoding="utf-8")

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
    assert "manifest projection failure" not in output
    assert "Kilo preflight (local): ok" in output
    for root_name in REQUIRED_KILO_ROOTS:
        root = project / ".kilo" / root_name
        assert root.is_dir(), f"Missing projected root: {root}\n{output}"
        assert not root.is_symlink(), f"Projected root is a symlink: {root}"
    assert (project / ".kilo/commands/cg-plan.md").is_file()
    assert (project / ".compound-gpid/active-manifest.json").is_file()
    gitignore = (project / ".gitignore").read_text(encoding="utf-8")
    ignored = {line.rstrip("/") for line in gitignore.splitlines()}
    assert ".kilo" in ignored
    assert {
        ".compound-gpid/active",
        ".compound-gpid/generations",
        ".compound-gpid/projection-ownership.json",
        ".compound-gpid/projection-transaction.json",
        ".compound-gpid/staging",
        ".compound-gpid/quarantine",
        ".compound-gpid/retired",
    } <= ignored
    assert ".compound-gpid/active-manifest.json" not in ignored
    if required_instruction is not None:
        assert (project / ".kilo/instructions" / required_instruction).is_file()
    if excluded_instruction is not None:
        assert not (project / ".kilo/instructions" / excluded_instruction).exists()


@pytest.mark.skipif(os.name == "nt", reason="macOS/Linux link.sh integration")
def test_shell_normal_link_startup_without_arguments(tmp_path: Path) -> None:
    """Empty probe arguments must be safe under macOS Bash 3.2 nounset."""
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is unavailable")
    project, profile = tmp_path / "consumer", tmp_path / "profile"
    project.mkdir()
    profile.mkdir()
    (project / "compound-gpid.local.md").write_text(LOCAL_CONFIG, encoding="utf-8")
    environment = os.environ.copy()
    environment.update({"CG_SKIP_UPDATE": "1", "HOME": str(profile)})
    result = subprocess.run(
        [bash, str(REPO_ROOT / "scripts/link.sh")],
        cwd=project, env=environment, capture_output=True, text=True,
        timeout=180, check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "unbound variable" not in output
    assert "Linked!" in output


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
