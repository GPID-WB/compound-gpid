#!/usr/bin/env python3
"""Synchronize one Kilo copy-directory unit without following links."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Optional

try:
    import secure_fs
except ImportError:  # pragma: no cover - direct script execution path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import secure_fs


MARKER_NAME = ".compound-gpid-managed-copy.json"
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REPARSE_POINT_FLAG = 0x400


class CopyError(RuntimeError):
    """Raised when a copy-directory mutation cannot be proven safe."""


def _is_link(path: Path) -> bool:
    """Return whether ``path`` is a symlink or Windows reparse point."""
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & REPARSE_POINT_FLAG)
    except OSError:
        return False


def _ensure_directory(path: Path) -> None:
    """Create a directory only when every existing component is real."""
    if path.exists() and _is_link(path):
        raise CopyError(f"refusing to use a link or reparse directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    current = path
    while True:
        if _is_link(current):
            raise CopyError(f"refusing to use a link or reparse directory: {current}")
        if not current.is_dir():
            raise CopyError(f"copy destination component is not a directory: {current}")
        parent = current.parent
        if parent == current:
            break
        current = parent


def _read_marker(target: Path, source_relative: str) -> Optional[dict[str, str]]:
    """Read a valid ownership marker; invalid markers disable stale deletion."""
    marker = target / MARKER_NAME
    if not marker.exists():
        return None
    if _is_link(marker):
        raise CopyError(f"refusing to read a link or reparse marker: {marker}")
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
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
    except (OSError, ValueError, secure_fs.SecureMutationError) as exc:
        raise CopyError(f"safe Kilo destination read failed for {target_root / relative}: {exc}") from exc


def _write_target(target_root: Path, relative: str, content: bytes, prior: Optional[bytes]) -> None:
    """Atomically write one destination file with pinned expected bytes."""
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


def sync_directory(source: Path, target: Path, source_relative: str) -> None:
    """Copy a Kilo directory with checksum ownership and no-follow writes."""
    if not source.is_dir() or _is_link(source):
        raise CopyError(f"source is not a safe regular directory: {source}")
    if target.exists() and _is_link(target):
        raise CopyError(f"destination is a link or reparse point: {target}")
    _ensure_directory(target)
    previous = _read_marker(target, source_relative) or {}
    source_files = _walk_files(source)
    source_names = {relative for relative, _ in source_files}
    next_files: dict[str, str] = {}
    preserved_modified: list[str] = []
    preserved_stale: list[str] = []

    for relative, source_file in source_files:
        secure_fs.normalize_relative_path(relative)
        source_bytes = _read_source(source, relative)
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        old_hash = previous.get(relative)
        current_bytes = _read_target(target, relative)
        if current_bytes is not None:
            current_hash = hashlib.sha256(current_bytes).hexdigest()
            if current_hash == source_hash:
                next_files[relative] = source_hash
                continue
            if not old_hash or current_hash != old_hash:
                if old_hash:
                    next_files[relative] = old_hash
                preserved_modified.append(relative)
                continue
        _write_target(target, relative, source_bytes, current_bytes)
        next_files[relative] = source_hash

    for relative, old_hash in previous.items():
        if relative in source_names:
            continue
        current_bytes = _read_target(target, relative)
        if current_bytes is None:
            continue
        if hashlib.sha256(current_bytes).hexdigest() == old_hash:
            try:
                secure_fs.secure_delete_verified(target, relative, old_hash)
            except (OSError, ValueError, secure_fs.SecureMutationError) as exc:
                raise CopyError(f"safe stale Kilo deletion failed for {target / relative}: {exc}") from exc
        else:
            preserved_stale.append(relative)

    for label, paths in (("user-owned", preserved_modified), ("modified stale", preserved_stale)):
        if paths:
            examples = ", ".join(paths[:5])
            suffix = " (additional files omitted)" if len(paths) > 5 else ""
            sys.stderr.write(
                f"WARNING: preserving {label} Kilo files ({len(paths)}): {examples}{suffix}\n"
            )

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


def main(argv: Optional[list[str]] = None) -> int:
    """Run one safe copy-directory synchronization."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--source-relative", required=True)
    args = parser.parse_args(argv)
    try:
        sync_directory(Path(args.source), Path(args.target), args.source_relative)
    except CopyError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
