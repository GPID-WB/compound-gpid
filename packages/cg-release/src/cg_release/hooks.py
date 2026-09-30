"""Typed optional profile boundary; generic mode loads no project extension."""

import importlib
from pathlib import Path
from typing import Literal, Protocol

from pydantic import field_validator

from cg_release.events import ControllerError
from cg_release.metadata import Edit
from cg_release.models import Commit, Digest, Positive, StrictRecord


class HookResult(StrictRecord):
    """Compact trusted verifier output, not a source-written success flag."""

    stage: Literal["docs", "evidence"]
    release_sha: Commit
    evidence_digest: Digest
    remote_id: Positive
    verified: Literal[True] = True

    @field_validator("verified", mode="before")
    @classmethod
    def actual_boolean(cls, value):
        """Reject integer/string claims before Literal validation."""
        if value is not True:
            raise ValueError("verified must be the boolean true")
        return value


class Profile(Protocol):
    """Installed Profile API; source files are data, never module/resource providers.

    VERSION identifies protocol v1; REQUIRED_FILES declares metadata-read inputs.
    Errors below are ControllerError unless a strict-record validation fails.
    resource and verify_snapshot must be usable with no repository checkout.
    """

    VERSION: str
    REQUIRED_FILES: tuple[str, ...]

    def validate_policy(self, policy) -> None:
        """Check structural policy, returning None or raising; no I/O.

        Example: profile.validate_policy(policy) before preview's remote checks.
        """
        ...

    def source_blobs(self, api, tree: str, tag: str, *, default_tree: str) -> dict:
        """GET exact source/default Git trees; return declared SourceBlob mapping.

        Reject existing payload/collisions. No writes. Example:
        profile.source_blobs(api, tree, 'v1.5.0', default_tree=default_tree).
        """
        ...

    def verify_bridge(self, api, policy) -> None:
        """GET exact real qualifier/Release evidence or raise; return None.

        Example: profile.verify_bridge(api, policy). No local or remote writes.
        """
        ...

    def resource(self, name: str) -> Path:
        """Return a RECORD-verified installed Node path or raise on unsafe data.

        Reads all fixed resource identities, with no writes or source fallback.
        Example: profile.resource('docs-snapshots.js').
        """
        ...

    def verify_snapshot(
        self,
        raw: bytes,
        *,
        tag: str | None,
        sha: str,
        run_id: int,
        run_attempt: int,
        kind: str = "release",
    ) -> dict:
        """Decode bounded raw snapshot bytes; return the verified record or raise.

        No I/O. Example: profile.verify_snapshot(raw, tag='v1.5.0', sha=sha,
        run_id=12, run_attempt=1). kind='dev' requires tag=None.
        """
        ...

    def prepare(
        self, snapshot, *, tag: str, version: str, created_at: str
    ) -> tuple[Edit, ...]:
        """Return immutable metadata edits from a verified snapshot; no writes.

        Raise for invalid source/payload/version. Example:
        profile.prepare(snapshot, tag='v1.5.0', version='1.5.0', created_at=utc).
        """
        ...

    def complete(self, context, record, *, resuming_actor_id=None) -> dict[str, dict]:
        """Return compact post-publication hook records or raise on failed proof.

        May write only declared authorized evidence/dispatch/journal effects.
        Example: profile.complete(ctx, record, resuming_actor_id=7).
        """
        ...


def selected_profile(policy) -> Profile | None:
    """Load only the explicit wheel-bundled profile, e.g. selected_profile(policy).

    No source checkout, entry-point discovery or environment-selected module is used.
    The wheel is independently pinned by the trusted worker installation.
    Args: validated Policy with explicit gpid_profile=None or 'v1'. Returns None
    in generic mode or the installed Profile module. Raises ControllerError for
    unsupported/missing installations. Imports trusted code only; no remote writes.
    """
    if policy.gpid_profile is None:
        return None
    if policy.gpid_profile != "v1":
        raise ControllerError("E_PROFILE", "Unsupported profile version.")
    try:
        return importlib.import_module("_cg_release_gpid")
    except ImportError:
        raise ControllerError(
            "E_PROFILE", "Selected profile is not installed in the trusted wheel."
        ) from None


def verified_hooks(context, record, *, resuming_actor_id=None) -> dict:
    """Run installed post-publication hooks and validate raw HookResult dictionaries.

    Args: authorized context, published journal record, and applicable resumer ID.
    Returns a stage mapping; absent stages are pending, never verified completion.
    Raises ControllerError or validation errors for unknown stages or bad evidence.
    Example: verified_hooks(ctx, record, resuming_actor_id=7). Hooks may create the
    declared evidence PR, composition dispatch and authenticated journal entries
    after fresh authority checks; published tag and asset bytes remain immutable.
    """
    profile = selected_profile(context.policy)
    if profile is None:
        return {}
    results = profile.complete(context, record, resuming_actor_id=resuming_actor_id)
    if set(results) - {"docs", "evidence"}:
        raise ControllerError("E_HOOK", "Unexpected profile completion stage.")
    validated = {
        name: HookResult.model_validate(value, strict=True).model_dump()
        for name, value in results.items()
    }
    if any(value["stage"] != name for name, value in validated.items()):
        raise ControllerError(
            "E_HOOK", "Profile result stage differs from its required hook."
        )
    return validated
