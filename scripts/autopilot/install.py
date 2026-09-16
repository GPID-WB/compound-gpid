"""Installed helper identity, version and code-path allowlist (Phase 5, Step 13).

The control helper resolves its code from the installation directory through
wrapper-relative launchers; the consumer project root is passed explicitly as
``--root`` and is never derived from the helper checkout. This module
validates the installed identity the helper runs under: a bounded helper
version (``SCHEMA_VERSION``), the stage contract digest, at least one
committed launcher, and an allowlisted code surface confined to the install
root with no link or hardlink aliases. It never reads the installed source
test inventory or any consumer reproduction inventory.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path, PurePosixPath
from typing import List, Optional, Set

import secure_fs
from autopilot.contracts import sha256_hex

HELPER_VERSION_REL = "SCHEMA_VERSION"
ENTRYPOINT_REL = "scripts/cg_autopilot.py"
CONTRACT_RELATIVE = ".github/shared/autopilot-stage.contract.md"
PACKAGE_INIT_REL = "scripts/autopilot/__init__.py"
SECURE_FS_REL = "scripts/secure_fs.py"
CG_SUMMARY_REL = "scripts/cg_summary.py"
LAUNCHER_CMD_REL = "bin/cg-autopilot-control.cmd"
LAUNCHER_POSIX_REL = "bin/cg-autopilot-control"
SCRIPTS_DIR_REL = "scripts"
PACKAGE_DIR_REL = "scripts/autopilot"

MAX_IDENTITY_READ_BYTES = 262144
MAX_VERSION_BYTES = 128

# The helper may import code only under these installation-relative prefixes;
# anything else is outside the allowlist and blocks helper identity.
# evidence.py imports cg_summary for test-receipt summarization, the
# artifact_views validator used by plan.py imports parsing_utils, and
# parsing_utils imports brain.utils for frontmatter parsing, so all three
# files are part of the declared import closure as well.
CODE_PATH_PREFIXES = (
    "scripts/autopilot/",
    "scripts/artifact_views/",
    "scripts/secure_fs.py",
    "scripts/cg_summary.py",
    "scripts/parsing_utils.py",
    "scripts/brain/utils.py",
)

_VERSION_TOKEN_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


def resolve_install_root() -> Path:
    """The installation directory: two levels above this module's file."""
    return Path(__file__).resolve().parents[2]


def _bounded_digest(
    root: Path, relative_path: str, problems: List[str], label: str
) -> Optional[str]:
    """Hash one identity file through pinned no-follow bounded reads."""
    try:
        raw = secure_fs.secure_read_bytes(
            root, PurePosixPath(relative_path),
            max_bytes=MAX_IDENTITY_READ_BYTES, reject_hardlinks=True,
        )
    except FileNotFoundError:
        problems.append(f"{label}-missing: {relative_path}")
        return None
    except (secure_fs.SecureMutationError, OSError) as error:
        problems.append(f"{label}-unsafe: {relative_path}: {error}")
        return None
    return sha256_hex(raw)


def read_helper_version(root: Path, problems: List[str]) -> Optional[str]:
    """Read the bounded single-line helper version token."""
    try:
        raw = secure_fs.secure_read_bytes(
            root, PurePosixPath(HELPER_VERSION_REL),
            max_bytes=MAX_VERSION_BYTES, reject_hardlinks=True,
        )
    except FileNotFoundError:
        problems.append(f"helper-version-missing: {HELPER_VERSION_REL}")
        return None
    except (secure_fs.SecureMutationError, OSError) as error:
        problems.append(f"helper-version-unsafe: {HELPER_VERSION_REL}: {error}")
        return None
    text = raw.decode("utf-8", errors="strict").strip()
    if not text or not _VERSION_TOKEN_RE.fullmatch(text):
        problems.append(
            f"helper-version-invalid: {HELPER_VERSION_REL} must be a bounded "
            "single-line version token."
        )
        return None
    return text


def _require_directory(
    root: Path, relative_path: str, problems: List[str], label: str
) -> bool:
    path = root / relative_path
    if not path.exists():
        problems.append(f"{label}-missing: {relative_path}")
        return False
    if path.is_symlink() or not path.is_dir():
        problems.append(f"{label}-unsafe: {relative_path} is not a real directory.")
        return False
    return True


def _in_prefix(relative_path: str) -> bool:
    for prefix in CODE_PATH_PREFIXES:
        if prefix.endswith("/"):
            if relative_path.startswith(prefix):
                return True
        elif relative_path == prefix:
            return True
    return False


def _resolve_module_file(root: Path, module_parts: Sequence[str]) -> Optional[str]:
    """Map an absolute module name to a scripts-relative file path, if present."""
    if not module_parts:
        return None
    relative = Path(*module_parts)
    candidates = (
        PurePosixPath(f"scripts/{relative.as_posix()}.py"),
        PurePosixPath(f"scripts/{relative.as_posix()}/__init__.py"),
    )
    for candidate in candidates:
        path = root / str(candidate)
        if path.is_file() and not path.is_symlink():
            return str(candidate)
    return None


