"""Created 2026-08-13. Typed loopback API over canonical evidence state."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ..claims import create_claim, create_evidence
from ..config import RuntimeSettings, validate_loopback_host
from ..errors import PathPolicyError
from ..schemas import (
    ClaimRecord,
    EvidenceRecord,
    EvidenceRelation,
    ReviewEvent,
    ReviewState,
    VerificationStatus,
)
from ..transactions import RevisionConflictError
from ..security import OfflineNetworkGuard
from ..verification.basic import verify_evidence_context
from ..workbench import LocalEvidenceWorkbench


class ScanRequest(BaseModel):
    """Validate one API resource scan request.

    Args:
        path: Project-relative Markdown resource path.
        expected_revision: Optional optimistic aggregate revision.

    Returns:
        A validated scan request.

    Example:
        ``ScanRequest(path="findings.md")``.
    """

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    expected_revision: Optional[int] = Field(default=None, ge=0)


class CandidateRequest(BaseModel):
    """Validate one manually created candidate evidence request.

    Args:
        source_unit_id: Local source unit selected by the researcher.
        statement: Atomic claim statement.
        quote: Verbatim quote to review.
        relation: Evidence relation to the claim.

    Returns:
        A validated candidate request.

    Example:
        ``CandidateRequest(source_unit_id="unit", statement="The rate fell.", quote="The rate fell.")``.
    """

    model_config = ConfigDict(extra="forbid")

    source_unit_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS


class ReviewActionRequest(BaseModel):
    """Validate one evidence review action and optimistic revision.

    Args:
        action: Approve, reject, or flag action.
        expected_revision: Optional optimistic aggregate revision.
        reason: Optional reviewer reason for reject/flag actions.

    Returns:
        A validated review action request.

    Example:
        ``ReviewActionRequest(action="approve", expected_revision=2)``.
    """

    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "reject", "flag"]
    expected_revision: Optional[int] = Field(default=None, ge=0)
    reason: str = ""


class EvidenceAPIService:
    """Coordinate typed API reads and transaction-backed evidence mutations.

    Args:
        workbench: Local workbench owning canonical YAML and derived index.

    Returns:
        An API service object used by FastAPI route closures.

    Example:
        ``service = EvidenceAPIService(workbench)``.
    """

    def __init__(self, workbench: LocalEvidenceWorkbench) -> None:
        """Create an API service over one local workbench.

        Args:
            workbench: Local evidence workbench.

        Returns:
            ``None``; route operations can now use the service.

        Example:
            ``EvidenceAPIService(LocalEvidenceWorkbench(settings))``.
        """
        self.workbench = workbench

    def source_view(self, source_unit_id: str) -> dict[str, object]:
        """Return provenance-rich source context from the derived index.

        Args:
            source_unit_id: Local source-unit identifier.

        Returns:
            Source text, locator, version, parser metadata, and authority marker.

        Raises:
            KeyError: If the source unit is not indexed.

        Example:
            ``service.source_view("source-unit:...")`` supplies review context.
        """
        unit = self.workbench.index.get(source_unit_id)
        if unit is None:
            raise KeyError(source_unit_id)
        return {
            "source_unit_id": unit.source_unit_id,
            "source_version_id": unit.source_version_id,
            "locator": unit.locator.model_dump(mode="json", exclude_none=True),
            "text": unit.text,
            "heading_path": unit.heading_path,
            "unit_type": unit.unit_type,
            "review_required": unit.review_required,
            "parser_metadata": unit.parser_metadata,
            "original_authority": True,
        }

    def create_candidate(self, request: CandidateRequest) -> dict[str, object]:
        """Create and persist a candidate claim/evidence pair transactionally.

        Args:
            request: Validated candidate request.

        Returns:
            Candidate claim/evidence plus operation and revision metadata.

        Raises:
            KeyError: If the source unit is not indexed.
            ValueError: If the claim is not atomic or data is malformed.

        Example:
            ``service.create_candidate(request)`` keeps the record unapproved.
        """
        unit = self.workbench.index.get(request.source_unit_id)
        if unit is None:
            raise KeyError(request.source_unit_id)
        claim = create_claim(
            self._record_id("claim-candidate", request.source_unit_id, request.statement),
            request.statement,
        )
        evidence = create_evidence(
            self._record_id("evidence-candidate", request.source_unit_id, request.quote),
            claim,
            unit,
            request.quote,
            request.relation,
            extraction_method="manual-api",
        )
        evidence_payload = self._read_yaml(
            "evidence-records.yaml",
            {"schema_version": "research-evidence-records-v1", "records": []},
        )
        claim_matrix_name = self.workbench._claim_matrix_name()
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
        expected_revision = self.workbench.store.current_revision()
        with self.workbench.store.transaction(
            expected_revision=expected_revision,
            actor="api",
            action="create-candidate",
        ) as transaction:
            event = ReviewEvent(
                event_id=self._record_id("review", transaction.operation_id, evidence.evidence_id),
                operation_id=transaction.operation_id,
                target_type="evidence",
                target_id=evidence.evidence_id,
                action="candidate",
                actor="api",
                revision=expected_revision + 1,
            )
            history_payload["events"] = [
                *history_payload.get("events", []),
                event.model_dump(mode="json", exclude_none=True),
            ]
            transaction.stage_yaml("evidence-records.yaml", evidence_payload)
            transaction.stage_yaml(claim_matrix_name, claim_payload)
            transaction.stage_yaml("review-history.yaml", history_payload)
            result = transaction.commit()
        return {
            "claim": claim.model_dump(mode="json", exclude_none=True),
            "evidence": evidence.model_dump(mode="json", exclude_none=True),
            "operation_id": result.operation_id,
            "revision": result.revision,
        }

    def review_evidence(
        self,
        evidence_id: str,
        request: ReviewActionRequest,
    ) -> dict[str, object]:
        """Apply approve/reject/flag after independent verification and journal the action.

        Args:
            evidence_id: Canonical evidence identifier.
            request: Validated review action.

        Returns:
            Updated evidence, linked claim, operation, and revision metadata.

        Raises:
            KeyError: If evidence or its claim/source is unknown.
            ValueError: If approval verification cannot reach high confidence.
            RevisionConflictError: If expected revision is stale.

        Example:
            ``service.review_evidence("evidence-1", ReviewActionRequest(action="flag"))``.
        """
        evidence_payload = self._read_yaml("evidence-records.yaml", {"records": []})
        claim_matrix_name = self.workbench._claim_matrix_name()
        claim_payload = self._read_yaml(claim_matrix_name, {"claims": []})
        history_payload = self._read_yaml(
            "review-history.yaml",
            {"schema_version": "research-evidence-history-v1", "events": []},
        )
        evidence = next(
            (EvidenceRecord.model_validate(item) for item in evidence_payload.get("records", []) if item.get("evidence_id") == evidence_id),
            None,
        )
        if evidence is None:
            raise KeyError(evidence_id)
        claim = next(
            (ClaimRecord.model_validate(item) for item in claim_payload.get("claims", []) if evidence_id in item.get("evidence_ids", [])),
            None,
        )
        if claim is None:
            raise KeyError(f"claim for evidence is missing: {evidence_id}")
        unit = self.workbench.index.get(evidence.source_unit_id)
        if unit is None:
            raise KeyError(evidence.source_unit_id)
        if request.action == "approve":
            unit = self.workbench._load_authoritative_unit(unit)
            updated_evidence, verification = verify_evidence_context(
                evidence,
                [unit],
                original_authority_available=True,
                source_hash_matches=True,
            )
            if verification.status != VerificationStatus.VERIFIED_HIGH:
                raise ValueError(f"approval blocked: {verification.reason}")
            updated_evidence.review_state = ReviewState.APPROVED
            claim.review_state = ReviewState.APPROVED
        elif request.action == "reject":
            updated_evidence = evidence.model_copy(
                update={
                    "verification_status": VerificationStatus.REJECTED,
                    "confidence": "low",
                    "review_state": ReviewState.REJECTED,
                    "original_authority_verified": False,
                }
            )
            claim.review_state = ReviewState.REJECTED
        else:
            updated_evidence = evidence.model_copy(
                update={
                    "verification_status": VerificationStatus.FLAGGED_MEDIUM,
                    "confidence": "medium",
                    "review_state": ReviewState.FLAGGED,
                    "original_authority_verified": False,
                }
            )
            claim.review_state = ReviewState.FLAGGED
        evidence_payload["records"] = self._merge_by_id(
            evidence_payload.get("records", []),
            [updated_evidence.model_dump(mode="json", exclude_none=True)],
            "evidence_id",
        )
        claim_payload["claims"] = self._merge_by_id(
            claim_payload.get("claims", []),
            [claim.model_dump(mode="json", exclude_none=True)],
            "claim_id",
        )
        expected_revision = self.workbench.store.current_revision()
        if request.expected_revision is not None:
            expected_revision = request.expected_revision
        with self.workbench.store.transaction(
            expected_revision=expected_revision,
            actor="api",
            action=f"review-{request.action}",
        ) as transaction:
            event = ReviewEvent(
                event_id=self._record_id("review", transaction.operation_id, evidence_id, request.action),
                operation_id=transaction.operation_id,
                target_type="evidence",
                target_id=evidence_id,
                action=request.action,
                actor="api",
                revision=expected_revision + 1,
            )
            history_payload["events"] = [
                *history_payload.get("events", []),
                event.model_dump(mode="json", exclude_none=True),
            ]
            transaction.stage_yaml("evidence-records.yaml", evidence_payload)
            transaction.stage_yaml(claim_matrix_name, claim_payload)
            transaction.stage_yaml("review-history.yaml", history_payload)
            result = transaction.commit()
        return {
            "claim": claim.model_dump(mode="json", exclude_none=True),
            "evidence": updated_evidence.model_dump(mode="json", exclude_none=True),
            "operation_id": result.operation_id,
            "revision": result.revision,
            "verification_reason": (
                "exact-normalized-quote-and-locator-match"
                if request.action == "approve"
                else request.reason or request.action
            ),
        }

    def history(self) -> list[dict[str, object]]:
        """Return append-only review events in canonical file order.

        Args:
            None.

        Returns:
            Review event mappings.

        Example:
            ``service.history()`` supplies the review-history view.
        """
        return self._read_yaml("review-history.yaml", {"events": []}).get("events", [])

    def _read_yaml(self, name: str, default: dict[str, object]) -> dict[str, object]:
        """Read one canonical mapping through the workbench's evidence root."""
        return self.workbench._read_yaml(name, default)

    @staticmethod
    def _merge_by_id(
        existing: list[dict[str, object]],
        additions: list[dict[str, object]],
        key: str,
    ) -> list[dict[str, object]]:
        """Merge canonical records by stable ID in deterministic order."""
        merged = {str(item[key]): item for item in existing if key in item}
        merged.update({str(item[key]): item for item in additions if key in item})
        return [merged[item_id] for item_id in sorted(merged)]

    @staticmethod
    def _record_id(prefix: str, *parts: str) -> str:
        """Derive a stable API record ID from ordered parts."""
        import hashlib

        return f"{prefix}:" + hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def create_app(settings: RuntimeSettings, *, bind_host: str = "127.0.0.1") -> FastAPI:
    """Create a loopback-only FastAPI application over local canonical evidence state.

    Args:
        settings: Validated project/resource/offline runtime settings.
        bind_host: Literal loopback host; remote bind addresses are rejected.

    Returns:
        A FastAPI application with typed local evidence routes.

    Raises:
        ValueError: If ``bind_host`` is not loopback-only.

    Example:
        ``app = create_app(settings)`` creates the local service boundary.
    """
    validate_loopback_host(bind_host)
    workbench = LocalEvidenceWorkbench(settings)
    service = EvidenceAPIService(workbench)
    app = FastAPI(
        title="Compound Research Evidence Workbench",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.service = service

    @app.middleware("http")
    async def offline_network_boundary(request: Request, call_next):
        """Enforce the local-only socket/proxy boundary around each request.

        Args:
            request: Incoming local HTTP request.
            call_next: FastAPI next-handler callable.

        Returns:
            The downstream response produced inside the offline guard.

        Example:
            Every ``/sources/search`` request executes inside this boundary.
        """
        with OfflineNetworkGuard():
            return await call_next(request)

    @app.exception_handler(HTTPException)
    async def structured_http_error(_request: Request, exc: HTTPException) -> JSONResponse:
        """Return typed API errors without a framework-specific nesting layer.

        Args:
            _request: Incoming request supplied by FastAPI.
            exc: HTTP exception raised by a route.

        Returns:
            JSON response preserving structured error fields at the top level.

        Example:
            A revision conflict returns ``{"error": "revision-conflict"}``.
        """
        content = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.get("/health")
    def health() -> dict[str, object]:
        """Return local service status and canonical revision.

        Args:
            None.

        Returns:
            Active status and aggregate revision.

        Example:
            ``GET /health`` returns a local status payload.
        """
        return {"status": "active", "revision": service.workbench.store.current_revision()}

    @app.post("/resources/scan")
    def scan(request: ScanRequest) -> dict[str, object]:
        """Scan a confined Markdown resource through a transaction.

        Args:
            request: Validated scan request.

        Returns:
            Parsed units and resulting canonical revision.

        Example:
            ``POST /resources/scan`` with ``{"path":"findings.md"}``.
        """
        try:
            parsed = service.workbench.scan_markdown(
                request.path,
                expected_revision=request.expected_revision,
            )
        except RevisionConflictError as error:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "revision-conflict",
                    "expected_revision": error.expected,
                    "actual_revision": error.actual,
                    "conflict_path": str(error.conflict_path),
                },
            ) from error
        except (PathPolicyError, ValueError, OSError) as error:
            raise HTTPException(status_code=400, detail={"error": str(error)}) from error
        return {
            "revision": service.workbench.store.current_revision(),
            "resource": parsed.resource.model_dump(mode="json", exclude_none=True),
            "source_version": parsed.source_version.model_dump(mode="json", exclude_none=True),
            "units": [unit.model_dump(mode="json", exclude_none=True) for unit in parsed.units],
        }

    @app.get("/sources/search")
    def search(q: str, limit: int = 20) -> dict[str, object]:
        """Search local source units without external retrieval.

        Args:
            q: Lexical query.
            limit: Positive result limit.

        Returns:
            Provenance-rich matching source units.

        Example:
            ``GET /sources/search?q=weighted``.
        """
        try:
            results = service.workbench.search(q, limit)
        except ValueError as error:
            raise HTTPException(status_code=400, detail={"error": str(error)}) from error
        return {"results": [service.source_view(unit.source_unit_id) for unit in results]}

    @app.get("/sources/{source_unit_id}")
    def source_context(source_unit_id: str) -> dict[str, object]:
        """Return one source unit's local context and provenance.

        Args:
            source_unit_id: Source-unit identifier.

        Returns:
            Source context and authority metadata.

        Example:
            ``GET /sources/source-unit:...``.
        """
        try:
            return service.source_view(source_unit_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail={"error": "source-not-found"}) from error

    @app.post("/evidence/candidates")
    def candidate(request: CandidateRequest) -> dict[str, object]:
        """Create one candidate evidence record through canonical YAML transaction.

        Args:
            request: Candidate evidence request.

        Returns:
            Candidate claim/evidence and revision.

        Example:
            ``POST /evidence/candidates`` creates a review candidate.
        """
        try:
            return service.create_candidate(request)
        except KeyError as error:
            raise HTTPException(status_code=404, detail={"error": "source-not-found"}) from error
        except (ValueError, TypeError) as error:
            raise HTTPException(status_code=400, detail={"error": str(error)}) from error

    @app.post("/review/evidence/{evidence_id}")
    def review(evidence_id: str, request: ReviewActionRequest) -> dict[str, object]:
        """Apply one typed evidence review action through a journaled mutation.

        Args:
            evidence_id: Evidence identifier.
            request: Approve/reject/flag action.

        Returns:
            Updated evidence, claim, history operation, and revision.

        Example:
            ``POST /review/evidence/e1`` with ``{"action":"approve"}``.
        """
        try:
            return service.review_evidence(evidence_id, request)
        except RevisionConflictError as error:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "revision-conflict",
                    "expected_revision": error.expected,
                    "actual_revision": error.actual,
                    "conflict_path": str(error.conflict_path),
                },
            ) from error
        except KeyError as error:
            raise HTTPException(status_code=404, detail={"error": str(error)}) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"error": str(error)}) from error

    @app.get("/review/history")
    def review_history() -> dict[str, object]:
        """Return append-only review history from canonical YAML.

        Args:
            None.

        Returns:
            Review events.

        Example:
            ``GET /review/history`` returns local decision history.
        """
        return {"events": service.history()}

    @app.post("/recovery")
    def recovery() -> dict[str, object]:
        """Run explicit journal recovery for interrupted local mutations.

        Args:
            None.

        Returns:
            Recovery result summaries.

        Example:
            ``POST /recovery`` replays or aborts incomplete operations.
        """
        return {
            "recovered": [
                {"operation_id": item.operation_id, "status": item.status, "reason": item.reason}
                for item in service.workbench.store.recover()
            ]
        }

    @app.get("/run/status")
    def run_status() -> dict[str, object]:
        """Return local run revision and startup recovery state.

        Args:
            None.

        Returns:
            Current revision and recovery summaries.

        Example:
            ``GET /run/status`` returns restart-safe run state.
        """
        return {
            "revision": service.workbench.store.current_revision(),
            "startup_recovery": [
                {"operation_id": item.operation_id, "status": item.status, "reason": item.reason}
                for item in service.workbench.recovery
            ],
        }

    from ..ui.routes import register_ui_routes

    register_ui_routes(app, service)
    return app
