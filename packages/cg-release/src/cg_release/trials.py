"""Offline rollout plans and unverified measurement summaries; no provider access."""

import math
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cg_release.events import ControllerError
from cg_release.jsonio import decode_json

Identifier = Annotated[int, Field(strict=True, gt=0)]
Seconds = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]
Stage = Literal["queue", "review", "approval", "build", "publication", "recovery"]
INTERVALS = {"queue", "review", "approval", "build", "publication", "recovery"}
MAX_INPUT_BYTES = 65536
MIN_SAMPLES = 10
HANDOFF_SECONDS = 120


class TrialRecord(BaseModel):
    """Reject unknown or coerced fields in local trial data."""

    model_config = ConfigDict(extra="forbid", strict=True)


class SandboxConfig(TrialRecord):
    """Target declaration for planning only; not a runtime policy or approval."""

    schema_version: int = Field(strict=True, ge=1, le=1)
    repository_id: Identifier
    repository_url: str = Field(
        max_length=255,
        pattern=r"^https://github\.com/[A-Za-z0-9][A-Za-z0-9-]*/"
        r"[A-Za-z0-9_][A-Za-z0-9_.-]*$",
    )
    profile: Literal["generic", "gpid"]
    authorization_reference: str = Field(
        min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$"
    )


class Sample(TrialRecord):
    """One attempted start, including failures and only the confirmation exclusion."""

    total_seconds: Seconds
    confirmation_seconds: Seconds
    outcome: Literal["receipt", "failed", "blocked", "unknown"]
    error_code: str | None = Field(default=None, pattern=r"^E_[A-Z0-9_]{1,64}$")

    @model_validator(mode="after")
    def validate_sample(self) -> "Sample":
        """Reject impossible intervals and inconsistent outcomes; e.g. Sample(...)."""
        if self.confirmation_seconds > self.total_seconds:
            raise ValueError("Confirmation exceeds total duration")
        if (self.outcome == "receipt") != (self.error_code is None):
            raise ValueError("Receipt and failure code disagree")
        return self


class Environment(TrialRecord):
    """Bounded host labels and managed history size supplied by a trial operator."""

    python: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_. -]+$")
    platform: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_. -]+$")
    history_size: int = Field(ge=0)


class Measurements(TrialRecord):
    """Data for arithmetic checks, never proof of receipt or remote identity."""

    schema_version: int = Field(strict=True, ge=1, le=1)
    repository_id: Identifier
    environment: Environment
    warm_dependencies: bool
    sequential: bool
    samples: list[Sample] = Field(min_length=1, max_length=1000)
    intervals: dict[Stage, Seconds | None]


CASES = {
    "preview-and-versions": "Read-only plan; non-production prerelease; stable; "
    "allowed/rejected override; maintenance latest; signing and tampered policy.",
    "approval-role-denials": "Pre-approval URL visible; requester/reconfirmer "
    "excluded; actual App cross-role ref denials; protected settings; hostile source.",
    "publication": "Exact reviewed commit, tag object, Release, asset digests "
    "and latest selection; source cannot obtain control/signing/publication secrets.",
    "portable-locator-recovery": "Lost response on either side of every write; "
    "second-machine status/resume; concurrency, dropped wakeup, repeat convergence.",
    "retention-and-lineage": "Expired evidence, journal backup/restore, owner "
    "credential expiry, branch advancement after tag; no rewrite or asset clobber.",
    "native-hosts": "Clean install; Windows PowerShell 5.1/native Unix launchers; "
    "Python 3.11/3.12 on Windows/Linux/macOS; bounded child-only Pester.",
    "timing": "At least ten sequential warm-dependency starts, all failures, "
    "confirmation alone excluded, min/median/nearest-rank p95 <=120 seconds; "
    "history/environment, separate stage intervals and comparable legacy workload.",
}
GPID_CASES = {
    "bridge-clean-clients": "Delivered legacy bridge and actual Windows/native "
    "Unix previous updater -> bridge -> SemVer pin receipts with exact identities.",
    "registered-final-sha-ci": "Preparation merge/squash on a non-integration "
    "branch; registered final SHA (not PR test-merge SHA), six cells, Ruff, aggregate "
    "and native/profile run/attempt/job/producer evidence.",
    "post-hooks": "Failed hook/resume; published differs from complete; mutable "
    "dev advancement during approval and after tag refreshes composition only.",
}


