"""Bounded evidence acquisition, reference verification and frozen receipts.

Every document is acquired exactly once through the current secure-read API,
then parsed and hashed from those same bytes. Limits are per-kind and
aggregate; over-limit acquisition stops ``evidence-too-large`` and never
truncates, expands scope or falls back to pathname reads. Change-manifest
capture lives in ``manifest.py``, which imports the shared acquisition helpers
from this module.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional

import secure_fs
from secure_fs import ExpectedFileState
from autopilot.contracts import (
    EvidenceError,
    sha256_hex,
)
from autopilot.packets import ArtifactReference
from autopilot.plan import ValidatedPlan

PLAN_REPORT_LIMIT = 2 * 1024 * 1024
RECEIPT_LIMIT = 8 * 1024 * 1024
AGGREGATE_LIMIT = 128 * 1024 * 1024

_KIND_LIMITS = {
    "plan": PLAN_REPORT_LIMIT,
    "report": PLAN_REPORT_LIMIT,
    "receipt": RECEIPT_LIMIT,
    "manifest-input": 8 * 1024 * 1024,
}
_PARENT_IDENTITY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_OPERATION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,127}$")
_REPORT_TYPES = ("review", "verify-review")


class AcquisitionBudget:
    """Aggregate byte budget shared by one validation operation."""

    def __init__(self, limit: int = AGGREGATE_LIMIT) -> None:
        if not isinstance(limit, int) or limit < 1:
            raise EvidenceError("aggregate limit must be a positive integer.")
        self.limit = limit
        self.used = 0

    def spend(self, amount: int) -> None:
        if self.used + amount > self.limit:
            raise EvidenceError(
                f"aggregate evidence budget exceeded ({self.limit} bytes per "
                "validation operation)."
            )
        self.used += amount


@dataclass(frozen=True)
class AcquiredDocument:
    """Exact acquired bytes plus their identity; parse/hash the same bytes."""

    path: str
    kind: str
    byte_count: int
    sha256: str
    content: bytes


@dataclass(frozen=True)
class ReportIdentity:
    """Collision-safe report identity: explicit type plus parent identity."""

    report_type: str
    parent_report: str
    path: str


def _normalize(root: Path, relative_path: str, label: str) -> str:
    if not isinstance(relative_path, str) or not relative_path:
        raise EvidenceError(f"{label} path must be a non-empty contained path.")
    try:
        return secure_fs.normalize_relative_path(PurePosixPath(relative_path))
    except (secure_fs.SecureMutationError, ValueError) as error:
        raise EvidenceError(
            f"{label} path {relative_path!r} must stay contained in the repository."
        ) from error


def acquire_document(
    root: Path,
    relative_path: str,
    *,
    kind: str,
    budget: AcquisitionBudget,
    reject_hardlinks: bool = True,
) -> AcquiredDocument:
    """Acquire one complete document through the current secure-read API."""
    if kind not in _KIND_LIMITS:
        raise EvidenceError(f"unknown evidence kind {kind!r}.")
    normalized = _normalize(root, relative_path, kind)
    try:
        content = secure_fs.secure_read_bytes(
            root,
            PurePosixPath(normalized),
            max_bytes=_KIND_LIMITS[kind],
            reject_hardlinks=reject_hardlinks,
        )
    except FileNotFoundError as error:
        raise EvidenceError(
            f"missing evidence: {relative_path!r} cannot be acquired."
        ) from error
    except secure_fs.SecureMutationError as error:
        if "hard link" in str(error):
            raise EvidenceError(
                f"evidence-unsafe: {kind} acquisition rejected a hard-linked or "
                f"aliased source: {error}"
            ) from error
        raise EvidenceError(
            f"evidence-too-large: {kind} acquisition failed: {error}"
        ) from error
    except OSError as error:
        raise EvidenceError(
            f"evidence-unreadable: {kind} acquisition failed: {error}"
        ) from error
    budget.spend(len(content))
    return AcquiredDocument(
        path=normalized,
        kind=kind,
        byte_count=len(content),
        sha256=sha256_hex(content),
        content=content,
    )


def verify_artifact_reference(
    root: Path,
    reference: ArtifactReference,
    *,
    budget: AcquisitionBudget,
    referencing_path: Optional[str] = None,
) -> AcquiredDocument:
    """Re-acquire one referenced artifact and verify its exact identity."""
    if referencing_path and reference.path == referencing_path:
        raise EvidenceError(f"self-reference: {reference.path} references itself.")
    kind = "receipt" if reference.kind == "test-result" else "report"
    document = acquire_document(root, reference.path, kind=kind, budget=budget)
    if document.sha256 != reference.sha256:
        raise EvidenceError(
            f"content-changed: {reference.path} no longer matches the recorded "
            "SHA-256; the file was replaced after capture."
        )
    if document.byte_count != reference.byte_count:
        raise EvidenceError(
            f"byte-count mismatch for {reference.path}: recorded "
            f"{reference.byte_count}, acquired {document.byte_count}."
        )
    return document


def verify_plan_linked_report(
    root: Path, plan: ValidatedPlan, *, budget: AcquisitionBudget
) -> AcquiredDocument:
    """Verify the plan's own linked work report, never the newest file."""
    try:
        return acquire_document(
            root, plan.execution_report, kind="report", budget=budget
        )
    except EvidenceError as error:
        if "missing" in error.message:
            raise EvidenceError(
                f"missing-work-report: the plan links "
                f"{plan.execution_report!r} but it cannot be acquired."
            ) from error
        raise


