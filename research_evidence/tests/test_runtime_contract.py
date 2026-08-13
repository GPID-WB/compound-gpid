"""Created 2026-08-12. Tests for the local-only runtime contract."""
from __future__ import annotations

import socket
from pathlib import Path
import subprocess
import sys

import pytest

from research_evidence.config import RuntimeSettings, ensure_supported_runtime
from research_evidence.errors import NetworkAccessDenied, PathPolicyError
from research_evidence.security import OfflineNetworkGuard, validate_subprocess_command


def test_supported_runtime_accepts_python_311() -> None:
    """Accept a Python version inside the package's supported range."""
    ensure_supported_runtime((3, 11, 0))


def test_runtime_rejects_python_314() -> None:
    """Reject a Python version outside the package's supported range."""
    with pytest.raises(RuntimeError, match="Python >=3.11 and <3.14"):
        ensure_supported_runtime((3, 14, 0))


def test_package_metadata_declares_supported_range_and_lockfile() -> None:
    """Require the dedicated project metadata and committed lockfile."""
    package_root = Path(__file__).parents[1]
    pyproject = (package_root / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.11,<3.14"' in pyproject
    assert (package_root / "uv.lock").is_file()


def test_cli_help_is_available() -> None:
    """Expose the documented local command names through the package CLI."""
    result = subprocess.run(
        [sys.executable, "-m", "research_evidence", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout
    assert "recover" in result.stdout


def test_settings_confine_resources_to_project(tmp_path: Path) -> None:
    """Allow a resource root inside the project and reject an escaping path."""
    resources = tmp_path / "resources"
    resources.mkdir()
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    assert settings.validate_resource_path(Path("notes.md")) == resources / "notes.md"

    with pytest.raises(PathPolicyError, match="inside the configured resources root"):
        settings.validate_resource_path(Path("../outside.md"))

    with pytest.raises(PathPolicyError, match="existing regular directory"):
        RuntimeSettings.from_paths(tmp_path, tmp_path / "missing")


def test_settings_reject_urls_and_remote_bind_hosts(tmp_path: Path) -> None:
    """Reject URL resources and non-loopback bind addresses."""
    resources = tmp_path / "resources"
    resources.mkdir()
    settings = RuntimeSettings.from_paths(tmp_path, resources)

    with pytest.raises(PathPolicyError, match="URL"):
        settings.validate_resource_path("https://example.org/paper.pdf")
    with pytest.raises(ValueError, match="loopback"):
        RuntimeSettings.from_paths(tmp_path, resources, bind_host="8.8.8.8")


def test_offline_model_settings_are_local_only(tmp_path: Path) -> None:
    """Expose model-loader settings that cannot trigger a download."""
    resources = tmp_path / "resources"
    resources.mkdir()
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    assert settings.model_loader_kwargs() == {"local_files_only": True}
    assert settings.offline is True


def test_network_guard_denies_remote_socket_and_allows_loopback() -> None:
    """Deny non-loopback socket connections while the guard is active."""
    with OfflineNetworkGuard():
        with pytest.raises(NetworkAccessDenied, match="outbound network"):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect(("203.0.113.1", 9))

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            with pytest.raises((ConnectionRefusedError, TimeoutError, OSError)):
                client.settimeout(0.01)
                client.connect(("127.0.0.1", 9))


def test_forbidden_subprocesses_are_rejected() -> None:
    """Reject shell, downloader, and package-manager subprocesses."""
    with pytest.raises(ValueError, match="forbidden"):
        validate_subprocess_command(["curl", "https://example.org"])
    with pytest.raises(ValueError, match="allowlist"):
        validate_subprocess_command(["tesseract", "input.png"])
    assert validate_subprocess_command(["/usr/bin/pdftotext", "input.pdf"], {"pdftotext"})
