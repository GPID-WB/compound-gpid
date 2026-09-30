"""Dependency-free legacy/strict SemVer reader for Python 3.8 consumers."""

import re

NUMBER = r"(?:0|[1-9][0-9]*)"
IDENTIFIER = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER_TAG = re.compile(
    rf"v({NUMBER})\.({NUMBER})\.({NUMBER})"
    rf"(?:-({IDENTIFIER}(?:\.{IDENTIFIER})*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
LEGACY_TAG = re.compile(r"v([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)")


def version_key(tag: str) -> tuple:
    """Return precedence, ignoring build metadata; raise on invalid tags.

    Args: tag is an immutable GPID tag, e.g. ``v1.2.0-rc.10``.
    Returns: A numeric/ASCII tuple; legacy four-part tags use a separate lane.
    Raises: ValueError for unsupported syntax. Cross-lane migration needs policy.
    """
    legacy = LEGACY_TAG.fullmatch(tag)
    if legacy:
        return (*map(int, legacy.groups()[:3]), 0, ((0, int(legacy[4])),))
    match = SEMVER_TAG.fullmatch(tag)
    if not match:
        raise ValueError("Release tag is not supported: " + tag)
    suffix = match[4]
    parts = tuple(
        (0, int(part)) if part.isascii() and part.isdigit() else (1, part)
        for part in suffix.split(".")
    ) if suffix else ()
    return (*map(int, match.groups()[:3]), 1 if suffix else 2, parts)
