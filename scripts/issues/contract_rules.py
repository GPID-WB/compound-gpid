"""Deterministic validation rules for the structured readiness contract."""
from __future__ import annotations

import re
from typing import Sequence

from .contract import (
    CHECKBOX_RE,
    CODE_SPAN_RE,
    FEATURE_ID_FORMAT_RE,
    LIST_ITEM_RE,
    REQUIRED_SECTIONS,
    RISK_CLASSES,
    RuleResult,
    _is_overbroad_allowed_path,
    _iter_fence_state,
    _non_fence_lines,
    _section_detail,
    _section_nonempty,
    find_feature_id,
    find_marker,
    parse_sections,
    strip_bom,
    validate_path_entry,
)


def _extract_checkboxes(content_lines: Sequence[str]) -> list[bool]:
    """Extract checked states from checklist items outside fences."""
    boxes: list[bool] = []
    for line in _non_fence_lines(content_lines):
        match = CHECKBOX_RE.match(line)
        if match:
            boxes.append(match.group(1).lower() == "x")
    return boxes


def _extract_path_entries(content_lines: Sequence[str]) -> list[str]:
    """Extract backtick path spans from list items outside fences."""
    entries: list[str] = []
    for line in _non_fence_lines(content_lines):
        match = LIST_ITEM_RE.match(line)
        if match:
            entries.extend(CODE_SPAN_RE.findall(match.group(1)))
    return entries


def _extract_risk_class(content_lines: Sequence[str]) -> str | None:
    """Return a risk token whose whole line is a supported class."""
    for line in _non_fence_lines(content_lines):
        token = line.strip().strip("`").strip().lower()
        if token in RISK_CLASSES:
            return token
    return None


def _has_blocking_dependency(content_lines: Sequence[str]) -> tuple[bool, str]:
    """Return whether an unchecked or non-negated ``blocked by`` item exists."""
    unchecked = re.compile(r"^\s*[-*]\s*\[\s\](?:\s+|$)")
    negation = re.compile(
        r"\b(?:not|cannot|can't|won't|isn't|aren't|wasn't|weren't|"
        r"doesn't|don't|didn't)\s+(?:be\s+)?$",
        re.IGNORECASE,
    )
    for line in _non_fence_lines(content_lines):
        if unchecked.match(line):
            return True, f"unchecked dependency item: {line.strip()}"
        for match in re.finditer(r"\bblocked\s+by\b", line, re.IGNORECASE):
            if negation.search(line[: match.start()]):
                continue
            return True, f"blocking dependency: {line.strip()}"
    return False, ""


def _verification_commands_nonempty(content_lines: Sequence[str]) -> bool:
    """Return whether a section contains a non-empty fenced command block."""
    in_fence = False
    buffer: list[str] = []
    for line, _, opens, closes in _iter_fence_state(content_lines):
        if opens:
            in_fence = True
            buffer = []
        elif in_fence and closes:
            if any(part.strip() for part in buffer):
                return True
            in_fence = False
            buffer = []
        elif in_fence:
            buffer.append(line)
    return False


