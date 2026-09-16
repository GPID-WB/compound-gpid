"""Offline GitHub wire server for real client/worker/context integration tests."""

import base64
import json
import subprocess
from urllib.parse import parse_qs, unquote, urlsplit

from test_remote_faults import Server

from cg_release.events import ControllerError
from cg_release.git_journal import blob_id
from cg_release.models import Policy, canonical_bytes, load_record


class WorkerTransport(Server):
    def __init__(self, cwd):
        super().__init__(cwd)
        raw = self.policy.model_dump(mode="json")
        raw["enabled"] = True
        raw["release_lines"][0]["branches"] = ["main", "feature"]
        self.policy = load_record(Policy, canonical_bytes(raw))
        self.actor = 7
        self.trigger_actor = 456
        self.roles = {7: "maintain", 8: "maintain", 456: "maintain"}
        self.event = "workflow_dispatch"
        self.now = 0.0
        self.slow_users = set()
        self.fail_checkpoint = False
        self.expire_after_acceptance = False
        self.resumer_revoke_after = None
        self.resumer_checks = 0
        self.calls, self.issues, self.dispatches, self.tag_nodes = [], [], [], []
        self.branches = {"main": "a" * 40, "feature": "b" * 40}
        self.install_source("a" * 40)
        self.install_source("b" * 40)

    def clock(self):
        return self.now

    def install_source(self, sha):
        contents = {
            ".release-controller.json": canonical_bytes(self.policy),
            "package.json": b'{"name":"generic","version":"0.9.0"}\n',
            "CHANGELOG.md": b"# Changes\n\n<!-- release -->\n",
        }
        files = {}
        for path, raw in contents.items():
            oid = blob_id(raw)
            self.objects[oid] = raw
            files[path] = oid
        self._commit(sha, None, files)

    def environment(self):
        return {
            "GITHUB_ACTIONS": "true",
            "GITHUB_RUN_ID": "10",
            "GITHUB_ACTOR_ID": str(self.trigger_actor),
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": self.branches["main"],
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_REPOSITORY_ID": "123",
            "GITHUB_REPOSITORY": self.slug,
            "GITHUB_WORKFLOW_REF": f"{self.slug}/.github/workflows/"
            "release-controller.yml@refs/heads/main",
            "CG_RELEASE_CONTROLLER_REVISION": self.policy.controller.revision,
            "CG_RELEASE_WHEEL_SHA256": self.policy.controller.wheel_digest,
        }

    def branch(self, name):
        if name == self.policy.state_branch:
            return super().branch(name)
        if name not in self.branches:
            raise ControllerError("E_NOT_FOUND", "Branch absent.")
        return {
            "name": name,
            "protected": name == "main",
            "commit": {"sha": self.branches[name]},
        }

    def get(self, endpoint, **kwargs):
        if endpoint == "rulesets":
            return self.rules
        if endpoint.startswith("branches/") and not endpoint.endswith("/protection"):
            return self.branch(unquote(endpoint[9:]))
        if endpoint.startswith("git/commits/"):
            commit = self.commits[endpoint[12:]]
            return {"sha": commit["sha"], "tree": commit["commit"]["tree"]}
        if endpoint.startswith("git/trees/"):
            return self.trees[endpoint[10:]]
        if endpoint.startswith("collaborators/"):
            actor = int(unquote(endpoint.split("/")[1]).removeprefix("user"))
            role = self.roles[actor]
            if actor == self.trigger_actor:
                self.resumer_checks += 1
                if self.resumer_checks == self.resumer_revoke_after:
                    self.roles[actor] = "write"
            return {
                "role_name": role,
                "permission": {"maintain": "write"}.get(role, role),
                "user": {"id": actor},
            }
        if endpoint == "actions/runs/10":
            return {
                "id": 10,
                "run_attempt": 1,
                "head_sha": self.branches["main"],
                "head_branch": "main",
                "path": ".github/workflows/release-controller.yml",
                "event": self.event,
                "repository": {"id": 123},
                "actor": {"id": self.trigger_actor},
                "status": "in_progress",
            }
        if endpoint == "releases":
            return []
        return super().get(endpoint, **kwargs)

    def read_wire(self, resource, query):
        if resource == "user" or resource.startswith("user/"):
            actor = self.actor if resource == "user" else int(resource[5:])
            return {"id": actor, "login": f"user{actor}"}
        if resource == "graphql":
            if "issues(" in query:
                connection = {
                    "nodes": list(self.issues),
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
                return {
                    "data": {"repository": {"databaseId": 123, "issues": connection}}
                }
            if "refs(" in query:
                return {
                    "data": {
                        "repository": {
                            "databaseId": 123,
                            "refs": {
                                "nodes": self.tag_nodes,
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                            },
                        }
                    }
                }
            raise AssertionError(query)
        if resource.startswith("apps/") or resource.startswith("users/"):
            return super()._request(resource, None)
        parsed = urlsplit("https://unused/" + resource)
        endpoint = parsed.path.removeprefix("/repos/" + self.slug).lstrip("/")
        parameters = parse_qs(parsed.query)
        if endpoint == "commits":
            sha = parameters["sha"][0]
            return [{"sha": sha, "commit": {"message": "Initial generic source"}}]
        return self.get(
            endpoint,
            **({"page": int(parameters["page"][0])} if "page" in parameters else {}),
        )

    def run(self, tool, argv, **kwargs):
        self.calls.append((tool, list(argv)))
        if tool == "git":
            assert argv == ["remote", "get-url", "origin"]
            return subprocess.CompletedProcess(
                argv, 0, f"https://github.com/{self.slug}.git\n", ""
            )
        assert tool == "gh"
        method, resource = argv[argv.index("--method") + 1], argv[-1]
        if method == "GET":
            if any(
                resource == f"user/{actor}"
                or resource.endswith(f"/collaborators/user{actor}/permission")
                for actor in self.slow_users
            ):
                self.now += kwargs["timeout"]
            else:
                self.now += 0.01
            query = (
                argv[argv.index("--raw-field") + 1][6:]
                if "--raw-field" in argv
                else None
            )
            value = self.read_wire(resource, query)
            return subprocess.CompletedProcess(
                argv, 0, "HTTP/2.0 200 OK\n\n" + json.dumps(value), ""
            )
        payload = json.loads(kwargs["input_text"])
        if resource.endswith("/issues"):
            number = len(self.issues) + 1
            self.issues.append(
                {
                    "id": f"I_{number}",
                    "number": number,
                    "body": payload["body"],
                    "url": f"https://github.com/{self.slug}/issues/{number}",
                    "author": {"__typename": "User", "databaseId": self.actor},
                    "createdAt": "2026-09-11T00:00:00Z",
                    "lastEditedAt": None,
                    "userContentEdits": {"totalCount": 0},
                }
            )
            return subprocess.CompletedProcess(
                argv, 0, "HTTP/2.0 201 Created\n\n{}", ""
            )
        if resource.endswith("/dispatches"):
            self.dispatches.append(payload)
            return subprocess.CompletedProcess(
                argv, 0, "HTTP/2.0 204 No Content\n\n", ""
            )
        assert resource == "graphql"
        additions = payload["variables"]["input"]["fileChanges"]["additions"]
        event = next(
            json.loads(base64.b64decode(item["contents"]))
            for item in additions
            if item["path"].startswith("events/")
        )
        is_queue = event["record"].get("kind") == "queue"
        if is_queue and self.fail_checkpoint:
            raise ControllerError("E_TIMEOUT", "Injected checkpoint transport failure.")
        result = super().runner(tool, argv, **kwargs)
        if not is_queue and self.expire_after_acceptance:
            self.now += kwargs["timeout"]
        return result
