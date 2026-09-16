"""Read declared regular Git blobs by exact object identity, never checkout paths."""

import base64
import hashlib
import re

from cg_release.events import ControllerError
from cg_release.github import GitHubReads
from cg_release.metadata import MAX_BLOB_BYTES, SourceBlob
from cg_release.policy import safe_path


def commit_tree(api: GitHubReads, sha: str) -> str:
    """Resolve one commit tree, e.g. commit_tree(api, exact_sha).

    Args:
        api: Bounded read adapter.
        sha: Exact expected commit ID.
    Returns:
        Verified tree ID from the exact commit response.
    Raises:
        ControllerError: Missing or malformed commit identity.
    """
    value = api.get("git/commits/" + sha)
    try:
        tree = value["tree"]["sha"]
        if value["sha"] != sha or not re.fullmatch(r"[0-9a-f]{40}", tree):
            raise ValueError
        return tree
    except (TypeError, KeyError, ValueError):
        raise ControllerError(
            "E_RESPONSE", "Exact source commit/tree cannot be verified."
        ) from None


def read_blobs(
    api: GitHubReads, tree: str, paths: list[str], *, optional: set[str] | None = None
) -> dict[str, SourceBlob]:
    """Read bounded declared files, e.g. read_blobs(api, tree, ['package.json']).

    Args:
        api: Bounded read adapter.
        tree: Exact commit tree ID.
        paths: Portable declared paths. No symlink or submodule traversal.
        optional: Paths allowed to be absent, e.g. a new release manifest.
    Returns:
        Regular immutable UTF-8 blobs, checked against Git SHA-1 identities.
    Raises:
        ControllerError: Missing, aliased, nonregular, truncated, or corrupt input.
    """
    cache, result = {}, {}
    optional = optional or set()
    for path in paths:
        safe_path(path)
        parts, current = path.split("/"), tree
        for index, part in enumerate(parts):
            if current not in cache:
                value = api.get("git/trees/" + current)
                if (
                    not isinstance(value, dict)
                    or value.get("sha") != current
                    or value.get("truncated") is not False
                    or not isinstance(value.get("tree"), list)
                ):
                    raise ControllerError(
                        "E_TREE", "Source tree is incomplete or has the wrong identity."
                    )
                entries = value["tree"]
                if any(
                    not isinstance(e, dict) or not isinstance(e.get("path"), str)
                    for e in entries
                ):
                    raise ControllerError("E_TREE", "Malformed source tree entry.")
                if len({e["path"].casefold() for e in entries}) != len(entries):
                    raise ControllerError(
                        "E_TREE", "Source tree has case-fold aliases."
                    )
                cache[current] = {e["path"]: e for e in entries}
            entry = cache[current].get(part)
            if entry is None:
                if any(name.casefold() == part.casefold() for name in cache[current]):
                    raise ControllerError("E_PATH", "Declared path has a case alias.")
                if path in optional:
                    break
                raise ControllerError(
                    "E_BLOB", "Declared file is absent from the exact source tree."
                )
            oid = entry.get("sha")
            if not isinstance(oid, str) or not re.fullmatch(r"[0-9a-f]{40}", oid):
                raise ControllerError("E_TREE", "Invalid Git object identity.")
            if index != len(parts) - 1:
                if entry.get("type") != "tree" or entry.get("mode") != "040000":
                    raise ControllerError(
                        "E_TREE", "Declared path traverses a non-directory object."
                    )
                current = oid
                continue
            if entry.get("type") != "blob" or entry.get("mode") not in {
                "100644",
                "100755",
            }:
                raise ControllerError(
                    "E_BLOB", "Declared source must be a regular Git blob."
                )
            if "size" in entry and (
                type(entry["size"]) is not int
                or not 0 <= entry["size"] <= MAX_BLOB_BYTES
            ):
                raise ControllerError(
                    "E_BLOB", "Declared tree blob size exceeds the input limit."
                )
            value = api.get("git/blobs/" + oid)
            try:
                if (
                    value["sha"] != oid
                    or value["encoding"] != "base64"
                    or type(value["size"]) is not int
                    or not 0 <= value["size"] <= MAX_BLOB_BYTES
                ):
                    raise ValueError
                raw = base64.b64decode(
                    value["content"].replace("\n", ""), validate=True
                )
                actual = hashlib.sha1(
                    b"blob " + str(len(raw)).encode() + b"\0" + raw
                ).hexdigest()
                if len(raw) != value["size"] or actual != oid:
                    raise ValueError
            except (KeyError, TypeError, ValueError, AttributeError):
                raise ControllerError(
                    "E_BLOB", "Source blob identity, size, or encoding does not match."
                ) from None
            result[path] = SourceBlob(raw, entry["mode"])
    return result
