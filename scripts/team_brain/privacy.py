"""team_brain.privacy — 3-layer privacy filter for team brain push.

Runs before any content is pushed to the central team brain repo. The filter
is blocking — if it cannot safely redact content, the push is aborted.

Layers (applied in order):
1. **Regex layer** (deterministic, fast): Strips absolute paths, emails,
   credential patterns, and configurable internal URLs.
2. **Frontmatter layer**: Respects ``private: true`` (block entire entry)
   and ``private-sections: [...]`` (strip named sections).
3. **LLM layer** (non-blocking, auto-applied): Scans for contextual
   sensitivity the regex missed. Suggestions are auto-applied and logged.
   Disable with ``llm-filter: false`` in config or ``--no-llm`` flag.

The three layers are composed by ``run_privacy_filter()``.

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from team_brain.schema import TeamBrainConfig

# ---------------------------------------------------------------------------
# Redaction types
# ---------------------------------------------------------------------------


@dataclass
class Redaction:
    """A single redaction made by the privacy filter.

    Args:
        layer: Which layer made the redaction (``regex``, ``frontmatter``, ``llm``).
        redaction_type: Category of the redacted content (e.g., ``path``, ``email``).
        line_number: 1-based line number where the redaction occurred.
        snippet_length: Character length of the original content that was removed.
    """

    layer: str
    redaction_type: str
    line_number: int
    snippet_length: int


@dataclass
class FilterResult:
    """Result of running the full privacy filter pipeline.

    Args:
        clean_content: Filtered markdown content ready for push.
        redactions: All redactions applied (regex + frontmatter + LLM).
        blocked: Whether the entry was blocked entirely (``private: true``).
        block_reason: Human-readable reason if blocked.
    """

    clean_content: str
    redactions: List[Redaction] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""

    def summary(self) -> str:
        """Return a human-readable summary of filter activity.

        Returns:
            Summary string for the push confirmation message.

        Example::

            result.summary()
            # "Privacy filter: 3 regex redactions, 2 LLM redactions (auto-applied)"
        """
        regex_count = sum(1 for r in self.redactions if r.layer == "regex")
        llm_count = sum(1 for r in self.redactions if r.layer == "llm")
        llm_types = sorted({r.redaction_type for r in self.redactions if r.layer == "llm"})
        parts = []
        if regex_count:
            parts.append(f"{regex_count} regex redaction{'s' if regex_count != 1 else ''}")
        if llm_count:
            types_str = f" (auto-applied: [{', '.join(llm_types)}])" if llm_types else ""
            parts.append(f"{llm_count} LLM redaction{'s' if llm_count != 1 else ''}{types_str}")
        if not parts:
            parts.append("no redactions")
        return "Privacy filter: " + ", ".join(parts)


# ---------------------------------------------------------------------------
# Regex layer patterns
# ---------------------------------------------------------------------------

#: Windows absolute paths: C:\..., D:\Users\... (backslash or forward slash — Git Bash, WSL, R).
#: Uses negative lookbehind (?<![A-Za-z]) to prevent matching 's://' in 'https://'.
_WIN_PATH_RE = re.compile(r"(?<![A-Za-z])[A-Z]:[/\\][^\s\"'\n]+", re.IGNORECASE)

#: Unix home/system paths: /home/user/..., /Users/..., /tmp/..., etc.
#: Unix absolute paths — matches any two-level+ absolute path (e.g. /home/..., /mnt/..., /srv/...).
#: Uses negative lookbehind (?<![A-Za-z0-9_.]) to avoid matching relative path components
#: like the /brain/ segment inside ./scripts/brain/utils.py.
#: The {4,} after the second slash prevents matching short tokens like /a/b.
_UNIX_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.])/[A-Za-z][A-Za-z0-9_\-]*/[^\s\"'\n]{4,}")

#: UNC network paths: \\server\share
_UNC_PATH_RE = re.compile(r"\\\\[^\s\"'\n]+")

#: Email addresses (simplified RFC 5322)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

#: Credential-adjacent patterns: password=..., token: ..., api_key=..., etc.
_CREDENTIAL_RE = re.compile(
    r"(?:password|passwd|secret|token|api[_\-]?key|auth[_\-]?key)"
    r"\s*[:=]\s*\S+",
    re.IGNORECASE,
)

#: Relative paths (should NOT be redacted — e.g. ./scripts/foo.py)
_RELATIVE_PATH_RE = re.compile(r"^\.{1,2}/")


def _build_url_pattern(patterns: List[str]) -> Optional[re.Pattern]:
    """Build a compiled regex from a list of hostname patterns.

    Args:
        patterns: List of glob-style hostname patterns (e.g. ``*.worldbank.org``).

    Returns:
        Compiled regex, or None if patterns list is empty.
    """
    if not patterns:
        return None
    regex_parts = []
    for p in patterns:
        # Escape everything; replace * with [^.]* (single-segment wildcard, no dots).
        # Using .* would allow nested greedy groups → ReDoS on adversarial input.
        escaped = re.escape(p).replace(r"\*", r"[^.]*")
        regex_parts.append(escaped)
    combined = "|".join(regex_parts)
    # Match http/https URLs containing the pattern
    return re.compile(
        r"https?://(?:" + combined + r")[^\s\"'\n]*",
        re.IGNORECASE,
    )


def apply_regex_filter(
    content: str, config: Optional[TeamBrainConfig] = None
) -> Tuple[str, List[Redaction]]:
    """Apply the deterministic regex privacy layer to content.

    Strips: Windows paths, Unix system paths, UNC paths, email addresses,
    credential-adjacent strings, and configurable internal URLs.
    Does NOT redact relative paths (``./foo``, ``../bar``).

    Args:
        content: Raw markdown content to filter.
        config: Optional TeamBrainConfig for internal URL patterns.

    Returns:
        Tuple of (filtered_content, list_of_redactions).

    Example::

        filtered, redactions = apply_regex_filter(
            "Path: E:\\\\PovcalNet\\\\data\\\\file.dta",
            config=None,
        )
        assert "<REDACTED:path>" in filtered
        assert len(redactions) == 1
    """
    redactions: List[Redaction] = []
    lines = content.splitlines(keepends=True)
    result_lines: List[str] = []

    url_pattern = _build_url_pattern(config.internal_url_patterns if config else [])

    for line_num, line in enumerate(lines, start=1):

        # Windows paths
        for m in reversed(list(_WIN_PATH_RE.finditer(line))):
            redactions.append(
                Redaction("regex", "path", line_num, len(m.group()))
            )
            line = line[: m.start()] + "<REDACTED:path>" + line[m.end() :]

        # UNC paths
        for m in reversed(list(_UNC_PATH_RE.finditer(line))):
            redactions.append(
                Redaction("regex", "path", line_num, len(m.group()))
            )
            line = line[: m.start()] + "<REDACTED:path>" + line[m.end() :]

        # Unix system paths
        for m in reversed(list(_UNIX_PATH_RE.finditer(line))):
            redactions.append(
                Redaction("regex", "path", line_num, len(m.group()))
            )
            line = line[: m.start()] + "<REDACTED:path>" + line[m.end() :]

        # Internal URLs (before email to avoid double-matching)
        if url_pattern:
            for m in reversed(list(url_pattern.finditer(line))):
                redactions.append(
                    Redaction("regex", "url", line_num, len(m.group()))
                )
                line = line[: m.start()] + "<REDACTED:url>" + line[m.end() :]

        # Email addresses
        for m in reversed(list(_EMAIL_RE.finditer(line))):
            redactions.append(
                Redaction("regex", "email", line_num, len(m.group()))
            )
            line = line[: m.start()] + "<REDACTED:email>" + line[m.end() :]

        # Credentials
        for m in reversed(list(_CREDENTIAL_RE.finditer(line))):
            redactions.append(
                Redaction("regex", "credential", line_num, len(m.group()))
            )
            line = line[: m.start()] + "<REDACTED:credential>" + line[m.end() :]

        result_lines.append(line)

    return "".join(result_lines), redactions


# ---------------------------------------------------------------------------
# Frontmatter layer
# ---------------------------------------------------------------------------

#: Heading pattern for section extraction
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _extract_private_sections(body: str, section_names: List[str]) -> str:
    """Remove named sections from a markdown body.

    Removes sections matching any name in ``section_names`` along with all
    content under that heading until the next heading of equal or higher level.

    Args:
        body: Full markdown body (without frontmatter).
        section_names: List of heading names to strip.

    Returns:
        Markdown body with matching sections removed.
    """
    if not section_names:
        return body

    lower_names = {n.strip().lower() for n in section_names}
    lines = body.splitlines(keepends=True)
    result: List[str] = []
    skip_until_level: Optional[int] = None

    for line in lines:
        m = _HEADING_RE.match(line.rstrip())
        if m:
            level = len(m.group(1))
            # Strip trailing closing # (ATX closed headings: ## Title ##)
            title = m.group(2).strip().rstrip("#").strip().lower()
            if title in lower_names:
                skip_until_level = level
                continue
            if skip_until_level is not None and level <= skip_until_level:
                skip_until_level = None
        if skip_until_level is None:
            result.append(line)

    return "".join(result)


def apply_frontmatter_filter(
    content: str,
    frontmatter: Dict,
) -> Tuple[str, bool, str]:
    """Apply the frontmatter-declared privacy rules.

    Checks ``private: true`` (block entire entry) and
    ``private-sections: [...]`` (strip named sections from body).
    Default is ``private: false`` — entries are pushed unless explicitly
    opted out.

    Args:
        content: Full markdown content (including frontmatter delimiter lines).
        frontmatter: Parsed frontmatter dictionary.

    Returns:
        Tuple of (filtered_content, blocked, block_reason).
        If blocked is True, filtered_content is empty.

    Example::

        filtered, blocked, reason = apply_frontmatter_filter(
            "---\\nprivate: true\\n---\\n# Title\\n",
            {"private": True},
        )
        assert blocked is True
    """
    private = frontmatter.get("private", False)
    if isinstance(private, str):
        private = private.strip().lower() in ("true", "yes", "1")

    if private:
        return "", True, "Entry marked 'private: true' in frontmatter"

    private_sections_raw = frontmatter.get("private-sections", [])
    if not isinstance(private_sections_raw, list):
        warnings.warn(
            "Frontmatter 'private-sections' is not a list — ignoring section filtering.",
            UserWarning,
            stacklevel=2,
        )
        private_sections: List[str] = []
    else:
        private_sections = [str(s) for s in private_sections_raw]

    if not private_sections:
        return content, False, ""

    # Split frontmatter from body
    lines = content.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break
        if end_idx is not None:
            fm_block = "".join(lines[: end_idx + 1])
            body = "".join(lines[end_idx + 1 :])
            filtered_body = _extract_private_sections(body, private_sections)
            return fm_block + filtered_body, False, ""

    # No frontmatter delimiters found — treat entire content as body
    return _extract_private_sections(content, private_sections), False, ""


# ---------------------------------------------------------------------------
# LLM layer prompt builder
# ---------------------------------------------------------------------------

_LLM_LAYER_PROMPT_TEMPLATE = """\
You are a privacy filter for a shared knowledge base. The content below has
already been processed by a regex filter that removed absolute paths, email
addresses, and credential strings. Your job is to find ADDITIONAL sensitive
content that the regex missed.

