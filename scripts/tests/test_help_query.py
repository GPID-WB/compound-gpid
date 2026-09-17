"""Step 5 deterministic retrieval contracts; no model or filesystem retrieval."""
from __future__ import annotations

import copy
import itertools
import tracemalloc
from pathlib import Path

import pytest

from help import catalog, query

FIXTURES = Path(__file__).parent / "fixtures/help"


def evidence() -> tuple:
    """Return independent strict catalog/registry fixtures for retrieval tests."""
    value = catalog.load_strict_json(FIXTURES / "catalog-full.json")
    registry = catalog.load_strict_json(FIXTURES / "registry.json")
    template = value["commands"][1]
    for name, suite, intents in [
        ("cg-work", "cg", ["implement a plan"]),
        ("cg-review", "cg", ["review my recent code changes"]),
        ("cr-review", "cr", ["research review"]),
        ("cg-token-audit", "cg", ["measure token usage"]),
    ]:
        item = copy.deepcopy(template)
        item.update(id="slash:" + name, name="/" + name,
                    ownerModule="suite-" + suite, supportedSuites=[suite],
                    aliases=[], intents=intents, usage="/" + name,
                    examples=["/" + name], relatedCommands=[])
        item["activation"] = [dict(template["activation"][0], suite=suite)]
        value["commands"].append(item)
    shell = copy.deepcopy(value["commands"][0])
    shell.update(id="shell:cg-token-audit", name="cg-token-audit", aliases=[],
                 intents=["measure token usage"], supportedOS=["posix"],
                 usage="cg-token-audit", examples=["cg-token-audit"])
    shell["availability"]["evidence"] = shell["availability"]["evidence"][:1]
    value["commands"].append(shell)
    value["commands"].sort(key=lambda item: item["id"])
    catalog.validate_catalog(value, registry)
    return value, registry


def retrieve(text: str, suites: tuple = ("cg",), os_name: str = "windows") -> dict:
    """Query isolated evidence with explicitly proved active suites."""
    value, _ = evidence()
    return query.retrieve(value, text, suites, "kilo", os_name)


@pytest.mark.parametrize("text,kind,name", [
    ("  /CG-SKILL  ", "slash", "cg-skill"),
    ("\uff0f\uff23\uff27\uff0d\uff33\uff2b\uff29\uff2c\uff2c", "slash", "cg-skill"),
    ("SLASH:CG-SKILL", "slash", "cg-skill"),
    ("shell:CG-SKILL", "shell", "cg-skill"),
    ("/usr/bin/cg-skill", None, "/usr/bin/cg-skill"),
    ("cg-skill", None, "cg-skill"),
])
def test_normalization_preserves_kind_and_shell_basename(text, kind, name):
    """Names normalize before exact matching without merging command kinds."""
    assert query.normalize_query(text) == (kind, name)


@pytest.mark.parametrize("text,name", [
    ("/usr/bin/cg-skill", "cg-skill"),
    ("/tools/cg-skill.cmd", "cg-skill"),
])
def test_slash_path_coercion_requires_leading_slash_and_known_name(text, name):
    """Only leading-slash launcher paths with a known command name coerce."""
    assert query.normalize_query(text, known_names={"cg-skill"}) == ("shell", name)


@pytest.mark.parametrize("text,expected", [
    (r"C:\tools\cg-skill.cmd", r"c:\tools\cg-skill.cmd"),
    ("./bin/cg-skill", "./bin/cg-skill"),
    ("cg-skill.cmd", "cg-skill.cmd"),
    ("/usr/bin/cg-skill", "/usr/bin/cg-skill"),
])
def test_plain_query_text_is_kept_without_known_command_path_coercion(text, expected):
    """Free text and non-leading or unknown slash paths stay plain queries."""
    assert query.normalize_query(text) == (None, expected)


@pytest.mark.parametrize("text", ["a\x00b", "a\nb", "\t", "\x7f", "\x85", "\u200b", "\ud800", "x" * 4097])
def test_invalid_input_is_rejected_before_scoring(text):
    """Controls and overlength input never enter ranking."""
    with pytest.raises(catalog.HelpValidationError):
        query.normalize_query(text)


