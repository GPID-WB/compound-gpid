#!/usr/bin/env python3
"""Synchronize one Kilo copy-directory unit without following links."""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
from typing import Optional

try:
    import secure_fs
except ImportError:  # pragma: no cover - direct script execution path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import secure_fs

from cg_link_ownership import ReleasedContent, copilot_decision, file_decision


MARKER_NAME = ".compound-gpid-managed-copy.json"
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
# Keep aligned with cg_kilo_preflight.REQUIRED_LOCAL_ROOTS without a host dependency.
VALIDATED_KILO_ROOTS = (
    ".kilo/commands", ".kilo/skills", ".kilo/agents",
    ".kilo/instructions", ".kilo/shared",
)


class CopyError(RuntimeError):
    """Raised when a copy-directory mutation cannot be proven safe."""


def _is_link(path: Path) -> bool:
    """Return whether ``path`` is a real symlink or Windows junction."""
    if path.is_symlink():
        return True
    try:
        return getattr(path.lstat(), "st_reparse_tag", 0) in (0xA000000C, 0xA0000003)
    except OSError:
        return False


def _ensure_directory(path: Path, root: Path | None = None) -> None:
    """Check components inside a resolved root, not the user's parent aliases."""
    lexical_root = root or path.parent
    relative = path.relative_to(lexical_root)
    root = lexical_root.resolve()
    path = root / relative
    if path.exists() and _is_link(path):
        raise CopyError(f"refusing to use a link or reparse directory: {path}")
    current = path
    while True:
        if _is_link(current):
            raise CopyError(f"refusing to use a link or reparse directory: {current}")
        if current.exists() and not current.is_dir():
            raise CopyError(f"copy destination component is not a directory: {current}")
        parent = current.parent
        if current == root:
            break
        current = parent
    path.mkdir(parents=True, exist_ok=True)


