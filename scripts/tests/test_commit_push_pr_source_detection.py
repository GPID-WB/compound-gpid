"""Git-backed contract tests for /cg-commit-push-pr source detection.

The command is a Markdown workflow, so this module provides a small decision
oracle for the approved Git-provenance state machine and exercises it against
real temporary repositories.
"""
from __future__ import annotations

import json
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest


MARKER = ".compound-gpid-source.json"
MAPPING = ".github/shared/target-mapping.json"
GENERATOR = "scripts/cg_generate_targets.py"
SOURCE_PATHS = (MARKER, MAPPING, GENERATOR)
REGULAR_GIT_MODES = {"100644", "100755"}
MARKER_CONTENT = '{\n  "schemaVersion": 1,\n  "kind": "compound-gpid-source"\n}\n'
ADAPTER_MAPPINGS = (
    ".github/shared/target-mapping.json",
    ".claude/shared/target-mapping.json",
    ".agents/shared/target-mapping.json",
    ".opencode/shared/target-mapping.json",
    ".kilo/shared/target-mapping.json",
)
REPO_ROOT = Path(__file__).resolve().parents[2]


class GitInspectionError(RuntimeError):
    """Raised when Git cannot provide unambiguous provenance."""


class SourceContractError(RuntimeError):
    """Raised when a detected source checkout has an incomplete contract."""


@dataclass(frozen=True)
class SourceDecision:
    """Retained source identity for one command invocation."""

    is_source: bool
    used_bootstrap: bool
    initial_head: str
    resolved_base: str


@dataclass(frozen=True)
class GitEntry:
    """One unambiguous Git tree or index entry."""

    mode: str
    object_type: str


def _git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run one Git command in a temporary repository."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if check and result.returncode != 0:
        raise GitInspectionError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result


