"""Phase 2 pure version selection from validated, adopted line history.

Provider identity/adoption validation belongs to policy tests. These cases use
already selected line history; occupied identities cover all release lines.
"""

import json
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.models import ReleaseLine
from cg_release.versions import parse_version, resolve_version

FIXTURES = Path(__file__).parent / "fixtures"
LINE = ReleaseLine(
    id="current",
    branches=["main", "feature"],
    minimum_core=(1, 0, 0),
    maximum_core_exclusive=(3, 0, 0),
)


@pytest.mark.parametrize(
    "bump,channel,expected",
    [
        ("patch", None, "1.4.3"),
        ("minor", None, "1.5.0"),
        ("major", None, "2.0.0"),
        ("minor", "rc", "1.5.0-rc.1"),
    ],
)
def test_stable_bumps_use_highest_stable_baseline(
    bump: str, channel: str | None, expected: str
) -> None:
    """Input order does not change selection or promote an unrelated RC core."""
    history = ["1.4.2", "1.3.0", "1.4.3-rc.9"]
    for ordered in (history, list(reversed(history))):
        assert (
            resolve_version(ordered, line=LINE, bump=bump, channel=channel, occupied=[])
            == expected
        )


def test_shared_semver_corpus_at_controller_boundary() -> None:
    """Reject whitespace, leading zeroes, and legacy syntax without conversion."""
    corpus = json.loads((FIXTURES / "versions.json").read_text(encoding="utf-8"))
    for value in corpus["valid"]:
        assert str(parse_version(value)) == value
    for value in corpus["invalid"]:
        with pytest.raises(ControllerError):
            parse_version(value)
    ordered = [parse_version(value) for value in corpus["ascending"]]
    assert ordered == sorted(set(ordered))
    for left, right in corpus["equivalent"]:
        assert parse_version(left) == parse_version(right)
    with pytest.raises(ControllerError):
        parse_version("1.5.0.1")


def test_prerelease_sequence_compares_numeric_identifiers() -> None:
    """rc.10 follows rc.9, independent of tag time and lexical ordering."""
    assert (
        resolve_version(
            ["1.4.2", "1.5.0-rc.2", "1.5.0-rc.9"],
            line=LINE,
            bump="prerelease",
            channel="rc",
            occupied=[],
        )
        == "1.5.0-rc.10"
    )


@pytest.mark.parametrize(
    "history,channel",
    [
        (["1.4.2"], "rc"),
        (["1.5.0-rc.1", "1.6.0-rc.1"], "rc"),
        (["1.5.0-alpha.1", "1.5.0-rc.1"], None),
    ],
)
def test_unknown_or_ambiguous_sequence_requires_explicit_input(
    history: list[str], channel: str | None
) -> None:
    with pytest.raises(ControllerError):
        resolve_version(
            history, line=LINE, bump="prerelease", channel=channel, occupied=[]
        )


def test_initial_version_is_explicit_and_stable_promotion_is_explicit() -> None:
    assert resolve_version([], line=LINE, version="1.0.0", occupied=[]) == "1.0.0"
    with pytest.raises(ControllerError):
        resolve_version([], line=LINE, bump="patch", occupied=[])
    assert (
        resolve_version(
            ["1.4.2", "1.5.0-rc.10"], line=LINE, version="1.5.0", occupied=[]
        )
        == "1.5.0"
    )


@pytest.mark.parametrize("occupied", [["1.4.3"], ["1.4.3+other-build"]])
def test_global_collision_ignores_build_metadata(occupied: list[str]) -> None:
    """Drafts, refs, and reservations must supply global normalized identities."""
    with pytest.raises(ControllerError):
        resolve_version(
            ["1.4.2"], line=LINE, version="1.4.3+requested", occupied=occupied
        )


def test_newer_other_line_does_not_prohibit_maintenance_patch() -> None:
    assert (
        resolve_version(["1.4.2"], line=LINE, bump="patch", occupied=["2.1.0"])
        == "1.4.3"
    )


@pytest.mark.parametrize("version", ["0.9.9", "3.0.0", "1.4.2", "1.4.1"])
def test_manual_version_enforces_bounds_and_baseline(version: str) -> None:
    with pytest.raises(ControllerError):
        resolve_version(["1.4.2"], line=LINE, version=version, occupied=[])


@pytest.mark.parametrize("channel", ["", "123", "rc.1", "rc_1", "rc\n"])
def test_direct_api_rejects_invalid_channels(channel: str) -> None:
    with pytest.raises(ControllerError):
        resolve_version(
            ["1.4.2"], line=LINE, bump="minor", channel=channel, occupied=[]
        )


def test_direct_api_rejects_conflicting_selection_inputs() -> None:
    with pytest.raises(ControllerError):
        resolve_version(
            ["1.4.2"], line=LINE, bump="patch", version="1.4.3", occupied=[]
        )
    with pytest.raises(ControllerError):
        resolve_version(
            ["1.4.2"], line=LINE, version="1.4.3", channel="rc", occupied=[]
        )


def test_malformed_adopted_history_is_not_silently_ignored() -> None:
    with pytest.raises(ControllerError):
        resolve_version(["1.4.2", "broken"], line=LINE, bump="patch", occupied=[])
