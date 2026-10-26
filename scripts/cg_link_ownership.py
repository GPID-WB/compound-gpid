"""Shared file replacement rule and lazy, read-only release-content proof."""
from __future__ import annotations

from pathlib import Path
import hashlib
import os
import re
import subprocess


def file_decision(current: str | None, desired: str, previous: str = "",
                  released: bool = False) -> tuple[str, str]:
    """Decide from checksums, never markers; e.g. unknown bytes are preserved."""
    if current is None:
        return "create", "destination is absent"
    if current == desired:
        return "keep/adopt", "bytes already match the desired plan"
    if re.fullmatch(r"[0-9a-fA-F]{64}", previous) and current == previous.lower():
        return "update", "matches the recorded ownership checksum"
    if released:
        return "update", "matches released content at the same source path"
    return "preserve/block", "manual action required: no unchanged ownership proof"


def copilot_decision(current: bytes | None, desired: bytes, previous: str = "",
                     *, backup_exists: bool = False,
                     allow_transition: bool = True, remove: bool = False) -> tuple[str, str, bool]:
    """Apply the one-time Copilot transition, then require unchanged receipts.

    The returned boolean requires an absent-only byte backup before replacement.
    Unlink disables the marker transition; a marker alone never proves deletion.
    """
    current_hash = hashlib.sha256(current).hexdigest() if current is not None else None
    desired_hash = hashlib.sha256(desired).hexdigest()
    valid_previous = bool(re.fullmatch(r"[0-9a-fA-F]{64}", previous))
    if remove:
        if current is None:
            return "none", "destination is absent", False
        if valid_previous and current_hash == previous.lower():
            return "remove", "unchanged Copilot ownership proof", False
        return "preserve/block", "manual action required: no unchanged ownership proof", False
    action, reason = file_decision(current_hash, desired_hash, previous)
    if (action == "preserve/block" and not valid_previous and allow_transition
            and current is not None and b"<!-- compound-gpid:managed -->" in current):
        if backup_exists:
            return action, "manual action required: pre-9024 backup already exists; preserved", False
        return "update", "one-time legacy Copilot transition with pre-9024 byte backup", True
    return action, reason, False


class ReleasedContent:
    """Index release blobs once, only on demand; e.g. match an old Kilo copy.

    Missing Git history, tags or objects gives no replacement permission. The
    lookup and hashes remain in memory. No Git objects or cache files are written.
    """

    def __init__(self, source_root: Path) -> None:
        self.root = source_root.resolve()
        self.blobs: dict[str, set[str]] | None = None

    def _git(self, *args: str, content: bytes | None = None) -> bytes:
        # -C alone does not override a caller's GIT_DIR or Git object store.
        local_environment = {
            "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_NAMESPACE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
            "GIT_CEILING_DIRECTORIES",
        }
        environment = {key: value for key, value in os.environ.items()
                        if key.upper() not in local_environment}
        environment["GIT_CEILING_DIRECTORIES"] = str(self.root.parent)
        result = subprocess.run(
            ["git", "-C", str(self.root), *args], input=content,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, env=environment,
            cwd=self.root,
        )
        return result.stdout

    def matches(self, source_path: str, content: bytes) -> bool:
        """Compare filtered Git blob IDs at one exact path; e.g. CRLF copies."""
        if self.blobs is None:
            self.blobs = {}
            try:
                top_level = self._git("rev-parse", "--show-toplevel").decode("utf-8").strip()
                if Path(top_level).resolve() != self.root:
                    return False
                tags = self._git("tag", "--list").decode("utf-8").splitlines()
                for tag in tags:
                    if not re.fullmatch(r"v?\d+\.\d+\.\d+(?:\.\d+|[-+][\w.+-]+)?", tag):
                        continue
                    for entry in self._git("ls-tree", "-r", "-z", tag).split(b"\0"):
                        if not entry:
                            continue
                        metadata, path = entry.split(b"\t", 1)
                        mode, kind, blob = metadata.split()
                        if kind == b"blob" and mode in (b"100644", b"100755"):
                            self.blobs.setdefault(path.decode("utf-8"), set()).add(
                                blob.decode("ascii")
                            )
            except (OSError, subprocess.SubprocessError, ValueError, UnicodeError):
                self.blobs = {}
        known = self.blobs.get(source_path, set())
        if not known:
            return False
        try:
            blob = self._git("hash-object", "--path=" + source_path,
                             "--stdin", content=content).decode("ascii").strip()
        except (OSError, subprocess.SubprocessError, UnicodeError):
            return False
        return blob in known
