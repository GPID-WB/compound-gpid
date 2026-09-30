"""Complete GPID provider wire fixture; only outer GitHub/Git I/O is substituted."""

import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from profile_bridge_fixture import wire
from profile_fixture import ProfileFixture
from profile_fixture import snapshot_bytes as snapshot_bytes

from cg_release.events import ControllerError


class ProfileTransport(ProfileFixture):
    def read_wire(self, resource, query):
        parsed = urlsplit("https://unused/" + resource)
        if parsed.path.endswith("/pulls"):
            branch = parse_qs(parsed.query)["head"][0].split(":", 1)[1]
            return [p for p in self.prs if p["head"]["ref"] == branch]
        if parsed.path.endswith("/actions/runs") and "head_sha=" in parsed.query:
            sha = parse_qs(parsed.query)["head_sha"][0]
            rows = [
                r
                for r in self.get("actions/runs")["workflow_runs"]
                if r["head_sha"] == sha
            ]
            return {"total_count": len(rows), "workflow_runs": rows}
        if "/git/trees/" in parsed.path and "recursive=1" in parsed.query:
            oid = parsed.path.rsplit("/", 1)[-1]
            if oid in self.git.flat:
                return self.git.flat[oid]
        return super().read_wire(resource, query)

    def get(self, endpoint, **kwargs):
        endpoint = unquote(endpoint)
        bridge_value = wire(self, endpoint)
        if bridge_value is not None:
            return bridge_value
        if endpoint == "environments/github-pages/secrets":
            return {
                "total_count": 2,
                "secrets": [
                    {"name": n}
                    for n in [
                        "RELEASE_CONTROL_APP_ID",
                        "RELEASE_CONTROL_APP_PRIVATE_KEY",
                    ]
                ],
            }
        if endpoint == "releases/70":
            return next(r for r in self.release_rows if r["id"] == 70)
        if endpoint.startswith("check-suites/") and endpoint.split("/")[1] in {
            "91",
            "92",
        }:
            return {"app": {"id": 15368}, "head_sha": self.bridge_sha}
        if endpoint.startswith("actions/runs/"):
            run_id = int(endpoint.split("/")[2])
            if run_id in self.deleted_doc_runs:
                raise ControllerError(
                    "E_NOT_FOUND", "Synthetic run expired from retention."
                )
            if run_id in {91, 92}:
                if endpoint.endswith("jobs"):
                    return {
                        "total_count": 1,
                        "jobs": [
                            dict(
                                id=run_id,
                                name="bridge-clean-client-"
                                + ("windows" if run_id == 91 else "unix"),
                                run_id=run_id,
                                run_attempt=1,
                                conclusion="success",
                            )
                        ],
                    }
                return dict(
                    id=run_id,
                    head_sha=self.bridge_sha,
                    run_attempt=1,
                    repository={"id": 123},
                    status="completed",
                    conclusion="success",
                    path=".github/workflows/release-controller-bridge.yml",
                    check_suite_id=run_id,
                )
            if run_id in self.builds:
                self.build = self.builds[run_id]
                self.jobs = self.build_jobs[run_id]
                self.build_id = run_id
                self.raw_archive = self.archives.get(run_id, b"")
            if run_id in self.docs_runs:
                if endpoint.endswith("jobs"):
                    jobs = self.docs_jobs[run_id]
                    return {"total_count": len(jobs), "jobs": jobs}
                return self.docs_runs[run_id]
        if (
            endpoint
            == "actions/workflows/.github/workflows/release-controller-docs.yml/runs"
        ):
            return {
                "total_count": len(self.docs_runs),
                "workflow_runs": list(self.docs_runs.values()),
            }
        if endpoint == "deployments":
            return self.deployments
        if endpoint.endswith("/statuses") and endpoint.startswith("deployments/"):
            return [
                dict(
                    id=900,
                    state="success",
                    log_url=f"https://{self.host}/{self.slug}/actions/runs/{self.deployed_run}/job/1",
                )
            ]
        if endpoint.startswith("pulls/"):
            number = int(endpoint.split("/")[1])
            pr = next(p for p in self.prs if p["number"] == number)
            if endpoint.endswith("reviews"):
                return [
                    dict(
                        id=120 + number,
                        user={"id": 8},
                        state="APPROVED",
                        commit_id=pr["head"]["sha"],
                    )
                ]
            return pr
        if endpoint.endswith("/check-runs"):
            sha = endpoint.split("/")[1]
            return {
                "total_count": 1,
                "check_runs": [
                    dict(
                        id=14,
                        name="release-controller-ci",
                        head_sha=sha,
                        status="completed",
                        conclusion="success",
                        app={"id": 15368},
                        check_suite={"id": 15},
                    )
                ],
            }
        if endpoint == "actions/runs":
            return {
                "total_count": len(self.prs),
                "workflow_runs": [
                    dict(
                        id=19 + n,
                        run_attempt=1,
                        head_sha=p["head"]["sha"],
                        status="completed",
                        conclusion="success",
                        check_suite_id=15,
                        path=".github/workflows/release-controller-ci.yml",
                    )
                    for n, p in enumerate(self.prs)
                ],
            }
        return super().get(endpoint, **kwargs)

    def run(self, tool, args, **kwargs):
        endpoint = args[-1].removeprefix(f"repos/{self.slug}/")
        if kwargs.get("binary_output") and endpoint in {
            "actions/artifacts/91/zip",
            "actions/artifacts/92/zip",
        }:
            return subprocess.CompletedProcess(
                args, 0, self.bridge_archives[int(endpoint.split("/")[2])], b""
            )
        if (
            tool == "gh"
            and "POST" in args
            and endpoint.startswith("https://uploads.github.com/")
        ):
            release_id = int(urlsplit(endpoint).path.split("/")[-2])
            name = parse_qs(urlsplit(endpoint).query)["name"][0]
            assert not any(
                a["release_id"] == release_id and a["name"] == name
                for a in self.asset_rows.values()
            )
            raw = Path(args[args.index("--input") + 1]).read_bytes()
            asset_id = max(self.asset_rows) + 1
            self.asset_rows[asset_id] = dict(
                id=asset_id,
                name=name,
                bytes=raw,
                size=len(raw),
                release_id=release_id,
                state="uploaded",
                content_type=args[args.index("--header") + 1].removeprefix(
                    "Content-Type: "
                ),
            )
            self.publication_writes.append("asset-" + name)
            return subprocess.CompletedProcess(
                args, 0, "HTTP/2.0 201 Created\n\n{}", ""
            )
        if kwargs.get("binary_output"):
            self.downloads.append(endpoint)
        if tool == "gh" and "POST" in args and endpoint == "git/trees":
            payload = json.loads(kwargs["input_text"])
            rows = self.git.flat[payload["base_tree"]]["tree"]
            files = {row["path"]: self.objects[row["sha"]] for row in rows}
            files.update(
                {row["path"]: self.objects[row["sha"]] for row in payload["tree"]}
            )
            self.git.tree(files)
            self.objects.update(self.git.blobs)
            self.trees.update(self.git.trees)
            self.prep_writes.append(endpoint)
            return subprocess.CompletedProcess(
                args, 0, "HTTP/2.0 201 Created\n\n{}", ""
            )
        result = super().run(tool, args, **kwargs)
        if tool == "gh" and "POST" in args and endpoint == "pulls":
            self.prs[-1].update(number=41 + len(self.prs), id=98 + len(self.prs))
        return result

    def merge(self):
        pr = self.prs[-1]
        head = pr["head"]["sha"]
        pr.update(
            state="closed",
            merged=True,
            merged_at="2026-09-12T00:00:00Z",
            merge_commit_sha=head,
        )
        self.branches[pr["base"]["ref"]] = head

    def begin_build(self, sealed, run_id=21):
        super().begin_build(sealed)
        self.build["id"] = run_id
        for job in self.jobs:
            job["run_id"] = run_id
        self.builds[run_id], self.build_jobs[run_id] = self.build, self.jobs
        self.build_id = run_id
        self.sealed = sealed

    def finish_build(self, tag="v1.1.0"):
        self.build.update(status="completed", conclusion="success")
        self.snapshot = snapshot_bytes(tag, self.sealed["release_sha"], self.build_id)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("release-output/release-docs.json", self.snapshot)
            lock = self.files["packages/cg-release/uv.lock"]
            import tomllib

            versions = {
                p["name"]: p["version"] for p in tomllib.loads(lock.decode())["package"]
            }
            archive.writestr(
                "release-output/native-environment.json",
                json.dumps(
                    dict(
                        schema_version=1,
                        source_sha=self.sealed["release_sha"],
                        run_id=self.build_id,
                        run_attempt=1,
                        gate_owner="gpid-native-profile",
                        python="3.12.0",
                        platform="linux",
                        lock_sha256=hashlib.sha256(lock).hexdigest(),
                        packages={
                            k: v
                            for k, v in versions.items()
                            if k not in {"cg-release", "colorama", "win32-setctime"}
                        },
                    )
                ),
            )
        self.raw_archive = self.archives[self.build_id] = stream.getvalue()

    def begin_docs(self, item, run_id=55):
        sealed = item.ticket
        self.docs_runs[run_id] = dict(
            id=run_id,
            run_attempt=1,
            event="workflow_dispatch",
            path=sealed["workflow_path"],
            display_title="release-docs " + sealed["nonce"],
            head_sha=sealed["controller_sha"],
            head_branch="main",
            repository={"id": 123},
            actor={"id": 77},
            status="in_progress",
            conclusion=None,
        )
        self.docs_jobs[run_id] = [
            dict(
                id=run_id * 10 + n,
                name=name,
                run_id=run_id,
                run_attempt=1,
                status="completed",
                conclusion="success",
            )
            for n, name in enumerate(["register", "dev-preview", "compose", "deploy"])
        ]

    def deploy_docs(self, run_id=55):
        self.docs_runs[run_id].update(status="completed", conclusion="success")
        self.deployed_run = run_id
        self.deployments[:] = [
            dict(id=900, sha=self.branches["main"], environment="github-pages")
        ]
