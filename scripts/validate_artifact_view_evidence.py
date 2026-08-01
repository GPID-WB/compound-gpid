#!/usr/bin/env python3
"""Validate the complete artifact-view design evidence matrix."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Optional, Sequence

from artifact_views.evidence import EvidenceValidationError, validate_evidence_file


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for evidence validation."""
    parser = argparse.ArgumentParser(
        description="Validate artifact-view design evidence and referenced files."
    )
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--require-all-pass", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Validate one evidence file and return a process exit code."""
    arguments = build_parser().parse_args(argv)
    try:
        result = validate_evidence_file(
            arguments.evidence,
            require_all_pass=arguments.require_all_pass,
        )
    except EvidenceValidationError as error:
        sys.stderr.write(f"Artifact-view evidence invalid: {error}\n")
        return 1
    sys.stdout.write(
        f"Artifact-view evidence passed: {result.artifact_count} artifacts, "
        f"{result.viewport_count} viewports.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
