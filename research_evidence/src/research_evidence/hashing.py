"""Created 2026-08-12. Content and filesystem identity helpers."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class FileIdentity:
    """Represent filesystem identity metadata used only for move explanations.

    Args:
        device: Operating-system device identifier.
        inode: Operating-system inode/file identifier.

    Returns:
        An immutable filesystem identity.

    Example:
        ``FileIdentity(device=1, inode=42)`` identifies one local file object.
    """

    device: int
    inode: int


def file_identity(path: Path) -> FileIdentity:
    """Read device/inode identity without treating metadata as content identity.

    Args:
        path: Existing regular file.

    Returns:
        Device/inode identity for move detection and audit explanation.

    Raises:
        OSError: If the file cannot be inspected.
        ValueError: If the path is not a regular non-link file.

    Example:
        ``file_identity(Path("resources/notes.md"))``.
    """
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"Resource must be a regular non-link file: {candidate}")
    metadata = candidate.stat()
    return FileIdentity(device=metadata.st_dev, inode=metadata.st_ino)


def sha256_file(path: Path) -> str:
    """Compute a streaming lowercase SHA-256 digest for one local file.

    Args:
        path: Existing regular file to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the path is not a regular non-link file.

    Example:
        ``sha256_file(Path("resources/notes.md"))`` returns a 64-character digest.
    """
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"Resource must be a regular non-link file: {candidate}")
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
