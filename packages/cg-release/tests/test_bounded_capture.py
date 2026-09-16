"""Small real producers prove streaming bounds before process completion."""

import subprocess
import sys
from pathlib import Path

import pytest

from cg_release import process
from cg_release.events import ControllerError


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_overflow_kills_and_reaps_live_producer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stream: str
) -> None:
    processes = []
    original = subprocess.Popen

    def spawn(*args: object, **kwargs: object):
        assert kwargs["shell"] is False and kwargs["bufsize"] == 0
        assert (
            kwargs["stdout"] == subprocess.PIPE and kwargs["stderr"] == subprocess.PIPE
        )
        assert kwargs["cwd"] == str(tmp_path)
        child = original(*args, **kwargs)
        processes.append(child)
        return child

    monkeypatch.setattr(process.subprocess, "Popen", spawn)
    code = (
        f"import sys,time; sys.{stream}.buffer.write(b'x'*2048); "
        f"sys.{stream}.flush(); time.sleep(30)"
    )
    with pytest.raises(ControllerError) as error:
        process._capture(
            [sys.executable, "-c", code], cwd=tmp_path, timeout=5, max_output_bytes=512
        )
    assert error.value.code == "E_RESPONSE_SIZE"
    assert len(processes) == 1 and processes[0].poll() is not None


def test_bounded_capture_retains_both_streams_and_nonzero_status(
    tmp_path: Path,
) -> None:
    code = "import sys; sys.stdout.write('out'); sys.stderr.write('err'); sys.exit(3)"
    result = process._capture(
        [sys.executable, "-c", code], cwd=tmp_path, timeout=5, max_output_bytes=512
    )
    assert (result.stdout, result.stderr, result.returncode) == ("out", "err", 3)


def test_timeout_reaps_producer_without_raw_error(tmp_path: Path) -> None:
    with pytest.raises(subprocess.TimeoutExpired):
        process._capture(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=tmp_path,
            timeout=0.1,
            max_output_bytes=512,
        )


def test_tree_size_rejects_blob_before_download() -> None:
    from cg_release.source_blobs import read_blobs

    class Tree:
        def get(self, endpoint: str) -> dict:
            assert endpoint == "git/trees/" + "a" * 40
            return {
                "sha": "a" * 40,
                "truncated": False,
                "tree": [
                    {
                        "path": "large.json",
                        "type": "blob",
                        "mode": "100644",
                        "sha": "b" * 40,
                        "size": 1048577,
                    }
                ],
            }

    with pytest.raises(ControllerError) as error:
        read_blobs(Tree(), "a" * 40, ["large.json"])
    assert error.value.code == "E_BLOB"
