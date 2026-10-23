"""No-follow path classification for the read-only cg-link report."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
from typing import Any

import cg_kilo_copy as kilo_copy
import cg_project_projection as projection
import cg_retire_native_evidence as retirement
from cg_link_ownership import ReleasedContent, copilot_decision, file_decision
import secure_fs

COPY_MARKER = ".compound-gpid-managed-copy.json"
MIRROR_ROOT = ".compound-gpid/kilo-compat-skills"


def mirror_receipt(root: Path, relative: str, source: str) -> dict | None:
    """Validate a copy receipt after a no-follow read; e.g. Codex skills."""
    try:
        root = root.resolve()
        state, _, error = inspect_path(root, f"{relative}/{COPY_MARKER}")
        if state != "file" or error:
            return None
        return kilo_copy._read_marker(root / relative, source)
    except (OSError, ValueError, RuntimeError, kilo_copy.CopyError):
        return None


def link_component(root: Path, relative: str) -> str:
    """Return the first linked component without traversal; e.g. ``.kilo``."""
    root = root.resolve()
    path = root
    for part in Path(secure_fs.normalize_relative_path(relative)).parts:
        path = path / part
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            break
        if (stat.S_ISLNK(metadata.st_mode)
                or getattr(metadata, "st_reparse_tag", 0) in (
                    0xA000000C, 0xA0000003  # Symlink and mount-point/junction tags.
                )):
            return path.relative_to(root).as_posix()
        if not stat.S_ISDIR(metadata.st_mode):
            break
    return ""


def link_matches(path: Path, expected: Path) -> bool:
    """Compare a known link's target identity only; e.g. an exact source link."""
    try:
        return path.resolve(strict=True) == expected.resolve(strict=True)
    except (OSError, RuntimeError):
        return False


def inspect_path(root: Path, relative: str) -> tuple[str, str, str]:
    """Return no-follow state, hash and error; e.g. missing has no checksum."""
    try:
        root = root.resolve()
        linked = link_component(root, relative)
        if linked:
            return "link/reparse", "", f"link/reparse path retained without traversal: {linked}"
        content = secure_fs.secure_read_bytes(
            root, relative, reject_hardlinks=True, max_bytes=retirement.READ_LIMIT
        )
        return "file", hashlib.sha256(content).hexdigest(), ""
    except FileNotFoundError:
        return "missing", "", ""
    except (OSError, ValueError, RuntimeError) as error:
        return "directory/unsafe", "", str(error)


def file_row(root: Path, relative: str, desired: str, previous: str,
              *, stale: bool = False, released: ReleasedContent | None = None,
              source_relative: str = "", user_file: bool = False) -> dict[str, Any]:
    """Classify checksum-gated copying/cleanup; e.g. an edited file is preserved."""
    root = root.resolve()
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
        elif user_file and not previous and state == "file":
            action, reason = "keep/adopt", "user file kept; no ownership receipt"
        else:
            action, reason = "preserve", "no unchanged ownership proof for cleanup"
            manual = state != "missing"
        if state == "missing":
            action, reason = "none", "stale owned path is already absent"
    else:
        action, reason = file_decision(
            None if state == "missing" else current, desired, previous
        )
        if (action == "preserve/block" and released is not None
                and source_relative):
            content = secure_fs.secure_read_bytes(
                root, relative, reject_hardlinks=True, max_bytes=retirement.READ_LIMIT
            )
            if released.matches(source_relative, content):
                action, reason = file_decision(current, desired, previous, released=True)
                owner = "managed"
        manual = action == "preserve/block"
    return dict(path=relative, owner=owner, state=state, sha256=current,
                action=action, reason=reason, manual=manual)


def inventory(root: Path, relative: str) -> list[str]:
    """List managed-root leaves without following links; e.g. stale commands."""
    root = root.resolve()
    path = root / relative
    if link_component(root, relative) or not path.is_dir():
        return []
    leaves = []
    for directory, names, files in os.walk(path, followlinks=False):
        for name in list(names):
            child = Path(directory) / name
            if link_component(root, child.relative_to(root).as_posix()):
                leaves.append(child.relative_to(root).as_posix())
                names.remove(name)
        leaves.extend(
            (Path(directory) / name).relative_to(root).as_posix() for name in files
        )
    return sorted(leaves)


