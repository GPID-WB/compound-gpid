"""Validate JSON, then replace only one string token without numeric conversion."""

import json
import re

from cg_release.events import ControllerError


def edit_json_string(raw: str, pointer: str | None, version: str) -> str:
    """Replace a declared string, e.g. edit_json_string(raw, '/version', '1.2.0').

    Args:
        raw: Bounded UTF-8 JSON text, including its original formatting.
        pointer: Exact RFC 6901 pointer to an existing string field.
        version: Replacement version string, already validated as SemVer.
    Returns:
        Text with only the selected JSON string token replaced. All other bytes,
        including decimal/exponent lexemes and escaped strings, remain unchanged.
    Raises:
        ControllerError: Invalid/ambiguous JSON or a missing/non-string target.
    """
    if not pointer or not pointer.startswith("/") or re.search(r"~(?![01])", pointer):
        raise ControllerError("E_METADATA", "Expected one valid JSON Pointer.")

    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject(_token: str) -> None:
        raise ValueError

    # JSONDecoder validates numeric grammar; no arithmetic or serialization of
    # numeric values is needed. Keeping lexemes avoids float rounding/overflow.
    decoder = json.JSONDecoder(
        object_pairs_hook=unique, parse_float=str, parse_int=str, parse_constant=reject
    )
    segments = [p.replace("~1", "/").replace("~0", "~") for p in pointer[1:].split("/")]

    def skip(index: int) -> int:
        while index < len(raw) and raw[index] in " \t\r\n":
            index += 1
        return index

    def locate(start: int, remaining: list[str]) -> tuple[int, int]:
        if not remaining:
            _, end = decoder.raw_decode(raw, start)
            if raw[start] != '"':
                raise ValueError
            return start, end
        if raw[start] == "{":
            index = skip(start + 1)
            while raw[index] != "}":
                key, key_end = decoder.raw_decode(raw, index)
                value_start = skip(skip(key_end) + 1)  # Validated colon.
                if key == remaining[0]:
                    return locate(value_start, remaining[1:])
                _, end = decoder.raw_decode(raw, value_start)
                index = skip(end)
                if raw[index] == ",":
                    index = skip(index + 1)
        elif raw[start] == "[" and re.fullmatch(r"0|[1-9][0-9]*", remaining[0]):
            target, count, index = int(remaining[0]), 0, skip(start + 1)
            while raw[index] != "]":
                if count == target:
                    return locate(index, remaining[1:])
                _, end = decoder.raw_decode(raw, index)
                index, count = skip(end), count + 1
                if raw[index] == ",":
                    index = skip(index + 1)
        raise ValueError

    try:
        _, end = decoder.raw_decode(raw, skip(0))
        if skip(end) != len(raw):
            raise ValueError
        start, end = locate(skip(0), segments)
        return raw[:start] + json.dumps(version, ensure_ascii=True) + raw[end:]
    except (ValueError, TypeError, IndexError, RecursionError):
        raise ControllerError(
            "E_METADATA", "Invalid JSON or missing string version field."
        ) from None
