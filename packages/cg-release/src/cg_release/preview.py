"""Read-only proposals and rechecked confirmation; admission stays unavailable."""

import argparse
import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass

from cg_release.events import ControllerError
from cg_release.metadata import Edit, SourceBlob, proposed_edits
from cg_release.models import (
    HistoricalRelease,
    Policy,
    Request,
    canonical_bytes,
    load_record,
)
from cg_release.policy import approval_route, safe_ref, select_line, validate_policy
from cg_release.versions import resolve_version


@dataclass(frozen=True)
class Snapshot:
    """Inputs bound to exact remote revisions, never from source-branch policy."""

    repository_id: int
    host: str
    slug: str
    actor_id: int
    role: str
    default_branch: str
    source_branch: str
    source_sha: str
    policy_sha: str
    policy_raw: bytes
    history: list[dict]
    occupied: list[str]
    blobs: dict[str, SourceBlob]
    notes: str


@dataclass(frozen=True)
class Proposal:
    """Confirmed-input envelope with pure edits; no reservation or request receipt."""

    version: str
    tag: str
    source_sha: str
    policy_sha: str
    approval_environment: str
    edits: tuple[Edit, ...]
    inputs: dict
    digest: str

    def display(self) -> dict:
        """Return bounded proposal fields, e.g. for one JSON preview event."""
        return {
            **self.inputs,
            "proposal_digest": self.digest,
            "edits": [
                {
                    "path": e.path,
                    "input_digest": e.input_digest,
                    "output_digest": e.output_digest,
                    "projection": e.projection,
                }
                for e in self.edits
            ],
        }