def legacy_rows(root: Path, source: Path, targets: list[dict], scalar: dict,
                manifest_driven: bool, force: bool,
                released: ReleasedContent | None = None) -> list[dict]:
    """Describe pre-projection install units; e.g. checksum-owned JSON copies."""
    rows = []
    for target in targets:
        foreign_roots = set()
        migrating_roots = set()
        for root_relative in sorted({Path(unit["target"]).parts[0]
                                     for unit in target["installUnits"]}):
            linked = link_component(root, root_relative)
            if linked and (linked != root_relative or not link_matches(
                root / root_relative, source / root_relative
            )):
                row = file_row(root, root_relative, "", "")
                row["reason"] = (
                    "foreign root link retained without traversal; manual action required"
                )
                rows.append(row)
                foreign_roots.add(root_relative)
            elif linked:
                migrating_roots.add(root_relative)
        for unit in target["installUnits"]:
            relative, strategy = unit["target"], unit["strategy"]
            if Path(relative).parts[0] in foreign_roots:
                continue
            path, expected = root / relative, source / unit["source"]
            if not expected.exists():
                row = file_row(root, relative, "", "")
                row.update(action="block", reason="source unit is missing", manual=True)
                rows.append(row)
                continue
            if Path(relative).parts[0] in migrating_roots:
                if unit["type"] == "directory" and strategy == "copy-directory":
                    paths = [f"{relative}/{leaf}" for leaf, _ in kilo_copy._walk_files(expected)]
                else:
                    paths = [relative]
                rows.extend(dict(
                    path=destination, owner="managed", state="link/reparse",
                    action="link" if strategy == "link-directory" else "create",
                    reason="exact legacy whole-root link is migrated before copying",
                    manual=False,
                ) for destination in paths)
                continue
            if unit["type"] == "directory":
                mirror = f"{MIRROR_ROOT}/{target.get('id', '')}"
                linked = link_component(root, relative)
                if (relative in (".claude/skills", ".agents/skills", ".opencode/skills")
                        and linked == relative
                        and link_matches(path, root / mirror)
                        and mirror_receipt(root, mirror, unit["source"]) is not None):
                    rows.append(dict(
                        path=relative, owner="managed", state="link/reparse",
                        action="keep", reason="recognized managed compatibility mirror link",
                        manual=False,
                    ))
                    continue
                if manifest_driven and target.get("generatedTreePath"):
                    if linked:
                        rows.append(file_row(root, linked, "", ""))
                    continue
                owned = linked == relative and link_matches(path, expected)
                if strategy == "link-directory":
                    state = "missing"
                    if linked:
                        state = "link/reparse"
                    elif path.exists():
                        state = "directory" if path.is_dir() else "file"
                    conflict = state != "missing" and not owned
                    action = "link"
                    if owned:
                        action = "keep"
                    elif conflict:
                        action = "preserve/block"
                    reason = "directory install unit"
                    if owned:
                        reason = "exact source link"
                    elif conflict:
                        reason = "existing unit retained; manual action required"
                    rows.append(dict(
                        path=relative, owner="managed" if owned else "unowned",
                        state=state, action=action, reason=reason,
                        manual=conflict,
                    ))
                    continue
                if linked and not owned:
                    rows.append(file_row(root, linked, "", ""))
                    continue
                previous = mirror_receipt(root, relative, unit["source"]) or {}
                files = dict(kilo_copy._walk_files(expected))
                for leaf in sorted(files):
                    source_relative = f"{unit['source']}/{leaf}"
                    content = kilo_copy._read_source(source, source_relative)
                    row = file_row(
                        root, f"{relative}/{leaf}",
                        hashlib.sha256(content).hexdigest(),
                        previous.get(leaf, ""), released=released,
                        source_relative=source_relative,
                    )
                    if owned:
                        row.update(
                            owner="managed", action="migrate/copy", manual=False,
                            reason="exact legacy link is replaced with a managed copy",
                        )
                    rows.append(row)
                for leaf, checksum in sorted(previous.items()):
                    if leaf not in files:
                        rows.append(file_row(
                            root, f"{relative}/{leaf}", "", checksum, stale=True
                        ))
                for destination in inventory(root, relative):
                    leaf = destination[len(relative) + 1:]
                    if leaf not in files and leaf not in previous and leaf != COPY_MARKER:
                        rows.append(file_row(root, destination, "", "", stale=True,
                                             user_file=True))
                continue
            record = scalar.get(relative, {})
            checksum = (record.get("checksum", "")
                        if record.get("source") == unit["source"] else "")
            if strategy == "generated-copy":
                for config in ("compound-gpid.local.md", "compound-gpid.md"):
                    _, _, error = inspect_path(root, config)
                    if error:
                        raise ValueError(f"unsafe instruction config: {config}: {error}")
            content = (kilo_copy.generated_instructions(source, root)
                       if strategy == "generated-copy"
                       else kilo_copy._read_source(source, unit["source"]))
            row = file_row(
                root, relative, hashlib.sha256(content).hexdigest(), checksum,
                released=released if strategy != "generated-copy" else None,
                source_relative=unit["source"],
            )
            if strategy == "generated-copy" and row["state"] in ("file", "missing"):
                current = (secure_fs.secure_read_bytes(root, relative, reject_hardlinks=True)
                           if row["state"] == "file" else None)
                backup_state, _, backup_error = inspect_path(root, relative + ".pre-9024.bak")
                action, reason, _ = copilot_decision(
                    current, content, checksum,
                    backup_exists=backup_state != "missing" or bool(backup_error),
                )
                row.update(action=action, reason=reason, manual=action == "preserve/block")
            if row["manual"] and unit.get("manualSnippet"):
                row["reason"] += "; " + unit["manualSnippet"]
            rows.append(row)
    return rows


