"""Require a non-skipped secure publication backend test result."""
from __future__ import annotations

import sys
from pathlib import Path
import xml.etree.ElementTree as ElementTree


def main(arguments: list[str]) -> int:
    """Validate one JUnit report produced by a backend-specific pytest gate.

    Args:
        arguments: Report path followed by the backend marker name.

    Returns:
        ``0`` when at least one test ran and none were skipped; otherwise ``1``.

    Example:
        ``main(["publisher-backend-results.xml", "backend_posix"])``.
    """
    if len(arguments) != 2:
        print("usage: assert_backend_race_gate.py REPORT.xml MARKER", file=sys.stderr)
        return 2
    report_path = Path(arguments[0])
    marker = arguments[1]
    if not report_path.is_file():
        print(f"Backend gate report was not created: {report_path}", file=sys.stderr)
        return 1
    try:
        root = ElementTree.parse(report_path).getroot()
    except ElementTree.ParseError as error:
        print(f"Backend gate report is malformed: {error}", file=sys.stderr)
        return 1
    testcases = list(root.iter("testcase"))
    skipped = [case for case in testcases if case.find("skipped") is not None]
    if not testcases:
        print(f"No tests were collected for {marker}.", file=sys.stderr)
        return 1
    if skipped:
        print(f"Applicable {marker} backend tests were skipped.", file=sys.stderr)
        return 1
    print(f"{len(testcases)} {marker} backend tests ran without skips.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))