def create_proposal(snapshot: Snapshot, args: argparse.Namespace) -> Proposal:
    """Compute one read-only preview, e.g. from an injected verified snapshot.

    Args:
        snapshot: Exact-input provider snapshot; authority verified at acquisition.
        args: Parsed plan/start inputs.
    Returns:
        Canonical digest and validated edits; no filesystem or provider writes.
    Raises:
        ControllerError: Policy, history, authority, metadata, or version failure.
    """
    try:
        policy = load_record(Policy, snapshot.policy_raw)
    except ValueError:
        raise ControllerError(
            "E_POLICY", "Trusted policy is not valid schema v1."
        ) from None
    validate_policy(policy, repository_id=snapshot.repository_id, host=snapshot.host)
    line = select_line(policy, snapshot.source_branch, args.line)
    try:
        adopted = [
            load_record(HistoricalRelease, canonical_bytes(row))
            for row in snapshot.history
        ]
    except ValueError:
        raise ControllerError(
            "E_HISTORY", "Adopted history does not match its strict schema."
        ) from None
    selected = [row for row in adopted if row.line == line.id]
    version = resolve_version(
        [r.version for r in selected],
        line=line,
        occupied=snapshot.occupied,
        bump=args.bump,
        version=args.version,
        channel=args.channel,
    )
    tag = safe_ref(policy.tag_prefix + version)
    environment = approval_route(
        policy,
        snapshot.source_branch,
        version,
        snapshot.role,
        snapshot.default_branch,
        args.reason,
    )
    sign = args.sign or policy.signing_required
    if sign and not policy.allowed_signing_fingerprints:
        raise ControllerError(
            "E_SIGNING", "Signed tags require a trusted allowlisted fingerprint."
        )
    policy_digest = hashlib.sha256(canonical_bytes(policy)).hexdigest()
    projections = {}
    for adapter in policy.metadata:
        if adapter.kind == "python-project":
            if any(adapter.path not in r.projections for r in selected):
                raise ControllerError(
                    "E_PROJECTION_HISTORY",
                    "Adopted distribution projection history is missing.",
                )
            projections[adapter.path] = [r.projections[adapter.path] for r in selected]
    inputs = {
        "repository_id": snapshot.repository_id,
        "host": snapshot.host,
        "repository_slug": snapshot.slug,
        "requester_id": snapshot.actor_id,
        "source_branch": snapshot.source_branch,
        "source_sha": snapshot.source_sha,
        "policy_sha": snapshot.policy_sha,
        "policy_digest": policy_digest,
        "line": line.id,
        "baseline": sorted(r.version for r in selected),
        "version": version,
        "tag": tag,
        "sign": sign,
        "signing_fingerprints": policy.allowed_signing_fingerprints if sign else [],
        "approval_environment": environment,
        "override_reason": args.reason,
        "requested_bump": args.bump,
        "requested_channel": args.channel,
        "notes_digest": hashlib.sha256(snapshot.notes.encode()).hexdigest(),
        "history_digest": hashlib.sha256(
            canonical_bytes(
                {
                    "history": sorted(snapshot.history, key=lambda r: r["release_id"]),
                    "occupied": sorted(snapshot.occupied),
                }
            )
        ).hexdigest(),
        "publishing_enabled": policy.enabled,
        "submission_available": policy.enabled,
        "command_timeout_seconds": policy.timeouts.start_seconds,
    }
    edits = proposed_edits(
        policy.metadata,
        policy.changelog,
        snapshot.blobs,
        version=version,
        tag=tag,
        line=line.id,
        source_sha=snapshot.source_sha,
        policy_digest=policy_digest,
        request_id="preview-not-submitted",
        notes=snapshot.notes,
        projections_history=projections,
        outputs=[a.path for a in policy.build.artifacts],
    )
    if policy.gpid_profile:
        from cg_release.hooks import selected_profile

        profile = selected_profile(policy)
        if not set(profile.REQUIRED_FILES).issubset(snapshot.blobs):
            raise ControllerError(
                "E_PROFILE", "Selected profile requires its declared source files."
            )
        inputs["profile_edits"] = [f"releases/{tag}.json", "releases/latest.json"]
        inputs["profile_timestamp"] = (
            "durable submission receipt created_at; preparation-time metadata only"
        )
    digest = hashlib.sha256(
        canonical_bytes(
            {
                "inputs": inputs,
                "edits": [
                    {"path": e.path, "input": e.input_digest, "output": e.output_digest}
                    for e in edits
                ],
            }
        )
    ).hexdigest()
    return Proposal(
        version,
        tag,
        snapshot.source_sha,
        snapshot.policy_sha,
        environment,
        edits,
        inputs,
        digest,
    )


def confirmed_proposal(
    args: argparse.Namespace,
    acquire: Callable[[], Snapshot],
    confirm: Callable[[Proposal], bool],
) -> Proposal:
    """Recompute after confirmation, e.g. with a fake provider and rejecting callback.

    Args:
        args: Parsed start flags; no earlier plan is required.
        acquire: Fresh read-only snapshot function called before and after consent.
        confirm: Displays exact inputs; returns acceptance. --yes is not authority.
    Returns:
        Unchanged confirmed proposal; never a queued request.
    Raises:
        ControllerError: Declined consent or stale/invalid rechecked inputs.
    """
    before = create_proposal(acquire(), args)
    if not confirm(before):
        raise ControllerError(
            "E_DECLINED", "Proposal declined; no submission occurred."
        )
    after = create_proposal(acquire(), args)
    if before.digest != after.digest:
        raise ControllerError(
            "E_STALE_PROPOSAL", "Confirmed inputs changed; run a new explicit start."
        )
    return before


def request_from_proposal(proposal: Proposal, *, nonce: str | None = None) -> Request:
    """Bind a nonce to confirmed inputs, e.g. request_from_proposal(proposal)."""
    values = {
        key: proposal.inputs[key]
        for key in Request.model_fields
        if key not in {"schema_version", "nonce", "proposal_digest"}
    }
    return load_record(
        Request,
        canonical_bytes(
            {
                **values,
                "schema_version": 1,
                "nonce": nonce or secrets.token_hex(16),
                "proposal_digest": proposal.digest,
            }
        ),
    )
