"""Typed bounded errors, closed JSON parsing and field validators.

Packet records live in ``packets.py``, which imports this module for its shared
constants and validators; the import graph stays acyclic.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

MAX_RESULT_BYTES = 4096
MAX_ENVELOPE_BYTES = 16384
MAX_MARKER_BYTES = 32768
MAX_CHECKPOINT_BYTES = 32768
MAX_ARTIFACT_REFS = 16
ID_MAX_BYTES = 128

STAGES = (
    "work", "prepare-publication", "review", "triage", "verify-review",
    "compound", "publish", "verify-pr",
)
RESULT_STATUSES = ("succeeded", "failed", "blocked", "needs-input")
ARTIFACT_KINDS = (
    "plan", "report", "review", "verify-review", "finding", "test-result",
    "receipt", "lesson", "manifest", "other",
)
TEST_STATUSES = ("passed", "failed", "accepted-exception")
EVENT_KINDS = ("report-created", "phase-boundary", "blocked-stop")

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
# Bounded ID charset: lowercase letters, digits and hyphens, starting with a
# letter or digit, at most 128 characters. Digit-leading run IDs such as
# "20260915-103000" are valid (active-state.contract.md autopilot section).
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_GIT_IDENTITY_RE = re.compile(r"^git:[0-9a-f]{40}$|^git:[0-9a-f]{64}$")


def sha256_hex(content: bytes) -> str:
    """Return the lowercase SHA-256 of exact bytes."""
    return hashlib.sha256(content).hexdigest()


class AutopilotError(Exception):
    """Typed bounded error; message and code stay separate from stdout data."""

    error_code = "autopilot-error"

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        corrective_action: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.corrective_action = corrective_action
        if error_code is not None:
            self.error_code = error_code

    def __str__(self) -> str:
        rendered = self.message
        if self.corrective_action:
            rendered += f" Corrective action: {self.corrective_action}"
        return rendered


class ArgumentError(AutopilotError):
    """Invalid or ambiguous invocation."""

    error_code = "autopilot-argument-error"


class PlanError(AutopilotError):
    """The plan is not a strict eligible autopilot plan."""

    error_code = "autopilot-plan-error"


class PacketError(AutopilotError):
    """A closed packet violates its shape, size or correlation contract."""

    error_code = "autopilot-packet-error"


class EvidenceError(AutopilotError):
    """Evidence acquisition or reference verification failed."""

    error_code = "autopilot-evidence-error"


class StateError(AutopilotError):
    """A control transaction violated ownership or expected bytes."""

    error_code = "autopilot-state-error"


class RecoveryBlocked(AutopilotError):
    """Recovery cannot proceed safely; recovery files are preserved."""

    error_code = "autopilot-recovery-blocked"


# ---------------------------------------------------------------------------
# Closed JSON parsing
# ---------------------------------------------------------------------------


def parse_closed_json(raw: bytes, *, max_bytes: int, label: str) -> dict:
    """Parse one bounded JSON object, rejecting duplicate keys and non-UTF-8."""
    if not isinstance(raw, (bytes, bytearray)):
        raise PacketError(f"{label}: packet must be exact bytes.")
    if len(raw) > max_bytes:
        raise PacketError(
            f"{label}: packet-too-large ({len(raw)} bytes; limit {max_bytes})."
        )
    try:
        text = bytes(raw).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise PacketError(f"{label}: packet is not valid strict UTF-8.") from error

    def unique_pairs(pairs: Sequence[Tuple[str, Any]]) -> dict:
        result = dict(pairs)
        if len(result) != len(pairs):
            raise PacketError(f"{label}: duplicate-key rejected.")
        return result

    try:
        value = json.loads(text, object_pairs_hook=unique_pairs)
    except PacketError:
        raise
    except json.JSONDecodeError as error:
        raise PacketError(f"{label}: malformed JSON: {error.msg}.") from error
    if not isinstance(value, dict):
        raise PacketError(f"{label}: packet must be a JSON object.")
    return value


def dumps_closed(payload: dict, *, max_bytes: int, label: str) -> bytes:
    """Serialize one packet and enforce the raw byte ceiling."""
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    if len(raw) > max_bytes:
        raise PacketError(
            f"{label}: packet-too-large ({len(raw)} bytes; limit {max_bytes})."
        )
    return raw


# ---------------------------------------------------------------------------
# Field validators
# ---------------------------------------------------------------------------

Checker = Callable[[Any, str], Any]


def _check_type(value: Any, types: tuple, path: str) -> None:
    if not isinstance(value, types):
        expected = " or ".join(t.__name__ for t in types)
        raise PacketError(f"{path} must have {expected} type.")


def _check_id(value: Any, path: str, *, nullable: bool = False) -> Optional[str]:
    if nullable and value is None:
        return None
    _check_type(value, (str,), path)
    if not _ID_RE.fullmatch(value) or len(value.encode("utf-8")) > ID_MAX_BYTES:
        raise PacketError(
            f"{path} must be a lowercase ID of at most {ID_MAX_BYTES} UTF-8 bytes "
            "using lowercase letters, digits and hyphens, starting with a letter "
            "or digit."
        )
    return value


def _check_sha(value: Any, path: str, *, nullable: bool = False) -> Optional[str]:
    if nullable and value is None:
        return None
    _check_type(value, (str,), path)
    if not _SHA_RE.fullmatch(value):
        raise PacketError(f"{path} must match pattern [0-9a-f]{{64}} (SHA-256).")
    return value


def _check_string(
    value: Any, path: str, *, min_bytes: int = 1, max_bytes: int = 512,
    nullable: bool = False,
) -> Optional[str]:
    if nullable and value is None:
        return None
    _check_type(value, (str,), path)
    if not min_bytes <= len(value.encode("utf-8")) <= max_bytes:
        raise PacketError(f"{path} must be {min_bytes}..{max_bytes} UTF-8 bytes.")
    return value


def _check_int(
    value: Any, path: str, *, minimum: int = 0, maximum: int = 2**31 - 1,
    nullable: bool = False,
) -> Optional[int]:
    if nullable and value is None:
        return None
    if type(value) is not int:
        raise PacketError(f"{path} must have integer type (Boolean is not integer).")
    if not minimum <= value <= maximum:
        raise PacketError(f"{path} must be in range {minimum}..{maximum}.")
    return value


def _check_list(
    value: Any, path: str, *, max_items: int, nullable: bool = False,
) -> Optional[list]:
    if nullable and value is None:
        return None
    _check_type(value, (list,), path)
    if len(value) > max_items:
        raise PacketError(f"{path} has more than {max_items} items.")
    return value


def _check_path(value: Any, path: str, *, max_bytes: int = 512) -> str:
    """Validate one contained repository-relative reference path."""
    checked = _check_string(value, path, max_bytes=max_bytes)
    if (
        checked.startswith("/")
        or "\\" in checked
        or ".." in PurePosixPath(checked).parts
    ):
        raise PacketError(
            f"{path} must be a contained relative path with no absolute prefix, "
            "backslashes or traversal components."
        )
    return checked


def _check_content_identity(value: Any, path: str) -> Optional[str]:
    if value is None:
        return None
    _check_type(value, (str,), path)
    if not _SHA_RE.fullmatch(value) and not _GIT_IDENTITY_RE.fullmatch(value):
        raise PacketError(f"{path} must be null, a SHA-256, or git:<40/64 hex>.")
    return value


def parse_object(
    value: Any, path: str, label: str, fields: Tuple[Tuple[str, Checker, dict], ...]
) -> Dict[str, Any]:
    """Parse one closed object: exact declared fields, each validated."""
    _check_type(value, (dict,), path)
    names = {name for name, _, _ in fields}
    if set(value) != names:
        raise PacketError(f"{path} ({label}) has unexpected field or missing fields.")
    result: Dict[str, Any] = {}
    for name, checker, kwargs in fields:
        result[name] = checker(value[name], f"{path}.{name}", **kwargs)
    return result


def parse_enum(value: Any, allowed: Sequence[str], path: str) -> str:
    """Validate one closed enum string."""
    checked = _check_string(value, path, max_bytes=32)
    if checked not in allowed:
        raise PacketError(f"{path} enum must be one of {tuple(allowed)}.")
    return checked


# Protocol packet records live in packets.py, which imports this module for its
# shared constants and validators. The import graph is a DAG: callers needing
# StageEnvelope/StageResult/Decision/ArtifactReference import autopilot.packets.
