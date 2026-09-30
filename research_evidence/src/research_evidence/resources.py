"""Created 2026-08-12. Deterministic local resource discovery and version events."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import hashlib
import os
from pathlib import Path
import stat
from typing import Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field

from .config import RuntimeSettings
from .errors import PathPolicyError
from .filesystem import secure_read_bytes

SUPPORTED_RESOURCE_EXTENSIONS = frozenset(
    {".pdf", ".docx", ".md", ".markdown", ".tex", ".latex", ".html", ".htm"}
)


class ResourceEventKind(str, Enum):
    """Classify one deterministic corpus discovery event.

    Args:
        value: Serialized event kind.

    Returns:
        A validated resource event kind.

    Example:
        ``ResourceEventKind.MOVED`` records an identity-preserving path move.
    """

    NEW = "new"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    MOVED = "moved"
    REMOVED = "removed"
    DUPLICATE_CONTENT = "duplicate-content"
    UNSUPPORTED = "unsupported"
    INACCESSIBLE = "inaccessible"


class ResourceObservation(BaseModel):
    """Record one supported local resource observation.

    Args:
        resource_id: Logical resource identifier used by downstream records.
        relative_path: Normalized POSIX path below the resources root.
        sha256: Content hash that determines source identity.
        size: Byte size captured as metadata.
        mtime_ns: Modification time captured for diagnostics only.
        device: Filesystem device identity used to explain moves.
        inode: Filesystem inode identity used to explain moves.
        suffix: Lowercase supported resource extension.

    Returns:
        A validated resource observation.

    Example:
        ``ResourceObservation(resource_id="r1", relative_path="notes.md", sha256="a" * 64, size=1, mtime_ns=0, device=1, inode=2, suffix=".md")``.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size: int = Field(ge=0)
    mtime_ns: int = Field(ge=0)
    device: int = Field(ge=0)
    inode: int = Field(gt=0)
    suffix: str = Field(pattern=r"^\.[a-z0-9]+$")


