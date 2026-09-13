"""The dispatch-only generic build must not be invented as a preparation PR check."""

import re

from phase4_transport import Phase4Transport
from test_worker_e2e import start, worker

from cg_release import build_worker, source
from cg_release.context import context_for
from cg_release.github import GitHubReads
from cg_release.models import RequiredCheck


class GenericTransport(Phase4Transport):
    def __init__(self, cwd):
        super().__init__(cwd)
        self.runs, self.run_jobs, self.archives = {}, {}, {}
        self.policy = self.policy.model_copy(
            update={
                "required_checks": [
                    *self.policy.required_checks,
                    RequiredCheck(
                        name="build",
                        app_id=15368,
                        stage="release",
                        workflow_path=".github/workflows/release-controller-build.yml",
                    ),
                ]
            }
        )
        self.install_source("a" * 40)
        self.install_source("b" * 40)

    def get(self, endpoint, **kwargs):
        match = re.fullmatch(
            r"actions/runs/(2[1-9])(?:/(attempts/1(?:/jobs)?|artifacts))?", endpoint
        )
        if match:
            rid, suffix = int(match[1]), match[2]
            if suffix == "attempts/1/jobs":
                return {
                    "total_count": len(self.run_jobs[rid]),
                    "jobs": self.run_jobs[rid],
                }
            if suffix == "artifacts":
                self.build = self.runs[rid]
                self.raw_archive = self.archives[rid]
                result = super().get("actions/runs/21/artifacts")
                result["artifacts"][0]["id"] = rid + 30
                result["artifacts"][0]["workflow_run"]["id"] = rid
                return result
            return self.runs[rid]
        match = re.fullmatch(r"check-suites/(3[1-9])", endpoint)
        if match:
            return {"id": int(match[1]), "head_sha": "a" * 40, "app": {"id": 15368}}
        # PR inventory stays the original CI-only inventory. There is no generic PR run.
        return super().get(endpoint, **kwargs)

    def run(self, tool, argv, **kwargs):
        if kwargs.get("binary_output"):
            import subprocess

            aid = int(argv[-1].split("/")[-2])
            return subprocess.CompletedProcess(argv, 0, self.archives[aid - 30], b"")
        return super().run(tool, argv, **kwargs)

    def begin_registered(self, sealed, rid):
        super().begin_build(sealed)
        self.build.update(id=rid, check_suite_id=rid + 10)
        for job in self.jobs:
            job.update(run_id=rid, id=job["id"] + rid * 100)
        self.runs[rid], self.run_jobs[rid] = self.build, self.jobs

    def finish_registered(self, sealed, rid):
        self.build = self.runs[rid]
        if sealed["produces_artifacts"]:
            super().finish_build()
            self.archives[rid] = self.raw_archive
        else:
            self.build.update(status="completed", conclusion="success")


def test_generic_and_ci_workflows_start_before_binding_and_finish_real_pipeline(
    monkeypatch, tmp_path, capsys
):
    world = GenericTransport(tmp_path)
    monkeypatch.setattr(source, "run_process", world.run)
    monkeypatch.setitem(GitHubReads.__init__.__kwdefaults__, "runner", world.run)
    locator = start(world, capsys)
    assert worker(world, monkeypatch, capsys, locator)[1]["observed"] == "queued"
    assert (
        worker(world, monkeypatch, capsys, locator)[1]["observed"] == "awaiting-review"
    )
    world.merge()
    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["observed"] == "building", event

    for number, rid in [(1, 21), (2, 22)]:
        code, event = worker(world, monkeypatch, capsys, locator)
        assert code == 0 and event["step"] == f"build-dispatch-{number}", event
        context = context_for(
            locator, cwd=tmp_path, deadline=world.clock() + 120, clock=world.clock
        )
        sealed = context.journal.get(locator).evidence[f"build-request-{number}"]
        world.begin_registered(sealed, rid)
        env = world.environment()
        env.update(
            GITHUB_RUN_ID=str(rid),
            GITHUB_ACTOR_ID="77",
            GITHUB_WORKFLOW_REF=f"{world.slug}/{sealed['workflow_path']}@refs/heads/main",
            GITHUB_OUTPUT=str(tmp_path / f"output-{rid}"),
        )
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        assert (
            build_worker.main(
                [
                    "register",
                    "--request-id",
                    locator,
                    "--nonce",
                    sealed["dispatch_nonce"],
                ]
            )
            == 0
        )
        world.finish_registered(sealed, rid)

    code, event = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and event["observed"] == "awaiting-approval", event
    context = context_for(
        locator, cwd=tmp_path, deadline=world.clock() + 120, clock=world.clock
    )
    record = context.journal.get(locator)
    assert [c["name"] for c in record.evidence["review-binding"]["checks"]] == [
        "release-controller-ci"
    ]
    assert set(record.evidence["build-validated-2"]["gates"]) == {
        c.workflow_path for c in world.policy.required_checks
    }
    assert set(world.archives) == {21} and len(world.dispatches) == 2
