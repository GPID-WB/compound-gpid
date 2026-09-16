"""Explicit authorized real bridge qualification; never an ordinary fixture test."""

import argparse
import os
import platform
import time
from pathlib import Path

from cg_release.authority import actor_role
from cg_release.bridge_client import roundtrip
from cg_release.events import ControllerError, emit_event
from cg_release.github import GitHubReads
from cg_release.journal import digest
from cg_release.models import Event, canonical_bytes, load_record
from cg_release.profile_bridge import verify_releases
from cg_release.profile_models import BridgeSpec


def qualify(
    spec: BridgeSpec, root: Path, env: dict, *, authorized: bool, api=None
) -> dict:
    """Qualify actual three-release delivery on one authorized native source-only job.

    Args: reviewed explicit spec, new scratch root, Actions identity environment,
    explicit authorized=True, optional outer GET transport. Returns a strict receipt
    for qualification.json. Raises ControllerError before clone on unknown authority,
    wrong host/run/source/release, or during real updater/link failure. Only scratch
    files change; no tags, Releases, settings, global installs or profile writes.
    Example: qualify(spec, scratch, dict(os.environ), authorized=True) after approval.
    """
    if not authorized:
        raise ControllerError(
            "E_BRIDGE_AUTHORIZATION", "Explicit real bridge authorization is required."
        )
    try:
        host = "windows" if platform.system() == "Windows" else "unix"
        if (
            env["GITHUB_ACTIONS"] != "true"
            or env["GITHUB_EVENT_NAME"] != "workflow_dispatch"
            or env["GITHUB_SHA"] != spec.bridge.revision
            or env["GITHUB_REPOSITORY"] != spec.repository_slug
            or int(env["GITHUB_REPOSITORY_ID"]) != spec.repository_id
            or env["CG_BRIDGE_PLATFORM"] != host
            or int(env["GITHUB_RUN_ATTEMPT"]) != 1
            or platform.system() not in {"Windows", "Linux", "Darwin"}
            or any(
                env.get(key)
                for key in (
                    "RELEASE_CONTROL_TOKEN",
                    "RELEASE_PUBLISH_TOKEN",
                    "RELEASE_CONTROL_APP_PRIVATE_KEY",
                    "RELEASE_PUBLISH_APP_PRIVATE_KEY",
                )
            )
            or env.get("CG_INTERNAL_CALL")
            or env.get("CG_SKIP_UPDATE")
        ):
            raise ValueError
        run_id, actor = int(env["GITHUB_RUN_ID"]), int(env["GITHUB_ACTOR_ID"])
        if run_id <= 0 or actor <= 0:
            raise ValueError
    except (ValueError, KeyError):
        raise ControllerError(
            "E_BRIDGE_AUTHORIZATION", "Exact native bridge job identity is required."
        ) from None
    api = api or GitHubReads(
        "github.com",
        spec.repository_slug,
        cwd=Path.cwd(),
        deadline=time.monotonic() + 600,
    )
    if actor_role(api, actor) not in {"maintain", "admin"}:
        raise ControllerError(
            "E_BRIDGE_AUTHORIZATION", "Current maintainer authorization is required."
        )
    expected = verify_releases(api, spec)
    observed = roundtrip(
        spec,
        root,
        remote=f"https://github.com/{spec.repository_slug}.git",
        shell_kind=host,
    )
    if observed != expected or verify_releases(api, spec) != expected:
        raise ControllerError(
            "E_BRIDGE_CLIENT",
            "Real bridge installed tree differs from remote evidence.",
        )
    if actor_role(api, actor) not in {"maintain", "admin"}:
        raise ControllerError(
            "E_BRIDGE_AUTHORIZATION", "Maintainer authorization changed."
        )
    return dict(
        schema_version=1,
        kind="actual-bridge-clean-consumer-v1",
        platform=host,
        spec_digest=digest(spec),
        repository_id=spec.repository_id,
        repository_slug=spec.repository_slug,
        workflow_revision=spec.bridge.revision,
        run_id=run_id,
        run_attempt=1,
        stages=observed,
        new_pin_rejected_before_bridge=True,
    )


def main(argv=None) -> int:
    """Parse --authorize-real-bridge/--scratch/--output and CG_BRIDGE_SPEC JSON.

    Returns 0 and creates one exclusive receipt only after qualification; returns 2
    with a structured error otherwise. Argparse errors exit 2. Example:
    python -m cg_release.bridge_qualifier --authorize-real-bridge --scratch private
    --output qualification.json. This is an externally authorized operation only.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-real-bridge", action="store_true")
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        spec = load_record(BridgeSpec, os.environ["CG_BRIDGE_SPEC"].encode())
        if args.output.exists():
            raise ControllerError(
                "E_BRIDGE_OUTPUT", "Bridge evidence output already exists."
            )
        result = qualify(
            spec, args.scratch, dict(os.environ), authorized=args.authorize_real_bridge
        )
        with args.output.open("xb") as output:
            output.write(canonical_bytes(result) + b"\n")
        return 0
    except (KeyError, OSError):
        error = ControllerError(
            "E_BRIDGE_INPUT", "Explicit bridge inputs or output are unavailable."
        )
    except ControllerError as caught:
        error = caught
    emit_event(
        Event(kind="error", code=error.code, message=error.message), json_output=True
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
