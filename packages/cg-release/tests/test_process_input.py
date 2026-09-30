"""Bounded stdin for non-argv request bodies and local Git object plumbing."""

import hashlib
from pathlib import Path

import pytest

from cg_release.events import ControllerError
from cg_release.journal_transport import encode_files
from cg_release.models import MAX_RECORD_BYTES
from cg_release.process import MAX_INPUT_BYTES, run_process


def test_git_object_input_uses_stdin(tmp_path: Path) -> None:
    raw = "exact content\n"
    result = run_process(
        "git", ["hash-object", "--stdin"], cwd=tmp_path, input_text=raw
    )
    assert (
        result.stdout.strip()
        == hashlib.sha1(f"blob {len(raw)}\0{raw}".encode()).hexdigest()
    )


@pytest.mark.parametrize(
    "value",
    ["a" * (MAX_INPUT_BYTES + 1), "token=synthetic-credential"],
    ids=["oversized", "credential"],
)
def test_stdin_rejects_oversized_or_credential_shaped_input(
    tmp_path: Path, value: str
) -> None:
    with pytest.raises(ControllerError):
        run_process("git", ["hash-object", "--stdin"], cwd=tmp_path, input_text=value)


def test_maximum_journal_file_envelope_fits_real_process_input(tmp_path):
    payload = encode_files(
        "owner/repo",
        "release-controller-state",
        "a" * 40,
        {
            "events/0000000001.json": b"x" * MAX_RECORD_BYTES,
            "requests/" + "b" * 64 + ".json": b"x" * MAX_RECORD_BYTES,
            "reservations/" + "c" * 64 + ".json": b"x" * 8192,
        },
        "Release controller checkpoint",
    )
    assert 65536 < len(payload.encode()) <= MAX_INPUT_BYTES
    result = run_process(
        "git", ["hash-object", "--stdin"], cwd=tmp_path, input_text=payload
    )
    assert (
        result.stdout.strip()
        == hashlib.sha1(
            f"blob {len(payload.encode())}\0".encode() + payload.encode()
        ).hexdigest()
    )
