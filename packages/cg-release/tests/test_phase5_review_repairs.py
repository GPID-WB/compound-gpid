"""Regression proofs for all five findings in Phase 5 review cycle one."""

import io
import json
import subprocess
import zipfile
from unittest.mock import patch

import pytest
from phase5_transport import Phase5Transport
from test_phase5_transport import prepare, publisher
from test_worker_e2e import worker

from cg_release import process
from cg_release.preparation import TreeEntry, object_id, tree_id


class BoundedTransport(Phase5Transport):
    notes_size = 0
    artifact_count = 1

    def __init__(self, cwd):
        super().__init__(cwd)
        self.downloads = 0
        self.inputs_seen = []

    def install_source(self, sha):
        artifacts = [self.policy.build.artifacts[0]]
        artifacts += [
            artifacts[0].model_copy(
                update={"name": f"extra-{n}.whl", "path": f"dist/extra-{n}.whl"}
            )
            for n in range(self.artifact_count - 1)
        ]
        self.policy = self.policy.model_copy(
            update={
                "build": self.policy.build.model_copy(update={"artifacts": artifacts})
            }
        )
        super().install_source(sha)
        root = self.commits[sha]["commit"]["tree"]["sha"]
        rows = [dict(row) for row in self.trees[root]["tree"]]
        entry = next(row for row in rows if row["path"] == "CHANGELOG.md")
        raw = self.objects[entry["sha"]] + b"\n" + b"A" * self.notes_size + b"\n"
        entry["sha"] = object_id("blob", raw)
        self.objects[entry["sha"]] = raw
        root = tree_id([TreeEntry(r["path"], r["mode"], r["sha"]) for r in rows])
        self.trees[root] = {"sha": root, "tree": rows, "truncated": False}
        self.commits[sha]["commit"]["tree"]["sha"] = root

    def finish_build(self):
        super().finish_build()
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w") as archive:
            for asset in self.policy.build.artifacts:
                archive.writestr(asset.path, b"verified wheel bytes")
        self.raw_archive = raw.getvalue()

    def run(self, tool, args, **kwargs):
        if kwargs.get("input_text") is not None:
            self.inputs_seen.append(len(kwargs["input_text"].encode()))
            # Exercise the real production validator, but never start a subprocess.
            with patch.object(
                process,
                "_capture",
                return_value=subprocess.CompletedProcess(args, 0, "", ""),
            ):
                process.run_process(tool, args, **kwargs)
        if kwargs.get("binary_output") and "/actions/artifacts/" in args[-1]:
            self.downloads += 1
        return super().run(tool, args, **kwargs)


@pytest.mark.parametrize("notes,count,recoveries", [(6000, 4, 2), (15000, 4, 0)])
def test_P1_1_real_envelope_supports_notes_inventory_and_recovery(
    monkeypatch, tmp_path, capsys, notes, count, recoveries
):
    class World(BoundedTransport):
        notes_size = notes
        artifact_count = count

    world = World(tmp_path)
    locator, nonce = prepare(world, monkeypatch, capsys, tmp_path)
    for attempt in range(recoveries + 1):
        run_id = 41 + attempt
        world.begin_publication(run_id)
        assert (
            publisher(
                world,
                monkeypatch,
                capsys,
                tmp_path,
                locator,
                nonce,
                "seal",
                run_id=run_id,
            )[0]
            == 0
        )
        if attempt < recoveries:
            world.fault = ("asset-package.whl", "before")
            with pytest.raises(KeyboardInterrupt):
                publisher(
                    world,
                    monkeypatch,
                    capsys,
                    tmp_path,
                    locator,
                    nonce,
                    "publish",
                    run_id=run_id,
                )
            world.publication_runs[run_id]["status"] = "completed"
            world.wall_time += 7200
            code, result = worker(world, monkeypatch, capsys, locator)
            assert code == 0, json.dumps(result)
            nonce = world.dispatches[-1]["inputs"]["nonce"]
        else:
            code, result = publisher(
                world,
                monkeypatch,
                capsys,
                tmp_path,
                locator,
                nonce,
                "publish",
                run_id=run_id,
            )
            assert code == 0 and result["observed"] == "complete", json.dumps(result)
    assert max(world.inputs_seen) > 65536
    assert world.publication_writes.count("tag") == 1


