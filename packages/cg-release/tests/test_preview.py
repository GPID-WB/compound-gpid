"""Immutable snapshot preview and confirmation are independent of admission."""

import json
from pathlib import Path

import pytest

from cg_release.cli import parse_args
from cg_release.events import ControllerError
from cg_release.metadata import SourceBlob
from cg_release.models import canonical_bytes
from cg_release.preview import Snapshot, confirmed_proposal, create_proposal


def snapshot(**changes: object) -> Snapshot:
    """Build a verified offline snapshot; remote acquisition is tested separately."""
    raw = (Path(__file__).parent / "fixtures/policy.json").read_bytes()
    data = dict(
        repository_id=123,
        host="github.com",
        slug="owner/repo",
        actor_id=7,
        role="write",
        default_branch="main",
        source_branch="main",
        source_sha="a" * 40,
        policy_sha="b" * 40,
        policy_raw=raw,
        history=[],
        occupied=[],
        blobs={
            "package.json": SourceBlob(b'{"version":"0.9.0"}'),
            "CHANGELOG.md": SourceBlob(b"<!-- release -->\n"),
        },
        notes="Initial release.",
    )
    data.update(changes)
    return Snapshot(**data)


def test_preview_is_deterministic_and_contains_all_confirmation_inputs() -> None:
    first = create_proposal(snapshot(), parse_args(["plan", "--version", "1.0.0"]))
    again = create_proposal(
        snapshot(), parse_args(["start", "--version", "1.0.0", "--yes"])
    )
    assert first.digest == again.digest
    assert first.version == "1.0.0" and first.tag == "v1.0.0"
    assert first.source_sha == "a" * 40 and first.policy_sha == "b" * 40
    assert first.approval_environment == "release-publish"
    assert len(first.edits) == 3


@pytest.mark.parametrize(
    "change",
    [
        {"source_sha": "c" * 40},
        {"role": "read"},
        {"occupied": ["1.0.0"]},
        {"policy_sha": "c" * 40},
        {"notes": "Changed notes."},
    ],
)
def test_confirmation_rechecks_without_silent_drift(change: dict) -> None:
    snapshots = iter([snapshot(), snapshot(**change)])
    args = parse_args(["start", "--version", "1.0.0", "--yes"])
    with pytest.raises(ControllerError):
        confirmed_proposal(args, lambda: next(snapshots), lambda _p: True)


def test_decline_does_not_recheck_or_submit() -> None:
    calls = []

    def acquire() -> Snapshot:
        calls.append(1)
        return snapshot()

    with pytest.raises(ControllerError) as error:
        confirmed_proposal(
            parse_args(["start", "--version", "1.0.0"]), acquire, lambda _p: False
        )
    assert error.value.code == "E_DECLINED" and calls == [1]


def test_missing_python_projection_history_is_not_inferred_from_source() -> None:
    state = snapshot()
    p = json.loads(state.policy_raw)
    p["metadata"] = [
        {"kind": "python-project", "path": "pyproject.toml", "pointer": None}
    ]
    p["bootstrap"] = [
        {
            "release_id": 1,
            "tag": "v1.0.0",
            "commit": "a" * 40,
            "line": "current",
            "version": "1.0.0",
            "legacy_version": None,
            "projections": {},
        }
    ]
    state = snapshot(
        policy_raw=canonical_bytes(p),
        history=p["bootstrap"],
        blobs={
            "pyproject.toml": SourceBlob(b'[project]\nversion="1.0.0"\n'),
            "CHANGELOG.md": SourceBlob(b"<!-- release -->\n"),
        },
    )
    with pytest.raises(ControllerError):
        create_proposal(state, parse_args(["plan", "--version", "1.1.0"]))
