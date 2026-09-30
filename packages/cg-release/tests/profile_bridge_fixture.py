"""Synthetic provider wire data for exact bridge evidence; never delivery evidence."""

import hashlib
import io
import json
import zipfile

from cg_release.journal import digest
from cg_release.profile_bridge import LINKS, MANAGED, STEPS, WORKFLOW


def configure(world, raw):
    """Install exact synthetic distribution objects and qualification archives."""
    identities, proofs = {}, {}
    world.bridge_commits = {}
    for name, tag, sha, oid, release_id in (
        ("previous", "v1.0.0.9000", "8" * 40, "7" * 40, 68),
        ("bridge", "v1.0.0", world.bridge_sha, world.bridge_oid, 70),
        ("successor", "v1.0.1-rc.1", "9" * 40, "6" * 40, 69),
    ):
        files = {p: (name + p).encode() for p in MANAGED}
        tree = world.git.tree(files)
        world.objects.update(world.git.blobs)
        world.trees.update(world.git.trees)
        world.bridge_commits[sha] = {"sha": sha, "tree": {"sha": tree}}
        item = dict(
            tag=tag, revision=sha, tag_object=oid, tree=tree, release_id=release_id
        )
        identities[name] = item
        proofs[name] = dict(
            release=item,
            tracked_digest=digest(
                sorted(
                    (r["path"], r["mode"], r["sha"])
                    for r in world.git.flat[tree]["tree"]
                )
            ),
            managed={p: hashlib.sha256(b).hexdigest() for p, b in files.items()},
            links=list(LINKS),
            pin=tag,
            copilot_refreshed=True,
        )
        if name != "bridge":
            world.tags[tag] = {"oid": oid, "commit": sha}
            world.tag_nodes.append(
                {"name": tag, "target": {"oid": oid, "__typename": "Tag"}}
            )
            world.release_rows.append(
                dict(
                    id=release_id,
                    tag_name=tag,
                    draft=False,
                    prerelease=True,
                    published_at="2026-09-09T00:00:00Z",
                )
            )
            raw["bootstrap"].append(
                dict(
                    release_id=release_id,
                    tag=tag,
                    commit=sha,
                    line="current",
                    version="1.0.0-dev.1" if name == "previous" else tag[1:],
                    legacy_version=tag[1:] if name == "previous" else None,
                    projections={},
                )
            )
    spec = dict(repository_id=123, repository_slug=world.slug, **identities)
    world.bridge_archives, world.bridge_metadata = {}, {}
    bridge = {
        **identities["bridge"],
        "previous": identities["previous"],
        "successor": identities["successor"],
        "workflow_path": WORKFLOW,
        "app_id": 15368,
    }
    for platform, run_id in (("windows", 91), ("unix", 92)):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr(
                "qualification.json",
                json.dumps(
                    dict(
                        schema_version=1,
                        kind="actual-bridge-clean-consumer-v1",
                        platform=platform,
                        repository_id=123,
                        repository_slug=world.slug,
                        spec_digest=digest(spec),
                        workflow_revision=world.bridge_sha,
                        run_id=run_id,
                        run_attempt=1,
                        stages=proofs,
                        new_pin_rejected_before_bridge=True,
                    )
                ),
            )
        data = stream.getvalue()
        sha = hashlib.sha256(data).hexdigest()
        world.bridge_archives[run_id] = data
        world.bridge_metadata[run_id] = dict(
            id=run_id,
            name="bridge-clean-client-" + platform,
            workflow_run={"id": run_id, "head_sha": world.bridge_sha},
            digest="sha256:" + sha,
            expired=False,
            size_in_bytes=len(data),
        )
        bridge.update(
            {
                platform + "_run_id": run_id,
                platform + "_job_id": run_id,
                platform + "_artifact_id": run_id,
                platform + "_artifact_digest": sha,
            }
        )
    raw["profile"]["bridge"] = bridge


def wire(world, endpoint):
    """Return only additional read endpoints for the synthetic bridge distributions."""
    if endpoint.startswith("git/commits/") and endpoint[12:] in world.bridge_commits:
        return world.bridge_commits[endpoint[12:]]
    if endpoint.startswith("releases/") and endpoint[9:] in {"68", "69"}:
        return next(r for r in world.release_rows if r["id"] == int(endpoint[9:]))
    if endpoint.startswith("actions/runs/") and endpoint.split("/")[2] in {"91", "92"}:
        run_id = int(endpoint.split("/")[2])
        if endpoint.endswith("artifacts"):
            return {"total_count": 1, "artifacts": [world.bridge_metadata[run_id]]}
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
                        status="completed",
                        conclusion="success",
                        steps=[
                            dict(name=n, status="completed", conclusion="success")
                            for n in STEPS
                        ],
                    )
                ],
            }
        return dict(
            id=run_id,
            head_sha=world.bridge_sha,
            run_attempt=1,
            repository={"id": 123},
            status="completed",
            conclusion="success",
            event="workflow_dispatch",
            path=WORKFLOW,
            check_suite_id=run_id,
        )
    return None
