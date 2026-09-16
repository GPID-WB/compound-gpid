"""Deadline-aware CI check classification and safe diagnostics (Step 11).

Pure, deterministic classification over normalized ``gh`` rollup entries with a
closed policy table, complete pagination, original/effective deadlines, clipped
request/poll timing, bounded transport retries, and redaction of any fetched
diagnostic before it can reach model output. No sleeps, network calls or remote
effects live here; runners and clocks are injected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from autopilot.contracts import AutopilotError
from autopilot.queries import REQUEST_TIMEOUT_SECONDS, Check

POLL_SECONDS = 15
READ_RETRIES = 2
RERUNS_PER_BATCH = 1
MAX_DIAGNOSTIC_BYTES = 8 * 1024

_JOB_URL_RE = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/actions/runs/(?P<run>[0-9]+)/job/(?P<job>[0-9]+)(?:[/?#].*)?$"
)
# Case-insensitive secret redaction patterns. The GitHub token shapes mirror the
# canonical .github/shared/vendor-policy.json blockedSecretPatterns entries
# (ghp_/gho_ with 36 body characters; github_pat_ with 22+); this module stays
# pure with no file I/O, so the patterns are mirrored as constants.
_SECRET_RE = (
    (re.compile(rb"ghp_[A-Za-z0-9]{36}", re.IGNORECASE), b"ghp_<redacted>"),
    (re.compile(rb"ghs_[A-Za-z0-9]{36}", re.IGNORECASE), b"ghs_<redacted>"),
    (re.compile(rb"gho_[A-Za-z0-9]{36}", re.IGNORECASE), b"gho_<redacted>"),
    (re.compile(rb"github_pat_[A-Za-z0-9_]{22,}", re.IGNORECASE), b"github_pat_<redacted>"),
    (re.compile(rb"xox[prsbo]-[A-Za-z0-9-]+", re.IGNORECASE), b"xox-<redacted>"),
    (re.compile(rb"AKIA[0-9A-Z]{16}", re.IGNORECASE), b"AKIA<redacted>"),
    (re.compile(rb"ASIA[0-9A-Z]{16}", re.IGNORECASE), b"ASIA<redacted>"),
    (re.compile(rb"eyJ\S{8,}", re.IGNORECASE), b"JWT<redacted>"),
    (re.compile(rb"Bearer\s+\S+", re.IGNORECASE), b"Bearer <redacted>"),
    (re.compile(rb"token=\S+", re.IGNORECASE), b"token=<redacted>"),
)


class CiError(AutopilotError):
    error_code = "autopilot-ci-error"


@dataclass(frozen=True)
class RequiredContext:
    name: str
    app_id: Optional[str]


@dataclass(frozen=True)
class FailedIdentity:
    name: str
    conclusion: str
    details_url: Optional[str]


@dataclass(frozen=True)
class RunJob:
    run_id: str
    job_id: str


@dataclass(frozen=True)
class Observation:
    status: str
    reason: str
    failing: Tuple[FailedIdentity, ...]
    missing: Tuple[str, ...]
    counts: Mapping[str, int]


@dataclass(frozen=True)
class Deadline:
    original: str
    effective: str


@dataclass(frozen=True)
class Diagnostic:
    identity: RunJob
    byte_count: int
    redacted: bytes
    truncated: bool


def clip_request_timeout(remaining_seconds: int) -> int:
    if not isinstance(remaining_seconds, int) or remaining_seconds <= 0:
        return 0
    return min(REQUEST_TIMEOUT_SECONDS, remaining_seconds)


def clip_poll_seconds(remaining_seconds: int) -> int:
    if not isinstance(remaining_seconds, int) or remaining_seconds <= 0:
        return 0
    return min(POLL_SECONDS, remaining_seconds)


def merged_checks(pages: Sequence[Sequence[Check]]) -> Tuple[Check, ...]:
    """Merge complete pages, rejecting ambiguous duplicate check identities."""
    by_name: dict[str, Check] = {}
    for page in pages:
        for check in page:
            prior = by_name.get(check.name)
            if prior is not None and (
                prior.status, prior.conclusion, prior.details_url
            ) != (check.status, check.conclusion, check.details_url):
                raise CiError(
                    f"ambiguous-check: {check.name!r} appears with conflicting "
                    "identities; duplicate resolution requires explicit order."
                )
            by_name[check.name] = check
    return tuple(by_name[name] for name in sorted(by_name))


def classify_observation(
    checks: Sequence[Check],
    *,
    required: Sequence[RequiredContext] = (),
    non_applicable: frozenset = frozenset(),
    cancelled_rerun_approved: frozenset = frozenset(),
) -> Observation:
    by_name = {check.name: check for check in checks}
    missing = tuple(context.name for context in required if context.name not in by_name)
    counts = {
        "success": 0, "failure": 0, "timed_out": 0, "neutral": 0, "skipped": 0,
        "cancelled": 0, "action_required": 0, "stale": 0, "pending": 0,
        "missing": len(missing), "malformed": 0,
    }
    failing: list[FailedIdentity] = []
    blockers: list[str] = []
    neutral: list[str] = []
    cancelled: list[str] = []
    success_names = {check.name for check in checks if check.conclusion == "SUCCESS"}
    redeemed_cancelled: list[str] = []
    for check in checks:
        conclusion = check.conclusion
        if check.status == "COMPLETED" and conclusion is None:
            counts["malformed"] += 1
            blockers.append(check.name)
            continue
        if conclusion == "SUCCESS":
            counts["success"] += 1
        elif conclusion == "FAILURE":
            counts["failure"] += 1
            failing.append(FailedIdentity(check.name, "FAILURE", check.details_url))
        elif conclusion == "TIMED_OUT":
            counts["timed_out"] += 1
            failing.append(FailedIdentity(check.name, "TIMED_OUT", check.details_url))
        elif conclusion == "ACTION_REQUIRED":
            counts["action_required"] += 1
            blockers.append(check.name)
        elif conclusion == "STALE":
            counts["stale"] += 1
            blockers.append(check.name)
        elif conclusion == "CANCELLED":
            counts["cancelled"] += 1
            if (
                check.name in cancelled_rerun_approved
                and check.name in success_names
            ):
                redeemed_cancelled.append(check.name)
            else:
                cancelled.append(check.name)
        elif conclusion == "NEUTRAL":
            counts["neutral"] += 1
            neutral.append(check.name)
        elif conclusion == "SKIPPED":
            counts["skipped"] += 1
            neutral.append(check.name)
        else:
            counts["pending"] += 1

    if blockers:
        if counts["malformed"]:
            return Observation("block", "malformed-check",
                               tuple(failing), tuple(missing), counts)
        return Observation("block", "action-required", tuple(failing), tuple(missing), counts)
    unresolved_neutral = [name for name in neutral if name not in non_applicable]
    if unresolved_neutral:
        return Observation("block", "neutral-policy-required",
                           tuple(failing), tuple(missing), counts)
    if len(redeemed_cancelled) > RERUNS_PER_BATCH:
        return Observation(
            "block", "cancelled-approval-exceeded",
            tuple(failing), tuple(missing), counts,
        )
    if cancelled:
        return Observation("block", "cancelled", tuple(failing), tuple(missing), counts)
    if failing:
        return Observation("diagnose", "failure", tuple(failing), tuple(missing), counts)
    if missing:
        return Observation("wait", "missing-context", (), tuple(missing), counts)
    if counts["pending"]:
        return Observation("wait", "pending", (), (), counts)
    return Observation("eligible", "eligible", (), (), counts)


def parse_job_url(url: str) -> RunJob:
    if not isinstance(url, str):
        raise CiError("job-url: the details URL must be a string.")
    match = _JOB_URL_RE.match(url)
    if not match:
        raise CiError(
            f"job-url: {url!r} is not an exact Actions run/job URL; no other "
            "log route is permitted."
        )
    return RunJob(match.group("run"), match.group("job"))


def redact_diagnostic(raw: bytes) -> bytes:
    redacted = bytes(raw)
    for pattern, replacement in _SECRET_RE:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def bound_diagnostic(identity: RunJob, raw: bytes) -> Diagnostic:
    if not isinstance(raw, (bytes, bytearray)):
        raise CiError("diagnostic bytes must be exact bytes.")
    truncated = len(raw) > MAX_DIAGNOSTIC_BYTES
    body = redact_diagnostic(bytes(raw[:MAX_DIAGNOSTIC_BYTES]))
    return Diagnostic(identity, len(raw), body, truncated)