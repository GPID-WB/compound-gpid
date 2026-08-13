"""Created 2026-08-13. Inventory-gated offline retrieval profile contracts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Mapping, Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..inventory import ActivationStatus, EnterpriseReviewStatus


class ProfileUnavailableError(RuntimeError):
    """Signal an inactive, missing, or unsafe optional retrieval profile.

    Args:
        message: Human-readable capability failure.

    Returns:
        An exception suitable for explicit profile handling.

    Example:
        ``raise ProfileUnavailableError("profile is candidate")``.
    """


class RetrievalProfile(BaseModel):
    """Describe one optional local dense, sparse, or reranking profile.

    Args:
        id: Stable profile identifier.
        kind: Dense, sparse, or reranker profile kind.
        model_id: Model identifier supplied to a local adapter.
        model_revision: Exact model revision or commit.
        package_version: Exact local runtime package version.
        distribution_source: Setup-time source, never a runtime endpoint.
        model_cache_path: Project-relative verified local cache path.
        sha256: Model artifact hash when available.
        license_or_access_terms: License/access terms.
        restriction: Human-readable restriction, if any.
        setup_network_required: Whether explicit setup may need a network.
        runtime_network_required: Whether normal retrieval needs a network.
        telemetry_notes: Declared or unverified telemetry behavior.
        platform_support: Supported operating-system labels.
        hardware_support: Supported device labels.
        deterministic: Whether the profile claims deterministic output.
        query_p95_budget_ms: Declared query latency budget.
        memory_budget_bytes: Declared additional memory budget.
        enterprise_review_status: Organization review state.
        selection_rationale: Reason the profile is retained.
        caveat_disclaimer: Visible caveat for researchers.
        activation_status: Candidate, enabled, or blocked state.
        activation_acknowledged: Local acknowledgement for caveated use.

    Returns:
        A validated profile record.

    Example:
        ``RetrievalProfile.model_validate({"id": "dense", ...})``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: Literal["dense", "sparse", "reranker"]
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    package_version: str = Field(min_length=1)
    distribution_source: str = Field(min_length=1)
    model_cache_path: Optional[str] = None
    sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    license_or_access_terms: str = Field(min_length=1)
    restriction: str = ""
    setup_network_required: bool
    runtime_network_required: bool
    telemetry_notes: str = Field(min_length=1)
    platform_support: list[str] = Field(min_length=1)
    hardware_support: list[str] = Field(min_length=1)
    deterministic: bool
    query_p95_budget_ms: float = Field(gt=0)
    memory_budget_bytes: int = Field(gt=0)
    enterprise_review_status: EnterpriseReviewStatus
    selection_rationale: str = Field(min_length=1)
    caveat_disclaimer: str = Field(min_length=1)
    activation_status: ActivationStatus = ActivationStatus.CANDIDATE
    activation_acknowledged: bool = False

    @model_validator(mode="after")
    def validate_activation_contract(self) -> "RetrievalProfile":
        """Reject runtime network and unsafe activation metadata.

        Args:
            self: Profile being validated.

        Returns:
            The validated profile.

        Raises:
            ValueError: If network or restriction gates are violated.

        Example:
            ``profile.validate_activation_contract()`` returns a safe profile.
        """
        if self.runtime_network_required:
            raise ValueError("retrieval profiles cannot require runtime network access")
        if self.model_cache_path:
            parsed = urlsplit(self.model_cache_path)
            if parsed.scheme or parsed.netloc:
                raise ValueError("retrieval model cache must be a local path")
        restricted = bool(self.restriction.strip()) or self.enterprise_review_status in {
            EnterpriseReviewStatus.RESTRICTED,
            EnterpriseReviewStatus.BLOCKED,
        }
        if self.activation_status == ActivationStatus.ENABLED_LOCAL and restricted:
            raise ValueError("restricted profiles cannot use enabled-local status")
        if self.activation_status == ActivationStatus.ENABLED_WITH_CAVEAT and not self.activation_acknowledged:
            raise ValueError("enabled-with-caveat profiles require acknowledgement")
        if self.enterprise_review_status == EnterpriseReviewStatus.BLOCKED:
            raise ValueError("blocked profiles cannot be activated")
        return self


