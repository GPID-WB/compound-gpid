"""GPID launcher for the standalone CLI and explicit legacy bridge/recovery only.

Example: python scripts/cg_release_cli.py plan --version 1.5.0-rc.1 --json.
No installation, settings change, shell interpolation or version selection occurs.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def main(argv=None, *, run=None):
    """Dispatch exact argv to the installed core or an explicit legacy operation.

    Args: argv is a string sequence (None uses sys.argv[1:]); run is an optional
    outer process callable accepting an argv list and returning its integer status.
    Returns: the unchanged child exit code, or 2 if legacy PowerShell is unavailable.
    Raises: OSError if the selected process cannot start. No installation, version
    resolution, source edit or shell interpolation occurs here. The child owns all
    plan/start/status/resume effects. Legacy children retain remote authority checks.
    Example: main(['plan', '--version', '1.5.0-rc.1', '--json']). A repository-local
    package venv wins; otherwise sys.executable runs the installed module with -I.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    run = run or (lambda command: subprocess.call(command, shell=False))
    if args and args[0] in {"--legacy-bridge", "--legacy-recovery"}:
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell is None:
            sys.stderr.write(
                "Legacy GPID recovery requires PowerShell; the standalone core does not.\n"
            )
            return 2
        operation = "Bridge" if args[0] == "--legacy-bridge" else "Recovery"
        return run(
            [
                shell,
                "-NoProfile",
                "-File",
                str(root / "create-release.ps1"),
                "-LegacyOperation",
                operation,
                *args[1:],
            ]
        )
    environment = root / "packages/cg-release/.venv"
    python = environment / (
        "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
    )
    interpreter = str(python) if python.is_file() else sys.executable
    return run([interpreter, "-I", "-m", "cg_release.cli", *args])


if __name__ == "__main__":
    raise SystemExit(main())
