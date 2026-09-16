"""Created 2026-08-12. Tests for dependency/model inventory activation rules."""
from __future__ import annotations

import pytest

from research_evidence.inventory import (
    ActivationStatus,
    DependencyInventoryEntry,
    DependencyModelInventory,
    InventoryValidationError,
)


def _entry(**overrides: object) -> DependencyInventoryEntry:
    """Build a complete local inventory entry for tests."""
    values: dict[str, object] = {
        "id": "pydantic",
        "kind": "package",
        "distribution_source": "https://pypi.org/project/pydantic/",
        "exact_version_or_revision": "2.12.0",
        "sha256": None,
        "license_or_access_terms": "MIT",
        "restriction": "",
        "setup_network_required": True,
        "runtime_network_required": False,
        "telemetry_notes": "No telemetry known.",
        "platform_support": ["macos", "windows", "linux"],
        "enterprise_review_status": "unreviewed",
        "selection_rationale": "Strict runtime schemas.",
        "caveat_disclaimer": "Not enterprise-approved by this inventory.",
        "activation_status": ActivationStatus.ENABLED_LOCAL,
        "activation_acknowledged": False,
    }
    values.update(overrides)
    return DependencyInventoryEntry.model_validate(values)


def test_complete_local_entry_is_selectable() -> None:
    """Allow a complete non-restricted dependency to be selected."""
    inventory = DependencyModelInventory(entries=[_entry()])
    assert inventory.selectable("pydantic").activation_status == ActivationStatus.ENABLED_LOCAL


def test_restricted_entry_requires_caveat_and_acknowledgement() -> None:
    """Block restricted activation until caveat and local acknowledgement exist."""
    with pytest.raises(InventoryValidationError, match="caveat"):
        _entry(
            id="restricted-model",
            kind="model",
            restriction="Research-only access",
            caveat_disclaimer="",
            activation_status=ActivationStatus.ENABLED_WITH_CAVEAT,
            activation_acknowledged=False,
        )

    with pytest.raises(InventoryValidationError, match="acknowledgement"):
        _entry(
            id="restricted-model",
            kind="model",
            restriction="Research-only access",
            activation_status=ActivationStatus.ENABLED_WITH_CAVEAT,
            activation_acknowledged=False,
        )


def test_candidate_and_blocked_entries_cannot_run() -> None:
    """Keep candidate and blocked entries visible but non-selectable."""
    inventory = DependencyModelInventory(
        entries=[
            _entry(id="candidate", activation_status=ActivationStatus.CANDIDATE),
            _entry(id="blocked", activation_status=ActivationStatus.BLOCKED),
        ]
    )
    with pytest.raises(InventoryValidationError, match="not selectable"):
        inventory.selectable("candidate")
    with pytest.raises(InventoryValidationError, match="not selectable"):
        inventory.selectable("blocked")


def test_duplicate_inventory_ids_are_rejected() -> None:
    """Reject duplicate IDs because activation references must be unambiguous."""
    with pytest.raises(ValueError, match="unique"):
        DependencyModelInventory(entries=[_entry(), _entry()])
