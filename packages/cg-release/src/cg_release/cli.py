"""Release preview, durable start, read-only status, and trusted resume dispatch."""

import argparse
import re
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from loguru import logger
from semver import Version

from cg_release import runtime
from cg_release.admission import Locator
from cg_release.events import ControllerError, configure_diagnostics, emit_event
from cg_release.lifecycle import watch
from cg_release.models import Event
from cg_release.preview import confirmed_proposal, create_proposal
from cg_release.read_session import ReadSession
from cg_release.source import acquire_snapshot
from cg_release.timing import TimingRecorder


class ContractParser(argparse.ArgumentParser):
    """Reject malformed options without echoing arbitrary secret-bearing argv."""

    def error(self, message: str) -> None:
        """Raise a typed argument error instead of printing the supplied value."""
        raise ControllerError("E_ARGUMENT", "Invalid arguments; use command --help.")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Validate the four-command schema without consulting a repository.

    Args:
        argv: Arguments excluding executable, e.g. ``['plan', '--bump', 'patch']``.
    Returns:
        Validated namespace. No remote or local writes occur.
    Raises:
        ControllerError: Invalid argument combinations or syntax.
    """
    parser = ContractParser(prog="cg-release", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "start", "status", "resume"):
        sub = commands.add_parser(command, allow_abbrev=False)
        sub.add_argument("--json", action="store_true")
        if command in {"plan", "start"}:
            version = sub.add_mutually_exclusive_group(required=True)
            version.add_argument(
                "--bump", choices=("major", "minor", "patch", "prerelease")
            )
            version.add_argument("--version")
            sub.add_argument("--channel")
            sub.add_argument("--branch")
            sub.add_argument("--line")
            sub.add_argument("--allow-non-deployment-branch", action="store_true")
            sub.add_argument("--reason")
            sub.add_argument("--sign", action="store_true")
            sub.add_argument("--yes", action="store_true")
        else:
            sub.add_argument("request_id")
            if command == "status":
                sub.add_argument("--watch", action="store_true")
                sub.add_argument("--timeout", default="10m")
    args = parser.parse_args(argv)
    try:
        if args.command in {"plan", "start"}:
            if args.version is not None:
                if str(Version.parse(args.version)) != args.version:
                    raise ValueError("version must be exact SemVer")
                if args.channel is not None:
                    raise ValueError("channel with explicit version")
            if args.channel is not None and (
                not re.fullmatch(r"[A-Za-z0-9-]{1,64}", args.channel)
                or args.channel.isdigit()
            ):
                raise ValueError("invalid channel")
            if args.allow_non_deployment_branch != bool(args.reason):
                raise ValueError("override reason mismatch")
            if args.reason and (not args.reason.strip() or len(args.reason) > 1024):
                raise ValueError("invalid reason")
            for value in (args.branch, args.line):
                if value is not None and (
                    not value.strip()
                    or len(value) > 255
                    or value.startswith("-")
                    or any(ord(char) < 32 for char in value)
                ):
                    raise ValueError("invalid identifier")
        elif not args.request_id or len(args.request_id) > 4096:
            raise ValueError("invalid request locator")
        if args.command == "status":
            match = re.fullmatch(r"([1-9][0-9]{0,4})([sm])", args.timeout)
            if not match:
                raise ValueError("invalid timeout")
            args.timeout_seconds = int(match[1]) * (60 if match[2] == "m" else 1)
            if args.timeout_seconds > 3600:
                raise ValueError("watch exceeds maximum")
    except ValueError:
        raise ControllerError(
            "E_ARGUMENT", "Invalid arguments; use command --help."
        ) from None
    return args


def main(
    argv: Sequence[str] | None = None, *, clock: Callable[[], float] = time.monotonic
) -> int:
    """Run the preview CLI, e.g. ``main(['plan', '--bump', 'patch'])``.

    Args:
        argv: Explicit arguments or the process command line.
        clock: Injectable monotonic clock shared by reads and confirmation timing.
    Returns:
        Exit 0 for a preview; 2 for errors/disabled admission. Help exits 0.
    """
    configure_diagnostics()
    arguments = list(sys.argv[1:] if argv is None else argv)
    retained_locator = None
    retained_version, retained_step, retained_observed = None, None, None
    command_started, human_wait = clock(), 0.0
    try:
        args = parse_args(arguments)
        api_factory = ReadSession()

        def emit(event):
            nonlocal \
                retained_locator, \
                retained_version, \
                retained_step, \
                retained_observed
            if event.request_id:
                retained_locator = event.request_id
            retained_version = event.version or retained_version
            retained_step = event.step or retained_step
            retained_observed = event.observed or retained_observed
            if event.elapsed_seconds is None:
                event = event.model_copy(
                    update={
                        "elapsed_seconds": max(
                            0.0, clock() - command_started - human_wait
                        )
                    }
                )
            emit_event(event, json_output=args.json)

        command_started = clock()
        deadline = command_started + 120
        timing = TimingRecorder(enabled=True, clock=clock)

        def acquire():
            return acquire_snapshot(
                args,
                cwd=Path.cwd(),
                deadline=deadline,
                clock=clock,
                api_factory=api_factory,
            )

        def confirm(proposal):
            nonlocal deadline, human_wait
            deadline = min(
                deadline, command_started + proposal.inputs["command_timeout_seconds"]
            )
            if clock() >= deadline:
                raise ControllerError(
                    "E_DEADLINE", "Preview exceeded the command deadline."
                )
            emit_event(
                Event(
                    kind="preview",
                    version=proposal.version,
                    message="Read-only proposal; no reservation or submission.",
                    proposal=proposal.display(),
                ),
                json_output=args.json,
            )
            if args.command == "plan" or args.yes:
                return True
            if not sys.stdin.isatty():
                raise ControllerError(
                    "E_CONFIRMATION_REQUIRED",
                    "Noninteractive start requires --yes; no submission occurred.",
                )
            try:
                sys.stderr.write("Accept this exact proposal? [y/N] ")
                sys.stderr.flush()
                with timing.span("confirmation"):
                    return input().strip().lower() in {"y", "yes"}
            except (EOFError, KeyboardInterrupt):
                return False
            finally:
                measured = timing.records[-1]
                elapsed = measured["elapsed_seconds"]
                deadline += elapsed
                human_wait += elapsed
                emit_event(
                    Event(
                        kind="timing",
                        step="confirmation",
                        elapsed_seconds=float(elapsed),
                        observed=measured["outcome"],
                        message="Human confirmation interval; not submission time.",
                    ),
                    json_output=args.json,
                )

        if args.command == "plan":
            confirm(create_proposal(acquire(), args))
            return 0
        if args.command == "start":
            proposal = confirmed_proposal(args, acquire, confirm)
            if clock() >= deadline:
                raise ControllerError(
                    "E_DEADLINE", "Recheck exceeded the command deadline."
                )
            runtime.start(
                proposal, emit, deadline=deadline, clock=clock, api_factory=api_factory
            )
            return 0
        Locator.decode(args.request_id)
        retained_locator = args.request_id
        if args.command == "resume":
            emit(
                runtime.resume(
                    args.request_id,
                    deadline=deadline,
                    clock=clock,
                    api_factory=api_factory,
                )
            )
        elif args.watch:
            end = clock() + args.timeout_seconds
            watch(
                lambda: runtime.status(
                    args.request_id, deadline=end, clock=clock, api_factory=api_factory
                ),
                emit,
                timeout=args.timeout_seconds,
                clock=clock,
            )
        else:
            emit(
                runtime.status(
                    args.request_id,
                    deadline=deadline,
                    clock=clock,
                    api_factory=api_factory,
                )
            )
        return 0
    except ControllerError as caught:
        error = caught
    except KeyboardInterrupt:
        error = ControllerError(
            "E_SUBMISSION_UNKNOWN"
            if retained_step == "submission"
            else "E_INTERRUPTED",
            "Interrupted; retain the locator and inspect remote state before retry."
            if retained_locator
            else "Interrupted before a submission attempt.",
        )
    emit_event(
        Event(
            kind="error",
            code=error.code,
            message=error.message,
            request_id=retained_locator,
            version=retained_version,
            step=retained_step,
            observed=retained_observed,
            expected="verified remote state" if retained_locator else None,
            elapsed_seconds=max(0.0, clock() - command_started - human_wait),
            next_action=(
                "Retain locator and use status; do not repeat start."
                if retained_locator
                else "Inspect this error and command --help."
            ),
        ),
        json_output="--json" in arguments,
    )
    logger.error("{}", error.code)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
