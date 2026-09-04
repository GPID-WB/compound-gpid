"""Created 2026-08-12. Thin local Markdown evidence-loop coordinator."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import yaml

from .claims import create_claim, create_evidence
from .config import RuntimeSettings
from .identity import sha256_file
from .index.lexical import LexicalIndex
from .schemas import (
    ClaimRecord,
    EvidenceRecord,
    EvidenceRelation,
    ReviewState,
    ReviewEvent,
    is_approved_evidence,
)
from .source_records import ParsedMarkdownResource, ingest_markdown_resource
from .parsers.markdown import parse_markdown
from .transactions import ArtifactStore, RecoveryResult
from .verification.basic import verify_evidence


@dataclass(frozen=True)
class DecisionResult:
    """Return the approved claim/evidence decision and commit metadata.

    Args:
        claim: Persisted approved claim.
        evidence: Persisted verified evidence.
        operation_id: Journal transaction operation ID.
        revision: Aggregate revision after commit.

    Returns:
        An immutable thin-loop decision result.

    Example:
        ``decision.revision`` identifies the canonical state version.
    """

    claim: ClaimRecord
    evidence: EvidenceRecord
    operation_id: str
    revision: int


@dataclass(frozen=True)
class ApprovedDecision:
    """Pair one approved claim with its eligible evidence after restart.

    Args:
        claim: Approved atomic claim.
        evidence: Original-verified supporting evidence.

    Returns:
        An immutable decision view.

    Example:
        ``approved.evidence.source_unit_id`` locates its source context.
    """

    claim: ClaimRecord
    evidence: EvidenceRecord


class LocalEvidenceWorkbench:
    """Coordinate local Markdown ingestion, search, verification, and persistence.

    Args:
        settings: Validated project/resource/offline runtime settings.

    Returns:
        A local workbench backed by canonical YAML and a derived SQLite index.

    Example:
        ``workbench = LocalEvidenceWorkbench(settings)``.
    """

    def __init__(self, settings: RuntimeSettings) -> None:
        """Open canonical state, recover interrupted writes, and open the index.

        Args:
            settings: Runtime settings for the local project.

        Returns:
            ``None``; the workbench is ready for scan/search/review.

        Example:
            ``LocalEvidenceWorkbench(settings)`` starts a restart-safe session.
        """
        self.settings = settings
        self.store = ArtifactStore(settings.evidence_root)
        self.recovery: list[RecoveryResult] = self.store.recover()
        self.index = LexicalIndex(settings.evidence_root / "index" / "lexical.sqlite")

    def scan_markdown(
        self,
        relative_path: str,
        *,
        expected_revision: int | None = None,
    ) -> ParsedMarkdownResource:
        """Ingest one Markdown resource and update canonical source records/index.

        Args:
            relative_path: Resource path relative to the configured resources root.
            expected_revision: Optional aggregate revision read by the caller.

        Returns:
            Parsed resource bundle containing source units for search and review.

        Raises:
            ValueError: If the selected resource is not Markdown.

        Example:
            ``workbench.scan_markdown("findings.md")``.
        """
        parsed = ingest_markdown_resource(self.settings, relative_path)
        source_records = self._read_yaml(
            "source-records.yaml",
            {
                "schema_version": "research-evidence-source-records-v1",
                "resources": [],
                "source_versions": [],
                "source_units": [],
            },
        )
        previous_version_ids = {
            item.get("source_version_id")
            for item in source_records.get("source_versions", [])
            if item.get("resource_id") == parsed.resource.resource_id
            and item.get("source_version_id") != parsed.source_version.source_version_id
        }
        source_records["resources"] = self._merge_by_id(
            source_records.get("resources", []),
            [parsed.resource.model_dump(mode="json", exclude_none=True)],
            "resource_id",
        )
        source_records["source_versions"] = self._merge_by_id(
            source_records.get("source_versions", []),
            [parsed.source_version.model_dump(mode="json", exclude_none=True)],
            "source_version_id",
        )
        source_records["source_units"] = self._merge_by_id(
            source_records.get("source_units", []),
            [unit.model_dump(mode="json", exclude_none=True) for unit in parsed.units],
            "source_unit_id",
        )
        evidence_payload = self._read_yaml(
            "evidence-records.yaml",
            {"schema_version": "research-evidence-records-v1", "records": []},
        )
        claim_matrix_name = self._claim_matrix_name()
        claim_payload = self._read_yaml(
            claim_matrix_name,
            {"schema_version": "research-evidence-matrix-v1", "claims": []},
        )
        analysis_payload = self._read_yaml(
            "analysis-links.yaml",
            {"schema_version": "research-evidence-analysis-links-v1", "analysis_links": []},
        )
        stale_evidence_ids: set[str] = set()
        if previous_version_ids:
            for record in evidence_payload.get("records", []):
                if record.get("source_version_id") in previous_version_ids:
                    record.update(
                        {
                            "stale": True,
                            "review_state": "stale",
                            "verification_status": "stale",
                            "original_authority_verified": False,
                        }
                    )
                    stale_evidence_ids.add(str(record.get("evidence_id")))
            stale_claim_ids: set[str] = set()
            for claim in claim_payload.get("claims", []):
                if stale_evidence_ids.intersection(claim.get("evidence_ids", [])):
                    claim.update({"stale": True, "review_state": "stale"})
                    stale_claim_ids.add(str(claim.get("claim_id")))
            for link in analysis_payload.get("analysis_links", []):
                if link.get("claim_id") in stale_claim_ids:
                    link["active"] = False
        with self.store.transaction(
            expected_revision=(
                self.store.current_revision()
                if expected_revision is None
                else expected_revision
            ),
            actor="researcher",
            action="scan-markdown",
        ) as transaction:
            transaction.stage_yaml("source-records.yaml", source_records)
            if stale_evidence_ids:
                transaction.stage_yaml("evidence-records.yaml", evidence_payload)
                transaction.stage_yaml(claim_matrix_name, claim_payload)
                transaction.stage_yaml("analysis-links.yaml", analysis_payload)
                transaction.mark_derived_stale(
                    "index/lexical.sqlite",
                    "source rescan invalidated downstream evidence",
                )
            transaction.commit()
        self.index.upsert(parsed.units)
        return parsed

    def search(self, query: str, limit: int = 20) -> list[Any]:
        """Search derived local source units with deterministic lexical ranking.

        Args:
            query: Lexical search text.
            limit: Maximum result count.

        Returns:
            Matching source units.

        Example:
            ``workbench.search("weighted poverty")`` returns review candidates.
        """
        return self.index.search(query, limit)

    def create_and_verify(
        self,
        source_unit_id: str,
        claim_statement: str,
        quote: str,
        relation: EvidenceRelation | str = EvidenceRelation.SUPPORTS,
    ) -> DecisionResult:
        """Create, exactly verify, approve, and journal one manual decision.

        Args:
            source_unit_id: Selected source-unit identifier.
            claim_statement: One atomic claim statement.
            quote: Verbatim quote selected from the source unit.
            relation: Supports, contradicts, or contextualizes relation.

        Returns:
            Committed approved claim/evidence decision.

        Raises:
            KeyError: If the source unit is not in the local index.
            ValueError: If exact original-authority verification fails.

        Example:
            ``workbench.create_and_verify(unit_id, "The rate fell.", "The rate fell.")``.
        """
        source_unit = self.index.get(source_unit_id)
        if source_unit is None:
            raise KeyError(f"Source unit is not indexed: {source_unit_id}")
        source_unit = self._load_authoritative_unit(source_unit)
        claim_id = self._record_id("claim", claim_statement, source_unit_id)
        evidence_id = self._record_id("evidence", quote, source_unit_id)
        claim = create_claim(claim_id, claim_statement)
        evidence = create_evidence(evidence_id, claim, source_unit, quote, relation)
        evidence, verification = verify_evidence(
            evidence,
            source_unit,
            original_authority=True,
        )
        if verification.status.value != "verified-high":
            raise ValueError(f"Evidence verification failed: {verification.reason}")
        claim.review_state = ReviewState.APPROVED
        evidence.review_state = ReviewState.APPROVED
        evidence_payload = self._read_yaml(
            "evidence-records.yaml",
            {"schema_version": "research-evidence-records-v1", "records": []},
        )
        claim_matrix_name = self._claim_matrix_name()
        claim_payload = self._read_yaml(
            claim_matrix_name,
            {"schema_version": "research-evidence-matrix-v1", "claims": []},
        )
        history_payload = self._read_yaml(
            "review-history.yaml",
            {"schema_version": "research-evidence-history-v1", "events": []},
        )
        evidence_payload["records"] = self._merge_by_id(
            evidence_payload.get("records", []),
            [evidence.model_dump(mode="json", exclude_none=True)],
            "evidence_id",
        )
        claim_payload["claims"] = self._merge_by_id(
            claim_payload.get("claims", []),
            [claim.model_dump(mode="json", exclude_none=True)],
            "claim_id",
        )
        expected_revision = self.store.current_revision()
        with self.store.transaction(
            expected_revision=expected_revision,
            actor="researcher",
            action="approve-evidence",
        ) as transaction:
            next_revision = expected_revision + 1
            event = ReviewEvent(
                event_id=self._record_id("review", transaction.operation_id, evidence_id),
                operation_id=transaction.operation_id,
                target_type="evidence",
                target_id=evidence.evidence_id,
                action="approve",
                actor="researcher",
                revision=next_revision,
            )
            history_payload["events"] = [
                *history_payload.get("events", []),
                event.model_dump(mode="json", exclude_none=True),
            ]
            transaction.stage_yaml("evidence-records.yaml", evidence_payload)
            transaction.stage_yaml(claim_matrix_name, claim_payload)
            transaction.stage_yaml("review-history.yaml", history_payload)
            result = transaction.commit()
        return DecisionResult(claim, evidence, result.operation_id, result.revision)

    def load_approved_decisions(self) -> list[ApprovedDecision]:
        """Reload approved claim/evidence pairs from canonical YAML state.

        Args:
            None.

        Returns:
            Approved, original-verified decisions that are not stale.

        Example:
            ``workbench.load_approved_decisions()`` supports restart recovery.
        """
        evidence_payload = self._read_yaml("evidence-records.yaml", {"records": []})
        claim_payload = self._read_yaml(self._claim_matrix_name(), {"claims": []})
        evidence_records = {
            record.evidence_id: record
            for record in (
                EvidenceRecord.model_validate(item)
                for item in evidence_payload.get("records", [])
            )
            if is_approved_evidence(record)
        }
        decisions: list[ApprovedDecision] = []
        for item in claim_payload.get("claims", []):
            claim = ClaimRecord.model_validate(item)
            if claim.review_state != ReviewState.APPROVED or claim.stale:
                continue
            for evidence_id in claim.evidence_ids:
                evidence = evidence_records.get(evidence_id)
                if evidence is not None:
                    decisions.append(ApprovedDecision(claim, evidence))
        return decisions

    def close(self) -> None:
        """Close the derived index while leaving canonical YAML untouched.

        Args:
            None.

        Returns:
            ``None`` after the SQLite connection closes.

        Example:
            ``workbench.close()`` ends a local session cleanly.
        """
        self.index.close()

    def _claim_matrix_name(self) -> str:
        """Choose a separate workbench matrix when an existing CR matrix is present.

        Args:
            None.

        Returns:
            The canonical workbench matrix filename.

        Example:
            ``workbench._claim_matrix_name()`` preserves legacy CR rows.
        """
        standard = "claim-evidence-matrix.yaml"
        path = self.settings.evidence_root / standard
        if not path.exists():
            return standard
        payload = self._read_yaml(standard, {})
        claims = payload.get("claims", [])
        if any(
            isinstance(claim, dict)
            and "claim_id" not in claim
            and ("id" in claim or "status" in claim or "evidence" in claim)
            for claim in claims
        ):
            return "workbench-claim-evidence-matrix.yaml"
        return standard

    def _load_authoritative_unit(self, indexed_unit: Any) -> Any:
        """Re-read the original resource and reject stale indexed source text.

        Args:
            indexed_unit: Source unit selected from the derived lexical index.

        Returns:
            The matching source unit parsed from unchanged original bytes.

        Raises:
            ValueError: If canonical source metadata is missing, the file hash
                changed, or the typed unit no longer resolves uniquely.

        Example:
            ``_load_authoritative_unit(indexed_unit)`` gates approval on originals.
        """
        source_records = self._read_yaml("source-records.yaml", {})
        source_version = next(
            (
                item
                for item in source_records.get("source_versions", [])
                if item.get("source_version_id") == indexed_unit.source_version_id
            ),
            None,
        )
        if source_version is None:
            raise ValueError("Source version metadata is missing; rescan before verification.")
        resource = next(
            (
                item
                for item in source_records.get("resources", [])
                if item.get("resource_id") == source_version.get("resource_id")
            ),
            None,
        )
        if resource is None or not resource.get("relative_path"):
            raise ValueError("Source resource metadata is missing; rescan before verification.")
        path = self.settings.validate_resource_path(resource["relative_path"])
        if sha256_file(path) != source_version.get("sha256"):
            raise ValueError("Source version is stale; rescan before verification.")
        current_units = parse_markdown(
            path.read_text(encoding="utf-8"),
            indexed_unit.source_version_id,
        )
        matching_units = [
            unit for unit in current_units if unit.source_unit_id == indexed_unit.source_unit_id
        ]
        if len(matching_units) != 1:
            raise ValueError("Source unit is stale or ambiguous; rescan before verification.")
        return matching_units[0]

    def _read_yaml(self, name: str, default: dict[str, Any]) -> dict[str, Any]:
        """Read one canonical mapping or return a fresh default mapping."""
        path = self.settings.evidence_root / name
        if not path.exists():
            return dict(default)
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Canonical evidence file must be a mapping: {path}")
        return payload

    @staticmethod
    def _merge_by_id(
        existing: list[dict[str, Any]],
        additions: list[dict[str, Any]],
        key: str,
    ) -> list[dict[str, Any]]:
        """Merge records by stable ID while preserving deterministic sort order."""
        merged = {str(item[key]): item for item in existing if key in item}
        merged.update({str(item[key]): item for item in additions if key in item})
        return [merged[item_id] for item_id in sorted(merged)]

    @staticmethod
    def _record_id(prefix: str, *parts: str) -> str:
        """Derive a stable record ID from a prefix and ordered parts."""
        payload = "\x1f".join(parts)
        return f"{prefix}:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
