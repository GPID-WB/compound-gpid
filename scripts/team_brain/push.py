"""team_brain.push — Push a solution entry to the team brain central repo.

Uses the GitHub Contents API (stdlib urllib only — no third-party deps).

Token lookup order (never printed, never logged):
  1. Caller-provided ``token`` argument
  2. ``GITHUB_TOKEN`` environment variable
  3. ``GH_TOKEN`` environment variable
  4. ``gh auth token`` subprocess (GitHub CLI)
  5. ``git credential fill`` subprocess fallback (Windows Credential Manager)

Usage (from cg-index)::

    cg-index --push-entry .cg-docs/solutions/bugs/2026-05-20-my-fix.md

Requirements: Python 3.8+, stdlib only.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
import warnings
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Literal

from team_brain.config import TeamBrainLocalConfig, load_team_brain_local_config
from team_brain.distiller import distill_pattern
from team_brain.privacy import run_privacy_filter
from team_brain.schema import PatternEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GITHUB_API = "https://api.github.com"
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)^---\s*\n", re.DOTALL | re.MULTILINE)


# ---------------------------------------------------------------------------
# HTTP redirect guard (SEC-P0.1)
# ---------------------------------------------------------------------------

class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject all HTTP redirects to prevent Authorization header forwarding.

    Python's default HTTPRedirectHandler copies all headers (except
    content-length) to redirect targets. A GitHub 301 to an attacker-
    controlled endpoint would receive the full Bearer token.
    """

    def redirect_request(  # type: ignore[override]
        self, req: urllib.request.Request, fp: object, code: int,
        msg: str, headers: object, newurl: str,
    ) -> None:
        raise urllib.error.HTTPError(
            req.full_url, code,
            f"Redirect to {newurl!r} blocked (would forward Authorization header)",
            headers,  # type: ignore[arg-type]
            None,
        )


_opener = urllib.request.build_opener(_NoRedirectHandler())

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class PushResult:
    """Result of a team brain push operation.

    Args:
        action: One of ``created``, ``updated``, ``skipped``, ``blocked``,
            or ``dry-run``.
        entry_path: Relative path of the markdown entry in the central repo
            (e.g. ``entries/project/2026-05-20-fix.md``).
        jsonl_path: Relative path of the JSONL patterns file
            (e.g. ``patterns/project.jsonl``).
        summary: Human-readable one-line summary suitable for agent output.

    Example::

        result = push_entry(Path(".cg-docs/solutions/bugs/fix.md"), config)
        print(result.summary)
    """

    action: Literal["created", "updated", "skipped", "blocked", "dry-run"]
    entry_path: str
    jsonl_path: str
    summary: str


# ---------------------------------------------------------------------------
# Token resolution
# ---------------------------------------------------------------------------


