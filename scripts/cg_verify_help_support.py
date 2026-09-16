#!/usr/bin/env python3
"""Read-only help support gate: validate evidence plus the current strict catalog.

Example: python scripts/cg_verify_help_support.py --evidence path/to/support.json
Exit 0 means verified; exit 2 means invalid/missing/stale evidence or catalog.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

import secure_fs
from help import catalog, support


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Verify source-bound evidence without writing or inferring runtime status.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code 0 when evidence and catalog verify; exit 2 otherwise.

    Raises:
        SystemExit: When invoked as ``__main__`` after this function returns.

    Example:
        ``raise SystemExit(main(["--evidence", "support.json"]))``
        verifies one evidence artifact and the current strict catalog.
    """
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--evidence",
        help=(
            "Required path to the review support-evidence JSON artifact "
            "(e.g. .cg-docs/work-reports/<date>-<command>-support.json). "
            "There is no usable default: a fixed default would silently point "
            "at a stale or absent artifact."
        ),
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.evidence is None:
        sys.stderr.write(
            "--evidence is required; pass the review support-evidence JSON "
            "artifact (e.g. --evidence .cg-docs/work-reports/<artifact>-support.json)\n"
        )
        return 2
    try:
        catalog._validate_relative_path(args.evidence, "support evidence")
        raw = secure_fs.secure_read_bytes(root, args.evidence, reject_hardlinks=True, max_bytes=catalog.MAX_JSON_BYTES)
        value = catalog.load_strict_json_bytes(raw, source=args.evidence)
        support.verify_evidence(root, value)
        catalog.check_catalog(root)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            catalog.HelpCatalogStaleError) as error:
        sys.stderr.write("Help support verification failed: {}\n".format(error))
        return 2
    sys.stdout.write("Help support evidence is current; runtime claims are limited to verified rows.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
