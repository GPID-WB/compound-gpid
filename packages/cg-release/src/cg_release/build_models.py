"""Strict durable build-ticket boundary, separate from source-written manifests."""

from typing import Annotated

from pydantic import Field

from cg_release.models import Build, Commit, Digest, Name, Positive, StrictRecord


class BuildTicket(StrictRecord):
    """Immutable inputs sealed in the schema-v1 journal before trusted dispatch."""

    repository_id: Positive
    request_digest: Digest
    dispatch_nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    workflow_path: Name
    controller_sha: Commit
    controller_ref: Name
    release_sha: Commit
    release_tree: Commit
    policy_digest: Digest
    controller_digest: Digest
    required_checks_digest: Digest
    build_inputs_digest: Digest
    lock_digests: dict[str, Digest]
    toolchain: Name
    profile_version: Name | None
    app_id: Positive
    required_jobs: Annotated[list[Name], Field(min_length=1, max_length=128)]
    build_spec: Build
    produces_artifacts: bool


class BuildRegistration(StrictRecord):
    """One immutable run claim for a sealed build ticket."""

    build_digest: Digest
    dispatch_nonce: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
    run_id: Positive
    run_attempt: Positive
    release_sha: Commit
