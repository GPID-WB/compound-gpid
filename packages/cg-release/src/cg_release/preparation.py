"""Apply complete validated metadata sets in a private, source-code-free worktree."""

import hashlib
import os
import re
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from cg_release.events import ControllerError
from cg_release.metadata import MAX_BLOB_BYTES, Edit, SourceBlob
from cg_release.policy import safe_path
from cg_release.process import run_process


@dataclass(frozen=True)
class TreeEntry:
    """One flattened Git tree entry, e.g. TreeEntry('a', '100644', oid)."""

    path: str
    mode: str
    oid: str


@dataclass(frozen=True)
class PreparedTree:
    """Expected reviewed tree and exact edits; temporary paths never escape."""

    tree: str
    changed_paths: tuple[str, ...]
    edits: tuple[Edit, ...]


def object_id(kind: str, content: bytes) -> str:
    """Compute a Git SHA-1 object identity, e.g. object_id('blob', b'hello')."""
    return hashlib.sha1(
        kind.encode("ascii") + b" " + str(len(content)).encode() + b"\0" + content
    ).hexdigest()


def tree_id(entries: list[TreeEntry]) -> str:
    """Validate a bounded flat inventory and hash its complete Git tree recursively.

    Args: entries include regular blobs, symlinks and submodules, not directories.
    Returns: Exact root tree ID, e.g. tree_id([TreeEntry('a', '100644', oid)]).
    Raises: ControllerError for unsafe paths, aliases, conflicts, or invalid modes.
    No source blob is executed or materialized.
    """
    root, aliases = {}, {}
    if len(entries) > 10000:
        raise ControllerError("E_TREE_SIZE", "Source inventory exceeds 10000 files.")
    for entry in entries:
        safe_path(entry.path)
        if entry.mode not in {
            "100644",
            "100755",
            "120000",
            "160000",
        } or not re.fullmatch(r"[0-9a-f]{40}", entry.oid):
            raise ControllerError("E_TREE", "Invalid source tree mode or object ID.")
        parts, node = entry.path.split("/"), root
        for index, part in enumerate(parts):
            prefix = "/".join(parts[: index + 1])
            if aliases.setdefault(prefix.casefold(), prefix) != prefix:
                raise ControllerError("E_PATH", "Source tree has case-fold aliases.")
            if index == len(parts) - 1:
                if part in node:
                    raise ControllerError(
                        "E_TREE", "Duplicate or overlapping source path."
                    )
                node[part] = entry
            else:
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    raise ControllerError(
                        "E_TREE", "Source path crosses a file or link."
                    )

    def encode(node):
        rows = []
        for name, value in node.items():
            directory = isinstance(value, dict)
            mode, oid = (
                ("40000", encode(value)) if directory else (value.mode, value.oid)
            )
            raw_name = name.encode("utf-8")
            rows.append(
                (
                    raw_name + (b"/" if directory else b""),
                    mode.encode() + b" " + raw_name + b"\0" + bytes.fromhex(oid),
                )
            )
        return object_id("tree", b"".join(raw for _, raw in sorted(rows)))

    return encode(root)


