"""Argv-only Git/gh process boundary with explicit cwd and finite timeouts."""

import math
import subprocess
import threading
import time
from collections.abc import Sequence
from pathlib import Path

from cg_release.events import AUTHORIZATION_FIELD, ControllerError, redact

MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_BINARY_BYTES = 64 * 1024 * 1024
# A journal update carries two base64-encoded copies of a <=64 KiB record
# (event and materialized state), plus bounded headers and reservation data.
MAX_INPUT_BYTES = 256 * 1024


def _capture(
    argv: list[str],
    *,
    cwd: Path,
    timeout: float,
    max_output_bytes: int,
    input_text: str | None = None,
    environment: dict[str, str] | None = None,
    binary_output: bool = False,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    """Capture each pipe within its byte limit and reap on overflow or timeout."""
    deadline = time.monotonic() + timeout
    overflow, read_error = threading.Event(), threading.Event()
    buffers = [bytearray(), bytearray()]
    child = subprocess.Popen(
        argv,
        cwd=str(cwd),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        **({"env": environment} if environment is not None else {}),
    )

    def kill() -> None:
        try:
            child.kill()
        except OSError:
            if child.poll() is None:
                read_error.set()

    def collect(pipe, buffer: bytearray) -> None:
        try:
            while True:
                # Read at most one byte beyond the remaining allowance. Never
                # append overflow bytes, and never queue unbounded reader output.
                chunk = pipe.read(min(65536, max_output_bytes - len(buffer) + 1))
                if not chunk:
                    return
                if len(buffer) + len(chunk) > max_output_bytes:
                    overflow.set()
                    kill()
                    return
                buffer.extend(chunk)
        except OSError:
            read_error.set()
            kill()

    pipes = [child.stdout, child.stderr]
    threads = [
        threading.Thread(target=collect, args=(pipe, buffer), daemon=True)
        for pipe, buffer in zip(pipes, buffers, strict=True)
    ]
    if input_text is not None:

        def send_input() -> None:
            try:
                pending = memoryview(input_text.encode("utf-8"))
                while pending:
                    written = child.stdin.write(pending)
                    if not written:
                        raise OSError("stdin did not accept bytes")
                    pending = pending[written:]
            except BrokenPipeError:
                pass
            except OSError:
                read_error.set()
                kill()
            finally:
                child.stdin.close()

        threads.append(threading.Thread(target=send_input, daemon=True))
    try:
        for thread in threads:
            thread.start()
        child.wait(timeout=max(0, deadline - time.monotonic()))
        for thread in threads:
            thread.join(max(0, deadline - time.monotonic()))
        if any(thread.is_alive() for thread in threads):
            raise subprocess.TimeoutExpired(argv[0], timeout)
        if overflow.is_set():
            raise ControllerError(
                "E_RESPONSE_SIZE", "Process output exceeds a stream byte limit."
            )
        if read_error.is_set():
            raise ControllerError(
                "E_PROCESS", "Process output could not be read safely."
            )
        return subprocess.CompletedProcess(
            argv,
            child.returncode,
            bytes(buffers[0]) if binary_output else buffers[0].decode("utf-8"),
            bytes(buffers[1]) if binary_output else buffers[1].decode("utf-8"),
        )
    finally:
        if child.poll() is None:
            kill()
        child.wait()
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=1)
        for pipe in pipes:
            pipe.close()


def run_process(
    tool: str,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float = 20,
    allow_failure: bool = False,
    input_text: str | None = None,
    environment: dict[str, str] | None = None,
    binary_output: bool = False,
    max_output_bytes: int = MAX_OUTPUT_BYTES,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    """Execute one Git/gh call; callers own read retries and write reconciliation.

    Args:
        tool: ``git``, ``gh``, or the isolated signing tools ``gpg``/``gpgconf``.
        args: Separated arguments, e.g. ``['status', '--porcelain']``.
        cwd: Explicit existing directory.
        timeout: Positive finite subprocess timeout in seconds.
        allow_failure: Return nonzero gh HTTP responses for typed read classification.
        input_text: Optional bounded public JSON/object input through stdin, not argv.
        environment: Optional complete child environment for isolated local Git.
        binary_output: Keep artifact bytes unchanged; never render them as logs.
        max_output_bytes: Explicit bounded stream capacity, at most 64 MiB.
    Returns:
        Successful completed process. Its output is data, not diagnostic text.
    Raises:
        ControllerError: Invalid input, missing tool, timeout, or process failure.
    """
    if (
        tool not in {"git", "gh", "gpg", "gpgconf"}
        or isinstance(args, (str, bytes))
        or not args
        or not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or not math.isfinite(timeout)
        or timeout <= 0
        or type(binary_output) is not bool
        or type(max_output_bytes) is not int
        or not 1 <= max_output_bytes <= MAX_BINARY_BYTES
    ):
        raise ControllerError("E_PROCESS_ARGUMENT", "Invalid process contract.")
    if any(
        not isinstance(arg, str)
        or "\x00" in arg
        or AUTHORIZATION_FIELD.search(arg)
        or redact(arg) != arg
        for arg in args
    ):
        raise ControllerError(
            "E_PROCESS_ARGUMENT", "Unsafe process arguments rejected."
        )
    if not isinstance(cwd, Path) or not cwd.is_dir():
        raise ControllerError(
            "E_PROCESS_ARGUMENT", "An existing working directory is required."
        )
    if input_text is not None and (
        not isinstance(input_text, str)
        or len(input_text.encode("utf-8")) > MAX_INPUT_BYTES
        or redact(input_text) != input_text
        or AUTHORIZATION_FIELD.search(input_text)
    ):
        raise ControllerError(
            "E_PROCESS_ARGUMENT", "Unsafe or oversized process input rejected."
        )
    try:
        result = _capture(
            [tool, *args],
            cwd=cwd,
            timeout=timeout,
            max_output_bytes=max_output_bytes,
            **({"input_text": input_text} if input_text is not None else {}),
            **({"environment": environment} if environment is not None else {}),
            **({"binary_output": True} if binary_output else {}),
        )
    except FileNotFoundError:
        raise ControllerError(
            "E_TOOL_MISSING", "Required Git or GitHub CLI is missing."
        ) from None
    except subprocess.TimeoutExpired:
        raise ControllerError(
            "E_TIMEOUT", "Process deadline exceeded; reconcile writes."
        ) from None
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise ControllerError(
            "E_PROCESS", "Process execution failed; inspect tool setup."
        ) from None
    if result.returncode and not allow_failure:
        raise ControllerError(
            "E_PROCESS", f"{tool} exited with code {result.returncode}."
        )
    return result
