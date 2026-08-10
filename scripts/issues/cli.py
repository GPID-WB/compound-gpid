"""Argument parsing and command-line orchestration for readiness checks."""
from __future__ import annotations

import argparse
import sys
from typing import Callable, Optional, Sequence, TextIO, Type

from .contract import ApiError, ConfigError, EXIT_API, EXIT_CONFIG, ReadinessResult
from .render import render_human, render_json


class _ReadinessArgumentParser(argparse.ArgumentParser):
    """Argument parser that reserves exit code 3 for usage/configuration errors."""

    def __init__(self, *args, stderr: Optional[TextIO] = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._err_stream = stderr if stderr is not None else sys.stderr

    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(self._err_stream)
        self._err_stream.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(EXIT_CONFIG)


def build_parser(*, stderr: Optional[TextIO] = None) -> argparse.ArgumentParser:
    """Build the readiness CLI parser.

    Args:
        stderr: Optional stream for usage errors.

    Returns:
        An argument parser with mutually exclusive issue and fixture sources.

    Example:
        ``build_parser().parse_args(["--fixture", "ready.json"])`` parses a
        local validation source.
    """
    parser = _ReadinessArgumentParser(
        prog="cg-issue-ready",
        stderr=stderr,
        description=(
            "Deterministic, read-only readiness validator for Copilot "
            "implementation issues. Never mutates GitHub state."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--issue", type=int, metavar="N", help="issue number to validate (live, read-only)")
    source.add_argument("--fixture", metavar="PATH", help="offline JSON fixture file (no network)")
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="read-only validation (always on; the validator never mutates GitHub state)",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="machine-readable JSON output")
    return parser


def _emit(result: ReadinessResult, args: argparse.Namespace, out: TextIO) -> None:
    """Write the selected result representation to a stream."""
    text = render_json(result) if args.as_json else render_human(result)
    out.write(text)
    if not text.endswith("\n"):
        out.write("\n")


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    client=None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
    fixture_client_cls: Optional[Type] = None,
    gh_client_cls: Optional[Type] = None,
    validate_fn: Optional[Callable[..., ReadinessResult]] = None,
) -> int:
    """Run the read-only readiness CLI.

    Args:
        argv: Command arguments, defaulting to ``sys.argv[1:]``.
        client: Optional injected client used by deterministic tests.
        out: Output stream for the human or JSON result.
        err: Stream for parser usage errors.
        fixture_client_cls: Optional fixture-client factory for compatibility
            injection.
        gh_client_cls: Optional live-client factory for compatibility injection.
        validate_fn: Optional validator function for compatibility injection.

    Returns:
        One documented exit code: 0, 2, 3, or 4.

    Raises:
        SystemExit: When argparse detects missing, conflicting, or invalid
            command-line arguments.

    Example:
        ``main(["--issue", "127", "--dry-run"], client=client)`` runs a
        validation without any GitHub mutation.
    """
    from .clients import FixtureClient, GhCliClient
    from .orchestration import _error_result, validate_readiness

    fixture_class = fixture_client_cls or FixtureClient
    gh_class = gh_client_cls or GhCliClient
    validator = validate_fn or validate_readiness
    parser = build_parser(stderr=err)
    args = parser.parse_args(argv)

    if args.fixture is not None:
        if not args.fixture:
            result = _error_result(
                None, EXIT_CONFIG, "--fixture path must not be empty", args.dry_run,
            )
            _emit(result, args, out)
            return result.exit_code
        try:
            fixture_client = fixture_class(args.fixture)
        except (ConfigError, ApiError) as error:
            code = EXIT_CONFIG if isinstance(error, ConfigError) else EXIT_API
            result = _error_result(None, code, str(error), args.dry_run)
            _emit(result, args, out)
            return result.exit_code
        issue_number = fixture_client.issue_number
        active_client = client or fixture_client
    else:
        issue_number = args.issue
        active_client = client or gh_class()

    result = validator(issue_number, active_client, dry_run=args.dry_run)
    _emit(result, args, out)
    return result.exit_code
