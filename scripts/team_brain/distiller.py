"""team_brain.distiller — Pattern distillation for team brain entries.

Extracts a ≤200-character one-liner from a solution entry, tracking
the source of the distillation for audit and LLM-enhancement purposes.

Usage::

    from team_brain.distiller import distill_pattern

    result = distill_pattern(frontmatter, body)
    print(result.pattern_text)  # "Always guard against None at system boundaries."
    print(result.source)        # "root-cause"
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

_MAX_PATTERN_LEN = 200

DistillSource = Literal[
    "root-cause",
    "solution-section",
    "root-cause-section",
    "title",
    "fallback",
]


@dataclass
class DistillResult:
    """Result of pattern distillation from a solution entry.

    Args:
        pattern_text: Distilled one-liner, truncated to
            :data:`_MAX_PATTERN_LEN` characters.
        source: Label for which fallback level produced the pattern —
            ``root-cause`` (frontmatter field), ``solution-section``
            (## Solution body), ``root-cause-section`` (## Root Cause body),
            ``title`` (frontmatter title), or ``fallback`` (nothing found).
        prompt: Optional LLM prompt string for caller-driven LLM
            distillation. ``None`` for deterministic sources
            (``root-cause``, ``solution-section``, ``root-cause-section``).
            Non-``None`` for ``title`` only — callers may use this prompt
            to request a higher-quality one-liner from a model.
            ``None`` for all other sources including ``fallback``.

    Example::

        result = distill_pattern({"root-cause": "Missing null check."}, "")
        assert result.pattern_text == "Missing null check."
        assert result.source == "root-cause"
        assert result.prompt is None
    """

    pattern_text: str
    source: DistillSource
    prompt: Optional[str] = None


def distill_pattern(frontmatter: dict, body: str) -> DistillResult:
    """Distill a ≤200-char one-liner pattern from a solution entry.

    Attempts extraction sources in order of quality:

    1. ``root-cause`` frontmatter field — authoritative one-liner by
       convention; no truncation beyond the 200-char cap.
    2. First substantive sentence from the ``## Solution`` section body.
    3. First substantive sentence from the ``## Root Cause`` section body.
    4. ``title`` frontmatter field (with an LLM prompt hint).
    5. Literal ``"(no pattern)"`` fallback.

    A "substantive sentence" is one that:
    - Has more than 10 characters.
    - Does not start with ``#``, `` ``` ``, ``|``, or ``-`` (headings, code
      fences, table rows, and list items are not actionable one-liners).

    Args:
        frontmatter: Parsed YAML frontmatter dict from the solution file.
        body: Markdown body text (the content after the ``---`` frontmatter
            block).

    Returns:
        :class:`DistillResult` with the pattern text, source label, and
        an optional LLM prompt string for caller-driven enhancement.

    Example::

        result = distill_pattern(
            {"title": "Fix null crash"},
            "## Solution\\n\\nAlways guard inputs.\\n",
        )
        assert result.pattern_text == "Always guard inputs."
        assert result.source == "solution-section"
    """
    # 1. root-cause frontmatter field (authoritative one-liner by convention)
    # Guard: only use string values — null or non-string values (list, dict)
    # produce "None" or a Python repr via str(), which must not be stored.
    rc_val = frontmatter.get("root-cause")
    rc_fm = str(rc_val).strip().strip("\"'") if isinstance(rc_val, str) else ""
    if rc_fm:
        return DistillResult(
            pattern_text=rc_fm[:_MAX_PATTERN_LEN],
            source="root-cause",
        )

    # 2 & 3. First substantive sentence from ## Solution / ## Root Cause
    for section_name, src in (
        ("Solution", "solution-section"),
        ("Root Cause", "root-cause-section"),
    ):
        section_m = re.search(
            rf"#{{2,6}}\s*{re.escape(section_name)}\s*\n+(.*?)(?:\n#{{2,6}}|\Z)",
            body,
            re.DOTALL,
        )
        if section_m:
            text = section_m.group(1).strip()
            # Split on paragraph boundaries first (blank lines), then sentence
            # boundaries, so code blocks and table rows are isolated as their
            # own tokens — they are then individually rejected by the
            # startswith guard, and the actual prose that follows can be found.
            for sentence in re.split(r"(?<=[.!?])\s+|\n{2,}", text):
                s = sentence.strip()
                if s and len(s) > 10 and not s.startswith(("#", "```", "|", "-")):
                    return DistillResult(
                        pattern_text=s[:_MAX_PATTERN_LEN],
                        source=src,  # type: ignore[arg-type]
                    )

    # 4. Title frontmatter field (include LLM prompt for enhancement)
    # Same guard as root-cause: only use string values.
    title_val = frontmatter.get("title")
    title = str(title_val).strip().strip("\"'") if isinstance(title_val, str) else ""
    if title:
        llm_prompt = (
            f"Summarize the following solution title as a one-sentence, actionable lesson "
            f"(≤ {_MAX_PATTERN_LEN} chars) that could be reused across projects:\n\n"
            f"Title: {title}\n\nLesson:"
        )
        return DistillResult(
            pattern_text=title[:_MAX_PATTERN_LEN],
            source="title",
            prompt=llm_prompt,
        )

    return DistillResult(pattern_text="(no pattern)", source="fallback")
