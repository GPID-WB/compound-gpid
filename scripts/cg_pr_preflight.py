#!/usr/bin/env python3
"""Select and run the authoritative native CI target for a change set.

The selector is deliberately independent of pytest, PyYAML, and the Kilo host.
It can therefore be used before a commit as well as by CI after checkout.  The
only commands it executes are the native pytest target and the three existing
module-registry validators; host-dependent Kilo integration remains outside
this generic gate.

Requirements: Python 3.8+ and the standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple


PYTHON = sys.executable
ZERO_REVISION = "0" * 40
MAX_CAPTURED_OUTPUT_BYTES = 8 * 1024
MAX_KILO_RESULT_BYTES = 2 * 1024 * 1024
MAX_CACHE_REPORT_PATHS = 100
MODULE_CHECKS = ("dependencies", "cross-suite", "ownership")
GENERATED_ROOTS = (".agents", ".claude", ".kilo", ".opencode")
OWNERSHIP_MANIFEST_NAME = ".compound-gpid-generated.json"
PROJECT_IMPACT_PATHS = frozenset({
    "compound-gpid.local.md",
    ".compound-gpid/active-manifest.json",
    ".compound-gpid/project-manifest.json",
})

# This order is the release-gate order.  Do not duplicate it in a workflow.
NATIVE_PYTEST_FILES = (
    "scripts/tests/test_target_mapping.py",
    "scripts/tests/test_cg_generate_targets.py",
    "scripts/tests/test_target_path_safety.py",
    "scripts/tests/test_target_packaging.py",
    "scripts/tests/test_target_ownership.py",
    "scripts/tests/test_target_closure.py",
    "scripts/tests/test_target_determinism.py",
    "scripts/tests/test_target_drift.py",
    "scripts/tests/test_target_claude.py",
    "scripts/tests/test_target_codex.py",
    "scripts/tests/test_target_opencode.py",
    "scripts/tests/test_target_kilo.py",
    "scripts/tests/test_kilo_coexistence.py",
    "scripts/tests/test_kilo_copy.py",
    "scripts/tests/test_link_projection_order.py",
    "scripts/tests/test_copilot_skill_projection.py",
    "scripts/tests/test_project_skill_registry.py",
    "scripts/tests/test_skill_catalog.py",
    "scripts/tests/test_import_skill.py",
    "scripts/tests/test_skill_management_contracts.py",
    "scripts/tests/test_skill_management_dispatch.py",
    "scripts/tests/test_skill_management_read.py",
    "scripts/tests/test_skill_management_locking.py",
    "scripts/tests/test_skill_management_planning.py",
    "scripts/tests/test_skill_management_github_provider.py",
    "scripts/tests/test_skill_management_security.py",
    "scripts/tests/test_skill_management_config_editor.py",
    "scripts/tests/test_skill_management_project_lifecycle.py",
    "scripts/tests/test_skill_management_create.py",
    "scripts/tests/test_skill_management_vendor.py",
    "scripts/tests/test_skill_management_update.py",
    "scripts/tests/test_skill_management_audit.py",
    "scripts/tests/test_skill_management_removal.py",
    "scripts/tests/test_skill_management_release_attestation.py",
    "scripts/tests/test_skill_management_completeness.py",
    "scripts/tests/test_cg_pr_preflight.py",
    "scripts/tests/test_project_manifest.py",
    "scripts/tests/test_project_projection.py",
    "scripts/tests/test_target_documentation.py",
    "scripts/tests/test_model_advisory.py",
    "scripts/tests/test_audit_context.py",
    "scripts/tests/test_module_registry.py",
    "scripts/tests/test_context_budget.py",
    "scripts/tests/test_config_migration.py",
    "scripts/tests/test_cg_characterization.py",
    "scripts/tests/test_cr_baseline.py",
    "scripts/tests/test_issue_readiness.py",
    "scripts/tests/test_issue_dispatch.py",
    "scripts/tests/test_frontmatter_parsing.py",
    "scripts/tests/test_yaml_frontmatter_lint.py",
    "scripts/tests/test_release_policy.py",
)
NATIVE_TEST_FILES = NATIVE_PYTEST_FILES
HEAD_DRIFT_TEST = "scripts/tests/test_target_drift.py"

Command = Tuple[str, ...]
MODULE_VALIDATOR_COMMANDS = tuple(
    (PYTHON, "scripts/cg_validate_modules.py", f"--check-{check}")
    for check in MODULE_CHECKS
)


class GitSelectionError(RuntimeError):
    """Raised only when Git cannot provide a trustworthy change selection."""


class KiloResultError(ValueError):
    """Raised when a Kilo preflight result is unknown or malformed."""


@dataclass(frozen=True)
class GitResult:
    """Bounded result from one Git invocation."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Return whether the Git command succeeded."""
        return self.returncode == 0


