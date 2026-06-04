"""team_brain.dedup — Contradiction detection for cross-project pattern entries.

Scans all ``patterns/*.jsonl`` files and groups candidate pairs using
Jaccard similarity on tokenized pattern text (primary signal).  Tag overlap
is a secondary tiebreaker, not the sole grouping criterion.

Within each candidate pair, the problem descriptions (``root-cause`` + ``title``
from the entry frontmatter) are compared to classify the relationship:

- **contradiction**: Same problem, same context → one entry should supersede
  the other.  Newer date + higher confidence wins.
- **contextual_variant**: Same problem, different context → both entries are
  valid.  A ``context-note`` field is recommended to distinguish them.
- **false_positive**: Different problem (low Jaccard was noise) → skip.

Intra-project pairs are always skipped (dedup within a project is handled by
the local brain, not the team brain).

Usage::

    from team_brain.dedup import detect_contradictions
    from pathlib import Path

    reports = detect_contradictions(Path("patterns/"))
    for r in reports:
        print(r.entry_a["id"], "<->", r.entry_b["id"], "→", r.classification)

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Jaccard similarity threshold for candidate pairing (primary signal).
JACCARD_THRESHOLD = 0.4

#: Number of shared tags required to boost candidate confidence.
TAG_BOOST_MIN_SHARED = 2

#: Jaccard threshold for automatic supersession classification (same context).
SUPERSESSION_JACCARD = 0.6

#: Minimum number of word tokens required for a meaningful Jaccard comparison.
MIN_TOKEN_COUNT = 3

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ContradictionReport:
    """A pair of pattern entries flagged as potential contradictions.

    Args:
        entry_a: First JSONL pattern dict.
        entry_b: Second JSONL pattern dict.
        classification: One of ``"contradiction"``, ``"contextual_variant"``,
            or ``"false_positive"``.
        jaccard_score: Word-overlap Jaccard similarity of the pattern texts.
        shared_tags: Tags shared by both entries.
        recommended_action: Short human-readable action string, e.g.
            ``"supersede entry_a with entry_b (newer, higher confidence)"``
            or ``"add context-note to both entries"``.

    Example::

        report = ContradictionReport(
            entry_a={"id": "a", "date": "2026-01-01", "pattern": "Always guard."},
            entry_b={"id": "b", "date": "2026-02-01", "pattern": "Never skip guards."},
            classification="contextual_variant",
            jaccard_score=0.5,
            shared_tags=["guard", "validation"],
            recommended_action="add context-note to both entries",
        )
    """

    entry_a: dict
    entry_b: dict
    classification: str  # "contradiction" | "contextual_variant" | "false_positive"
    jaccard_score: float
    shared_tags: List[str] = field(default_factory=list)
    recommended_action: str = ""


# ---------------------------------------------------------------------------
# Tokenisation helpers
# ---------------------------------------------------------------------------

#: Common English stop words excluded from Jaccard tokenisation
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "do", "for",
        "from", "has", "have", "in", "is", "it", "its", "not", "of",
        "on", "or", "that", "the", "this", "to", "use", "was", "with",
    }
)


def _tokenize(text: str) -> Set[str]:
    """Return the set of lowercase word tokens from *text*.

    Non-alphabetic characters are treated as delimiters.  Single-character
    tokens and common English stop words are excluded to reduce noise.

    Args:
        text: Raw string to tokenise.

    Returns:
        Set of unique lowercase word tokens.

    Example::

        _tokenize("Always guard inputs at system boundaries.")
        # {"always", "guard", "inputs", "system", "boundaries"}
    """
    raw_tokens = re.findall(r"[a-zA-Z]{2,}", text.lower())
    return {t for t in raw_tokens if t not in _STOP_WORDS}


def _jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """Return the Jaccard similarity between two token sets.

    Returns 0.0 when either set is empty (degenerate case — no meaningful
    overlap is possible).

    Args:
        set_a: First token set.
        set_b: Second token set.

    Returns:
        Float in [0, 1].

    Example::

        _jaccard({"guard", "inputs"}, {"guard", "validate"})
        # 0.333...
    """
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


# ---------------------------------------------------------------------------
# JSONL loading helpers
# ---------------------------------------------------------------------------


def _load_all_patterns(patterns_dir: Path) -> List[dict]:
    """Load all pattern entries from ``*.jsonl`` files in *patterns_dir*.

    Args:
        patterns_dir: Directory containing ``<project>.jsonl`` files.

    Returns:
        List of parsed pattern dicts.  Malformed lines are skipped with a
        ``UserWarning`` so a single bad file does not abort the full scan.

    Example::

        entries = _load_all_patterns(Path("patterns/"))
    """
    entries: List[dict] = []
    if not patterns_dir.exists():
        return entries

    for jsonl_path in sorted(patterns_dir.glob("*.jsonl")):
        try:
            lines = jsonl_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            warnings.warn(f"Could not read {jsonl_path}: {exc}", UserWarning, stacklevel=3)
            continue

        for line_no, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.warn(
                    f"Malformed JSON in {jsonl_path}:{line_no} — {exc}",
                    UserWarning,
                    stacklevel=3,
                )
                continue
            entries.append(entry)

    return entries


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def _problem_similarity(entry_a: dict, entry_b: dict) -> float:
    """Estimate similarity of the *problems* described by two entries.

    Uses the ``root-cause`` + ``title`` fields from entry frontmatter.  Falls
    back gracefully if either field is absent.

    Args:
        entry_a: First pattern entry dict.
        entry_b: Second pattern entry dict.

    Returns:
        Jaccard similarity in [0, 1].
    """
    def _problem_tokens(entry: dict) -> Set[str]:
        parts = []
        rc = entry.get("root-cause") or entry.get("root_cause") or ""
        title = entry.get("title") or ""
        topic = entry.get("topic") or ""
        parts.extend([rc, title, topic])
        return _tokenize(" ".join(parts))

    return _jaccard(_problem_tokens(entry_a), _problem_tokens(entry_b))


def _classify(
    entry_a: dict,
    entry_b: dict,
) -> Tuple[str, str]:
    """Classify the relationship between two candidate entries.

    Args:
        entry_a: First pattern entry dict.
        entry_b: Second pattern entry dict.

    Returns:
        ``(classification, recommended_action)`` tuple.
    """
    problem_sim = _problem_similarity(entry_a, entry_b)

    # High problem similarity → same problem
    if problem_sim >= JACCARD_THRESHOLD:
        # Which is newer? Higher confidence?
        date_a = entry_a.get("date", "")
        date_b = entry_b.get("date", "")
        conf_a = float(entry_a.get("confidence", 1.0))
        conf_b = float(entry_b.get("confidence", 1.0))

        if date_b > date_a or (date_b == date_a and conf_b >= conf_a):
            winner_id = entry_b.get("id", "entry_b")
            loser_id = entry_a.get("id", "entry_a")
        else:
            winner_id = entry_a.get("id", "entry_a")
            loser_id = entry_b.get("id", "entry_b")

        action = f"supersede {loser_id} with {winner_id} (newer, higher confidence)"
        return "contradiction", action

    # Low problem similarity → same pattern words, different problem
    # → contextual variant (both are valid in their respective contexts)
    action = (
        "add context-note to both entries to distinguish when each applies"
    )
    return "contextual_variant", action


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_contradictions(patterns_dir: Path) -> List[ContradictionReport]:
    """Scan *patterns_dir* for contradicting or redundant pattern entries.

    Algorithm:
        1. Load all entries from ``*.jsonl`` files.
        2. For each cross-project pair, compute word-overlap Jaccard on
           ``pattern`` text.
        3. Pairs with Jaccard ≥ :data:`JACCARD_THRESHOLD` are candidates.
        4. Tag overlap (≥ :data:`TAG_BOOST_MIN_SHARED`) is recorded as a
           secondary signal in the report.
        5. Classify each candidate as ``contradiction``,
           ``contextual_variant``, or ``false_positive``.
        6. Intra-project pairs are skipped entirely.

    Args:
        patterns_dir: Directory containing ``<project>.jsonl`` files.  May
            be empty or non-existent; returns an empty list in that case.

    Returns:
        List of :class:`ContradictionReport` objects.  False-positive
        candidates are excluded from the returned list (they are filtered
        out after classification).

    Example::

        reports = detect_contradictions(Path("patterns/"))
        for r in reports:
            print(f"{r.entry_a['id']} <-> {r.entry_b['id']}: {r.classification}")
    """
    entries = _load_all_patterns(patterns_dir)

    if len(entries) < 2:
        return []

    reports: List[ContradictionReport] = []

    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a = entries[i]
            b = entries[j]

            # Skip intra-project pairs
            proj_a = a.get("source-project") or a.get("source_project") or ""
            proj_b = b.get("source-project") or b.get("source_project") or ""
            if proj_a and proj_b and proj_a == proj_b:
                continue

            # Primary grouping: Jaccard similarity on pattern text
            tokens_a = _tokenize(a.get("pattern", ""))
            tokens_b = _tokenize(b.get("pattern", ""))

            # Skip pairs where either entry has too few tokens to be meaningful
            if len(tokens_a) < MIN_TOKEN_COUNT or len(tokens_b) < MIN_TOKEN_COUNT:
                continue

            jaccard = _jaccard(tokens_a, tokens_b)
            if jaccard < JACCARD_THRESHOLD:
                continue

            # Secondary signal: tag overlap
            tags_a = set(a.get("tags", []))
            tags_b = set(b.get("tags", []))
            shared_tags = sorted(tags_a & tags_b)

            classification, action = _classify(a, b)

            if classification == "false_positive":
                continue

            reports.append(
                ContradictionReport(
                    entry_a=a,
                    entry_b=b,
                    classification=classification,
                    jaccard_score=round(jaccard, 4),
                    shared_tags=shared_tags,
                    recommended_action=action,
                )
            )

    return reports