def _write(repo: Path, relative_path: str, content: str = "fixture\n") -> Path:
    """Write one fixture file below a repository root."""
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _init_repo(tmp_path: Path) -> Path:
    """Create a repository with one neutral committed file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Source Detection Tests")
    _write(repo, "README.md")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "test: initialize fixture")
    return repo


def _commit(repo: Path, message: str) -> str:
    """Commit all fixture changes and return the new HEAD object ID."""
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _tree_entry(
    repo: Path, revision: str, relative_path: str
) -> Optional[GitEntry]:
    """Return one exact tree entry, or None when the path is absent."""
    result = _git(
        repo,
        "ls-tree",
        "--full-tree",
        revision,
        "--",
        relative_path,
    )
    lines = [line for line in result.stdout.splitlines() if line]
    if not lines:
        return None
    if len(lines) != 1 or "\t" not in lines[0]:
        raise GitInspectionError(f"ambiguous tree entry for {relative_path}")
    metadata, actual_path = lines[0].split("\t", 1)
    fields = metadata.split()
    if len(fields) != 3 or actual_path != relative_path:
        raise GitInspectionError(f"malformed tree entry for {relative_path}")
    return GitEntry(mode=fields[0], object_type=fields[1])


def _index_entry(repo: Path, relative_path: str) -> Optional[GitEntry]:
    """Return one stage-0 index entry, rejecting unresolved index states."""
    result = _git(repo, "ls-files", "--stage", "--", relative_path)
    lines = [line for line in result.stdout.splitlines() if line]
    if not lines:
        return None
    if len(lines) != 1 or "\t" not in lines[0]:
        raise GitInspectionError(f"ambiguous index entry for {relative_path}")
    metadata, actual_path = lines[0].split("\t", 1)
    fields = metadata.split()
    if len(fields) != 3 or fields[2] != "0" or actual_path != relative_path:
        raise GitInspectionError(f"non-stage-0 index entry for {relative_path}")
    object_type = _git(repo, "cat-file", "-t", fields[1]).stdout.splitlines()
    if len(object_type) != 1 or not object_type[0]:
        raise GitInspectionError(f"ambiguous index object type for {relative_path}")
    return GitEntry(mode=fields[0], object_type=object_type[0])


def _validate_marker_text(content: str) -> None:
    """Validate the exact source-marker JSON contract."""
    try:
        marker = json.loads(content)
    except json.JSONDecodeError as exc:
        raise SourceContractError("source marker is malformed JSON") from exc
    if not isinstance(marker, dict) or set(marker) != {"schemaVersion", "kind"}:
        raise SourceContractError("source marker has the wrong keys")
    if type(marker["schemaVersion"]) is not int or marker["schemaVersion"] != 1:
        raise SourceContractError("source marker has the wrong schemaVersion")
    if marker["kind"] != "compound-gpid-source":
        raise SourceContractError("source marker has the wrong kind")


def _validate_physical_regular_file(repo: Path, relative_path: str) -> None:
    """Require a physical regular file that is not a filesystem link."""
    path = repo / relative_path
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        raise SourceContractError(f"unstaged deletion: {relative_path}") from exc
    if path.is_symlink() or not stat.S_ISREG(mode):
        raise SourceContractError(f"source contract path is not regular: {relative_path}")


def classify_source(
    repo: Path, initial_head: str, resolved_base: str
) -> SourceDecision:
    """Classify and validate source identity from retained Git provenance."""
    tree_entries = {
        path: (
            _tree_entry(repo, initial_head, path),
            _tree_entry(repo, resolved_base, path),
        )
        for path in SOURCE_PATHS
    }
    index_entries = {path: _index_entry(repo, path) for path in SOURCE_PATHS}
    for relative_path in SOURCE_PATHS:
        entries = (*tree_entries[relative_path], index_entries[relative_path])
        for entry in entries:
            if entry is not None and (
                entry.mode not in REGULAR_GIT_MODES or entry.object_type != "blob"
            ):
                raise SourceContractError(
                    f"non-regular Git entry for {relative_path}: "
                    f"{entry.mode} {entry.object_type}"
                )
    evidence = {
        path: index_entries[path] is not None
        or any(entry is not None for entry in tree_entries[path])
        for path in SOURCE_PATHS
    }
    marker_evidence = evidence[MARKER]
    bootstrap_evidence = evidence[MAPPING] and evidence[GENERATOR]
    is_source = marker_evidence or bootstrap_evidence
    decision = SourceDecision(
        is_source=is_source,
        used_bootstrap=bootstrap_evidence and not marker_evidence,
        initial_head=initial_head,
        resolved_base=resolved_base,
    )
    if not is_source:
        return decision

    for relative_path in (MAPPING, GENERATOR):
        entry = index_entries[relative_path]
        if entry is None:
            raise SourceContractError(f"staged deletion: {relative_path}")

    marker_index = index_entries[MARKER]
    if marker_index is None:
        if not decision.used_bootstrap:
            raise SourceContractError(f"staged deletion: {MARKER}")
        status_result = _git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            MARKER,
        )
        if status_result.stdout.strip() != f"?? {MARKER}":
            raise SourceContractError("bootstrap marker is not exactly untracked")

    for relative_path in SOURCE_PATHS:
        _validate_physical_regular_file(repo, relative_path)
    _validate_marker_text((repo / MARKER).read_text(encoding="utf-8"))
    return decision


def run_committed_gate(repo: Path, decision: SourceDecision) -> str:
    """Apply the post-commit gate using only the retained source decision."""
    if not decision.is_source:
        return "skipped"
    committed_head = _git(repo, "rev-parse", "--verify", "HEAD^{commit}").stdout.strip()
    for relative_path in SOURCE_PATHS:
        entry = _tree_entry(repo, committed_head, relative_path)
        if entry is None:
            raise SourceContractError(f"committed HEAD is missing {relative_path}")
        if entry.mode not in REGULAR_GIT_MODES or entry.object_type != "blob":
            raise SourceContractError(f"committed HEAD has non-regular {relative_path}")
    marker = _git(repo, "show", f"{committed_head}:{MARKER}").stdout
    _validate_marker_text(marker)
    return "ran"


def _add_complete_source(repo: Path, *, commit: bool = True) -> str:
    """Add the three canonical source paths and optionally commit them."""
    _write(repo, MARKER, MARKER_CONTENT)
    _write(repo, MAPPING, "{}\n")
    _write(repo, GENERATOR, "# fixture generator\n")
    if commit:
        return _commit(repo, "test: add source contract")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def test_repository_marker_has_exact_pretty_json() -> None:
    assert (REPO_ROOT / MARKER).read_text(encoding="utf-8") == MARKER_CONTENT


def test_canonical_prompt_has_no_path_existence_classifier_or_consumer_python_dependency() -> None:
    prompt = (REPO_ROOT / ".github/prompts/cg-commit-push-pr.prompt.md").read_text(
        encoding="utf-8"
    )
    step = prompt.split("### Step 1.5: Regenerate Platform Trees", 1)[1].split(
        "### Step 2: Analyze Changes", 1
    )[0]
    normalized_step = " ".join(step.split())

    assert (
        "Git absence and physical worktree presence cannot coexist" in normalized_step
    )
    assert "can never make a Git-absent path present" in normalized_step
    assert "Check if `.github/shared/target-mapping.json` exists" not in step
    assert step.index("If `$isCompoundGpidSource` is false") < step.index(
        "Resolve a working Python command"
    )


def test_complete_source_is_detected_from_initial_head(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)

    decision = classify_source(repo, initial_head, initial_head)

    assert decision.is_source is True
    assert decision.used_bootstrap is False


def test_staged_marker_is_source_evidence(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, MAPPING, "{}\n")
    _write(repo, GENERATOR, "# fixture generator\n")
    base = _commit(repo, "test: add legacy source contract")
    _write(repo, MARKER, MARKER_CONTENT)
    _git(repo, "add", MARKER)

    decision = classify_source(repo, base, base)

    assert decision.is_source is True
    assert decision.used_bootstrap is False


def test_initial_untracked_marker_bootstrap_is_supported(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, MAPPING, "{}\n")
    _write(repo, GENERATOR, "# fixture generator\n")
    initial_head = _commit(repo, "test: add legacy source contract")
    _write(repo, MARKER, MARKER_CONTENT)

    decision = classify_source(repo, initial_head, initial_head)

    assert decision.is_source is True
    assert decision.used_bootstrap is True


@pytest.mark.parametrize("missing_path", [MARKER, MAPPING, GENERATOR])
def test_unstaged_source_contract_deletion_halts(
    tmp_path: Path, missing_path: str
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    (repo / missing_path).unlink()

    with pytest.raises(SourceContractError, match="unstaged deletion"):
        classify_source(repo, initial_head, initial_head)


@pytest.mark.parametrize("missing_path", [MARKER, MAPPING, GENERATOR])
def test_staged_source_contract_deletion_halts(
    tmp_path: Path, missing_path: str
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    _git(repo, "rm", missing_path)

    with pytest.raises(SourceContractError, match="staged deletion"):
        classify_source(repo, initial_head, initial_head)


@pytest.mark.parametrize("missing_path", [MARKER, MAPPING, GENERATOR])
def test_cached_deletion_halts_when_worktree_file_remains(
    tmp_path: Path, missing_path: str
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    _git(repo, "rm", "--cached", missing_path)

    assert (repo / missing_path).is_file()
    with pytest.raises(SourceContractError, match="staged deletion"):
        classify_source(repo, initial_head, initial_head)


@pytest.mark.parametrize("linked_path", [MARKER, MAPPING, GENERATOR])
@pytest.mark.parametrize("provenance", ["index", "committed"])
def test_link_mode_source_contract_entry_halts_before_use(
    tmp_path: Path,
    linked_path: str,
    provenance: str,
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    blob = _git(repo, "hash-object", "-w", linked_path).stdout.strip()
    _git(repo, "update-index", "--cacheinfo", "120000", blob, linked_path)
    if provenance == "committed":
        _git(repo, "commit", "-m", "test: add source-contract link mode")
        initial_head = _git(repo, "rev-parse", "HEAD").stdout.strip()

    with pytest.raises(SourceContractError, match="120000.*blob"):
        classify_source(repo, initial_head, initial_head)


@pytest.mark.parametrize(
    "content",
    [
        "{not-json}\n",
        '{"schemaVersion": 1, "kind": "wrong"}\n',
        '{"schemaVersion": 1, "kind": "compound-gpid-source", "extra": true}\n',
    ],
)
def test_malformed_or_invalid_marker_halts(tmp_path: Path, content: str) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    _write(repo, MARKER, content)

    with pytest.raises(SourceContractError, match="source marker"):
        classify_source(repo, initial_head, initial_head)


@pytest.mark.parametrize("adapter_mapping", ADAPTER_MAPPINGS)
def test_copied_adapter_mapping_does_not_identify_source(
    tmp_path: Path, adapter_mapping: str
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _write(repo, adapter_mapping, "{}\n")

    decision = classify_source(repo, initial_head, initial_head)

    assert decision.is_source is False


def test_tracked_adapter_mapping_alone_does_not_identify_source(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, ".kilo/shared/target-mapping.json", "{}\n")
    initial_head = _commit(repo, "test: add consumer adapter mapping")

    decision = classify_source(repo, initial_head, initial_head)

    assert decision.is_source is False


def test_link_mode_canonical_mapping_halts_instead_of_classifying_consumer(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    link_placeholder = _write(repo, MAPPING, "../../../installed/target-mapping.json\n")
    blob = _git(repo, "hash-object", "-w", str(link_placeholder)).stdout.strip()
    _git(repo, "update-index", "--add", "--cacheinfo", "120000", blob, MAPPING)
    _git(repo, "commit", "-m", "test: add linked consumer mapping")
    initial_head = _git(repo, "rev-parse", "HEAD").stdout.strip()

    with pytest.raises(SourceContractError, match="120000.*blob"):
        classify_source(repo, initial_head, initial_head)


def test_manifest_projected_adapter_mappings_do_not_identify_source(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    for adapter_mapping in ADAPTER_MAPPINGS:
        _write(repo, adapter_mapping, "{}\n")
    _write(
        repo,
        ".compound-gpid/managed-files.json",
        '{"schemaVersion":"compound-gpid-managed-files-v1","files":{}}\n',
    )
    initial_head = _commit(repo, "test: add projected consumer adapters")

    decision = classify_source(repo, initial_head, initial_head)

    assert decision.is_source is False


def test_untracked_marker_does_not_identify_ordinary_consumer(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _write(repo, MARKER, MARKER_CONTENT)

    decision = classify_source(repo, initial_head, initial_head)

    assert decision.is_source is False


def test_marker_evidence_with_missing_contract_halts(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _write(repo, MARKER, MARKER_CONTENT)
    initial_head = _commit(repo, "test: add incomplete source marker")

    with pytest.raises(SourceContractError, match="staged deletion"):
        classify_source(repo, initial_head, initial_head)


def test_base_provenance_retains_source_identity_after_contract_removal(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    source_base = _add_complete_source(repo)
    for relative_path in SOURCE_PATHS:
        (repo / relative_path).unlink()
    initial_head = _commit(repo, "test: remove source contract")

    with pytest.raises(SourceContractError, match="staged deletion"):
        classify_source(repo, initial_head, source_base)


def test_git_inspection_ambiguity_halts(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _git(repo, "rev-parse", "HEAD").stdout.strip()

    with pytest.raises(GitInspectionError):
        classify_source(repo, initial_head, "refs/heads/does-not-exist")


def test_source_decision_is_retained_when_post_commit_contract_is_deleted(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    decision = classify_source(repo, initial_head, initial_head)
    for relative_path in SOURCE_PATHS:
        (repo / relative_path).unlink()
    _commit(repo, "test: remove source contract after classification")

    with pytest.raises(SourceContractError, match="committed HEAD is missing"):
        run_committed_gate(repo, decision)


def test_consumer_decision_is_retained_after_post_classification_source_commit(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    decision = classify_source(repo, initial_head, initial_head)
    _add_complete_source(repo)

    assert run_committed_gate(repo, decision) == "skipped"


def test_committed_gate_requires_valid_committed_marker(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    initial_head = _add_complete_source(repo)
    decision = classify_source(repo, initial_head, initial_head)
    _write(repo, MARKER, "{not-json}\n")
    _commit(repo, "test: corrupt committed marker")

    with pytest.raises(SourceContractError, match="malformed JSON"):
        run_committed_gate(repo, decision)