@pytest.mark.parametrize("text,expected", [
    ("/cg-skill", "slash:cg-skill"), ("shell:cg-skill", "shell:cg-skill"),
    ("slash:skill-chat", "slash:cg-skill"), ("/skill-chat", "slash:cg-skill"),
    ("skill-terminal", "shell:cg-skill"), ("cg-wrok", "slash:cg-work"),
    ("/cg-token-audit", "slash:cg-token-audit"),
    ("shell:cg-token-audit", "shell:cg-token-audit"),
])
def test_exact_alias_and_unique_transposition(text, expected):
    """Exact and unique typo matches retain the qualified identity."""
    result = retrieve(text)
    assert result["state"] == "exact"
    assert result["data"] == {"commandId": expected}


@pytest.mark.parametrize("name", ["cg-skill", "cg-token-audit"])
def test_bare_collision_is_always_candidates(name):
    """Availability must not suppress a kind collision."""
    result = retrieve(name)
    assert result["state"] == "candidates"
    assert set(result["data"]["commandIds"]) == {"shell:" + name, "slash:" + name}


@pytest.mark.parametrize("left,right,limit,expected", [
    ("ab", "ac", 0, 1), ("abc", "acb", 1, 1),
    ("abc", "axy", 1, 2), ("abcdef", "abcfed", 2, 2),
    ("abcdef", "xyzdef", 2, 3), ("", "abc", 1, 2),
])
def test_bounded_damerau_distance(left, right, limit, expected):
    """Distance is capped at limit + 1; adjacent transposition is one edit."""
    assert query.edit_distance(left, right, limit) == expected


def test_typo_limits_and_tied_best_are_not_exact():
    """Short queries receive no correction and a best-distance tie stays open."""
    value, _ = evidence()
    value["commands"][0]["aliases"] = ["ab", "abc", "abcde", "abcdef"]
    for text in ("ac", "axy", "abxyz", "xyzdef"):
        assert query.retrieve(value, text, ("cg",), "kilo", "windows")["state"] == "unsupported"
    result = retrieve("cg-skikl")
    assert result["state"] == "candidates"
    assert len(result["data"]["commandIds"]) == 2


def test_named_score_contract_and_semantic_abstention():
    """Thresholds are chosen before implementation and are not availability boosts."""
    assert query.WEIGHTS == {"identity_phrase": 30, "identity_token": 2,
                            "intent_phrase": 24, "intent_token": 6,
                            "usage_token": 1, "category_token": 2}
    assert (query.MIN_SCORE, query.WORKFLOW_THRESHOLD) == (6, 24)
    assert (query.MAX_CANDIDATES, query.CATEGORY_LIMIT, query.WORKFLOW_LIMIT) == (3, 3, 3)
    for text in ("quantum banana", "run a direct agent", "@cg-code-quality", "cg-skill-python/SKILL.md"):
        assert retrieve(text)["state"] == "unsupported"
    value, _ = evidence()
    value["commands"][0]["category"] = "banana"
    assert query.retrieve(value, "banana", ("cg",), "kilo", "windows")["state"] == "unsupported"


def test_relevance_precedes_active_and_os_tiebreaks():
    """Inactive but better evidence ranks ahead; relevance ties use availability."""
    value, _ = evidence()
    value["workflows"] = []
    for command in value["commands"]:
        command["intents"] = ["review"]
    cr = next(item for item in value["commands"] if item["id"] == "slash:cr-review")
    cr["intents"] = ["research review"]
    result = query.retrieve(value, "research review", ("cg",), "kilo", "windows")
    assert result["data"]["commandIds"][0] == "slash:cr-review"
    assert len(result["data"]["commandIds"]) == 3
    tied = query.retrieve(value, "review", ("cg",), "kilo", "windows")
    assert "slash:cr-review" not in tied["data"]["commandIds"]
    assert "shell:cg-token-audit" not in tied["data"]["commandIds"]
    assert tied == query.retrieve(value, "review", ("cg",), "kilo", "windows")


@pytest.mark.parametrize("suites", [("cg",), ("cr",), ("cg", "cr")])
def test_shared_commands_use_active_intersection(suites):
    """A capability command remains active in every supporting suite selection."""
    value, _ = evidence()
    command = value["commands"][0]
    assert query.availability(command, suites, "kilo", "windows")[0]