def get_token(explicit: str | None = None) -> str | None:
    """Resolve a GitHub personal access token.

    Tries sources in order:
    1. ``explicit`` argument (caller-provided)
    2. ``GITHUB_TOKEN`` environment variable
    3. ``GH_TOKEN`` environment variable
    4. ``gh auth token`` subprocess (GitHub CLI — most reliable, cross-platform)
    5. ``git credential fill`` subprocess (Windows Credential Manager, etc.)

    The token is never printed or logged.

    Args:
        explicit: Caller-provided token override.

    Returns:
        Token string, or None if no token could be found.

    Example::

        token = get_token()
        if token is None:
            raise ValueError("No GitHub token available.")
    """
    if explicit:
        return explicit
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        val = os.environ.get(var)
        if val:
            return val
    # gh CLI — preferred: handles token refresh, works in non-interactive shells
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        pass
    # Fallback: git credential fill (Windows Credential Manager, macOS Keychain, etc.)
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        for line in result.stdout.splitlines():
            if line.startswith("password="):
                return line[len("password="):].strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return None


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split markdown content into a frontmatter dict and the body text.

    Handles quoted strings, inline lists (``[a, b]``), and boolean values.
    Returns ``({}, content)`` if no frontmatter block is present.

    Args:
        content: Full markdown file content.

    Returns:
        Tuple of (frontmatter_dict, body_text).

    Example::

        fm, body = _parse_frontmatter("---\\ndate: 2026-05-20\\n---\\n# Title\\n")
        assert fm["date"] == "2026-05-20"
    """
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return {}, content

    fm_text = m.group(1)
    body = content[m.end():]
    fm: dict = {}

    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, raw_val = line.partition(":")
        key = key.strip()
        val = raw_val.strip()
        # Strip outer quotes FIRST, then strip trailing inline comment.
        # If we stripped the comment before unquoting, a title like
        # `title: "My Fix #1"` would be truncated to `"My Fix` (quote + partial text).
        if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
            val = val[1:-1]
        elif " #" in val:
            # Only strip unquoted inline comments (space before #)
            val = val[: val.index(" #")].rstrip()
        # Handle inline lists: [tag1, tag2]
        if val.startswith("[") and val.endswith("]"):
            fm[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            continue
        # Coerce booleans
        if val.lower() == "true":
            fm[key] = True
        elif val.lower() == "false":
            fm[key] = False
        else:
            fm[key] = val

    return fm, body


# ---------------------------------------------------------------------------
# Pattern distillation
# ---------------------------------------------------------------------------


def _distill_pattern(frontmatter: dict, body: str) -> str:
    """Backward-compatible wrapper — delegates to :func:`team_brain.distiller.distill_pattern`.

    Returns the plain ``pattern_text`` string. Use :func:`distill_pattern`
    directly when the :class:`~team_brain.distiller.DistillResult` metadata
    (source label, LLM prompt) is needed.

    Args:
        frontmatter: Parsed frontmatter dictionary.
        body: Markdown body text (after the frontmatter block).

    Returns:
        One-liner pattern string, truncated to 200 characters.

    Example::

        pattern = _distill_pattern({"root-cause": "Missing null check."}, "")
        assert pattern == "Missing null check."
    """
    return distill_pattern(frontmatter, body).pattern_text


# ---------------------------------------------------------------------------
# GitHub Contents API helpers
# ---------------------------------------------------------------------------


def _api_request(
    method: str,
    url: str,
    token: str,
    body: dict | None = None,
) -> tuple[int, dict]:
    """Make a GitHub REST API request.

    Never logs or prints the token.

    Args:
        method: HTTP method (``GET``, ``PUT``, ``PATCH``).
        url: Full API URL.
        token: GitHub token.
        body: Optional JSON body for PUT/PATCH requests.

    Returns:
        Tuple of (http_status_code, response_dict).
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "compound-gpid/team-brain-push",
    }
    if not url.startswith("https://"):
        raise ValueError(f"_api_request requires HTTPS; got: {url!r}")
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _opener.open(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            error_body = json.loads(raw)
        except json.JSONDecodeError:
            error_body = {"message": raw[:200]}
        return exc.code, error_body


def _get_remote_file(
    owner_repo: str,
    path: str,
    token: str,
) -> tuple[str, str] | None:
    """Fetch a file from the GitHub repo.

    Args:
        owner_repo: ``owner/repo`` string.
        path: File path relative to the repo root.
        token: GitHub token.

    Returns:
        ``(sha, decoded_content)`` if the file exists, ``None`` if 404.

    Raises:
        RuntimeError: On unexpected HTTP errors (not 200 or 404).
    """
    url = f"{_GITHUB_API}/repos/{owner_repo}/contents/{path}"
    status, data = _api_request("GET", url, token)
    if status == 404:
        return None
    if status != 200:
        raise RuntimeError(
            f"Unexpected HTTP {status} fetching {path}: {data.get('message', '')}"
        )
    sha = data["sha"]
    decoded = base64.b64decode(data["content"]).decode("utf-8")
    return sha, decoded


def _put_remote_file(
    owner_repo: str,
    path: str,
    token: str,
    content: str,
    message: str,
    sha: str | None = None,
) -> None:
    """Create or update a file in the GitHub repo via the Contents API.

    Args:
        owner_repo: ``owner/repo`` string.
        path: File path relative to repo root.
        token: GitHub token.
        content: UTF-8 text content to write.
        message: Commit message.
        sha: Existing file SHA (required when updating an existing file).

    Raises:
        RuntimeError: If the API returns a non-2xx status.
    """
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload: dict = {"message": message, "content": encoded}
    if sha:
        payload["sha"] = sha
    url = f"{_GITHUB_API}/repos/{owner_repo}/contents/{path}"
    status, data = _api_request("PUT", url, token, payload)
    if status not in (200, 201):
        raise RuntimeError(
            f"Failed to push {path} (HTTP {status}): {data.get('message', '')}"
        )


def _put_jsonl_with_retry(
    owner_repo: str,
    path: str,
    token: str,
    new_line: str,
    entry_id: str,
    commit_msg: str,
    max_retries: int = 3,
) -> None:
    """Upsert a JSONL patterns file with exponential back-off on SHA races.

    A 409 or 422 response means a concurrent push updated the file between
    our GET and our PUT.  We re-fetch the current SHA and retry.

    Args:
        owner_repo: ``owner/repo`` string.
        path: JSONL file path in the central repo.
        token: GitHub token.
        new_line: Serialized JSON line to upsert.
        entry_id: ``id`` field of the entry being upserted.
        commit_msg: Commit message for the PUT.
        max_retries: Maximum number of retry attempts (default 3).

    Raises:
        RuntimeError: If all retries are exhausted or an unexpected HTTP
            error occurs.
    """
    for attempt in range(max_retries + 1):
        existing_jsonl = _get_remote_file(owner_repo, path, token)
        if existing_jsonl:
            jsonl_sha, jsonl_content = existing_jsonl
            updated_jsonl, was_replaced = _upsert_jsonl_line(jsonl_content, new_line, entry_id)
            jsonl_commit_msg = commit_msg + (" (update)" if was_replaced else " (append)")
            encoded = base64.b64encode(updated_jsonl.encode("utf-8")).decode("ascii")
            payload: dict = {
                "message": jsonl_commit_msg,
                "content": encoded,
                "sha": jsonl_sha,
            }
        else:
            initial_content = new_line + "\n"
            encoded = base64.b64encode(initial_content.encode("utf-8")).decode("ascii")
            payload = {"message": commit_msg + " (initialize)", "content": encoded}

        url = f"{_GITHUB_API}/repos/{owner_repo}/contents/{path}"
        status, data = _api_request("PUT", url, token, payload)
        if status in (200, 201):
            return
        if status in (409, 422) and attempt < max_retries:
            # Stale SHA — concurrent push beat us; back off and retry
            time.sleep(2 ** attempt)
            continue
        raise RuntimeError(
            f"Failed to push {path} (HTTP {status}) after {attempt + 1} attempt(s): "
            f"{data.get('message', '')}"
        )


# ---------------------------------------------------------------------------
# JSONL merge helpers
# ---------------------------------------------------------------------------


def _upsert_jsonl_line(existing_content: str, new_line: str, entry_id: str) -> tuple[str, bool]:
    """Insert or replace an entry in JSONL content.

    Replaces the line whose ``id`` matches ``entry_id``, or appends the new
    line if no match is found.

    Args:
        existing_content: Current text content of the JSONL file.
        new_line: Serialized JSON line for the new/updated entry.
        entry_id: ``id`` field of the entry being upserted.

    Returns:
        Tuple of (updated_jsonl_text, was_replaced). ``was_replaced`` is True
        if an existing entry was updated, False if a new line was appended.
    """
    lines = [ln for ln in existing_content.splitlines() if ln.strip()]
    replaced = False
    for i, line in enumerate(lines):
        try:
            parsed = json.loads(line)
            if parsed.get("id") == entry_id:
                lines[i] = new_line
                replaced = True
                break
        except json.JSONDecodeError:
            warnings.warn(
                f"Skipping malformed JSONL line {i + 1} in existing file; "
                "it will be preserved as-is.",
                stacklevel=3,
            )
            continue
    if not replaced:
        lines.append(new_line)
    return "\n".join(lines) + "\n", replaced


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------


def push_entry(
    solution_path: Path,
    config: TeamBrainLocalConfig | None = None,
    token: str | None = None,
    *,
    dry_run: bool = False,
    local_config_path: Path | None = None,
) -> PushResult:
    """Push a solution entry to the team brain central repo.

    Reads the solution file, runs the privacy filter, builds a JSONL pattern
    entry, and creates/updates two files in the central repo:

    - ``entries/<project>/<filename>.md`` — privacy-filtered full entry
    - ``patterns/<project>.jsonl`` — one-liner pattern (upserted)

    Args:
        solution_path: Absolute or repo-relative path to the solution
            markdown file.
        config: Pre-loaded ``TeamBrainLocalConfig``. If None, loaded from
            ``compound-gpid.local.md`` via ``load_team_brain_local_config()``.
        token: GitHub personal access token. If None, resolved via
            ``get_token()``.
        dry_run: If True, skip all GitHub API calls and return a
            ``dry-run`` result showing what *would* be pushed.
        local_config_path: Override path to ``compound-gpid.local.md``
            (used in tests to avoid searching the filesystem).

    Returns:
        :class:`PushResult` describing the action taken.

    Raises:
        ValueError: If config is present but invalid, or no token is
            available in live mode.
        RuntimeError: If GitHub API calls fail.

    Example::

        result = push_entry(
            Path(".cg-docs/solutions/bugs/2026-05-20-my-fix.md"),
            dry_run=True,
        )
        print(result.summary)
    """
    # Resolve config
    if config is None:
        config = load_team_brain_local_config(local_config_path)

    if config is None:
        return PushResult(
            action="skipped",
            entry_path="",
            jsonl_path="",
            summary="Team brain push skipped: not configured (no team-brain: section in compound-gpid.local.md).",
        )

    if not config.enabled:
        return PushResult(
            action="skipped",
            entry_path="",
            jsonl_path="",
            summary="Team brain push skipped: disabled in compound-gpid.local.md.",
        )

    # Resolve token early (before reading files) to fail fast in live mode
    resolved_token = get_token(token)
    if not resolved_token and not dry_run:
        raise ValueError(
            "No GitHub token found. Set the GITHUB_TOKEN environment variable "
            "or ensure the git credential manager has a GitHub token stored."
        )

    # Read solution
    solution_path = Path(solution_path)
    content = solution_path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(content)

    if not frontmatter:
        raise ValueError(
            f"Solution file has no YAML frontmatter block: {solution_path}\n"
            "Add a --- block with at least 'title' and 'date' fields."
        )

    # Run privacy filter (regex + frontmatter layers; no LLM layer)
    filter_result = run_privacy_filter(
        content=content,
        frontmatter=frontmatter,
        config=None,      # No central TeamBrainConfig available here
        llm_findings=None,  # LLM layer skipped unless caller pre-computes it
    )

    if filter_result.blocked:
        return PushResult(
            action="blocked",
            entry_path="",
            jsonl_path="",
            summary=f"Team brain push blocked by privacy filter: {filter_result.block_reason}",
        )

    # Guard: abort if the filtered body is effectively empty (DQ-P1.3).
    # This happens when all sections are marked private — pushing only frontmatter
    # would produce a noise entry with no reusable content.
    _, filtered_body_only = _parse_frontmatter(filter_result.clean_content)
    if len(filtered_body_only.strip()) < 50:
        return PushResult(
            action="blocked",
            entry_path="",
            jsonl_path="",
            summary=(
                "Team brain push blocked: body is empty or too short after privacy filtering "
                "(< 50 characters). Check 'private-sections:' in the frontmatter."
            ),
        )

    # Inject source-project and pushed-date into the clean content
    pushed_date = _date.today().isoformat()
    extra_fields = (
        f'source-project: "{config.project_name}"\n'
        f'pushed-date: "{pushed_date}"\n'
    )
    clean_content = re.sub(
        r"(^---\s*\n.*?)(^---\s*\n)",
        lambda m: m.group(1) + extra_fields + m.group(2),
        filter_result.clean_content,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )

    # Determine target paths in the central repo
    filename = solution_path.name
    entry_path = f"entries/{config.project_name}/{filename}"
    jsonl_path = f"patterns/{config.project_name}.jsonl"

    # Build pattern entry — distill from *filtered* content to avoid leaking private data
    clean_fm, clean_body = _parse_frontmatter(filter_result.clean_content)
    pattern_text = distill_pattern(clean_fm, clean_body).pattern_text
    if pattern_text == "(no pattern)":
        return PushResult(
            action="skipped",
            entry_path="",
            jsonl_path="",
            summary=(
                "Team brain push skipped: could not distill a meaningful pattern. "
                "Add a 'root-cause:' frontmatter field or a '## Solution' section."
            ),
        )
    tags: list[str] = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]

    pattern_entry = PatternEntry(
        id=solution_path.stem,
        date=str(frontmatter.get("date", pushed_date)),
        source_project=config.project_name,
        topic=str(frontmatter.get("category", "uncategorized")),
        tags=tags,
        pattern=pattern_text,
        entry_path=entry_path,
        confidence=1.0,
        superseded_by=None,
    )
    new_line = pattern_entry.to_jsonl_line()

    if dry_run:
        return PushResult(
            action="dry-run",
            entry_path=entry_path,
            jsonl_path=jsonl_path,
            summary=(
                f"[dry-run] Would push entry to {entry_path} and "
                f"append pattern to {jsonl_path}. "
                f"{filter_result.summary()}."
            ),
        )

    # Push JSONL patterns file FIRST (ADV-P1.3: JSONL-first ordering).
    # If the entry PUT fails afterwards, the JSONL is still indexable and
    # re-running will overwrite the entry with a consistent state.
    jsonl_base_msg = f"knowledge({config.project_name}): {solution_path.stem}"
    _put_jsonl_with_retry(
        config.repo, jsonl_path, resolved_token,
        new_line, pattern_entry.id, jsonl_base_msg,
    )

    # Push the markdown entry (create or update)
    existing_entry = _get_remote_file(config.repo, entry_path, resolved_token)
    entry_sha = existing_entry[0] if existing_entry else None
    action = "updated" if entry_sha else "created"
    commit_msg = (
        f"knowledge({config.project_name}): update {solution_path.stem}"
        if entry_sha
        else f"knowledge({config.project_name}): add {solution_path.stem}"
    )
    _put_remote_file(
        config.repo, entry_path, resolved_token, clean_content, commit_msg, entry_sha
    )

    return PushResult(
        action=action,
        entry_path=entry_path,
        jsonl_path=jsonl_path,
        summary=(
            f"Entry {action} at {entry_path}. "
            f"Pattern pushed to {jsonl_path}. "
            f"{filter_result.summary()}."
        ),
    )
