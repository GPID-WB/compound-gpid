"""Portable path, ownership-glob, and shared inventory primitives."""
from __future__ import annotations

from fnmatch import fnmatchcase
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Dict, Iterable, List, Optional, Tuple
import unicodedata


WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
_REPARSE_POINT_FLAG = 0x400
_LOCAL_ARTIFACT_NAMES = {".DS_Store", "Thumbs.db"}
_LOCAL_ARTIFACT_SUFFIXES = (".pyc", ".pyo", ".swp", ".tmp", "~")


def normalize_canonical_path(path: str) -> str:
    """Normalize one canonical path to POSIX repository-relative form."""
    value = PurePosixPath(path.replace("\\", "/")).as_posix()
    while value.startswith("./"):
        value = value[2:]
    return value


def glob_match(pattern: str, asset: str) -> bool:
    """Match one component-aware owned-asset glob against an asset."""
    is_directory = pattern.endswith("/")
    pattern_parts = PurePosixPath(normalize_canonical_path(pattern)).parts
    asset_parts = PurePosixPath(normalize_canonical_path(asset)).parts
    if len(asset_parts) < len(pattern_parts):
        return False
    if len(asset_parts) == len(pattern_parts) and not is_directory:
        return all(
            fnmatchcase(asset_part, pattern_part)
            for pattern_part, asset_part in zip(pattern_parts, asset_parts)
        )
    if is_directory:
        return all(
            fnmatchcase(asset_part, pattern_part)
            for pattern_part, asset_part in zip(pattern_parts, asset_parts)
        )
    return False


def portable_path_key(value: str) -> Tuple[str, ...]:
    """Return a Unicode-normalized, case-insensitive portable path key."""
    return tuple(
        unicodedata.normalize("NFC", part).casefold().rstrip(". ")
        for part in PurePosixPath(value).parts
    )


def validate_repo_relative_path(label: str, value: Any) -> List[str]:
    """Validate one portable POSIX repository-relative path."""
    if not isinstance(value, str):
        return [f"{label}: must be a string"]
    if not value:
        return [f"{label}: must not be empty"]
    errors: List[str] = []
    if "\x00" in value:
        errors.append(f"{label}: must not contain NUL")
    if "\\" in value:
        errors.append(f"{label}: must use POSIX '/' separators")
    if value.startswith(("/", "//", "\\\\")) or re.match(r"^[A-Za-z]:", value):
        errors.append(
            f"{label}: must be repository-relative, not absolute, drive-qualified, or UNC"
        )
    parts = value.replace("\\", "/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        errors.append(f"{label}: must not contain empty, '.', or traversal components")
    for part in parts:
        portable = unicodedata.normalize("NFC", part).casefold().rstrip(". ")
        forbidden = sorted(
            character
            for character in part
            if ord(character) < 32 or character in '<>:"|?*'
        )
        if forbidden:
            errors.append(
                f"{label}: component '{part}' contains Windows-forbidden characters: "
                + ", ".join(repr(character) for character in forbidden)
            )
        if part.endswith((".", " ")):
            errors.append(f"{label}: component '{part}' has a trailing dot or space")
        if portable.split(".", 1)[0] in WINDOWS_RESERVED_NAMES:
            errors.append(f"{label}: component '{part}' is a Windows reserved name")
    return errors


def is_local_artifact_path(value: str) -> bool:
    """Return whether a path contains a hidden, cache, or temporary artifact."""
    parts = PurePosixPath(value).parts
    return any(
        part.startswith(".")
        or part == "__pycache__"
        or part in _LOCAL_ARTIFACT_NAMES
        or part.endswith(_LOCAL_ARTIFACT_SUFFIXES)
        for part in parts[2:]
    )


def _is_link_or_reparse(metadata: os.stat_result) -> bool:
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & _REPARSE_POINT_FLAG
    )


def _may_match_descendant(patterns: Iterable[str], value: str) -> bool:
    value_parts = PurePosixPath(normalize_canonical_path(value)).parts
    for pattern in patterns:
        is_directory = pattern.endswith("/")
        pattern_parts = PurePosixPath(normalize_canonical_path(pattern)).parts
        shared = min(len(value_parts), len(pattern_parts))
        if not all(
            fnmatchcase(value_parts[index], pattern_parts[index])
            for index in range(shared)
        ):
            continue
        if len(value_parts) < len(pattern_parts):
            return True
        if len(value_parts) == len(pattern_parts):
            if is_directory or glob_match(pattern, value):
                return True
            continue
        if is_directory:
            return True
    return False


def inventory_shared_assets(
    root: Path,
    *,
    include_globs: Optional[Iterable[str]] = None,
    max_files: int = 5000,
    max_depth: int = 32,
) -> List[str]:
    """Recursively inventory safe regular files under `.github/shared`."""
    shared_root = root / ".github/shared"
    try:
        root_metadata = os.lstat(str(shared_root))
    except OSError as error:
        raise ValueError("Required canonical shared root is missing or invalid") from error
    if _is_link_or_reparse(root_metadata) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ValueError("Canonical shared root is a link, reparse point, or non-directory")

    files: List[str] = []
    seen_paths: Dict[Tuple[str, ...], str] = {}
    selected_globs = tuple(include_globs) if include_globs is not None else None
    stack = [(shared_root, 0)]
    visited_entries = 0
    while stack:
        directory, depth = stack.pop()
        if depth > max_depth:
            raise ValueError(
                f"Canonical shared inventory exceeds depth {max_depth}: {directory}"
            )
        try:
            with os.scandir(str(directory)) as entries:
                ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        except OSError as error:
            raise ValueError(
                f"Cannot inventory canonical shared directory: {directory}"
            ) from error
        for entry in ordered:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            if selected_globs is not None and not _may_match_descendant(
                selected_globs, relative
            ):
                continue
            visited_entries += 1
            if visited_entries > max_files:
                raise ValueError(
                    f"Canonical shared inventory exceeds {max_files} selected entries"
                )
            errors = validate_repo_relative_path("canonical shared path", relative)
            if errors:
                raise ValueError("Unsafe canonical shared path: " + "; ".join(errors))
            if relative == ".github/shared/.gitkeep":
                continue
            if is_local_artifact_path(relative):
                raise ValueError(f"Canonical shared path is a local artifact: {relative}")
            metadata = entry.stat(follow_symlinks=False)
            if _is_link_or_reparse(metadata):
                raise ValueError(
                    f"Canonical shared entry is a link or reparse point: {relative}"
                )
            key = portable_path_key(relative)
            prior = seen_paths.get(key)
            if prior is not None and prior != relative:
                raise ValueError(
                    f"Canonical shared portable path collision: {prior} and {relative}"
                )
            seen_paths[key] = relative
            if stat.S_ISDIR(metadata.st_mode):
                stack.append((path, depth + 1))
            elif stat.S_ISREG(metadata.st_mode):
                if selected_globs is not None and not any(
                    glob_match(pattern, relative) for pattern in selected_globs
                ):
                    continue
                files.append(relative)
            else:
                raise ValueError(
                    f"Canonical shared entry is not a regular file or directory: {relative}"
                )
    return sorted(files)