@dataclass(frozen=True)
class ChangeSelection:
    """Impact classification and gates selected for changed paths."""

    native_required: bool = False
    generated_tree_changed: bool = False
    drift_required: bool = False
    module_checks: Tuple[str, ...] = ()
    kilo_changed: bool = False
    pester_files: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()
    categories: Tuple[str, ...] = ()

    @property
    def native_target_required(self) -> bool:
        """Compatibility alias for callers that name the gate explicitly."""
        return self.native_required

    @property
    def native_target_changed(self) -> bool:
        """Return whether a native target gate is needed."""
        return self.native_required

    @property
    def generated_changed(self) -> bool:
        """Compatibility alias for generated-tree impact."""
        return self.generated_tree_changed

    @property
    def module_required(self) -> bool:
        """Return whether module validation is needed."""
        return bool(self.module_checks)

    @property
    def module_gate_required(self) -> bool:
        """Return whether at least one module validator is selected."""
        return bool(self.module_checks)

    @property
    def kilo_required(self) -> bool:
        """Return whether a Kilo or coexistence path changed."""
        return self.kilo_changed

    @property
    def no_impact(self) -> bool:
        """Return whether the change has no native or Pester impact."""
        return not self.native_required and not self.module_checks and not self.pester_files

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe classification record."""
        return {
            "native_required": self.native_required,
            "generated_tree_changed": self.generated_tree_changed,
            "drift_required": self.drift_required,
            "module_checks": list(self.module_checks),
            "kilo_changed": self.kilo_changed,
            "pester_files": list(self.pester_files),
            "reasons": list(self.reasons),
            "categories": list(self.categories),
            "no_impact": self.no_impact,
        }


@dataclass(frozen=True)
class ChangedFilesResult:
    """Result of deriving paths from Git, including fail-closed context."""

    changed_files: Tuple[str, ...] = ()
    selection_error: Optional[str] = None
    full_gate_fallback: bool = False
    base: Optional[str] = None
    source: str = "git"

    @property
    def files(self) -> Tuple[str, ...]:
        """Compatibility alias for the normalized changed paths."""
        return self.changed_files


# A shorter name is useful to callers and keeps the public API descriptive.
ChangeDerivation = ChangedFilesResult


@dataclass(frozen=True)
class CacheReport:
    """Cache artifacts found in the repository and their severity."""

    paths: Tuple[str, ...] = ()
    tracked_paths: Tuple[str, ...] = ()
    manifest_paths: Tuple[str, ...] = ()
    local_paths: Tuple[str, ...] = ()
    fatal: bool = False
    git_error: Optional[str] = None
    path_count: int = 0
    truncated: bool = False

    @property
    def fatal_paths(self) -> Tuple[str, ...]:
        """Return the tracked or manifest-referenced paths that block CI."""
        return tuple(sorted(set(self.tracked_paths) | set(self.manifest_paths)))

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe cache report."""
        return {
            "paths": list(self.paths),
            "tracked_paths": list(self.tracked_paths),
            "manifest_paths": list(self.manifest_paths),
            "local_paths": list(self.local_paths),
            "fatal_paths": list(self.fatal_paths),
            "fatal": self.fatal,
            "git_error": self.git_error,
            "path_count": self.path_count,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class CommandResult:
    """Bounded result from one native command."""

    command: Command
    returncode: int
    stdout: str = ""
    stderr: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe command result."""
        return {
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True)
class KiloOutcome:
    """Workflow-facing Kilo outcome retaining authoritative source evidence."""

    outcome: str
    source_status: str
    exit_code: int
    message: str = ""
    remediation: str = ""
    kilo_version: Optional[str] = None
    kilo_executable: Optional[str] = None
    kilo_executable_sha256: Optional[str] = None
    certified_launch_required: bool = False
    direct_launch_supported: bool = True
    inventory: Any = field(default_factory=dict)
    containment_environment: Optional[str] = None
    host_evidence: Optional[str] = None
    evidence: Mapping[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        """Return the authoritative source status."""
        return self.source_status

    @property
    def source_payload(self) -> Mapping[str, Any]:
        """Return the original bounded Kilo result payload."""
        return self.evidence

    def as_dict(self) -> dict[str, Any]:
        """Return the mapped outcome plus the bounded source evidence."""
        return {
            "outcome": self.outcome,
            "source_status": self.source_status,
            "exit_code": self.exit_code,
            "message": self.message,
            "remediation": self.remediation,
            "kilo_version": self.kilo_version,
            "kilo_executable": self.kilo_executable,
            "kilo_executable_sha256": self.kilo_executable_sha256,
            "certified_launch_required": self.certified_launch_required,
            "direct_launch_supported": self.direct_launch_supported,
            "inventory": self.inventory,
            "containment_environment": self.containment_environment,
            "host_evidence": self.host_evidence,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class NativeRunResult:
    """Results from the ordered native pytest and module commands."""

    commands: Tuple[CommandResult, ...] = ()

    @property
    def exit_code(self) -> int:
        """Return the first nonzero command code, or zero."""
        for result in self.commands:
            if result.returncode != 0:
                return result.returncode
        return 0

    @property
    def results(self) -> Tuple[CommandResult, ...]:
        """Return command results under the commonly used plural name."""
        return self.commands


@dataclass(frozen=True)
class PreflightResult:
    """Complete bounded result for one prepare or committed preflight."""

    phase: str
    selection: ChangeSelection
    changed_files: Tuple[str, ...]
    base: Optional[str] = None
    full_gate_fallback: bool = False
    selection_error: Optional[str] = None
    cache: CacheReport = field(default_factory=CacheReport)
    native_commands: Tuple[Command, ...] = ()
    selected_commands: Tuple[Command, ...] = ()
    command_results: Tuple[CommandResult, ...] = ()
    kilo: Optional[KiloOutcome] = None

    def as_dict(self) -> dict[str, Any]:
        """Return a bounded JSON-safe result without full subprocess output."""
        native = self.native_commands or native_commands(Path("."), phase=self.phase)
        selected = self.selected_commands
        if not selected and self.selection.native_required:
            selected = native
        payload: dict[str, Any] = {
            "phase": self.phase,
            "base": self.base,
            "changed_files": list(self.changed_files),
            "full_gate_fallback": self.full_gate_fallback,
            "selection_error": self.selection_error,
            "selection": self.selection.as_dict(),
            "native_commands": [list(command) for command in native],
            "selected_commands": [list(command) for command in selected],
            "command_results": [result.as_dict() for result in self.command_results],
            "cache": self.cache.as_dict(),
            "exit_code": self.exit_code,
        }
        if self.kilo is not None:
            payload["kilo"] = self.kilo.as_dict()
        return payload

    @property
    def exit_code(self) -> int:
        """Return the result's fail-closed exit code."""
        if self.selection_error or self.cache.fatal:
            return 2
        if self.kilo is not None and self.kilo.outcome.startswith("blocking-"):
            return self.kilo.exit_code or 2
        for result in self.command_results:
            if result.returncode != 0:
                return result.returncode
        return 0

    @property
    def cache_report(self) -> CacheReport:
        """Return the cache inspection under its descriptive alias."""
        return self.cache


def _normalise_path(path: str) -> str:
    """Normalize a repository path to a relative POSIX spelling."""
    value = str(path).strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def _under(path: str, root: str) -> bool:
    """Return whether a normalized path is exactly at or under ``root``."""
    return path == root or path.startswith(root + "/")


def _is_generated(path: str) -> bool:
    """Return whether a path belongs to a committed native tree."""
    return any(_under(path, root) for root in GENERATED_ROOTS)


def _is_kilo(path: str) -> bool:
    """Return whether a path affects Kilo or adapter coexistence behavior."""
    lowered = path.casefold()
    return (
        _under(path, ".kilo")
        or "kilo" in lowered
        or _under(path, ".compound-gpid/kilo-compat-skills")
        or lowered.startswith("scripts/link")
        or lowered.startswith("scripts/unlink")
        or lowered.startswith("bin/cg-link")
        or lowered.startswith("bin/cg-unlink")
        or lowered in {"tests/link.tests.ps1", "tests/unlink.tests.ps1", "tests/parity.tests.ps1"}
    )


def _is_module_path(path: str) -> bool:
    """Return whether a path can change registry or closure validation."""
    return (
        _under(path, ".github")
        or path in {"pytest.ini", "scripts/cg_validate_modules.py"}
        or path.startswith("scripts/cg_context_budget")
        or path.startswith("scripts/cg_project_manifest")
        or path.startswith("scripts/cg_project_projection")
        or path.startswith("scripts/tests/test_module_registry.py")
        or path.startswith("scripts/tests/test_context_budget.py")
        or path.startswith("scripts/tests/test_project_manifest.py")
        or path.startswith("scripts/tests/test_project_projection.py")
        or path in PROJECT_IMPACT_PATHS
    )


def _is_native_path(path: str) -> bool:
    """Return whether a path changes the native target or its gate."""
    return (
        _is_generated(path)
        or _under(path, ".github")
        or _under(path, "scripts")
        or _under(path, "bin")
        or path == "pytest.ini"
        or path in PROJECT_IMPACT_PATHS
    )


def _pester_group(path: str) -> Optional[str]:
    """Return the safe-runner group name for one Pester test path."""
    if not path.casefold().startswith("tests/") or not path.casefold().endswith(".tests.ps1"):
        return None
    return Path(path).name[: -len(".Tests.ps1")]


def classify_changed_files(changed_files: Iterable[str]) -> ChangeSelection:
    """Classify paths into native, generated, module, Kilo, and no-impact gates.

    Args:
        changed_files: Repository-relative paths using either slash convention.

    Returns:
        A deterministic :class:`ChangeSelection` record.

    Example:
        ``classify_changed_files([".github/prompts/cg-work.prompt.md"])``
        selects the native and all module checks.
    """
    paths = tuple(sorted({_normalise_path(path) for path in changed_files if str(path).strip()}))
    native = any(_is_native_path(path) for path in paths)
    generated = any(_is_generated(path) for path in paths)
    kilo = any(_is_kilo(path) for path in paths)
    module = any(_is_module_path(path) for path in paths)
    pester = tuple(sorted(filter(None, (_pester_group(path) for path in paths))))

    reasons: list[str] = []
    if any(path.startswith(".github/prompts/") for path in paths):
        reasons.append("prompt")
    if any(path.startswith(".github/skills/") for path in paths):
        reasons.append("skill")
    if any(path.startswith(".github/agents/") for path in paths):
        reasons.append("agent")
    if any(path.startswith(".github/instructions/") for path in paths):
        reasons.append("instruction")
    if generated:
        reasons.extend(("generated-tree", "drift"))
    if module:
        reasons.append("module")
    if any(path in PROJECT_IMPACT_PATHS for path in paths):
        reasons.append("project-config")
    if kilo:
        reasons.append("kilo")
    if pester:
        reasons.append("pester")
    if native and "native" not in reasons:
        reasons.append("native")
    if not reasons:
        reasons.append("no-impact")

    categories: list[str] = []
    if native:
        categories.append("native")
    if generated:
        categories.append("generated")
    if module:
        categories.append("module")
    if kilo:
        categories.append("kilo")
    if pester:
        categories.append("pester")
    if not categories:
        categories.append("no-impact")

    return ChangeSelection(
        native_required=native,
        generated_tree_changed=generated,
        drift_required=generated,
        module_checks=MODULE_CHECKS if module else (),
        kilo_changed=kilo,
        pester_files=pester,
        reasons=tuple(dict.fromkeys(reasons)),
        categories=tuple(categories),
    )


def full_gate_selection() -> ChangeSelection:
    """Return the conservative selection used when no trustworthy diff exists."""
    return ChangeSelection(
        native_required=True,
        generated_tree_changed=True,
        drift_required=True,
        module_checks=MODULE_CHECKS,
        reasons=("full-gate",),
        categories=("native", "generated", "module", "full-gate"),
    )


def select_native_targets(changed_files: Iterable[str]) -> ChangeSelection:
    """Select native targets from changed paths."""
    return classify_changed_files(changed_files)


def select_module_checks(changed_files: Iterable[str]) -> Tuple[str, ...]:
    """Select the ordered module validation checks for changed paths."""
    return classify_changed_files(changed_files).module_checks


def resolve_base_branch(
    existing_pr_base: Optional[str] = None,
    explicit_base: Optional[str] = None,
    default_branch: Optional[str] = None,
    *,
    pr_base: Optional[str] = None,
) -> str:
    """Resolve a base using PR metadata, explicit input, then default branch.

    Empty values are treated as unavailable.  The function never consults a
    remote symbolic reference, so an unavailable base cannot silently become a
    different revision.

    Example:
        ``resolve_base_branch("release", "feature-base", "main") == "release"``
    """
    if pr_base is not None:
        existing_pr_base = pr_base
    for candidate in (existing_pr_base, explicit_base, default_branch):
        if candidate is not None and str(candidate).strip():
            return str(candidate).strip()
    raise ValueError("No PR base, explicit base, or default branch was provided")


def _run_git(root: Path, arguments: Sequence[str]) -> GitResult:
    """Run one bounded Git command in ``root``."""
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return GitResult(127, "", f"{type(exc).__name__}: {exc}")
    return GitResult(completed.returncode, completed.stdout or "", completed.stderr or "")


def git_tracked_paths(root: Path) -> set[str]:
    """Return tracked repository paths, failing closed when Git is unavailable."""
    result = _run_git(root, ("ls-files", "-z"))
    if not result.ok:
        detail = result.stderr.strip() or f"git exited with status {result.returncode}"
        raise GitSelectionError(f"git ls-files failed: {detail}")
    return {_normalise_path(path) for path in result.stdout.split("\0") if path}


def _parse_git_paths(output: str) -> Tuple[str, ...]:
    """Parse NUL- or line-delimited Git path output deterministically."""
    values = output.split("\0") if "\0" in output else output.splitlines()
    return tuple(sorted({_normalise_path(value) for value in values if value.strip()}))


def _is_zero_revision(value: Optional[str]) -> bool:
    """Return whether a Git event supplied the all-zero before revision."""
    if value is None:
        return False
    normalized = value.strip()
    return len(normalized) == 40 and set(normalized) == {"0"}


def _git_paths_or_error(root: Path, arguments: Sequence[str]) -> Tuple[Tuple[str, ...], Optional[str]]:
    """Run a Git path query and turn failures into a visible selection error."""
    result = _run_git(root, arguments)
    if not result.ok:
        detail = result.stderr.strip() or f"git exited with status {result.returncode}"
        return (), detail
    return _parse_git_paths(result.stdout), None


def derive_changed_files(
    root: Path,
    *,
    base: Optional[str] = None,
    phase: str = "committed",
    full_gate: bool = False,
    push_before: Optional[str] = None,
    before: Optional[str] = None,
) -> ChangedFilesResult:
    """Derive changed paths without falling back to an unrelated revision.

    A zero push-before SHA or explicit ``full_gate`` requests the conservative
    full gate.  Any other Git failure is returned as ``selection_error`` and is
    never converted into an empty diff.

    Example:
        ``derive_changed_files(Path.cwd(), base="main")``
    """
    if phase not in {"prepare", "committed"}:
        raise ValueError("phase must be 'prepare' or 'committed'")
    if base is None:
        base = push_before if push_before is not None else before
    if full_gate or _is_zero_revision(base):
        return ChangedFilesResult(full_gate_fallback=True, base=base, source="full-gate")
    if not base or not base.strip():
        return ChangedFilesResult(
            selection_error="No base revision was supplied; refusing to guess a Git comparison.",
            source="git",
        )

    revision = base.strip()
    # Resolve the revision before diffing.  This prevents a missing shallow
    # object from being mistaken for a valid empty comparison.
    resolved, error = _git_paths_or_error(root, ("rev-parse", "--verify", f"{revision}^{{commit}}"))
    if error:
        return ChangedFilesResult(
            selection_error=(
                f"Cannot resolve base revision {revision!r}: {error}. "
                "Fetch the base history or request an explicit full-gate fallback."
            ),
            base=revision,
        )
    if not resolved:
        # A valid rev-parse prints one SHA.  Empty output is not trustworthy.
        return ChangedFilesResult(
            selection_error=f"Git resolved base revision {revision!r} without returning a commit.",
            base=revision,
        )

    changed, error = _git_paths_or_error(
        root,
        ("diff", "--name-only", "-z", f"{revision}...HEAD"),
    )
    if error:
        return ChangedFilesResult(
            selection_error=(
                f"Cannot derive changed files against base {revision!r}: {error}. "
                "Refusing to compare a different revision."
            ),
            base=revision,
        )

    if phase == "prepare":
        # Prepare mode also sees edits not yet represented by HEAD.  Each query
        # is independent so a failure remains visible instead of being hidden
        # by a successful committed diff.
        for arguments in (
            ("diff", "--name-only", "-z"),
            ("diff", "--cached", "--name-only", "-z"),
            ("ls-files", "--others", "--exclude-standard", "-z"),
        ):
            extra, error = _git_paths_or_error(root, arguments)
            if error:
                return ChangedFilesResult(
                    selection_error=f"Cannot inspect prepare-phase changes: {error}.",
                    base=revision,
                )
            changed = tuple(sorted(set(changed) | set(extra)))

    return ChangedFilesResult(changed_files=changed, base=revision)


def _cache_like(path: str) -> bool:
    """Return whether a relative path names Python cache content."""
    normalized = _normalise_path(path)
    parts = normalized.split("/")
    return "__pycache__" in parts or normalized.casefold().endswith(".pyc")


def _filesystem_cache_paths(root: Path) -> Tuple[str, ...]:
    """Find cache files without following repository links."""
    found: set[str] = set()
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = [name for name in directories if name != ".git"]
        for filename in files:
            candidate = current_path / filename
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError:
                continue
            if _cache_like(relative):
                found.add(relative)
    return tuple(sorted(found))


def _manifest_cache_paths(root: Path) -> Tuple[str, ...]:
    """Find cache paths named by generated ownership manifests."""
    found: set[str] = set()
    manifests = sorted(root.rglob(OWNERSHIP_MANIFEST_NAME))
    for manifest in manifests:
        try:
            raw = manifest.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            # A malformed prior manifest is handled by its own validator.  If
            # it visibly contains cache content, still surface that evidence.
            candidates = re.findall(r"[^\"'\s,}]+(?:__pycache__/|\.pyc(?:\b|$))[^\"'\s,}]*", raw)
            for candidate in candidates:
                if _cache_like(candidate):
                    found.add(_normalise_path(candidate))
            continue
        if not isinstance(payload, dict):
            continue
        entries = payload.get("files", [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for key in ("path", "source"):
                value = entry.get(key)
                if isinstance(value, str) and _cache_like(value):
                    found.add(_normalise_path(value))
    return tuple(sorted(found))


def inspect_cache_artifacts(root: Path) -> CacheReport:
    """Report cache files and fail only for tracked or manifest-owned paths.

    Untracked interpreter noise is deliberately nonfatal, but remains visible
    in ``local_paths`` and ``paths`` so a caller can diagnose it.

    Example:
        ``report = inspect_cache_artifacts(Path.cwd())``
    """
    filesystem = set(_filesystem_cache_paths(root))
    manifest = set(_manifest_cache_paths(root))
    git_error: Optional[str] = None
    try:
        tracked = git_tracked_paths(root)
    except (OSError, RuntimeError) as exc:
        tracked = set()
        git_error = f"could not inspect tracked paths: {exc}"
    normalized_tracked: set[str] = set()
    for path in tracked:
        candidate = Path(path)
        if candidate.is_absolute():
            try:
                path = candidate.relative_to(root).as_posix()
            except ValueError:
                continue
        normalized_tracked.add(_normalise_path(path))

    tracked_cache = {
        path for path in filesystem | manifest if _normalise_path(path) in normalized_tracked
    }
    manifest_cache = set(manifest)
    all_paths = tuple(sorted(filesystem | manifest))
    fatal_paths = tuple(sorted(tracked_cache | manifest_cache))
    local_paths = tuple(sorted(set(all_paths) - set(fatal_paths)))
    report_paths = all_paths[:MAX_CACHE_REPORT_PATHS]
    report_local_paths = local_paths[:MAX_CACHE_REPORT_PATHS]
    return CacheReport(
        paths=report_paths,
        tracked_paths=tuple(sorted(tracked_cache)),
        manifest_paths=tuple(sorted(manifest_cache)),
        local_paths=report_local_paths,
        fatal=bool(fatal_paths) or git_error is not None,
        git_error=git_error,
        path_count=len(all_paths),
        truncated=len(all_paths) > MAX_CACHE_REPORT_PATHS,
    )


def _native_pytest_files(phase: str) -> Tuple[str, ...]:
    """Return the ordered native pytest files for one preflight phase."""
    if phase not in {"prepare", "committed"}:
        raise ValueError("phase must be 'prepare' or 'committed'")
    if phase == "committed":
        return NATIVE_PYTEST_FILES
    return tuple(path for path in NATIVE_PYTEST_FILES if path != HEAD_DRIFT_TEST)


def native_commands(root: Path, phase: str = "committed") -> Tuple[Command, ...]:
    """Return the one canonical ordered pytest command and module gates.

    ``root`` is the subprocess working directory; paths stay repository
    relative so the same command is used locally and in CI.

    Example:
        ``commands = native_commands(Path.cwd())``
    """
    pytest_files = _native_pytest_files(phase)
    pytest_command: Command = (
        PYTHON,
        "-m",
        "pytest",
        *pytest_files,
        "-m",
        "not integration",
        "-q",
    )
    return (pytest_command, *MODULE_VALIDATOR_COMMANDS)


def selected_native_commands(
    selection: ChangeSelection, root: Path, phase: str = "committed"
) -> Tuple[Command, ...]:
    """Return commands selected for an impact classification."""
    _native_pytest_files(phase)
    return native_commands(root, phase=phase) if selection.native_required else ()


def _bounded_text(value: Any, limit: int = MAX_CAPTURED_OUTPUT_BYTES) -> str:
    """Convert command output to a bounded UTF-8-safe string."""
    text = str(value or "")
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    return encoded[:limit].decode("utf-8", errors="ignore") + "\n[output truncated]"


def run_native_target(
    root: Path,
    selection: Optional[ChangeSelection] = None,
    commands: Optional[Sequence[Command]] = None,
    phase: str = "committed",
) -> NativeRunResult:
    """Execute selected native commands in order and stop on the first failure."""
    selected = selection or full_gate_selection()
    _native_pytest_files(phase)
    command_list = (
        tuple(commands)
        if commands is not None
        else selected_native_commands(selected, root, phase=phase)
    )
    results: list[CommandResult] = []
    for command in command_list:
        try:
            completed = subprocess.run(
                list(command),
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
                check=False,
            )
            result = CommandResult(
                command=command,
                returncode=completed.returncode,
                stdout=_bounded_text(completed.stdout),
                stderr=_bounded_text(completed.stderr),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            result = CommandResult(command, 127, "", _bounded_text(f"{type(exc).__name__}: {exc}"))
        results.append(result)
        if result.returncode != 0:
            break
    return NativeRunResult(tuple(results))


_KILO_STATUSES = frozenset(
    {
        "ok",
        "ok-no-coexistence",
        "missing-kilo",
        "unsupported-kilo-version",
        "local-projection-missing",
        "local-projection-invalid",
        "local-content-invalid",
        "host-command-error",
        "host-schema-error",
        "local-inventory-missing",
        "containment-unhonored",
    }
)
KILO_STATUSES = _KILO_STATUSES
_KILO_EXIT_CODES = {
    "ok": frozenset({0}),
    "ok-no-coexistence": frozenset({0}),
    "missing-kilo": frozenset({3}),
    "unsupported-kilo-version": frozenset({3}),
    "local-projection-missing": frozenset({2}),
    "local-projection-invalid": frozenset({2}),
    "local-content-invalid": frozenset({2}),
    "host-command-error": frozenset({3}),
    "host-schema-error": frozenset({5}),
    "local-inventory-missing": frozenset({5}),
    "containment-unhonored": frozenset({4}),
}


def _kilo_outcome_for(status: str) -> str:
    """Map one authoritative Kilo status to a bounded workflow outcome."""
    if status in {"missing-kilo", "unsupported-kilo-version", "ok-no-coexistence"}:
        return "generic-not-applicable"
    if status == "ok":
        return "certified-ready"
    if status == "containment-unhonored":
        return "blocking-containment"
    if status in {"local-content-invalid", "local-inventory-missing"}:
        return "blocking-content"
    return "blocking-configuration"


def adapt_kilo_result(payload: Any) -> KiloOutcome:
    """Adapt bounded ``cg_kilo_preflight.py`` JSON without changing its status.

    Unknown statuses, missing required fields, wrong field shapes, and oversized
    payloads raise :class:`KiloResultError`; none are treated as host absence.

    Example:
        ``adapt_kilo_result({"status": "missing-kilo", "exit_code": 3})``
    """
    if isinstance(payload, str):
        if len(payload.encode("utf-8", errors="replace")) > MAX_KILO_RESULT_BYTES:
            raise KiloResultError("malformed Kilo result: JSON exceeds bounded limit")
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise KiloResultError(f"malformed Kilo result JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise KiloResultError("malformed Kilo result: expected a JSON object")
    try:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise KiloResultError(f"malformed Kilo result: not JSON-safe: {exc}") from exc
    if len(encoded) > MAX_KILO_RESULT_BYTES:
        raise KiloResultError("malformed Kilo result: JSON exceeds bounded limit")

    status = payload.get("status")
    if not isinstance(status, str):
        raise KiloResultError("malformed Kilo result: status must be a string")
    if status not in _KILO_STATUSES:
        raise KiloResultError(f"unknown Kilo status: {status}")
    exit_code = payload.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise KiloResultError("malformed Kilo result: exit_code must be an integer")
    if exit_code not in _KILO_EXIT_CODES[status]:
        expected = ", ".join(str(value) for value in sorted(_KILO_EXIT_CODES[status]))
        raise KiloResultError(
            f"malformed Kilo result: status '{status}' requires exit_code {expected}"
        )

    for key in ("message", "remediation", "kilo_version", "kilo_executable", "kilo_executable_sha256", "containment_environment", "host_evidence"):
        if key in payload and payload[key] is not None and not isinstance(payload[key], str):
            raise KiloResultError(f"malformed Kilo result: {key} must be a string or null")
    for key in ("certified_launch_required", "direct_launch_supported"):
        if key in payload and not isinstance(payload[key], bool):
            raise KiloResultError(f"malformed Kilo result: {key} must be boolean")
    if status in {"ok", "ok-no-coexistence", "containment-unhonored"} and "inventory" not in payload:
        raise KiloResultError(
            f"malformed Kilo result: status '{status}' requires inventory evidence"
        )
    inventory = payload.get("inventory", {})
    if not isinstance(inventory, (dict, list)):
        raise KiloResultError("malformed Kilo result: inventory must be an object or array")
    if status == "ok":
        required = ("kilo_version", "kilo_executable", "kilo_executable_sha256")
        missing = [
            key for key in required
            if not isinstance(payload.get(key), str) or not payload[key]
        ]
        if missing:
            raise KiloResultError(
                "malformed Kilo result: certified success requires " + ", ".join(missing)
            )

    evidence = json.loads(json.dumps(payload, ensure_ascii=False))
    return KiloOutcome(
        outcome=_kilo_outcome_for(status),
        source_status=status,
        exit_code=exit_code,
        message=payload.get("message") or "",
        remediation=payload.get("remediation") or "",
        kilo_version=payload.get("kilo_version"),
        kilo_executable=payload.get("kilo_executable"),
        kilo_executable_sha256=payload.get("kilo_executable_sha256"),
        certified_launch_required=payload.get("certified_launch_required", False),
        direct_launch_supported=payload.get("direct_launch_supported", True),
        inventory=inventory,
        containment_environment=payload.get("containment_environment"),
        host_evidence=payload.get("host_evidence"),
        evidence=evidence,
    )


def adapt_kilo_json(raw: str) -> KiloOutcome:
    """Adapt one bounded JSON document emitted by the Kilo preflight."""
    return adapt_kilo_result(raw)


def load_kilo_result_file(path: Path) -> KiloOutcome:
    """Read and adapt one bounded JSON result emitted by Kilo preflight."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise KiloResultError(f"could not read Kilo result file {path}: {exc}") from exc
    if len(raw) > MAX_KILO_RESULT_BYTES:
        raise KiloResultError(
            f"malformed Kilo result: {path} exceeds {MAX_KILO_RESULT_BYTES} bytes"
        )
    try:
        return adapt_kilo_json(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise KiloResultError(f"malformed Kilo result: {path} is not UTF-8") from exc


def build_preflight_result(
    root: Path,
    *,
    phase: str = "prepare",
    base: Optional[str] = None,
    changed_files: Optional[Iterable[str]] = None,
    full_gate: bool = False,
    kilo: Optional[KiloOutcome] = None,
) -> PreflightResult:
    """Build a selection result without executing native commands."""
    if phase not in {"prepare", "committed"}:
        raise ValueError("phase must be 'prepare' or 'committed'")
    if changed_files is not None:
        normalized = tuple(sorted({_normalise_path(path) for path in changed_files if str(path).strip()}))
        selection = full_gate_selection() if full_gate else classify_changed_files(normalized)
        derivation = ChangedFilesResult(
            changed_files=normalized,
            full_gate_fallback=full_gate,
            base=base,
            source="explicit" if not full_gate else "full-gate",
        )
    else:
        derivation = derive_changed_files(root, base=base, phase=phase, full_gate=full_gate)
        if derivation.full_gate_fallback:
            selection = full_gate_selection()
        else:
            selection = classify_changed_files(derivation.changed_files)

    commands = native_commands(root, phase=phase)
    selected = selected_native_commands(selection, root, phase=phase)
    cache = inspect_cache_artifacts(root)
    return PreflightResult(
        phase=phase,
        selection=selection,
        changed_files=derivation.changed_files,
        base=derivation.base,
        full_gate_fallback=derivation.full_gate_fallback,
        selection_error=derivation.selection_error,
        cache=cache,
        native_commands=commands,
        selected_commands=selected,
        kilo=kilo,
    )


def render_result(result: PreflightResult, output_format: str = "text") -> str:
    """Render one bounded result as JSON or concise text."""
    if output_format not in {"text", "json"}:
        raise ValueError("output format must be 'text' or 'json'")
    if output_format == "json":
        return json.dumps(result.as_dict(), sort_keys=True, ensure_ascii=False)

    status = "PASS" if result.exit_code == 0 else "BLOCKED"
    lines = [f"{status}: phase={result.phase}"]
    lines.append(f"Changed files: {len(result.changed_files)}")
    if result.full_gate_fallback:
        lines.append("Selection: explicit full-gate fallback")
    if result.selection_error:
        lines.append(f"Selection error: {result.selection_error}")
    lines.append("Gates: " + (", ".join(result.selection.categories) or "no-impact"))
    if result.selection.module_checks:
        lines.append("Module checks: " + ", ".join(result.selection.module_checks))
    if result.cache.paths:
        severity = "fatal" if result.cache.fatal else "local-only"
        lines.append(f"Cache artifacts ({severity}): " + ", ".join(result.cache.paths))
        if result.cache.truncated:
            lines.append(
                f"Cache report truncated to {MAX_CACHE_REPORT_PATHS} of "
                f"{result.cache.path_count} paths."
            )
    for command_result in result.command_results:
        lines.append(f"Command {command_result.returncode}: {' '.join(command_result.command)}")
        if command_result.returncode != 0:
            if command_result.stdout:
                lines.append("Native command stdout:\n" + command_result.stdout)
            if command_result.stderr:
                lines.append("Native command stderr:\n" + command_result.stderr)
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the preflight."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--phase", choices=("prepare", "committed"), default="prepare")
    parser.add_argument("--base", help="explicit base branch, ref, or SHA")
    parser.add_argument("--pr-base", dest="existing_pr_base", help=argparse.SUPPRESS)
    parser.add_argument("--default-branch", default=os.environ.get("GITHUB_DEFAULT_BRANCH", "main"))
    parser.add_argument("--push-before", "--before", dest="push_before", help=argparse.SUPPRESS)
    parser.add_argument("--changed-file", action="append", dest="changed_files")
    parser.add_argument("--full-gate", action="store_true", help="run the conservative full gate")
    parser.add_argument("--selection-only", "--select-only", action="store_true", dest="selection_only")
    parser.add_argument("--run-native-target", action="store_true", help="execute selected native commands")
    parser.add_argument(
        "--kilo-result-json", "--kilo-result", dest="kilo_result_json",
        type=Path, help="bounded JSON result from cg_kilo_preflight.py",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run selection and, optionally, the native target."""
    args = _build_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    explicit_files = args.changed_files

    full_gate = args.full_gate
    explicit_base = args.base
    if args.push_before is not None and not args.base and not args.existing_pr_base:
        if _is_zero_revision(args.push_before):
            full_gate = True
            explicit_base = args.push_before
        else:
            explicit_base = args.push_before

    try:
        base = resolve_base_branch(args.existing_pr_base, explicit_base, args.default_branch)
    except ValueError as exc:
        base = None
        if explicit_files is None and not full_gate:
            result = build_preflight_result(
                root, phase=args.phase, base=None, changed_files=(), full_gate=False
            )
            result = replace(result, selection_error=str(exc))
            output = "json" if args.json else args.format
            sys.stdout.write(render_result(result, output) + "\n")
            return result.exit_code

    kilo = None
    kilo_error = None
    if args.kilo_result_json is not None:
        try:
            kilo = load_kilo_result_file(args.kilo_result_json)
        except KiloResultError as exc:
            kilo_error = str(exc)

    result = build_preflight_result(
        root,
        phase=args.phase,
        base=base,
        changed_files=explicit_files,
        full_gate=full_gate,
        kilo=kilo,
    )
    if kilo_error is not None:
        result = replace(result, selection_error=kilo_error)
    if args.run_native_target and not args.selection_only and result.exit_code == 0:
        run = run_native_target(root, result.selection, phase=args.phase)
        result = replace(result, command_results=run.commands)

    output = "json" if args.json else args.format
    sys.stdout.write(render_result(result, output) + "\n")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