Look ONLY for these categories (do NOT re-flag what the regex already handled):
1. Project-identifying jargon — team-specific terminology that reveals the
   project or organization (e.g., internal code names, product aliases).
2. Internal system names — database names, server hostnames, internal tool
   names not in the public domain.
3. Domain-specific secrets — internal classification codes, budget references,
   proprietary methodology names.
4. Overly specific examples — examples so specific to one project that they
   should be generalized for reuse.

For each finding, output a JSON object on its own line:
  {{"line": <1-based line number>, "type": "<jargon|system-name|secret|specific-example>", "original": "<exact text>", "replacement": "<generalized version>"}}

If no additional sensitive content is found, output exactly:
  {{"findings": []}}

CONTENT TO REVIEW:
---
{content}
---
"""


def build_llm_filter_prompt(content: str) -> str:
    """Build the prompt for the LLM privacy layer.

    The LLM layer scans for contextual sensitivity the regex missed.
    This function returns the prompt text; the caller invokes the LLM.

    Args:
        content: Post-regex-filtered content.

    Returns:
        Prompt string for the LLM.
    """
    return _LLM_LAYER_PROMPT_TEMPLATE.format(content=content)


def apply_llm_redactions(
    content: str,
    llm_findings: List[Dict],
) -> Tuple[str, List[Redaction]]:
    """Apply LLM-suggested redactions to content.

    LLM findings are auto-applied (non-blocking). Results are logged in the
    returned redaction list for the push confirmation summary.

    Args:
        content: Post-regex-filtered content.
        llm_findings: List of finding dicts from LLM output, each with keys:
            ``line`` (int), ``type`` (str), ``original`` (str), ``replacement`` (str).

    Returns:
        Tuple of (filtered_content, list_of_llm_redactions).
    """
    redactions: List[Redaction] = []
    for finding in llm_findings:
        original = finding.get("original", "")
        replacement = finding.get("replacement", "<REDACTED:llm>")
        finding_type = finding.get("type", "unknown")
        line_num = finding.get("line", 0)
        if original and original in content:
            content = content.replace(original, replacement, 1)
            redactions.append(
                Redaction("llm", finding_type, line_num, len(original))
            )
    return content, redactions


# ---------------------------------------------------------------------------
# Full pipeline orchestrator
# ---------------------------------------------------------------------------


def run_privacy_filter(
    content: str,
    frontmatter: Dict,
    config: Optional[TeamBrainConfig] = None,
    llm_findings: Optional[List[Dict]] = None,
) -> FilterResult:
    """Run the full 3-layer privacy filter pipeline.

    Layers applied in order:
    1. Frontmatter check (may block entirely)
    2. Regex redaction
    3. LLM redactions (if llm_findings provided)

    Args:
        content: Full markdown content to filter.
        frontmatter: Parsed frontmatter dictionary.
        config: Optional TeamBrainConfig for internal URL patterns.
        llm_findings: Optional list of LLM-suggested redactions to apply.
            Pass None to skip the LLM layer (e.g., ``--no-llm`` mode).

    Returns:
        FilterResult with clean_content, all redactions, and blocked status.

    Example::

        result = run_privacy_filter(
            content="# Title\\n\\nPath: E:\\\\data\\\\file.dta",
            frontmatter={},
            config=None,
        )
        assert not result.blocked
        assert "<REDACTED:path>" in result.clean_content
    """
    # Step 1: Frontmatter filter (may short-circuit before regex)
    filtered, blocked, block_reason = apply_frontmatter_filter(content, frontmatter)
    if blocked:
        return FilterResult(
            clean_content="",
            redactions=[],
            blocked=True,
            block_reason=block_reason,
        )

    # Step 2: Regex filter (deterministic path/email/credential stripping)
    filtered, regex_redactions = apply_regex_filter(filtered, config)

    # Step 3: LLM filter (auto-applied if findings provided)
    llm_redactions: List[Redaction] = []
    if llm_findings:
        filtered, llm_redactions = apply_llm_redactions(filtered, llm_findings)
        # Re-run regex after LLM: a jailbroken LLM could inject absolute paths as replacement
        # strings. The second pass is cheap (deterministic) and eliminates that attack surface.
        filtered, post_llm_redactions = apply_regex_filter(filtered, config)
        regex_redactions = regex_redactions + post_llm_redactions

    return FilterResult(
        clean_content=filtered,
        redactions=regex_redactions + llm_redactions,
        blocked=False,
        block_reason="",
    )
