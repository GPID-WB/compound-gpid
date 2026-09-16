"""Bounded binary GitHub artifact downloads through the existing gh transport."""

from cg_release.events import ControllerError
from cg_release.github_checks import inventory
from cg_release.process import MAX_BINARY_BYTES


def retained_archive(api, run_id, controller_sha, *, expected_id=None):
    """Return retained metadata or verified absence/expiry, never a read denial."""
    rows = inventory(api, f"actions/runs/{run_id}/artifacts", "artifacts")
    matches = [row for row in rows if row.get("name") == "release-assets"]
    try:
        if len(matches) > 1 or (
            expected_id is not None
            and any(
                row["id"] == expected_id and row.get("name") != "release-assets"
                for row in rows
            )
        ):
            raise ValueError
        if not matches:
            return None
        metadata = matches[0]
        if (
            type(metadata["id"]) is not int
            or metadata["id"] <= 0
            or (expected_id is not None and metadata["id"] != expected_id)
            or type(metadata["expired"]) is not bool
            or type(metadata["workflow_run"]["id"]) is not int
            or metadata["workflow_run"]["id"] != run_id
            or metadata["workflow_run"]["head_sha"] != controller_sha
        ):
            raise ValueError
        return None if metadata["expired"] else metadata
    except (KeyError, ValueError, TypeError, AttributeError):
        raise ControllerError(
            "E_ARTIFACT",
            "Registered artifact inventory is ambiguous or has changed identity.",
        ) from None


def download_archive(api, metadata: dict) -> bytes:
    """Download an exact artifact ID, e.g. download_archive(api, meta).

    Metadata must first be acquired from the registered run inventory. No upload
    URL or user-supplied download URL is followed. gh owns GitHub redirect handling.
    This v1 transport has an explicit 64 MiB compressed archive capacity.
    """
    try:
        identity, size = metadata["id"], metadata["size_in_bytes"]
        if (
            type(identity) is not int
            or identity <= 0
            or type(size) is not int
            or not 1 <= size <= MAX_BINARY_BYTES
            or metadata["expired"] is not False
        ):
            raise ValueError
    except (KeyError, ValueError, TypeError):
        raise ControllerError(
            "E_ARTIFACT", "Artifact locator, retention or download size is invalid."
        ) from None
    result = api.runner(
        "gh",
        [
            "api",
            "--method",
            "GET",
            "--hostname",
            api.host,
            f"repos/{api.slug}/actions/artifacts/{identity}/zip",
        ],
        cwd=api.cwd,
        timeout=min(api.read_seconds, api.remaining()),
        binary_output=True,
        max_output_bytes=size,
        allow_failure=True,
    )
    if (
        result.returncode
        or not isinstance(result.stdout, bytes)
        or len(result.stdout) != size
    ):
        raise ControllerError("E_ARTIFACT", "Artifact download failed or changed size.")
    return result.stdout
