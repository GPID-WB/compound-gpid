"""Deterministic change-manifest capture and verification.

Each present input file is acquired once within its per-file and the shared
aggregate budget; absent files are recorded as deletions, never invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Optional, Sequence, Tuple

import secure_fs
from autopilot.contracts import EvidenceError, sha256_hex
from autopilot.evidence import AcquisitionBudget, _normalize

MANIFEST_INPUT_LIMIT = 8 * 1024 * 1024
_GENERATED_HTML_PATTERN = ".cg-docs/views/**/*.html"


@dataclass(frozen=True)
class ManifestEntry:
    """One change-manifest input with its captured identity."""

    path: str
    sha256: Optional[str]
    byte_count: Optional[int]
    status: str


@dataclass(frozen=True)
class ChangeManifest:
    """Deterministic manifest over exact captured input bytes."""

    entries: Tuple[ManifestEntry, ...]
    excluded: Tuple[str, ...]
    digest: str


def resolve_exclusions(
    root: Path, declared: Iterable[str], *, own_report: str
) -> frozenset:
    """Resolve declared self-output exclusions to exact contained paths.

    Exact file paths (including declared control/test-output paths) and the
    operation's own report are allowed. The only pattern exemption is
    generated HTML bodies under ``.cg-docs/views/``. Directory-wide or
    arbitrary glob exemptions are rejected.
    """
    resolved: set[str] = set()
    for declaration in declared:
        if declaration == _GENERATED_HTML_PATTERN:
            views = root / ".cg-docs/views"
            if views.is_dir():
                for path in views.rglob("*.html"):
                    if path.is_file():
                        resolved.add(path.relative_to(root).as_posix())
            continue
        if any(character in declaration for character in "*?[") or declaration.endswith("/"):
            raise EvidenceError(
                f"directory-wide exemption {declaration!r} is not allowed; only "
                "exact file paths or generated HTML bodies under .cg-docs/views/ "
                "may be excluded."
            )
        resolved.add(_normalize(root, declaration, "exclusion"))
    if own_report:
        resolved.add(_normalize(root, own_report, "own-report"))
    return frozenset(resolved)


def capture_change_manifest(
    root: Path,
    paths: Sequence[str],
    *,
    budget: AcquisitionBudget,
    exclusions: Iterable[str] = (),
) -> ChangeManifest:
    """Capture a deterministic manifest over exact current input bytes."""
    excluded = frozenset(exclusions)
    entries: list[ManifestEntry] = []
    for raw_path in sorted(set(paths)):
        normalized = _normalize(root, raw_path, "manifest-input")
        if normalized in excluded:
            continue
        try:
            content = secure_fs.secure_read_bytes(
                root,
                PurePosixPath(normalized),
                max_bytes=MANIFEST_INPUT_LIMIT,
                reject_hardlinks=True,
            )
        except FileNotFoundError:
            entries.append(ManifestEntry(normalized, None, None, "deleted"))
            continue
        except secure_fs.SecureMutationError as error:
            raise EvidenceError(
                f"evidence-too-large: manifest acquisition failed: {error}"
            ) from error
        budget.spend(len(content))
        entries.append(
            ManifestEntry(normalized, sha256_hex(content), len(content), "present")
        )
    digest_lines = [
        f"{entry.status}:{entry.path}:{entry.sha256 or '-'}:{entry.byte_count or 0}"
        for entry in sorted(entries, key=lambda entry: entry.path)
    ]
    return ChangeManifest(
        entries=tuple(entries),
        excluded=tuple(sorted(excluded)),
        digest=sha256_hex("\n".join(digest_lines).encode("utf-8")),
    )


def verify_change_manifest(
    root: Path, manifest: ChangeManifest, *, budget: AcquisitionBudget
) -> Tuple[str, ...]:
    """Re-acquire manifest inputs and report every drifted path."""
    drifted: list[str] = []
    for entry in manifest.entries:
        try:
            content = secure_fs.secure_read_bytes(
                root,
                PurePosixPath(entry.path),
                max_bytes=MANIFEST_INPUT_LIMIT,
                reject_hardlinks=True,
            )
        except FileNotFoundError:
            if entry.status != "deleted":
                drifted.append(entry.path)
            continue
        except secure_fs.SecureMutationError as error:
            raise EvidenceError(f"manifest verification failed: {error}") from error
        budget.spend(len(content))
        if (
            entry.status != "present"
            or sha256_hex(content) != entry.sha256
            or len(content) != entry.byte_count
        ):
            drifted.append(entry.path)
    return tuple(drifted)
