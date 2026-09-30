"""Created 2026-08-12. Dependency and model activation inventory schemas."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .errors import InventoryValidationError


class ActivationStatus(str, Enum):
    """Represent whether an inventory component may run locally.

    Args:
        value: Serialized activation state.

    Returns:
        A validated activation status.

    Example:
        ``ActivationStatus.CANDIDATE`` keeps an evaluated option inactive.
    """

    CANDIDATE = "candidate"
    ENABLED_LOCAL = "enabled-local"
    ENABLED_WITH_CAVEAT = "enabled-with-caveat"
    BLOCKED = "blocked"


class DependencyKind(str, Enum):
    """Classify an inventory item by package, executable, model, or weights.

    Args:
        value: Serialized component kind.

    Returns:
        A validated inventory kind.

    Example:
        ``DependencyKind.PACKAGE`` identifies a Python dependency.
    """

    PACKAGE = "package"
    EXECUTABLE = "executable"
    MODEL = "model"
    WEIGHTS = "weights"


class EnterpriseReviewStatus(str, Enum):
    """Record the organization-level review state without implying approval.

    Args:
        value: Serialized review state.

    Returns:
        A validated enterprise-review status.

    Example:
        ``EnterpriseReviewStatus.UNREVIEWED`` is the default for new entries.
    """

    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class DependencyInventoryEntry(BaseModel):
    """Describe one dependency, executable, model, or weight distribution.

    Args:
        id: Stable inventory identifier.
        kind: Component category.
        distribution_source: Setup-time registry or repository source.
        exact_version_or_revision: Exact package version or model revision.
        sha256: Stable distribution hash when available.
        license_or_access_terms: License or access restrictions.
        restriction: Human-readable restriction, if any.
        setup_network_required: Whether explicit setup may require a network.
        runtime_network_required: Whether normal processing requires a network.
        telemetry_notes: Declared or unverified telemetry behavior.
        platform_support: Supported operating-system labels.
        enterprise_review_status: Review state in this inventory.
        selection_rationale: Reason the component is retained.
        caveat_disclaimer: Visible caveat for users.
        activation_status: Candidate, enabled, or blocked state.
        activation_acknowledged: Explicit local acknowledgement for caveated use.

    Returns:
        A validated inventory entry.

    Example:
        ``DependencyInventoryEntry.model_validate({...})`` validates a record.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: DependencyKind
    distribution_source: str = Field(min_length=1)
    exact_version_or_revision: str = Field(min_length=1)
    sha256: Optional[str] = None
    license_or_access_terms: str = Field(min_length=1)
    restriction: str = ""
    setup_network_required: bool
    runtime_network_required: bool
    telemetry_notes: str = Field(min_length=1)
    platform_support: list[str] = Field(min_length=1)
    enterprise_review_status: EnterpriseReviewStatus
    selection_rationale: str = Field(min_length=1)
    caveat_disclaimer: str = ""
    activation_status: ActivationStatus = ActivationStatus.CANDIDATE
    activation_acknowledged: bool = False

    @model_validator(mode="after")
    def validate_activation(self) -> "DependencyInventoryEntry":
        """Enforce caveat and acknowledgement rules for activation.

        Args:
            self: Entry being validated.

        Returns:
            The validated entry.

        Raises:
            InventoryValidationError: If restrictions and activation metadata conflict.

        Example:
            ``entry.validate_activation()`` returns the same safe entry.
        """
        restricted = bool(self.restriction.strip()) or self.enterprise_review_status in {
            EnterpriseReviewStatus.RESTRICTED,
            EnterpriseReviewStatus.BLOCKED,
        }
        if self.runtime_network_required:
            raise InventoryValidationError(
                f"Inventory entry {self.id!r} requires runtime network access."
            )
        if self.activation_status == ActivationStatus.ENABLED_LOCAL and restricted:
            raise InventoryValidationError(
                f"Restricted entry {self.id!r} cannot use enabled-local status."
            )
        if self.activation_status == ActivationStatus.ENABLED_WITH_CAVEAT:
            if not self.caveat_disclaimer.strip():
                raise InventoryValidationError(
                    f"Enabled-with-caveat entry {self.id!r} requires a caveat."
                )
            if not self.activation_acknowledged:
                raise InventoryValidationError(
                    f"Enabled-with-caveat entry {self.id!r} requires local acknowledgement."
                )
        if self.activation_status == ActivationStatus.ENABLED_LOCAL and not self.activation_acknowledged:
            if not self.caveat_disclaimer.strip():
                raise InventoryValidationError(
                    f"Enabled-local entry {self.id!r} requires complete metadata."
                )
        if self.enterprise_review_status == EnterpriseReviewStatus.BLOCKED:
            raise InventoryValidationError(f"Blocked entry {self.id!r} cannot be activated.")
        return self


class DependencyModelInventory(BaseModel):
    """Store a uniquely keyed set of dependency and model entries.

    Args:
        entries: Inventory entries to validate and expose.
        schema_version: Version of the inventory serialization contract.

    Returns:
        A validated inventory collection.

    Example:
        ``DependencyModelInventory(entries=[entry])`` creates an inventory.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "research-evidence-inventory-v1"
    entries: list[DependencyInventoryEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "DependencyModelInventory":
        """Reject duplicate IDs so activation references remain deterministic.

        Args:
            self: Inventory being validated.

        Returns:
            The validated inventory.

        Raises:
            ValueError: If two entries share an ID.

        Example:
            ``inventory.validate_unique_ids()`` returns a unique inventory.
        """
        ids = [entry.id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("Inventory entry IDs must be unique.")
        return self

    def selectable(self, entry_id: str) -> DependencyInventoryEntry:
        """Return an entry that is explicitly enabled for local execution.

        Args:
            entry_id: Stable inventory identifier to select.

        Returns:
            The enabled local or caveated entry.

        Raises:
            InventoryValidationError: If the entry is missing or inactive.

        Example:
            ``inventory.selectable("pydantic")`` returns the active entry.
        """
        matches = [entry for entry in self.entries if entry.id == entry_id]
        if not matches:
            raise InventoryValidationError(f"Inventory entry {entry_id!r} was not found.")
        entry = matches[0]
        if entry.activation_status not in {
            ActivationStatus.ENABLED_LOCAL,
            ActivationStatus.ENABLED_WITH_CAVEAT,
        }:
            raise InventoryValidationError(
                f"Inventory entry {entry_id!r} is not selectable in status "
                f"{entry.activation_status.value!r}."
            )
        return entry

    def to_yaml(self) -> str:
        """Serialize the inventory deterministically as readable YAML.

        Args:
            None.

        Returns:
            Sorted-key YAML text ending with a newline.

        Example:
            ``inventory.to_yaml()`` produces a diffable canonical record.
        """
        return yaml.safe_dump(
            self.model_dump(mode="json"),
            sort_keys=True,
            allow_unicode=False,
        )


def load_inventory(path: Path) -> DependencyModelInventory:
    """Load and validate an inventory YAML file.

    Args:
        path: Local inventory file path.

    Returns:
        A validated dependency/model inventory.

    Raises:
        InventoryValidationError: If the file is absent or malformed.

    Example:
        ``load_inventory(Path("dependency-model-inventory.yaml"))``.
    """
    try:
        payload: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        return DependencyModelInventory.model_validate(payload or {})
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise InventoryValidationError(f"Unable to load inventory {path}: {error}") from error
