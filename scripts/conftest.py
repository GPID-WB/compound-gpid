"""Shared pytest configuration for tests under ``scripts/``.

Inserts the scripts/ directory into sys.path so that ``from brain import ...``
resolves correctly when pytest is invoked from the repo root:

    python -m pytest scripts/brain/tests/ -v
"""
import errno
import sys
from pathlib import Path

import pytest

# scripts/ directory — parent of this conftest.py
_SCRIPTS_DIR = str(Path(__file__).parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Establish the dispatcher's captured core before test collection imports any
# skill-management helper through Python's normal importer.
import cg_skill  # noqa: E402,F401


@pytest.fixture
def require_symlink_support(tmp_path: Path) -> None:
    """Skip a test when the host cannot create file and directory symlinks."""
    target_file = tmp_path / "symlink-capability-file"
    target_directory = tmp_path / "symlink-capability-directory"
    file_link = tmp_path / "symlink-capability-file-link"
    directory_link = tmp_path / "symlink-capability-directory-link"
    target_file.write_text("probe", encoding="utf-8")
    target_directory.mkdir()
    try:
        file_link.symlink_to(target_file)
        directory_link.symlink_to(target_directory, target_is_directory=True)
    except OSError as error:
        if error.errno in {errno.EACCES, errno.EPERM, errno.ENOSYS} or getattr(
            error, "winerror", None
        ) == 1314:
            pytest.skip("host does not permit symlink creation")
        raise
    finally:
        for link in (directory_link, file_link):
            if link.is_symlink():
                link.unlink()
