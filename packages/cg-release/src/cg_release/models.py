"""Schema-v1 boundary records, strict JSON decoding, and canonical digest input."""

import json
from typing import Annotated, Literal, TypeVar

from pydantic import BaseModel, Field, field_validator
from semver import Version

from cg_release.model_base import (
    Commit as Commit,
)
from cg_release.model_base import (
    Digest as Digest,
)
from cg_release.model_base import (
    Host,
    Name,
)
from cg_release.model_base import (
    Positive as Positive,
)
from cg_release.model_base import (
    StrictRecord as StrictRecord,
)
from cg_release.model_base import (
    VersionedRecord as VersionedRecord,
)
from cg_release.profile_models import Bridge as Bridge
from cg_release.profile_models import ProfilePolicy as ProfilePolicy

MAX_RECORD_BYTES = 65536


class ReleaseLine(StrictRecord):
    """Named branch membership and inclusive/exclusive numeric core bounds."""

    id: Name
    branches: Annotated[list[Name], Field(min_length=1)]
    minimum_core: tuple[int, int, int]
    maximum_core_exclusive: tuple[int, int, int] | None


class HistoricalRelease(StrictRecord):
    """Audited adoption record; never an instruction to rewrite legacy objects."""

    release_id: Positive
    tag: Name
    commit: Commit
    line: Name
    version: Name
    legacy_version: Name | None
    projections: dict[str, str]


class MetadataAdapter(StrictRecord):
    """Declared metadata location; pure format semantics live in metadata.py."""

    kind: Literal["json", "python-project", "r-description"]
    path: Name
    pointer: str | None


class Changelog(StrictRecord):
    """One declared insertion marker in one Markdown file."""

    path: Name
    marker: Annotated[str, Field(min_length=1, max_length=1024)]


class Artifact(StrictRecord):
    """Required inventory item, with a per-file byte limit."""

    name: Name
    path: Name
    media_type: Name
    required: bool
    max_bytes: Positive


class Build(StrictRecord):
    """Trusted build inputs; these commands are not executed in Phase 1."""

    argv: Annotated[list[Name], Field(min_length=1)]
    cwd: Name
    lock_paths: Annotated[list[Name], Field(min_length=1)]
    artifacts: Annotated[list[Artifact], Field(min_length=1)]
    max_artifacts: Positive
    max_total_bytes: Positive


class RequiredCheck(StrictRecord):
    """Explicit stage and producer identity, not a status name alone."""

    name: Name
    app_id: Positive
    workflow_path: Name
    stage: Literal["preparation-and-release", "release"]


class ControllerPin(StrictRecord):
    """Exact reviewed controller revision and installed wheel identity."""

    revision: Commit
    wheel_digest: Digest


class Apps(StrictRecord):
    """Distinct control and publication GitHub App numeric identities."""

    control: Positive
    control_slug: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
    publishing: Positive


class Environments(StrictRecord):
    """Environment names whose settings must be verified before admission."""

    control: Name
    publish: Name
    override: Name


class Timeouts(StrictRecord):
    """Explicit bounded timing controls, in seconds."""

    read_seconds: Annotated[int, Field(gt=0, le=20)]
    read_attempts: Annotated[int, Field(gt=0, le=3)]
    start_seconds: Annotated[int, Field(gt=0, le=120)]
    watch_seconds: Annotated[int, Field(gt=0, le=3600)]
    poll_seconds: Annotated[int, Field(ge=5)]
    job_minutes: Annotated[int, Field(gt=0, le=360)]


class Policy(VersionedRecord):
    """Strict policy shape; policy.py and source.py enforce semantics and trust."""

    enabled: bool
    repository_id: Positive
    host: Host
    tag_prefix: Annotated[str, Field(max_length=64)]
    production_branches: list[Name]
    release_lines: Annotated[list[ReleaseLine], Field(min_length=1)]
    bootstrap: list[HistoricalRelease]
    metadata: Annotated[list[MetadataAdapter], Field(min_length=1)]
    changelog: Changelog
    build: Build
    required_checks: Annotated[list[RequiredCheck], Field(min_length=1)]
    controller: ControllerPin
    state_branch: Name
    journal_root: Commit
    apps: Apps
    signing_required: bool
    allowed_signing_fingerprints: list[
        Annotated[str, Field(pattern=r"^(?:[A-F0-9]{40}|[A-F0-9]{64})$")]
    ]
    environments: Environments
    timeouts: Timeouts
    gpid_profile: Literal["v1"] | None
    profile: ProfilePolicy | None = None