def _read_marker(target: Path, source_relative: str) -> Optional[dict[str, str]]:
    """Read a valid ownership marker; invalid markers disable stale deletion."""
    marker = target / MARKER_NAME
    if not marker.exists():
        return None
    if _is_link(marker):
        raise CopyError(f"refusing to read a link or reparse marker: {marker}")
    try:
        data = json.loads(marker.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        return None
    if data.get("source") != source_relative or not isinstance(data.get("files"), dict):
        return None
    result: dict[str, str] = {}
    for relative, checksum in data["files"].items():
        relative_text = str(relative).replace("\\", "/")
        checksum_text = str(checksum).lower()
        if (
            not relative_text
            or relative_text == MARKER_NAME
            or any(part in {"", ".", ".."} for part in relative_text.split("/"))
            or not HASH_PATTERN.fullmatch(checksum_text)
        ):
            return None
        result[relative_text] = checksum_text
    return result


def _read_source(source_root: Path, relative: str) -> bytes:
    """Read one source file through the shared no-follow filesystem backend."""
    try:
        return secure_fs.secure_read_bytes(
            source_root,
            relative,
            reject_hardlinks=True,
            max_bytes=16 * 1024 * 1024,
        )
    except (OSError, ValueError, secure_fs.SecureMutationError) as exc:
        raise CopyError(f"safe Kilo source read failed for {source_root / relative}: {exc}") from exc


def _read_target(target_root: Path, relative: str) -> Optional[bytes]:
    """Read an existing destination file or return ``None`` when absent."""
    try:
        return secure_fs.secure_read_bytes(
            target_root,
            relative,
            reject_hardlinks=True,
            max_bytes=16 * 1024 * 1024,
        )
    except FileNotFoundError:
        return None
    except (secure_fs.SecureMutationError, OSError) as exc:
        if not isinstance(exc, secure_fs.SecureMutationError) and exc.errno != errno.ELOOP:
            raise
        raise CopyError(f"safe Kilo destination read failed for {target_root / relative}: {exc}") from exc


def _write_target(target_root: Path, relative: str, content: bytes, prior: Optional[bytes]) -> None:
    """Atomically write one destination file with pinned expected bytes."""
    if prior == content:
        return
    expected = (
        secure_fs.ExpectedFileState.absent()
        if prior is None
        else secure_fs.ExpectedFileState.from_bytes(prior)
    )
    try:
        secure_fs.secure_write_bytes(
            target_root,
            relative,
            content,
            expected_state=expected,
        )
    except (OSError, ValueError, secure_fs.SecureMutationError) as exc:
        raise CopyError(f"safe Kilo destination write failed for {target_root / relative}: {exc}") from exc


def _walk_files(source: Path) -> list[tuple[str, Path]]:
    """List source files while rejecting every source link/reparse point."""
    result: list[tuple[str, Path]] = []
    pending = [source]
    while pending:
        current = pending.pop()
        if _is_link(current):
            raise CopyError(f"source contains a link or reparse point: {current}")
        try:
            entries = list(os.scandir(current))
        except OSError as exc:
            raise CopyError(f"cannot scan source directory {current}: {exc}") from exc
        for entry in entries:
            item = Path(entry.path)
            if _is_link(item):
                raise CopyError(f"source contains a link or reparse point: {item}")
            if entry.is_dir(follow_symlinks=False):
                pending.append(item)
            elif entry.is_file(follow_symlinks=False) and item.name != MARKER_NAME:
                result.append((item.relative_to(source).as_posix(), item))
    return sorted(result)


def sync_directory(source: Path, target: Path, source_relative: str,
                   released: Optional[ReleasedContent] = None,
                   project: Path | None = None) -> list[str]:
    """Copy a Kilo directory with checksum ownership and no-follow writes."""
    if not source.is_dir() or _is_link(source):
        raise CopyError(f"source is not a safe regular directory: {source}")
    source = source.resolve()
    if target.exists() and _is_link(target):
        raise CopyError(f"destination is a link or reparse point: {target}")
    lexical_project = project or target.parent
    relative_target = target.relative_to(lexical_project)
    project = lexical_project.resolve()
    target = project / relative_target
    _ensure_directory(target, project)
    if released is None:
        source_root = source
        for _ in Path(source_relative).parts:
            source_root = source_root.parent
        released = ReleasedContent(source_root)
    previous = _read_marker(target, source_relative) or {}
    source_files = _walk_files(source)
    source_names = {relative for relative, _ in source_files}
    next_files: dict[str, str] = {}
    preserved_modified: list[str] = []
    preserved_stale: list[str] = []
    manual: set[str] = set()
    totals = dict(create=0, update=0, adopt=0, remove=0)

    for relative, source_file in source_files:
        secure_fs.normalize_relative_path(relative)
        source_bytes = _read_source(source, relative)
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        old_hash = previous.get(relative)
        try:
            current_bytes = _read_target(target, relative)
        except CopyError as exc:
            sys.stderr.write(f"WARNING: {target / relative}: manual action required: {exc}\n")
            manual.add(str(target / relative))
            continue
        current_hash = hashlib.sha256(current_bytes).hexdigest() if current_bytes is not None else None
        action, reason = file_decision(current_hash, source_hash, old_hash or "")
        if action == "preserve/block" and released.matches(
            f"{source_relative}/{relative}", current_bytes
        ):
            action, reason = file_decision(current_hash, source_hash, old_hash or "", True)
        if action == "keep/adopt":
            totals["adopt"] += 1
            next_files[relative] = source_hash
            continue
        if action == "preserve/block":
            if old_hash:
                next_files[relative] = old_hash
            preserved_modified.append(relative)
            manual.add(str(target / relative))
            continue
        _write_target(target, relative, source_bytes, current_bytes)
        totals[action] += 1
        next_files[relative] = source_hash

    for relative, old_hash in previous.items():
        if relative in source_names:
            continue
        try:
            current_bytes = _read_target(target, relative)
        except CopyError as exc:
            sys.stderr.write(f"WARNING: {target / relative}: manual action required: {exc}\n")
            manual.add(str(target / relative))
            continue
        if current_bytes is None:
            continue
        if hashlib.sha256(current_bytes).hexdigest() == old_hash:
            try:
                secure_fs.secure_delete_verified(target, relative, old_hash)
                totals["remove"] += 1
            except (OSError, ValueError, secure_fs.SecureMutationError) as exc:
                raise CopyError(f"safe stale Kilo deletion failed for {target / relative}: {exc}") from exc
        else:
            preserved_stale.append(relative)
            manual.add(str(target / relative))

    for label, paths in (("user-owned", preserved_modified), ("modified stale", preserved_stale)):
        if paths:
            examples = ", ".join(paths[:5])
            suffix = " (additional files omitted)" if len(paths) > 5 else ""
            sys.stderr.write(
                f"WARNING: manual action required: preserving {label} Kilo files ({len(paths)}): {examples}{suffix}\n"
            )

    for directory, names, files in os.walk(target, followlinks=False):
        for name in list(names):
            path = Path(directory) / name
            if _is_link(path):
                names.remove(name)
                manual.add(str(path))
                sys.stderr.write(f"WARNING: {path}: manual action required: preserving foreign link\n")
        for name in files:
            relative = (Path(directory) / name).relative_to(target).as_posix()
            if relative != MARKER_NAME and relative not in source_names and relative not in previous:
                path = target / relative
                if _is_link(path) or not path.is_file():
                    manual.add(str(path))
                    sys.stderr.write(f"WARNING: {path}: manual action required: preserving unsafe file\n")
                else:
                    sys.stdout.write(f"{path.as_posix()}: user file kept\n")

    marker = target / MARKER_NAME
    if marker.exists() and _is_link(marker):
        raise CopyError(f"refusing to overwrite a link or reparse marker: {marker}")
    marker_data = {
        "schemaVersion": 1,
        "source": source_relative,
        "files": {key: next_files[key] for key in sorted(next_files)},
    }
    marker_bytes = (json.dumps(marker_data, indent=2) + "\n").encode("utf-8")
    prior_marker = _read_target(target, MARKER_NAME)
    _write_target(target, MARKER_NAME, marker_bytes, prior_marker)
    sys.stdout.write(f"Unit {source_relative}: " + ", ".join(
        f"{name}={count}" for name, count in totals.items()) + f", kept={len(manual)}\n")
    return sorted(manual)


def scalar_receipt(root: Path) -> dict:
    """Read checksum copy records without following links; e.g. a root adapter."""
    relative = ".compound-gpid/managed-files.json"
    try:
        content = secure_fs.secure_read_bytes(
            root, relative, reject_hardlinks=True, max_bytes=16 * 1024 * 1024,
        )
    except FileNotFoundError:
        return {}
    except (OSError, ValueError, secure_fs.SecureMutationError) as exc:
        raise CopyError(f"safe copy receipt read failed for {root / relative}: {exc}") from exc
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"WARNING: {relative}: invalid copy receipt: {exc}\n")
        return {}
    if (not isinstance(data, dict)
            or data.get("schemaVersion") != "compound-gpid-managed-files-v1"
            or not isinstance(data.get("files"), dict)):
        sys.stderr.write(f"WARNING: {relative}: invalid copy receipt schema\n")
        return {}
    records = data["files"]
    valid = {}
    for relative, record in records.items():
        try:
            secure_fs.normalize_relative_path(relative)
            secure_fs.normalize_relative_path(record["source"])
            if HASH_PATTERN.fullmatch(record["checksum"].lower()):
                valid[relative] = record
        except (ValueError, TypeError, KeyError, AttributeError):
            continue
    return valid


