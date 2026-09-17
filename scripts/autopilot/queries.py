"""Structured Git/GitHub observation and publication reconciliation (Step 10).

The argv runner is injected by the caller (tests use fakes). Output and timeout
bounds are enforced here; ``gh`` wire payloads are validated against exact field
shapes and wrong types raise ``QueryError``. Publication requires a selected
base before any existing-PR base is consulted, retains the Git-based
source/consumer classification, and distinguishes dirty, clean-unpushed,
pushed-no-pr, existing-matching-PR and lost acknowledgement without ever
rebasing, force-pushing, merging or retargeting.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence, Tuple

from autopilot.contracts import (
    AutopilotError,
    PacketError,
    parse_closed_json,
    sha256_hex,
)

MAX_QUERY_BYTES = 8 * 1024 * 1024
MAX_STDOUT_BYTES = 8 * 1024 * 1024
MAX_STDERR_BYTES = 256 * 1024
REQUEST_TIMEOUT_SECONDS = 30

SOURCE_MARKER = ".compound-gpid-source.json"
CANONICAL_MAPPING = ".github/shared/target-mapping.json"
GENERATOR = "scripts/cg_generate_targets.py"

# gh pr view exits 1 both for "no pull requests exist here" and for transient
# or network failures. Only these exact stderr diagnostics may be read as
# "no PR": anything else is an error, so a duplicate PR can never be created
# after a failed read.
_GH_NO_PR_MARKERS = (
    "no pull requests",
    "no open pull requests",
    "no pull requests found",
    "no open pull requests found",
    "could not resolve to a pull request",
)

CHECK_RUN_STATUSES = ("COMPLETED", "IN_PROGRESS", "QUEUED", "EXPECTED")
CHECK_RUN_CONCLUSIONS = (
    "SUCCESS", "NEUTRAL", "SKIPPED", "CANCELLED",
    "ACTION_REQUIRED", "STALE", "FAILURE", "TIMED_OUT",
)
STATUS_CONTEXT_STATES = {
    "SUCCESS": ("COMPLETED", "SUCCESS"),
    "FAILURE": ("COMPLETED", "FAILURE"),
    "ERROR": ("COMPLETED", "FAILURE"),
    "PENDING": ("IN_PROGRESS", None),
    "EXPECTED": ("EXPECTED", None),
}


class QueryError(AutopilotError):
    error_code = "autopilot-query-error"


@dataclass(frozen=True)
class CommandOutcome:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str]], CommandOutcome]


@dataclass(frozen=True)
class GitIndexEntry:
    mode: str
    object_id: str
    stage: str
    path: str


@dataclass(frozen=True)
class Routing:
    kind: str
    evidence: Tuple[str, ...]


@dataclass(frozen=True)
class Pr:
    number: int
    url: str
    title: str
    state: str
    base_ref_name: str
    head_ref_name: str
    head_ref_oid: Optional[str]


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    conclusion: Optional[str]
    details_url: Optional[str]


@dataclass(frozen=True)
class PublicationState:
    state: str
    branch: str
    head: str
    remote_ref: Optional[str]
    remote_head: Optional[str]
    ahead: int
    behind: int
    pr: Optional[Pr]
    diagnostics: Tuple[str, ...]


@dataclass(frozen=True)
class PathIdentity:
    path: str
    status: str
    sha256: Optional[str]
    byte_count: Optional[int]


@dataclass(frozen=True)
class Coverage:
    paths: Tuple[PathIdentity, ...]
    digest: str


def _bound_text(text: object, limit: int) -> str:
    value = str(text or "")
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return value
    return encoded[:limit].decode("utf-8", errors="ignore") + "\n[output truncated]"


def _field(data: dict, key: str, path: str, types: tuple) -> Any:
    if key not in data:
        raise QueryError(f"{path}.{key} is missing from the wire payload.")
    value = data[key]
    if not isinstance(value, types):
        expected = " or ".join(t.__name__ for t in types)
        raise QueryError(f"{path}.{key} must have {expected} type.")
    return value


def run_query(runner: Runner, argv: Sequence[str], *, label: str,
              timeout: int = REQUEST_TIMEOUT_SECONDS) -> CommandOutcome:
    if not isinstance(argv, (list, tuple)) or any(not isinstance(a, str) for a in argv):
        raise QueryError(f"{label}: argv must be a list of strings.")
    try:
        outcome = runner(argv)
    except subprocess.TimeoutExpired as error:
        raise QueryError(f"{label}: request timed out after {timeout} seconds.") from error
    except TimeoutError as error:
        raise QueryError(f"{label}: request timed out.") from error
    if not isinstance(outcome, CommandOutcome):
        raise QueryError(f"{label}: runner must return a CommandOutcome.")
    if not isinstance(outcome.returncode, int):
        raise QueryError(f"{label}: runner returncode must be an integer.")
    return CommandOutcome(
        outcome.returncode,
        _bound_text(outcome.stdout, MAX_STDOUT_BYTES),
        _bound_text(outcome.stderr, MAX_STDERR_BYTES),
    )


def decode_wire_json(raw: object, label: str) -> Any:
    """Parse one bounded JSON object through the shared closed parser."""
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    try:
        return parse_closed_json(raw, max_bytes=MAX_QUERY_BYTES, label=label)
    except PacketError as error:
        raise QueryError(error.message) from error


def parse_index_entries(raw: str, label: str) -> Tuple[GitIndexEntry, ...]:
    entries: list[GitIndexEntry] = []
    for token in raw.split("\0"):
        token = token.strip()
        if not token:
            continue
        try:
            metadata, path = token.split("\t", 1)
            mode, object_id, stage = metadata.split(" ", 2)
        except ValueError as error:
            raise QueryError(f"{label}: malformed index line {token!r}.") from error
        if mode not in ("100644", "100755"):
            raise QueryError(f"{label}: entry {path!r} has non-regular mode {mode!r}.")
        entries.append(GitIndexEntry(mode, object_id, stage, path))
    return tuple(entries)


def classify_routing(entries: Sequence[GitIndexEntry]) -> Routing:
    paths = {entry.path for entry in entries}
    marker = SOURCE_MARKER in paths
    mapping = CANONICAL_MAPPING in paths
    generator = GENERATOR in paths
    if marker or (mapping and generator):
        evidence = [p for present, p in (
            (marker, SOURCE_MARKER), (mapping, CANONICAL_MAPPING), (generator, GENERATOR)
        ) if present]
        return Routing("source", tuple(sorted(evidence)))
    return Routing("consumer", ())


def parse_pr_view(payload: object, path: str) -> Pr:
    if not isinstance(payload, dict):
        raise QueryError(f"{path} must be a JSON object.")
    number = _field(payload, "number", path, (int,))
    if type(number) is not int:
        raise QueryError(f"{path}.number must be an integer.")
    head_oid = payload.get("headRefOid")
    if head_oid is not None and not isinstance(head_oid, str):
        raise QueryError(f"{path}.headRefOid must be a string or null.")
    for name in ("url", "title", "state", "baseRefName", "headRefName"):
        if not _field(payload, name, path, (str,)):
            raise QueryError(f"{path}.{name} must be a non-empty string.")
    return Pr(
        number, payload["url"], payload["title"], payload["state"],
        payload["baseRefName"], payload["headRefName"], head_oid,
    )


def normalize_rollup(payload: object, path: str) -> Tuple[Check, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise QueryError(f"{path} must be a JSON array.")
    checks: list[Check] = []
    for index, item in enumerate(payload):
        sub = f"{path}[{index}]"
        if not isinstance(item, dict):
            raise QueryError(f"{sub} must be a JSON object.")
        typename = item.get("__typename")
        if typename == "CheckRun":
            name = _field(item, "name", sub, (str,))
            status = _field(item, "status", sub, (str,))
            if status not in CHECK_RUN_STATUSES:
                raise QueryError(f"{sub}.status {status!r} is unknown.")
            conclusion = item.get("conclusion")
            if conclusion is not None and not isinstance(conclusion, str):
                raise QueryError(f"{sub}.conclusion must be a string or null.")
            if conclusion is not None and conclusion not in CHECK_RUN_CONCLUSIONS:
                raise QueryError(f"{sub}.conclusion {conclusion!r} is unknown.")
            details_url = item.get("detailsUrl")
            if details_url is not None and not isinstance(details_url, str):
                raise QueryError(f"{sub}.detailsUrl must be a string or null.")
            checks.append(Check(name, status, conclusion, details_url))
        elif typename == "StatusContext":
            context = _field(item, "context", sub, (str,))
            state = _field(item, "state", sub, (str,))
            if state not in STATUS_CONTEXT_STATES:
                raise QueryError(f"{sub}.state {state!r} is unknown.")
            normalized, conclusion = STATUS_CONTEXT_STATES[state]
            target_url = item.get("targetUrl")
            if target_url is not None and not isinstance(target_url, str):
                raise QueryError(f"{sub}.targetUrl must be a string or null.")
            checks.append(Check(context, normalized, conclusion, target_url))
        else:
            raise QueryError(f"{sub}.__typename {typename!r} is unknown.")
    return tuple(checks)


def require_selected_base(selected_base: Optional[str]) -> str:
    if not isinstance(selected_base, str) or not selected_base.strip():
        raise QueryError(
            "base-required: a selected base must be supplied before the "
            "existing-PR base is ever consulted."
        )
    return selected_base.strip()


def _probe(runner: Runner, argv: Sequence[str], label: str, code: str) -> str:
    result = run_query(runner, argv, label=label)
    if result.returncode != 0 or not result.stdout.strip():
        raise QueryError(f"{code}: {label} could not be resolved.")
    return result.stdout.strip()


def _ahead_behind(runner: Runner, remote_ref: str) -> Tuple[int, int]:
    result = run_query(
        runner, ("git", "rev-list", "--left-right", "--count", f"{remote_ref}...HEAD"),
        label="ahead-behind",
    )
    if result.returncode != 0:
        raise QueryError("rev-count-error: ahead/behind counts could not be derived.")
    try:
        behind_text, ahead_text = result.stdout.split()
        return int(behind_text), int(ahead_text)
    except (ValueError, TypeError) as error:
        raise QueryError("rev-count-malformed: unexpected ahead/behind output.") from error


def _gh_open_pr(runner: Runner) -> Optional[Pr]:
    result = run_query(
        runner,
        ("gh", "pr", "view", "--json",
         "url,number,title,state,baseRefName,headRefName,headRefOid"),
        label="gh-pr-view",
    )
    if result.returncode == 0:
        return parse_pr_view(decode_wire_json(result.stdout, "gh-pr-view"), "gh-pr-view")
    if result.returncode == 1:
        stderr = result.stderr.casefold()
        if any(word in stderr for word in ("auth", "not authenticated")):
            raise QueryError("gh-auth: authentication failed; never a policy fallback.")
        if any(marker in stderr for marker in _GH_NO_PR_MARKERS):
            return None
        raise QueryError(
            "gh-pr-error: gh pr view exited 1 without a recognized no-PR "
            "diagnostic; treat transient and network failures as errors so a "
            "duplicate PR is never created."
        )
    raise QueryError(f"gh-pr-error: gh pr view exited with {result.returncode}.")


def observe_publication(runner: Runner, *, branch: Optional[str] = None,
                        selected_base: Optional[str] = None) -> PublicationState:
    base = require_selected_base(selected_base)
    status = run_query(runner, ("git", "status", "--porcelain"), label="git-status")
    if status.returncode != 0:
        raise QueryError("git-status-error: git status could not be read.")
    if status.stdout.strip():
        return PublicationState(
            "dirty",
            _probe(runner, ("git", "branch", "--show-current"), "branch", "detached-head"),
            _probe(runner, ("git", "rev-parse", "HEAD"), "head", "head-unresolved"),
            None, None, 0, 0, None, ("uncommitted changes block publication",),
        )
    current = _probe(runner, ("git", "branch", "--show-current"), "branch", "detached-head")
    if branch is not None and current != branch:
        raise QueryError(f"branch-mismatch: on {current!r}, not {branch!r}.")
    head = _probe(runner, ("git", "rev-parse", "HEAD"), "head", "head-unresolved")
    _probe(runner, ("git", "rev-parse", "--verify", f"{base}^{{commit}}"), "base",
           "base-unresolved")

    upstream = run_query(runner, ("git", "rev-parse", "--abbrev-ref", "@{u}"), label="upstream")
    if upstream.returncode != 0 or not upstream.stdout.strip():
        return PublicationState("clean-unpushed", current, head, None, None, 0, 0, None, ())
    remote_ref = upstream.stdout.strip()
    remote_head = _probe(
        runner, ("git", "rev-parse", f"{remote_ref}^{{commit}}"), "remote-head",
        "remote-unresolved",
    )

    if head != remote_head:
        behind, ahead = _ahead_behind(runner, remote_ref)
        if ahead > 0 and behind > 0:
            raise QueryError("diverged: rebase, merge and force-push are never automatic.")
        if ahead > 0 and behind == 0:
            return PublicationState(
                "clean-unpushed", current, head, remote_ref, remote_head, ahead, 0, None, ()
            )
        if ahead == 0 and behind > 0:
            raise QueryError("remote-ahead: a non-fast-forward push is never attempted.")

    pr = _gh_open_pr(runner)
    if pr is None:
        return PublicationState(
            "pushed-no-pr", current, head, remote_ref, remote_head, 0, 0, None, ()
        )
    if pr.state != "OPEN":
        raise QueryError(f"pr-closed: existing PR {pr.number} is {pr.state!r}, not OPEN.")
    if pr.head_ref_name != current:
        raise QueryError(f"pr-head-mismatch: PR head {pr.head_ref_name!r}, branch {current!r}.")
    if pr.base_ref_name != base:
        raise QueryError(
            f"base-conflict: PR {pr.number} targets {pr.base_ref_name!r}, not the "
            f"required base {base!r}."
        )
    return PublicationState(
        "existing-matching-pr", current, head, remote_ref, remote_head, 0, 0,
        pr, ("existing PR reused, never duplicated",),
    )


def coverage_of(paths: Sequence[PathIdentity]) -> Coverage:
    entries = tuple(paths)
    if len({e.path for e in entries}) != len(entries):
        raise QueryError("coverage-duplicate: path inventory repeats a path.")
    for entry in entries:
        if entry.status not in ("present", "deleted"):
            raise QueryError(f"coverage-status: unknown status {entry.status!r}.")
    lines = [
        f"{e.status}:{e.path}:{e.sha256 or '-'}:{e.byte_count or 0}"
        for e in sorted(entries, key=lambda e: e.path)
    ]
    return Coverage(entries, sha256_hex("\n".join(lines).encode("utf-8")))


def coverage_drift(expected: Coverage, actual: Coverage) -> Tuple[str, ...]:
    expected_lookup = {e.path: e for e in expected.paths}
    actual_lookup = {e.path: e for e in actual.paths}
    drifted = set()
    for path, entry in actual_lookup.items():
        prior = expected_lookup.get(path)
        if prior is None or (prior.status, prior.sha256, prior.byte_count) != (
            entry.status, entry.sha256, entry.byte_count
        ):
            drifted.add(path)
    drifted.update(path for path in expected_lookup if path not in actual_lookup)
    return tuple(sorted(drifted))


def idempotent(expected: Coverage, actual: Coverage) -> bool:
    return not coverage_drift(expected, actual)