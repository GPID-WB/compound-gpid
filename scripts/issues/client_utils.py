"""JSON-shape helpers shared by live and fixture readiness clients."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def expect_mapping(value: Any, label: str, error_type: type[Exception]) -> Mapping[str, Any]:
    """Require a JSON object and raise the supplied domain error otherwise."""
    if not isinstance(value, Mapping):
        raise error_type(
            f"malformed {label}: expected object, got {type(value).__name__}"
        )
    return value


def require_int(value: Any, label: str, error_type: type[Exception]) -> int:
    """Require a JSON integer without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise error_type(f"malformed {label}: expected integer")
    return value


def require_string(
    value: Any,
    label: str,
    error_type: type[Exception],
    *,
    default: str = "",
    allow_none: bool = True,
) -> str:
    """Require a string field, optionally treating ``null`` as empty."""
    if value is None and allow_none:
        return default
    if not isinstance(value, str):
        raise error_type(f"malformed {label}: expected string")
    return value


def normalize_objects(
    value: Any,
    field: str,
    label: str,
    error_type: type[Exception],
) -> list[str]:
    """Normalize a list of objects containing one required string field."""
    if not isinstance(value, list):
        raise error_type(f"malformed {label}: expected list")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise error_type(f"malformed {label}: each item must be an object")
        field_value = item.get(field)
        if not isinstance(field_value, str):
            raise error_type(f"malformed {label}: {field} must be a string")
        normalized.append(field_value)
    return normalized
