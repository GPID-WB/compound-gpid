"""Offline GitHub protocol with irreversible writes, read faults and cancellation."""

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from phase4_transport import Phase4Transport

from cg_release.events import ControllerError


class Phase5Transport(Phase4Transport):
    def __init__(self, cwd):
        super().__init__(cwd)
        self.tags, self.tag_text, self.release_rows, self.asset_rows = {}, {}, [], {}
        self.publication_runs, self.publication_jobs = {}, {}
        self.latest = None
        self.publication_writes = []
        self.fault = None
        self.read_faults = {}
        self.wall_time = 1789171200
        self.expired = False
        self.build_id = 21
        self.artifact_id = 51
        self.approval_environment = self.policy.environments.override
        self.write_roles = []
        self.checkpoint_fault = None

    def begin_publication(self, run_id=41):
        self.publication_runs[run_id] = {
            "id": run_id,
            "run_attempt": 1,
            "display_title": "release-publication "
            + self.dispatches[-1]["inputs"]["nonce"],
            "event": "workflow_dispatch",
            "path": ".github/workflows/release-controller-publish.yml",
            "head_sha": self.branches["main"],
            "head_branch": "main",
            "repository": {"id": 123},
            "actor": {"id": 77},
            "status": "in_progress",
            "created_at": datetime.fromtimestamp(self.wall_time, UTC).isoformat(),
        }
        self.publication_jobs[run_id] = [
            {
                "id": run_id * 10 + 1,
                "name": "seal",
                "run_id": run_id,
                "run_attempt": 1,
                "status": "completed",
                "conclusion": "success",
            },
            {
                "id": run_id * 10 + 2,
                "name": "publish",
                "run_id": run_id,
                "run_attempt": 1,
                "status": "in_progress",
                "conclusion": None,
            },
        ]

    def get(self, endpoint, **kwargs):
        endpoint = unquote(endpoint)
        if endpoint == "actions/workflows/release-controller-publish.yml/runs":
            return {
                "total_count": len(self.publication_runs),
                "workflow_runs": list(self.publication_runs.values()),
            }
        fault = self.read_faults.get(endpoint)
        if fault:
            self.read_faults[endpoint] -= 1
            raise ControllerError("E_FORBIDDEN", "Injected unreadable observation")
        if endpoint == "releases":
            page = int(kwargs.get("page") or 1)
            return self.release_rows[(page - 1) * 100 : page * 100]
        if endpoint.startswith("compare/"):
            base, head = endpoint.removeprefix("compare/").split("...")
            return {
                "status": "identical" if base == head else "ahead",
                "total_commits": 0,
                "base_commit": {"sha": base},
                "merge_base_commit": {"sha": base},
                "commits": [],
            }
        if endpoint == "releases/latest":
            if self.latest is None:
                raise ControllerError("E_NOT_FOUND", "No latest release")
            return next(r for r in self.release_rows if r["id"] == self.latest)
        if endpoint.startswith("releases/") and endpoint.endswith("/assets"):
            return [
                {k: v for k, v in a.items() if k != "bytes"}
                for a in self.asset_rows.values()
                if a["release_id"] == int(endpoint.split("/")[1])
            ]
        if endpoint.startswith("git/ref/tags/"):
            tag = endpoint.removeprefix("git/ref/tags/")
            if tag not in self.tags:
                raise ControllerError("E_NOT_FOUND", "No tag")
            return {
                "ref": "refs/tags/" + tag,
                "object": {"type": "tag", "sha": self.tags[tag]["oid"]},
            }
        if endpoint.startswith("git/tags/"):
            oid = endpoint.removeprefix("git/tags/")
            tag, value = next((k, v) for k, v in self.tags.items() if v["oid"] == oid)
            return {
                "sha": oid,
                "tag": tag,
                "object": {"type": "commit", "sha": value["commit"]},
            }
        if endpoint.startswith("environments/") and endpoint.count("/") == 1:
            return {
                **super().get(endpoint, **kwargs),
                "id": 18
                if endpoint.endswith(self.policy.environments.override)
                else 17,
                "name": endpoint.split("/")[1],
                "protection_rules": [
                    {
                        "type": "required_reviewers",
                        "prevent_self_review": True,
                        "reviewers": [{"type": "User", "reviewer": {"id": 999}}],
                    }
                ],
            }
        if endpoint.startswith("actions/runs/"):
            run_id = int(endpoint.split("/")[2])
            if run_id in self.publication_runs:
                if endpoint.endswith("/approvals"):
                    return [
                        {
                            "state": "approved",
                            "user": {"id": 999},
                            "environments": [
                                {
                                    "id": 18
                                    if self.approval_environment
                                    == self.policy.environments.override
                                    else 17,
                                    "name": self.approval_environment,
                                }
                            ],
                        }
                    ]
                if endpoint.endswith("/jobs"):
                    return {"total_count": 2, "jobs": self.publication_jobs[run_id]}
                return self.publication_runs[run_id]
            if run_id == self.build_id:
                translated = endpoint.replace(
                    f"actions/runs/{self.build_id}", "actions/runs/21", 1
                )
                value = super().get(translated, **kwargs)
                if endpoint.endswith("/artifacts"):
                    value["artifacts"][0].update(
                        id=self.artifact_id,
                        expired=self.expired,
                        workflow_run={
                            "id": self.build_id,
                            "head_sha": self.build["head_sha"],
                        },
                    )
                return value
        return super().get(endpoint, **kwargs)

    def _effect(self, name, action):
        self.publication_writes.append(name)
        self.write_roles.append(self.current_token)
        if self.fault == (name, "before"):
            self.fault = None
            raise KeyboardInterrupt("Cancelled before remote write")
        action()
        if self.fault == (name, "uncertain"):
            self.fault = None
            endpoint = (
                "git/ref/tags/" + next(iter(self.tags))
                if name == "tag"
                else "releases/71/assets"
                if name.startswith("asset-")
                else "releases"
            )
            self.read_faults[endpoint] = 1
            raise ControllerError(
                "E_TIMEOUT",
                "Remote effect accepted; response and read-back unavailable",
            )
        if self.fault == (name, "after"):
            self.fault = None
            raise KeyboardInterrupt("Cancelled after remote acceptance")

    def run(self, tool, args, **kwargs):
        self.current_token = kwargs.get("environment", {}).get("GH_TOKEN")
        if (
            tool == "gh"
            and args[-1] == "graphql"
            and "POST" in args
            and self.checkpoint_fault
        ):
            payload = json.loads(kwargs["input_text"])["variables"]["input"]
            import base64

            event = next(
                json.loads(base64.b64decode(f["contents"]))
                for f in payload["fileChanges"]["additions"]
                if f["path"].startswith("events/")
            )
            kind = (
                "atomic"
                if event["audit"].get("publication_atomic")
                else "intent"
                if event["record"].get("intent")
                else "result"
            )
            slot = event["audit"]["operation"] + ":" + kind
            if slot == self.checkpoint_fault[0]:
                _, boundary = self.checkpoint_fault
                self.checkpoint_fault = None
                if boundary == "before":
                    raise KeyboardInterrupt("before journal checkpoint")
                super().run(tool, args, **kwargs)
                raise KeyboardInterrupt("after journal checkpoint")
        if tool == "git" and "hash-object" in args:
            raw = kwargs["input_text"].encode()
            oid = hashlib.sha1(
                b"tag " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest()
            self.tag_text[oid] = raw
            return subprocess.CompletedProcess(args, 0, oid + "\n", "")
        if tool == "git" and "push" in args:
            oid, tag = args[-1].split(":refs/tags/")
            assert not any(a.startswith(("--force", "+")) for a in args)
            assert tag not in self.tags

            def push():
                self.tags[tag] = {
                    "oid": oid,
                    "commit": self.tag_text[oid].decode().splitlines()[0].split()[1],
                }
                self.tag_nodes.append(
                    {"name": tag, "target": {"oid": oid, "__typename": "Tag"}}
                )

            self._effect("tag", push)
            return subprocess.CompletedProcess(args, 0, "", "")
        if tool == "git" and ("init" in args or "fetch" in args):
            return subprocess.CompletedProcess(args, 0, "", "")
        if kwargs.get("binary_output"):
            if "/releases/assets/" in args[-1]:
                raw = self.asset_rows[int(args[-1].rsplit("/", 1)[1])]["bytes"]
                return subprocess.CompletedProcess(args, 0, raw, b"")
            if "/actions/artifacts/" in args[-1]:
                return subprocess.CompletedProcess(args, 0, self.raw_archive, b"")
        if tool == "gh" and "--method" in args:
            method = args[args.index("--method") + 1]
            endpoint = args[-1].removeprefix(f"repos/{self.slug}/")
            if method == "POST" and endpoint == "releases":
                payload = json.loads(kwargs["input_text"])
                self._effect(
                    "draft",
                    lambda: self.release_rows.append(
                        {**payload, "id": 71, "published_at": None}
                    ),
                )
                return subprocess.CompletedProcess(
                    args, 0, "HTTP/2.0 201 Created\n\n{}", ""
                )
            if method == "POST" and endpoint.startswith("https://uploads.github.com/"):
                name = parse_qs(urlsplit(endpoint).query)["name"][0]
                raw = Path(args[args.index("--input") + 1]).read_bytes()
                media = args[args.index("--header") + 1].removeprefix("Content-Type: ")
                assert not any(a["name"] == name for a in self.asset_rows.values())
                ident = 81 + len(self.asset_rows)
                self._effect(
                    "asset-" + name,
                    lambda: self.asset_rows.update(
                        {
                            ident: {
                                "id": ident,
                                "release_id": 71,
                                "name": name,
                                "size": len(raw),
                                "content_type": media,
                                "state": "uploaded",
                                "bytes": raw,
                            }
                        }
                    ),
                )
                return subprocess.CompletedProcess(
                    args, 0, "HTTP/2.0 201 Created\n\n{}", ""
                )
            if method == "PATCH" and endpoint == "releases/71":
                payload = json.loads(kwargs["input_text"])

                def published():
                    next(r for r in self.release_rows if r["id"] == 71).update(
                        draft=False, published_at="2026-09-12T00:00:00Z"
                    )
                    if payload["make_latest"] == "true":
                        self.latest = 71

                self._effect("publish", published)
                return subprocess.CompletedProcess(args, 0, "HTTP/2.0 200 OK\n\n{}", "")
        return super().run(tool, args, **kwargs)
