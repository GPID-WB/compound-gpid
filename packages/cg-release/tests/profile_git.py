"""Exact nested Git objects for offline profile transport, with no helper mocks."""

import base64
import json
from types import SimpleNamespace
from urllib.parse import urlsplit

from cg_release.git_journal import blob_id
from cg_release.preparation import TreeEntry, tree_id


class GitData:
    """Content-addressed provider fixture for nested source and generated manifests."""

    def __init__(self):
        self.blobs, self.trees, self.flat, self.calls = {}, {}, {}, []
        self.releases = []

    def tree(self, files):
        """Build real Git tree IDs from bytes, including intermediate directories."""
        rows = []
        for path, raw in files.items():
            oid = blob_id(raw)
            self.blobs[oid] = raw
            rows.append(TreeEntry(path, "100644", oid))
        root = tree_id(rows)
        direct, dirs = [], {}
        for entry in rows:
            if "/" in entry.path:
                name, rest = entry.path.split("/", 1)
                dirs.setdefault(name, {})[rest] = self.blobs[entry.oid]
            else:
                direct.append(
                    {
                        "path": entry.path,
                        "mode": entry.mode,
                        "type": "blob",
                        "sha": entry.oid,
                    }
                )
        for name, children in dirs.items():
            direct.append(
                {
                    "path": name,
                    "mode": "040000",
                    "type": "tree",
                    "sha": self.tree(children),
                }
            )
        self.trees[root] = {"sha": root, "truncated": False, "tree": direct}
        self.flat[root] = {
            "sha": root,
            "truncated": False,
            "tree": [
                {"path": e.path, "mode": e.mode, "type": "blob", "sha": e.oid}
                for e in rows
            ],
        }
        return root

    def transport(self, tool, args, **kwargs):
        assert tool == "gh" and args[:3] == ["api", "--method", "GET"]
        self.calls.append(args[-1])
        resource = urlsplit("https://unused/" + args[-1])
        path = resource.path.removeprefix("/repos/owner/repo/")
        if path.startswith("git/trees/"):
            value = (self.flat if "recursive=1" in resource.query else self.trees)[
                path[10:]
            ]
        elif path.startswith("git/blobs/"):
            raw = self.blobs[path[10:]]
            value = {
                "sha": path[10:],
                "encoding": "base64",
                "size": len(raw),
                "content": base64.b64encode(raw).decode(),
            }
        elif path == "releases":
            value = self.releases
        elif args[-1] == "graphql":
            value = {
                "data": {
                    "repository": {
                        "databaseId": 123,
                        "refs": {"nodes": [], "pageInfo": {"hasNextPage": False}},
                    }
                }
            }
        else:
            raise AssertionError(path)
        return SimpleNamespace(
            returncode=0, stdout="HTTP/2.0 200 OK\n\n" + json.dumps(value)
        )
