"""Strict reviewed recovery directives and permanent journal audit records."""

from typing import Annotated, Literal

from pydantic import Field, model_serializer, model_validator

from cg_release.models import Commit, Digest, Request, StrictRecord, VersionedRecord


class PublicTag(StrictRecord):
    """Public object only. Private signing material is never a recovery input."""

    text: Annotated[str, Field(min_length=1, max_length=16384)]
    oid: Commit
    fingerprint: Annotated[str, Field(pattern=r"(?:[A-F0-9]{40}|[A-F0-9]{64})")] | None


class EvidenceBase(StrictRecord):
    """Explicit reviewed evidence-PR destination for an exceptional GPID recovery."""

    branch: Annotated[
        str,
        Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9][A-Za-z0-9/_.-]*$"),
    ]
    sha: Commit
    created_at: Annotated[
        str, Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
    ]


class RecoveryDirective(VersionedRecord):
    """An exact .release-recovery.json reviewed on the protected default branch."""

    schema_version: Literal[1] = 1
    operation: Literal["journal-restore", "stranded-publication", "source-exception"]
    repository_id: Annotated[int, Field(gt=0)]
    policy_digest: Digest
    reason: Annotated[str, Field(min_length=1, max_length=1024)]
    mirror_head: Commit | None = None
    expected_head: Commit | None = None
    request: Request | None = None
    tag: PublicTag | None = None
    release_tree: Commit | None = None
    release_sha: Commit | None = None
    allow_source_exception: bool = False
    evidence_base: EvidenceBase | None = None

    @model_serializer(mode="wrap")
    def preserve_reviewed_shape(self, serialize):
        """Preserve existing audited digests when no evidence base is selected."""
        value = serialize(self)
        if self.evidence_base is None:
            value.pop("evidence_base", None)
        return value

    @model_validator(mode="after")
    def shape(self):
        """Keep restore and publication directives disjoint."""
        if self.operation == "journal-restore":
            if (
                self.mirror_head is None
                or self.request
                or self.tag
                or self.release_tree
                or self.release_sha
                or self.allow_source_exception
                or self.evidence_base
            ):
                raise ValueError(
                    "restore requires one mirror and no publication inputs"
                )
        elif (
            self.mirror_head
            or self.expected_head
            or self.request is None
            or self.tag is None
            or self.release_tree is None
            or self.release_sha is None
        ):
            raise ValueError(
                "publication recovery requires exact request, tag and tree"
            )
        if not self.reason.strip():
            raise ValueError("recovery requires a nonempty reason")
        if (
            self.request is not None
            and self.request.repository_id != self.repository_id
        ):
            raise ValueError("recovery cannot mix repository identities")
        return self


class RecoveryAudit(VersionedRecord):
    """Durable recovery execution, separate from reservations and queue state."""

    schema_version: Literal[1] = 1
    kind: Literal["recovery"] = "recovery"
    directive: RecoveryDirective
    directive_digest: Digest
    policy_sha: Commit
    actor_id: Annotated[int, Field(gt=0)]
    run_id: Annotated[int, Field(gt=0)]


def event_model(value):
    """Select a supported journal type, e.g. event_model(event['record'])."""
    from cg_release.composition_journal import Composition
    from cg_release.journal_models import Record
    from cg_release.queue import QueueCursor

    return {
        "queue": QueueCursor,
        "recovery": RecoveryAudit,
        "composition": Composition,
    }.get(value.get("kind"), Record)