class Request(VersionedRecord):
    """Confirmed immutable input shape, not proof of admission or approval."""

    host: Host
    repository_id: Positive
    repository_slug: Annotated[str, Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")]
    requester_id: Positive
    nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    proposal_digest: Digest
    source_branch: Name
    source_sha: Commit
    policy_sha: Commit
    policy_digest: Digest
    line: Name
    version: Name
    tag: Name
    sign: bool
    override_reason: Annotated[str, Field(min_length=1, max_length=1024)] | None
    requested_bump: Literal["major", "minor", "patch", "prerelease"] | None
    requested_channel: Annotated[str, Field(max_length=64)] | None

    @field_validator("version")
    @classmethod
    def valid_version(cls, value: str) -> str:
        """Validate strict SemVer syntax without resolving policy or precedence."""
        if str(Version.parse(value)) != value:
            raise ValueError("version must be exact SemVer without whitespace")
        return value


class Event(VersionedRecord):
    """Bounded stdout event; absent measurements remain null, not zero."""

    schema_version: Literal[1] = 1
    kind: Literal[
        "error", "submission-intent", "receipt", "status", "timing", "preview"
    ]
    code: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]*$")] | None = None
    message: Annotated[str, Field(max_length=2048)] = ""
    request_id: Annotated[str, Field(max_length=4096)] | None = None
    version: Name | None = None
    step: Name | None = None
    expected: Name | None = None
    observed: Name | None = None
    elapsed_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    next_action: Annotated[str, Field(max_length=1024)] | None = None
    proposal: dict | None = None


class JobResult(StrictRecord):
    """Actual job identity and conclusion from the trusted jobs API."""

    job_id: Positive
    name: Name
    conclusion: Literal["success", "failure", "cancelled", "skipped", "timed_out"]


class Provenance(VersionedRecord):
    """Source and controller identities stay separate in release-mode evidence."""

    repository_id: Positive
    request_digest: Digest
    dispatch_nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    workflow_path: Name
    controller_workflow_sha: Commit
    controller_workflow_ref: Name
    release_source_sha: Commit
    release_tree: Commit
    policy_digest: Digest
    controller_digest: Digest
    run_id: Positive
    run_attempt: Positive
    jobs: Annotated[list[JobResult], Field(min_length=1)]
    required_checks_digest: Digest
    build_inputs_digest: Digest
    toolchain_digest: Digest
    inventory_digest: Digest
    profile_version: Name | None


Record = TypeVar("Record", bound=BaseModel)


def canonical_bytes(value: BaseModel | dict) -> bytes:
    """Return UTF-8 sorted compact JSON for hashing.

    Args: value is a validated model or JSON dictionary, e.g. ``{"a": 1}``.
    Returns: Canonical bytes; no digest is added to its own input.
    Raises: ValueError for non-finite JSON numbers.
    """
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def load_record(model: type[Record], raw: bytes) -> Record:
    """Decode a bounded schema record, rejecting duplicate keys and input leaks.

    Args:
        model: Boundary model, e.g. ``Request``.
        raw: UTF-8 JSON bytes, at most 64 KiB.
    Returns:
        Strictly validated model.
    Raises:
        ValueError: Invalid JSON or schema; never includes the input payload.
    """

    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise ValueError("non-finite JSON constant")

    if not isinstance(raw, bytes) or len(raw) > MAX_RECORD_BYTES:
        raise ValueError("record must be bounded UTF-8 JSON bytes")
    try:
        decoded = raw.decode("utf-8")
        payload = json.loads(
            decoded, object_pairs_hook=unique, parse_constant=reject_constant
        )
        if not isinstance(payload, dict):
            raise ValueError("invalid record")
        return model.model_validate_json(raw, strict=True)
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError("invalid schema-v1 record") from None
