"""Installed static-data Node boundary; arbitrary source scripts are forbidden."""

import base64
import hashlib
import math
import os
import shutil
import subprocess
from importlib.metadata import distribution
from pathlib import Path

from cg_release.events import ControllerError
from cg_release.jsonio import decode_json
from cg_release.process import _capture

RESOURCES = {"docs-snapshots.js", "snapshot-data.js", "release-version.js"}


def resource(name: str) -> Path:
    """Return a wheel-record-verified resource, e.g. resource('docs-snapshots.js').

    Args: name is a fixed installed data-helper name, never a source path.
    Returns: An absolute regular file under the installed distribution.
    Raises: ControllerError for missing, aliased or changed installed bytes.
    No source code is imported and no file is modified.
    """
    if name not in RESOURCES:
        raise ControllerError(
            "E_PROFILE_RESOURCE", "Unknown installed profile resource."
        )
    dist = distribution("cg-release")
    files = {str(item).replace("\\", "/"): item for item in dist.files or []}
    result = None
    for filename in sorted(RESOURCES):
        item = files.get("cg_release_profile_data/" + filename)
        if item is None or item.hash is None or item.hash.mode != "sha256":
            raise ControllerError(
                "E_PROFILE_RESOURCE",
                "Installed resource lacks its wheel RECORD digest.",
            )
        target = Path(dist.locate_file(item)).absolute()
        if (
            target.is_symlink()
            or not target.is_file()
            or target.stat().st_nlink != 1
            or target.resolve() != target
            or target.stat().st_size > 128 * 1024
        ):
            raise ControllerError(
                "E_PROFILE_RESOURCE", "Installed resource containment is invalid."
            )
        actual = (
            base64.urlsafe_b64encode(hashlib.sha256(target.read_bytes()).digest())
            .decode()
            .rstrip("=")
        )
        if actual != item.hash.value:
            raise ControllerError(
                "E_PROFILE_RESOURCE",
                "Installed resource differs from the pinned wheel.",
            )
        if filename == name:
            result = target
    if result is None:
        raise ControllerError("E_PROFILE_RESOURCE", "Installed resource is missing.")
    return result


def run_snapshot(operation: str, args: list[str], *, cwd: Path, timeout: float = 20):
    """Run only installed snapshot import/compose, e.g. run_snapshot('import',
    [str(input_file), str(output_dir)], cwd=isolated_root).

    Args: absolute data paths must remain in cwd; timeout is finite, <=120 seconds.
    Returns: Bounded process result (64 KiB streams). Import/compose create only
    exclusive output directories; no network, source execution or remote writes.
    Raises: ControllerError for argv, containment, identity or process failure.
    NODE_OPTIONS, NODE_PATH and all credentials are removed from the child environment.
    """
    try:
        if (
            operation not in {"import", "compose"}
            or not isinstance(args, list)
            or len(args) != (2 if operation == "import" else 1)
            or isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or not 0 < timeout <= 120
            or not isinstance(cwd, Path)
            or not cwd.is_dir()
            or cwd.resolve() != cwd.absolute()
        ):
            raise ValueError

        def contained(value):
            if not isinstance(value, str) or "\0" in value:
                raise ValueError
            target = Path(value)
            if not target.is_absolute() or target.resolve() != target or target == cwd:
                raise ValueError
            target.relative_to(cwd)
            return target

        paths = [contained(value) for value in args]
        if operation == "compose":
            if paths[0].stat().st_size > 65536:
                raise ValueError
            options = decode_json(paths[0].read_text(encoding="utf-8"))
            if set(options) != {
                "releases",
                "dev",
                "out",
                "composerRevision",
                "currentDevSha",
                "stableTag",
            }:
                raise ValueError
            if (
                not isinstance(options["releases"], list)
                or not 1 <= len(options["releases"]) <= 100
            ):
                raise ValueError
            for value in [*options["releases"], options["dev"], options["out"]]:
                contained(value)
        helper = resource("docs-snapshots.js")
        executable = shutil.which("node")
        if executable is None:
            raise ControllerError(
                "E_TOOL_MISSING", "Installed Node runtime is required."
            )
        executable = str(Path(executable).resolve())
        if Path(executable).is_relative_to(cwd):
            raise ValueError
        env = {
            key: val
            for key, val in os.environ.items()
            if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
        }
        result = _capture(
            [executable, "--disable-proto=throw", "--", str(helper), operation, *args],
            cwd=cwd,
            timeout=timeout,
            max_output_bytes=65536,
            environment=env,
        )
    except subprocess.TimeoutExpired:
        raise ControllerError(
            "E_TIMEOUT", "Snapshot helper deadline exceeded."
        ) from None
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        raise ControllerError(
            "E_PROCESS_ARGUMENT", "Invalid contained snapshot process contract."
        ) from None
    if result.returncode:
        raise ControllerError(
            "E_PROCESS", "Installed snapshot helper rejected static data."
        )
    return result