def apply_edits(
    source_tree: str,
    entries: list[TreeEntry],
    blobs: dict[str, SourceBlob],
    edits: tuple[Edit, ...],
    allowed_paths: set[str],
    *,
    create_paths: set[str] | None = None,
    runner=run_process,
    clock=time.monotonic,
    deadline: float | None = None,
) -> PreparedTree:
    """Stage only an exact approved edit set, leaving the user's checkout untouched.

    Args: source_tree/inventory must come from the approved source SHA. blobs are
        its declared regular metadata; edits come from proposed_edits. allowed_paths
        is the trusted policy's complete metadata/changelog/manifest set.
    Returns: Expected tree and changed-path allowlist, e.g. apply_edits(tree, ...).
    Raises: ControllerError on any identity, digest, staging, or inventory mismatch.
    """
    deadline = clock() + 120 if deadline is None else deadline
    create_paths = (
        {".release-manifest.json"} & allowed_paths
        if create_paths is None
        else create_paths
    )
    if not create_paths.issubset(allowed_paths):
        raise ControllerError(
            "E_EDIT_SET",
            "New paths must be explicitly declared in the complete edit set.",
        )
    if tree_id(entries) != source_tree:
        raise ControllerError(
            "E_TREE", "Source inventory does not hash to the approved tree."
        )
    if (
        not edits
        or len(edits) != len(allowed_paths)
        or {e.path for e in edits} != allowed_paths
    ):
        raise ControllerError(
            "E_EDIT_SET", "Complete policy edit set is required exactly once."
        )
    original = {e.path: e for e in entries}
    updated = dict(original)
    for edit in edits:
        safe_path(edit.path)
        SourceBlob(edit.content)
        if hashlib.sha256(edit.content).hexdigest() != edit.output_digest:
            raise ControllerError("E_EDIT_DIGEST", "Proposed output digest differs.")
        previous, blob = original.get(edit.path), blobs.get(edit.path)
        if previous is None:
            if (
                edit.path not in create_paths
                or edit.input_digest is not None
                or blob is not None
            ):
                raise ControllerError(
                    "E_EDIT_SET", "Only an explicitly declared new file may be created."
                )
            mode = "100644"
        else:
            if (
                blob is None
                or previous.mode not in {"100644", "100755"}
                or blob.mode != previous.mode
                or object_id("blob", blob.content) != previous.oid
                or hashlib.sha256(blob.content).hexdigest() != edit.input_digest
            ):
                raise ControllerError(
                    "E_EDIT_DIGEST", "Approved input blob or mode differs."
                )
            mode = previous.mode
        updated[edit.path] = TreeEntry(edit.path, mode, object_id("blob", edit.content))
    expected = tree_id(list(updated.values()))
    ordered = tuple(sorted(edits, key=lambda e: e.path))
    changed = tuple(e.path for e in ordered if original.get(e.path) != updated[e.path])
    index_input = "".join(f"{e.mode} {e.oid}\t{e.path}\0" for e in updated.values())
    if (
        len(index_input.encode()) > 65536
        or sum(len(e.content) for e in edits) > 16 * MAX_BLOB_BYTES
    ):
        raise ControllerError(
            "E_TREE_SIZE", "Preparation exceeds bounded staging capacity."
        )
    # Only controller-created regular files enter this fresh worktree. No source
    # checkout, attributes, hooks, submodules, filters, or inherited Git routing.
    with TemporaryDirectory(prefix="cg-release-prepare-") as temporary:
        worktree = Path(temporary)
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_ATTR_NOSYSTEM="1",
            GIT_TERMINAL_PROMPT="0",
        )

        def git(*args, input_text=None):
            remaining = deadline - clock()
            if remaining <= 0:
                raise ControllerError("E_DEADLINE", "Preparation deadline exceeded.")
            return runner(
                "git",
                ["-c", "core.hooksPath=" + str(worktree / "no-hooks"), *args],
                cwd=worktree,
                input_text=input_text,
                environment=env,
                timeout=min(20, remaining),
            ).stdout.strip()

        git("init", "--quiet", "--template=")
        for edit in ordered:
            path = worktree.joinpath(*edit.path.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as handle:
                handle.write(edit.content)
            info = path.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or path.resolve() != path
            ):
                raise ControllerError(
                    "E_PATH", "Staged file is not a private regular file."
                )
            # --no-filters keeps bytes independent of source or global attributes.
            oid = git("hash-object", "-w", "--no-filters", "--", edit.path)
            if oid != updated[edit.path].oid:
                raise ControllerError(
                    "E_EDIT_DIGEST", "Staged bytes differ from approved output."
                )
        git("update-index", "-z", "--index-info", input_text=index_input)
        if git("write-tree", "--missing-ok") != expected:
            raise ControllerError(
                "E_TREE", "Staged tree differs from complete expected tree."
            )
    return PreparedTree(expected, changed, ordered)
