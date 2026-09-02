"""Digest-bound planning, expected-byte publication, and forward recovery."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import secure_fs

from . import paths as path_policy
from .contracts import (
    ContractFinding,
    CONTRACTS_ROOT,
    EXIT_CONTRACT,
    EXIT_SUCCESS,
    canonical_json_bytes,
    load_contract,
    sort_findings,
    validate_instance,
)
from .locking import project_lifecycle_lock


PLAN_ROOT = PurePosixPath(".compound-gpid/skill-plans")
TRANSACTION_ROOT = PurePosixPath(".compound-gpid/skill-transactions")
JOURNAL_SCHEMA = "cg-skill-transaction-v1"
MAX_JOURNAL_BYTES = 128 * 1024 * 1024
_TRANSACTION_ID = re.compile(r"^[0-9a-f]{32}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_KEY = re.compile(
    r"(?:^|[-_])(authorization|credential|password|secret|token|api[-_]?key)(?:$|[-_])",
    re.IGNORECASE,
)
_PUBLISH_ORDER = {
    "source": 0,
    "provenance": 1,
    "registry": 2,
    "config": 3,
    "manifest": 4,
    "generated": 5,
    "projection": 6,
    "ownership": 7,
}


class PlanningError(ValueError):
    """Base plan/apply transaction error."""


class StalePlanError(PlanningError):
    """Raised when apply inputs no longer match the stored plan digest."""


class PlanReplayError(PlanningError):
    """Raised when a committed plan digest is applied again."""


class PlanRoleError(PlanningError):
    """Raised when apply uses a role different from the planned role."""


class ConcurrentMutationError(PlanningError):
    """Raised without overwrite when live bytes differ from both expected states."""


class JournalValidationError(PlanningError):
    """Raised when durable transaction state is malformed or unsafe."""


@dataclass(frozen=True)
class PlanBindings:
    """All common state digests bound into a lifecycle plan."""

    source_revision: str
    configuration_digest: str
    canonical_registry_digest: str
    project_registry_digest: str
    manifest_digest: str
    provenance_digest: str
    references_digest: str
    bundle_inventory_digest: str

    def to_dict(self) -> Dict[str, str]:
        """Return the common plan-contract binding representation."""
        return {
            "sourceRevision": self.source_revision,
            "configurationDigest": self.configuration_digest,
            "canonicalRegistryDigest": self.canonical_registry_digest,
            "projectRegistryDigest": self.project_registry_digest,
            "manifestDigest": self.manifest_digest,
            "provenanceDigest": self.provenance_digest,
            "referencesDigest": self.references_digest,
            "bundleInventoryDigest": self.bundle_inventory_digest,
        }

    @classmethod
    def fixture(cls) -> "PlanBindings":
        """Return deterministic valid bindings for focused transaction tests."""
        return cls("a" * 40, *("b" * 64 for _ in range(7)))


@dataclass(frozen=True)
class ExpectedMutation:
    """One project-relative exact old/new byte publication."""

    path: str
    before: Optional[bytes]
    after: Optional[bytes]
    publish_group: str
    executable: bool = False

    def __post_init__(self) -> None:
        secure_fs.normalize_relative_path(self.path)
        if self.publish_group not in _PUBLISH_ORDER:
            raise ValueError(f"Unknown lifecycle publish group: {self.publish_group}")
        if self.before == self.after:
            raise ValueError(f"Lifecycle mutation has no byte change: {self.path}")


@dataclass(frozen=True)
class InventoryCheck:
    """Exact regular-file inventory required below one managed bundle root."""

    root: str
    paths: Tuple[str, ...]

    def __post_init__(self) -> None:
        secure_fs.normalize_relative_path(self.root)
        for path in self.paths:
            secure_fs.normalize_relative_path(path)
            if PurePosixPath(path).parts[: len(PurePosixPath(self.root).parts)] != (
                PurePosixPath(self.root).parts
            ):
                raise ValueError(f"Inventory path is outside bundle root: {path}")


@dataclass(frozen=True)
class PlannedAction:
    """One public plan action and its optional internal expected-byte mutation."""

    kind: str
    path: str
    description: str
    mutation: Optional[ExpectedMutation] = None

    def to_public_dict(self) -> Dict[str, str]:
        """Return the reviewable action without embedding live or desired bytes."""
        result = {
            "kind": self.kind,
            "path": self.path,
            "description": self.description,
        }
        if self.mutation is not None:
            result["digest"] = _bytes_digest(self.mutation.after)
        return result


@dataclass(frozen=True)
class LifecyclePlan:
    """Complete deterministic operation plan supplied to common plan/apply."""

    operation: str
    role: str
    arguments: Mapping[str, Any]
    bindings: PlanBindings
    actions: Tuple[PlannedAction, ...]
    inventory_checks: Tuple[InventoryCheck, ...] = ()

    @property
    def digest(self) -> str:
        """Return a digest of raw normalized inputs and exact mutation states."""
        value = {
            "operation": self.operation,
            "role": self.role,
            "arguments": dict(self.arguments),
            "bindings": self.bindings.to_dict(),
            "actions": [
                {
                    "public": action.to_public_dict(),
                    "mutation": _mutation_identity(action.mutation),
                }
                for action in self.actions
            ],
            "inventoryChecks": [
                {"root": item.root, "paths": list(item.paths)}
                for item in self.inventory_checks
            ],
        }
        return plan_digest(value)


@dataclass(frozen=True)
class StoredPlan:
    """Stored common plan envelope and digest."""

    digest: str
    envelope: Mapping[str, Any]


@dataclass(frozen=True)
class TransactionResult:
    """Final durable transaction identity and state."""

    transaction_id: str
    plan_digest: str
    state: str


FaultHook = Optional[Callable[[str], None]]


@dataclass(frozen=True)
class OperationOutcome:
    """Handler output before the dispatcher adds the common result envelope."""

    changed: bool = False
    data: Mapping[str, Any] = field(default_factory=dict)
    actions: Tuple[Mapping[str, Any], ...] = ()
    findings: Tuple[ContractFinding, ...] = ()
    plan_digest: Optional[str] = None
    manifest_health: Optional[str] = None
    exit_code: Optional[int] = None


def plan_digest(bound_inputs: Mapping[str, Any]) -> str:
    """Return the SHA-256 digest of deterministic normalized plan inputs."""
    return hashlib.sha256(canonical_json_bytes(bound_inputs)).hexdigest()


def _bytes_digest(content: Optional[bytes]) -> str:
    marker = b"absent" if content is None else b"present\0" + content
    return hashlib.sha256(marker).hexdigest()


def _mutation_identity(mutation: Optional[ExpectedMutation]) -> Optional[Dict[str, Any]]:
    if mutation is None:
        return None
    return {
        "path": mutation.path,
        "before": _bytes_digest(mutation.before),
        "after": _bytes_digest(mutation.after),
        "publishGroup": mutation.publish_group,
        "executable": mutation.executable,
    }


def _redact(value: Any, key: str = "") -> Any:
    if key and _SENSITIVE_KEY.search(key):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(name): _redact(item, str(name)) for name, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _plan_envelope(plan: LifecyclePlan) -> Dict[str, Any]:
    return {
        "schema": "cg-skill-plan-v1",
        "digest": plan.digest,
        "operation": plan.operation,
        "phase": "plan",
        "role": plan.role,
        "projectRoot": ".",
        "sourceRoot": ".",
        "arguments": _redact(dict(plan.arguments)),
        "bindings": plan.bindings.to_dict(),
        "actions": [action.to_public_dict() for action in plan.actions],
        "findings": [],
    }


def _validate_plan_envelope(envelope: Mapping[str, Any]) -> None:
    schema = load_contract(
        Path(__file__).resolve().parents[2],
        CONTRACTS_ROOT / "plan-v1.schema.json",
    )
    findings = validate_instance(dict(envelope), schema)
    if findings:
        detail = "; ".join(
            f"{finding.path}: {finding.code}" for finding in findings
        )
        raise PlanningError(f"Lifecycle plan envelope is invalid: {detail}")


def _read_optional_bytes(project_root: Path, relative: str) -> Optional[bytes]:
    try:
        return secure_fs.secure_read_bytes(
            project_root,
            PurePosixPath(relative),
            reject_hardlinks=True,
            max_bytes=MAX_JOURNAL_BYTES,
        )
    except FileNotFoundError:
        return None


def store_plan(project_root: Path, plan: LifecyclePlan) -> StoredPlan:
    """Store one ignored deterministic and redacted plan record.

    Planning writes only this review record. Exact live and desired bytes remain
    in memory until apply creates a durable prepared transaction journal.
    """
    root = Path(project_root).resolve(strict=True)
    envelope = _plan_envelope(plan)
    _validate_plan_envelope(envelope)
    content = canonical_json_bytes(envelope) + b"\n"
    relative = PLAN_ROOT / f"{plan.digest}.json"
    existing = _read_optional_bytes(root, relative.as_posix())
    if existing is not None:
        if existing != content:
            raise PlanningError(
                f"Stored plan digest path has different bytes: {relative.as_posix()}"
            )
    else:
        secure_fs.secure_write_bytes(
            root,
            relative,
            content,
            expected_state=secure_fs.ExpectedFileState.absent(),
        )
    return StoredPlan(plan.digest, envelope)


def _load_stored_plan(project_root: Path, digest: str) -> Dict[str, Any]:
    if _DIGEST.fullmatch(digest) is None:
        raise StalePlanError("Apply requires one lowercase SHA-256 plan digest")
    relative = PLAN_ROOT / f"{digest}.json"
    try:
        content = secure_fs.secure_read_bytes(
            project_root,
            relative,
            reject_hardlinks=True,
            max_bytes=1024 * 1024,
        )
        envelope = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise StalePlanError(f"Stored plan is absent, unsafe, or invalid: {relative}") from error
    if not isinstance(envelope, dict):
        raise StalePlanError("Stored plan must be one JSON object")
    _validate_plan_envelope(envelope)
    if envelope.get("digest") != digest:
        raise StalePlanError("Stored plan digest disagrees with its path")
    return envelope


def _ordered_mutations(plan: LifecyclePlan) -> Tuple[ExpectedMutation, ...]:
    indexed = [
        (index, action.mutation)
        for index, action in enumerate(plan.actions)
        if action.mutation is not None
    ]
    ordered = sorted(
        indexed,
        key=lambda item: (
            _PUBLISH_ORDER[item[1].publish_group],
            item[0],
            item[1].path,
        ),
    )
    paths = set()
    mutations = []
    for _index, mutation in ordered:
        assert mutation is not None
        key = path_policy.portable_path_key(mutation.path)
        if key in paths:
            raise PlanningError(f"Lifecycle plan mutates one path more than once: {mutation.path}")
        paths.add(key)
        mutations.append(mutation)
    return tuple(mutations)


def _encode_bytes(content: Optional[bytes]) -> Optional[str]:
    return None if content is None else base64.b64encode(content).decode("ascii")


def _decode_bytes(value: Any, label: str) -> Optional[bytes]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise JournalValidationError(f"Journal {label} must be base64 or null")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeError, ValueError) as error:
        raise JournalValidationError(f"Journal {label} is not valid base64") from error


def _journal_bytes(journal: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(dict(journal)) + b"\n"


def _journal_relative(transaction_id: str) -> PurePosixPath:
    if _TRANSACTION_ID.fullmatch(transaction_id) is None:
        raise JournalValidationError("Transaction id must be 32 lowercase hex characters")
    return TRANSACTION_ROOT / f"{transaction_id}.json"


def _write_journal(
    project_root: Path,
    journal: Mapping[str, Any],
    expected: secure_fs.ExpectedFileState,
) -> bytes:
    transaction_id = str(journal.get("transactionId", ""))
    relative = _journal_relative(transaction_id)
    content = _journal_bytes(journal)
    if len(content) > MAX_JOURNAL_BYTES:
        raise JournalValidationError("Lifecycle journal exceeds its canonical byte ceiling")
    secure_fs.secure_write_bytes(
        project_root,
        relative,
        content,
        expected_state=expected,
    )
    return content


def _new_journal(plan: LifecyclePlan, transaction_id: str) -> Dict[str, Any]:
    actions = []
    for mutation in _ordered_mutations(plan):
        actions.append(
            {
                "path": mutation.path,
                "publishGroup": mutation.publish_group,
                "executable": mutation.executable,
                "oldBytes": _encode_bytes(mutation.before),
                "oldDigest": _bytes_digest(mutation.before),
                "newBytes": _encode_bytes(mutation.after),
                "newDigest": _bytes_digest(mutation.after),
                "status": "pending",
            }
        )
    return {
        "schema": JOURNAL_SCHEMA,
        "schemaVersion": 1,
        "transactionId": transaction_id,
        "requestDigest": hashlib.sha256(
            canonical_json_bytes(dict(plan.arguments))
        ).hexdigest(),
        "planDigest": plan.digest,
        "operation": plan.operation,
        "role": plan.role,
        "roots": {"project": "."},
        "state": "prepared",
        "recoveryState": "not-required",
        "actions": actions,
        "inventoryChecks": [
            {"root": item.root, "paths": list(item.paths)}
            for item in plan.inventory_checks
        ],
    }


def _staging_relative(transaction_id: str) -> PurePosixPath:
    if _TRANSACTION_ID.fullmatch(transaction_id) is None:
        raise JournalValidationError("Transaction id must be 32 lowercase hex characters")
    return TRANSACTION_ROOT / f"{transaction_id}.staging"


def _stage_expected_bytes(
    project_root: Path,
    journal: Mapping[str, Any],
) -> None:
    """Durably stage and re-read every desired file before ``prepared``."""
    staging = _staging_relative(str(journal["transactionId"]))
    if (project_root / staging).exists() or (project_root / staging).is_symlink():
        raise JournalValidationError("Lifecycle staging path already exists")
    for index, action in enumerate(journal["actions"]):
        desired = _decode_bytes(action.get("newBytes"), f"action {index} newBytes")
        if desired is None:
            continue
        relative = staging / f"{index:06d}.bin"
        secure_fs.secure_write_bytes(
            project_root,
            relative,
            desired,
            expected_state=secure_fs.ExpectedFileState.absent(),
        )
        staged = secure_fs.secure_read_bytes(
            project_root,
            relative,
            reject_hardlinks=True,
            max_bytes=MAX_JOURNAL_BYTES,
        )
        if staged != desired:
            raise JournalValidationError(
                f"Staged desired bytes failed exact validation for action {index}"
            )


def _remove_staging(project_root: Path, transaction_id: str) -> None:
    root = project_root / _staging_relative(transaction_id)
    try:
        metadata = os.lstat(str(root))
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & 0x400
    ) or not stat.S_ISDIR(metadata.st_mode):
        raise JournalValidationError("Lifecycle staging root changed into an unsafe object")

    def remove_directory(directory: Path) -> None:
        with os.scandir(str(directory)) as entries:
            ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        for entry in ordered:
            metadata = entry.stat(follow_symlinks=False)
            path = Path(entry.path)
            if stat.S_ISLNK(metadata.st_mode) or bool(
                getattr(metadata, "st_file_attributes", 0) & 0x400
            ):
                raise JournalValidationError("Lifecycle staging contains a link")
            if stat.S_ISDIR(metadata.st_mode):
                remove_directory(path)
                path.rmdir()
            elif stat.S_ISREG(metadata.st_mode):
                path.unlink()
            else:
                raise JournalValidationError("Lifecycle staging contains a non-regular entry")

    remove_directory(root)
    root.rmdir()


def _validate_journal(journal: Any, *, expected_id: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(journal, dict):
        raise JournalValidationError("Lifecycle journal must be one JSON object")
    required = {
        "schema",
        "schemaVersion",
        "transactionId",
        "requestDigest",
        "planDigest",
        "operation",
        "role",
        "roots",
        "state",
        "recoveryState",
        "actions",
        "inventoryChecks",
    }
    if set(journal) != required:
        raise JournalValidationError("Lifecycle journal has an invalid closed schema")
    transaction_id = journal.get("transactionId")
    if not isinstance(transaction_id, str) or _TRANSACTION_ID.fullmatch(transaction_id) is None:
        raise JournalValidationError("Lifecycle journal transactionId is invalid")
    if expected_id is not None and transaction_id != expected_id:
        raise JournalValidationError("Lifecycle journal identity disagrees with its path")
    if journal.get("schema") != JOURNAL_SCHEMA or journal.get("schemaVersion") != 1:
        raise JournalValidationError("Lifecycle journal schema is unsupported")
    for field_name in ("requestDigest", "planDigest"):
        value = journal.get(field_name)
        if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
            raise JournalValidationError(f"Lifecycle journal {field_name} is invalid")
    if journal.get("state") not in {
        "prepared",
        "publishing",
        "blocked",
        "committed",
        "aborted",
    }:
        raise JournalValidationError("Lifecycle journal state is invalid")
    if journal.get("roots") != {"project": "."}:
        raise JournalValidationError("Lifecycle journal root binding is invalid")
    actions = journal.get("actions")
    if not isinstance(actions, list):
        raise JournalValidationError("Lifecycle journal actions must be an array")
    seen = set()
    for index, action in enumerate(actions):
        if not isinstance(action, dict) or set(action) != {
            "path",
            "publishGroup",
            "executable",
            "oldBytes",
            "oldDigest",
            "newBytes",
            "newDigest",
            "status",
        }:
            raise JournalValidationError(f"Lifecycle journal action {index} is invalid")
        path = action.get("path")
        try:
            normalized = secure_fs.normalize_relative_path(path)
        except (TypeError, ValueError, OSError) as error:
            raise JournalValidationError(f"Lifecycle journal action {index} path is unsafe") from error
        key = path_policy.portable_path_key(normalized)
        if key in seen:
            raise JournalValidationError("Lifecycle journal has colliding action paths")
        seen.add(key)
        if action.get("publishGroup") not in _PUBLISH_ORDER:
            raise JournalValidationError("Lifecycle journal publish group is invalid")
        if type(action.get("executable")) is not bool:
            raise JournalValidationError("Lifecycle journal executable flag is invalid")
        old_bytes = _decode_bytes(action.get("oldBytes"), f"action {index} oldBytes")
        new_bytes = _decode_bytes(action.get("newBytes"), f"action {index} newBytes")
        if old_bytes == new_bytes:
            raise JournalValidationError("Lifecycle journal action has no byte change")
        if action.get("oldDigest") != _bytes_digest(old_bytes) or action.get(
            "newDigest"
        ) != _bytes_digest(new_bytes):
            raise JournalValidationError("Lifecycle journal expected-byte digest mismatch")
        if action.get("status") not in {"pending", "applied"}:
            raise JournalValidationError("Lifecycle journal action status is invalid")
    checks = journal.get("inventoryChecks")
    if not isinstance(checks, list):
        raise JournalValidationError("Lifecycle journal inventoryChecks must be an array")
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"root", "paths"}:
            raise JournalValidationError("Lifecycle journal inventory check is invalid")
        if not isinstance(check["paths"], list) or any(
            not isinstance(path, str) for path in check["paths"]
        ):
            raise JournalValidationError("Lifecycle journal inventory paths are invalid")
        InventoryCheck(str(check["root"]), tuple(check["paths"]))
    return journal


def _load_journal(project_root: Path, relative: PurePosixPath) -> Tuple[Dict[str, Any], bytes]:
    transaction_id = relative.stem
    try:
        content = secure_fs.secure_read_bytes(
            project_root,
            relative,
            reject_hardlinks=True,
            max_bytes=MAX_JOURNAL_BYTES,
        )
        journal = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise JournalValidationError(f"Lifecycle journal is unsafe or malformed: {relative}") from error
    return _validate_journal(journal, expected_id=transaction_id), content


def _journal_paths(project_root: Path) -> Tuple[PurePosixPath, ...]:
    directory = project_root / TRANSACTION_ROOT
    try:
        metadata = os.lstat(str(directory))
    except FileNotFoundError:
        return ()
    if stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & 0x400
    ) or not stat.S_ISDIR(metadata.st_mode):
        raise JournalValidationError("Lifecycle transaction root is unsafe")
    result = []
    with os.scandir(str(directory)) as entries:
        for entry in sorted(entries, key=lambda item: item.name):
            if not entry.name.endswith(".json"):
                continue
            metadata = entry.stat(follow_symlinks=False)
            if not stat.S_ISREG(metadata.st_mode):
                raise JournalValidationError("Lifecycle transaction journal is not regular")
            result.append(TRANSACTION_ROOT / entry.name)
    return tuple(result)


def _expected_state(content: Optional[bytes]) -> secure_fs.ExpectedFileState:
    return (
        secure_fs.ExpectedFileState.absent()
        if content is None
        else secure_fs.ExpectedFileState.from_bytes(content)
    )


def _apply_expected_action(project_root: Path, action: Mapping[str, Any]) -> None:
    path = str(action["path"])
    before = _decode_bytes(action.get("oldBytes"), f"{path} oldBytes")
    after = _decode_bytes(action.get("newBytes"), f"{path} newBytes")
    current = _read_optional_bytes(project_root, path)
    if action.get("status") == "applied":
        if current != after:
            raise ConcurrentMutationError(
                f"Previously applied path changed outside lifecycle recovery: {path}; "
                "restore the journaled new bytes, then rerun recovery"
            )
        return
    if current == after:
        return
    if current != before:
        raise ConcurrentMutationError(
            f"Expected-byte publication blocked by concurrent change at {path}; "
            "restore the journaled old or new bytes, then rerun recovery"
        )
    if after is None:
        assert before is not None
        secure_fs.secure_delete_verified(
            project_root,
            PurePosixPath(path),
            hashlib.sha256(before).hexdigest(),
        )
        return
    secure_fs.secure_write_bytes(
        project_root,
        PurePosixPath(path),
        after,
        executable=bool(action["executable"]),
        expected_state=_expected_state(before),
    )


def _inventory_regular_files(project_root: Path, relative_root: str) -> Tuple[str, ...]:
    root = project_root / Path(*PurePosixPath(relative_root).parts)
    try:
        metadata = os.lstat(str(root))
    except FileNotFoundError:
        return ()
    if stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & 0x400
    ) or not stat.S_ISDIR(metadata.st_mode):
        raise ConcurrentMutationError(f"Managed inventory root is unsafe: {relative_root}")
    result = []
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(str(directory)) as entries:
            ordered = sorted(entries, key=lambda item: item.name, reverse=True)
        for entry in ordered:
            metadata = entry.stat(follow_symlinks=False)
            path = Path(entry.path)
            relative = path.relative_to(project_root).as_posix()
            if stat.S_ISLNK(metadata.st_mode) or bool(
                getattr(metadata, "st_file_attributes", 0) & 0x400
            ):
                raise ConcurrentMutationError(f"Managed inventory contains a link: {relative}")
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                result.append(relative)
            else:
                raise ConcurrentMutationError(
                    f"Managed inventory contains a non-regular entry: {relative}"
                )
    return tuple(sorted(result))


def _verify_journal_state(project_root: Path, journal: Mapping[str, Any]) -> None:
    for action in journal["actions"]:
        expected = _decode_bytes(action.get("newBytes"), f"{action['path']} newBytes")
        actual = _read_optional_bytes(project_root, str(action["path"]))
        if actual != expected:
            raise ConcurrentMutationError(
                f"Committed desired bytes do not match at {action['path']}"
            )
    for check in journal["inventoryChecks"]:
        actual = _inventory_regular_files(project_root, str(check["root"]))
        expected = tuple(sorted(check["paths"]))
        if actual != expected:
            raise ConcurrentMutationError(
                f"Managed bundle inventory does not match desired state: {check['root']}"
            )


def _recover_one_locked(
    project_root: Path,
    relative: PurePosixPath,
    *,
    fault_hook: FaultHook = None,
) -> TransactionResult:
    journal, prior_bytes = _load_journal(project_root, relative)
    state = journal["state"]
    if state in {"committed", "aborted"}:
        return TransactionResult(
            str(journal["transactionId"]), str(journal["planDigest"]), state
        )
    if state == "prepared":
        _remove_staging(project_root, str(journal["transactionId"]))
        journal["state"] = "aborted"
        journal["recoveryState"] = "discarded-before-commit-point"
        _write_journal(
            project_root, journal, secure_fs.ExpectedFileState.from_bytes(prior_bytes)
        )
        return TransactionResult(
            str(journal["transactionId"]), str(journal["planDigest"]), "aborted"
        )

    journal["state"] = "publishing"
    journal["recoveryState"] = "forward"
    current_journal_bytes = _write_journal(
        project_root, journal, secure_fs.ExpectedFileState.from_bytes(prior_bytes)
    )
    for index, action in enumerate(journal["actions"]):
        try:
            _apply_expected_action(project_root, action)
        except ConcurrentMutationError:
            journal["state"] = "blocked"
            journal["recoveryState"] = f"blocked-action-{index}"
            _write_journal(
                project_root,
                journal,
                secure_fs.ExpectedFileState.from_bytes(current_journal_bytes),
            )
            raise
        if fault_hook is not None:
            fault_hook(f"after-action:{index}")
        action["status"] = "applied"
        current_journal_bytes = _write_journal(
            project_root,
            journal,
            secure_fs.ExpectedFileState.from_bytes(current_journal_bytes),
        )
        if fault_hook is not None:
            fault_hook(f"after-status:{index}")
    try:
        _verify_journal_state(project_root, journal)
    except ConcurrentMutationError:
        journal["state"] = "blocked"
        journal["recoveryState"] = "blocked-verification"
        _write_journal(
            project_root,
            journal,
            secure_fs.ExpectedFileState.from_bytes(current_journal_bytes),
        )
        raise
    journal["state"] = "committed"
    journal["recoveryState"] = "complete"
    _write_journal(
        project_root,
        journal,
        secure_fs.ExpectedFileState.from_bytes(current_journal_bytes),
    )
    _remove_staging(project_root, str(journal["transactionId"]))
    return TransactionResult(
        str(journal["transactionId"]), str(journal["planDigest"]), "committed"
    )


def _recover_all_locked(project_root: Path) -> Tuple[TransactionResult, ...]:
    results = []
    for relative in _journal_paths(project_root):
        journal, _content = _load_journal(project_root, relative)
        if journal["state"] in {"publishing", "blocked", "prepared"}:
            results.append(_recover_one_locked(project_root, relative))
    return tuple(results)


def _committed_plan_exists(project_root: Path, digest: str) -> bool:
    for relative in _journal_paths(project_root):
        journal, _content = _load_journal(project_root, relative)
        if journal["planDigest"] == digest and journal["state"] == "committed":
            return True
    return False


def apply_plan(
    project_root: Path,
    plan: LifecyclePlan,
    digest: str,
    *,
    lock_timeout: float = 30.0,
    fault_hook: FaultHook = None,
) -> TransactionResult:
    """Apply one recomputed exact plan through the common durable transaction."""
    root = Path(project_root).resolve(strict=True)
    with project_lifecycle_lock(root, timeout=lock_timeout):
        _recover_all_locked(root)
        stored = _load_stored_plan(root, digest)
        if stored.get("role") != plan.role:
            raise PlanRoleError("Apply role differs from the stored plan role")
        if plan.digest != digest:
            raise StalePlanError(
                "Apply inputs differ from the stored plan; create and review a new plan"
            )
        if stored != _plan_envelope(plan):
            raise StalePlanError(
                "Stored plan bytes differ from the recomputed review envelope"
            )
        if _committed_plan_exists(root, digest):
            raise PlanReplayError("A successfully committed plan cannot be replayed")
        transaction_id = uuid.uuid4().hex
        journal_relative = _journal_relative(transaction_id)
        if _read_optional_bytes(root, journal_relative.as_posix()) is not None:
            raise StalePlanError(
                "A noncommitted journal already exists for this plan; run recovery first"
            )
        journal = _new_journal(plan, transaction_id)
        try:
            _stage_expected_bytes(root, journal)
        except BaseException:
            _remove_staging(root, transaction_id)
            raise
        journal_bytes = _write_journal(
            root, journal, secure_fs.ExpectedFileState.absent()
        )
        if fault_hook is not None:
            fault_hook("after-prepared")
        journal["state"] = "publishing"
        journal["recoveryState"] = "not-required"
        _write_journal(
            root,
            journal,
            secure_fs.ExpectedFileState.from_bytes(journal_bytes),
        )
        if fault_hook is not None:
            fault_hook("after-publishing")
        return _recover_one_locked(root, journal_relative, fault_hook=fault_hook)


def recover_transactions(
    project_root: Path,
    *,
    lock_timeout: float = 30.0,
) -> Tuple[TransactionResult, ...]:
    """Recover every prepared/publishing journal under the held project lock."""
    root = Path(project_root).resolve(strict=True)
    with project_lifecycle_lock(root, timeout=lock_timeout):
        return _recover_all_locked(root)


def result_envelope(
    operation: str,
    phase: str,
    role: str,
    outcome: OperationOutcome,
) -> dict:
    """Build one deterministic common result envelope from a handler outcome."""
    findings = sort_findings(outcome.findings)
    has_error = any(item.severity == "error" for item in findings)
    exit_code = outcome.exit_code
    if exit_code is None or (has_error and exit_code == EXIT_SUCCESS):
        exit_code = EXIT_CONTRACT if has_error else EXIT_SUCCESS
    result = {
        "schema": "cg-skill-result-v1",
        "ok": exit_code == EXIT_SUCCESS,
        "exitCode": exit_code,
        "operation": operation,
        "phase": phase,
        "role": role,
        "changed": outcome.changed,
        "actions": [dict(action) for action in outcome.actions],
        "findings": [item.to_dict() for item in findings],
        "data": dict(outcome.data),
    }
    if outcome.plan_digest is not None:
        result["planDigest"] = outcome.plan_digest
    if outcome.manifest_health is not None:
        result["manifestHealth"] = outcome.manifest_health
    return result