def validate_contract(body: str) -> list[RuleResult]:
    """Validate every pure readiness-contract rule.

    Args:
        body: Untrusted GitHub issue Markdown.

    Returns:
        Rule results R001 through R018 in stable order. No network or file I/O
        is performed.

    Example:
        ``validate_contract("")`` returns a list whose first rule is not passed.
    """
    body = strip_bom(body)
    sections = parse_sections(body)
    section_map: dict[str, list[str]] = {}
    name_counts: dict[str, int] = {}
    for name, lines in sections:
        name_counts[name] = name_counts.get(name, 0) + 1
        section_map.setdefault(name, lines)

    marker_id = find_marker(body)
    feature_id, feature_count = find_feature_id(body)
    rules: list[RuleResult] = []

    rules.append(RuleResult(
        "R001", "marker-present", marker_id is not None,
        "tracked marker found" if marker_id else "no tracked marker",
    ))
    format_ok = feature_id is not None and FEATURE_ID_FORMAT_RE.match(feature_id) is not None
    rules.append(RuleResult(
        "R002", "feature-id-declared", feature_count == 1 and format_ok,
        f"feature_id={feature_id!r} count={feature_count} format_ok={format_ok}",
    ))
    marker_match = marker_id is not None and feature_id is not None and marker_id == feature_id
    rules.append(RuleResult(
        "R003", "feature-id-marker-match", marker_match,
        f"marker={marker_id!r} feature_id={feature_id!r}",
    ))

    missing = [name for name in REQUIRED_SECTIONS if name not in section_map]
    roadmap_linkage = section_map.get("Roadmap linkage")
    empty_linkage = roadmap_linkage is not None and not _section_nonempty(roadmap_linkage)
    sections_ok = not missing and not empty_linkage
    if missing:
        sections_detail = f"missing: {missing}"
    elif empty_linkage:
        sections_detail = "Roadmap linkage is empty"
    else:
        sections_detail = "all required sections present"
    rules.append(RuleResult(
        "R004", "required-sections-present", sections_ok, sections_detail,
    ))
    duplicates = [name for name in REQUIRED_SECTIONS if name_counts.get(name, 0) > 1]
    rules.append(RuleResult(
        "R005", "no-duplicate-sections", not duplicates,
        f"duplicates: {duplicates}" if duplicates else "no duplicate required sections",
    ))

    ready_section = section_map.get("Ready for Copilot")
    if ready_section is None:
        ready_ok, ready_detail = False, "section absent"
    else:
        boxes = _extract_checkboxes(ready_section)
        unchecked = sum(not checked for checked in boxes)
        ready_ok = bool(boxes) and unchecked == 0
        ready_detail = f"{unchecked} unchecked of {len(boxes)} boxes"
    rules.append(RuleResult("R006", "readiness-confirmation-checked", ready_ok, ready_detail))

    acceptance = section_map.get("Acceptance criteria")
    rules.append(RuleResult(
        "R007", "acceptance-criteria-nonempty",
        acceptance is not None and _section_nonempty(acceptance),
        _section_detail(acceptance),
    ))
    verification = section_map.get("Verification commands")
    verification_ok = verification is not None and _verification_commands_nonempty(verification)
    rules.append(RuleResult(
        "R008", "verification-commands-nonempty", verification_ok,
        "section absent" if verification is None else (
            "non-empty" if verification_ok else "no fenced command block"
        ),
    ))

    risk_section = section_map.get("Risk class")
    risk = _extract_risk_class(risk_section) if risk_section is not None else None
    rules.append(RuleResult("R009", "risk-class-valid", risk in RISK_CLASSES, f"risk={risk!r}"))

    allowed_section = section_map.get("Expected allowed paths")
    allowed = _extract_path_entries(allowed_section) if allowed_section is not None else []
    rules.append(RuleResult("R010", "allowed-paths-present", bool(allowed), f"{len(allowed)} path entries"))
    prohibited_section = section_map.get("Prohibited paths")
    prohibited = _extract_path_entries(prohibited_section) if prohibited_section is not None else []
    rules.append(RuleResult("R011", "prohibited-paths-present", bool(prohibited), f"{len(prohibited)} path entries"))

    all_paths = [(entry, "allowed") for entry in allowed] + [(entry, "prohibited") for entry in prohibited]
    unsafe = [
        {"entry": entry, "location": location, "error": error}
        for entry, location in all_paths
        if (error := validate_path_entry(entry)) is not None
    ]
    overbroad = [entry for entry in allowed if _is_overbroad_allowed_path(entry)]
    rules.append(RuleResult(
        "R012", "path-entries-safe", not unsafe and not overbroad,
        f"{len(unsafe)} unsafe, {len(overbroad)} overbroad allowed"
        if unsafe or overbroad else "all path entries safe",
    ))

    blocked_stop = section_map.get("Blocked-stop conditions")
    rules.append(RuleResult(
        "R013", "blocked-stop-conditions-nonempty",
        blocked_stop is not None and _section_nonempty(blocked_stop),
        _section_detail(blocked_stop),
    ))
    dependencies = section_map.get("Dependencies / blockers")
    if dependencies is None:
        blocking, dependency_detail = False, "section absent (see R004)"
    else:
        blocking, dependency_detail = _has_blocking_dependency(dependencies)
    rules.append(RuleResult(
        "R014", "dependencies-not-blocking", not blocking,
        dependency_detail or "no blockers",
    ))

    for rule_id, name, section_name in (
        ("R015", "outcome-nonempty", "Outcome"),
        ("R016", "scope-nonempty", "Scope"),
        ("R017", "non-goals-nonempty", "Non-goals"),
        ("R018", "human-review-instructions-nonempty", "Human review instructions"),
    ):
        section = section_map.get(section_name)
        rules.append(RuleResult(
            rule_id, name, section is not None and _section_nonempty(section),
            _section_detail(section),
        ))
    return rules
