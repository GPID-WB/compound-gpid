#!/usr/bin/env python3
"""Generate and maintain the deterministic Compound GPID help catalog.

Exit codes:
    0: The requested operation succeeded.
    2: Source validation or explicit-review validation failed.
    3: The committed catalog is missing, stale, or unexpected.
    4: An input/output operation failed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import BinaryIO, Optional, Sequence

from help import catalog


EXIT_SUCCESS = 0
EXIT_SOURCE_INVALID = 2
EXIT_CATALOG_STALE = 3
EXIT_IO_ERROR = 4


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse one explicit catalog or one-record digest operation."""
    parser = argparse.ArgumentParser(
        description="Generate or verify the deterministic command help catalog."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Canonical Compound GPID source root.",
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true", help="Atomically write the catalog.")
    modes.add_argument("--check", action="store_true", help="Check catalog freshness.")
    modes.add_argument("--stdout", action="store_true", help="Write expected catalog bytes to stdout.")
    modes.add_argument(
        "--preview-definition-digest",
        metavar="QUALIFIED_ID",
        help="Preview one named record's current and computed definition digest.",
    )
    modes.add_argument(
        "--repin-definition-digest",
        metavar="QUALIFIED_ID",
        help="Refresh one named record's digest after metadata review.",
    )
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Confirm that the one record selected for repinning was reviewed.",
    )
    arguments = parser.parse_args(argv)
    if arguments.repin_definition_digest and not arguments.reviewed:
        parser.error("--repin-definition-digest requires --reviewed")
    if arguments.reviewed and not arguments.repin_definition_digest:
        parser.error("--reviewed is valid only with --repin-definition-digest")
    return arguments


def _write(stream: BinaryIO, content: bytes) -> None:
    stream.write(content)
    stream.flush()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main(
    argv: Optional[Sequence[str]] = None,
    stdout: Optional[BinaryIO] = None,
    stderr: Optional[BinaryIO] = None,
) -> int:
    """Run one fail-closed catalog maintenance operation."""
    arguments = parse_args(argv)
    output_stream = stdout if stdout is not None else sys.stdout.buffer
    error_stream = stderr if stderr is not None else sys.stderr.buffer
    root = arguments.root.resolve()
    try:
        if arguments.stdout:
            _write(output_stream, catalog.generate_catalog_bytes(root))
        elif arguments.check:
            catalog.check_catalog(root)
            _write(
                output_stream,
                "help catalog is current: {}\n".format(
                    catalog.CATALOG_OUTPUT_PATH
                ).encode("utf-8"),
            )
        elif arguments.write:
            changed = catalog.write_catalog(root)
            action = "wrote" if changed else "already current"
            _write(
                output_stream,
                "help catalog {}: {}\n".format(
                    action, catalog.CATALOG_OUTPUT_PATH
                ).encode("utf-8"),
            )
        elif arguments.preview_definition_digest:
            preview = catalog.preview_definition_digest(
                root, arguments.preview_definition_digest
            )
            _write(output_stream, _json_bytes(preview))
        else:
            result = catalog.repin_definition_digest(
                root, arguments.repin_definition_digest
            )
            _write(output_stream, _json_bytes(result))
        return EXIT_SUCCESS
    except catalog.HelpValidationError as error:
        _write(
            error_stream,
            "help catalog source validation failed: {}\n".format(error).encode(
                "utf-8"
            ),
        )
        return EXIT_SOURCE_INVALID
    except catalog.HelpCatalogStaleError as error:
        _write(
            error_stream,
            "help catalog freshness check failed: {}\n".format(error).encode(
                "utf-8"
            ),
        )
        return EXIT_CATALOG_STALE
    except (catalog.HelpCatalogIOError, OSError) as error:
        try:
            _write(
                error_stream,
                "help catalog I/O failed: {}\n".format(error).encode("utf-8"),
            )
        except OSError:
            pass
        return EXIT_IO_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
