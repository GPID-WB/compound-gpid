"""Artifact download uses a bounded binary process response and exact API locator."""

import subprocess
import sys
from types import SimpleNamespace

import pytest

from cg_release.artifact_download import download_archive
from cg_release.events import ControllerError
from cg_release.process import _capture


def test_binary_capture_preserves_non_utf8_bytes(tmp_path):
    result = _capture(
        [
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(bytes([0,255,13,10]))",
        ],
        cwd=tmp_path,
        timeout=5,
        max_output_bytes=100,
        binary_output=True,
    )
    assert result.stdout == bytes([0, 255, 13, 10])


def test_download_uses_exact_registered_artifact_endpoint(tmp_path):
    calls = []

    def runner(tool, argv, **kwargs):
        calls.append((tool, argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, b"ZIP", b"")

    api = SimpleNamespace(
        host="github.com",
        slug="owner/repo",
        cwd=tmp_path,
        runner=runner,
        read_seconds=20,
        remaining=lambda: 5,
    )
    assert (
        download_archive(api, {"id": 42, "size_in_bytes": 3, "expired": False})
        == b"ZIP"
    )
    assert calls[0][1][-1] == "repos/owner/repo/actions/artifacts/42/zip"
    assert calls[0][2]["binary_output"] is True and calls[0][2]["max_output_bytes"] == 3


@pytest.mark.parametrize(
    "meta",
    [
        {"id": "42", "size_in_bytes": 3, "expired": False},
        {"id": 42, "size_in_bytes": 3, "expired": True},
    ],
)
def test_bad_artifact_locator_stops_before_download(meta):
    api = SimpleNamespace(runner=lambda *a, **k: pytest.fail("unsafe download"))
    with pytest.raises(ControllerError):
        download_archive(api, meta)
