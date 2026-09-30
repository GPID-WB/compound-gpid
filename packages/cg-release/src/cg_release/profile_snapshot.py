"""Bounded static-data verification shared by the optional profile hook workers."""

import base64
import hashlib
import json
import re

from semver import Version

from cg_release.events import ControllerError
from cg_release.jsonio import _decode
from cg_release.snapshot_contract import (
    MAX_ENVELOPE_BYTES,
    MAX_SNAPSHOT_BYTES,
    validate_paths,
)


def verify_snapshot(
    raw: bytes,
    *,
    tag: str | None,
    sha: str,
    run_id: int,
    run_attempt: int,
    kind="release",
) -> dict:
    """Verify static bytes before approval, e.g. verify_snapshot(raw, tag=tag,
    sha=sha, run_id=12, run_attempt=1).

    Args: raw is a <=64 MiB UTF-8 envelope with <=32 MiB decoded files; the
    expected kind/tag/SHA/run tuple comes from trusted registration, not source.
    Returns: Exact schema-v2 metadata, without changing its bytes or digest.
    Raises: ControllerError for malformed data, paths, capacity or identity.
    This function has no filesystem or remote effects.
    """
    try:
        if kind not in {"release", "dev"} or (kind == "dev" and tag is not None):
            raise ValueError
        if kind == "release":
            if not isinstance(tag, str) or len(tag) > 255 or not tag.startswith("v"):
                raise ValueError
            if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", tag):
                Version.parse(tag[1:])
                if not tag.isascii():
                    raise ValueError
        if not isinstance(raw, bytes) or len(raw) > MAX_ENVELOPE_BYTES:
            raise ValueError
        value = _decode(raw.decode("utf-8"), MAX_ENVELOPE_BYTES)
        record, files = value["record"], value["files"]
        if (
            set(value) != {"record", "files"}
            or set(record)
            != {
                "schemaVersion",
                "kind",
                "tag",
                "sha",
                "runId",
                "runAttempt",
                "files",
                "snapshotDigest",
            }
            or record["schemaVersion"] != 2
            or type(record["schemaVersion"]) is not int
            or kind not in {"release", "dev"}
            or record["kind"] != kind
            or record["tag"] != tag
            or record["sha"] != sha
            or not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
            or type(record["runId"]) is not int
            or type(record["runAttempt"]) is not int
            or record["runId"] != run_id
            or record["runAttempt"] != run_attempt
            or not 1 <= run_id <= 9007199254740991
            or not 1 <= run_attempt <= 9007199254740991
            or not isinstance(files, dict)
            or not 5 <= len(files) <= 10000
            or set(files) != set(record["files"])
            or len({p.casefold() for p in files}) != len(files)
            or not {
                "index.html",
                "navigation.json",
                "assets/site.css",
                "assets/site.js",
                ".nojekyll",
            }.issubset(files)
        ):
            raise ValueError
        validate_paths(files)
        if kind == "dev":
            directories = {
                p.rsplit("/", n)[0] for p in files for n in range(1, p.count("/") + 1)
            }
            if (
                len(files) > 1000
                or len(directories) > 1000
                or any(len(p) > 251 or p.count("/") > 31 for p in files)
            ):
                raise ValueError
        total = 0
        for name, content in files.items():
            data = base64.b64decode(content, validate=True)
            total += len(data)
            if (
                base64.b64encode(data).decode() != content
                or total > MAX_SNAPSHOT_BYTES
                or hashlib.sha256(data).hexdigest() != record["files"][name]
            ):
                raise ValueError
        identity = {
            key: record[key]
            for key in (
                "schemaVersion",
                "kind",
                "tag",
                "sha",
                "runId",
                "runAttempt",
                "files",
            )
        }
        identity["files"] = dict(sorted(record["files"].items()))
        serialized = json.dumps(identity, separators=(",", ":"), ensure_ascii=False)
        if hashlib.sha256(serialized.encode()).hexdigest() != record["snapshotDigest"]:
            raise ValueError
        return record
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise ControllerError(
            "E_PROFILE_SNAPSHOT", "Snapshot inventory or source/run identity differs."
        ) from None