class RetrievalProfileRegistry(BaseModel):
    """Store uniquely keyed optional profiles before activation.

    Args:
        entries: Profile records to validate.
        schema_version: Profile inventory contract version.

    Returns:
        A validated profile registry.

    Example:
        ``RetrievalProfileRegistry(entries=[profile])`` keeps options explicit.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "research-evidence-retrieval-profiles-v1"
    entries: list[RetrievalProfile] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "RetrievalProfileRegistry":
        """Reject duplicate profile IDs.

        Args:
            self: Registry being validated.

        Returns:
            The unique registry.

        Raises:
            ValueError: If IDs are duplicated.

        Example:
            ``registry.validate_unique_ids()`` returns a safe registry.
        """
        ids = [entry.id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("Retrieval profile IDs must be unique")
        return self

    def selectable(self, profile_id: str, project_root: Path) -> RetrievalProfile:
        """Return an active profile with an existing project-local model cache.

        Args:
            profile_id: Stable profile identifier.
            project_root: Project root containing the verified model cache.

        Returns:
            An enabled local or caveated profile.

        Raises:
            ProfileUnavailableError: If inactive, missing, or path-unsafe.

        Example:
            ``registry.selectable("dense", project_root)`` gates execution.
        """
        matches = [entry for entry in self.entries if entry.id == profile_id]
        if not matches:
            raise ProfileUnavailableError(f"retrieval profile not found: {profile_id}")
        profile = matches[0]
        if profile.activation_status not in {
            ActivationStatus.ENABLED_LOCAL,
            ActivationStatus.ENABLED_WITH_CAVEAT,
        }:
            raise ProfileUnavailableError(
                f"retrieval profile {profile_id!r} is {profile.activation_status.value}, not active"
            )
        if not profile.model_cache_path:
            raise ProfileUnavailableError(f"retrieval profile {profile_id!r} has no model cache")
        root = Path(project_root).resolve()
        cache = (root / profile.model_cache_path).resolve()
        if not cache.is_relative_to(root) or not cache.is_dir():
            raise ProfileUnavailableError(
                f"retrieval profile {profile_id!r} local model cache is unavailable"
            )
        return profile


@dataclass(frozen=True)
class ProfileBudgetEvaluation:
    """Capture whether measured optional-profile budgets were met.

    Args:
        profile_id: Profile evaluated.
        passed: Whether all declared budgets passed.
        metrics: Measured latency and memory metrics.
        resulting_activation_status: Candidate or eligible status after evaluation.

    Returns:
        An immutable profile-gate result.

    Example:
        ``evaluation.resulting_activation_status`` prevents failed promotion.
    """

    profile_id: str
    passed: bool
    metrics: dict[str, float | int]
    resulting_activation_status: str


@dataclass(frozen=True)
class RankedCandidate:
    """Represent one deterministic scored retrieval candidate.

    Args:
        source_unit_id: Source-unit identifier.
        score: Adapter-produced relevance score.

    Returns:
        An immutable ranked candidate.

    Example:
        ``RankedCandidate("unit-1", 0.8)`` is safe to serialize.
    """

    source_unit_id: str
    score: float


def load_local_profile(
    registry: RetrievalProfileRegistry,
    profile_id: str,
    project_root: Path,
    loader: Callable[..., object],
) -> object:
    """Load an enabled model through a strictly local-cache-only adapter.

    Args:
        registry: Inventory-controlled profile registry.
        profile_id: Profile to load.
        project_root: Project root containing the verified cache.
        loader: Injected local adapter callable.

    Returns:
        Adapter-loaded model object.

    Raises:
        ProfileUnavailableError: If profile activation/cache gates fail.

    Example:
        ``load_local_profile(registry, "dense", root, loader)``.
    """
    profile = registry.selectable(profile_id, project_root)
    cache = (Path(project_root).resolve() / profile.model_cache_path).resolve()
    return loader(
        model_id=profile.model_id,
        revision=profile.model_revision,
        cache_dir=str(cache),
        local_files_only=True,
    )


def evaluate_profile_budget(
    profile: RetrievalProfile,
    metrics: Mapping[str, float | int],
) -> ProfileBudgetEvaluation:
    """Evaluate declared latency/memory budgets without promoting on failure.

    Args:
        profile: Optional profile with declared resource budgets.
        metrics: Measured ``p95_query_ms`` and ``memory_bytes`` values.

    Returns:
        Evaluation whose failed result remains candidate status.

    Example:
        ``evaluate_profile_budget(profile, {"p95_query_ms": 100.0, "memory_bytes": 1})``.
    """
    query_ms = float(metrics.get("p95_query_ms", float("inf")))
    memory_bytes = int(metrics.get("memory_bytes", 2**63 - 1))
    passed = query_ms <= profile.query_p95_budget_ms and memory_bytes <= profile.memory_budget_bytes
    return ProfileBudgetEvaluation(
        profile_id=profile.id,
        passed=passed,
        metrics=dict(metrics),
        resulting_activation_status=(
            profile.activation_status.value if passed else ActivationStatus.CANDIDATE.value
        ),
    )


def _rank_scores(
    units: list[object],
    scores: Mapping[str, float],
) -> list[RankedCandidate]:
    """Sort adapter scores deterministically without interpreting source text."""
    candidates = [
        RankedCandidate(unit.source_unit_id, float(scores[unit.source_unit_id]))
        for unit in units
        if unit.source_unit_id in scores
    ]
    return sorted(candidates, key=lambda item: (-item.score, item.source_unit_id))
