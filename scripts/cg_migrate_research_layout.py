"""Created 2026-09-02. Migrate legacy CR research outputs safely."""
from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

from secure_fs import (
    ExpectedFileState,
    SecureMutationError,
    secure_delete_verified,
    secure_read_bytes,
    secure_write_bytes,
)
from research_layout import (
    LEGACY_RESEARCH_ROOT,
    LEGACY_OUTPUT_DIRECTORY_MAP,
    RESEARCH_OUTPUT_DIRECTORIES,
    RESEARCH_ROOT,
    destination_for_legacy,
)

LEGACY_PATH_MARKERS = (
    b".cg-docs/research/",
    b".cg-docs\\research\\",
    b".cg-docs\\research/",
    b".cg-docs/research\\",
)
LEGACY_DIRECTORY_NAMES = frozenset(LEGACY_OUTPUT_DIRECTORY_MAP)
AMBIGUOUS_INPUT_DIRECTORY_NAMES = frozenset(
    {"code", "data", "input", "inputs", "raw", "source", "sources"}
)
HISTORICAL_DIRECTORY_PREFIXES = (
    ".cg-docs/archive",
    ".cg-docs/brainstorms",
    ".cg-docs/plans",
    ".cg-docs/reviews",
    ".cg-docs/solutions",
    ".cg-docs/strategy",
    ".cg-docs/work-reports",
)
PRESERVED_DIRECTORY_PREFIXES = (
    ".cg-docs/competitive-reviews",
    ".cg-docs/evidence-fixtures",
    ".cg-docs/inbox",
)
GENERATED_TARGET_PREFIXES = (".agents", ".claude", ".kilo", ".opencode")
MIGRATION_TOOL_PATHS = frozenset(
    {
        "scripts/cg_migrate_research_layout.py",
        "scripts/research_layout.py",
        "scripts/tests/test_research_layout.py",
        "scripts/tests/test_update_generates_targets.py",
    }
)
SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "node_modules",
        "venv",
        "data",
    }
)


class MigrationError(RuntimeError):
    """Represent a blocked or unsafe research-layout migration."""


@dataclass(frozen=True)
class MigrationMove:
    """Describe one legacy file and its canonical destination.

    Args:
        source: Existing file below the legacy research root.
        destination: Project-relative canonical destination path.
        source_sha256: SHA-256 digest of the source bytes.
        action: ``move`` or ``skip-identical`` when the destination exists.

    Returns:
        An immutable migration move record.

    Example:
        ``MigrationMove(source, destination, digest)`` records one move.
    """

    source: Path
    destination: Path
    source_sha256: str
    action: str = "move"


@dataclass(frozen=True)
class MigrationResult:
    """Summarize one applied research-layout migration.

    Args:
        moved: Number of files copied and removed from the legacy tree.
        skipped: Number of identical destination files whose source was removed.
        removed_legacy_root: Whether the now-empty legacy root was removed.

    Returns:
        An immutable migration result.

    Example:
        ``MigrationResult(moved=2, skipped=1, removed_legacy_root=True)``.
    """

    moved: int
    skipped: int
    removed_legacy_root: bool


@dataclass(frozen=True)
class PathReference:
    """Classify one file that still contains the legacy research path marker.

    Args:
        path: File containing the legacy path marker.
        classification: ``operational``, ``historical``, or ``migration-tool``.

    Returns:
        An immutable path-reference record.

    Example:
        ``PathReference(Path("docs/workflow.md"), "operational")``.
    """

    path: Path
    classification: str


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one regular file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.

    Example:
        ``_sha256(Path("notes.md"))`` returns a 64-character digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_root(root: Path) -> Path:
    """Validate and resolve a project root for migration operations.

    Args:
        root: Candidate project root.

    Returns:
        Resolved regular project directory.

    Raises:
        MigrationError: If the root is missing, linked, or not a directory.

    Example:
        ``_validate_root(Path("."))`` returns the current project directory.
    """
    candidate = Path(root).expanduser()
    if candidate.is_symlink() or not candidate.exists() or not candidate.is_dir():
        raise MigrationError(f"Project root must be an existing regular directory: {candidate}")
    return candidate.resolve()