def generated_instructions(source: Path, project: Path) -> bytes:
    """Render the Copilot template for this project; e.g. no configured language."""
    def value(path: Path, key: str) -> str:
        content = _read_target(project, path.relative_to(project).as_posix())
        if content is None:
            return ""
        text = content.decode("utf-8-sig")
        frontmatter = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---", text, re.DOTALL)
        if not frontmatter:
            return ""
        match = re.search(r"(?m)^\s*" + re.escape(key) + r":\s*[\"']?([^\"'\r\n]+)[\"']?\s*$", frontmatter[1])
        return match[1].strip() if match else ""

    local = project / "compound-gpid.local.md"
    language = value(local, "language") or "<not configured>"
    dialect = value(local, "r-syntax")
    if dialect and re.search(r"\bR\b", language, re.I):
        language += f" (R dialect: {dialect})"
    replacements = {
        "project-name": value(project / "compound-gpid.md", "project-name") or "<project-name>",
        "project-type": value(local, "project-type") or "<not configured>",
        "languages": language,
        "review-depth": value(local, "review-depth") or "<not configured>",
    }
    template = _read_source(source, ".github/copilot-instructions.template.md").decode("utf-8")
    if not template.strip():
        raise CopyError("Copilot instruction template is empty")
    for key, replacement in replacements.items():
        if "{{" in replacement:
            raise CopyError("Config value contains a placeholder token")
        template = template.replace("{{" + key + "}}", replacement)
    separator = "\r\n" if "\r\n" in template else "\n"
    return ("<!-- compound-gpid:managed -->" + separator + template).encode("utf-8")


