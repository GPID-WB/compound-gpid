"""Consumer-safe context discovery and strict maintainer write checks."""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple


CANONICAL_SOURCE_ORIGIN = "https://github.com/GPID-WB/compound-gpid.git"
TRUSTED_CANONICAL_ANCESTOR = "c94b6bca30a2010b020002325abf3eb2c4185db8"
PROTECTED_BRANCHES = (
    "main",
    "master",
    "develop",
    "development",
    "production",
    "stable",
)
PROTECTED_BRANCH_PREFIXES = ("release/", "hotfix/", "protected/")
_REPARSE_POINT_FLAG = 0x400


class ContextDiscoveryError(ValueError):
    """Raised when an explicit project or source root is unsafe or invalid."""


class WriteContextError(PermissionError):
    """Raised when a maintainer operation lacks strict write context."""


@dataclass(frozen=True)
class SkillManagementContext:
    """Resolved roots, role, branch, and maintainer-check diagnostics."""

    invocation_root: Optional[Path]
    project_root: Path
    source_root: Path
    role: str
    branch: Optional[str]
    write_context_errors: Tuple[str, ...]

    @property
    def can_write_canonical(self) -> bool:
        """Return whether all strict maintainer checks passed."""
        return self.role == "maintainer" and not self.write_context_errors


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _validated_root(path: Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    try:
        metadata = os.lstat(str(candidate))
    except OSError as error:
        raise ContextDiscoveryError(f"{label} does not exist: {candidate}") from error
    if _is_link_or_reparse(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise ContextDiscoveryError(
            f"{label} must be a real directory, not a link or reparse point: {candidate}"
        )
    return candidate.resolve(strict=True)


def _git(root: Path, arguments: Sequence[str]) -> Tuple[int, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name, None)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            stdin=subprocess.DEVNULL,
            env=environment,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, ""
    return result.returncode, result.stdout.strip()


def _git_root(path: Path) -> Optional[Path]:
    code, output = _git(path, ("rev-parse", "--show-toplevel"))
    if code != 0 or not output:
        return None
    try:
        return Path(output).resolve(strict=True)
    except OSError:
        return None


def _branch(root: Path) -> Optional[str]:
    code, output = _git(root, ("symbolic-ref", "--quiet", "--short", "HEAD"))
    return output if code == 0 and output else None


def _default_branch(root: Path) -> Optional[str]:
    code, output = _git(
        root, ("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    )
    if code == 0 and output:
        return output.split("/", 1)[-1]
    for candidate in ("main", "master"):
        code, _ = _git(root, ("show-ref", "--verify", "--quiet", f"refs/heads/{candidate}"))
        if code == 0:
            return candidate
    return None


def _normalized_origin(value: str) -> str:
    normalized = value.strip().rstrip("/")
    if normalized.casefold().endswith(".git"):
        normalized = normalized[:-4]
    return normalized.casefold()


def _canonical_registry_valid(root: Path) -> bool:
    path = root / ".github/shared/module-registry.json"
    try:
        metadata = os.lstat(str(path))
        if _is_link_or_reparse(metadata) or not stat.S_ISREG(metadata.st_mode):
            return False
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(registry, dict) or registry.get("schemaVersion") != 2:
        return False
    modules = registry.get("modules")
    if not isinstance(modules, list):
        return False
    module_ids = {
        module.get("id") for module in modules if isinstance(module, dict)
    }
    if not {"kernel", "cap-skill-management", "suite-cg"}.issubset(module_ids):
        return False
    try:
        import cg_validate_modules as module_validator
    except ImportError:
        return False
    errors = list(module_validator.validate_registry_schema(registry))
    errors.extend(module_validator.check_layer_rules(registry))
    errors.extend(module_validator.validate_capability_records(registry, module_ids))
    return not errors


def discover_context(
    project_root: Path,
    source_root: Optional[Path] = None,
    *,
    invocation_path: Optional[Path] = None,
    trusted_source_root: Optional[Path] = None,
) -> SkillManagementContext:
    """Resolve consumer context and elevate only a strict canonical checkout."""
    project = _validated_root(Path(project_root), "project_root")
    source = _validated_root(
        Path(source_root) if source_root is not None else project,
        "source_root",
    )
    invocation_start = _validated_root(
        Path(invocation_path) if invocation_path is not None else Path.cwd(),
        "invocation path",
    )
    git_roots = {}  # type: dict[Path, Optional[Path]]

    def cached_git_root(path: Path) -> Optional[Path]:
        key = path.resolve(strict=True)
        if key not in git_roots:
            git_roots[key] = _git_root(key)
        return git_roots[key]

    invocation = cached_git_root(invocation_start)
    errors = []  # type: list[str]
    trusted_source = None
    if trusted_source_root is None:
        errors.append("Canonical source is not bound to the running dispatcher checkout.")
    else:
        trusted_source = _validated_root(Path(trusted_source_root), "trusted source root")
        if source != trusted_source:
            errors.append("source_root must equal the running dispatcher's trusted checkout.")

    project_git_root = cached_git_root(project)
    source_git_root = cached_git_root(source)
    if invocation is None:
        errors.append("Invocation path is not inside a Git checkout.")
    if project_git_root != project:
        errors.append("project_root must be the root of its Git checkout.")
    if source_git_root != source:
        errors.append("source_root must be the root of its Git checkout.")
    if invocation != project or project != source:
        errors.append(
            "Invocation Git root, project_root, and source_root must be the same checkout."
        )
    if not _canonical_registry_valid(source):
        errors.append("Canonical module registry identity is missing or invalid.")

    origin_code, origin = _git(
        source,
        ("config", "--local", "--get", "remote.origin.url"),
    )
    if origin_code != 0 or _normalized_origin(origin) != _normalized_origin(
        CANONICAL_SOURCE_ORIGIN
    ):
        errors.append("Git origin does not match the approved canonical source origin.")

    branch = _branch(source)
    default_branch = _default_branch(source)
    if branch is None:
        errors.append("Canonical maintainer writes are forbidden from detached HEAD.")
    else:
        protected = {item.casefold() for item in PROTECTED_BRANCHES}
        if default_branch:
            protected.add(default_branch.casefold())
        if branch.casefold() in protected or any(
            branch.casefold().startswith(prefix)
            for prefix in PROTECTED_BRANCH_PREFIXES
        ):
            errors.append(
                f"Branch {branch!r} is default or protected; use a feature branch."
            )
    head_code, head = _git(source, ("rev-parse", "--verify", "HEAD^{commit}"))
    if head_code != 0 or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        errors.append("Canonical maintainer writes require a valid committed HEAD.")
    anchor_code, _ = _git(
        source,
        ("cat-file", "-e", f"{TRUSTED_CANONICAL_ANCESTOR}^{{commit}}"),
    )
    anchor_ancestry_code, _ = _git(
        source,
        ("merge-base", "--is-ancestor", TRUSTED_CANONICAL_ANCESTOR, "HEAD"),
    )
    if anchor_code != 0 or anchor_ancestry_code != 0:
        errors.append(
            "HEAD must descend from the immutable canonical trust anchor."
        )
    if default_branch is None:
        errors.append("Canonical default branch identity could not be resolved.")
    else:
        remote_default = f"refs/remotes/origin/{default_branch}"
        remote_code, remote_commit = _git(
            source,
            ("rev-parse", "--verify", f"{remote_default}^{{commit}}"),
        )
        ancestry_code, _ = _git(
            source,
            ("merge-base", "--is-ancestor", remote_default, "HEAD"),
        )
        if (
            remote_code != 0
            or not re.fullmatch(r"[0-9a-fA-F]{40}", remote_commit)
            or ancestry_code != 0
        ):
            errors.append(
                "HEAD must descend from the approved origin default-branch revision."
            )

    ordered_errors = tuple(sorted(set(errors)))
    role = "maintainer" if not ordered_errors else "consumer"
    return SkillManagementContext(
        invocation_root=invocation,
        project_root=project,
        source_root=source,
        role=role,
        branch=branch,
        write_context_errors=ordered_errors,
    )


def require_maintainer_write_context(context: SkillManagementContext) -> None:
    """Require strict maintainer authority for canonical mutation planning."""
    if context.can_write_canonical:
        return
    detail = "; ".join(context.write_context_errors) or "Role is not maintainer."
    raise WriteContextError(detail)
