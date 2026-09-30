"""Pure bounded retrieval over validated help evidence (Python 3.8+).

Queries are limited to 4096 UTF-8 bytes before and after NFKC normalization.
Scores are evidence weights, not probabilities. Availability only breaks ties.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from bisect import bisect_left
from typing import Any, Dict, Optional, Sequence, Tuple

from help.base import HelpValidationError, normalize_command_key

MAX_QUERY_BYTES = 4096
MAX_CANDIDATES = CATEGORY_LIMIT = WORKFLOW_LIMIT = 3
MIN_SCORE = 6
WORKFLOW_THRESHOLD = 24
WORKFLOW_EXACT_SCORE = 24
WORKFLOW_TOKEN_SCORE = 6
WEIGHTS = {"identity_phrase": 30, "identity_token": 2, "intent_phrase": 24,
           "intent_token": 6, "usage_token": 1, "category_token": 2}
STOP_WORDS = frozenset("a an and are as at be by cg cr for from how i in is it me my of on or the to with".split())


def normalize_query(text: str, known_names: Optional[set] = None) -> Tuple[Optional[str], str]:
    """Return (kind selector, normalized query); e.g. '/CG-WORK' -> slash/cg-work.

    A leading slash without a slash inside selects the slash kind. A multi-
    segment slash path (a copyable launcher path) is coerced to the shell kind
    only when the caller proves its final segment (after an optional ``.cmd``
    suffix) is a known command name; every other path-like or plain text is
    kept as free query text.

    Args: text: Untrusted invocation text, never a shell command.
        known_names: Optional casefolded known command names/aliases that
            authorize slash-path-to-shell coercion.
    Returns: Optional kind and normalized identifier or free text.
    Raises: HelpValidationError for controls, invalid Unicode, or byte overflow.
    """
    if not isinstance(text, str):
        raise HelpValidationError("query must be text")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    for value in (text, normalized):
        if any(unicodedata.category(char).startswith("C") for char in value):
            raise HelpValidationError("query contains control or invalid characters")
        if len(value.encode("utf-8")) > MAX_QUERY_BYTES:
            raise HelpValidationError("query exceeds 4096 UTF-8 bytes")
    text = normalized.strip()
    kind = None
    if text.startswith(("slash:", "shell:")):
        kind, text = text.split(":", 1)
        text = text.strip()
    path = text.replace("\\", "/")
    if kind != "slash" and " " not in path and path.startswith("/") and "/" in path[1:]:
        basename = path.rsplit("/", 1)[-1]
        if basename.endswith(".cmd"):
            basename = basename[:-4]
        if known_names is not None and basename in known_names:
            kind, text = "shell", basename
    elif text.startswith("/"):
        kind, text = kind or "slash", text[1:]
    return kind, text


def host_os(platform: Optional[str] = None) -> str:
    """Map sys.platform to catalog OS; e.g. 'win32' returns 'windows'.

    Args: platform: Host value, injectable for tests.
    Returns: windows or posix.
    Raises: HelpValidationError for unsupported hosts.
    """
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        return "windows"
    if platform.startswith(("linux", "darwin", "freebsd", "openbsd", "netbsd", "aix", "sunos", "cygwin")):
        return "posix"
    raise HelpValidationError("unsupported host OS: " + platform)


def _tokens(text: str) -> set:
    """Return punctuation-separated semantic tokens without common stop words."""
    return set(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold())) - STOP_WORDS


def edit_distance(left: str, right: str, limit: int) -> int:
    """Return bounded Damerau-Levenshtein distance; e.g. ('abc','acb',1) -> 1.

    Args: left, right: Identifiers. limit: Maximum accepted distance.
    Returns: Exact distance up to limit, otherwise limit + 1.
    """
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    # A path costing <= limit cannot leave this diagonal band. Retain sparse
    # earlier rows for full Damerau transpositions, rather than an O(n*m) table.
    cap = limit + 1
    rows = [{} for _ in range(len(left) + 2)]
    rows[1] = {j + 1: j for j in range(min(len(right), limit) + 1)}
    positions: Dict[str, list] = {}
    for j, char in enumerate(right, 1):
        positions.setdefault(char, []).append(j)
    seen: Dict[str, int] = {}
    for i, char in enumerate(left, 1):
        if i <= limit:
            rows[i + 1][1] = i
        low, high = max(1, i - limit), min(len(right), i + limit)
        occurrences = positions.get(char, [])
        previous = bisect_left(occurrences, low)
        matched = occurrences[previous - 1] if previous else 0
        for j in range(low, high + 1):
            other = right[j - 1]
            prior_i, prior_j = seen.get(other, 0), matched
            cost = int(char != other)
            if not cost:
                matched = j
            rows[i + 1][j + 1] = min(
                cap, rows[i].get(j, cap) + cost,
                rows[i + 1].get(j, cap) + 1, rows[i].get(j + 1, cap) + 1,
                rows[prior_i].get(prior_j, cap) + i - prior_i + j - prior_j - 1)
        seen[char] = i
    return rows[-1].get(len(right) + 1, cap)


def availability(command: dict, suites: Sequence[str], platform: str, os_name: str) -> tuple:
    """Return suite/host booleans and label; shared commands use intersection.

    Args: command: Validated record. suites/platform/os_name: Proved context.
    Returns: (active, host available, display label), e.g. (True, True, 'active').
    """
    active = bool(set(command["supportedSuites"]) & set(suites))
    host = platform in command["supportedPlatforms"] and bool(
        {"any", os_name} & set(command["supportedOS"]))
    label = "active" if active else "inactive suite: " + ", ".join(command["supportedSuites"])
    if not host:
        label += "; unavailable on " + platform + "/" + os_name
    elif command["availability"]["status"] == "conditional":
        label += "; prerequisites apply"
    return active, host, label


def _score(command: dict, text: str, tokens: set) -> Tuple[int, str]:
    """Score each semantic field once; repeated query words cannot inflate rank."""
    identities = [command["id"].split(":", 1)[1]] + command["aliases"]
    fields = {
        "identity_phrase": any(text == normalize_command_key(item) for item in identities),
        "identity_token": len(tokens & _tokens(" ".join(identities))),
        "intent_phrase": any(_tokens(item) == tokens and tokens for item in command["intents"]),
        "intent_token": len(tokens & _tokens(" ".join(command["intents"]))),
        "usage_token": len(tokens & _tokens(" ".join(command["examples"] + [command["usage"]]))),
        "category_token": len(tokens & _tokens(command["category"])),
    }
    if not (fields["intent_token"] or fields["usage_token"]):
        return 0, ""
    score = sum(WEIGHTS[key] * int(count) for key, count in fields.items())
    reason = ", ".join(key.replace("_", " ") for key, count in fields.items() if count)
    return score, reason


def retrieve(value: dict, text: str, suites: Sequence[str], platform: str, os_name: str) -> Dict[str, Any]:
    """Return a deterministic state/data retrieval decision without I/O.

    Args: value: Fully validated catalog. text: Query. suites/platform/os_name:
        Validated installation context supplied by the callable service.
    Returns: State, schema data, and internal ranking rows for rendering.
    Raises: HelpValidationError for absent/unknown activation or invalid input.
    Example: retrieve(catalog, '/cg-work', ['cg'], 'kilo', 'windows').
    """
    if not suites or not set(suites) <= {item["id"] for item in value["suites"]}:
        raise HelpValidationError("active suite evidence is missing or unknown")
    if os_name not in {"windows", "posix"}:
        raise HelpValidationError("host OS evidence is missing")
    commands = value["commands"]
    by_id = {item["id"]: item for item in commands}
    known_names = set()
    for item in commands:
        known_names.add(normalize_command_key(item["name"]))
        known_names.update(normalize_command_key(alias) for alias in item["aliases"])
    kind, text = normalize_query(text, known_names=known_names)
    if re.search(r"@[a-z][a-z0-9-]*|(?:cg|cr)-skill-[a-z]|skill\.md", text):
        return {"state": "unsupported", "data": {"reason": "Direct agent and skill assets are outside command help. Use /cg-help for commands."}}
    tokens = _tokens(text)

    def order(row: tuple) -> tuple:
        """Rank relevance first, then active suite, host support, and qualified ID."""
        active, host, _ = availability(by_id[row[0]], suites, platform, os_name)
        return -row[1], -int(active), -int(host), row[0]

    def available(command: dict) -> bool:
        """Require both suite and host availability for overview/workflow steps."""
        return all(availability(command, suites, platform, os_name)[:2])

    workflows = [item for item in value["workflows"]
                 if set(item["supportedSuites"]) & set(suites)
                 and all(available(by_id[step["commandId"]]) and step["evidence"] for step in item["steps"])]
    if not text and kind is None:
        ids = []
        for category in sorted({item["category"] for item in commands}):
            ids.extend(item["id"] for item in sorted(commands, key=lambda item: item["id"])
                       if item["category"] == category and available(item))
            category_ids = [key for key in ids if by_id[key]["category"] == category]
            ids = [key for key in ids if key not in category_ids[CATEGORY_LIMIT:]]
        return {"state": "overview", "data": {"commandIds": ids,
                "workflowIds": [item["id"] for item in workflows[:WORKFLOW_LIMIT]]}}
    eligible = [item for item in commands if kind is None or item["kind"] == kind]
    exact = [item["id"] for item in eligible if text in
             [normalize_command_key(name) for name in [item["name"]] + item["aliases"]]]
    rows = [(key, 100, "exact name or alias") for key in exact]
    if not rows and re.fullmatch(r"[a-z][a-z0-9-]*", text) and len(text) >= 3:
        limit = 1 if len(text) <= 5 else 2
        distances = [(item["id"], min(edit_distance(text, normalize_command_key(name), limit)
                     for name in [item["name"]] + item["aliases"])) for item in eligible]
        best = min((distance for _, distance in distances), default=limit + 1)
        if best <= limit:
            rows = [(key, 100 - best, "identifier typo: {} edit(s)".format(best))
                    for key, distance in distances if distance == best]
    if len(rows) == 1:
        return {"state": "exact", "data": {"commandId": rows[0][0]}}
    if not rows:
        matches = []
        for workflow in workflows:
            score = max((WORKFLOW_EXACT_SCORE * int(tokens == _tokens(intent) and bool(tokens))
                         + WORKFLOW_TOKEN_SCORE * len(tokens & _tokens(intent))
                         for intent in workflow["intents"]), default=0)
            if score >= WORKFLOW_THRESHOLD:
                matches.append((score, workflow["id"]))
        if matches and kind is None:
            workflow_id = sorted(matches, key=lambda row: (-row[0], row[1]))[0][1]
            workflow = next(item for item in workflows if item["id"] == workflow_id)
            return {"state": "workflow", "data": {"workflowId": workflow_id,
                    "commandIds": list(dict.fromkeys(step["commandId"] for step in workflow["steps"]))}}
        rows = [(item["id"], *_score(item, text, tokens)) for item in eligible]
        rows = [row for row in rows if row[1] >= MIN_SCORE]
    rows = sorted(rows, key=order)[:MAX_CANDIDATES]
    if not rows:
        return {"state": "unsupported", "data": {"reason": "No in-scope command or explicit workflow evidence supports this request."}}
    ids = [row[0] for row in rows]
    return {"state": "candidates", "rows": rows, "data": {
        "commandIds": ids, "reasons": [row[2] for row in rows],
        "followUpQueries": [follow_up(key) for key in ids]}}


def follow_up(command_id: str) -> str:
    """Return a disambiguated exact query; e.g. shell:cg-skill stays qualified.

    Args: command_id: Validated qualified ID.
    Returns: Copyable /cg-help invocation.
    """
    return "/cg-help " + ("/" + command_id.split(":", 1)[1]
                          if command_id.startswith("slash:") else command_id)