def test_P2_1_protected_job_downloads_one_verified_archive(
    monkeypatch, tmp_path, capsys
):
    world = BoundedTransport(tmp_path)
    locator, nonce = prepare(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    assert (
        publisher(world, monkeypatch, capsys, tmp_path, locator, nonce, "seal")[0] == 0
    )
    before = world.downloads
    code, result = publisher(
        world, monkeypatch, capsys, tmp_path, locator, nonce, "publish"
    )
    assert code == 0, json.dumps(result)
    assert world.downloads - before == 1


@pytest.mark.parametrize("effect", [None, "tag", "draft"])
def test_P2_2_errors_keep_verified_identity_checkpoint_and_next_action(
    monkeypatch, tmp_path, capsys, effect
):
    world = BoundedTransport(tmp_path)
    locator, nonce = prepare(world, monkeypatch, capsys, tmp_path)
    world.begin_publication()
    assert (
        publisher(world, monkeypatch, capsys, tmp_path, locator, nonce, "seal")[0] == 0
    )
    if effect is None:
        world.read_faults["actions/runs/21"] = 1
    else:
        world.fault = (effect, "uncertain")
    code, error = publisher(
        world, monkeypatch, capsys, tmp_path, locator, nonce, "publish"
    )
    assert code == 2 and error["code"] == "E_FORBIDDEN", json.dumps(error)
    assert error["request_id"] == locator and error["version"] == "1.0.0"
    assert error["step"] and error["expected"] and error["observed"]
    if effect is not None:
        assert error["step"] == "publication-" + effect
    assert error["elapsed_seconds"] >= 0 and "reconcil" in error["next_action"]


def test_P1_2_pre_tag_verified_absence_creates_new_ticket(
    monkeypatch, tmp_path, capsys
):
    world = BoundedTransport(tmp_path)
    locator, _ = prepare(world, monkeypatch, capsys, tmp_path)
    get = world.get
    monkeypatch.setattr(
        world,
        "get",
        lambda path, **kw: (
            {"total_count": 0, "artifacts": []}
            if path == "actions/runs/21/artifacts"
            else get(path, **kw)
        ),
    )
    code, result = worker(world, monkeypatch, capsys, locator)
    assert code == 0 and result["observed"] == "building", json.dumps(result)
    assert result["step"] == "build-request-2" and not world.publication_writes


def test_P1_1_capacity_failure_precedes_any_tag_or_release_write(publication):
    from test_publisher import invoke

    from cg_release.events import ControllerError
    from cg_release.models import MAX_RECORD_BYTES, canonical_bytes
    from cg_release.prepare_stage import checkpoint

    journal, record, *_ = publication
    record = checkpoint(
        journal, record, "capacity-pad-1", {"data": "x" * 31000}, record.state
    )
    remaining = MAX_RECORD_BYTES - 1024 - len(canonical_bytes(record)) - 512
    assert 0 < remaining < 32700
    checkpoint(
        journal, record, "capacity-pad-2", {"data": "x" * remaining}, record.state
    )
    with pytest.raises(ControllerError) as error:
        invoke(publication)
    assert error.value.code == "E_JOURNAL_CAPACITY"
    assert not publication[-1].writes
    assert not journal.get(record.request_id).publication_started


@pytest.mark.parametrize(
    "mutation",
    ["denied", "unauthenticated", "duplicate", "wrong-run", "replacement", "renamed"],
)
def test_P1_2_absence_recovery_does_not_accept_conflicting_artifacts(
    monkeypatch, tmp_path, capsys, mutation
):
    from copy import deepcopy

    from cg_release.events import ControllerError

    world = BoundedTransport(tmp_path)
    locator, _ = prepare(world, monkeypatch, capsys, tmp_path)
    get = world.get

    def changed(path, **kwargs):
        value = get(path, **kwargs)
        if path != "actions/runs/21/artifacts":
            return value
        if mutation == "denied":
            raise ControllerError("E_FORBIDDEN", "Denied inventory")
        if mutation == "unauthenticated":
            raise ControllerError("E_AUTH", "Unauthenticated inventory")
        value = deepcopy(value)
        row = value["artifacts"][0]
        row["expired"] = True
        if mutation == "duplicate":
            value["artifacts"].append({**row, "id": 52})
            value["total_count"] = 2
        if mutation == "wrong-run":
            row["workflow_run"]["id"] = 999
        if mutation == "replacement":
            row["id"] = 52
        if mutation == "renamed":
            row["name"] = "other"
        return value

    monkeypatch.setattr(world, "get", changed)
    code, result = worker(world, monkeypatch, capsys, locator)
    expected = {"denied": "E_FORBIDDEN", "unauthenticated": "E_AUTH"}.get(
        mutation, "E_ARTIFACT"
    )
    assert code == 2 and result["code"] == expected, json.dumps(result)
    assert not world.publication_writes


def test_P2_1_cache_rechecks_gate_identity_and_is_local_to_one_job(ready_build):
    from cg_release.events import ControllerError
    from cg_release.publication_inputs import verify_release_gates

    context, record, metadata, jobs = ready_build
    calls = []
    runner = context.api.runner

    def counted(*args, **kwargs):
        calls.append(args)
        return runner(*args, **kwargs)

    context.api.runner = counted
    cache = {}
    verify_release_gates(context, record, verified_artifacts=cache)
    verify_release_gates(context, record, verified_artifacts=cache)
    assert len(calls) == 1
    verify_release_gates(context, record, verified_artifacts={})
    assert len(calls) == 2
    jobs[0]["conclusion"] = "skipped"
    with pytest.raises(ControllerError):
        verify_release_gates(context, record, verified_artifacts=cache)
    assert len(calls) == 2
    jobs[0]["conclusion"] = "success"
    metadata["digest"] = "sha256:" + "f" * 64
    with pytest.raises(ControllerError):
        verify_release_gates(context, record, verified_artifacts=cache)
    assert len(calls) == 3
