"""No-follow path classification for the read-only cg-link report."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import cg_project_projection as projection
import cg_retire_native_evidence as retirement
import secure_fs

COPY_MARKER = ".compound-gpid-managed-copy.json"


def inspect_path(root: Path, relative: str) -> tuple[str, str, str]:
    """Return no-follow state, hash and error; e.g. missing has no checksum."""
    try:
        content = secure_fs.secure_read_bytes(
            root, relative, reject_hardlinks=True, max_bytes=retirement.READ_LIMIT
        )
        return "file", hashlib.sha256(content).hexdigest(), ""
    except FileNotFoundError:
        return "missing", "", ""
    except (OSError, ValueError) as error:
        path = root / relative
        state = (
            "link/reparse" if projection._is_link_or_reparse_path(path)
            else "directory/unsafe"
        )
        return state, "", str(error)


def file_row(root: Path, relative: str, desired: str, previous: str,
             *, adopt: bool = True, stale: bool = False) -> dict[str, Any]:
    """Classify checksum-gated copying/cleanup; e.g. an edited file is preserved."""
    state, current, error = inspect_path(root, relative)
    owner = "managed" if previous else "unowned"
    if previous and current and current != previous:
        owner = "modified-owned"
    action, reason, manual = "create", "destination is absent", False
    if error:
        action, reason, manual = "preserve/block", error, True
    elif stale:
        if previous and current == previous:
            owner = "old-version leftover"
            action, reason = "remove", "unchanged stale ownership checksum"
        else:
            action, reason = "preserve", "no unchanged ownership proof for cleanup"
            manual = state != "missing"
        if state == "missing":
            action, reason = "none", "stale owned path is already absent"
    elif state != "missing":
        if previous and current == previous:
            action = "keep" if current == desired else "update"
            reason = "matches the recorded ownership checksum"
        elif adopt and current == desired:
            action, reason = "keep/adopt", "bytes already match the desired plan"
        else:
            action, manual = "preserve/block", True
            reason = (
                "modified owned bytes" if previous
                else "unowned destination conflict"
            )
    return dict(path=relative, owner=owner, state=state, sha256=current,
                action=action, reason=reason, manual=manual)


def inventory(root: Path, relative: str) -> list[str]:
    """List managed-root leaves without following links; e.g. stale commands."""
    path = root / relative
    if projection._is_link_or_reparse_path(path) or not path.is_dir():
        return []
    leaves = []
    for directory, names, files in os.walk(path, followlinks=False):
        for name in list(names):
            child = Path(directory) / name
            if projection._is_link_or_reparse_path(child):
                leaves.append(child.relative_to(root).as_posix())
                names.remove(name)
        leaves.extend(
            (Path(directory) / name).relative_to(root).as_posix() for name in files
        )
    return sorted(leaves)


def legacy_rows(root: Path, source: Path, targets: list[dict], scalar: dict,
                manifest_driven: bool, force: bool) -> list[dict]:
    """Describe pre-projection install units; e.g. checksum-owned JSON copies."""
    rows = []
    ignore_state, _, ignore_error = inspect_path(root, ".gitignore")
    ignore_text = ""
    if ignore_state == "file" and not ignore_error:
        ignore_text = secure_fs.secure_read_bytes(root, ".gitignore").decode(
            "utf-8", errors="replace"
        )
    for target in targets:
        for unit in target["installUnits"]:
            relative, strategy = unit["target"], unit["strategy"]
            path, expected = root / relative, source / unit["source"]
            if not expected.exists():
                row = file_row(root, relative, "", "")
                row.update(action="block", reason="source unit is missing", manual=True)
                rows.append(row)
                continue
            if unit["type"] == "directory":
                if manifest_driven and target.get("generatedTreePath"):
                    continue
                linked = projection._is_link_or_reparse_path(path)
                owned = linked and path.resolve() == expected.resolve()
                if strategy == "link-directory":
                    state = "missing"
                    if linked:
                        state = "link/reparse"
                    elif path.exists():
                        state = "directory" if path.is_dir() else "file"
                    conflict = state != "missing" and not owned
                    replace = conflict and linked and force
                    action = "link"
                    if owned:
                        action = "keep"
                    elif conflict:
                        action = "relink" if replace else "preserve/prompt"
                    reason = "directory install unit"
                    if owned:
                        reason = "exact source link"
                    elif conflict:
                        reason = "existing unit requires review"
                    rows.append(dict(
                        path=relative, owner="managed" if owned else "unowned",
                        state=state, action=action, reason=reason,
                        manual=conflict and not replace,
                    ))
                    continue
                marker_relative = f"{relative}/{COPY_MARKER}"
                marker = {}
                marker_state, _, marker_error = inspect_path(root, marker_relative)
                if not linked and marker_state == "file" and not marker_error:
                    try:
                        marker = json.loads(secure_fs.secure_read_bytes(
                            root, marker_relative
                        ).decode("utf-8"))
                    except (ValueError, UnicodeError):
                        pass  # The copy worker also baselines malformed markers.
                if not isinstance(marker, dict):
                    marker = {}
                previous = {}
                if (marker.get("source") == unit["source"]
                        and marker.get("schemaVersion") == 1):
                    previous = marker.get("files", {})
                if not isinstance(previous, dict):
                    previous = {}
                legacy_backup = (
                    os.name != "nt" and marker_state == "missing"
                    and "# Compound GPID managed items" in ignore_text
                    and relative in {line.rstrip("/") for line in ignore_text.splitlines()}
                )
                files = {
                    p.relative_to(expected).as_posix(): p
                    for p in expected.rglob("*")
                    if p.is_file() and not p.is_symlink() and p.name != COPY_MARKER
                }
                for leaf, source_file in sorted(files.items()):
                    row = file_row(
                        root, f"{relative}/{leaf}",
                        hashlib.sha256(source_file.read_bytes()).hexdigest(),
                        previous.get(leaf, ""),
                    )
                    if owned:
                        row.update(
                            owner="managed", action="migrate/copy", manual=False,
                            reason="exact legacy link is replaced with a managed copy",
                        )
                    elif (legacy_backup and not previous.get(leaf)
                          and row["state"] == "file" and row["manual"]):
                        row.update(
                            action="backup/overwrite", manual=False,
                            reason="existing POSIX gitignore-marker fallback backs up "
                                   "unrecorded bytes before overwrite; policy is unchanged",
                        )
                    rows.append(row)
                for leaf, checksum in sorted(previous.items()):
                    if leaf not in files:
                        rows.append(file_row(
                            root, f"{relative}/{leaf}", "", checksum, stale=True
                        ))
                continue
            checksum = scalar.get(relative, {}).get("checksum", "")
            row = file_row(
                root, relative, hashlib.sha256(expected.read_bytes()).hexdigest(),
                checksum, adopt=False,
            )
            if strategy == "generated-copy":
                state, _, error = inspect_path(root, relative)
                marked = not error and state != "missing" and (
                    b"<!-- compound-gpid:managed -->"
                    in secure_fs.secure_read_bytes(root, relative)
                )
                if state == "missing" or marked:
                    row.update(
                        owner=row["owner"] if checksum else "managed" if marked else "unowned",
                        action="regenerate", manual=False,
                        reason="current marker-only policy permits regeneration; "
                               "checksum protection is deferred to Step3b",
                    )
            if row["manual"] and unit.get("manualSnippet"):
                row["reason"] += "; " + unit["manualSnippet"]
            rows.append(row)
    return rows
