"""Created 2026-08-12. Command-line entrypoint for local evidence operations."""
from __future__ import annotations

import argparse
from typing import Optional, Sequence

from .config import ensure_supported_runtime


def build_parser() -> argparse.ArgumentParser:
    """Build the local-only evidence workbench command parser.

    Args:
        None.

    Returns:
        An argument parser exposing dry-run, search, create, verify, and recover.

    Example:
        ``build_parser().parse_args(["--help"])`` exposes CLI help.
    """
    parser = argparse.ArgumentParser(
        prog="research-evidence",
        description="Local-only evidence and claim verification workbench.",
    )
    subparsers = parser.add_subparsers(dest="command")
    for name, help_text in (
        ("dry-run", "Validate local runtime configuration without mutation."),
        ("search", "Search the derived local lexical index."),
        ("create", "Create a manually supplied claim/evidence decision."),
        ("verify", "Verify a stored quotation against its source."),
        ("recover", "Recover journaled canonical state after interruption."),
    ):
        subparsers.add_parser(name, help=help_text)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse the CLI and run the safe command boundary.

    Args:
        argv: Optional argument sequence; process arguments are used when omitted.

    Returns:
        Process-style exit code, with zero for help or an accepted command.

    Raises:
        RuntimeError: If the active Python runtime is outside the supported range.

    Example:
        ``main(["--help"])`` returns zero after displaying help.
    """
    ensure_supported_runtime()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
    return 0
