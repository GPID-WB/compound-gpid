"""Strict optional GPID policy records, separate from generic policy semantics."""

from typing import Annotated, Literal

from pydantic import Field

from cg_release.model_base import Commit, Digest, Name, Positive, StrictRecord


class BridgeRelease(StrictRecord):
    """One reviewed published distribution, including immutable Git identities."""

    tag: Name
    release_id: Positive
    revision: Commit
    tag_object: Commit
    tree: Commit


class BridgeSpec(StrictRecord):
    """Explicit three-release qualification inputs, not inferred from origin/HEAD."""

    repository_id: Positive
    repository_slug: Name
    previous: BridgeRelease
    bridge: BridgeRelease
    successor: BridgeRelease


class Bridge(BridgeRelease):
    """Reviewed delivery and exact real qualifier job/artifact identities."""

    previous: BridgeRelease
    successor: BridgeRelease
    workflow_path: Literal[".github/workflows/release-controller-bridge.yml"]
    windows_run_id: Positive
    unix_run_id: Positive
    windows_job_id: Positive
    unix_job_id: Positive
    windows_artifact_id: Positive
    unix_artifact_id: Positive
    windows_artifact_digest: Digest
    unix_artifact_digest: Digest
    app_id: Positive


class DocsBaseline(StrictRecord):
    """Reviewed snapshot of an adopted release; never newly generated history."""

    tag: Name
    sha: Commit
    release_id: Positive
    asset_id: Positive
    sha256: Digest
    size: Annotated[int, Field(gt=0, le=67108864)]
    run_id: Positive
    run_attempt: Positive


class ProfilePolicy(StrictRecord):
    """GPID edits, immutable documentation adoption and bounded mutable repairs."""

    bridge: Bridge | None
    payload_directory: Literal["releases"]
    latest_payload: Literal["releases/latest.json"]
    attestation_directory: Literal[
        ".github/shared/skill-management/release-attestations"
    ]
    docs_workflow: Literal[".github/workflows/release-controller-docs.yml"]
    composition_retries: Annotated[int, Field(ge=0, le=10)] = 3
    docs_baselines: Annotated[list[DocsBaseline], Field(max_length=100)] = Field(
        default_factory=list
    )
