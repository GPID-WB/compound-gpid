"""Optional GPID native-test dependency receipts, independent of core runtime deps."""

import hashlib
import importlib.metadata
import os
import platform
import re
import sys
import tomllib
from pathlib import Path

from packaging.markers import Marker

from cg_release.events import ControllerError
from cg_release.jsonio import decode_json

LOCK = "packages/cg-release/uv.lock"
NATIVE_ARTIFACT = "release-output/native-environment.json"


def environment(root: Path) -> dict:
    """Inspect the selected isolated interpreter against root's locked distributions.

    Returns a JSON-safe dependency identity; reads files and imports yaml/pytest,
    but installs nothing. Raises ControllerError on wrong interpreter or lock.
    Example: environment(Path.cwd()) in the unprivileged source build.
    """
    try:
        expected = Path(os.environ["CG_RELEASE_NATIVE_PYTHON"])
        # Unix venv launchers can share one symlink target. Compare the invoked
        # venv path, not just the common base interpreter inode.
        if (
            not expected.is_absolute()
            or os.path.normcase(os.path.abspath(expected))
            != os.path.normcase(os.path.abspath(sys.executable))
            or expected.parent.parent != Path(sys.prefix)
            or sys.prefix == sys.base_prefix
        ):
            raise ValueError
        import pytest
        import yaml

        packages = {
            re.sub(r"[-_.]+", "-", d.metadata["Name"]).lower(): d.version
            for d in importlib.metadata.distributions()
        }
        if (
            packages["pyyaml"] != yaml.__version__
            or packages["pytest"] != pytest.__version__
        ):
            raise ValueError
        result = {
            "gate_owner": "gpid-native-profile",
            "lock_sha256": hashlib.sha256((root / LOCK).read_bytes()).hexdigest(),
            "python": platform.python_version(),
            "platform": sys.platform,
            "packages": packages,
        }
        _dependencies(result, (root / LOCK).read_bytes())
        return result
    except (KeyError, ValueError, TypeError, OSError, ImportError):
        raise ControllerError(
            "E_NATIVE_ENVIRONMENT", "Locked native interpreter is required."
        ) from None


def _dependencies(data: dict, lock: bytes) -> None:
    rows = tomllib.loads(lock.decode())["package"]
    roots = [r for r in rows if r.get("source") == {"editable": "."}]
    if len(roots) != 1 or data["platform"] not in {"linux", "win32", "darwin"}:
        raise ValueError
    marker_env = dict(
        python_full_version=data["python"],
        python_version=".".join(data["python"].split(".")[:2]),
        sys_platform=data["platform"],
        os_name="nt" if data["platform"] == "win32" else "posix",
        implementation_name="cpython",
        implementation_version=data["python"],
        platform_python_implementation="CPython",
        extra="",
    )
    by_name = {}
    for row in rows:
        by_name.setdefault(row["name"], []).append(row)
    root = roots[0]
    pending = list(root["dependencies"])
    for group in ("dev", "gpid-native"):
        pending.extend(root["dev-dependencies"][group])
    locked = {}
    while pending:
        dep = pending.pop()
        if dep.get("marker") and not Marker(dep["marker"]).evaluate(marker_env):
            continue
        matches = [
            r
            for r in by_name[dep["name"]]
            if "registry" in r.get("source", {})
            and ("version" not in dep or r["version"] == dep["version"])
            and ("source" not in dep or r["source"] == dep["source"])
        ]
        if len(matches) != 1:
            raise ValueError
        row = matches[0]
        if row["name"] in locked:
            if locked[row["name"]] != row["version"]:
                raise ValueError
            continue
        locked[row["name"]] = row["version"]
        pending.extend(row.get("dependencies", []))
    packages = data["packages"]
    if (
        data["gate_owner"] != "gpid-native-profile"
        or not re.fullmatch(r"3\.(?:1[1-9]|[2-9][0-9])\.[0-9]+", data["python"])
        or data["lock_sha256"] != hashlib.sha256(lock).hexdigest()
        or not isinstance(packages, dict)
        or not {"pyyaml", "pytest"}.issubset(packages)
        or packages != locked
    ):
        raise ValueError


def verify_environment(
    raw: bytes,
    lock: bytes,
    *,
    sha: str,
    run_id: int,
    run_attempt: int,
    expected_platform: str = "linux",
    python_minor: str = "3.12",
) -> dict:
    """Verify a downloaded receipt against exact source lock bytes and registered run.

    Returns the validated dictionary. Raises ControllerError for missing, oversized,
    malformed or substituted native evidence. No writes or imports of target code.
    Example: verify_environment(raw, lock, sha=sha, run_id=12, run_attempt=1).
    """
    try:
        if len(raw) > 65536:
            raise ValueError
        data = decode_json(raw.decode("utf-8"))
        if set(data) != {
            "schema_version",
            "source_sha",
            "run_id",
            "run_attempt",
            "gate_owner",
            "lock_sha256",
            "python",
            "platform",
            "packages",
        }:
            raise ValueError
        for key, value in {
            "schema_version": 1,
            "source_sha": sha,
            "run_id": run_id,
            "run_attempt": run_attempt,
        }.items():
            if type(data[key]) is not type(value) or data[key] != value:
                raise ValueError
        if data["platform"] != expected_platform or not data["python"].startswith(
            python_minor + "."
        ):
            raise ValueError
        _dependencies(data, lock)
        return data
    except (ValueError, TypeError, KeyError, UnicodeError, ControllerError):
        raise ControllerError(
            "E_NATIVE_ENVIRONMENT", "Exact locked native evidence is required."
        ) from None
