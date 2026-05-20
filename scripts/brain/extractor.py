"""brain.extractor — Keyword extraction for the brain engine.

Extracts weighted keywords from entity content using six signals:

1. **Backtick terms** (weight 3.0) — code names, package names, function refs.
2. **Heading text** (weight 3.0) — section headings highlight key topics.
3. **Command refs** ``/cg-*`` (weight 2.0) — slash commands are prominent concepts.
4. **File refs** (weight 2.0) — ``.py``, ``.ps1``, ``.R``, ``.md``, etc.
5. **Pattern names** (weight 3.0) — Title Case multi-word phrases (named concepts).
6. **Frequency keywords** (weight 1.0) — normalised TF on stopword-filtered body words.

The same keyword may receive contributions from multiple signals; scores are
accumulated and the top :data:`_MAX_KEYWORDS` results are returned sorted by
score descending.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, FrozenSet, List, Tuple

from brain import Entity

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Maximum keywords to return per entity.
_MAX_KEYWORDS = 50

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

#: Content within backticks — inline code spans.
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")

#: Markdown headings: captures the text after the ``#`` characters.
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

#: Slash commands of the form ``/cg-*``.
_COMMAND_RE = re.compile(r"/cg-[\w-]+")

#: File references with common extensions (case-insensitive).
_FILE_REF_RE = re.compile(
    r"\b[\w./\\-]+\.(?:py|ps1|r|rmd|md|json|do|ado|sh|cmd|bat|yml|yaml|txt)\b",
    re.IGNORECASE,
)

#: Title Case multi-word sequences — two or more consecutive capitalised words.
_PATTERN_RE = re.compile(r"\b([A-Z][a-z]{1,}(?:\s+[A-Z][a-z]{1,})+)\b")

#: Tokeniser — matches word-like tokens (letters + digits, 3+ chars).
_WORD_RE = re.compile(r"[a-z][a-z0-9_-]{2,}")

# ---------------------------------------------------------------------------
# Stopword list (~150 words)
# ---------------------------------------------------------------------------

_STOPWORDS: FrozenSet[str] = frozenset(
    {
        # Common English function words
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "if",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "was",
        "are",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "we",
        "you",
        "they",
        "them",
        "their",
        "there",
        "here",
        "when",
        "where",
        "what",
        "which",
        "who",
        "how",
        "all",
        "each",
        "every",
        "any",
        "some",
        "not",
        "as",
        "also",
        "then",
        "than",
        "about",
        "above",
        "after",
        "before",
        "between",
        "into",
        "through",
        "during",
        "against",
        "within",
        "without",
        "around",
        "among",
        # Common verbs / verb forms
        "use",
        "used",
        "using",
        "make",
        "makes",
        "made",
        "add",
        "adds",
        "added",
        "get",
        "gets",
        "set",
        "run",
        "runs",
        "see",
        "call",
        "calls",
        "return",
        "returns",
        "pass",
        "fail",
        "fails",
        "need",
        "needs",
        "want",
        "wants",
        "keep",
        "kept",
        "move",
        "moved",
        "load",
        "loads",
        "save",
        "saves",
        "read",
        "reads",
        "write",
        "writes",
        "find",
        "found",
        "create",
        "created",
        "remove",
        "removed",
        "update",
        "updated",
        "check",
        "checks",
        "allow",
        "allows",
        # Common adjectives / adverbs
        "new",
        "old",
        "now",
        "more",
        "only",
        "well",
        "just",
        "very",
        "same",
        "other",
        "like",
        "true",
        "false",
        "first",
        "last",
        "next",
        "full",
        "main",
        "many",
        "both",
        "such",
        "own",
        "per",
        # Technical noise
        "file",
        "files",
        "line",
        "lines",
        "text",
        "type",
        "one",
        "two",
        "three",
        "four",
        "five",
        "note",
        "see",
        "ref",
        "todo",
        "fixme",
        "example",
        "output",
        "input",
        "value",
        "values",
        "name",
        "names",
        "item",
        "items",
        "list",
        "dict",
        "str",
        "int",
        "bool",
        "none",
        # Compound GPID domain noise
        "cg",
        "docs",
        "doc",
        "path",
        "code",
        "data",
        "log",
        "logs",
        "key",
        "keys",
        "step",
        "steps",
        "plan",
        "plans",
    }
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_keywords(entity: Entity, text: str) -> List[Tuple[str, float]]:
    """Extract weighted keywords from entity content.

    Applies six extraction signals to the raw text, accumulates scores per
    keyword, and returns the top :data:`_MAX_KEYWORDS` results sorted by score
    descending.

    Args:
        entity: The :class:`~brain.Entity` being processed.  Frontmatter fields
            such as ``tags`` and ``title`` provide additional signal.
        text: Raw body text of the entity (including frontmatter and headings).

    Returns:
        List of ``(keyword, score)`` tuples sorted by score descending.
        Keywords are lower-cased and normalised.

    Example:
        >>> from pathlib import Path
        >>> from brain import Entity
        >>> from brain.extractor import extract_keywords
        >>> e = Entity(path=Path("f.md"), entity_type="solution", frontmatter={})
        >>> kws = extract_keywords(e, "## Problem\\n\\nUse `parse_frontmatter()` here.")
        >>> assert any(k == "parse_frontmatter()" for k, _ in kws)
    """
    scores: Dict[str, float] = defaultdict(float)

    # --- Signal 1: backtick terms (weight 3.0) ---
    for raw in _BACKTICK_RE.findall(text):
        kw = raw.strip().lower()
        if kw and len(kw) > 1 and kw not in _STOPWORDS:
            scores[kw] += 3.0

    # --- Signal 2: heading text (weight 3.0 per word) ---
    for heading_text in _HEADING_RE.findall(text):
        for word in _WORD_RE.findall(heading_text.lower()):
            if word not in _STOPWORDS:
                scores[word] += 3.0

    # --- Signal 3: /cg-* command refs (weight 2.0) ---
    for raw_cmd in _COMMAND_RE.findall(text):
        kw = raw_cmd.lstrip("/").lower()
        if kw:
            scores[kw] += 2.0

    # --- Signal 4: file refs (weight 2.0) ---
    for fref in _FILE_REF_RE.findall(text):
        kw = Path(fref).name.lower()  # basename only, e.g. "cg_index.py"
        if kw not in _STOPWORDS:
            scores[kw] += 2.0

    # --- Signal 5: pattern names — Title Case phrases (weight 3.0) ---
    for phrase in _PATTERN_RE.findall(text):
        kw = phrase.lower()
        if kw not in _STOPWORDS:
            scores[kw] += 3.0

    # --- Signal 6: normalised word frequency, stopword-filtered (weight 1.0) ---
    freq: Dict[str, int] = defaultdict(int)
    for word in _WORD_RE.findall(text.lower()):
        if word not in _STOPWORDS:
            freq[word] += 1

    total_words = sum(freq.values()) or 1
    for word, count in freq.items():
        scores[word] += count / total_words  # normalised TF

    # --- Also include frontmatter title words (weight 2.0) ---
    title = str(entity.frontmatter.get("title", ""))
    for word in _WORD_RE.findall(title.lower()):
        if word not in _STOPWORDS:
            scores[word] += 2.0

    # --- Also include frontmatter tags (weight 2.0) ---
    for tag in entity.tags:
        kw = tag.strip().lower()
        if kw and kw not in _STOPWORDS:
            scores[kw] += 2.0

    # Sort by score descending, return top N
    sorted_kws = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return sorted_kws[:_MAX_KEYWORDS]