class ResourceSnapshot(BaseModel):
    """Store the prior corpus state used for deterministic comparisons.

    Args:
        resources: Supported resource observations from one scan.
        schema_version: Version of the snapshot contract.

    Returns:
        A validated snapshot suitable for YAML persistence.

    Example:
        ``ResourceSnapshot(resources=[observation])`` becomes the next scan baseline.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "research-evidence-resource-snapshot-v1"
    resources: list[ResourceObservation] = Field(default_factory=list)


class ResourceEvent(BaseModel):
    """Explain one resource lifecycle event without silently changing identity.

    Args:
        kind: Discovery event classification.
        relative_path: Current or removed normalized resource path.
        resource_id: Logical resource identity, when known.
        previous_path: Prior path for an unambiguous move.
        current_sha256: Current content hash, when available.
        previous_sha256: Prior content hash, when available.
        reason: Stable human-readable explanation.
        requires_review: Whether a researcher must resolve ambiguity.

    Returns:
        A validated lifecycle event.

    Example:
        ``ResourceEvent(kind="new", relative_path="notes.md", reason="not in prior snapshot")``.
    """

    model_config = ConfigDict(extra="forbid")

    kind: ResourceEventKind
    relative_path: str = Field(min_length=1)
    resource_id: Optional[str] = None
    previous_path: Optional[str] = None
    current_sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    previous_sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(min_length=1)
    requires_review: bool = False


@dataclass(frozen=True)
class DiscoveryResult:
    """Return current observations and deterministic events from one scan.

    Args:
        resources: Supported current observations.
        events: Ordered events describing changes and unsupported inputs.

    Returns:
        An immutable discovery result.

    Example:
        ``result.snapshot()`` supplies the baseline for the next scan.
    """

    resources: list[ResourceObservation]
    events: list[ResourceEvent]

    def snapshot(self) -> ResourceSnapshot:
        """Build a validated snapshot from the current observations.

        Args:
            None.

        Returns:
            Snapshot sorted by normalized relative path.

        Example:
            ``previous = result.snapshot()`` persists a scan baseline.
        """
        return ResourceSnapshot(resources=sorted(self.resources, key=lambda item: item.relative_path))


def _resource_id(relative_path: str) -> str:
    """Derive a stable new logical identity from a normalized path."""
    return "resource:" + hashlib.sha256(relative_path.encode("utf-8")).hexdigest()


def _iter_entries(root: Path) -> Iterable[Path]:
    """Walk a resource root without following any symbolic link."""
    directories = [root]
    while directories:
        directory = directories.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as error:
            raise PathPolicyError(f"Resources directory is inaccessible: {directory}") from error
        for entry in entries:
            path = Path(entry.path)
            if entry.is_symlink():
                resolved = path.resolve(strict=False)
                if not resolved.is_relative_to(root):
                    raise PathPolicyError(
                        f"Resource symbolic link escapes the configured root: {path}"
                    )
                raise PathPolicyError(
                    f"Resource symbolic links are not authoritative inputs: {path}"
                )
            try:
                if entry.is_dir(follow_symlinks=False):
                    directories.append(path)
                elif entry.is_file(follow_symlinks=False):
                    yield path
            except OSError as error:
                raise PathPolicyError(f"Resource path is inaccessible: {path}") from error


def _observe_file(path: Path, root: Path) -> ResourceObservation:
    """Hash and record one supported regular file."""
    relative_path = path.relative_to(root).as_posix()
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise PathPolicyError(f"Resource must be a regular non-link file: {path}")
    content = secure_read_bytes(root, relative_path, reject_hardlinks=True)
    after = os.lstat(path)
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise PathPolicyError(f"Resource changed during observation: {path}")
    return ResourceObservation(
        resource_id=_resource_id(relative_path),
        relative_path=relative_path,
        sha256=hashlib.sha256(content).hexdigest(),
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        device=after.st_dev,
        inode=after.st_ino,
        suffix=path.suffix.lower(),
    )


def _event_priority(kind: ResourceEventKind) -> int:
    """Return deterministic display order for event categories."""
    return {
        ResourceEventKind.NEW: 1,
        ResourceEventKind.UNCHANGED: 2,
        ResourceEventKind.CHANGED: 3,
        ResourceEventKind.MOVED: 4,
        ResourceEventKind.DUPLICATE_CONTENT: 5,
        ResourceEventKind.REMOVED: 6,
        ResourceEventKind.UNSUPPORTED: 7,
        ResourceEventKind.INACCESSIBLE: 8,
    }[kind]


def discover_resources(
    settings: RuntimeSettings,
    previous: Optional[ResourceSnapshot] = None,
) -> DiscoveryResult:
    """Discover configured local resources and compare them with a prior snapshot.

    Args:
        settings: Validated project/resource-root settings.
        previous: Optional prior snapshot used for lifecycle comparison.

    Returns:
        Current supported observations and deterministic lifecycle events.

    Raises:
        PathPolicyError: If a resource path is inaccessible or symlinked.

    Example:
        ``discover_resources(settings, previous_snapshot)`` detects a moved file.
    """
    root = settings.resources_root
    prior_resources = list(previous.resources) if previous else []
    prior_by_path = {item.relative_path: item for item in prior_resources}
    prior_by_hash: dict[str, list[ResourceObservation]] = defaultdict(list)
    for item in prior_resources:
        prior_by_hash[item.sha256].append(item)

    observations: list[ResourceObservation] = []
    events: list[ResourceEvent] = []
    for path in _iter_entries(root):
        suffix = path.suffix.lower()
        relative_path = path.relative_to(root).as_posix()
        if suffix not in SUPPORTED_RESOURCE_EXTENSIONS:
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.UNSUPPORTED,
                    relative_path=relative_path,
                    reason=f"unsupported extension: {suffix or '<none>'}",
                    requires_review=False,
                )
            )
            continue
        try:
            observations.append(_observe_file(path, root))
        except OSError as error:
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.INACCESSIBLE,
                    relative_path=relative_path,
                    reason=f"resource could not be read: {error}",
                    requires_review=True,
                )
            )

    current_by_hash: dict[str, list[ResourceObservation]] = defaultdict(list)
    for observation_index, observation in enumerate(observations):
        current_by_hash[observation.sha256].append(observation)

    matched_previous_paths: set[str] = set()
    for observation in observations:
        prior = prior_by_path.get(observation.relative_path)
        if len(current_by_hash[observation.sha256]) > 1:
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.DUPLICATE_CONTENT,
                    relative_path=observation.relative_path,
                    resource_id=prior.resource_id if prior else observation.resource_id,
                    current_sha256=observation.sha256,
                    reason="multiple current resources have identical content",
                    requires_review=True,
                )
            )
            if prior:
                matched_previous_paths.add(prior.relative_path)
            continue
        if prior is not None:
            matched_previous_paths.add(prior.relative_path)
            if prior.sha256 == observation.sha256:
                observation = observation.model_copy(update={"resource_id": prior.resource_id})
                observations[observation_index] = observation
                events.append(
                    ResourceEvent(
                        kind=ResourceEventKind.UNCHANGED,
                        relative_path=observation.relative_path,
                        resource_id=prior.resource_id,
                        current_sha256=observation.sha256,
                        previous_sha256=prior.sha256,
                        reason="content hash unchanged; metadata ignored",
                    )
                )
            else:
                observation = observation.model_copy(update={"resource_id": prior.resource_id})
                observations[observation_index] = observation
                events.append(
                    ResourceEvent(
                        kind=ResourceEventKind.CHANGED,
                        relative_path=observation.relative_path,
                        resource_id=prior.resource_id,
                        current_sha256=observation.sha256,
                        previous_sha256=prior.sha256,
                        reason="content hash changed at the same path",
                        requires_review=True,
                    )
                )
            continue
        hash_matches = [
            candidate
            for candidate in prior_by_hash.get(observation.sha256, [])
            if candidate.relative_path not in matched_previous_paths
        ]
        if len(hash_matches) == 1:
            prior = hash_matches[0]
            matched_previous_paths.add(prior.relative_path)
            observation = observation.model_copy(update={"resource_id": prior.resource_id})
            observations[observation_index] = observation
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.MOVED,
                    relative_path=observation.relative_path,
                    previous_path=prior.relative_path,
                    resource_id=prior.resource_id,
                    current_sha256=observation.sha256,
                    previous_sha256=prior.sha256,
                    reason="one prior resource has the same content hash",
                )
            )
        elif len(hash_matches) > 1:
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.DUPLICATE_CONTENT,
                    relative_path=observation.relative_path,
                    resource_id=observation.resource_id,
                    current_sha256=observation.sha256,
                    reason="multiple prior resources match the content hash",
                    requires_review=True,
                )
            )
        else:
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.NEW,
                    relative_path=observation.relative_path,
                    resource_id=observation.resource_id,
                    current_sha256=observation.sha256,
                    reason="resource was not present in the prior snapshot",
                )
            )

    for prior in prior_resources:
        if prior.relative_path not in matched_previous_paths and not any(
            item.relative_path == prior.relative_path for item in observations
        ):
            events.append(
                ResourceEvent(
                    kind=ResourceEventKind.REMOVED,
                    relative_path=prior.relative_path,
                    resource_id=prior.resource_id,
                    previous_sha256=prior.sha256,
                    reason="resource is absent from the current scan",
                    requires_review=True,
                )
            )

    ordered_events = sorted(
        events,
        key=lambda event: (_event_priority(event.kind), event.relative_path),
    )
    return DiscoveryResult(
        resources=sorted(observations, key=lambda item: item.relative_path),
        events=ordered_events,
    )
