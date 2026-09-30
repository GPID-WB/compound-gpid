#!/usr/bin/env python3
"""Generate the current host-neutral help support manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

import secure_fs
from help import catalog, support


OUTPUT_PATH = ".cg-docs/work-reports/docs-help-support-current.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default=OUTPUT_PATH)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Write the exact current source manifest to the single managed path."""
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.output != OUTPUT_PATH:
        raise SystemExit("output must be " + OUTPUT_PATH)
    if not root.joinpath(OUTPUT_PATH).parent.is_dir():
        raise SystemExit("support evidence directory is missing")
    subject = support._git(root, "rev-parse", "HEAD").decode().strip()
    catalog.check_catalog(root)
    evidence = support.build_evidence(root, subject)
    support.verify_evidence(root, evidence)
    content = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    secure_fs.secure_write_bytes(root, Path(OUTPUT_PATH), content)
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
