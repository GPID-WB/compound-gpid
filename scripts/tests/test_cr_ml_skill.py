"""Content and routing contracts for the CR ML skill.

Created 2026-09-03. These tests keep the activated skill small and verify that
its detailed statistical-learning guidance remains available through focused,
progressive-disclosure references.
"""
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / ".github/skills/cr-skill-ml-economics"
CORE_PATH = SKILL_ROOT / "SKILL.md"
FIXTURE_PATH = REPO_ROOT / "scripts/tests/fixtures/cr_ml_skill_evaluation.json"
CR_WORK_PATH = REPO_ROOT / ".github/prompts/cr-work.prompt.md"
ML_AGENT_PATH = REPO_ROOT / ".github/agents/cr-ml-methodology.agent.md"
CORE_LINE_LIMIT = 120
TARGET_SKILL_ROOTS = (
    REPO_ROOT / ".claude/skills",
    REPO_ROOT / ".agents/skills",
    REPO_ROOT / ".opencode/skills",
    REPO_ROOT / ".kilo/skills",
)


def _read_fixture() -> Dict[str, Any]:
    """Load the inert ML skill evaluation fixture."""
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _read_frontmatter(text: str) -> Dict[str, str]:
    """Parse the simple scalar frontmatter fields used by skills."""
    match = re.match(r"^\ufeff?---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if match is None:
        return {}
    values: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def _assert_terms(text: str, terms: list[str], context: str) -> None:
    """Assert each required term independently for useful failure messages."""
    lowered = text.casefold()
    missing = [term for term in terms if term.casefold() not in lowered]
    assert not missing, f"{context} is missing required terms: {missing}"


def _parse_core_routes(core: str) -> dict[str, set[str]]:
    """Parse the core router's need-to-reference table."""
    routes: dict[str, set[str]] = {}
    for line in core.splitlines():
        match = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", line)
        if match is None:
            continue
        need, read = match.groups()
        references = set(re.findall(r"references/([a-z0-9-]+\.md)", read))
        if references:
            routes[need.strip()] = references
    return routes


def _resolve_task_references(task: dict[str, Any], routes: dict[str, set[str]]) -> set[str]:
    """Resolve one fixture task through named core route rows."""
    resolved: set[str] = set()
    for need in task["route_needs"]:
        if need not in routes:
            raise KeyError(f"Unknown ML route need: {need}")
        resolved.update(routes[need])
    return resolved


def test_ml_skill_core_has_valid_frontmatter() -> None:
    """The canonical ML skill retains the research skill frontmatter contract."""
    frontmatter = _read_frontmatter(CORE_PATH.read_text(encoding="utf-8"))

    assert frontmatter.get("name") == "cr-skill-ml-economics"
    assert frontmatter.get("module") == "research"
    assert frontmatter.get("description")


def test_ml_skill_core_is_a_thin_router() -> None:
    """The activated core stays within the local thin-router target."""
    line_count = len(CORE_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= CORE_LINE_LIMIT, (
        f"SKILL.md has {line_count} lines; expected no more than {CORE_LINE_LIMIT}"
    )


def test_ml_skill_core_contains_selective_reference_routing() -> None:
    """The core inventories references and directs agents to load selectively."""
    core = CORE_PATH.read_text(encoding="utf-8")
    fixture = _read_fixture()
    reference_names = list(fixture["references"])

    for reference_name in reference_names:
        assert reference_name in core, f"Core router omits {reference_name}"
    _assert_terms(
        core,
        ["one or two", "only", "not load all", "reference"],
        "Core selective-loading contract",
    )


def test_ml_skill_core_keeps_research_integrity_boundaries_inline() -> None:
    """High-risk interpretation and reproducibility boundaries remain visible."""
    core = CORE_PATH.read_text(encoding="utf-8")

    _assert_terms(
        core,
        [
            "prediction",
            "causal",
            "leakage",
            "seed",
            "test set",
            "target population",
            "weights",
        ],
        "Core integrity contract",
    )


@pytest.mark.parametrize("reference_name", list(_read_fixture()["references"]))
def test_ml_skill_reference_exists_and_has_assigned_content(reference_name: str) -> None:
    """Each reference exists, is non-empty, and carries its assigned content."""
    fixture = _read_fixture()
    specification = fixture["references"][reference_name]
    reference_path = SKILL_ROOT / "references" / reference_name

    assert reference_path.is_file(), reference_path
    content = reference_path.read_text(encoding="utf-8")
    assert content.strip(), reference_path
    _assert_terms(content, specification["required_terms"], reference_name)


def test_ml_skill_reference_roles_are_distinct() -> None:
    """The reference inventory assigns one distinct role to each file."""
    purposes = [
        specification["purpose"]
        for specification in _read_fixture()["references"].values()
    ]

    assert len(purposes) == len(set(purposes))


def test_ml_skill_routing_fixture_covers_every_reference() -> None:
    """Representative tasks route to one or two focused references."""
    fixture = _read_fixture()
    known_references = set(fixture["references"])
    routed_references = set()

    assert fixture["tasks"]
    for task in fixture["tasks"]:
        expected = set(task["expected_references"])
        assert expected
        assert len(expected) <= 2, task["id"]
        assert expected <= known_references, task["id"]
        routed_references.update(expected)

    assert routed_references == known_references


def test_ml_skill_routing_fixture_matches_core_routes() -> None:
    """Each representative task resolves through the intended route rows."""
    core = CORE_PATH.read_text(encoding="utf-8")
    routes = _parse_core_routes(core)
    fixture = _read_fixture()

    for task in fixture["tasks"]:
        _assert_terms(core, task["required_core_terms"], task["id"])
        assert _resolve_task_references(task, routes) == set(task["expected_references"])


def test_unknown_ml_route_need_is_rejected() -> None:
    """A fixture cannot silently route through an unknown need label."""
    routes = _parse_core_routes(CORE_PATH.read_text(encoding="utf-8"))
    task = {"route_needs": ["unknown route need"]}

    with pytest.raises(KeyError, match="Unknown ML route need"):
        _resolve_task_references(task, routes)


def test_ml_skill_core_does_not_require_loading_the_full_reference_directory() -> None:
    """The router prevents an all-reference context expansion by default."""
    core = CORE_PATH.read_text(encoding="utf-8").casefold()

    assert "do not load all eight" in core
    assert "only the reference" in core or "only one or two references" in core


def test_ml_skill_references_have_no_nonprinting_control_characters() -> None:
    """Reference Markdown remains safe for renderers and mathematical notation."""
    reference_files = sorted((SKILL_ROOT / "references").glob("*.md"))

    assert reference_files
    for reference_path in reference_files:
        content = reference_path.read_bytes()
        control_bytes = [
            byte
            for byte in content
            if byte < 32 and byte not in (9, 10, 13)
        ]
        assert not control_bytes, f"{reference_path} contains {control_bytes}"

    high_dimensional = (
        SKILL_ROOT / "references/high-dimensional-and-regularized-methods.md"
    ).read_text(encoding="utf-8")
    assert r"\beta_0" in high_dimensional


def test_ranger_example_sets_an_explicit_engine_seed() -> None:
    """The stochastic R forest example controls the ranger RNG explicitly."""
    implementation = (
        SKILL_ROOT / "references/implementation-r-tidymodels.md"
    ).read_text(encoding="utf-8")

    assert 'set_engine("ranger", importance = "permutation", seed = 20260903)' in implementation


def test_r_starter_tuning_budget_is_bounded() -> None:
    """The starter R workflow does not imply an uncontrolled compute budget."""
    implementation = (
        SKILL_ROOT / "references/implementation-r-tidymodels.md"
    ).read_text(encoding="utf-8")

    assert "rand_forest(trees = 300" in implementation
    assert "vfold_cv(train_data, v = 5)" in implementation
    assert "grid = 8" in implementation
    assert "control_grid(save_pred = FALSE)" in implementation
    assert "fit time and memory" in implementation


def test_cr_work_conditionally_loads_ml_skill_for_ml_work() -> None:
    """Research work loads ML guidance only for ML implementation slices."""
    work = CR_WORK_PATH.read_text(encoding="utf-8")

    assert re.search(
        r"plan task type.*ML/Prediction.*cr-skill-ml-economics",
        work,
        re.IGNORECASE | re.DOTALL,
    )
    assert re.search(
        r"Implementation.*ML.*cr-skill-ml-economics",
        work,
        re.IGNORECASE | re.DOTALL,
    )
    assert "Do not load all eight references" in work
    always_load = work.split("4. If the plan task type", 1)[0]
    assert "cr-skill-ml-economics" not in always_load


def test_cr_work_does_not_load_derivation_skill_without_derivation_context() -> None:
    """Derivation guidance is conditional rather than universal for implementation."""
    work = CR_WORK_PATH.read_text(encoding="utf-8")

    assert re.search(
        r"Implementation.*declared or detected.*derivation|"
        r"Implementation.*derivation artifact",
        work,
        re.IGNORECASE | re.DOTALL,
    )


def test_ml_methodology_agent_has_a_cumulative_reference_budget() -> None:
    """Review routing caps references across a file review, not per check."""
    agent = ML_AGENT_PATH.read_text(encoding="utf-8").casefold()

    _assert_terms(
        agent,
        ["per-file", "per-review", "reference budget", "cumulative", "additional"],
        "ML methodology cumulative reference budget",
    )


def test_ml_methodology_agent_routes_checks_to_focused_references() -> None:
    """The review agent maps checks to relevant references without a bulk read."""
    agent = ML_AGENT_PATH.read_text(encoding="utf-8")
    fixture = _read_fixture()

    for reference_name in fixture["references"]:
        assert reference_name in agent, f"Agent routing omits {reference_name}"
    _assert_terms(
        agent,
        [
            "reference routing",
            "only the relevant",
            "target population",
            "estimator support",
            "design-based variance",
            "sample_weight",
        ],
        "ML methodology agent routing contract",
    )
    assert "every ML estimator fit call" not in agent


def test_public_docs_describe_the_cr_ml_skill_reference_set() -> None:
    """Public documentation exposes the CR ML skill without counting references as skills."""
    catalog = (REPO_ROOT / "docs/skills/index.md").read_text(encoding="utf-8")
    research = (REPO_ROOT / "docs/skills/research.md").read_text(encoding="utf-8")
    reference = (REPO_ROOT / "docs/reference.md").read_text(encoding="utf-8")

    _assert_terms(
        catalog + research + reference,
        [
            "cr-skill-ml-economics",
            "progressive disclosure",
            "Hastie",
            "high-dimensional",
            "tidymodels",
            "scikit-learn",
        ],
        "CR ML public documentation",
    )


def test_public_research_catalog_lists_all_canonical_cr_skills() -> None:
    """The research catalog cannot claim completeness while omitting CR skills."""
    catalog = (REPO_ROOT / "docs/skills/research.md").read_text(encoding="utf-8")
    canonical = {
        path.name
        for path in (REPO_ROOT / ".github/skills").iterdir()
        if path.is_dir() and path.name.startswith("cr-skill-")
    }
    listed = set(
        re.findall(
            r"\.github/skills/(cr-skill-[a-z-]+)/SKILL\.md",
            catalog,
        )
    )

    assert listed == canonical
    assert len(listed) == 15


def test_docs_site_checker_validates_both_skill_families() -> None:
    """The docs checker enforces complete CG and CR catalog sets symmetrically."""
    checker = (REPO_ROOT / "scripts/check-docs-site.js").read_text(encoding="utf-8")

    _assert_terms(
        checker,
        ["technicalCanonical", "technicalCatalog", "researchCatalog", "researchCanonical"],
        "Docs skill-catalog checker",
    )
    assert "categoryCounts.join" not in checker


def test_generated_cr_ml_skill_bundles_match_canonical_inventory() -> None:
    """Every generated platform contains the complete CR ML reference bundle."""
    canonical_files = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
    }
    assert len(canonical_files) == 9

    for target_root in TARGET_SKILL_ROOTS:
        generated = target_root / SKILL_ROOT.name
        generated_files = {
            path.relative_to(generated).as_posix()
            for path in generated.rglob("*")
            if path.is_file()
        }
        assert generated_files == canonical_files, target_root
        for relative in canonical_files:
            assert (generated / relative).read_bytes() == (
                SKILL_ROOT / relative
            ).read_bytes(), relative


def test_ci_and_release_gates_include_the_cr_ml_contract() -> None:
    """The focused CR ML contract runs in CI and release preflight."""
    ci = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    release = (REPO_ROOT / "create-release.ps1").read_text(encoding="utf-8")
    preflight = (REPO_ROOT / "scripts/cg_pr_preflight.py").read_text(encoding="utf-8")

    assert "scripts/cg_pr_preflight.py" in ci
    assert "scripts/cg_pr_preflight.py" in release
    assert "scripts/tests/test_cr_ml_skill.py" in preflight


def test_semantic_ml_safeguards_are_present() -> None:
    """High-risk safeguards are tested beyond generic keyword inventory."""
    references = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SKILL_ROOT / "references").glob("*.md")
    )

    _assert_terms(
        references,
        [
            "blocked group-time",
            "event_level",
            "pos_label",
            "effective sample size",
            "nonresponse",
            "design-based variance",
            "training-mean OOS",
        ],
        "ML semantic safeguards",
    )


def test_ml_scholarly_references_have_stable_provenance() -> None:
    """Scholarly recommendations carry a DOI or stable canonical URL."""
    references = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SKILL_ROOT / "references").glob("*.md")
    )

    assert references.count("https://doi.org/") >= 12
    assert "Davis and Goadrich (2006)" in references
    assert re.search(
        r"The relationship between Precision-Recall and ROC\s+curves",
        references,
    )
    assert "Illustrations, sources and a solution" in references
