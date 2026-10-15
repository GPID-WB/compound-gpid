"""Released-content ownership checks in disposable Git and HOME fixtures."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

import cg_kilo_copy as kilo_copy
from scripts.tests.test_cg_link_check import (
    REPO_ROOT, _snapshot, _write, runtime, source as base_source,
)
from scripts.tests.test_install_sh import _git

TAGS = ("v1.1.10", "v1.2.0.9017")
COPY_ROOT = ".kilo/commands"
COPY_NAMES = ("cg-released.md", "cg-edited.md", "cg-created.md")
COPILOT = ".github/copilot-instructions.md"
MARKER = "<!-- compound-gpid:managed -->\n"
REAL_RELEASE_FILES = (".kilo/commands/cg-plan.md", ".kilo/agents/cg-wiki.md")


@pytest.fixture
def source(base_source: Path, tmp_path: Path) -> Path:
    """Reuse the small source fixture, with two local release commits and tags."""
    root = tmp_path / "release-source"
    shutil.copytree(base_source, root)
    home = tmp_path / "git-home"
    home.mkdir()
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith(("GIT_", "CG_", "KILO_"))}
    environment.update(
        HOME=str(home), USERPROFILE=str(home), GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
        GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
        GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
    )
    for name in COPY_NAMES:
        _write(root / COPY_ROOT / name,
               f'---\ndescription: "Ownership fixture"\n---\ncurrent {name}\n')
    for relative in REAL_RELEASE_FILES:
        _write(root / relative, (REPO_ROOT / relative).read_bytes())
    _write(root / ".github/copilot-instructions.template.md",
           "# {{project-name}}\n{{project-type}} {{languages}} {{review-depth}}\n")
    _write(root / COPILOT, MARKER + "# current source, not generated output\n")
    _write(root / ".gitattributes", ".kilo/commands/*.md text eol=lf\n")
    paths = [f"{COPY_ROOT}/{name}" for name in COPY_NAMES]
    paths.extend((*REAL_RELEASE_FILES, COPILOT))
    desired = {relative: (root / relative).read_bytes() for relative in paths}
    _git(root, "init", env=environment)
    for index, tag in enumerate(TAGS):
        for name in COPY_NAMES:
            _write(root / COPY_ROOT / name,
                   f'---\ndescription: "Ownership fixture"\n---\nrelease {index} {name}\n')
        _write(root / COPILOT, MARKER + f"# released instructions {index}\n")
        for relative in REAL_RELEASE_FILES:
            if index == 0:
                blob = subprocess.run(
                    ["git", "-C", str(REPO_ROOT), "show", f"v1.1.10:{relative}"],
                    env=environment, capture_output=True, check=True, timeout=30,
                ).stdout
                _write(root / relative, blob)
            else:
                _write(root / relative, desired[relative] + b"\nsecond release\n")
        _git(root, "-c", "core.autocrlf=false", "add", ".", env=environment)
        _git(root, "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
             "commit", "-m", f"test: release fixture {index}", env=environment)
        _git(root, "tag", tag, env=environment)
    for relative, content in desired.items():
        _write(root / relative, content)
    assert _git(root, "tag", "--list", env=environment).splitlines() == list(TAGS)
    return root


@pytest.fixture
def release_lookup(source: Path, monkeypatch: pytest.MonkeyPatch) -> tuple:
    """Observe bounded Git queries without changing their real fixture results."""
    from cg_link_ownership import ReleasedContent

    calls = []
    original = ReleasedContent._git

    def recorded(lookup: ReleasedContent, *args: str, **kwargs: bytes) -> bytes:
        calls.append(args)
        return original(lookup, *args, **kwargs)

    monkeypatch.setattr(ReleasedContent, "_git", recorded)
    return ReleasedContent(source), calls


@pytest.mark.parametrize("current,desired,previous,released,expected", (
    (None, "b" * 64, "", False, "create"),
    ("b" * 64, "b" * 64, "", False, "keep/adopt"),
    ("b" * 64, "b" * 64, "a" * 64, False, "keep/adopt"),
    ("a" * 64, "b" * 64, "a" * 64, False, "update"),
    ("a" * 64, "b" * 64, "", True, "update"),
    ("a" * 64, "b" * 64, "c" * 64, True, "update"),
    ("a" * 64, "b" * 64, "", False, "preserve/block"),
    ("c" * 64, "b" * 64, "a" * 64, False, "preserve/block"),
))
def test_file_decision_requires_content_proof(
    current: str | None, desired: str, previous: str, released: bool, expected: str,
) -> None:
    """Markers, path names and force flags are not overwrite authorization."""
    from cg_link_ownership import file_decision

    action, reason = file_decision(current, desired, previous, released=released)
    assert action == expected
    assert reason


def test_released_content_checks_all_tags_and_exact_source_path(source: Path) -> None:
    """An old blob must match the same source path, not another file or HEAD."""
    from cg_link_ownership import ReleasedContent

    released = ReleasedContent(source)
    relative = f"{COPY_ROOT}/{COPY_NAMES[0]}"
    before = _snapshot(source)
    for tag in TAGS:
        blob = _git(source, "show", f"{tag}:{relative}").encode("utf-8")
        assert released.matches(relative, blob)
        assert not released.matches(f"{COPY_ROOT}/{COPY_NAMES[1]}", blob)
        assert not released.matches(relative, blob + b"user edit\n")
    assert not released.matches(relative, (source / relative).read_bytes())
    assert _snapshot(source) == before


def test_release_lookup_is_lazy_and_indexes_tags_once(
    source: Path, tmp_path: Path, release_lookup: tuple,
) -> None:
    """Absent and identical copies need no Git; two paths share one tag index."""
    released, calls = release_lookup
    assert calls == []
    project = tmp_path / "lazy-project"
    project.mkdir()
    records = {}
    for _ in range(2):
        kilo_copy.sync_file(source, project, ".kilo/AGENTS.md", ".kilo/AGENTS.md",
                            "managed-copy", records, released)
    assert calls == []
    for name in COPY_NAMES[:2]:
        relative = f"{COPY_ROOT}/{name}"
        blob = _git(source, "show", f"{TAGS[0]}:{relative}").encode("utf-8")
        assert released.matches(relative, blob)
    assert sum(args == ("tag", "--list") for args in calls) == 1
    assert sum(args[0] == "ls-tree" for args in calls) == len(TAGS)


def test_release_lookup_respects_git_crlf_normalization(source: Path) -> None:
    """The source's .gitattributes can normalize a CRLF consumer copy to a blob."""
    from cg_link_ownership import ReleasedContent

    relative = f"{COPY_ROOT}/{COPY_NAMES[0]}"
    blob = _git(source, "show", f"{TAGS[0]}:{relative}").encode("utf-8")
    assert b"\r\n" not in blob
    assert ReleasedContent(source).matches(relative, blob.replace(b"\n", b"\r\n"))


