"""Validate the complete mutable input before the composer creates any output."""

from pathlib import Path

from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.profile_dispatch import verify_identity
from cg_release.profile_snapshot import verify_snapshot
from cg_release.snapshot_contract import MAX_ENVELOPE_BYTES


def acquire_dev(context, sealed: dict, run_id: int, root: Path) -> bytes:
    """Read a registered dev artifact, e.g. acquire_dev(ctx, ticket, 12, root).

    Args: root is an absent absolute output under an existing non-aliased parent.
    Returns: Fully verified dev envelope bytes from this run's downloaded artifact.
    Raises: ControllerError before output creation for stale run, job, path or data.
    Reads remote run/job status and a regular local input; never writes or executes it.
    """
    if (
        not isinstance(root, Path)
        or not root.is_absolute()
        or root.resolve() != root
        or root.exists()
        or not root.parent.is_dir()
    ):
        raise ControllerError("E_HOOK", "Composition output containment is invalid.")
    run = context.api.get(f"actions/runs/{run_id}")
    verify_identity(run, sealed, run_id)
    if run.get("status") != "in_progress":
        raise ControllerError("E_HOOK", "Composition run is no longer active.")
    jobs = inventory(context.api, f"actions/runs/{run_id}/attempts/1/jobs", "jobs")
    selected = [j for j in jobs if j.get("name") == "dev-preview"]
    if (
        len(selected) != 1
        or selected[0].get("conclusion") != "success"
        or selected[0].get("run_id") != run_id
        or selected[0].get("run_attempt") != 1
    ):
        raise ControllerError(
            "E_HOOK", "Registered unprivileged dev build is not successful."
        )
    source = root.parent / "dev-artifact/dev-docs.json"
    if (
        source.is_symlink()
        or not source.is_file()
        or source.stat().st_nlink != 1
        or source.resolve() != source
        or source.stat().st_size > MAX_ENVELOPE_BYTES
    ):
        raise ControllerError("E_HOOK", "Mutable snapshot envelope is invalid.")
    raw = source.read_bytes()
    verify_snapshot(
        raw, tag=None, sha=sealed["dev_sha"], run_id=run_id, run_attempt=1, kind="dev"
    )
    return raw
