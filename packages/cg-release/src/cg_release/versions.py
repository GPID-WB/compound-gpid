"""Deterministic SemVer resolution over verified, adopted release-line history."""

import re
from collections.abc import Sequence

from semver import Version

from cg_release.events import ControllerError
from cg_release.models import ReleaseLine


def parse_version(value: str) -> Version:
    """Parse exact SemVer, e.g. ``parse_version('1.5.0-rc.10')``.

    Args:
        value: Unprefixed canonical version, not a tag or legacy version.
    Returns:
        Maintained-library version with metadata-insensitive comparison.
    Raises:
        ControllerError: Invalid, non-ASCII, or whitespace-bearing version.
    """
    try:
        if not isinstance(value, str) or len(value) > 255:
            raise ValueError
        parsed = Version.parse(value)
        if str(parsed) != value or not value.isascii():
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        raise ControllerError(
            "E_VERSION", "Expected exact SemVer without a tag prefix."
        ) from None


def resolve_version(
    history: Sequence[str],
    *,
    line: ReleaseLine,
    occupied: Sequence[str],
    bump: str | None = None,
    version: str | None = None,
    channel: str | None = None,
) -> str:
    """Resolve a proposal without reserving it, e.g. bump ``['1.4.2']`` by patch.

    Args:
        history: Verified adopted versions in the selected release line only.
        line: Named line and numeric core bounds.
        occupied: Global refs, drafts, and reservations, including other lines.
        bump: major/minor/patch/prerelease, exclusive with version.
        version: Explicit initial, transition, promotion, or next version.
        channel: One nonnumeric ASCII identifier for automatic bumps only.
    Returns:
        Canonical version string; input order cannot alter selection.
    Raises:
        ControllerError: Ambiguous baseline, invalid history, bounds, or collision.
    """
    if (bump is None) == (version is None) or (
        version is not None and channel is not None
    ):
        raise ControllerError(
            "E_ARGUMENT", "Select exactly one bump or explicit version."
        )
    if channel is not None and (
        not re.fullmatch(r"[A-Za-z0-9-]{1,64}", channel) or channel.isdigit()
    ):
        raise ControllerError(
            "E_ARGUMENT", "Channel must be one nonnumeric SemVer identifier."
        )
    adopted = [parse_version(item) for item in history]
    identities = [parse_version(item) for item in occupied]
    low, high = line.minimum_core, line.maximum_core_exclusive
    if any(type(n) is not int or n < 0 for n in low) or (
        high is not None
        and (any(type(n) is not int or n < 0 for n in high) or high <= low)
    ):
        raise ControllerError("E_POLICY", "Invalid release-line core bounds.")
    if any(
        not (low <= (v.major, v.minor, v.patch))
        or (high is not None and (v.major, v.minor, v.patch) >= high)
        for v in adopted
    ):
        raise ControllerError(
            "E_HISTORY", "Adopted history is outside its release line."
        )
    if version is not None:
        proposal = parse_version(version)
    elif bump == "prerelease":
        sequences: dict[tuple[int, int, int, str], int] = {}
        latest_stable = max((v for v in adopted if v.prerelease is None), default=None)
        for item in adopted:
            if item.prerelease is None or (
                latest_stable is not None and item <= latest_stable
            ):
                continue
            match = re.fullmatch(r"([A-Za-z0-9-]+)\.([1-9][0-9]*|0)", item.prerelease)
            if (
                match
                and not match[1].isdigit()
                and (channel is None or match[1] == channel)
            ):
                key = (item.major, item.minor, item.patch, match[1])
                sequences[key] = max(sequences.get(key, -1), int(match[2]))
        if len(sequences) != 1:
            raise ControllerError(
                "E_BASELINE",
                "An explicit core bump or version is required for this sequence.",
            )
        (major, minor, patch, selected), number = next(iter(sequences.items()))
        proposal = parse_version(f"{major}.{minor}.{patch}-{selected}.{number + 1}")
    elif bump in {"major", "minor", "patch"}:
        baseline = baseline_version(history, bump=bump)
        if baseline is None:
            raise ControllerError(
                "E_BASELINE",
                "No stable baseline; use an explicit initial version or bootstrap.",
            )
        proposal = getattr(baseline, f"bump_{bump}")().replace(build=None)
        if channel is not None:
            proposal = proposal.replace(prerelease=f"{channel}.1")
    else:
        raise ControllerError("E_ARGUMENT", "Unsupported bump type.")
    core = (proposal.major, proposal.minor, proposal.patch)
    if core < low or (high is not None and core >= high):
        raise ControllerError(
            "E_LINE_BOUNDS", "Proposed version is outside the selected line."
        )
    # Stable core bumps use the stable baseline, but cannot regress an adopted RC.
    relevant = baseline_version(history, version=str(proposal))
    if relevant is not None and proposal <= relevant:
        raise ControllerError(
            "E_PRECEDENCE",
            "Proposed version must increase the relevant adopted baseline.",
        )
    if proposal in adopted or proposal in identities:
        raise ControllerError(
            "E_COLLISION",
            "Version identity already exists; build metadata cannot distinguish it.",
        )
    return str(proposal)


def baseline_version(
    history: Sequence[str], *, version: str | None = None, bump: str | None = None
) -> Version | None:
    """Select the same baseline for version policy and notes, e.g. for a patch.

    Args:
        history: Adopted versions from exactly one selected release line.
        version: Resolved proposal for explicit promotion or RC continuation.
        bump: Base bumps use the highest stable baseline, ignoring future RCs.
    Returns:
        Relevant adopted version, or None for an explicit initial version.
    Raises:
        ControllerError: Invalid history or absent proposal for non-base selection.
    """
    adopted = [parse_version(item) for item in history]
    if bump in {"major", "minor", "patch"}:
        return max((v for v in adopted if v.prerelease is None), default=None)
    proposal = parse_version(version)
    core = (proposal.major, proposal.minor, proposal.patch)
    return max(
        (
            v
            for v in adopted
            if v.prerelease is None or (v.major, v.minor, v.patch) <= core
        ),
        default=None,
    )
