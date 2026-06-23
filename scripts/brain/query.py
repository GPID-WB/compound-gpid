"""Budgeted Knowledge Brain query helpers.

This module provides the native retrieval layer for ``cg-index query``. It is
deterministic and local: it scores existing Brain entities with keyword overlap,
changed-file hints, and intent boosts, then renders a bounded JSON/Markdown
answer. It does not call external services or require optional dependencies.
"""
from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from brain import Entity, build_brain

SCHEMA_VERSION = 1
VALID_INTENTS = frozenset({"brainstorm", "plan", "work", "review", "compound", "resume"})
DEFAULT_BUDGET_TOKENS = 800
MIN_BUDGET_TOKENS = 300
MAX_EXCLUDED_ITEMS = 8
MAX_SNIPPET_CHARS = 360
MAX_WARNING_CHARS = 180
DISCLAIMER = "Token estimates are heuristic and this retrieval output is not evidence of token savings."

_WORD_RE = re.compile(r"[a-z][a-z0-9_-]{2,}")
_SPACE_RE = re.compile(r"\s+")
_STALE_RE = re.compile(r"\b(?:abandoned|superseded|obsolete|deprecated|stale|blocked)\b", re.IGNORECASE)
_CONFLICT_RE = re.compile(r"\b(?:conflict|contradict|supersed|replace|instead of|do not|don't)\b", re.IGNORECASE)

_INTENT_BOOSTS: dict[str, tuple[str, ...]] = {
    "brainstorm": ("brainstorm", "strategy", "decision", "idea"),
    "plan": ("plan", "requirements", "implementation", "roadmap"),
    "work": ("work", "implementation", "test", "fix", "script"),
    "review": ("review", "finding", "p0", "p1", "p2", "p3", "testing"),
    "compound": ("solution", "root-cause", "prevention", "lesson"),
    "resume": ("status", "handoff", "current", "completed", "blocked"),
}


@dataclass(frozen=True)
class QueryOptions:
    """Inputs for a Knowledge Brain query."""

    intent: str
    query: str
    changed_files: tuple[str, ...] = ()
    budget_tokens: int = DEFAULT_BUDGET_TOKENS