def sync_file(source: Path, project: Path, source_relative: str,
               target_relative: str, strategy: str, records: dict,
               released: ReleasedContent) -> bool:
    """Create, adopt or replace only proven bytes; e.g. keep a marked user edit."""
    desired = (generated_instructions(source, project) if strategy == "generated-copy"
               else _read_source(source, source_relative))
    try:
        current = _read_target(project, target_relative)
    except CopyError as exc:
        sys.stderr.write(f"WARNING: {target_relative}: manual action required: {exc}\n")
        return False
    checksum = hashlib.sha256(desired).hexdigest()
    record = records.get(target_relative, {})
    previous = record.get("checksum", "") if record.get("source") == source_relative else ""
    current_hash = hashlib.sha256(current).hexdigest() if current is not None else None
    needs_backup = False
    if strategy == "generated-copy":
        backup = project / (target_relative + ".pre-9024.bak")
        action, reason, needs_backup = copilot_decision(
            current, desired, previous, backup_exists=backup.exists() or _is_link(backup))
    else:
        action, reason = file_decision(current_hash, checksum, previous)
    if action == "preserve/block" and strategy != "generated-copy":
        if released.matches(source_relative, current):
            action, reason = file_decision(current_hash, checksum, previous, True)
    sys.stdout.write(f"Unit {target_relative}: {action}=1\n")
    if action == "preserve/block":
        sys.stderr.write(f"WARNING: {target_relative}: {reason}\n")
        return False
    if needs_backup:
        secure_fs.secure_write_bytes(
            project, target_relative + ".pre-9024.bak", current,
            expected_state=secure_fs.ExpectedFileState.absent(),
        )
    if action != "keep/adopt":
        _write_target(project, target_relative, desired, current)
    records[target_relative] = {"source": source_relative, "checksum": checksum}
    return True


def sync_units(source: Path, project: Path, directories: list, files: list,
               sync_projection: bool = False, manual_paths: list[str] | None = None,
               snippets: list | None = None) -> None:
    """Sync all queued copies with one release lookup, including skill mirrors."""
    # Validate the complete queue before any directory creation or scalar write.
    directories = [tuple(secure_fs.normalize_relative_path(path) for path in unit)
                   for unit in directories]
    files = [(*[secure_fs.normalize_relative_path(path) for path in unit[:2]], unit[2])
             for unit in files]
    for unit in [*directories, *(unit[:2] for unit in files)]:
        for path in unit:
            if path == "." or PureWindowsPath(path).anchor:
                raise CopyError(f"copy unit must name a path below its root: {path}")
    released = ReleasedContent(source)
    manual = set(manual_paths or [])
    for source_relative, target_relative in directories:
        manual.update(Path(path).relative_to(project).as_posix() for path in
                      sync_directory(source / source_relative, project / target_relative,
                                     source_relative, released, project))
    records = scalar_receipt(project)
    for source_relative, target_relative, strategy in files:
        if not sync_file(source, project, source_relative, target_relative, strategy, records, released):
            manual.add(target_relative)
    if files and records:
        data = {"schemaVersion": "compound-gpid-managed-files-v1", "files": records}
        relative = ".compound-gpid/managed-files.json"
        _write_target(project, relative, (json.dumps(data, indent=2) + "\n").encode("utf-8"),
                      _read_target(project, relative))
    if sync_projection and (project / ".compound-gpid/active-manifest.json").is_file():
        import cg_project_projection as projection

        projection.sync_consumer_projection(project, source, released=released)
    try:
        marker_bytes = _read_target(project, ".kilo/skills/" + MARKER_NAME)
    except CopyError as exc:
        sys.stderr.write(f"WARNING: .kilo/skills: manual action required: {exc}\n")
        manual.add(".kilo/skills")
        marker_bytes = None
    platforms = (("claude-code", ".claude/skills"),
                            ("codex", ".agents/skills"), ("opencode", ".opencode/skills"))
    if marker_bytes is None or _read_marker(project / ".kilo/skills", ".kilo/skills") is None:
        platforms = ()
    for platform, path in platforms:
        target = project / path
        mirror = project / ".compound-gpid/kilo-compat-skills" / platform
        try:
            secure_fs.revalidate_destination_ancestors(project, target)
        except (OSError, ValueError) as exc:
            sys.stderr.write(f"WARNING: {path}: manual action required: {exc}\n")
            manual.add(path)
            continue
        if _is_link(target) and target.resolve() in ((source / path).resolve(), mirror.resolve()):
            if _is_link(mirror):
                sys.stderr.write(f"WARNING: {mirror}: manual action required: preserving foreign link\n")
                manual.add(mirror.relative_to(project).as_posix())
                continue
            manual.update(Path(item).relative_to(project).as_posix() for item in
                          sync_directory(source / path, mirror, path, released, project))
    sys.stdout.write(f"Manual action required: {len(manual)}\n")
    deferred = sum(any(
        Path(path) == Path(root) or Path(root) in Path(path).parents
        or Path(path) in Path(root).parents
        for root in VALIDATED_KILO_ROOTS
    ) for path in manual)
    sys.stdout.write(f"Kilo validation deferred: {deferred}\n")
    for path in sorted(manual):
        sys.stdout.write(f"  {path}\n")
    for path, snippet in snippets or []:
        if path in manual:
            sys.stdout.write(f"Manual config snippet for {path}: {snippet}\n")


