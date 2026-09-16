"""GET-only bridge transport backed by real private Git objects, never a live server."""

import base64
import hashlib
import io
import json
import subprocess
import zipfile
from urllib.parse import unquote, urlsplit

from cg_release.profile_bridge import STEPS, WORKFLOW
from cg_release.profile_models import Bridge


class BridgeRemote:
    def __init__(self, root, spec):
        self.root, self.spec = root, spec
        self.identities = [spec.previous, spec.bridge, spec.successor]
        self.artifacts, self.metadata = {}, {}
        self.bad = None

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True, timeout=30
        ).stdout

    def policy(self, receipt):
        """The opposite host is synthetic transport data, not an executed host claim."""
        fields = {
            **self.spec.bridge.model_dump(),
            "previous": self.spec.previous,
            "successor": self.spec.successor,
            "workflow_path": WORKFLOW,
            "app_id": 15368,
        }
        for platform, identity in (("windows", 91), ("unix", 92)):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as archive:
                archive.writestr(
                    "qualification.json",
                    json.dumps({**receipt, "platform": platform, "run_id": identity}),
                )
            raw = stream.getvalue()
            self.artifacts[identity] = raw
            sha = hashlib.sha256(raw).hexdigest()
            self.metadata[identity] = dict(
                id=identity,
                name="bridge-clean-client-" + platform,
                expired=False,
                size_in_bytes=len(raw),
                digest="sha256:" + sha,
                workflow_run={"id": identity, "head_sha": self.spec.bridge.revision},
            )
            fields.update(
                {
                    platform + "_run_id": identity,
                    platform + "_job_id": identity,
                    platform + "_artifact_id": identity,
                    platform + "_artifact_digest": sha,
                }
            )
        return Bridge(**fields)

    def run(self, tool, args, **kwargs):
        assert tool == "gh" and args[:3] == ["api", "--method", "GET"], (
            "No remote writes in this fixture"
        )
        resource = urlsplit("https://unused/" + args[-1])
        endpoint = unquote(
            resource.path.lstrip("/").removeprefix("repos/" + self.spec.repository_slug)
        ).lstrip("/")
        if kwargs.get("binary_output"):
            value = self.artifacts[int(endpoint.split("/")[2])]
            if self.bad == "archive-bytes":
                value = value[:-1] + bytes([value[-1] ^ 1])
            return subprocess.CompletedProcess(args, 0, value, b"")
        value = self.get(endpoint, resource.query)
        return subprocess.CompletedProcess(
            args, 0, "HTTP/2.0 200 OK\n\n" + json.dumps(value), ""
        )

    def get(self, endpoint, query):
        if endpoint == "user/7":
            return {"id": 7, "login": "maintainer"}
        if endpoint == "collaborators/maintainer/permission":
            return {"role_name": "maintain", "permission": "write", "user": {"id": 7}}
        if endpoint == "":
            return {
                "id": self.spec.repository_id,
                "full_name": self.spec.repository_slug,
            }
        if endpoint == "graphql":
            return {
                "data": {
                    "repository": {
                        "databaseId": self.spec.repository_id,
                        "refs": {
                            "nodes": [
                                {
                                    "name": r.tag,
                                    "target": {
                                        "oid": r.tag_object,
                                        "__typename": "Tag",
                                    },
                                }
                                for r in self.identities
                            ],
                            "pageInfo": {"hasNextPage": False},
                        },
                    }
                }
            }
        if endpoint.startswith("releases/"):
            item = next(r for r in self.identities if r.release_id == int(endpoint[9:]))
            return dict(
                id=item.release_id,
                tag_name=item.tag,
                draft=self.bad == "draft",
                published_at="2026-09-12T00:00:00Z",
            )
        if endpoint.startswith("git/ref/tags/"):
            item = next(r for r in self.identities if r.tag == endpoint[13:])
            return dict(
                ref="refs/tags/" + item.tag,
                object={"type": "tag", "sha": item.tag_object},
            )
        if endpoint.startswith("git/tags/"):
            item = next(r for r in self.identities if r.tag_object == endpoint[9:])
            return dict(
                sha=item.tag_object,
                tag=item.tag,
                object={"type": "commit", "sha": item.revision},
            )
        if endpoint.startswith("git/commits/"):
            item = next(r for r in self.identities if r.revision == endpoint[12:])
            return dict(sha=item.revision, tree={"sha": item.tree})
        if endpoint.startswith("git/trees/"):
            oid = endpoint[10:]
            rows = self.git(
                "ls-tree", "-z", *(["-r"] if "recursive=1" in query else []), oid
            )
            entries = []
            for line in rows.split(b"\0"):
                if line:
                    header, name = line.decode().split("\t", 1)
                    mode, kind, sha = header.split()
                    entries.append(dict(path=name, mode=mode, type=kind, sha=sha))
            return dict(sha=oid, truncated=False, tree=entries)
        if endpoint.startswith("git/blobs/"):
            oid = endpoint[10:]
            raw = self.git("cat-file", "blob", oid)
            return dict(
                sha=oid,
                encoding="base64",
                size=len(raw),
                content=base64.b64encode(raw).decode(),
            )
        if endpoint.startswith("check-suites/"):
            return {"app": {"id": 15368}, "head_sha": self.spec.bridge.revision}
        if endpoint.startswith("actions/runs/"):
            identity = int(endpoint.split("/")[2])
            if endpoint.endswith("artifacts"):
                meta = dict(self.metadata[identity])
                if self.bad == "artifact-run":
                    meta["workflow_run"] = {
                        "id": 999,
                        "head_sha": self.spec.bridge.revision,
                    }
                if self.bad == "expired":
                    meta["expired"] = True
                return {"total_count": 1, "artifacts": [meta]}
            if endpoint.endswith("jobs"):
                steps = [
                    dict(name=n, status="completed", conclusion="success")
                    for n in STEPS
                ]
                if self.bad == "arbitrary-fixture":
                    steps = [
                        dict(
                            name="Run old reader fixture",
                            status="completed",
                            conclusion="success",
                        )
                    ]
                job = dict(
                    id=identity,
                    name="bridge-clean-client-"
                    + ("windows" if identity == 91 else "unix"),
                    run_id=identity,
                    run_attempt=1,
                    status="completed",
                    conclusion="success",
                    steps=steps,
                )
                if self.bad == "job-id":
                    job["id"] = 999
                return {"total_count": 1, "jobs": [job]}
            result = dict(
                id=identity,
                path=WORKFLOW,
                head_sha=self.spec.bridge.revision,
                run_attempt=1,
                repository={"id": self.spec.repository_id},
                event="workflow_dispatch",
                status="completed",
                conclusion="success",
                check_suite_id=identity,
            )
            if self.bad == "rerun":
                result["run_attempt"] = 2
            return result
        raise AssertionError(endpoint)