def estimate_tokens(text: str) -> int:
    """Estimate tokens using the repository's directional chars/4 heuristic."""
    return max(1, len(text) // 4)


def _terms(value: str) -> set[str]:
    return {match.group(0).lower() for match in _WORD_RE.finditer(value)}


def _entity_text(entity: Entity) -> str:
    parts = [
        entity.title,
        entity.summary,
        entity.status,
        " ".join(entity.tags),
        str(entity.path),
        " ".join(keyword for keyword, _ in entity.keywords[:20]),
    ]
    return " ".join(part for part in parts if part)


def _changed_file_terms(changed_files: Sequence[str]) -> set[str]:
    terms: set[str] = set()
    for value in changed_files:
        path = Path(value)
        terms.update(_terms(value))
        terms.update(_terms(path.stem))
        terms.update(_terms(path.name))
    return terms


def _status_is_stale(entity: Entity) -> bool:
    status = entity.status
    haystack = f"{status} {entity.title} {' '.join(entity.tags)}"
    return bool(_STALE_RE.search(haystack))


def _snippet(entity: Entity, query_terms: set[str], max_chars: int = MAX_SNIPPET_CHARS) -> str:
    text = entity.summary.strip() or entity.title
    text = _SPACE_RE.sub(" ", text).strip()
    if len(text) <= max_chars:
        return text

    lower = text.lower()
    positions = [lower.find(term) for term in query_terms if lower.find(term) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    snippet = text[start : start + max_chars].strip()
    if start > 0:
        snippet = "..." + snippet
    if start + max_chars < len(text):
        snippet += "..."
    return snippet


def _truncate(value: str, max_chars: int) -> str:
    value = _SPACE_RE.sub(" ", value).strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def _score_entity(
    entity: Entity,
    query_terms: set[str],
    changed_terms: set[str],
    intent: str,
) -> tuple[float, list[str]]:
    text = _entity_text(entity).lower()
    entity_terms = _terms(text)
    score = 0.0
    reasons: list[str] = []

    overlap = sorted(query_terms & entity_terms)
    if overlap:
        score += len(overlap) * 5.0
        reasons.append("matched query terms: " + ", ".join(overlap[:5]))

    changed_overlap = sorted(changed_terms & entity_terms)
    if changed_overlap:
        score += len(changed_overlap) * 3.0
        reasons.append("matched changed-file hints: " + ", ".join(changed_overlap[:5]))

    boosts = [term for term in _INTENT_BOOSTS[intent] if term in entity_terms or term in text]
    if boosts:
        score += min(len(boosts), 3) * 1.5
        reasons.append(f"matched {intent} intent signals")

    if entity.entity_type in {"solution", "plan"}:
        score += 1.0
    if entity.entity_type == "feature" and intent in {"plan", "resume"}:
        score += 1.0
    if _status_is_stale(entity):
        score -= 2.0
        reasons.append("flagged stale by status/title metadata")

    return score, reasons


def _confidence(score: float, top_score: float) -> str:
    if score <= 0 or top_score <= 0:
        return "low"
    ratio = score / top_score
    if ratio >= 0.75:
        return "high"
    if ratio >= 0.35:
        return "medium"
    return "low"


def query_brain(root: Path, options: QueryOptions) -> dict[str, Any]:
    """Return a budgeted Knowledge Brain query payload.

    Args:
        root: Project root containing ``.cg-docs``.
        options: Query options.

    Returns:
        Stable JSON-serialisable payload.

    Raises:
        ValueError: If intent, budget, query, or project files are invalid.
    """
    if options.intent not in VALID_INTENTS:
        raise ValueError(f"invalid intent '{options.intent}'")
    if not options.query.strip():
        raise ValueError("--query is required")
    if options.budget_tokens < MIN_BUDGET_TOKENS:
        raise ValueError(f"--budget must be at least {MIN_BUDGET_TOKENS}")
    if not (root / ".cg-docs").is_dir():
        raise ValueError(f"{root / '.cg-docs'} does not exist")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        data = build_brain(root)
    query_terms = _terms(options.query)
    changed_terms = _changed_file_terms(options.changed_files)

    scored: list[tuple[float, Entity, list[str]]] = []
    for entity in data.entities:
        score, reasons = _score_entity(entity, query_terms, changed_terms, options.intent)
        if score > 0:
            scored.append((score, entity, reasons))

    scored.sort(key=lambda item: (-item[0], str(item[1].path)))
    top_score = scored[0][0] if scored else 0.0
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    remaining = options.budget_tokens

    for score, entity, reasons in scored:
        candidate = {
            "path": str(entity.path).replace("\\", "/"),
            "title": entity.title,
            "entity_type": entity.entity_type,
            "status": entity.status or None,
            "confidence": _confidence(score, top_score),
            "why_selected": reasons or ["matched query"],
            "stale": _status_is_stale(entity),
            "conflict": bool(_CONFLICT_RE.search(_entity_text(entity))),
            "snippet": _snippet(entity, query_terms),
        }
        candidate_tokens = estimate_tokens(json.dumps(candidate, sort_keys=True))
        if selected and remaining - candidate_tokens < 0:
            if len(excluded) < MAX_EXCLUDED_ITEMS:
                excluded.append({
                    "path": candidate["path"],
                    "why_excluded": "budget_exhausted",
                    "estimated_tokens": candidate_tokens,
                })
            continue
        if not selected or remaining - candidate_tokens >= 0:
            selected.append(candidate)
            remaining -= candidate_tokens

    if not selected and scored:
        score, entity, reasons = scored[0]
        selected.append({
            "path": str(entity.path).replace("\\", "/"),
            "title": entity.title,
            "entity_type": entity.entity_type,
            "status": entity.status or None,
            "confidence": _confidence(score, top_score),
            "why_selected": reasons or ["matched query"],
            "stale": _status_is_stale(entity),
            "conflict": bool(_CONFLICT_RE.search(_entity_text(entity))),
            "snippet": "",
        })

    answer = _answer(options, selected)
    warnings_list = [DISCLAIMER]
    if captured:
        warnings_list.append(f"Brain build emitted {len(captured)} warning(s); showing first 3.")
        warnings_list.extend(_truncate(str(item.message), MAX_WARNING_CHARS) for item in captured[:3])
    if not selected:
        warnings_list.append("No matching Brain artifacts found for the query.")
    if any(item["stale"] for item in selected):
        warnings_list.append("One or more selected artifacts are flagged stale; treat as advisory context.")
    if any(item["conflict"] for item in selected):
        warnings_list.append("One or more selected artifacts contain possible conflict/supersession language.")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "intent": options.intent,
        "query": options.query,
        "changed_files": list(options.changed_files),
        "budget_tokens": options.budget_tokens,
        "estimated_tokens": 0,
        "answer": answer,
        "selected": selected,
        "excluded": excluded,
        "warnings": warnings_list,
        "confidence": selected[0]["confidence"] if selected else "low",
    }
    _fit_payload_to_budget(payload)
    return payload


def _answer(options: QueryOptions, selected: Sequence[dict[str, Any]]) -> str:
    if not selected:
        return f"No Knowledge Brain artifacts matched `{options.query}` for `{options.intent}`."
    paths = ", ".join(item["path"] for item in selected[:3])
    return (
        f"Selected {len(selected)} Knowledge Brain artifact(s) for `{options.intent}` "
        f"within a {options.budget_tokens}-token budget: {paths}."
    )


def render_query_json(payload: dict[str, Any]) -> str:
    """Render query payload as stable JSON."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_query_markdown(payload: dict[str, Any]) -> str:
    """Render query payload as compact Markdown."""
    lines = [
        "# Knowledge Brain Query",
        "",
        f"Intent: `{payload['intent']}`",
        f"Budget: `{payload['budget_tokens']}` estimated tokens",
        f"Estimated output: `{payload['estimated_tokens']}` tokens",
        "",
        "## Answer",
        "",
        payload["answer"],
        "",
        "## Selected Artifacts",
        "",
    ]
    selected = payload.get("selected", [])
    if not selected:
        lines.append("- None")
    for item in selected:
        flags = []
        if item.get("stale"):
            flags.append("stale")
        if item.get("conflict"):
            flags.append("conflict")
        flag_text = f" ({', '.join(flags)})" if flags else ""
        lines.append(f"- `{item['path']}` - {item['title']} [{item['confidence']}]{flag_text}")
        lines.append(f"  - Why: {'; '.join(item.get('why_selected', []))}")
        snippet = item.get("snippet")
        if snippet:
            lines.append(f"  - Snippet: {snippet}")
    if payload.get("excluded"):
        lines.extend(["", "## Excluded", ""])
        for item in payload["excluded"][:8]:
            lines.append(f"- `{item['path']}` - {item['why_excluded']}")
    lines.extend(["", "## Warnings", ""])
    for warning in payload.get("warnings", []):
        lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def _rendered_estimate(payload: dict[str, Any]) -> int:
    """Estimate the larger JSON/Markdown representation for budget gating."""
    return max(
        estimate_tokens(render_query_json(payload)),
        estimate_tokens(render_query_markdown(payload)),
    )


def _fit_payload_to_budget(payload: dict[str, Any]) -> None:
    """Trim selected snippets/items until rendered output fits the budget.

    Mutates ``payload`` in place. If one selected item plus metadata still
    exceeds budget, the snippet is removed but the artifact path/reason remains.
    """
    budget = int(payload["budget_tokens"])
    while payload["selected"] and _rendered_estimate(payload) > budget:
        if payload["excluded"]:
            payload["excluded"].pop()
            continue
        if len(payload["selected"]) > 1:
            removed = payload["selected"].pop()
            if len(payload["excluded"]) < MAX_EXCLUDED_ITEMS:
                payload["excluded"].append({
                    "path": removed["path"],
                    "why_excluded": "render_budget_exhausted",
                    "estimated_tokens": estimate_tokens(json.dumps(removed, sort_keys=True)),
                })
            continue
        selected = payload["selected"][0]
        if selected.get("snippet"):
            selected["snippet"] = ""
            continue
        break
    payload["answer"] = _answer(
        QueryOptions(
            intent=payload["intent"],
            query=payload["query"],
            changed_files=tuple(payload.get("changed_files", [])),
            budget_tokens=budget,
        ),
        payload["selected"],
    )
    payload["confidence"] = payload["selected"][0]["confidence"] if payload["selected"] else "low"
    payload["estimated_tokens"] = _rendered_estimate(payload)


def query_from_args(
    root: Path,
    *,
    intent: str,
    query: str,
    changed_files: Iterable[str] = (),
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    output_format: str = "md",
) -> str:
    """Run a query and render it in the requested format."""
    payload = query_brain(
        root,
        QueryOptions(
            intent=intent,
            query=query,
            changed_files=tuple(changed_files),
            budget_tokens=budget_tokens,
        ),
    )
    if output_format == "json":
        return render_query_json(payload)
    if output_format == "md":
        return render_query_markdown(payload)
    raise ValueError("--format must be json or md")
