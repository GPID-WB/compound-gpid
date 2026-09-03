"""Created 2026-08-12. Adapter for the repository's secure filesystem layer."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any


def _load_shared_secure_fs() -> ModuleType:
    """Load the repository-owned secure filesystem implementation by relative path."""
    repository_root = Path(__file__).resolve().parents[3]
    source_path = repository_root / "scripts" / "secure_fs.py"
    if not source_path.is_file():
        raise RuntimeError(
            "The repository secure filesystem layer is unavailable; "
            "canonical evidence writes are blocked."
        )
    spec = spec_from_file_location("compound_gpid_secure_fs", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the repository secure filesystem layer.")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_shared = _load_shared_secure_fs()
ExpectedFileState: Any = _shared.ExpectedFileState
SecureMutationError: Any = _shared.SecureMutationError
supports_secure_dir_fd: Any = _shared.supports_secure_dir_fd
secure_read_bytes: Any = _shared.secure_read_bytes
secure_write_bytes: Any = _shared.secure_write_bytes
open_relative_parent: Any = _shared.open_relative_parent
validate_path_components: Any = _shared.validate_path_components
