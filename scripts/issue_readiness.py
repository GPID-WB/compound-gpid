#!/usr/bin/env python3
"""Execute the Compound GPID issue readiness validator (read-only)."""
from __future__ import annotations

from issues.readiness import main


if __name__ == "__main__":
    raise SystemExit(main())