def _assert_no_symlink_components(path: Path, root: Path) -> None:
    """Reject symlink components between a project root and a destination.

    Args:
        path: Candidate path below ``root``.
        root: Resolved project root.

    Returns:
        ``None`` when all existing components are regular filesystem entries.

    Raises:
        MigrationError: If an existing component is a symbolic link or escapes
            the project root.

    Example:
        ``_assert_no_symlink_components(root / "c-research", root)`` validates
        the destination parent before a migration write.
    """
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise MigrationError(f"Path escapes project root: {path}") from error
    current = root
    for component in relative.parts:
        current /= component
        try:
            metadata = os.lstat(current)
        except FileNotFoundError:
            continue
        except OSError as error:
            raise MigrationError(f"Could not inspect migration path: {current}") from error
        if stat.S_ISLNK(metadata.st_mode):
            raise MigrationError(f"Migration path cannot contain a symbolic link: {current}")
        if not stat.S_ISDIR(metadata.st_mode):
            raise MigrationError(f"Migration path component is not a directory: {current}")


def _allowed_legacy_paths(root: Path, allowed_paths: tuple[Path, ...]) -> set[Path]:
    """Normalize explicitly approved non-document legacy paths."""
    legacy_root = root / LEGACY_RESEARCH_ROOT
    allowed: set[Path] = set()
    for candidate in allowed_paths:
        path = candidate if candidate.is_absolute() else root / candidate
        try:
            path.relative_to(legacy_root)
        except ValueError as error:
            raise MigrationError(
                f"Explicit migration approval must be below {legacy_root}: {candidate}"
            ) from error
        allowed.add(path)
    return allowed


