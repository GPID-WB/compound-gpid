"""Restore proven installer wrapper output before a pinned checkout.

Usage: python scripts/cg_restore_installer_wrappers.py --root <install-clone>
Only the documented 9020/9021 tracked wrapper set is eligible. Staged edits,
unknown paths, and content that differs from the committed installer output
stop the operation before any restore. This is not a general dirty-tree repair.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


SHELL_NAMES = (
    "link", "unlink", "update", "index", "brain-init", "token-audit",
    "autopilot-control", "diff-summary", "log-summary", "problems-summary",
    "test-summary", "tree-summary", "kilo", "skill", "help",
    "render-artifact", "release", "publish-markdown",
)
KNOWN_PATHS = {f"bin/cg-{name}" for name in SHELL_NAMES} | {
    f"bin/cg-{name}.cmd" for name in ("link", "unlink", "update")
}


def _git(root: Path, *args: str) -> bytes:
    """Read Git output, retaining native errors on failure."""
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False,
    )
    if result.returncode:
        sys.stderr.buffer.write(result.stderr)
        raise ValueError(f"git {' '.join(args)} failed ({result.returncode})")
    return result.stdout


def _unquote_heredoc(body: str, values: dict[str, str]) -> bytes:
    """Expand only the known installer loop variables, never execute shell code."""
    for key, value in values.items():
        body = body.replace(f"${key}", value)
    body = re.sub(r"\\([$`\\])", r"\1", body)
    return (body + "\n").encode("utf-8")


def _shell_outputs(source: str) -> dict[str, bytes]:
    """Read the fixed wrapper heredocs from a committed installer."""
    outputs = {}
    loop = re.search(
        r'for cmd in link unlink update; do.*?cat > "\$WRAPPER" <<EOF\n'
        r'(.*?)\nEOF', source, re.S,
    )
    if loop:
        for name in ("link", "unlink", "update"):
            outputs[f"bin/cg-{name}"] = _unquote_heredoc(
                loop.group(1), {"cmd": name},
            )
    for match in re.finditer(
        r'WRAPPER="\$BIN_DIR/(cg-[a-z-]+)"\n'
        r'cat > "\$WRAPPER" <<\'EOF\'\n(.*?)\nEOF', source, re.S,
    ):
        relative = f"bin/{match.group(1)}"
        if relative in KNOWN_PATHS:
            outputs[relative] = (match.group(2) + "\n").encode("utf-8")
    summaries = re.search(
        r"for spec in \\\n(.*?)IFS='\|' read -r name kind description <<< "
        r'"\$spec".*?cat > "\$WRAPPER" <<EOF\n(.*?)\nEOF', source, re.S,
    )
    if summaries:
        for name, kind, description in re.findall(
            r'"([a-z-]+)\|([^|"\n]+)\|([^"\n]+)"', summaries.group(1),
        ):
            relative = f"bin/cg-{name}"
            if relative in KNOWN_PATHS:
                outputs[relative] = _unquote_heredoc(
                    summaries.group(2), dict(name=name, kind=kind,
                                             description=description),
                )
    return outputs


def restore_installer_wrappers(root: Path) -> list[str]:
    """Restore exact known output, e.g. a 9021 POSIX installed wrapper.

    Args:
        root: Disposable fixture or installation Git clone root.
    Returns:
        Paths whose proven installer output was restored from HEAD.
    Raises:
        ValueError: Tracked user changes or an unsuccessful Git operation.
    """
    if _git(root, "diff", "--cached", "--name-only", "-z"):
        raise ValueError("Staged tracked changes remain; preserve them before updating.")
    dirty = [os.fsdecode(path) for path in
             _git(root, "diff", "--name-only", "-z", "HEAD").split(b"\0") if path]
    unknown = sorted(set(dirty) - KNOWN_PATHS)
    if unknown:
        raise ValueError("Tracked user changes remain: " + ", ".join(unknown))
    if not dirty:
        return []
    source = _git(root, "show", "HEAD:scripts/install.sh").decode("utf-8")
    outputs = _shell_outputs(source.replace("\r\n", "\n"))
    ps_source = _git(root, "show", "HEAD:install.ps1").decode("utf-8")
    ps_template = (
        '"@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass '
        '-File `"%~dp0..\\scripts\\$script.ps1`" %*`r`n"'
    )
    if ps_template in ps_source:
        for name in ("link", "unlink", "update"):
            outputs[f"bin/cg-{name}.cmd"] = (
                '@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass '
                f'-File "%~dp0..\\scripts\\{name}.ps1" %*\r\n'
            ).encode("ascii")
    for relative in dirty:
        path = root / relative
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError(f"Unsafe installer wrapper; preserving: {relative}")
        if os.name != "nt" and bool(metadata.st_mode & stat.S_IXUSR) != (
            not relative.endswith(".cmd")
        ):
            raise ValueError(f"User-modified wrapper mode; preserving: {relative}")
        current = path.read_bytes()
        committed = _git(root, "show", f"HEAD:{relative}")
        expected = outputs.get(relative)
        if current != committed and (
            expected is None or current != expected
        ):
            raise ValueError(f"User-modified installer wrapper; preserving: {relative}")
    if dirty:
        _git(root, "restore", "--source=HEAD", "--worktree", "--", *dirty)
    if _git(root, "diff", "--name-only", "-z", "HEAD"):
        raise ValueError("Tracked changes remain after installer wrapper restore.")
    return dirty


def main() -> int:
    """Run the narrow restoration CLI and report preserved user changes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        restored = restore_installer_wrappers(args.root)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"Pinned update stopped: {exc}\n")
        return 1
    if restored:
        sys.stdout.write("Restored proven installer output: " + ", ".join(restored) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
