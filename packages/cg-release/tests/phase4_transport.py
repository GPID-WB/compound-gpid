"""Offline GitHub wire provider for the real Phase 4 worker and registration."""

import base64
import hashlib
import io
import json
import subprocess
import zipfile
from datetime import datetime
from urllib.parse import unquote

from worker_transport import WorkerTransport

from cg_release.events import ControllerError
from cg_release.preparation import TreeEntry, object_id, tree_id


class Phase4Transport(WorkerTransport):
    def __init__(self, cwd):
        super().__init__(cwd)
        self.prs, self.prep_commits, self.prep_writes = [], {}, []
        self.build = None
        self.raw_archive = b""
        self.lost_preparation = None

    def install_source(self, sha):
        super().install_source(sha)
        old = self.commits[sha]["commit"]["tree"]["sha"]
        rows = self.trees[old]["tree"]
        raw = b"version = 1\n"
        oid = object_id("blob", raw)
        self.objects[oid] = raw
        rows.append({"path": "uv.lock", "mode": "100644", "type": "blob", "sha": oid})
        root = tree_id([TreeEntry(r["path"], r["mode"], r["sha"]) for r in rows])
        self.trees[root] = {"sha": root, "tree": rows, "truncated": False}
        self.commits[sha]["commit"]["tree"]["sha"] = root

    def get(self, endpoint, **kwargs):
        endpoint = unquote(endpoint)
        if endpoint == "actions/workflows/release-controller-publish.yml/runs":
            return {"total_count": 0, "workflow_runs": []}
        if endpoint.startswith("git/ref/heads/"):
            name = endpoint.removeprefix("git/ref/heads/")
            if name not in self.branches:
                raise ControllerError("E_NOT_FOUND", "Missing ref.")
            return {
                "ref": "refs/heads/" + name,
                "object": {"sha": self.branches[name], "type": "commit"},
            }
        if endpoint.startswith("git/blobs/") and endpoint[10:] not in self.objects:
            raise ControllerError("E_NOT_FOUND", "Missing blob.")
        if endpoint.startswith("git/trees/") and endpoint[10:] not in self.trees:
            raise ControllerError("E_NOT_FOUND", "Missing tree.")
        if endpoint.startswith("git/commits/"):
            oid = endpoint[12:]
            if oid in self.prep_commits:
                return self.prep_commits[oid]
            if oid not in self.commits:
                raise ControllerError("E_NOT_FOUND", "Missing commit.")
        if endpoint == "pulls":
            return self.prs
        if endpoint == "pulls/42":
            return self.prs[0]
        if endpoint == "pulls/42/reviews":
            return [
                {
                    "id": 12,
                    "user": {"id": 8},
                    "state": "APPROVED",
                    "commit_id": self.prs[0]["head"]["sha"],
                }
            ]
        if endpoint.endswith("/check-runs"):
            return {
                "total_count": 1,
                "check_runs": [
                    {
                        "id": 14,
                        "name": "release-controller-ci",
                        "head_sha": self.prs[0]["head"]["sha"],
                        "status": "completed",
                        "conclusion": "success",
                        "app": {"id": 15368},
                        "check_suite": {"id": 15},
                    }
                ],
            }
        if endpoint == "actions/runs":
            return {
                "total_count": 1,
                "workflow_runs": [
                    {
                        "id": 19,
                        "run_attempt": 1,
                        "head_sha": self.prs[0]["head"]["sha"],
                        "status": "completed",
                        "conclusion": "success",
                        "check_suite_id": 15,
                        "path": ".github/workflows/release-controller-ci.yml",
                    }
                ],
            }
        if endpoint == "actions/runs/21/attempts/1":
            return {**self.build, "run_attempt": 1}
        if endpoint == "actions/runs/21":
            return self.build
        if endpoint == "actions/runs/21/attempts/1/jobs":
            return {"total_count": len(self.jobs), "jobs": self.jobs}
        if endpoint == "check-suites/31":
            return {"id": 31, "head_sha": self.build["head_sha"], "app": {"id": 15368}}
        if endpoint == "actions/runs/21/artifacts":
            return {
                "total_count": 1,
                "artifacts": [
                    {
                        "id": 51,
                        "name": "release-assets",
                        "expired": False,
                        "size_in_bytes": len(self.raw_archive),
                        "digest": "sha256:"
                        + hashlib.sha256(self.raw_archive).hexdigest(),
                        "workflow_run": {"id": 21, "head_sha": self.build["head_sha"]},
                    }
                ],
            }
        return super().get(endpoint, **kwargs)

    def run(self, tool, argv, **kwargs):
        if kwargs.get("binary_output"):
            assert argv[-1].endswith("/actions/artifacts/51/zip")
            return subprocess.CompletedProcess(argv, 0, self.raw_archive, b"")
        if (
            tool != "gh"
            or argv[argv.index("--method") + 1] == "GET"
            or argv[-1] == "graphql"
        ):
            return super().run(tool, argv, **kwargs)
        endpoint = argv[-1].removeprefix(f"repos/{self.slug}/")
        if endpoint not in {
            "git/blobs",
            "git/trees",
            "git/commits",
            "git/refs",
            "pulls",
        }:
            return super().run(tool, argv, **kwargs)
        payload = json.loads(kwargs["input_text"])
        self.prep_writes.append(endpoint)
        if endpoint == "git/blobs":
            raw = base64.b64decode(payload["content"])
            self.objects[object_id("blob", raw)] = raw
        elif endpoint == "git/trees":
            base = {r["path"]: r for r in self.trees[payload["base_tree"]]["tree"]}
            base.update({r["path"]: r for r in payload["tree"]})
            root = tree_id(
                [TreeEntry(r["path"], r["mode"], r["sha"]) for r in base.values()]
            )
            self.trees[root] = {
                "sha": root,
                "tree": list(base.values()),
                "truncated": False,
            }
        elif endpoint == "git/commits":

            def identity(person):
                stamp = int(datetime.fromisoformat(person["date"]).timestamp())
                return f"{person['name']} <{person['email']}> {stamp} +0000"

            raw = (
                f"tree {payload['tree']}\nparent {payload['parents'][0]}\n"
                f"author {identity(payload['author'])}\n"
                f"committer {identity(payload['committer'])}\n\n{payload['message']}"
            ).encode()
            oid = object_id("commit", raw)
            self.prep_commits[oid] = {
                "sha": oid,
                "tree": {"sha": payload["tree"]},
                "parents": [{"sha": p} for p in payload["parents"]],
            }
        elif endpoint == "git/refs":
            self.branches[payload["ref"].removeprefix("refs/heads/")] = payload["sha"]
        else:
            self.prs.append(
                {
                    "number": 42,
                    "id": 99,
                    "state": "open",
                    "merged_at": None,
                    "merged": False,
                    "draft": False,
                    "head": {
                        "ref": payload["head"],
                        "sha": self.branches[payload["head"]],
                        "repo": {"id": 123},
                    },
                    "base": {"ref": payload["base"], "repo": {"id": 123}},
                }
            )
        if self.lost_preparation == endpoint:
            self.lost_preparation = None
            raise ControllerError("E_TIMEOUT", "Lost response after preparation write.")
        return subprocess.CompletedProcess(argv, 0, "HTTP/2.0 201 Created\n\n{}", "")

    def merge(self):
        head = self.prs[0]["head"]["sha"]
        self.prs[0].update(
            state="closed",
            merged=True,
            merged_at="2026-09-12T00:00:00Z",
            merge_commit_sha=head,
        )
        self.branches["feature"] = head

    def begin_build(self, sealed):
        self.build = {
            "id": 21,
            "run_attempt": 1,
            "event": "workflow_dispatch",
            "path": sealed["workflow_path"],
            "head_sha": sealed["controller_sha"],
            "head_branch": "main",
            "repository": {"id": 123},
            "actor": {"id": 77},
            "status": "in_progress",
            "conclusion": None,
            "check_suite_id": 31,
        }
        self.jobs = [
            {
                "id": i + 100,
                "name": name,
                "run_id": 21,
                "run_attempt": 1,
                "status": "completed",
                "conclusion": "success",
                "runner_id": 1000 + i,
                "runner_name": "Hosted Agent",
                "labels": [
                    name.removeprefix("package-").rsplit("-py", 1)[0]
                    if name.startswith("package-")
                    else "ubuntu-24.04"
                ],
            }
            for i, name in enumerate(sealed["required_jobs"])
        ]

    def finish_build(self):
        self.build.update(status="completed", conclusion="success")
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("dist/package.whl", b"registered wheel bytes")
        self.raw_archive = data.getvalue()
