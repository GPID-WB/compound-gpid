"""Bash rollback edge cases in disposable Git fixtures, never real installs."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TAG = "v1.2.0.9022"
PIN_BYTES = b"\x00original pin\r\n\n"
REQUIRED = (
    "link.ps1", "link.sh", "update.ps1", "helpers.ps1",
    "cg_project_manifest.py", "cg_project_projection.py", "cg_kilo_preflight.py",
    "cg_kilo_copy.py", "cg_migrate_research_layout.py", "research_layout.py",
    "secure_fs.py",
)
GENERATOR = '''\
import os, sys
from pathlib import Path
root = Path(sys.argv[sys.argv.index("--root") + 1])
assert sys.argv[1:] == ["--root", str(root), "--all", "--dry-run"]
pin = root / ".cg-version"
if os.environ.get("BASH_ABSENT_PIN"):
    assert not pin.exists()
else:
    assert pin.read_bytes() == bytes.fromhex(os.environ["BASH_PIN_HEX"])
'''
RETIREMENT = '''\
import os, subprocess, sys
from pathlib import Path
root = Path(sys.argv[sys.argv.index("--root") + 1])
assert (root / ".cg-version").read_bytes() == b"v1.2.0.9022"
case = os.environ.get("BASH_FAILURE", "")
if case in ("carry", "staged-carry", "conflict"):
    path = root / ("common.txt" if case == "conflict" else "carry.txt")
    path.write_bytes(b"new user bytes\\n")
    if case == "staged-carry":
        subprocess.run(["git", "-C", str(root), "add", "carry.txt"], check=True)
    sys.stderr.write("fixture downstream failure\\n")
    raise SystemExit(9)
'''


@dataclass
class BashFixture:
    """A copied updater and isolated Git state, for example a failed pin write."""

    install: Path
    consumer: Path
    temporary: Path
    fake_bin: Path
    env: dict[str, str]
    git: str
    bash: str
    original: str
    target: str

    def git_run(self, *args: str) -> str:
        """Run fixture Git, e.g. git_run('rev-parse', 'HEAD')."""
        return subprocess.run(
            [self.git, "-C", str(self.install), *args], env=self.env,
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()

    def update(self) -> subprocess.CompletedProcess[str]:
        """Execute the copied updater against the explicit fixture tag."""
        return subprocess.run(
            [self.bash, str(self.install / "scripts/update.sh"), TAG],
            env=self.env, cwd=self.consumer, capture_output=True, text=True,
            check=False, timeout=30,
        )

    def assert_no_pin_temporary_files(self) -> None:
        """Check that private pin backups and publication files were removed."""
        assert not list(self.temporary.glob("cg-update-pin-*"))
        assert not list(self.install.glob(".cg-version.tmp.*"))


@pytest.fixture
def runtime(tmp_path: Path) -> BashFixture:
    """Create fixture-only refs and a utility-only PATH on Linux or macOS."""
    if not (sys.platform.startswith("linux") or sys.platform == "darwin"):
        pytest.skip("Bash updater runtime requires Linux or macOS")
    git, bash = shutil.which("git"), shutil.which("bash")
    if git is None or bash is None:
        pytest.skip("Bash and Git are required for the disposable fixture")
    install, consumer = tmp_path / "install", tmp_path / "consumer"
    home, temporary, fake_bin = (
        tmp_path / "home", tmp_path / "temporary", tmp_path / "bin",
    )
    for path in (install / "scripts", consumer, home, temporary, fake_bin):
        path.mkdir(parents=True)
    env = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith(("CG_", "KILO_", "GIT_", "PYTHON", "BASH_"))
        and key.upper() not in ("ENV", "PSMODULEPATH")
    }
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME"):
        env[name] = str(home)
    env.update(
        PATH=str(fake_bin), TEMP=str(temporary), TMP=str(temporary),
        TMPDIR=str(temporary), GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT="5",
        GIT_CONFIG_KEY_0="core.hooksPath", GIT_CONFIG_VALUE_0=str(home / "hooks"),
        GIT_CONFIG_KEY_1="commit.gpgSign", GIT_CONFIG_VALUE_1="false",
        GIT_CONFIG_KEY_2="protocol.allow", GIT_CONFIG_VALUE_2="never",
        GIT_CONFIG_KEY_3="protocol.file.allow", GIT_CONFIG_VALUE_3="always",
        GIT_CONFIG_KEY_4="core.autocrlf", GIT_CONFIG_VALUE_4="false",
        GIT_AUTHOR_NAME="Fixture", GIT_COMMITTER_NAME="Fixture",
        GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_EMAIL="fixture@example.invalid",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(install), CG_INTERNAL_CALL="1", BASH_PIN_HEX=PIN_BYTES.hex(),
    )
    for name in ("dirname", "mktemp", "cp", "mv", "rm", "grep", "head", "sed", "git"):
        utility = shutil.which(name)
        if utility is None:
            pytest.skip(f"Required fixture utility unavailable: {name}")
        (fake_bin / name).symlink_to(utility)
    python = fake_bin / "python3"
    python.write_text(
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n", encoding="utf-8",
    )
    python.chmod(0o755)
    shutil.copy2(REPO_ROOT / "scripts/update.sh", install / "scripts/update.sh")
    for name in REQUIRED:
        (install / "scripts" / name).write_text("# fixture\n", encoding="utf-8")
    # Clean fixture: actual residue recognition has separate common-helper tests.
    (install / "scripts/cg_restore_installer_wrappers.py").write_text(
        "# No old installer mutations in this fixture.\n", encoding="utf-8",
    )
    (install / "scripts/cg_generate_targets.py").write_text(GENERATOR, encoding="utf-8")
    (install / "scripts/cg_retire_native_evidence.py").write_text(RETIREMENT, encoding="utf-8")
    (install / ".gitignore").write_text(".cg-version*\n", encoding="utf-8")
    (install / "common.txt").write_text("old\n", encoding="utf-8")
    (install / "carry.txt").write_text("unchanged\n", encoding="utf-8")
    fixture = BashFixture(install, consumer, temporary, fake_bin, env, git, bash, "", "")
    fixture.git_run("init", "-b", "original")
    fixture.git_run("add", ".")
    fixture.git_run("commit", "-m", "fixture original")
    fixture.original = fixture.git_run("rev-parse", "HEAD")
    fixture.git_run("checkout", "-b", "fixture-target")
    (install / "common.txt").write_text("target\n", encoding="utf-8")
    fixture.git_run("add", "common.txt")
    fixture.git_run("commit", "-m", "fixture target")
    fixture.target = fixture.git_run("rev-parse", "HEAD")
    fixture.git_run("tag", TAG)
    fixture.git_run("remote", "add", "origin", str(install))
    fixture.git_run("checkout", "original")
    (install / ".cg-version").write_bytes(PIN_BYTES)
    return fixture


@pytest.mark.parametrize("absent", (False, True))
@pytest.mark.parametrize("operation", ("mv", "rm"))
def test_pin_operation_failure_restores_state_and_cleans_temp(
    runtime: BashFixture, absent: bool, operation: str,
) -> None:
    """Failed publication or cleanup restores original pin bytes or absence."""
    if absent:
        (runtime.install / ".cg-version").unlink()
        runtime.env["BASH_ABSENT_PIN"] = "1"
    sentinel = runtime.install / ".cg-version.tmp"
    sentinel.write_bytes(b"unowned temporary sentinel\n")
    utility = runtime.fake_bin / operation
    real_utility = shlex.quote(str(utility.resolve()))
    failure_marker = shlex.quote(str(runtime.temporary / "pin-operation-failed"))
    guard = (f'case "$2" in *cg-update-pin-*) ;; *) exec {real_utility} "$@" ;; esac\n'
             if operation == "rm" else "")
    utility.unlink()
    utility.write_text(
        f"#!/bin/sh\n{guard}if [ ! -e {failure_marker} ]; then\n"
        f"  : > {failure_marker}\n"
        f"  echo 'fixture pin {operation} failure' >&2\n  exit 7\nfi\n"
        f"exec {real_utility} \"$@\"\n",
        encoding="utf-8",
    )
    utility.chmod(0o755)
    result = runtime.update()
    assert result.returncode != 0
    assert f"fixture pin {operation} failure" in result.stderr
    assert runtime.git_run("rev-parse", "HEAD") == runtime.original
    assert runtime.git_run("symbolic-ref", "--short", "HEAD") == "original"
    pin = runtime.install / ".cg-version"
    assert not pin.exists() if absent else pin.read_bytes() == PIN_BYTES
    assert sentinel.read_bytes() == b"unowned temporary sentinel\n"
    runtime.assert_no_pin_temporary_files()


@pytest.mark.parametrize("failure", ("carry", "staged-carry"))
def test_rollback_retains_new_nonconflicting_tracked_dirt(
    runtime: BashFixture, failure: str,
) -> None:
    """Ordinary checkout restores HEAD without deleting new user bytes/index dirt."""
    runtime.env["BASH_FAILURE"] = failure
    result = runtime.update()
    assert result.returncode != 0
    assert "fixture downstream failure" in result.stderr
    assert runtime.git_run("rev-parse", "HEAD") == runtime.original
    assert runtime.git_run("symbolic-ref", "--short", "HEAD") == "original"
    assert (runtime.install / ".cg-version").read_bytes() == PIN_BYTES
    assert (runtime.install / "carry.txt").read_bytes() == b"new user bytes\n"
    status = runtime.git_run("status", "--porcelain")
    assert status.endswith("carry.txt")
    if failure == "staged-carry":
        assert runtime.git_run("show", ":carry.txt") == "new user bytes"
    runtime.assert_no_pin_temporary_files()


def test_conflicting_new_dirt_blocks_rollback_without_forced_restore(
    runtime: BashFixture,
) -> None:
    """Rollback failure preserves the target, new pin, and conflicting user bytes."""
    runtime.env["BASH_FAILURE"] = "conflict"
    result = runtime.update()
    assert result.returncode != 0
    assert "Rollback could not restore" in result.stderr
    assert "would be overwritten" in result.stderr
    assert runtime.git_run("rev-parse", "HEAD") == runtime.target
    assert (runtime.install / ".cg-version").read_bytes() == TAG.encode("ascii")
    assert (runtime.install / "common.txt").read_bytes() == b"new user bytes\n"
    runtime.assert_no_pin_temporary_files()


def test_explicit_tag_checkout_does_not_select_same_named_branch(
    runtime: BashFixture,
) -> None:
    """A same-name branch must not replace the requested explicit tag."""
    runtime.git_run("branch", TAG)
    result = runtime.update()
    assert result.returncode == 0, result.stdout + result.stderr
    assert runtime.git_run("rev-parse", "HEAD") == runtime.target
    assert runtime.git_run("rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
    assert (runtime.install / ".cg-version").read_bytes() == TAG.encode("ascii")
    assert runtime.git_run("status", "--porcelain") == ""
    runtime.assert_no_pin_temporary_files()


@pytest.mark.parametrize("failure_stage", ("target", "rollback"))
@pytest.mark.parametrize("detached", (False, True))
def test_failed_git_exit_after_successful_checkout_still_restores_state(
    runtime: BashFixture, failure_stage: str, detached: bool,
) -> None:
    """Checkout errors after Git changes state still permit exact pin restoration."""
    if detached:
        runtime.git_run("checkout", "--detach", runtime.original)
    if failure_stage == "rollback":
        runtime.env["BASH_FAILURE"] = "carry"
        failed_checkout = (f"checkout:--detach:{runtime.original}" if detached
                           else "checkout:original:")
    else:
        failed_checkout = f"checkout:--detach:refs/tags/{TAG}"
    git = runtime.fake_bin / "git"
    git.unlink()
    git.write_text(
        "#!/bin/sh\n"
        f"{shlex.quote(runtime.git)} \"$@\"\n"
        "status=$?\n"
        f'if [ "$3:$4:$5" = "{failed_checkout}" ] && '
        '[ "$status" = 0 ]; then\n'
        f"  echo 'fixture failure after {failure_stage} checkout' >&2\n  exit 7\nfi\n"
        'exit "$status"\n', encoding="utf-8",
    )
    git.chmod(0o755)
    result = runtime.update()
    assert result.returncode != 0
    assert f"fixture failure after {failure_stage} checkout" in result.stderr
    assert runtime.git_run("rev-parse", "HEAD") == runtime.original
    assert runtime.git_run("rev-parse", "--abbrev-ref", "HEAD") == (
        "HEAD" if detached else "original"
    )
    assert (runtime.install / ".cg-version").read_bytes() == PIN_BYTES
    if failure_stage == "rollback":
        assert (runtime.install / "carry.txt").read_bytes() == b"new user bytes\n"
    runtime.assert_no_pin_temporary_files()


def test_latest_guards_before_pin_and_branch_changes() -> None:
    """Latest may not discard tracked changes or write its pin before the guard."""
    source = (REPO_ROOT / "scripts/update.sh").read_text(encoding="utf-8")
    latest = source.split("# Latest mode: track main HEAD", 1)[1].split(
        "# Pinned mode: checkout a specific tag", 1,
    )[0]
    assert latest.index("refuse_tracked_changes") < latest.index("write_version_pin")
    assert latest.index("refuse_tracked_changes") < latest.index("git checkout main")
    assert "git checkout ." not in latest
    assert "git diff --cached --quiet" in source
