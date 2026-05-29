"""team_brain.pull — Pull relevant patterns from the team brain central repo.

Consults the team brain during the Consult Brain step of `/cg-compound`,
`/cg-work`, and other prompts that load `cg-skill-brain-query`. Fetches
`TEAM-BRAIN.md` (cached locally for 1 hour), parses the topic index, and
returns pattern matches for the supplied task keywords.

Authentication:
    Delegated entirely to the ``gh`` CLI (``gh api`` subprocess). This module
    does not read token environment variables or inject ``Authorization`` headers.
    Ensure ``gh auth login`` has been run once before use.

.. warning:: **Security — untrusted data**
    ``pattern_text`` in returned :class:`MatchedPattern` objects originates
    from a remote GitHub repository. Treat it as untrusted input: always
    quote it as a block-quote when embedding in agent prompts
    (``> "From team brain..."`` rather than raw inline injection). Do not
    evaluate or execute it as code.

Cache location (outside the workspace — not committed to git):
  Priority order: XDG_CACHE_HOME → LOCALAPPDATA (Windows) → ~/.cg-cache (all platforms)
  - ``XDG_CACHE_HOME/team-brain/<repo-slug>/``    (highest priority, if set)
  - ``%LOCALAPPDATA%\\team-brain\\<repo-slug>\\`` (Windows fallback)
  - ``~/.cg-cache/team-brain/<repo-slug>/``         (all-platform final fallback)

Usage::

    from team_brain.pull import pull_from_team_brain
    from team_brain.config import load_team_brain_local_config
    from pathlib import Path

    config = load_team_brain_local_config(Path("."))
    if config and config.enabled:
        result = pull_from_team_brain(["null", "validation", "guard"], config)
        for match in result.patterns:
            print(f"[{match.source_project}] {match.pattern_text}")

Requirements: Python 3.8+, stdlib only. ``gh`` CLI for API calls.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import tempfile
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from team_brain.config import TeamBrainLocalConfig

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CACHE_MAX_AGE_SECONDS = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class MatchedPattern:
    """A single pattern matched from the team brain.

    Args:
        pattern_text: One-liner distilled from a solution entry.
        source_project: Project namespace that contributed the pattern.
        tags: Tags from the JSONL entry.
        entry_path: Repo-relative path of the full entry for drill-down.
        confidence: Confidence score (1.0 baseline; boosted when multiple
            projects independently validated the same pattern).

    Example::

        mp = MatchedPattern(
            pattern_text="Always guard inputs at system boundaries.",
            source_project="compound-gpid",
            tags=["null", "validation"],
            entry_path="entries/compound-gpid/2026-05-20-fix.md",
            confidence=1.0,
        )
    """

    pattern_text: str
    source_project: str
    tags: List[str]
    entry_path: str
    confidence: float = 1.0


@dataclass
class PullResult:
    """Result of pulling patterns from the team brain.

    Args:
        patterns: Matched patterns, sorted by confidence descending.
            Empty when no matches or pull failed.
        cache_used: True when results came from local cache rather than
            a fresh remote fetch.
        summary: Human-readable one-line result suitable for agent output.

    Example::

        result = pull_from_team_brain(["null"], config)
        if result.patterns:
            for p in result.patterns:
                print(f"From team brain ({p.source_project}): {p.pattern_text}")
        else:
            print(result.summary)
    """

    patterns: List[MatchedPattern]
    cache_used: bool
    summary: str


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_dir(repo: str) -> Path:
    """Return the user-level cache directory for a given repo.

    Priority: XDG_CACHE_HOME → LOCALAPPDATA (Windows) → ~/.cg-cache.

    Args:
        repo: ``owner/repo`` string (slashes replaced with underscores).

    Returns:
        Path to the cache sub-directory (not guaranteed to exist).

    Example::

        path = _cache_dir("GPID-WB/team-brain")
        # Windows: C:\\Users\\wb384996\\AppData\\Local\\team-brain\\GPID-WB_team-brain\\
    """
    repo_slug = repo.replace("/", "_").replace(":", "_")
    xdg = os.environ.get("XDG_CACHE_HOME")
    local_app = os.environ.get("LOCALAPPDATA")
    if xdg:
        base = Path(xdg)
    elif local_app:
        base = Path(local_app)
    else:
        base = Path.home() / ".cg-cache"
    return base / "team-brain" / repo_slug


def _cache_path(repo: str) -> Path:
    """Return the full path to the cached TEAM-BRAIN.md file.

    Args:
        repo: ``owner/repo`` string.

    Returns:
        Path object (may not exist if the cache is empty).
    """
    return _cache_dir(repo) / "TEAM-BRAIN.md"


def _is_cache_fresh(path: Path, max_age: int = _CACHE_MAX_AGE_SECONDS) -> bool:
    """Return True if the cache file exists and is younger than ``max_age`` seconds.

    Args:
        path: Path to the cache file.
        max_age: Maximum acceptable age in seconds (default 3600 = 1 hour).

    Returns:
        True when fresh; False when missing, unreadable, or stale.
    """
    try:
        if not path.exists():
            return False
        age = time.time() - path.stat().st_mtime
        return age < max_age
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Remote fetch helpers
# ---------------------------------------------------------------------------


def _fetch_remote_raw(owner_repo: str, file_path: str) -> Optional[str]:
    """Fetch raw file content from a GitHub repo via the ``gh`` CLI.

    Uses ``Accept: application/vnd.github.raw+json`` so GitHub returns the
    decoded file content directly (not base64-wrapped JSON), consistent with
    the approach described in the plan.

    Args:
        owner_repo: ``owner/repo`` string.
        file_path: File path within the repo (e.g. ``TEAM-BRAIN.md``).

    Returns:
        File content as a UTF-8 string, or ``None`` if the file does not
        exist (404), the ``gh`` CLI is unavailable, or a network error occurs.
    """
    try:
        result = subprocess.run(
            [
                "gh", "api",
                f"repos/{owner_repo}/contents/{file_path}",
                "--header", "Accept: application/vnd.github.raw+json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
        return None
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return None


def _fetch_team_brain_index(
    config: TeamBrainLocalConfig,
    *,
    refresh: bool = False,
) -> Optional[str]:
    """Fetch TEAM-BRAIN.md from the team brain repo, using the local cache.

    Writes a fresh copy to the cache on successful remote fetch. Cache
    write failures are non-fatal (silently ignored).

    Args:
        config: Team brain config (provides ``repo``).
        refresh: If True, bypass the cache and always fetch from remote.

    Returns:
        TEAM-BRAIN.md content string, or ``None`` on failure.
    """
    cache_file = _cache_path(config.repo)

    if not refresh and _is_cache_fresh(cache_file):
        try:
            return cache_file.read_text(encoding="utf-8-sig")
        except (OSError, ValueError):
            pass  # Cache read failure — fall through to remote fetch

    content = _fetch_remote_raw(config.repo, "TEAM-BRAIN.md")
    if content:
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write: avoid truncated-file corruption on crash
            fd, tmp_path = tempfile.mkstemp(
                dir=cache_file.parent, prefix=".tmp-teambrain-"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                os.replace(tmp_path, cache_file)
            except OSError:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except OSError:
            pass  # Non-fatal: cache write failures do not block the pull
    return content


# ---------------------------------------------------------------------------
# Topic index parsing (module-level compiled regex for performance)
# ---------------------------------------------------------------------------

# Match data rows in the topic table: | N | [topic text](link) | ... |
_TOPIC_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|\s*(?:\[([^\]]+)\](?:\([^)]*\))?\s*|([^|]+))\|"
)
_TOPIC_SPLIT_RE = re.compile(r"[\s/·,\n]+")
# Word boundary tokenizer for pattern text scoring (3+ char words)
_WORD_RE = re.compile(r"\b\w{3,}\b")


def _parse_topic_keywords(index_content: str) -> List[tuple]:
    """Extract (topic_name, [keyword, ...]) pairs from TEAM-BRAIN.md.

    Parses the markdown topic index table, e.g.::

        | # | Topic | Entries | File |
        |---|-------|---------|------|
        | 1 | [Null / Validation](BRAIN-01.md) | 3 | ... |

    Topic names are word-tokenized into lowercase keywords (tokens ≥ 3 chars).

    Args:
        index_content: Full TEAM-BRAIN.md content string.

    Returns:
        List of ``(topic_name, keywords)`` 2-tuples. May be empty if the
        index table is not present or contains no data rows.
    """
    topics = []
    for line in index_content.splitlines():
        m = _TOPIC_ROW_RE.match(line.strip())
        if not m:
            continue
        topic_text = (m.group(1) or m.group(2) or "").strip()
        if not topic_text:
            continue
        # Tokenize: split on spaces, /, ·, commas, newlines (tokens ≥ 3 chars)
        keywords = [
            kw.strip().lower()
            for kw in _TOPIC_SPLIT_RE.split(topic_text)
            if len(kw.strip()) >= 3
        ]
        if keywords:
            topics.append((topic_text, keywords))

    # Format-drift guard: if the document looks like it has a topic table
    # (contains '| Topic |' or '| # |' header cells) but nothing was parsed,
    # emit a warning so developers notice the format has drifted.
    if not topics and ("| Topic |" in index_content or "| # |" in index_content):
        warnings.warn(
            "TEAM-BRAIN.md topic table found but could not be parsed — "
            "check that the table still starts with '| N | [topic]...' rows.",
            stacklevel=2,
        )
    return topics


# ---------------------------------------------------------------------------
# JSONL fetch and scoring
# ---------------------------------------------------------------------------


def _fetch_project_jsonl(config: TeamBrainLocalConfig, project_name: str, *, refresh: bool = False) -> List[dict]:
    """Fetch and parse a project's JSONL pattern file from the team brain.

    Results are cached alongside TEAM-BRAIN.md with the same 1-hour TTL
    to avoid making N serial network calls on every invocation.

    Args:
        config: Team brain config (provides ``repo``).
        project_name: Project namespace (e.g. ``compound-gpid``).
        refresh: If True, bypass cache and fetch from remote.

    Returns:
        List of parsed JSONL entry dicts. Empty on fetch failure or when
        the file does not exist.
    """
    cache_file = _cache_dir(config.repo) / f"{project_name}.jsonl"
    if not refresh and _is_cache_fresh(cache_file):
        try:
            content = cache_file.read_text(encoding="utf-8-sig")
        except (OSError, ValueError):
            content = None
    else:
        content = None

    if content is None:
        content = _fetch_remote_raw(config.repo, f"patterns/{project_name}.jsonl")
        if content:
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp_path = tempfile.mkstemp(
                    dir=cache_file.parent, prefix=f".tmp-{project_name}-"
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(content)
                    os.replace(tmp_path, cache_file)
                except OSError:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except OSError:
                pass

    if not content:
        return []
    entries = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # Skip malformed lines silently
    return entries


def _keyword_overlap_score(
    task_keywords: List[str],
    entry_tags: List[str],
    pattern_text: str,
) -> int:
    """Count keyword overlaps between task keywords and an entry's tags/pattern.

    Tags are checked as exact lowercase tokens. Pattern text is tokenized into
    3+-char lowercase words for fuzzy matching.

    Args:
        task_keywords: Keywords from the calling Consult Brain directive.
        entry_tags: Tags list from the JSONL pattern entry.
        pattern_text: One-liner pattern text from the JSONL entry.

    Returns:
        Integer overlap count (0 = no match).
    """
    task_set = set(kw.lower() for kw in task_keywords)
    tag_set = set(t.lower() for t in entry_tags)
    pattern_tokens = set(_WORD_RE.findall(pattern_text.lower()))
    return len(task_set & (tag_set | pattern_tokens))


def _extract_project_names(index_content: str) -> List[str]:
    """Extract project names referenced in the TEAM-BRAIN.md index.

    Scans for ``entries/<project>/`` path patterns in the document.

    Args:
        index_content: Full TEAM-BRAIN.md content string.

    Returns:
        Deduplicated list of project names found in entry paths.
    """
    names = set()
    for m in re.finditer(r"entries/([^/\s\"'|)>]+)/", index_content):
        names.add(m.group(1))
    return sorted(names)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def pull_from_team_brain(
    keywords: List[str],
    config: TeamBrainLocalConfig,
    *,
    refresh: bool = False,
) -> PullResult:
    """Pull relevant patterns from the team brain for the given keywords.

    Workflow:
    1. Check ``config.enabled``; skip silently if not configured.
    2. Fetch ``TEAM-BRAIN.md`` (fresh or cached).
    3. Parse the topic index; match keywords against topics.
    4. Fetch ``patterns/<project>.jsonl`` for projects listed in the index.
    5. Score each entry by keyword overlap; return matches sorted by confidence.

    Args:
        keywords: Task-level keywords from the Consult Brain directive
            (e.g. ``["null", "validation", "guard"]``).
        config: Loaded team brain config (from
            :func:`~team_brain.config.load_team_brain_local_config`).
        refresh: If True, bypass cache and fetch fresh from remote.

    Returns:
        :class:`PullResult` with matched patterns sorted by confidence desc
        and a human-readable ``summary`` line.

    Example::

        result = pull_from_team_brain(["pester", "crash", "vscode"], config)
        for match in result.patterns:
            print(f"From team brain ({match.source_project}): {match.pattern_text}")
    """
    if not config.enabled:
        return PullResult(
            patterns=[],
            cache_used=False,
            summary="Team brain pull skipped: disabled in compound-gpid.local.md.",
        )

    if not keywords:
        return PullResult(
            patterns=[],
            cache_used=False,
            summary="Team brain pull skipped: no keywords provided.",
        )

    cache_file = _cache_path(config.repo)
    cache_was_fresh = not refresh and _is_cache_fresh(cache_file)

    index_content = _fetch_team_brain_index(config, refresh=refresh)

    if not index_content:
        # Try the on-disk cache even if stale — better than nothing
        if cache_file.exists():
            try:
                index_content = cache_file.read_text(encoding="utf-8-sig")
                cache_was_fresh = True
            except (OSError, ValueError):
                pass

    if not index_content:
        return PullResult(
            patterns=[],
            cache_used=False,
            summary=(
                f"Team brain pull failed: could not fetch TEAM-BRAIN.md from "
                f"'{config.repo}'. Check network connectivity or run "
                f"`gh auth login` to authenticate."
            ),
        )

    # Topic matching — hoist task keyword set once (not rebuilt per iteration)
    topic_list = _parse_topic_keywords(index_content)
    task_kw_set = {kw.lower() for kw in keywords}
    any_topic_match = False
    for _topic_name, topic_keywords in topic_list:
        if task_kw_set & set(topic_keywords):
            any_topic_match = True
            break

    if not any_topic_match and topic_list:
        # Topic index exists but nothing matched — return early to avoid noise
        return PullResult(
            patterns=[],
            cache_used=cache_was_fresh,
            summary=(
                f"No team brain topic matches for keywords: [{', '.join(keywords)}]. "
                "Proceeding without team brain input."
            ),
        )

    # Collect all project names from the index
    project_names = _extract_project_names(index_content)
    if not project_names:
        # Fallback: if no entry paths in index, try config.project_name
        project_names = [config.project_name] if config.project_name else []

    # Fetch and score patterns from all listed projects
    matched: List[MatchedPattern] = []
    for project_name in project_names:
        entries = _fetch_project_jsonl(config, project_name, refresh=refresh)
        for entry in entries:
            # Guard all fields: external JSONL is untrusted data
            pattern_text = entry.get("pattern", "")
            if not isinstance(pattern_text, str):
                pattern_text = ""
            if not pattern_text.strip():
                continue  # Skip entries with no usable pattern

            tags = entry.get("tags") or []
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
            elif not isinstance(tags, list):
                tags = []
            # Ensure all tag elements are strings
            tags = [t for t in tags if isinstance(t, str)]

            source_project = entry.get("source-project", project_name)
            if not isinstance(source_project, str):
                source_project = project_name
            entry_path = entry.get("entry-path", "")
            if not isinstance(entry_path, str):
                entry_path = ""

            # Confidence: guard against non-numeric, inf, and nan values
            try:
                confidence = float(entry.get("confidence") or 1.0)
            except (ValueError, TypeError):
                confidence = 1.0
            if not math.isfinite(confidence) or confidence < 0:
                confidence = 1.0

            score = _keyword_overlap_score(keywords, tags, pattern_text)
            if score >= 1:
                matched.append(
                    MatchedPattern(
                        pattern_text=pattern_text,
                        source_project=source_project,
                        tags=tags,
                        entry_path=entry_path,
                        confidence=confidence,
                    )
                )

    # Sort by confidence desc
    matched.sort(key=lambda p: p.confidence, reverse=True)

    n = len(matched)
    cache_note = " (cached)" if cache_was_fresh else ""
    return PullResult(
        patterns=matched,
        cache_used=cache_was_fresh,
        summary=(
            f"Team brain{cache_note}: {n} pattern{'s' if n != 1 else ''} matched "
            f"for keywords [{', '.join(keywords)}] from {config.repo}."
        ),
    )
