"""Separate trusted registration and unprivileged exact-source build entry points."""

import argparse
import os
import re
import stat
import subprocess
import time
from pathlib import Path

from cg_release.build_control import register_build, ticket
from cg_release.context import context_for
from cg_release.events import ControllerError, emit_event
from cg_release.hook_authority import authorize_hooks
from cg_release.models import Build, Event, canonical_bytes, load_record
from cg_release.policy import safe_path
from cg_release.process import run_process
from cg_release.recovery_authority import authorize_record


def execute_build(
    spec: dict, sha: str, *, source: Path, output: Path, runner=subprocess.run
) -> None:
    """Run policy argv in the source job, e.g. execute_build(spec, sha, ...).

    The caller supplies a fresh unprivileged runner. Publication/control credentials
    must never be present in this job. Output bytes are still untrusted until the
    separate archive verifier checks the actual registered-run download.
    Args: strict Build dictionary, exact source SHA, source checkout, new output
    Path, and optional outer subprocess runner. Returns None. Raises ControllerError
    on invalid identity, paths, command failure, timeout or copied artifact limits.
    Writes only the declared source outputs and new artifact staging directory.
    """
    try:
        build = load_record(Build, canonical_bytes(spec))
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError
        head = run_process("git", ["rev-parse", "HEAD"], cwd=source).stdout.strip()
        if head != sha or output.exists():
            raise ValueError
        cwd = source if build.cwd == "." else source / safe_path(build.cwd)
        if not cwd.resolve().is_relative_to(source.resolve()):
            raise ValueError
        result = runner(
            build.argv,
            cwd=cwd,
            shell=False,
            timeout=1200,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode:
            raise ControllerError(
                "E_BUILD_COMMAND",
                "Declared source build failed; inspect its isolated job.",
            )
        output.mkdir(parents=True, exist_ok=False)
        total, seen = 0, set()
        for artifact in build.artifacts:
            safe_path(artifact.path)
            path = source / artifact.path
            if not path.exists() and not artifact.required:
                continue
            if artifact.path.casefold() in seen or len(seen) >= build.max_artifacts:
                raise ValueError
            seen.add(artifact.path.casefold())
            before = path.lstat()
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or not path.resolve().is_relative_to(source.resolve())
                or before.st_size > artifact.max_bytes
            ):
                raise ValueError
            destination = output / artifact.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            size = 0
            with path.open("rb") as incoming, destination.open("xb") as outgoing:
                opened = os.fstat(incoming.fileno())
                if (opened.st_dev, opened.st_ino, opened.st_size) != (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                ):
                    raise ValueError
                while chunk := incoming.read(65536):
                    size += len(chunk)
                    total += len(chunk)
                    if size > artifact.max_bytes or total > build.max_total_bytes:
                        raise ValueError
                    outgoing.write(chunk)
                after = path.lstat()
                if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                ):
                    raise ValueError
    except (ValueError, OSError, subprocess.SubprocessError):
        raise ControllerError(
            "E_BUILD_SOURCE",
            "Exact source or declared regular outputs failed validation.",
        ) from None


def main(argv=None) -> int:
    """Run register/build in distinct jobs, e.g. main(['register', ...]).

    Args: argv selects register with --request-id/--nonce, or build with --source
    and --output; Actions/source identity comes from the documented environment.
    Returns 0 or 2 with a structured error event; argparse errors exit 2. Register
    rechecks authority and writes only journal/GITHUB_OUTPUT registration. Build
    executes source policy argv and stages files without control credentials.
    """
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("operation", choices=["register", "build"])
        parser.add_argument("--request-id")
        parser.add_argument("--nonce")
        parser.add_argument("--source", type=Path)
        parser.add_argument("--output", type=Path)
        args = parser.parse_args(argv)
        if args.operation == "build":
            if (
                os.environ.get("CG_RELEASE_SOURCE_JOB") != "true"
                or os.environ.get("GH_TOKEN")
                or os.environ.get("RELEASE_CONTROL_APP_PRIVATE_KEY")
            ):
                raise ControllerError(
                    "E_BUILD_SOURCE",
                    "Build execution requires the unprivileged source job.",
                )
            build = load_record(Build, os.environ["CG_RELEASE_BUILD_SPEC"].encode())
            execute_build(
                build.model_dump(mode="json"),
                os.environ["CG_RELEASE_SOURCE_SHA"],
                source=args.source,
                output=args.output,
            )
        else:
            from cg_release.controller import verify_run

            context = context_for(
                args.request_id, deadline=time.monotonic() + 120, writable=True
            )
            record = context.journal.get(args.request_id)
            _, sealed = ticket(record, args.nonce)
            _, event = verify_run(
                context, dict(os.environ), workflow=sealed["workflow_path"]
            )
            if event != "workflow_dispatch":
                raise ControllerError(
                    "E_BUILD_REGISTRATION",
                    "Only trusted dispatch may register a build.",
                )
            authorize_record(context, record)
            register_build(
                context,
                args.request_id,
                args.nonce,
                dict(os.environ),
                before_write=lambda: authorize_hooks(
                    context, context.journal.get(args.request_id), fresh=True
                ),
            )
            outputs = {
                "source_sha": sealed["release_sha"],
                "source_tree": sealed["release_tree"],
                "build_spec": canonical_bytes(sealed["build_spec"]).decode(),
                "controller_revision": context.policy.controller.revision,
                "wheel_digest": context.policy.controller.wheel_digest,
                "produces_artifacts": "true"
                if sealed["produces_artifacts"]
                else "false",
            }
            with Path(os.environ["GITHUB_OUTPUT"]).open(
                "a", encoding="utf-8", newline="\n"
            ) as output:
                for key, value in outputs.items():
                    output.write(f"{key}={value}\n")
        return 0
    except (KeyError, TypeError, ValueError, OSError):
        error = ControllerError(
            "E_BUILD_INPUT", "Build worker input or output is invalid."
        )
    except ControllerError as caught:
        error = caught
    emit_event(
        Event(kind="error", code=error.code, message=error.message), json_output=True
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
