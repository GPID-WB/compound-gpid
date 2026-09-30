"""Command-line interface for the Stage 3 Copilot dispatcher."""
from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional, Sequence, TextIO

from .cli import _ReadinessArgumentParser
from .dispatch_client import DispatchMutator, GhDispatchMutator
from .dispatch_contract import DispatchResult
from .dispatch_render import render_human, render_json


def build_parser(*, stderr: Optional[TextIO] = None) -> argparse.ArgumentParser:
    """Build the dispatch CLI parser.

    Args:
        stderr: Optional stream for usage errors.

    Returns:
        An argument parser with issue and mode arguments; usage errors exit
        with ``EXIT_CONFIG`` (3), not argparse's default code 2.

    Example:
        ``build_parser().parse_args(["--issue", "127"])`` parses a dry-run
        dispatch request.
    """
    parser = _ReadinessArgumentParser(
        prog="cg-issue-dispatch",
        stderr=stderr,
        description=(
            "Controlled, manually triggered single-issue Copilot dispatcher. "
            "Dry-run (default) performs zero mutations."
        ),
    )
    parser.add_argument("--issue", type=int, required=True, metavar="N", help="issue number to dispatch")
    parser.add_argument(
        "--dry-run", dest="dry_run", action="store_true", default=True,
        help="validate and report only; zero mutations (default)",
    )
    parser.add_argument(
        "--no-dry-run", dest="dry_run", action="store_false",
        help="perform the live dispatch sequence (assignment, Project Status, audit comment)",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="machine-readable JSON output")
    return parser


def _emit(result: DispatchResult, args: argparse.Namespace, out: TextIO) -> None:
    """Write the selected result representation to a stream.

    Args:
        result: Dispatcher result to render.
        args: Parsed CLI arguments.
        out: Output stream.
    """
    text = render_json(result) if args.as_json else render_human(result)
    out.write(text)
    if not text.endswith("\n"):
        out.write("\n")


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    read_client=None,
    mutator: Optional[DispatchMutator] = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
    mutator_factory: Optional[Callable[[], DispatchMutator]] = None,
    dispatch_fn: Optional[Callable[..., DispatchResult]] = None,
) -> int:
    """Run the dispatch CLI.

    Args:
        argv: Command arguments, defaulting to ``sys.argv[1:]``.
        read_client: Optional injected read-only readiness client for tests.
        mutator: Optional injected mutation client for tests.
        out: Output stream for the result.
        err: Stream for parser usage errors.
        mutator_factory: Optional factory producing a real mutation client.
        dispatch_fn: Optional dispatch function for test injection.

    Returns:
        One documented exit code: 0, 2, 3, 4, 5, 6, or 7.

    Raises:
        SystemExit: When argparse detects missing or invalid arguments.

    Example:
        ``main(["--issue", "127", "--dry-run"], read_client=client,
        mutator=mutator)`` runs a zero-mutation dry run.
    """
    from .clients import GhCliClient
    from .dispatch import run_dispatch

    parser = build_parser(stderr=err)
    args = parser.parse_args(argv)
    active_read_client = read_client
    if active_read_client is None:
        active_read_client = GhCliClient()
    active_mutator = mutator
    if active_mutator is None:
        active_mutator = (mutator_factory or GhDispatchMutator)()
    dispatch = dispatch_fn or run_dispatch
    result = dispatch(
        args.issue, active_read_client, active_mutator, dry_run=args.dry_run
    )
    _emit(result, args, out)
    return result.exit_code
