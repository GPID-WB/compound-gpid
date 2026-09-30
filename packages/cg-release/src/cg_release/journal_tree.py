"""Incremental canonical Git trees for the fixed append-only journal path grammar."""

from bisect import bisect_left

from cg_release.git_journal import blob_id
from cg_release.preparation import object_id


class _Directory:
    def __init__(self):
        self.names, self.rows, self.raw = [], {}, bytearray()
        self.width = None

    def set(self, name, oid, *, directory=False):
        key = name + ("/" if directory else "")
        row = (
            (b"40000 " if directory else b"100644 ")
            + name.encode("ascii")
            + b"\0"
            + bytes.fromhex(oid)
            if oid
            else None
        )
        old = self.rows.get(key)
        if old == row:
            return False
        index = bisect_left(self.names, key)
        # Each journal leaf directory has fixed-width names. The small root and
        # an event ordinal wider than ten digits use the general offset path.
        offset = (
            index * self.width
            if self.width
            else sum(len(self.rows[k]) for k in self.names[:index])
        )
        self.raw[offset : offset + len(old or b"")] = row or b""
        if old is not None:
            del self.rows[key]
            self.names.pop(index)
        if row is not None:
            self.rows[key] = row
            self.names.insert(index, key)
        widths = (
            {len(value) for value in self.rows.values()}
            if self.width is None or (row is not None and len(row) != self.width)
            else {self.width}
        )
        self.width = next(iter(widths)) if len(widths) == 1 else None
        return True


class JournalTree:
    """Apply verified journal deltas, e.g. tree.update(transaction_files(raw, record)).

    Returns the exact canonical root OID after each delta. The head inventory is
    read once; historical trees are authenticated by their signed commit OIDs.
    No history is truncated, compacted, cached across operations, or rewritten.
    Leaf entries are updated once per change, not parsed once per later event.
    Canonical SHA-1 hashing still consumes each changed flat directory's binary
    bytes; hash_bytes reports this cost rather than claiming linear hashing.
    """

    def __init__(self):
        self.directories = {"": _Directory()}
        self.paths = {}
        self.entry_updates = self.hash_bytes = 0
        self.oid = object_id("tree", b"")

    def _hash(self, directory):
        self.hash_bytes += len(directory.raw)
        return object_id("tree", bytes(directory.raw))

    def update(self, changes):
        """Update exact regular journal paths and return the canonical Git root ID."""
        root = self.directories[""]
        for path, raw in changes.items():
            parent, _, name = path.rpartition("/")
            oid = blob_id(raw) if raw is not None else None
            if self.paths.get(path) == oid:
                continue
            if oid is None:
                self.paths.pop(path)
            else:
                self.paths[path] = oid
            directory = self.directories.setdefault(parent, _Directory())
            directory.set(name, oid)
            self.entry_updates += 1
            if parent:
                root.set(
                    parent,
                    self._hash(directory) if directory.raw else None,
                    directory=True,
                )
                self.entry_updates += 1
        self.oid = self._hash(root)
        return self.oid
