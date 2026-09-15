"""Portable snapshot path and capacity contract mirrored by docs-snapshots.js."""

import re

MAX_ENVELOPE_BYTES = 64 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 32 * 1024 * 1024
MAX_FILES = 10000
MAX_DEPLOYMENT_BYTES = 512 * 1024 * 1024
MAX_DEPTH = 33
REQUIRED = {
    "index.html",
    "navigation.json",
    "assets/site.css",
    "assets/site.js",
    ".nojekyll",
}


def validate_paths(paths, *, deployment=False) -> None:
    """Validate the whole directory graph before writes, e.g. validate_paths(files).

    Args: paths is the complete inventory; deployment permits dev/releases roots.
    Returns: None. Raises ValueError for aliases, file parents, grammar or capacity.
    No filesystem or remote effects occur.
    """
    if not 1 <= len(paths) <= MAX_FILES:
        raise ValueError("snapshot file capacity")
    nodes = {}
    for name in paths:
        if not isinstance(name, str) or len(name) > 255:
            raise ValueError("snapshot path length")
        parts = name.split("/")
        if len(parts) > MAX_DEPTH or (
            not deployment and parts[0].lower() in {"dev", "releases"}
        ):
            raise ValueError("snapshot reserved path or depth")
        for index, part in enumerate(parts):
            if (
                not re.fullmatch(r"[A-Za-z0-9_.+-]+", part)
                or part.endswith(".")
                or part.lower() in {".", "..", "__proto__", "constructor", "prototype"}
                or re.match(r"^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)", part, re.I)
            ):
                raise ValueError("snapshot path grammar")
            node = "/".join(parts[: index + 1])
            identity = (node, index == len(parts) - 1)
            if node.lower() in nodes and nodes[node.lower()] != identity:
                raise ValueError("snapshot directory alias or file parent")
            nodes[node.lower()] = identity
    if sum(not value[1] for value in nodes.values()) + 1 > MAX_FILES:
        raise ValueError("snapshot directory capacity")