def _import_closure(root: Path, problems: List[str]) -> Set[str]:
    """Compute the static local import closure of the helper entrypoint.

    Only repository modules under the ``scripts`` tree are followed; standard
    library and third-party imports stay out of the helper closure. Any local
    module reached by the entrypoint that resolves outside the declared
    ``CODE_PATH_PREFIXES`` allowlist is a problem, so a future import can
    never silently widen the captured-byte trust boundary.
    """
    closure: Set[str] = set()
    pending = [ENTRYPOINT_REL]
    stdlib = frozenset(getattr(sys, "stdlib_module_names", ()))
    while pending:
        relative = pending.pop()
        if relative in closure:
            continue
        closure.add(relative)
        if relative != ENTRYPOINT_REL and not _in_prefix(relative):
            problems.append(
                f"code-path-outside-allowlist: {relative} is reachable from the "
                "helper entrypoint but is not inside the declared code-path "
                "prefixes."
            )
            continue
        try:
            raw = secure_fs.secure_read_bytes(
                root, PurePosixPath(relative),
                max_bytes=MAX_IDENTITY_READ_BYTES, reject_hardlinks=True,
            )
        except (FileNotFoundError, secure_fs.SecureMutationError, OSError):
            problems.append(f"closure-read-failed: {relative}")
            continue
        try:
            tree = ast.parse(raw)
        except SyntaxError:
            problems.append(f"closure-parse-failed: {relative}")
            continue
        package_dir = "/".join(PurePosixPath(relative).parts[:-1])
        package = package_dir.replace("/", ".")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    resolved = _resolve_module_file(root, alias.name.split("."))
                    if resolved is not None:
                        pending.append(resolved)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0 and node.module:
                    base = package.split(".")
                    if node.level - 1 < len(base):
                        parts = base[: len(base) - (node.level - 1)] + node.module.split(".")
                    else:
                        parts = node.module.split(".")
                elif node.module:
                    parts = node.module.split(".")
                else:
                    continue
                if parts and parts[0] in stdlib:
                    continue
                resolved = _resolve_module_file(root, parts)
                if resolved is not None:
                    pending.append(resolved)
    return closure


def _closure_digest(root: Path, closure: Set[str], problems: List[str]) -> str:
    """Hash every module in the declared closure into one manifest digest."""
    lines: List[str] = []
    for relative in sorted(closure):
        if not _in_prefix(relative):
            continue
        try:
            raw = secure_fs.secure_read_bytes(
                root, PurePosixPath(relative),
                max_bytes=MAX_IDENTITY_READ_BYTES, reject_hardlinks=True,
            )
        except (FileNotFoundError, secure_fs.SecureMutationError, OSError):
            problems.append(f"closure-hash-failed: {relative}")
            continue
        lines.append(f"{relative}:{sha256_hex(raw)}")
    return sha256_hex("\n".join(lines).encode("utf-8"))


def _require_regular_file(
    root: Path, relative_path: str, problems: List[str], label: str
) -> bool:
    path = root / relative_path
    if not path.exists():
        problems.append(f"{label}-missing: {relative_path}")
        return False
    if path.is_symlink() or not path.is_file():
        problems.append(f"{label}-unsafe: {relative_path} is not a regular file.")
        return False
    try:
        if path.stat().st_nlink > 1:
            problems.append(
                f"{label}-hardlink: {relative_path} has multiple filesystem "
                "links; aliased helper bytes are never trusted."
            )
            return False
    except OSError as error:
        problems.append(f"{label}-unsafe: {relative_path}: {error}")
        return False
    return True


def validate_installed_layout(root: Optional[Path] = None) -> dict:
    """Validate the installed helper identity; every problem blocks helper use.

    The layout must contain the allowlisted code paths as regular
    non-hardlinked files under the installation root, the stage contract, a
    bounded helper version and at least one committed launcher. Problems are
    reported, never repaired here.
    """
    install_root = root if root is not None else resolve_install_root()
    problems: List[str] = []
    entrypoint_digest = _bounded_digest(
        install_root, ENTRYPOINT_REL, problems, "entrypoint")
    contract_digest = _bounded_digest(
        install_root, CONTRACT_RELATIVE, problems, "contract")
    _bounded_digest(install_root, PACKAGE_INIT_REL, problems, "package-init")
    _bounded_digest(install_root, SECURE_FS_REL, problems, "secure-fs")
    _require_directory(install_root, SCRIPTS_DIR_REL, problems, "scripts-dir")
    _require_directory(install_root, PACKAGE_DIR_REL, problems, "package-dir")
    version = read_helper_version(install_root, problems)
    launchers = []
    for rel, label in (
        (LAUNCHER_CMD_REL, "cmd-launcher"),
        (LAUNCHER_POSIX_REL, "posix-launcher"),
    ):
        if _require_regular_file(install_root, rel, [], label):
            launchers.append(label)
    if not launchers:
        problems.append(
            "launcher-missing: neither bin/cg-autopilot-control.cmd nor "
            "bin/cg-autopilot-control is installed."
        )
    for prefix in CODE_PATH_PREFIXES:
        if prefix.endswith("/"):
            _require_directory(install_root, prefix.rstrip("/"), problems, "code-path")
        else:
            _require_regular_file(install_root, prefix, problems, "code-path")
    closure = _import_closure(install_root, problems)
    closure_digest = _closure_digest(install_root, closure, problems)
    return {
        "problems": problems,
        "install-root": str(install_root),
        "helper-version": version,
        "contract-digest": contract_digest,
        "entrypoint-digest": entrypoint_digest,
        "launchers": launchers,
        "code-path-prefixes": list(CODE_PATH_PREFIXES),
        "closure-digest": closure_digest,
        "closure-module-count": len(closure),
    }
