"""Created 2026-08-12. Journaled, locked, revisioned YAML transactions."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Optional
import uuid

import yaml

from .filesystem import ExpectedFileState, secure_read_bytes, secure_write_bytes
from .schemas import canonical_yaml


class RevisionConflictError(RuntimeError):
    """Signal that a writer's expected aggregate revision is stale.

    Args:
        expected: Revision supplied by the caller.
        actual: Revision observed under the lock.
        conflict_path: Durable conflict record path.

    Returns:
        An exception carrying deterministic conflict metadata.

    Example:
        ``raise RevisionConflictError(0, 1, Path("conflict.yaml"))``.
    """

    def __init__(self, expected: int, actual: int, conflict_path: Path) -> None:
        super().__init__(f"expected revision {expected}, actual revision {actual}")
        self.expected = expected
        self.actual = actual
        self.conflict_path = conflict_path


class SimulatedCrash(RuntimeError):
    """Represent an injected interruption that leaves journal state for recovery.

    Args:
        failure_at: Journal boundary where the interruption occurred.

    Returns:
        An exception that test fixtures can use to exercise recovery.

    Example:
        ``raise SimulatedCrash("after_prepare")`` models process termination.
    """

    def __init__(self, failure_at: str) -> None:
        super().__init__(f"simulated crash at {failure_at}")
        self.failure_at = failure_at


@dataclass(frozen=True)
class TransactionResult:
    """Summarize one committed canonical transaction.

    Args:
        operation_id: Unique transaction operation ID.
        revision: Aggregate revision after commit.
        affected_files: Canonical files replaced by the operation.

    Returns:
        An immutable commit result.

    Example:
        ``TransactionResult("op1", 1, ["records.yaml"])``.
    """

    operation_id: str
    revision: int
    affected_files: list[str]


@dataclass(frozen=True)
class RecoveryResult:
    """Summarize one recovered prepared transaction.

    Args:
        operation_id: Recovered operation ID.
        status: ``committed`` or ``aborted`` recovery outcome.
        reason: Stable recovery reason.

    Returns:
        An immutable recovery result.

    Example:
        ``RecoveryResult("op1", "aborted", "partial replacement")``.
    """

    operation_id: str
    status: str
    reason: str


class ArtifactStore:
    """Coordinate canonical YAML state below one project evidence directory.

    Args:
        root: Evidence root that may be created below the project.

    Returns:
        A store with journal and staging subdirectories.

    Example:
        ``store = ArtifactStore(Path(".cg-docs/research/evidence"))``.
    """

    def __init__(self, root: Path) -> None:
        """Create the evidence root and its journal directories.

        Args:
            root: Canonical evidence directory.

        Returns:
            ``None``; the store is ready for transactions.

        Example:
            ``ArtifactStore(tmp_path / "evidence")`` prepares a test store.
        """
        self.root = Path(root)
        if self.root.exists() and self.root.is_symlink():
            raise ValueError("Evidence root cannot be a symbolic link.")
        self.root.mkdir(parents=True, exist_ok=True)
        self.journal_root = self.root / "runs" / "journal"
        self.journal_root.mkdir(parents=True, exist_ok=True)
        self.staging_root = self.journal_root / "staging"
        self.staging_root.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.journal_root / ".lock"
        self._revision_path = self.root / ".revision"

    def current_revision(self) -> int:
        """Read the current aggregate revision, defaulting to zero.

        Args:
            None.

        Returns:
            Non-negative aggregate revision.

        Raises:
            ValueError: If the revision file is malformed.

        Example:
            ``store.current_revision()`` returns ``0`` for a new store.
        """
        if not self._revision_path.exists():
            return 0
        try:
            value = int(self._revision_path.read_text(encoding="ascii").strip())
        except (OSError, ValueError) as error:
            raise ValueError("Canonical aggregate revision is malformed.") from error
        if value < 0:
            raise ValueError("Canonical aggregate revision cannot be negative.")
        return value

    def transaction(
        self,
        *,
        expected_revision: Optional[int],
        actor: str,
        action: str,
    ) -> "ArtifactTransaction":
        """Create a locked transaction with an optimistic revision expectation.

        Args:
            expected_revision: Revision the caller read, or ``None`` to accept current.
            actor: Local actor label recorded in the journal.
            action: State-changing action recorded in the journal.

        Returns:
            A transaction context manager.

        Example:
            ``store.transaction(expected_revision=0, actor="user", action="write")``.
        """
        if expected_revision is not None and expected_revision < 0:
            raise ValueError("Expected revision cannot be negative.")
        if not actor or not action:
            raise ValueError("Transaction actor and action are required.")
        return ArtifactTransaction(self, expected_revision, actor, action)

    def recover(self) -> list[RecoveryResult]:
        """Recover prepared operations that lack commit or abort markers.

        Args:
            None.

        Returns:
            Recovery outcomes in deterministic journal filename order.

        Example:
            ``store.recover()`` completes or aborts interrupted operations.
        """
        results: list[RecoveryResult] = []
        with self._exclusive_lock():
            for prepare_path in sorted(self.journal_root.glob("*-prepare.yaml")):
                operation_id = prepare_path.name.removesuffix("-prepare.yaml")
                if (self.journal_root / f"{operation_id}-commit.yaml").exists():
                    continue
                if (self.journal_root / f"{operation_id}-abort.yaml").exists():
                    continue
                prepare = yaml.safe_load(prepare_path.read_text(encoding="utf-8"))
                if not isinstance(prepare, dict):
                    raise ValueError(f"Malformed prepare journal: {prepare_path}")
                new_hashes = prepare.get("new_hashes", {})
                all_replaced = all(
                    self._hash_if_exists(self.root / relative) == digest
                    for relative, digest in new_hashes.items()
                )
                if all_replaced:
                    expected = int(prepare["actual_revision"])
                    if self.current_revision() == expected:
                        self._write_revision(expected + 1)
                    self._write_derived_state(prepare.get("derived_stale", []))
                    self._write_marker(
                        operation_id,
                        "commit",
                        {**prepare, "recovered": True, "revision": expected + 1},
                    )
                    self._remove_staging(operation_id)
                    results.append(RecoveryResult(operation_id, "committed", "replacement-complete"))
                else:
                    self._restore_prepared(prepare)
                    self._write_marker(
                        operation_id,
                        "abort",
                        {**prepare, "recovered": True, "reason": "replacement-incomplete"},
                    )
                    self._remove_staging(operation_id)
                    results.append(RecoveryResult(operation_id, "aborted", "replacement-incomplete"))
        return results

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        """Hold the project evidence lock across one mutation or recovery."""
        with self._lock_path.open("a+", encoding="ascii") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _write_atomic(self, path: Path, content: bytes) -> None:
        """Write bytes through the repository's handle-relative secure writer."""
        relative = path.relative_to(self.root).as_posix()
        if path.exists():
            expected_state = ExpectedFileState.from_bytes(
                secure_read_bytes(self.root, relative)
            )
        else:
            expected_state = ExpectedFileState.absent()
        secure_write_bytes(
            self.root,
            Path(relative),
            content,
            expected_state=expected_state,
        )

    def _write_revision(self, revision: int) -> None:
        """Persist a validated aggregate revision atomically."""
        self._write_atomic(self._revision_path, str(revision).encode("ascii"))

    def _write_marker(self, operation_id: str, phase: str, payload: dict[str, Any]) -> None:
        """Persist a journal marker atomically."""
        marker_path = self.journal_root / f"{operation_id}-{phase}.yaml"
        self._write_atomic(marker_path, canonical_yaml(payload).encode("utf-8"))

    def _write_derived_state(self, stale_items: list[dict[str, str]]) -> None:
        """Record whether derived indexes require a rebuild."""
        state = {
            "schema_version": "research-evidence-derived-state-v1",
            "status": "stale" if stale_items else "current",
            "items": stale_items,
        }
        self._write_atomic(
            self.root / "derived-state.yaml",
            canonical_yaml(state).encode("utf-8"),
        )

    def _hash_if_exists(self, path: Path) -> Optional[str]:
        """Hash a regular file or return ``None`` when absent."""
        if not path.exists():
            return None
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Canonical target is not a regular file: {path}")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _record_conflict(self, expected: int, actual: int, actor: str, action: str) -> Path:
        """Write a deterministic optimistic-concurrency conflict record."""
        seed = f"{expected}\x1f{actual}\x1f{actor}\x1f{action}"
        conflict_id = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
        path = self.journal_root / f"conflict-{conflict_id}.yaml"
        payload = {
            "schema_version": "research-evidence-conflict-v1",
            "conflict_id": conflict_id,
            "expected_revision": expected,
            "actual_revision": actual,
            "actor": actor,
            "action": action,
        }
        self._write_atomic(path, canonical_yaml(payload).encode("utf-8"))
        return path

    def _remove_staging(self, operation_id: str) -> None:
        """Remove one completed operation's private staging tree."""
        staging = self.staging_root / operation_id
        if staging.exists():
            for path in sorted(staging.rglob("*"), reverse=True):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            staging.rmdir()

    def _restore_prepared(self, prepare: dict[str, Any]) -> None:
        """Restore only targets still matching staged bytes after a partial write."""
        operation_id = str(prepare["operation_id"])
        staging = self.staging_root / operation_id
        for relative, new_hash in prepare.get("new_hashes", {}).items():
            target = self.root / PurePosixPath(relative)
            if self._hash_if_exists(target) != new_hash:
                continue
            previous_hash = prepare.get("previous_hashes", {}).get(relative)
            backup_name = prepare.get("backup_paths", {}).get(relative)
            if previous_hash is None:
                if target.exists():
                    target.unlink()
                continue
            if not backup_name:
                raise ValueError(f"Missing backup for recoverable target: {relative}")
            backup = staging / backup_name
            self._write_atomic(target, backup.read_bytes())


