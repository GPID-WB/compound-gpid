#!/usr/bin/env python3
"""Generate the current host-neutral help support manifest."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Sequence

from help import catalog, support


OUTPUT_PATH = ".cg-docs/work-reports/docs-help-support-current.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default=OUTPUT_PATH)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.output != OUTPUT_PATH:
        raise SystemExit("output must be " + OUTPUT_PATH)
    output = root / OUTPUT_PATH
    if not output.parent.is_dir():
        raise SystemExit("support evidence directory is missing")
    subject = support._git(root, "rev-parse", "HEAD").decode().strip()
    catalog.check_catalog(root)
    evidence = support.build_evidence(root, subject)
    support.verify_evidence(root, evidence)
    content = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=".help-support-", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    print(OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
