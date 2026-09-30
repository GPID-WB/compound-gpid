"""Bounded strict JSON decoding shared by transport and journal verification."""

import json
import math

from cg_release.events import ControllerError


def decode_json(raw: str) -> object:
    """Decode without duplicates, e.g. decode_json('{}'); reject input leaks.

    Args: raw is UTF-8-decoded API or metadata JSON, limited to 4 MiB.
    Returns: JSON value whose shape still requires validation.
    Raises: ControllerError for malformed or oversized data.
    """

    return _decode(raw, 4 * 1024 * 1024)


def _decode(raw: str, max_bytes: int) -> object:
    """Shared strict decoder; only fixed-capacity protocol decoders call this."""

    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject(_value: str) -> None:
        raise ValueError

    def finite(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError
        return number

    try:
        if len(raw.encode("utf-8")) > max_bytes:
            raise ValueError
        return json.loads(
            raw, object_pairs_hook=unique, parse_constant=reject, parse_float=finite
        )
    except (ValueError, RecursionError, UnicodeError):
        raise ControllerError(
            "E_RESPONSE", "Invalid or oversized JSON response."
        ) from None