def copilot_action(source: Path, project: Path, action: str) -> None:
    """Refresh or unlink instructions through the same byte ownership policy."""
    relative = ".github/copilot-instructions.md"
    records = scalar_receipt(project)
    if action == "update":
        sync_units(source, project, [], [(
            ".github/copilot-instructions.template.md", relative, "generated-copy")])
        return
    try:
        current = _read_target(project, relative)
    except CopyError as exc:
        sys.stderr.write(f"WARNING: {relative}: manual action required: {exc}\n")
        return
    record = records.get(relative, {})
    previous = (record.get("checksum", "") if record.get("source") ==
                ".github/copilot-instructions.template.md" else "")
    decision, reason, _ = copilot_decision(current, b"", previous, remove=True)
    if decision == "preserve/block":
        sys.stderr.write(f"WARNING: {relative}: {reason}\n")
        return
    if decision == "remove":
        secure_fs.secure_delete_verified(project, relative, hashlib.sha256(current).hexdigest())
        records.pop(relative, None)
        receipt = ".compound-gpid/managed-files.json"
        prior = _read_target(project, receipt)
        if prior is not None:
            data = {"schemaVersion": "compound-gpid-managed-files-v1", "files": records}
            _write_target(project, receipt, (json.dumps(data, indent=2) + "\n").encode("utf-8"), prior)
    sys.stdout.write(f"Unit {relative}: {decision}=1\n")


def main(argv: Optional[list[str]] = None) -> int:
    """Run one safe copy-directory synchronization."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--source-relative")
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--directory", nargs=2, action="append", default=[])
    parser.add_argument("--file", nargs=3, action="append", default=[])
    parser.add_argument("--sync-projection", action="store_true")
    parser.add_argument("--copilot-action", choices=("update", "unlink"))
    parser.add_argument("--manual-path", action="append", default=[])
    parser.add_argument("--manual-snippet", nargs=2, action="append", default=[])
    args = parser.parse_args(argv)
    try:
        if args.source_root and args.project_root:
            project = args.project_root.resolve()
            source = args.source_root.resolve()
            if args.copilot_action:
                copilot_action(source, project, args.copilot_action)
            else:
                sync_units(source, project, args.directory, args.file,
                           args.sync_projection, args.manual_path, args.manual_snippet)
        elif args.source and args.target and args.source_relative:
            manual = sync_directory(Path(args.source), Path(args.target), args.source_relative)
            sys.stdout.write(f"Manual action required: {len(manual)}\n")
            for path in manual:
                sys.stdout.write(f"  {path}\n")
        else:
            parser.error("supply a source/project root or a source/target/source-relative unit")
    except (CopyError, OSError, ValueError) as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