def allocate_report_path(
    report_dir: Path, parent_identity: str, report_type: str
) -> ReportIdentity:
    """Allocate a collision-safe path ending -review.md or -verify-review.md."""
    if report_type not in _REPORT_TYPES:
        raise EvidenceError(
            f"unknown report-type {report_type!r}; expected one of {_REPORT_TYPES}."
        )
    if not _PARENT_IDENTITY_RE.fullmatch(parent_identity):
        raise EvidenceError(
            f"invalid parent-identity {parent_identity!r}; use a bounded "
            "alphanumeric identifier."
        )
    base = f"{parent_identity}-{report_type}"
    counter = 1
    while True:
        name = f"{base}.md" if counter == 1 else f"{parent_identity}-{counter}-{report_type}.md"
        if not (report_dir / name).exists():
            break
        counter += 1
    return ReportIdentity(
        report_type=report_type,
        parent_report=parent_identity,
        path=(report_dir / name).as_posix(),
    )


def _frontmatter_field(content: str, key: str) -> Optional[str]:
    if not content.lstrip("\ufeff\r\n").startswith("---"):
        return None
    try:
        block = content.lstrip("\ufeff\r\n").split("---", 2)[1]
    except IndexError:
        return None
    matches: list[str] = []
    for line in block.splitlines():
        if line.startswith(f"{key}:"):
            value = line.partition(":")[2].strip().strip("\"'")
            if value:
                matches.append(value)
    if len(matches) > 1:
        raise EvidenceError(
            f"duplicate-{key}: the {key!r} field must be declared at most once."
        )
    return matches[0] if matches else None


def verify_review_report(
    root: Path,
    relative_path: str,
    *,
    expected_type: str,
    expected_parent: str,
    budget: AcquisitionBudget,
) -> AcquiredDocument:
    """Verify a review report's explicit type and parent identity fields."""
    document = acquire_document(root, relative_path, kind="report", budget=budget)
    try:
        content = document.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise EvidenceError("review report is not valid strict UTF-8.") from error
    declared_type = _frontmatter_field(content, "report-type")
    if declared_type is None:
        raise EvidenceError(
            f"report-type missing: {relative_path} does not declare 'report-type'."
        )
    if declared_type != expected_type:
        raise EvidenceError(
            f"wrong-report-type: {relative_path} declares {declared_type!r}, "
            f"expected {expected_type!r}."
        )
    declared_parent = _frontmatter_field(content, "parent-report")
    if declared_parent != expected_parent:
        raise EvidenceError(
            f"wrong-parent-report: {relative_path} declares parent "
            f"{declared_parent!r}, expected {expected_parent!r}."
        )
    return document


def read_test_result(root: Path, relative_path: str, *, budget: AcquisitionBudget) -> dict:
    """Read one machine test receipt; a summary is never execution evidence."""
    document = acquire_document(root, relative_path, kind="receipt", budget=budget)
    try:
        payload = json.loads(document.content.decode("utf-8", errors="strict"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise EvidenceError(
            f"test receipt {relative_path!r} is not valid machine JSON."
        ) from error
    import cg_summary

    return {
        "path": document.path,
        "sha256": document.sha256,
        "byte-count": document.byte_count,
        "summary": cg_summary.summarize_last_run(payload),
    }


def freeze_test_result(
    receipts_root: Path, operation_id: str, content: bytes
) -> str:
    """Freeze one operation-specific receipt before shared output can change.

    The frozen file is written expected-absent; an identical replay is
    idempotent while different bytes conflict.
    """
    if not _OPERATION_ID_RE.fullmatch(operation_id):
        raise EvidenceError("operation-id must be a lowercase bounded ID.")
    relative = f"{operation_id}.test-result.json"
    try:
        existing = secure_fs.secure_read_bytes(
            receipts_root, PurePosixPath(relative), max_bytes=RECEIPT_LIMIT
        )
    except FileNotFoundError:
        existing = None
    digest = sha256_hex(content)
    if existing is not None:
        if sha256_hex(existing) == digest:
            return digest
        raise EvidenceError(
            f"receipt-exists: {relative} already holds different frozen bytes."
        )
    try:
        secure_fs.secure_write_bytes(
            receipts_root,
            PurePosixPath(relative),
            content,
            expected_state=ExpectedFileState.absent(),
        )
    except secure_fs.SecureMutationError as error:
        raise EvidenceError(f"freeze failed: {error}") from error
    return digest


def verify_frozen_test_result(
    receipts_root: Path, operation_id: str, expected_sha256: str
) -> bytes:
    """Read back one frozen receipt and verify its exact digest."""
    if not _OPERATION_ID_RE.fullmatch(operation_id):
        raise EvidenceError("operation-id must be a lowercase bounded ID.")
    relative = f"{operation_id}.test-result.json"
    try:
        content = secure_fs.secure_read_bytes(
            receipts_root, PurePosixPath(relative), max_bytes=RECEIPT_LIMIT
        )
    except secure_fs.SecureMutationError as error:
        raise EvidenceError(f"frozen receipt unreadable: {error}") from error
    if sha256_hex(content) != expected_sha256:
        raise EvidenceError(
            f"receipt-changed: {relative} no longer matches the frozen digest."
        )
    return content


# Change-manifest capture and verification live in manifest.py, which imports
# the shared acquisition helpers above. Callers needing ChangeManifest and its
# helpers import autopilot.manifest directly: the import graph stays acyclic.