def test_release_lookup_ignores_caller_repository_environment(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A consumer's tagged user file cannot become installation-release proof."""
    from cg_link_ownership import ReleasedContent

    consumer = tmp_path / "foreign-repository"
    consumer.mkdir()
    relative = f"{COPY_ROOT}/{COPY_NAMES[0]}"
    content = b"user content released only in the consumer repository\n"
    _write(consumer / relative, content)
    _git(consumer, "init")
    _git(consumer, "add", ".")
    _git(consumer, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
         "commit", "-m", "test: unrelated consumer tag")
    _git(consumer, "tag", "v1.0.0")
    released_bytes = _git(source, "show", f"{TAGS[0]}:{relative}").encode("utf-8")
    monkeypatch.setenv("GIT_DIR", str(consumer / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(consumer))
    monkeypatch.setenv("GIT_COMMON_DIR", str(consumer / ".git"))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(consumer / ".git/objects"))
    released = ReleasedContent(source)
    assert not released.matches(relative, content)
    assert released.matches(relative, released_bytes)


@pytest.mark.parametrize("history", ("no-tags", "not-a-repository"))
def test_release_lookup_without_history_does_not_grant_ownership(
    source: Path, tmp_path: Path, history: str,
) -> None:
    """Unavailable release history fails closed, even for previously released data."""
    from cg_link_ownership import ReleasedContent

    relative = f"{COPY_ROOT}/{COPY_NAMES[0]}"
    blob = _git(source, "show", f"{TAGS[0]}:{relative}").encode("utf-8")
    if history == "no-tags":
        _git(source, "tag", "-d", *TAGS)
    else:
        source = tmp_path / "not-a-repository"
        source.mkdir()
    assert not ReleasedContent(source).matches(relative, blob)


def test_copy_worker_updates_released_bytes_without_adopting_edits(
    source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Release proof replaces old files, creates missing files and keeps extras."""
    from cg_link_ownership import ReleasedContent

    target = tmp_path / "target"
    old = _git(source, "show", f"{TAGS[0]}:{COPY_ROOT}/{COPY_NAMES[0]}")
    edited = "user edit with no receipt\n"
    _write(target / COPY_NAMES[0], old)
    _write(target / COPY_NAMES[1], edited)
    _write(target / "extra.md", "extra user file\n")
    kilo_copy.sync_directory(source / COPY_ROOT, target, COPY_ROOT,
                             released=ReleasedContent(source))
    assert (target / COPY_NAMES[0]).read_bytes() == (
        source / COPY_ROOT / COPY_NAMES[0]).read_bytes()
    assert (target / COPY_NAMES[1]).read_text(encoding="utf-8") == edited
    assert (target / COPY_NAMES[2]).read_bytes() == (
        source / COPY_ROOT / COPY_NAMES[2]).read_bytes()
    assert (target / "extra.md").read_bytes() == b"extra user file\n"
    receipt = json.loads((target / kilo_copy.MARKER_NAME).read_text(encoding="utf-8"))
    assert receipt["files"][COPY_NAMES[0]] == hashlib.sha256(
        (target / COPY_NAMES[0]).read_bytes()).hexdigest()
    assert COPY_NAMES[1] not in receipt["files"]
    assert "extra.md" not in receipt["files"]
    assert "manual action required" in capsys.readouterr().err.lower()
    assert not any("backup" in relative for relative in _snapshot(target))


@pytest.mark.parametrize("tag", TAGS)
def test_legacy_kilo_copy_check_and_link_use_same_release_proof(
    runtime: tuple, tag: str,
) -> None:
    """A gitignore block without a receipt cannot authorize an edited overwrite."""
    project, home, env, command, source = runtime
    old_relative, edited_relative, missing_relative = (
        f"{COPY_ROOT}/{name}" for name in COPY_NAMES)
    old = _git(source, "show", f"{tag}:{old_relative}")
    edited = _git(source, "show", f"{tag}:{edited_relative}") + "user edit\n"
    _write(project / old_relative, old)
    _write(project / edited_relative, edited)
    _write(project / COPY_ROOT / "extra.md", "extra user file\n")
    _write(project / ".gitignore", "user-content/\n\n"
           "# Compound GPID managed items (legacy copied directories)\n"
           f"{COPY_ROOT}/\n")
    assert not (project / COPY_ROOT / kilo_copy.MARKER_NAME).exists()
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    check = subprocess.run([*command, "--check", "--platforms=kilo", "--yes"],
                           cwd=project, env=env, capture_output=True, text=True,
                           timeout=45, check=False)
    output = check.stdout + check.stderr
    assert check.returncode == 1, output
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    rows = {line.split(" | ")[0]: line.split(" | ") for line in output.splitlines()
            if " | " in line}
    assert rows[old_relative][3] == "update"
    assert rows[edited_relative][3] == "preserve/block"
    assert rows[missing_relative][3] == "create"
    assert edited_relative in output.split("Manual action required:", 1)[1]
    assert "UPDATE WAS CALLED" not in output
    result = subprocess.run([*command, "--platforms=kilo", "--yes"], cwd=project,
                            env=dict(env, CG_SKIP_UPDATE="1"), capture_output=True,
                            text=True, timeout=60, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert (project / old_relative).read_bytes() == (source / old_relative).read_bytes(), output
    assert (project / edited_relative).read_bytes() == edited.encode("utf-8"), output
    assert (project / missing_relative).read_bytes() == (source / missing_relative).read_bytes(), output
    assert (project / COPY_ROOT / "extra.md").read_bytes() == b"extra user file\n"
    assert "manual action required" in output.lower()
    assert edited_relative in output.replace("\\", "/")
    assert not any("backup" in relative for relative in _snapshot(project))
    assert _snapshot(source) == before[2]


@pytest.mark.parametrize("proof", (
    "identical-generated", "released", "edited-marker", "receipt", "receipt-mismatch",
))
def test_copilot_check_compares_generated_output_and_preserves_marked_edits(
    runtime: tuple, proof: str,
) -> None:
    """Use actual generation, receipt proof or the marked one-time transition."""
    project, home, env, command, source = runtime
    _write(project / "compound-gpid.md", '---\nproject-name: "Ownership fixture"\n---\n')
    link_env = dict(env, CG_SKIP_UPDATE="1")
    fresh = subprocess.run([*command, "--platforms=copilot", "--yes"], cwd=project,
                           env=link_env, capture_output=True, text=True,
                           timeout=60, check=False)
    assert fresh.returncode == 0, fresh.stdout + fresh.stderr
    desired = (project / COPILOT).read_bytes()
    assert b"Ownership fixture" in desired
    assert b"{{project-name}}" not in desired
    assert desired != (source / ".github/copilot-instructions.template.md").read_bytes()
    receipt_path = project / ".compound-gpid/managed-files.json"
    if receipt_path.exists():
        receipt_path.unlink()
    if proof.startswith("receipt"):
        previous = (MARKER + "# previous project-specific generation\n").encode("utf-8")
        _write(receipt_path, json.dumps(dict(
            schemaVersion="compound-gpid-managed-files-v1", files={COPILOT: dict(
                source=".github/copilot-instructions.template.md",
                checksum=hashlib.sha256(previous).hexdigest(),
            )},
        )))
    elif proof == "identical-generated":
        previous = desired
    else:
        previous = _git(source, "show", f"{TAGS[0]}:{COPILOT}").encode("utf-8")
    edited = proof == "receipt-mismatch"
    current = previous + (b"user edit, management marker remains\n"
                          if proof in ("edited-marker", "receipt-mismatch") else b"")
    _write(project / COPILOT, current)
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    check = subprocess.run([*command, "--check", "--platforms=copilot", "--yes"],
                           cwd=project, env=env, capture_output=True, text=True,
                           timeout=45, check=False)
    output = check.stdout + check.stderr
    assert check.returncode == int(edited), output
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    row = next(line.split(" | ") for line in output.splitlines()
               if line.startswith(COPILOT + " | "))
    expected = ("keep/adopt" if proof == "identical-generated"
                else "preserve/block" if edited else "update")
    assert row[3] == expected
    result = subprocess.run([*command, "--platforms=copilot", "--yes"], cwd=project,
                            env=link_env, capture_output=True, text=True,
                            timeout=60, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert (project / COPILOT).read_bytes() == (current if edited else desired), output
    assert (project / COPILOT).read_bytes().startswith(MARKER.encode("utf-8"))
    if edited:
        assert "manual action required" in output.lower()
        assert COPILOT in output
    backup = project / (COPILOT + ".pre-9024.bak")
    if proof in ("released", "edited-marker"):
        assert backup.read_bytes() == current
    else:
        assert not backup.exists()
    assert _snapshot(source) == before[2]


@pytest.mark.parametrize("receipt", ("absent", "empty", "malformed", "matching", "edited"))
def test_copilot_transition_then_receipt_policy(
    source: Path, tmp_path: Path, receipt: str, capsys: pytest.CaptureFixture[str],
) -> None:
    """Backup legacy bytes once, then preserve edits across refresh and unlink."""
    project = tmp_path / "copilot-policy"
    current = (MARKER + "# project-specific legacy instructions\r\n").encode("utf-8")
    previous = current
    receipt_path = project / ".compound-gpid/managed-files.json"
    if receipt in ("matching", "edited"):
        _write(receipt_path, json.dumps(dict(
            schemaVersion="compound-gpid-managed-files-v1", files={COPILOT: dict(
                source=".github/copilot-instructions.template.md",
                checksum=hashlib.sha256(previous).hexdigest(),
            )},
        )))
        if receipt == "edited":
            current += b"user edit\n"
    elif receipt in ("empty", "malformed"):
        _write(receipt_path, "" if receipt == "empty" else "{broken")
    _write(project / COPILOT, current)
    kilo_copy.copilot_action(source, project, "update")
    output = capsys.readouterr()
    backup = project / (COPILOT + ".pre-9024.bak")
    if receipt == "edited":
        assert (project / COPILOT).read_bytes() == current
        assert "manual action required" in output.err.lower()
        assert not backup.exists()
    else:
        desired = kilo_copy.generated_instructions(source, project)
        assert (project / COPILOT).read_bytes() == desired
        if receipt == "matching":
            assert not backup.exists()
        else:
            assert backup.read_bytes() == current
        if receipt in ("empty", "malformed"):
            assert "WARNING" in output.err
        records = kilo_copy.scalar_receipt(project)
        assert records[COPILOT]["checksum"] == hashlib.sha256(desired).hexdigest()
        edited = desired + b"new user edit\n"
        _write(project / COPILOT, edited)
        kilo_copy.copilot_action(source, project, "update")
        assert (project / COPILOT).read_bytes() == edited
        assert "manual action required" in capsys.readouterr().err.lower()
        current = edited
    kilo_copy.copilot_action(source, project, "unlink")
    assert (project / COPILOT).read_bytes() == current
    assert "manual action required" in capsys.readouterr().err.lower()


def test_copilot_existing_backup_and_marker_only_unlink_preserve(
    source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """An existing backup is never overwritten; marker-only deletion is refused."""
    project = tmp_path / "copilot-existing-backup"
    current = (MARKER + "legacy user bytes\n").encode("utf-8")
    backup = project / (COPILOT + ".pre-9024.bak")
    _write(project / COPILOT, current)
    _write(backup, b"previous backup bytes\n")
    kilo_copy.copilot_action(source, project, "update")
    assert (project / COPILOT).read_bytes() == current
    assert backup.read_bytes() == b"previous backup bytes\n"
    assert not kilo_copy.scalar_receipt(project)
    assert "manual action required" in capsys.readouterr().err.lower()
    kilo_copy.copilot_action(source, project, "unlink")
    assert (project / COPILOT).read_bytes() == current
    assert "manual action required" in capsys.readouterr().err.lower()


def test_copilot_unlink_deletes_only_receipt_matching_bytes(source: Path, tmp_path: Path) -> None:
    """A generated receipt supplies deletion proof, including for empty files."""
    project = tmp_path / "copilot-owned-unlink"
    project.mkdir()
    kilo_copy.copilot_action(source, project, "update")
    assert (project / COPILOT).exists()
    kilo_copy.copilot_action(source, project, "unlink")
    assert not (project / COPILOT).exists()
    assert COPILOT not in kilo_copy.scalar_receipt(project)


def test_copy_output_has_unit_totals_manual_paths_and_conditional_snippet(
    source: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Successful files are not listed, and only a kept config gets a snippet."""
    project = tmp_path / "copy-output"
    _write(project / COPY_ROOT / COPY_NAMES[1], b"user-owned command\n")
    _write(project / COPY_ROOT / "extra.md", b"user extra\n")
    _write(project / ".kilo/kilo.json", b'{"user":true}\n')
    arguments = ["--source-root", str(source), "--project-root", str(project),
                 "--directory", COPY_ROOT, COPY_ROOT,
                 "--file", ".kilo/kilo.json", ".kilo/kilo.json", "config-copy-or-snippet",
                 "--manual-snippet", ".kilo/kilo.json", "CONFIG SNIPPET"]
    assert kilo_copy.main(arguments) == 0
    output = capsys.readouterr().out
    assert f"Unit {COPY_ROOT}: create=" in output
    assert f"{COPY_ROOT}/{COPY_NAMES[0]}" not in output
    assert f"{COPY_ROOT}/{COPY_NAMES[2]}" not in output
    assert "Manual action required: 2" in output
    assert "Kilo validation deferred: 1" in output
    assert f"{COPY_ROOT}/{COPY_NAMES[1]}" in output
    assert f"{COPY_ROOT}/extra.md" in output
    assert "user file kept" in output
    assert f"{COPY_ROOT}/extra.md" not in output.split("Manual action required:", 1)[1]
    assert "CONFIG SNIPPET" in output
    _write(project / ".kilo/kilo.json", (source / ".kilo/kilo.json").read_bytes())
    assert kilo_copy.main(arguments) == 0
    output = capsys.readouterr().out
    assert "Manual action required: 1" in output
    assert "Kilo validation deferred: 1" in output
    assert "CONFIG SNIPPET" not in output


@pytest.mark.skipif(os.name == "nt", reason="POSIX ancestor symlink fixture")
def test_copy_allows_project_ancestor_alias_but_keeps_in_project_link(
    source: Path, tmp_path: Path,
) -> None:
    """Resolve the project boundary first, without resolving links inside it."""
    physical = tmp_path / "physical"
    physical.mkdir()
    alias = tmp_path / "user-folder-alias"
    alias.symlink_to(physical, target_is_directory=True)
    project = alias / "project"
    project.mkdir()
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    _write(foreign / "sentinel", b"foreign bytes\n")
    _write(project / COPY_ROOT / "existing.md", b"user bytes\n")
    (project / COPY_ROOT / COPY_NAMES[1]).symlink_to(foreign / "sentinel")
    assert kilo_copy.main([
        "--source-root", str(source), "--project-root", str(project),
        "--directory", COPY_ROOT, COPY_ROOT,
    ]) == 0
    assert (project / COPY_ROOT / COPY_NAMES[0]).read_bytes() == (
        source / COPY_ROOT / COPY_NAMES[0]).read_bytes()
    assert (project / COPY_ROOT / COPY_NAMES[1]).is_symlink()
    assert (foreign / "sentinel").read_bytes() == b"foreign bytes\n"


@pytest.mark.parametrize("proof", ("receipt", "receipt-mismatch", "no-tags"))
def test_kilo_file_requires_receipt_match_or_local_release_tag(
    runtime: tuple, proof: str,
) -> None:
    """A mismatched receipt or absent release history keeps differing bytes."""
    project, home, env, command, source = runtime
    relative = ".kilo/AGENTS.md"
    previous = b"previous adapter output, not in a release\n"
    if proof == "no-tags":
        copied_relative = f"{COPY_ROOT}/{COPY_NAMES[0]}"
        copied_old = _git(source, "show", f"{TAGS[0]}:{copied_relative}").encode("utf-8")
        _write(project / copied_relative, copied_old)
        _write(project / ".gitignore", "# Compound GPID managed items (old copy)\n"
               f"{COPY_ROOT}/\n")
        _git(source, "tag", "-d", *TAGS, env=env)
        assert _git(source, "tag", "--list", env=env) == ""
    else:
        _write(project / ".compound-gpid/managed-files.json", json.dumps(dict(
            schemaVersion="compound-gpid-managed-files-v1", files={relative: dict(
                source=relative, checksum=hashlib.sha256(previous).hexdigest(),
            )},
        )))
    blocked = proof != "receipt"
    current = previous + (b"user edit\n" if proof == "receipt-mismatch" else b"")
    _write(project / relative, current)
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    check = subprocess.run([*command, "--check", "--platforms=kilo", "--yes"],
                           cwd=project, env=env, capture_output=True, text=True,
                           timeout=45, check=False)
    output = check.stdout + check.stderr
    assert check.returncode == int(blocked), output
    row = next(line.split(" | ") for line in output.splitlines()
               if line.startswith(relative + " | "))
    assert row[3] == ("preserve/block" if blocked else "update")
    if proof == "no-tags":
        copied_row = next(line.split(" | ") for line in output.splitlines()
                          if line.startswith(copied_relative + " | "))
        assert copied_row[3] == "preserve/block"
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    result = subprocess.run([*command, "--platforms=kilo", "--yes"], cwd=project,
                            env=dict(env, CG_SKIP_UPDATE="1"), capture_output=True,
                            text=True, timeout=60, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert (project / relative).read_bytes() == (
        current if blocked else (source / relative).read_bytes()), output
    if blocked:
        assert "manual action required" in output.lower()
        assert relative in output
    if proof == "no-tags":
        assert (project / copied_relative).read_bytes() == copied_old, output
        assert not any("backup" in name for name in _snapshot(project))
    assert _snapshot(source) == before[2]


@pytest.mark.parametrize("action", ("link", "update", "unlink", "check"))
def test_unmarked_instructions_matching_install_release_are_kept(
    runtime: tuple, action: str, capsys: pytest.CaptureFixture[str],
) -> None:
    """Tagged installation instructions never prove generated consumer ownership."""
    from cg_link_ownership import ReleasedContent

    project, home, env, command, source = runtime
    current = b"# Installation's unmarked instructions, not project output\n"
    env = dict(env, PYTHONDONTWRITEBYTECODE="1")
    _write(source / COPILOT, current)
    _git(source, "add", COPILOT, env=env)
    _git(source, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
         "commit", "-m", "test: unmarked installation instructions", env=env)
    _git(source, "tag", "v1.2.0.9000", env=env)
    assert ReleasedContent(source).matches(COPILOT, current)
    _write(project / COPILOT, current)
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    if action in ("link", "check"):
        arguments = [*command, "--platforms=copilot", "--yes"]
        if action == "check":
            arguments.append("--check")
        result = subprocess.run(arguments, cwd=project, env=dict(env, CG_SKIP_UPDATE="1"),
                                capture_output=True, text=True, timeout=60, check=False)
        output = result.stdout + result.stderr
        assert result.returncode == int(action == "check"), output
        if action == "check":
            row = next(line.split(" | ") for line in output.splitlines()
                       if line.startswith(COPILOT + " | "))
            assert row[3] == "preserve/block"
            assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    else:
        kilo_copy.copilot_action(source, project, action)
        captured = capsys.readouterr()
        output = captured.out + captured.err
    assert "manual action required" in output.lower()
    assert (project / COPILOT).read_bytes() == current
    assert not (project / (COPILOT + ".pre-9024.bak")).exists()
    assert COPILOT not in kilo_copy.scalar_receipt(project)
    assert _snapshot(home) == before[1]
    assert _snapshot(source) == before[2]


@pytest.mark.parametrize("relative,platform", (
    (".github/prompts", "copilot"), (".kilo/commands", "kilo"),
))
def test_foreign_directory_link_is_preserved_even_with_yes(
    runtime: tuple, relative: str, platform: str,
) -> None:
    """Noninteractive operation cannot replace a foreign junction or symlink."""
    project, home, env, command, source = runtime
    foreign = project.parent / "foreign-prompts"
    _write(foreign / "sentinel.txt", "foreign content\n")
    destination = project / relative
    destination.parent.mkdir()
    if os.name == "nt":
        linked = subprocess.run(
            ["cmd.exe", "/c", "mklink", "/J", str(destination), str(foreign)],
            capture_output=True, text=True, check=False, timeout=30,
        )
        assert linked.returncode == 0, linked.stdout + linked.stderr
    else:
        destination.symlink_to(foreign, target_is_directory=True)
    try:
        before = (_snapshot(project), _snapshot(home), _snapshot(source), _snapshot(foreign))
        check = subprocess.run([*command, "--check", f"--platforms={platform}", "--yes"],
                               cwd=project, env=env, capture_output=True, text=True,
                               timeout=45, check=False)
        output = check.stdout + check.stderr
        assert check.returncode == 1, output
        assert "preserve/block" in next(line for line in output.splitlines()
                                         if line.startswith(relative + " | "))
        assert (_snapshot(project), _snapshot(home), _snapshot(source), _snapshot(foreign)) == before
        result = subprocess.run([*command, f"--platforms={platform}", "--yes"], cwd=project,
                                env=dict(env, CG_SKIP_UPDATE="1"), capture_output=True,
                                text=True, timeout=60, check=False)
        output = result.stdout + result.stderr
        assert result.returncode == 0, output
        assert _snapshot(project)[relative] == before[0][relative], output
        assert destination.resolve() == foreign.resolve()
        assert _snapshot(foreign) == before[3]
        assert _snapshot(source) == before[2]
        assert "manual action required" in output.lower()
        assert relative in output
    finally:
        if os.name == "nt":
            os.rmdir(destination)
        else:
            destination.unlink()


@pytest.mark.skipif(os.name == "nt", reason="Real release upgrade requires POSIX")
@pytest.mark.parametrize("relative", REAL_RELEASE_FILES)
@pytest.mark.parametrize("edited", (False, True), ids=("unedited", "edited"))
def test_posix_upgrades_real_v1_1_10_blob_without_running_old_code(
    runtime: tuple, relative: str, edited: bool,
) -> None:
    """Execute only current scripts; use git show of the real release as data."""
    project, home, env, command, source = runtime
    old = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"v1.1.10:{relative}"], env=env,
        capture_output=True, check=True, timeout=30,
    ).stdout
    local_blob = subprocess.run(
        ["git", "-C", str(source), "show", f"v1.1.10:{relative}"], env=env,
        capture_output=True, check=True, timeout=30,
    ).stdout
    assert old == local_blob
    assert old != (source / relative).read_bytes()
    current = old + (b"\nuser customization\n" if edited else b"")
    _write(project / relative, current)
    _write(project / ".gitignore", "# Compound GPID managed items (old copy)\n"
           f"{Path(relative).parent.as_posix()}/\n")
    before = (_snapshot(project), _snapshot(home), _snapshot(source))
    check = subprocess.run([*command, "--check", "--platforms=kilo", "--yes"],
                           cwd=project, env=env, capture_output=True, text=True,
                           timeout=45, check=False)
    output = check.stdout + check.stderr
    assert check.returncode == int(edited), output
    row = next(line.split(" | ") for line in output.splitlines()
               if line.startswith(relative + " | "))
    assert row[3] == ("preserve/block" if edited else "update")
    assert (_snapshot(project), _snapshot(home), _snapshot(source)) == before
    result = subprocess.run([*command, "--platforms=kilo", "--yes"], cwd=project,
                            env=dict(env, CG_SKIP_UPDATE="1"), capture_output=True,
                            text=True, timeout=60, check=False)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert (project / relative).read_bytes() == (
        current if edited else (source / relative).read_bytes()), output
    if edited:
        assert "manual action required" in output.lower()
        assert relative in output
    assert not any("backup" in name for name in _snapshot(project))
    assert _snapshot(source) == before[2]