def test_explicit_workflow_requires_available_steps_and_threshold():
    """Relations never create workflows and weak intent overlap is insufficient."""
    assert retrieve("manage a skill")["state"] == "workflow"
    assert retrieve("manage a skill", ("cr",))["state"] != "workflow"
    value, _ = evidence()
    value["commands"][0]["supportedOS"] = ["posix"]
    assert query.retrieve(value, "manage a skill", ("cg",), "kilo", "windows")["state"] != "workflow"
    value["workflows"] = []
    assert query.retrieve(value, "manage a skill", ("cg",), "kilo", "windows")["state"] != "workflow"
    assert retrieve("manage")["state"] != "workflow"


def test_overview_is_stable_bounded_and_has_only_available_entries():
    """Overview is evidence-only and each category and workflow section is capped."""
    value, _ = evidence()
    result = query.retrieve(value, "  ", ("cr",), "kilo", "windows")
    assert result["state"] == "overview"
    assert result["data"]["workflowIds"] == []
    assert "slash:cg-skill" not in result["data"]["commandIds"]
    assert "shell:cg-token-audit" not in result["data"]["commandIds"]
    counts = {}
    for command in value["commands"]:
        if command["id"] in result["data"]["commandIds"]:
            counts[command["category"]] = counts.get(command["category"], 0) + 1
    assert max(counts.values()) <= 3
    assert result == query.retrieve(value, "", ("cr",), "kilo", "windows")


@pytest.mark.parametrize("platform,expected", [("win32", "windows"), ("linux", "posix"), ("darwin", "posix")])
def test_host_os_normalization(platform, expected):
    """Host OS comes from sys.platform, not a user query."""
    assert query.host_os(platform) == expected


def test_unknown_host_and_missing_active_evidence_fail_closed():
    """A missing activation/OS authority is not an unsupported task."""
    with pytest.raises(catalog.HelpValidationError):
        query.host_os("unknown")
    value, _ = evidence()
    with pytest.raises(catalog.HelpValidationError):
        query.retrieve(value, "", (), "kilo", "windows")


def test_typo_distance_memory_is_bounded_by_the_edit_band():
    """Long almost-equal identifiers must not allocate a quadratic matrix."""
    tracemalloc.start()
    try:
        assert query.edit_distance("a" * 512, "a" * 511 + "b", 2) == 1
        assert tracemalloc.get_traced_memory()[1] < 1000000
    finally:
        tracemalloc.stop()


def test_distance_matches_reference_for_short_identifier_space():
    """All short strings agree with an independent full Damerau reference."""
    def reference(left, right):
        """Unbounded matrix used only for tiny test inputs."""
        size = len(left) + len(right)
        rows = [[size] * (len(right) + 2) for _ in range(len(left) + 2)]
        rows[1][1:] = range(len(right) + 1)
        for i in range(len(left) + 1):
            rows[i + 1][1] = i
        seen = {}
        for i, char in enumerate(left, 1):
            matched = 0
            for j, other in enumerate(right, 1):
                prior_i, prior_j = seen.get(other, 0), matched
                cost = int(char != other)
                if not cost:
                    matched = j
                rows[i + 1][j + 1] = min(rows[i][j] + cost,
                    rows[i + 1][j] + 1, rows[i][j + 1] + 1,
                    rows[prior_i][prior_j] + i - prior_i + j - prior_j - 1)
            seen[char] = i
        return rows[-1][-1]
    words = ["".join(chars) for size in range(4)
             for chars in itertools.product("abc", repeat=size)]
    for left, right, limit in itertools.product(words, words, range(3)):
        assert query.edit_distance(left, right, limit) == min(reference(left, right), limit + 1)
    assert query.edit_distance("ca", "abc", 2) == 2


def test_normalized_asset_and_casefold_expansion_do_not_bypass_limits():
    """NFKC/case folding must precede the last boundary checks."""
    assert retrieve("\uff20cg-code-quality")["state"] == "unsupported"
    with pytest.raises(catalog.HelpValidationError):
        query.normalize_query("\u0130" * 2048)
