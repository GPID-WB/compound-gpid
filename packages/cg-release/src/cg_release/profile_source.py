"""Exact source/default durable payload inventory for the optional GPID profile."""

from cg_release.events import ControllerError
from cg_release.github import decode_json
from cg_release.source_blobs import read_blobs

REQUIRED_FILES = (
    "compound-gpid.md",
    ".github/shared/module-registry.json",
    ".github/shared/target-mapping.json",
    "releases/latest.json",
)


def source_blobs(api, tree: str, tag: str, *, default_tree: str) -> dict:
    """Read exact source/default trees before writes; return declared source blobs.

    Args: tree/default_tree are immutable Git trees, tag is the proposed identity.
    Returns: Source blobs, e.g. source_blobs(api, tree, tag, default_tree=trusted).
    Raises: ControllerError for stranded history or conflicting historical bytes.
    Read-only. An older source cannot conceal protected-default obligations.
    """
    paths_by_tree = {}
    for root in dict.fromkeys((tree, default_tree)):
        rows = api.tree(root, recursive=True)["tree"]
        paths = [
            row["path"]
            for row in rows
            if row["path"].startswith("releases/") and row["path"].endswith(".json")
        ]
        if len(set(paths)) != len(paths):
            raise ControllerError(
                "E_PROFILE_HISTORY", "Duplicate durable payload paths."
            )
        paths_by_tree[root] = set(paths)
    paths, default_paths = paths_by_tree[tree], paths_by_tree[default_tree]
    release_rows, refs = api.pages("releases"), api.refs()
    releases = {r.get("tag_name"): r for r in release_rows}
    if len(releases) != len(release_rows) or None in releases:
        raise ControllerError(
            "E_PROFILE_HISTORY", "Ambiguous remote release inventory."
        )
    for path in paths | default_paths:
        if path == "releases/latest.json":
            continue
        name = path[len("releases/") : -5]
        release = releases.get(name)
        if (
            release is None
            or release.get("draft") is not False
            or not release.get("published_at")
            or len([r for r in refs if r.get("ref") == "refs/tags/" + name]) != 1
        ):
            raise ControllerError(
                "E_PROFILE_HISTORY",
                "Durable payload lacks a published Release; "
                "use reviewed legacy recovery.",
            )
    wanted = set(REQUIRED_FILES) | paths | {f"releases/{tag}.json"}
    blobs = read_blobs(api, tree, sorted(wanted), optional={f"releases/{tag}.json"})
    historical = read_blobs(
        api, default_tree, sorted(default_paths - {"releases/latest.json"})
    )
    for path in (paths | default_paths) - {"releases/latest.json"}:
        values = [group[path].content for group in (blobs, historical) if path in group]
        payload = decode_json(values[0].decode())
        if (
            any(value != values[0] for value in values)
            or not isinstance(payload, dict)
            or payload.get("tag") != path[len("releases/") : -5]
        ):
            raise ControllerError(
                "E_PROFILE_HISTORY",
                "Historical payload bytes or tag differ between exact trees.",
            )
    return blobs
