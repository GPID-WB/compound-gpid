"""Deterministic readiness validator for Copilot implementation issues.

Stage 2 of the controlled Copilot issue-implementation pipeline.

The validator treats every GitHub issue body as **untrusted data** and checks
that the issue carries a complete, machine-parseable readiness contract plus the
required live GitHub state before it could be dispatched to the Copilot coding
agent. It is **read-only by construction**: it never creates, edits, closes,
assigns, labels, comments, or mutates any issue, Project item, pull request, or
repository setting. ``--dry-run`` is the canonical and only mode.

The contract format is derived from the structured Markdown issue proven by the
Stage 1 pilot (issue #127). Section heading text is matched exactly; validation
is deterministic and does not depend on AI judgment.

GitHub access uses the ``gh`` CLI with argv-safe invocation (``subprocess.run``
with a list, never ``shell=True``, and never interpolating the untrusted body
into a shell string), consistent with the documented
``.cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md``
lesson.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable, Optional, Sequence


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------

EXIT_READY = 0
EXIT_NOT_READY = 2
EXIT_CONFIG = 3
EXIT_API = 4

EXIT_REASONS = {
    EXIT_READY: "ready",
    EXIT_NOT_READY: "validation_failure",
    EXIT_CONFIG: "config_error",
    EXIT_API: "api_error",
}


# ---------------------------------------------------------------------------
# Canonical contract: marker, feature id, sections, risk classes
# ---------------------------------------------------------------------------

MARKER_RE = re.compile(
    r"<!--\s*compound-gpid-tracked:\s*([A-Za-z0-9][A-Za-z0-9-]*)\s*-->"
)

FEATURE_ID_LINE_RE = re.compile(
    r"\*\*\s*Feature\s+ID\s*:\s*\*\*\s*`([^`]+)`", re.IGNORECASE
)

FEATURE_ID_FORMAT_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

RISK_CLASSES = ("low", "medium", "high")

READY_STATUS = "Ready"
PROJECT_TITLE = "CompoundGPID-progress"
GH_TIMEOUT_SECONDS = 60

# Required `## ` sections, exact heading text, in the recommended order.
# Derived from the Stage 1 pilot issue (#127) proven structure.
REQUIRED_SECTIONS: tuple[str, ...] = (
    "Roadmap linkage",
    "Ready for Copilot",
    "Outcome",
    "Acceptance criteria",
    "Scope",
    "Non-goals",
    "Expected allowed paths",
    "Prohibited paths",
    "Verification commands",
    "Dependencies / blockers",
    "Risk class",
    "Human review instructions",
    "Blocked-stop conditions",
)

SECTION_HEADER_RE = re.compile(r"^##\s+(.+?)\s*#*\s*$")

CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[([ xX])\](?:\s+|$)")
UNCHECKED_BOX_RE = re.compile(r"^\s*[-*]\s*\[\s\](?:\s+|$)")
LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(.*)$")
CODE_SPAN_RE = re.compile(r"`([^`]+)`")

CLOSE_KEYWORDS = r"(?:closes?|closed|fixes?|fixed|resolves?|resolved)"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ReadinessError(Exception):
    """Base class for readiness validator failures."""


class ConfigError(ReadinessError):
    """Local configuration failure (gh missing, bad args, missing scope, 404)."""


class ApiError(ReadinessError):
    """GitHub API/network failure (5xx, timeout, rate limit, malformed response)."""


# ---------------------------------------------------------------------------
# Data records
# ---------------------------------------------------------------------------


@dataclass
class IssueRecord:
    number: int
    title: str
    body: str
    state: str
    assignees: list[str]
    labels: list[str]


@dataclass
class PRRecord:
    number: int
    title: str
    body: str
    url: str
    head_ref: str
    author: str


@dataclass
class RuleResult:
    id: str
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ReadinessResult:
    issue: Optional[int]
    ready: bool
    exit_code: int
    exit_reason: str
    rules: list[RuleResult] = field(default_factory=list)
    state: dict = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)
    dry_run: bool = True


# ---------------------------------------------------------------------------
# Pure parsing helpers (no I/O, fully deterministic)
# ---------------------------------------------------------------------------


def strip_bom(text: str) -> str:
    if text and text[0] == "\ufeff":
        return text[1:]
    return text


def _iter_fence_state(lines: Sequence[str]):
    """Yield ``(line, in_fence, opens, closes)`` per Markdown line.

    ``in_fence`` is True when the line begins inside an open fenced code block
    (````` ``` ```` or ``~~~``). ``opens`` and ``closes`` mark delimiter lines
    that start or end a fence. Consumers use these flags to locate section
    headers, markers, checkboxes, and command blocks while ignoring fenced
    content; the flags avoid three divergent hand-rolled fence trackers.
    """
    in_fence = False
    fence: Optional[str] = None
    for line in lines:
        stripped = line.lstrip()
        opens = False
        closes = False
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = "```" if stripped.startswith("```") else "~~~"
                opens = True
        elif fence is not None and stripped.startswith(fence):
            closes = True
        yield line, in_fence, opens, closes
        if opens:
            in_fence = True
        elif closes:
            in_fence = False
            fence = None


def _non_fence_lines(lines: Sequence[str]):
    """Yield lines that are outside fenced code blocks (``` or ~~~).

    Fence delimiters and fenced content are skipped, so markers, feature-id
    declarations, section headers, path entries, and checkboxes are never read
    from inside a code block.
    """
    for line, in_fence, opens, closes in _iter_fence_state(lines):
        if not in_fence and not opens and not closes:
            yield line


def parse_sections(body: str) -> list[tuple[str, list[str]]]:
    """Split the body into ordered ``## `` sections, ignoring fenced code blocks.

    Returns ``(name, content_lines)`` pairs. Content lines include any fences
    inside the section so downstream helpers can re-track fence state. Lines
    before the first section (the preamble, including the tracked marker) are
    not returned as a section.
    """
    sections: list[tuple[str, list[str]]] = []
    cur_name: Optional[str] = None
    cur: list[str] = []
    for line, in_fence, opens, closes in _iter_fence_state(body.splitlines()):
        if in_fence or opens or closes:
            if cur_name is not None:
                cur.append(line)
            continue
        header = SECTION_HEADER_RE.match(line)
        if header:
            if cur_name is not None:
                sections.append((cur_name, cur))
            cur_name = header.group(1).strip()
            cur = []
        elif cur_name is not None:
            cur.append(line)
    if cur_name is not None:
        sections.append((cur_name, cur))
    return sections


def find_marker(body: str) -> Optional[str]:
    """Return the feature id in the first tracked marker outside fences."""
    for line in _non_fence_lines(body.splitlines()):
        match = MARKER_RE.search(line)
        if match:
            return match.group(1)
    return None


def find_feature_id(body: str) -> tuple[Optional[str], int]:
    """Return ``(feature_id, count)`` from ``**Feature ID:** `id``` lines.

    Only non-fence lines are scanned. ``count`` is the number of matching
    lines; the canonical contract requires exactly one.
    """
    found: Optional[str] = None
    count = 0
    for line in _non_fence_lines(body.splitlines()):
        match = FEATURE_ID_LINE_RE.search(line)
        if match:
            count += 1
            if found is None:
                found = match.group(1).strip()
    return found, count


def _section_nonempty(content_lines: Sequence[str]) -> bool:
    return any(line.strip() for line in _non_fence_lines(content_lines))


def _section_detail(content_lines: Sequence[str] | None) -> str:
    """Describe a section's presence: ``section absent``, ``empty``, or ``non-empty``."""
    if content_lines is None:
        return "section absent"
    return "empty" if not _section_nonempty(content_lines) else "non-empty"


def _extract_checkboxes(content_lines: Sequence[str]) -> list[bool]:
    boxes: list[bool] = []
    for line in _non_fence_lines(content_lines):
        match = CHECKBOX_RE.match(line)
        if match:
            boxes.append(match.group(1).lower() == "x")
    return boxes


def _extract_path_entries(content_lines: Sequence[str]) -> list[str]:
    """Extract backtick code spans from list-item lines outside fences.

    List items without a code span are treated as prose and ignored, matching
    the proven issue structure where prose bullets describe scope in words.
    """
    entries: list[str] = []
    for line in _non_fence_lines(content_lines):
        match = LIST_ITEM_RE.match(line)
        if not match:
            continue
        for span in CODE_SPAN_RE.findall(match.group(1)):
            entries.append(span)
    return entries


def _extract_risk_class(content_lines: Sequence[str]) -> Optional[str]:
    """Return the risk class from a non-fence line that is exactly a class.

    The canonical form is a line whose content is ``low``, ``medium``, or
    ``high`` (optionally wrapped in backticks). A bare word embedded in prose
    such as "low confidence" is intentionally not accepted, to avoid a false
    ready verdict.
    """
    for line in _non_fence_lines(content_lines):
        token = line.strip().strip("`").strip().lower()
        if token in RISK_CLASSES:
            return token
    return None


def _has_blocking_dependency(content_lines: Sequence[str]) -> tuple[bool, str]:
    """Return ``(blocking, detail)``.

    A dependency is blocking when the section contains an unchecked checklist
    item (``- [ ]``) or a ``blocked by`` phrase (unless the individual
    occurrence is explicitly negated as "not blocked by"). A section that says
    ``None``, lists only resolved (``- [x]``) items, or contains only
    informational prose is not blocking.
    """
    for line in _non_fence_lines(content_lines):
        if UNCHECKED_BOX_RE.match(line):
            return True, f"unchecked dependency item: {line.strip()}"
        for match in re.finditer(r"\bblocked\s+by\b", line, re.IGNORECASE):
            before = line[: match.start()]
            if re.search(r"\b(?:not|cannot|can't|won't|isn't|aren't|wasn't|weren't|doesn't|don't|didn't)\s+(?:be\s+)?$", before, re.IGNORECASE):
                continue
            return True, f"blocking dependency: {line.strip()}"
    return False, ""


def _verification_commands_nonempty(content_lines: Sequence[str]) -> bool:
    """True when the section contains at least one fenced block with content."""
    in_fence = False
    buf: list[str] = []
    for line, _, opens, closes in _iter_fence_state(content_lines):
        if opens:
            in_fence = True
            buf = []
            continue
        if in_fence:
            if closes:
                if any(part.strip() for part in buf):
                    return True
                in_fence = False
                buf = []
                continue
            buf.append(line)
    return False


def validate_path_entry(entry: str) -> Optional[str]:
    """Return an error message for an unsafe/malformed path or glob, else None.

    Rejects surrounding whitespace and control characters, absolute paths,
    Windows drive/UNC paths, backslashes, ``..`` traversal segments, empty
    segments, and unbalanced glob brackets. Git pathspecs use forward slashes
    only; leading/trailing whitespace is rejected outright so a downstream
    ``.strip()`` cannot turn a padded unsafe entry into a real path.
    """
    if not entry:
        return "empty path entry"
    if entry != entry.strip():
        return "path entry has surrounding whitespace"
    if re.search(r"[\x00-\x1f\x7f]", entry):
        return "control character in path entry"
    if entry.startswith("//") or entry.startswith("\\\\"):
        return "UNC path"
    if entry.startswith("/"):
        return "absolute path"
    if re.match(r"^[A-Za-z]:", entry):
        return "Windows drive path"
    if "\\" in entry:
        return "backslash not allowed in git pathspec"
    parts = entry.split("/")
    for part in parts:
        if part == "":
            return "empty path segment (consecutive or trailing slash)"
        if part == "..":
            return "traversal segment '..'"
        if _brackets_unbalanced(part):
            return f"malformed glob (unbalanced brackets) in {part!r}"
    return None


def _is_overbroad_allowed_path(entry: str) -> bool:
    """True when an allowed-path entry is too broad to bound Copilot's scope.

    Rejects bare ``*``, ``**``, ``.``, and any entry whose every segment is
    empty after removing glob metacharacters (no literal path component). Such
    entries make the "exact allowed-path closure" meaningless. Prohibited paths
    are not subject to this check (``.github/workflows/**`` is a valid
    prohibition).
    """
    if entry in ("", ".", ".."):
        return True
    for part in entry.split("/"):
        literal = re.sub(r"[*?\[\]]", "", part)
        if literal and literal not in (".", ".."):
            return False
    return True


def _brackets_unbalanced(segment: str) -> bool:
    depth = 0
    for ch in segment:
        if ch == "[":
            depth += 1
        elif ch == "]":
            if depth == 0:
                return True
            depth -= 1
    return depth != 0


def pr_closes_issue(pr_body: str, issue_number: int) -> bool:
    """True when the PR body references the issue with a closing keyword."""
    n = str(issue_number)
    patterns = (
        rf"\b{CLOSE_KEYWORDS}\s+#{n}\b",
        rf"\b{CLOSE_KEYWORDS}\s+https?://\S+/issues/{n}\b",
    )
    for pattern in patterns:
        if re.search(pattern, pr_body, re.IGNORECASE):
            return True
    return False


def is_copilot_assignee(login: str) -> bool:
    """True when the login is (or looks like) the Copilot coding agent.

    Matches ``Copilot``, ``copilot``, and bot logins that start with ``copilot``
    (e.g. ``copilot-swe-agent``). A login that merely contains the substring
    (e.g. ``NotCopilot``) is not treated as Copilot.
    """
    if not login:
        return False
    low = login.lower()
    return low == "copilot" or low.startswith("copilot")


def copilot_assignees(assignees: Sequence[str]) -> list[str]:
    return [login for login in assignees if is_copilot_assignee(login)]


# ---------------------------------------------------------------------------
# Contract validation (pure, no network)
# ---------------------------------------------------------------------------


def validate_contract(body: str) -> list[RuleResult]:
    body = strip_bom(body)
    sections = parse_sections(body)
    section_map: dict[str, list[str]] = {}
    name_counts: dict[str, int] = {}
    for name, lines in sections:
        name_counts[name] = name_counts.get(name, 0) + 1
        if name not in section_map:
            section_map[name] = lines

    marker_id = find_marker(body)
    feature_id, feature_count = find_feature_id(body)

    rules: list[RuleResult] = []

    rules.append(
        RuleResult(
            "R001", "marker-present", marker_id is not None,
            "tracked marker found" if marker_id else "no <!-- compound-gpid-tracked: <id> --> marker",
        )
    )

    feature_format_ok = (
        feature_id is not None and FEATURE_ID_FORMAT_RE.match(feature_id) is not None
    )
    rules.append(
        RuleResult(
            "R002", "feature-id-declared", feature_count == 1 and feature_format_ok,
            f"feature_id={feature_id!r} count={feature_count} format_ok={feature_format_ok}",
        )
    )

    r003 = marker_id is not None and feature_id is not None and marker_id == feature_id
    rules.append(
        RuleResult(
            "R003", "feature-id-marker-match", r003,
            f"marker={marker_id!r} feature_id={feature_id!r}",
        )
    )

    missing = [name for name in REQUIRED_SECTIONS if name not in section_map]
    rules.append(
        RuleResult(
            "R004", "required-sections-present", not missing,
            f"missing: {missing}" if missing else "all required sections present",
        )
    )

    duplicates = [name for name in REQUIRED_SECTIONS if name_counts.get(name, 0) > 1]
    rules.append(
        RuleResult(
            "R005", "no-duplicate-sections", not duplicates,
            f"duplicates: {duplicates}" if duplicates else "no duplicate required sections",
        )
    )

    rfc = section_map.get("Ready for Copilot")
    if rfc is not None:
        boxes = _extract_checkboxes(rfc)
        unchecked = sum(1 for checked in boxes if not checked)
        r006 = len(boxes) > 0 and unchecked == 0
        detail = f"{unchecked} unchecked of {len(boxes)} boxes"
    else:
        r006 = False
        detail = "section absent"
    rules.append(RuleResult("R006", "readiness-confirmation-checked", r006, detail))

    ac = section_map.get("Acceptance criteria")
    rules.append(
        RuleResult(
            "R007", "acceptance-criteria-nonempty",
            ac is not None and _section_nonempty(ac),
            _section_detail(ac),
        )
    )

    vc = section_map.get("Verification commands")
    vc_ok = vc is not None and _verification_commands_nonempty(vc)
    rules.append(
        RuleResult(
            "R008", "verification-commands-nonempty", vc_ok,
            "section absent" if vc is None else ("no fenced command block" if not vc_ok else "non-empty"),
        )
    )

    rc = section_map.get("Risk class")
    risk = _extract_risk_class(rc) if rc is not None else None
    rules.append(
        RuleResult(
            "R009", "risk-class-valid", risk in RISK_CLASSES,
            f"risk={risk!r}",
        )
    )

    ap = section_map.get("Expected allowed paths")
    allowed = _extract_path_entries(ap) if ap is not None else []
    rules.append(
        RuleResult(
            "R010", "allowed-paths-present", len(allowed) > 0,
            f"{len(allowed)} path entries",
        )
    )

    pp = section_map.get("Prohibited paths")
    prohibited = _extract_path_entries(pp) if pp is not None else []
    rules.append(
        RuleResult(
            "R011", "prohibited-paths-present", len(prohibited) > 0,
            f"{len(prohibited)} path entries",
        )
    )

    all_paths = [(entry, "allowed") for entry in allowed] + [
        (entry, "prohibited") for entry in prohibited
    ]
    unsafe = [
        {"entry": entry, "location": location, "error": err}
        for entry, location in all_paths
        if (err := validate_path_entry(entry)) is not None
    ]
    overbroad = [entry for entry in allowed if _is_overbroad_allowed_path(entry)]
    r012_ok = not unsafe and not overbroad
    detail = (
        f"{len(unsafe)} unsafe, {len(overbroad)} overbroad allowed"
        if unsafe or overbroad
        else "all path entries safe"
    )
    rules.append(RuleResult("R012", "path-entries-safe", r012_ok, detail))

    bs = section_map.get("Blocked-stop conditions")
    rules.append(
        RuleResult(
            "R013", "blocked-stop-conditions-nonempty",
            bs is not None and _section_nonempty(bs),
            _section_detail(bs),
        )
    )

    db = section_map.get("Dependencies / blockers")
    if db is not None:
        blocking, detail = _has_blocking_dependency(db)
    else:
        blocking, detail = False, "section absent (see R004)"
    rules.append(
        RuleResult(
            "R014", "dependencies-not-blocking", not blocking, detail or "no blockers",
        )
    )

    for rule_id, name, section_name in (
        ("R015", "outcome-nonempty", "Outcome"),
        ("R016", "scope-nonempty", "Scope"),
        ("R017", "non-goals-nonempty", "Non-goals"),
        ("R018", "human-review-instructions-nonempty", "Human review instructions"),
    ):
        sec = section_map.get(section_name)
        ok = sec is not None and _section_nonempty(sec)
        rules.append(
            RuleResult(
                rule_id, name, ok,
                _section_detail(sec),
            )
        )

    return rules


# ---------------------------------------------------------------------------
# GitHub client
# ---------------------------------------------------------------------------


class GhCliClient:
    """Read-only GitHub access via the ``gh`` CLI (argv-safe)."""

    def __init__(self, runner: Optional[Callable[[list[str]], subprocess.CompletedProcess]] = None) -> None:
        self._runner = runner or _default_run_gh
        self._repo: Optional[tuple[str, str]] = None

    def _gh(self, args: list[str]) -> str:
        completed = self._runner(args)
        if completed.returncode != 0:
            _classify_gh_error(completed, args)
        return completed.stdout

    @staticmethod
    def _parse_json(out: str, label: str):
        try:
            return json.loads(out)
        except json.JSONDecodeError as error:
            raise ApiError(f"malformed {label} response from gh: {error}") from error

    def get_issue(self, issue_number: int) -> IssueRecord:
        out = self._gh([
            "issue", "view", str(issue_number), "--json",
            "number,title,body,state,assignees,labels",
        ])
        data = self._parse_json(out, "issue")
        try:
            assignees = [a.get("login") for a in data.get("assignees", []) if a.get("login")]
            labels = [label.get("name") for label in data.get("labels", []) if label.get("name")]
            return IssueRecord(
                number=int(data.get("number", issue_number)),
                title=data.get("title", "") or "",
                body=data.get("body", "") or "",
                state=str(data.get("state", "")).upper(),
                assignees=assignees,
                labels=labels,
            )
        except (ValueError, TypeError, AttributeError) as error:
            raise ApiError(f"malformed issue response from gh: {error}") from error

    def get_open_closing_prs(self, issue_number: int) -> list[PRRecord]:
        records: list[PRRecord] = []
        page = 1
        while True:
            out = self._gh([
                "pr", "list", "--state", "open", "--json",
                "number,title,body,url,headRefName,author",
                "--limit", "100", "--page", str(page),
            ])
            items = self._parse_json(out, "pr")
            if not items:
                break
            try:
                for item in items:
                    body = item.get("body") or ""
                    if not pr_closes_issue(body, issue_number):
                        continue
                    author = item.get("author")
                    if isinstance(author, dict):
                        author_login = author.get("login") or ""
                    elif isinstance(author, str):
                        author_login = author
                    else:
                        author_login = ""
                    records.append(PRRecord(
                        number=int(item.get("number", 0)),
                        title=item.get("title", "") or "",
                        body=body,
                        url=item.get("url", "") or "",
                        head_ref=item.get("headRefName", "") or "",
                        author=author_login,
                    ))
            except (ValueError, TypeError, AttributeError) as error:
                raise ApiError(f"malformed pr response from gh: {error}") from error
            if len(items) < 100:
                break
            page += 1
        return records

    def get_project_status(self, issue_number: int) -> Optional[str]:
        owner, name = self._repo_owner_name()
        query = _PROJECT_STATUS_QUERY.format(number=issue_number)
        out = self._gh([
            "api", "graphql", "-f", f"query={query}",
            "-F", f"owner={owner}", "-F", f"name={name}",
        ])
        data = self._parse_json(out, "graphql")
        if data.get("errors"):
            raise ConfigError(f"GitHub GraphQL error: {data['errors']}")
        try:
            nodes = data["data"]["repository"]["issue"]["projectItems"]["nodes"]
        except (KeyError, TypeError):
            return None
        try:
            for node in nodes:
                project = node.get("project") or {}
                if project.get("title") != PROJECT_TITLE:
                    continue
                field_value = node.get("fieldValueByName")
                return field_value.get("name") if isinstance(field_value, dict) else None
        except (TypeError, AttributeError) as error:
            raise ApiError(f"malformed graphql response from gh: {error}") from error
        return None

    def _repo_owner_name(self) -> tuple[str, str]:
        if self._repo is not None:
            return self._repo
        out = self._gh(["repo", "view", "--json", "nameWithOwner"])
        data = self._parse_json(out, "repo")
        try:
            name_with_owner = data.get("nameWithOwner", "")
        except AttributeError as error:
            raise ApiError(f"malformed repo response from gh: {error}") from error
        if "/" not in name_with_owner:
            raise ConfigError(f"could not determine repository from gh: {name_with_owner!r}")
        owner, name = name_with_owner.split("/", 1)
        self._repo = (owner, name)
        return self._repo


_PROJECT_STATUS_QUERY = """query ReadinessStatus($owner: String!, $name: String!) {{
  repository(owner: $owner, name: $name) {{
    issue(number: {number}) {{
      projectItems(first: 20) {{
        nodes {{
          project {{ title }}
          fieldValueByName(name: "Status") {{
            ... on ProjectV2ItemFieldSingleSelectValue {{ name }}
          }}
        }}
      }}
    }}
  }}
}}"""


def _default_run_gh(args: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["gh", *args], capture_output=True, text=True,
            encoding="utf-8", timeout=GH_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise ConfigError(
            "gh CLI not found; install GitHub CLI (https://cli.github.com) and run "
            "`gh auth login` before using --issue"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise ApiError(f"gh command timed out after {GH_TIMEOUT_SECONDS}s") from error


def _classify_gh_error(completed: subprocess.CompletedProcess, args: list[str]) -> None:
    stderr = (completed.stderr or "").strip()
    rc = completed.returncode
    lower = stderr.lower()
    status_match = re.search(r"HTTP (\d{3})", stderr)
    status = status_match.group(1) if status_match else None
    if status and 500 <= int(status) < 600:
        raise ApiError(f"gh command failed (HTTP {status}): {stderr}")
    if "rate limit" in lower:
        raise ApiError(f"GitHub rate limited: {stderr}")
    if "timeout" in lower or "timed out" in lower:
        raise ApiError(f"gh command timed out: {stderr}")
    if status == "404" or "not found" in lower or "could not find" in lower or "does not exist" in lower:
        raise ConfigError(f"GitHub resource not found: {stderr}")
    if status in ("401", "403") or "auth" in lower or "scope" in lower or "permission" in lower:
        raise ConfigError(f"GitHub authorization/scope error: {stderr}")
    # A failing GraphQL call that is not a 5xx/rate-limit/timeout is a
    # client-side query/scope/schema problem, not a GitHub server failure.
    if "graphql" in args:
        raise ConfigError(f"GitHub GraphQL query/schema error: {stderr}")
    if rc == 1 and not stderr:
        raise ConfigError("gh command failed with no message (not authenticated?)")
    raise ApiError(f"gh command failed (rc={rc}): {stderr}")


class FixtureClient:
    """Offline client backed by a JSON fixture file (no network)."""

    def __init__(self, fixture_path: str) -> None:
        path = Path(fixture_path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            issue = data.get("issue", {})
            body = issue.get("body", "")
            body_file = data.get("bodyFile")
            if body_file:
                body = (path.parent / body_file).read_text(encoding="utf-8")
        except (OSError, json.JSONDecodeError) as error:
            raise ConfigError(f"cannot load fixture {fixture_path}: {error}") from error
        self.issue_number = int(issue.get("number", 0))
        self._issue = IssueRecord(
            number=self.issue_number,
            title=issue.get("title", "") or "",
            body=body,
            state=str(issue.get("state", "OPEN")).upper(),
            assignees=list(issue.get("assignees", [])),
            labels=list(issue.get("labels", [])),
        )
        self._prs = []
        for pr in data.get("openClosingPRs", []):
            author = pr.get("author")
            if isinstance(author, dict):
                author_login = author.get("login") or ""
            elif isinstance(author, str):
                author_login = author
            else:
                author_login = ""
            self._prs.append(PRRecord(
                number=int(pr.get("number", 0)),
                title=pr.get("title", "") or "",
                body=pr.get("body", "") or "",
                url=pr.get("url", "") or "",
                head_ref=pr.get("headRefName", "") or "",
                author=author_login,
            ))
        self._status = data.get("projectStatus")

    def get_issue(self, issue_number: int) -> IssueRecord:
        return self._issue

    def get_open_closing_prs(self, issue_number: int) -> list[PRRecord]:
        return self._prs

    def get_project_status(self, issue_number: int) -> Optional[str]:
        return self._status


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def validate_readiness(
    issue_number: int, client, *, dry_run: bool = True
) -> ReadinessResult:
    try:
        issue = client.get_issue(issue_number)
        prs = client.get_open_closing_prs(issue_number)
        status = client.get_project_status(issue_number)
    except ConfigError as error:
        return _error_result(issue_number, EXIT_CONFIG, str(error), dry_run)
    except ApiError as error:
        return _error_result(issue_number, EXIT_API, str(error), dry_run)

    contract_rules = validate_contract(issue.body)
    assigned_copilot = copilot_assignees(issue.assignees)
    state_rules = [
        RuleResult(
            "R019", "project-status-ready", status == READY_STATUS,
            f"Project Status is {status!r}, expected {READY_STATUS!r}",
        ),
        RuleResult(
            "R020", "no-open-closing-pr", len(prs) == 0,
            f"{len(prs)} open PR(s) close this issue"
            + (f" (#{prs[0].number})" if prs else ""),
        ),
        RuleResult(
            "R021", "copilot-not-assigned", len(assigned_copilot) == 0,
            f"Copilot assignee(s): {assigned_copilot}" if assigned_copilot else "no Copilot assignee",
        ),
    ]
    rules = contract_rules + state_rules
    ready = all(rule.passed for rule in rules)
    exit_code = EXIT_READY if ready else EXIT_NOT_READY
    state = {
        "issueState": issue.state,
        "projectStatus": status,
        "openClosingPRs": [{"number": pr.number, "url": pr.url} for pr in prs],
        "copilotAssigned": len(assigned_copilot) > 0,
        "assignees": list(issue.assignees),
    }
    return ReadinessResult(
        issue=issue_number,
        ready=ready,
        exit_code=exit_code,
        exit_reason=EXIT_REASONS[exit_code],
        rules=rules,
        state=state,
        errors=[],
        dry_run=dry_run,
    )


def _error_result(issue_number: int, exit_code: int, message: str, dry_run: bool) -> ReadinessResult:
    return ReadinessResult(
        issue=issue_number,
        ready=False,
        exit_code=exit_code,
        exit_reason=EXIT_REASONS[exit_code],
        rules=[],
        state={},
        errors=[{"type": EXIT_REASONS[exit_code], "message": message}],
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def result_to_dict(result: ReadinessResult) -> dict:
    failed = [
        {"id": rule.id, "name": rule.name, "detail": rule.detail}
        for rule in result.rules
        if not rule.passed
    ]
    failed_count = len(failed)
    if result.exit_code == EXIT_READY:
        summary = "READY"
    elif result.exit_code == EXIT_NOT_READY:
        summary = f"NOT READY — {failed_count} rule(s) failed"
    else:
        summary = f"CANNOT COMPLETE — {result.exit_reason}"
    return {
        "issue": result.issue,
        "ready": result.ready,
        "dryRun": result.dry_run,
        "exitCode": result.exit_code,
        "exitReason": result.exit_reason,
        "summary": summary,
        "rules": [
            {"id": rule.id, "name": rule.name, "passed": rule.passed, "detail": rule.detail}
            for rule in result.rules
        ],
        "failedRules": failed,
        "state": result.state,
        "errors": result.errors,
    }


def render_json(result: ReadinessResult) -> str:
    return json.dumps(result_to_dict(result), indent=2, sort_keys=False)


def render_human(result: ReadinessResult) -> str:
    lines: list[str] = []
    label = "READY" if result.ready else {
        EXIT_NOT_READY: "NOT READY",
        EXIT_CONFIG: "CANNOT COMPLETE (config)",
        EXIT_API: "CANNOT COMPLETE (api/network)",
    }.get(result.exit_code, "NOT READY")
    if result.issue is None:
        lines.append(label)
    else:
        lines.append(f"Issue #{result.issue}: {label}")
    lines.append(f"Exit code: {result.exit_code} ({result.exit_reason})")
    lines.append(f"Dry-run: {result.dry_run} (validator is read-only)")
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  [{error['type']}] {error['message']}")
    failed = [rule for rule in result.rules if not rule.passed]
    if failed:
        lines.append("")
        lines.append("Failed rules:")
        for rule in failed:
            lines.append(f"  {rule.id}  {rule.name}  - {rule.detail}")
    if result.state:
        lines.append("")
        lines.append("State:")
        lines.append(f"  issue state: {result.state.get('issueState')}")
        lines.append(f"  project status: {result.state.get('projectStatus')}")
        lines.append(f"  open closing PRs: {len(result.state.get('openClosingPRs', []))}")
        lines.append(f"  copilot assigned: {result.state.get('copilotAssigned')}")
        lines.append(f"  assignees: {result.state.get('assignees')}")
    lines.append("")
    lines.append(
        "Passing validation does NOT assign Copilot or change Project status."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class _ReadinessArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that exits with ``EXIT_CONFIG`` on usage errors.

    argparse's default error exit code is 2, which collides with
    ``EXIT_NOT_READY``. A CLI misconfiguration must be distinguishable from a
    validation failure (per the documented exit-code contract). Custom error
    output is routed to ``stderr`` (defaulting to ``sys.stderr``) so callers
    and tests can capture it.
    """

    def __init__(self, *args, stderr=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._err_stream = stderr if stderr is not None else sys.stderr

    def error(self, message: str) -> None:  # type: ignore[override]
        self.print_usage(self._err_stream)
        self._err_stream.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(EXIT_CONFIG)


def build_parser(*, stderr=None) -> argparse.ArgumentParser:
    parser = _ReadinessArgumentParser(
        prog="cg-issue-ready",
        stderr=stderr,
        description=(
            "Deterministic, read-only readiness validator for Copilot "
            "implementation issues. Never mutates GitHub state."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--issue", type=int, metavar="N", help="issue number to validate (live, read-only)")
    source.add_argument("--fixture", metavar="PATH", help="offline JSON fixture file (no network)")
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="read-only validation (always on; the validator never mutates GitHub state)",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="machine-readable JSON output")
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    client=None,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    parser = build_parser(stderr=err)
    args = parser.parse_args(argv)

    if args.fixture:
        try:
            fixture_client = FixtureClient(args.fixture)
        except (ConfigError, ApiError) as error:
            result = _error_result(None, EXIT_CONFIG if isinstance(error, ConfigError) else EXIT_API, str(error), args.dry_run)
            _emit(result, args, out)
            return result.exit_code
        issue_number = fixture_client.issue_number
        active_client = client or fixture_client
    else:
        issue_number = args.issue
        active_client = client or GhCliClient()

    result = validate_readiness(issue_number, active_client, dry_run=args.dry_run)
    _emit(result, args, out)
    return result.exit_code


def _emit(result: ReadinessResult, args: argparse.Namespace, out) -> None:
    text = render_json(result) if args.as_json else render_human(result)
    out.write(text)
    if not text.endswith("\n"):
        out.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())