def _legacy_files(root: Path, allowed_paths: tuple[Path, ...] = ()) -> list[Path]:
    """Return sorted legacy files after validating the old tree contents.

    Args:
        root: Resolved project root.

    Returns:
        Files below ``.cg-docs/research/`` sorted by project-relative path.

    Raises:
        MigrationError: If the legacy tree contains unknown directories,
            symlinks, root-level files, or unsafe paths.

    Example:
        ``_legacy_files(Path.cwd())`` inventories the old research tree.
    """
    legacy_root = root / LEGACY_RESEARCH_ROOT
    _assert_no_symlink_components(legacy_root, root)
    allowed = _allowed_legacy_paths(root, allowed_paths)
    if not legacy_root.exists():
        return []
    if not legacy_root.is_dir():
        raise MigrationError(f"Legacy research root is not a directory: {legacy_root}")

    entries = sorted(legacy_root.iterdir(), key=lambda item: item.name)
    for entry in entries:
        if entry.is_symlink():
            raise MigrationError(f"Legacy research tree contains a symbolic link: {entry}")
        if entry.is_file():
            raise MigrationError(f"Legacy research root contains an unmapped file: {entry}")
        if entry.name not in LEGACY_DIRECTORY_NAMES:
            raise MigrationError(f"Unknown legacy research directory: {entry}")

    files: list[Path] = []
    for entry in entries:
        for path in sorted(entry.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_symlink():
                raise MigrationError(f"Legacy research tree contains a symbolic link: {path}")
            if path.is_file():
                relative_parts = path.relative_to(legacy_root).parts
                if any(part in AMBIGUOUS_INPUT_DIRECTORY_NAMES for part in relative_parts[:-1]):
                    raise MigrationError(
                        f"Legacy research path is classified as input, not output: {path}"
                    )
                if path not in allowed:
                    raise MigrationError(
                        f"Legacy research file needs explicit output approval: {path}"
                    )
                files.append(path)
            elif not path.is_dir():
                raise MigrationError(f"Legacy research tree contains an unsupported entry: {path}")
    return sorted(files, key=lambda item: item.relative_to(legacy_root).as_posix())


def build_migration_plan(
    root: Path,
    *,
    allowed_paths: tuple[Path, ...] = (),
) -> list[MigrationMove]:
    """Build a conflict-checked migration plan without changing files.

    Args:
        root: Project root containing the legacy research tree.

    Returns:
        Sorted migration moves. Identical destinations are marked
        ``skip-identical`` and are safe to reconcile during apply.

    Raises:
        MigrationError: If a source or destination is unsafe, unknown, or
            contains different bytes.

    Example:
        ``moves = build_migration_plan(Path("."))`` previews the move set.
    """
    project_root = _validate_root(root)
    legacy_root = project_root / LEGACY_RESEARCH_ROOT
    moves: list[MigrationMove] = []
    for source in _legacy_files(project_root, allowed_paths):
        relative = source.relative_to(legacy_root)
        try:
            destination = project_root / destination_for_legacy(relative)
        except ValueError as error:
            raise MigrationError(str(error)) from error
        _assert_no_symlink_components(destination.parent, project_root)
        source_relative = _project_relative(source, project_root)
        try:
            source_content = secure_read_bytes(
                project_root,
                source_relative,
                reject_hardlinks=True,
            )
        except (OSError, SecureMutationError) as error:
            raise MigrationError(f"Could not read migration source: {source}") from error
        digest = hashlib.sha256(source_content).hexdigest()
        action = "move"
        if destination.is_symlink() or destination.exists():
            if destination.is_symlink() or not destination.is_file():
                raise MigrationError(f"Migration conflict at destination: {destination}")
            destination_relative = _project_relative(destination, project_root)
            try:
                destination_content = secure_read_bytes(
                    project_root,
                    destination_relative,
                    reject_hardlinks=True,
                )
            except (OSError, SecureMutationError) as error:
                raise MigrationError(
                    f"Could not read migration destination: {destination}"
                ) from error
            if hashlib.sha256(destination_content).hexdigest() != digest:
                raise MigrationError(f"Migration conflict: destination has different bytes: {destination}")
            action = "skip-identical"
        moves.append(MigrationMove(source, destination, digest, action))
    return moves


def _is_skipped_path(path: Path, root: Path) -> bool:
    """Return whether a path is inside a generated or dependency directory.

    Args:
        path: Candidate file path.
        root: Project root.

    Returns:
        ``True`` for directories excluded from operational reference scans.

    Example:
        ``_is_skipped_path(root / ".git/config", root)`` returns ``True``.
    """
    relative = path.relative_to(root)
    relative_text = relative.as_posix()
    generated_brain_file = relative_text in {
        ".cg-docs/BRAIN.md",
        ".cg-docs/BRAIN-log.md",
        ".cg-docs/brain-index.json",
    } or relative_text.startswith(".cg-docs/BRAIN-")
    generated_directory = any(
        relative_text == prefix or relative_text.startswith(prefix + "/")
        for prefix in (".cg-docs/cost", ".cg-docs/token", ".cg-docs/views")
    )
    return any(part in SKIPPED_DIRECTORY_NAMES for part in relative.parts) or generated_brain_file or generated_directory


def _reference_classification(path: Path, root: Path) -> str:
    """Return the historical or operational class for a legacy reference.

    Args:
        path: Referencing file.
        root: Project root.

    Returns:
        ``historical`` for durable process records, otherwise ``operational``.

    Example:
        ``_reference_classification(root / ".cg-docs/plans/p.md", root)``
        returns ``"historical"``.
    """
    relative = path.relative_to(root).as_posix()
    if relative in MIGRATION_TOOL_PATHS:
        return "migration-tool"
    if any(
        relative == prefix or relative.startswith(prefix + "/")
        for prefix in GENERATED_TARGET_PREFIXES
    ):
        return "generated-target"
    if any(
        relative == prefix or relative.startswith(prefix + "/")
        for prefix in PRESERVED_DIRECTORY_PREFIXES
    ):
        return "preserved"
    if any(
        relative == prefix or relative.startswith(prefix + "/")
        for prefix in HISTORICAL_DIRECTORY_PREFIXES
    ):
        return "historical"
    return "operational"


def _contains_legacy_marker(path: Path) -> bool:
    """Return whether a file contains a legacy path without loading it whole."""
    marker_length = max(len(marker) for marker in LEGACY_PATH_MARKERS)
    overlap = b""
    contains_marker = False
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                if b"\x00" in chunk:
                    return False
                haystack = overlap + chunk
                contains_marker = contains_marker or any(
                    marker in haystack for marker in LEGACY_PATH_MARKERS
                )
                overlap = haystack[-(marker_length - 1) :]
    except OSError as error:
        raise MigrationError(f"Could not read reference candidate: {path}: {error}") from error
    return contains_marker


def find_old_path_references(root: Path) -> list[PathReference]:
    """Find and classify files containing the legacy research path.

    Args:
        root: Project root to scan.

    Returns:
        Sorted path-reference records. Generated views and dependency trees are
        excluded from the scan.

    Raises:
        MigrationError: If the project root is invalid or a path cannot be
            safely classified.

    Example:
        ``find_old_path_references(Path("."))`` lists stale path consumers.
    """
    project_root = _validate_root(root)
    references: list[PathReference] = []
    for directory, directory_names, file_names in os.walk(project_root, followlinks=False):
        directory_path = Path(directory)
        directory_names[:] = [
            name
            for name in directory_names
            if not _is_skipped_path(directory_path / name, project_root)
            and not (directory_path / name).is_symlink()
        ]
        for name in sorted(file_names):
            path = directory_path / name
            if path.is_symlink() or _is_skipped_path(path, project_root):
                continue
            if _contains_legacy_marker(path):
                references.append(PathReference(path, _reference_classification(path, project_root)))
    return references


def _ensure_research_scaffold(root: Path) -> None:
    """Create the fixed c-research artifact directories after migration."""
    research_root = root / RESEARCH_ROOT
    _assert_no_symlink_components(research_root, root)
    try:
        research_root.mkdir(parents=True, exist_ok=True)
        for directory_name in RESEARCH_OUTPUT_DIRECTORIES:
            artifact_root = research_root / directory_name
            _assert_no_symlink_components(artifact_root, root)
            artifact_root.mkdir(parents=True, exist_ok=True)
            _assert_no_symlink_components(artifact_root, root)
    except OSError as error:
        raise MigrationError(f"Could not create c-research scaffold: {research_root}") from error


def _project_relative(path: Path, root: Path) -> str:
    """Return one validated project-relative POSIX path."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError as error:
        raise MigrationError(f"Migration path escapes project root: {path}") from error


def _verify_destination(root: Path, move: MigrationMove) -> None:
    """Verify that the published destination still contains the source bytes."""
    relative = _project_relative(move.destination, root)
    try:
        content = secure_read_bytes(root, relative, reject_hardlinks=True)
    except (OSError, SecureMutationError) as error:
        raise MigrationError(f"Could not verify destination: {move.destination}") from error
    if hashlib.sha256(content).hexdigest() != move.source_sha256:
        raise MigrationError(f"Migration verification failed at destination: {move.destination}")


def _delete_source_and_confirm(
    root: Path,
    move: MigrationMove,
    source_content: bytes,
) -> None:
    """Delete a source only when the published destination remains intact."""
    source_relative = _project_relative(move.source, root)
    deleted = False
    try:
        secure_delete_verified(root, source_relative, move.source_sha256)
        deleted = True
        _verify_destination(root, move)
    except (MigrationError, OSError, SecureMutationError) as error:
        if deleted:
            try:
                secure_write_bytes(
                    root,
                    Path(source_relative),
                    source_content,
                    expected_state=ExpectedFileState.absent(),
                )
            except (OSError, SecureMutationError) as restore_error:
                raise MigrationError(
                    f"Migration recovery could not restore {move.source}: "
                    f"{restore_error}"
                ) from error
        raise


def apply_migration(
    root: Path,
    *,
    allowed_paths: tuple[Path, ...] = (),
) -> MigrationResult:
    """Apply a previously conflict-checked research-layout migration.

    Args:
        root: Project root containing the legacy research tree.

    Returns:
        Counts of moved and identical files, plus legacy-root cleanup status.

    Raises:
        MigrationError: If planning fails or a copy/hash/unlink operation fails.

    Example:
        ``result = apply_migration(Path("."))`` applies an idempotent move.
    """
    project_root = _validate_root(root)
    references = find_old_path_references(project_root)
    operational = [
        reference.path
        for reference in references
        if reference.classification == "operational"
    ]
    if operational:
        paths = ", ".join(path.relative_to(project_root).as_posix() for path in operational)
        raise MigrationError(f"Operational legacy references must be updated first: {paths}")
    moves = build_migration_plan(project_root, allowed_paths=allowed_paths)
    moved = 0
    skipped = 0
    for move in moves:
        try:
            source_relative = _project_relative(move.source, project_root)
            destination_relative = _project_relative(move.destination, project_root)
            if move.action == "skip-identical":
                source_content = secure_read_bytes(
                    project_root,
                    source_relative,
                    reject_hardlinks=True,
                )
                if hashlib.sha256(source_content).hexdigest() != move.source_sha256:
                    raise MigrationError(f"Source changed before migration: {move.source}")
                _verify_destination(project_root, move)
                _delete_source_and_confirm(project_root, move, source_content)
                skipped += 1
                continue
            content = secure_read_bytes(
                project_root,
                source_relative,
                reject_hardlinks=True,
            )
            if hashlib.sha256(content).hexdigest() != move.source_sha256:
                raise MigrationError(f"Source changed before migration: {move.source}")
            secure_write_bytes(
                project_root,
                Path(destination_relative),
                content,
                expected_state=ExpectedFileState.absent(),
            )
            _verify_destination(project_root, move)
            _delete_source_and_confirm(project_root, move, content)
        except (OSError, SecureMutationError) as error:
            raise MigrationError(
                f"Could not migrate {move.source} to {move.destination}: {error}"
            ) from error
        moved += 1

    legacy_root = project_root / LEGACY_RESEARCH_ROOT
    removed_legacy_root = False
    if os.path.lexists(legacy_root):
        _assert_no_symlink_components(legacy_root, project_root)
        if not legacy_root.is_dir():
            raise MigrationError(f"Legacy research root is not a directory: {legacy_root}")
        directories = sorted(
            (path for path in legacy_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        )
        for directory in directories:
            try:
                directory.rmdir()
            except OSError as error:
                raise MigrationError(
                    f"Legacy research tree is not empty after migration: {directory}"
                ) from error
        try:
            legacy_root.rmdir()
        except OSError as error:
            raise MigrationError(f"Legacy research tree is not empty: {legacy_root}") from error
        parent = legacy_root.parent
        if parent.exists() and not any(parent.iterdir()):
            try:
                parent.rmdir()
            except OSError as error:
                raise MigrationError(f"Could not remove empty legacy parent: {parent}") from error
        removed_legacy_root = True
    _ensure_research_scaffold(project_root)
    return MigrationResult(moved, skipped, removed_legacy_root)


def main(argv: list[str] | None = None) -> int:
    """Run the migration planner or apply the migration from the command line.

    Args:
        argv: Optional command-line arguments without the executable name.

    Returns:
        Process exit code: zero for success/no-op and one for a blocked check or
        migration error.

    Example:
        ``main(["--root", ".", "--check"])`` previews a migration.
    """
    parser = argparse.ArgumentParser(description="Migrate legacy CR research outputs to c-research.")
    parser.add_argument("--root", default=".", help="Project root directory (default: .)")
    parser.add_argument(
        "--allow-output",
        action="append",
        default=[],
        help="Explicitly approve one legacy research output (project-relative path)",
    )
    parser.add_argument("--check", action="store_true", help="Report moves and stale references without writing")
    args = parser.parse_args(argv)

    try:
        root = _validate_root(Path(args.root))
        allowed_paths = tuple(Path(path) for path in args.allow_output)
        if args.check:
            moves = build_migration_plan(root, allowed_paths=allowed_paths)
            references = find_old_path_references(root)
            for move in moves:
                relative_source = move.source.relative_to(root).as_posix()
                relative_destination = move.destination.relative_to(root).as_posix()
                sys.stdout.write(f"{move.action}: {relative_source} -> {relative_destination}\n")
            for reference in references:
                relative = reference.path.relative_to(root).as_posix()
                sys.stdout.write(f"{reference.classification}-reference: {relative}\n")
            if not moves and not any(item.classification == "operational" for item in references):
                sys.stdout.write("up-to-date\n")
                return 0
            return 1

        result = apply_migration(root, allowed_paths=allowed_paths)
        sys.stdout.write(
            f"migrated: moved={result.moved}, skipped={result.skipped}, "
            f"removed_legacy_root={str(result.removed_legacy_root).lower()}\n"
        )
        return 0
    except MigrationError as error:
        sys.stderr.write(f"Error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