def read_input(path: Path) -> object:
    """Read bounded strict JSON without executing it, e.g. read_input(Path('x.json')).

    Args:
        path: Explicit local JSON input.
    Returns:
        Parsed data, not authority.
    Raises:
        ValueError, OSError: Invalid, oversized or unreadable input.
    """
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Trial input exceeds 64 KiB")
    try:
        return decode_json(raw.decode("utf-8"))
    except ControllerError:
        raise ValueError("Invalid trial JSON") from None


def plan_sandbox(data: object, *, repository_id: int) -> dict:
    """Validate a target and list unexecuted cases.

    Example: plan_sandbox(data, repository_id=123).

    Args:
        data: Explicit sandbox configuration. Never read origin or a runtime policy.
        repository_id: Independently supplied numeric allowlist identity.
    Returns:
        An offline checklist with every live obligation still deferred.
    Raises:
        ValueError: Invalid or mismatched configuration.
    """
    config = SandboxConfig.model_validate(data)
    if type(repository_id) is not int or config.repository_id != repository_id:
        raise ValueError("Explicit sandbox repository ID does not match")
    cases = CASES | (GPID_CASES if config.profile == "gpid" else {})
    return {
        "schema_version": 1,
        "mode": "offline-trial-plan",
        "target": config.model_dump(),
        "authorization_verified": False,
        "remote_writes": 0,
        "live_evidence": "deferred-not-passed",
        "cases": [
            {"id": key, "required": text, "status": "deferred-not-passed"}
            for key, text in cases.items()
        ],
    }


def summarize_measurements(data: object, *, repository_id: int) -> dict:
    """Summarize supplied observations, not independently verified evidence.

    Example: summarize_measurements(data, repository_id=123).

    Args:
        data: Bounded sample inventory, including failed/blocked/unknown attempts.
        repository_id: Exact identity from the separately validated sandbox config.
    Returns:
        Unverified arithmetic; never a live gate or speedup claim.
    Raises:
        ValueError: Invalid identity, shape, duration, or incomplete interval set.
    """
    record = Measurements.model_validate(data)
    if type(repository_id) is not int or record.repository_id != repository_id:
        raise ValueError("Measurement repository ID does not match")
    if set(record.intervals) != INTERVALS:
        raise ValueError("All separate stage intervals must be present or null")
    durations = sorted(s.total_seconds - s.confirmation_seconds for s in record.samples)
    failures = [
        {"sample": i, "outcome": s.outcome, "error_code": s.error_code}
        for i, s in enumerate(record.samples, 1)
        if s.outcome != "receipt"
    ]
    p95 = durations[math.ceil(0.95 * len(durations)) - 1]
    middle = len(durations) // 2
    median = durations[middle]
    if len(durations) % 2 == 0:
        lower = durations[middle - 1]
        # Ordered nonnegative values permit a midpoint without an overflowing sum.
        median = lower + (median - lower) / 2
    if not math.isfinite(median):
        raise ValueError("Measurement median must be finite")
    return {
        "schema_version": 1,
        "evidence_status": "unverified-input-summary",
        "repository_id": repository_id,
        "environment": record.environment.model_dump(),
        "sample_count": len(durations),
        "failure_count": len(failures),
        "failures": failures,
        "samples": [s.model_dump() for s in record.samples],
        "warm_dependencies": record.warm_dependencies,
        "sequential": record.sequential,
        "min_seconds": durations[0],
        "median_seconds": median,
        "p95_seconds": p95,
        "percentile_method": "nearest-rank",
        "within_target_from_supplied_data": bool(
            len(durations) >= MIN_SAMPLES
            and not failures
            and record.warm_dependencies
            and record.sequential
            and p95 <= HANDOFF_SECONDS
        ),
        "live_handoff_passed": False,
        "legacy_baseline": None,
        "speedup": None,
        "intervals": record.intervals,
        "qualification": "Supplied observations are not independently verified. "
        "Keep exact argv/exits, receipt/request/run identities, timestamps and "
        "authorization records for separate rollout review. "
        "Missing baseline is not zero.",
    }
