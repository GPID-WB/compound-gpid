"""Process and temp-file helpers shared by the dispatcher (leaf module)."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

from .contract import ApiError, ConfigError
from .gh_process import _default_run_gh

SOURCE_CREDENTIAL_ENVS = ("COPILOT_ASSIGN_TOKEN", "PROJECT_SYNC_TOKEN")


def _default_mutation_runner(
    args: list, token: str
) -> subprocess.CompletedProcess:
    """Run ``gh`` with a dedicated token via a clean environment.

    The child process receives only ``GH_TOKEN`` set to the supplied
    ``token``.  Both source credentials (``COPILOT_ASSIGN_TOKEN`` and
    ``PROJECT_SYNC_TOKEN``) are explicitly removed from the inherited
    environment so that a subprocess can never silently use a credential
    it was not given.

    This reuses the shared ``gh_process._default_run_gh`` subprocess
    boundaries (single timeout, classification of OSError/Timeout/Unicode)
    while injecting the credential as ``GH_TOKEN`` for the child process.

    Args:
        args: Argument list after the ``gh`` program name.
        token: The credential value used as ``GH_TOKEN``.

    Returns:
        The completed process result.

    Raises:
        ConfigError: When ``gh`` is not installed or cannot execute.
        ApiError: On timeout or undecodable output.
    """
    clean_env = {k: v for k, v in os.environ.items()
                 if k not in SOURCE_CREDENTIAL_ENVS}
    clean_env["GH_TOKEN"] = token
    return _default_run_gh(args, env=clean_env)


def _write_temp_file(text: str, suffix: str) -> Path:
    """Write request body text to a temporary file, mapping I/O errors.

    Args:
        text: Body content to write.
        suffix: File suffix such as ``".json"`` or ``".md"``.

    Returns:
        The created temp file path (must be unlinked by the caller).

    Raises:
        ApiError: When the temp file cannot be created or written (e.g., no
            space left, permission denied).
    """
    try:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=suffix, encoding="utf-8", delete=False
        )
        try:
            handle.write(text)
            return Path(handle.name)
        finally:
            handle.close()
    except OSError as error:
        raise ApiError(
            f"could not write GitHub request payload temp file: {error}"
        ) from error


def _unlink_best_effort(tmp: Path) -> None:
    """Remove a temp file without masking the primary error.

    Args:
        tmp: The temp file path to remove.
    """
    try:
        tmp.unlink(missing_ok=True)
    except OSError:
        pass