class ArtifactTransaction:
    """Stage and commit a coordinated set of canonical YAML files.

    Args:
        store: Owning artifact store.
        expected_revision: Revision read by the caller.
        actor: Local actor label.
        action: State-changing action.

    Returns:
        A transaction context manager.

    Example:
        ``with store.transaction(expected_revision=0, actor="user", action="write") as tx:``.
    """

    def __init__(
        self,
        store: ArtifactStore,
        expected_revision: Optional[int],
        actor: str,
        action: str,
    ) -> None:
        """Initialize a transaction before lock acquisition.

        Args:
            store: Owning artifact store.
            expected_revision: Caller-observed revision.
            actor: Local actor label.
            action: State-changing action.

        Returns:
            ``None``; use the context manager to acquire the lock.

        Example:
            ``ArtifactTransaction(store, 0, "user", "write")``.
        """
        self.store = store
        self.expected_revision = expected_revision
        self.actor = actor
        self.action = action
        self.operation_id = uuid.uuid4().hex
        self.staging = self.store.staging_root / self.operation_id
        self._lock_context: Optional[Any] = None
        self._lock_entered = False
        self._staged: dict[str, dict[str, Any]] = {}
        self._derived_stale: list[dict[str, str]] = []
        self._committed = False
        self._aborted = False
        self.actual_revision: Optional[int] = None

    def __enter__(self) -> "ArtifactTransaction":
        """Acquire the evidence lock and validate the expected revision.

        Args:
            None.

        Returns:
            The active transaction.

        Raises:
            RevisionConflictError: If the caller's revision is stale.

        Example:
            ``with store.transaction(expected_revision=0, actor="u", action="a") as tx:``.
        """
        self._lock_context = self.store._exclusive_lock()
        self._lock_context.__enter__()
        self._lock_entered = True
        self.actual_revision = self.store.current_revision()
        if self.expected_revision is not None and self.expected_revision != self.actual_revision:
            conflict_path = self.store._record_conflict(
                self.expected_revision,
                self.actual_revision,
                self.actor,
                self.action,
            )
            self._release_lock()
            raise RevisionConflictError(self.expected_revision, self.actual_revision, conflict_path)
        self.staging.mkdir(parents=True, exist_ok=False)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Release the evidence lock without suppressing exceptions.

        Args:
            exc_type: Exception type supplied by the context protocol.
            exc: Exception instance supplied by the context protocol.
            traceback: Exception traceback supplied by the context protocol.

        Returns:
            ``None``; interrupted journal state remains for recovery.

        Example:
            Leaving the transaction context releases the process lock.
        """
        self._release_lock()
        return None

    def stage_yaml(self, relative_path: str, payload: Any) -> str:
        """Validate and stage one canonical YAML artifact.

        Args:
            relative_path: POSIX path below the evidence root.
            payload: YAML-compatible mapping/list or Pydantic model.

        Returns:
            SHA-256 digest of staged bytes.

        Raises:
            ValueError: If the path is unsafe, payload is malformed, or duplicate.

        Example:
            ``tx.stage_yaml("records.yaml", {"records": []})``.
        """
        self._ensure_active()
        normalized = self._normalize_relative_path(relative_path)
        if normalized in self._staged:
            raise ValueError(f"Artifact already staged: {normalized}")
        content = canonical_yaml(payload).encode("utf-8")
        yaml.safe_load(content.decode("utf-8"))
        staged_path = self.staging / normalized
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        self.store._write_atomic(staged_path, content)
        target = self.store.root / PurePosixPath(normalized)
        previous = target.read_bytes() if target.exists() else None
        backup_name: Optional[str] = None
        if previous is not None:
            backup_name = f"backup-{len(self._staged)}.bin"
            self.store._write_atomic(self.staging / backup_name, previous)
        digest = hashlib.sha256(content).hexdigest()
        self._staged[normalized] = {
            "new_hash": digest,
            "previous_hash": hashlib.sha256(previous).hexdigest() if previous else None,
            "backup_name": backup_name,
        }
        return digest

    def mark_derived_stale(self, relative_path: str, reason: str) -> None:
        """Record a derived artifact that must be rebuilt after canonical commit.

        Args:
            relative_path: Derived index or view path label.
            reason: Human-readable reason for invalidation.

        Returns:
            ``None``; stale state is persisted with the transaction.

        Example:
            ``tx.mark_derived_stale("lexical.sqlite", "source changed")``.
        """
        self._ensure_active()
        if not relative_path or not reason:
            raise ValueError("Derived stale path and reason are required.")
        self._derived_stale.append({"path": relative_path, "reason": reason})

    def abort(self) -> None:
        """Abort a staged transaction and write an abort marker.

        Args:
            None.

        Returns:
            ``None``; staged files are removed and no canonical file is replaced.

        Example:
            ``tx.abort()`` records an explicit user cancellation.
        """
        self._ensure_active()
        self.store._write_marker(
            self.operation_id,
            "abort",
            {"operation_id": self.operation_id, "actor": self.actor, "action": self.action},
        )
        self._aborted = True
        self.store._remove_staging(self.operation_id)

    def commit(self, failure_at: Optional[str] = None) -> TransactionResult:
        """Commit all staged YAML artifacts through journaled atomic replacement.

        Args:
            failure_at: Optional test boundary: ``after_prepare`` or ``after_replace``.

        Returns:
            Transaction result containing the new revision and affected files.

        Raises:
            SimulatedCrash: If an injected failure boundary is requested.
            ValueError: If nothing is staged or a boundary is invalid.

        Example:
            ``tx.commit()`` publishes one coordinated canonical revision.
        """
        self._ensure_active()
        if not self._staged:
            raise ValueError("Cannot commit a transaction with no staged artifacts.")
        if failure_at not in {None, "after_prepare", "after_replace"}:
            raise ValueError(f"Unknown transaction failure boundary: {failure_at}")
        assert self.actual_revision is not None
        affected = sorted(self._staged)
        previous_hashes = {path: data["previous_hash"] for path, data in self._staged.items()}
        new_hashes = {path: data["new_hash"] for path, data in self._staged.items()}
        payload_hash = hashlib.sha256(
            json.dumps(new_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        prepare = {
            "schema_version": "research-evidence-journal-v1",
            "operation_id": self.operation_id,
            "phase": "prepare",
            "expected_revision": self.expected_revision if self.expected_revision is not None else self.actual_revision,
            "actual_revision": self.actual_revision,
            "affected_files": affected,
            "previous_hashes": previous_hashes,
            "new_hashes": new_hashes,
            "backup_paths": {path: data["backup_name"] for path, data in self._staged.items() if data["backup_name"]},
            "payload_hash": payload_hash,
            "actor": self.actor,
            "action": self.action,
            "derived_stale": self._derived_stale,
        }
        self.store._write_marker(self.operation_id, "prepare", prepare)
        if failure_at == "after_prepare":
            raise SimulatedCrash("after_prepare")
        for relative in affected:
            staged_path = self.staging / relative
            staged_content = secure_read_bytes(
                self.store.root,
                (staged_path.relative_to(self.store.root)).as_posix(),
            )
            previous_hash = self._staged[relative]["previous_hash"]
            expected_state = (
                ExpectedFileState.absent()
                if previous_hash is None
                else ExpectedFileState(True, previous_hash)
            )
            secure_write_bytes(
                self.store.root,
                Path(relative),
                staged_content,
                expected_state=expected_state,
            )
        if failure_at == "after_replace":
            raise SimulatedCrash("after_replace")
        new_revision = self.actual_revision + 1
        self.store._write_revision(new_revision)
        self.store._write_derived_state(self._derived_stale)
        self.store._write_marker(
            self.operation_id,
            "commit",
            {**prepare, "phase": "commit", "revision": new_revision},
        )
        self.store._remove_staging(self.operation_id)
        self._committed = True
        return TransactionResult(self.operation_id, new_revision, affected)

    def _ensure_active(self) -> None:
        """Reject operations outside an entered, unfinished transaction."""
        if not self._lock_entered or self._committed or self._aborted:
            raise RuntimeError("Transaction is not active.")

    def _release_lock(self) -> None:
        """Release the held store lock once."""
        if self._lock_entered and self._lock_context is not None:
            self._lock_context.__exit__(None, None, None)
            self._lock_entered = False
            self._lock_context = None

    @staticmethod
    def _normalize_relative_path(relative_path: str) -> str:
        """Validate one POSIX canonical artifact path."""
        if not relative_path or "\\" in relative_path or "\x00" in relative_path:
            raise ValueError("Canonical artifact paths must be non-empty POSIX paths.")
        path = PurePosixPath(relative_path)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("Canonical artifact path cannot escape the evidence root.")
        if path.parts[0] == "runs":
            raise ValueError("Canonical artifacts cannot be staged inside runs/journal.")
        return path.as_posix()