def mirror_rows(root: Path, source: Path, targets: list[dict],
                released: ReleasedContent | None = None) -> list[dict]:
    """Report existing mirrors with copy checksums; never sync or clean them."""
    rows = {}
    for target in targets:
        if target["id"] not in ("claude-code", "codex", "opencode"):
            continue
        relative = f"{MIRROR_ROOT}/{target['id']}"
        path = root / relative
        linked = link_component(root, relative)
        if linked:
            rows[linked] = file_row(root, linked, "", "")
            continue
        if not path.exists():
            continue
        unit = next(u for u in target["installUnits"]
                    if u["target"] == target["outputPaths"]["skills"])
        previous = mirror_receipt(root, relative, unit["source"])
        owned = previous is not None
        directory = path.is_dir()
        rows[relative] = dict(
            path=relative, owner="managed" if owned else "unowned",
            state="directory" if directory else inspect_path(root, relative)[0],
            action="sync" if directory else "preserve/block", manual=not directory,
            reason="validated compatibility mirror copy receipt" if owned
            else "no valid mirror receipt; file-level ownership proof required",
        )
        if not directory:
            continue
        previous = previous or {}
        desired = {
            leaf: hashlib.sha256(kilo_copy._read_source(
                source, f"{unit['source']}/{leaf}"
            )).hexdigest()
            for leaf, _ in kilo_copy._walk_files(source / unit["source"])
        }
        leaves = set(desired) | set(previous) | {
            leaf[len(relative) + 1:] for leaf in inventory(root, relative)
        }
        for leaf in sorted(leaves - {COPY_MARKER}):
            destination = f"{relative}/{leaf}"
            rows[destination] = file_row(
                root, destination, desired.get(leaf, ""), previous.get(leaf, ""),
                stale=leaf not in desired, released=released,
                source_relative=f"{unit['source']}/{leaf}",
                user_file=leaf not in desired and leaf not in previous,
            )
        receipt = f"{relative}/{COPY_MARKER}"
        state, _, error = inspect_path(root, receipt)
        rows[receipt] = dict(
            path=receipt, owner="managed" if owned else "unowned", state=state,
            action="preserve/block" if error else "create" if state == "missing" else "retain",
            reason=error or ("validated mirror ownership receipt; check does not refresh it"
                            if owned else "no valid mirror receipt; stale cleanup disabled"),
            manual=bool(error),
        )
    for relative in inventory(root, MIRROR_ROOT):
        if relative not in rows:
            row = file_row(root, relative, "", "", stale=True)
            row["reason"] = "unrecognized mirror path; no ownership proof"
            rows[relative] = row
    return list(rows.values())
