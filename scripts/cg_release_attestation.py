#!/usr/bin/env python3
"""Create one deterministic reviewed post-release skill attestation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from skill_management.services import release_attestation  # noqa: E402
from skill_management import contracts  # noqa: E402
import secure_fs  # noqa: E402


def main(argv: Optional[List[str]] = None) -> int:
    """Build and securely publish one immutable release attestation."""
    parser = argparse.ArgumentParser(
        description="Create reviewed skill lifecycle evidence for one published release."
    )
    parser.add_argument("--root", default=".", help="Canonical repository root.")
    parser.add_argument("--tag", required=True, help="Exact published annotated tag.")
    parser.add_argument(
        "--check", action="store_true",
        help="Read-only verification of an existing byte-identical canonical attestation.",
    )
    parser.add_argument(
        "--review-reference",
        required=True,
        help="Immutable reviewed evidence reference containing a full commit SHA.",
    )
    arguments = parser.parse_args(argv)
    try:
        root = Path(arguments.root).resolve(strict=True)
        if arguments.check:
            value = release_attestation.build_release_attestation(
                root, arguments.tag, arguments.review_reference
            )
            relative = PurePosixPath(release_attestation.ATTESTATION_ROOT) / f"{arguments.tag}.json"
            existing = secure_fs.secure_read_bytes(
                root, relative, reject_hardlinks=True,
                max_bytes=contracts.MAX_CONTRACT_BYTES,
            )
            if existing != contracts.canonical_json_bytes(value) + b"\n":
                raise ValueError("Existing release attestation differs from canonical bytes")
            path = root / relative
        else:
            path = release_attestation.write_release_attestation(
                root, arguments.tag, arguments.review_reference
            )
    except (OSError, ValueError) as error:
        sys.stderr.write(f"ERROR: {error}\n")
        return 1
    sys.stdout.write(path.relative_to(Path(arguments.root).resolve()).as_posix() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
