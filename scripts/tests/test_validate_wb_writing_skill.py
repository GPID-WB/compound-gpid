"""Tests for World Bank report-writing skill validation logic.

Run from repo root:
    python -m pytest scripts/tests/test_validate_wb_writing_skill.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

import validate_wb_writing_skill as validator


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _skill_root(repo_root: Path) -> Path:
    return repo_root / ".github" / "skills" / "cg-skill-wb-report-writing"


def _create_repo_file(repo_root: Path, rel_path: str, content: str = "x") -> None:
    path = repo_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_source_pack(slug: str) -> dict:
    return {
        "schema_version": 1,
        "document_type": slug,
        "status": "approved",
        "approved_by": "reviewer@example.org",
        "approved_on": "2026-07-23",
        "intended_audience": "Policy and technical readers",
        "disclaimer_requirement": "required",
        "required_disclaimers": ["[UNPUBLISHED: DO NOT CIRCULATE]"],
        "terminology_status": "approved",
        "terminology_sources": [
            "https://www.worldbank.org/en/about/unit/decdg",
            "https://www.worldbank.org/en/publication/wdr",
        ],
        "exemplars": [
            {
                "title": "Exemplar A",
                "source": "https://www.worldbank.org/en/research/dime",
                "retrieved_on": "2026-07-20",
                "relevant_sections": ["Overview", "Findings"],
                "authority_rationale": "Authoritative publication.",
            },
            {
                "title": "Exemplar B",
                "source": "https://www.worldbank.org/en/research",
                "retrieved_on": "2026-07-20",
                "relevant_sections": ["Structure"],
                "authority_rationale": "Comparable audience and format.",
            },
        ],
    }


def _valid_eval_result(slug: str) -> dict:
    base = ".github/skills/cg-skill-wb-report-writing"
    return {
        "schema_version": 1,
        "document_type": slug,
        "status": "accepted",
        "eval_definition": f"{base}/evals/types/{slug}.json",
        "benchmark": f"{base}/evals/benchmarks/{slug}.benchmark.json",
        "grading": f"{base}/evals/grades/{slug}.grading.json",
        "feedback": f"{base}/evals/feedback/{slug}.feedback.json",
        "assertions": {"total": 4, "passed": 4, "failed": 0},
        "guardrails": {
            "numeric_fidelity": True,
            "citation_integrity": True,
            "institutional_position": True,
            "data_status_propagation": True,
            "country_sensitivity": True,
            "type_specific_checks": True,
        },
        "human_accepted": True,
        "human_reviewer": "reviewer@example.org",
        "human_reviewed_on": "2026-07-23",
    }


def _write_valid_eval_support_files(repo_root: Path, slug: str) -> None:
    """Create valid companion artifacts referenced by eval-result payloads."""
    base = _skill_root(repo_root) / "evals"

    _write_json(
        base / "types" / f"{slug}.json",
        {
            "schema_version": 1,
            "document_type": slug,
            "operation_coverage": ["draft", "revise"],
        },
    )
    _write_json(
        base / "benchmarks" / f"{slug}.benchmark.json",
        {
            "schema_version": 1,
            "document_type": slug,
            "baseline": "no-skill",
            "comparison": "with-skill",
            "required_checks": ["factual-fidelity"],
        },
    )
    _write_json(
        base / "grades" / f"{slug}.grading.json",
        {
            "schema_version": 1,
            "document_type": slug,
            "pass_threshold": 1,
            "criteria": [
                {"id": key, "required": True}
                for key in validator.REQUIRED_GUARDRAILS
            ],
        },
    )
    _write_json(
        base / "feedback" / f"{slug}.feedback.json",
        {
            "schema_version": 1,
            "document_type": slug,
            "summary": "Accepted",
            "reviewer_notes": ["All checks passed."],
        },
    )


def _write_child_plan(path: Path, status: str, completed_date: str | None) -> None:
    frontmatter = [
        "---",
        'title: "Child plan"',
        f"status: {status}",
        f'parent-plan: "{validator.PARENT_PLAN_PATH}"',
    ]
    if completed_date is not None:
        frontmatter.append(f"completed-date: {completed_date}")
    frontmatter.extend(["---", "", "# Child Plan", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(frontmatter), encoding="utf-8")


def _write_parent_plan_with_execution_report(repo_root: Path, report_rel_path: str) -> None:
    plan_path = repo_root / validator.PARENT_PLAN_PATH
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "---",
                'title: "Parent plan"',
                f'execution-report: "{report_rel_path}"',
                "---",
                "",
                "# Parent Plan",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_execution_report(path: Path, plan_path: str, status: str = "completed") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f'plan: "{plan_path}"',
                f"status: {status}",
                "---",
                "",
                "# Execution Report",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_validate_source_pack_passes_for_valid_payload(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-research-working-paper"
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, _valid_source_pack(slug))

    errors = validator.validate_source_pack(repo_root, slug)

    assert errors == []


def test_validate_source_pack_rejects_invalid_status(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_source_pack(slug)
    payload["status"] = "draft"
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("status" in err for err in errors)


def test_validate_source_pack_rejects_placeholder_exemplar_host(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_source_pack(slug)
    payload["exemplars"][0]["source"] = "https://example.org/placeholder"
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("placeholder host" in err for err in errors)


def test_validate_source_pack_rejects_path_escape(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "executive-summary"
    payload = _valid_source_pack(slug)
    payload["terminology_sources"] = ["../../outside.txt"]
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("outside repository root" in err for err in errors)


def test_validate_source_pack_rejects_directory_repo_path(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "executive-summary"
    payload = _valid_source_pack(slug)
    directory_rel = "docs/references"
    (repo_root / directory_rel).mkdir(parents=True, exist_ok=True)
    payload["terminology_sources"] = [directory_rel]
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("must be a file" in err for err in errors)


def test_validate_source_pack_rejects_impossible_iso_date(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "executive-summary"
    payload = _valid_source_pack(slug)
    payload["approved_on"] = "2026-02-31"
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("approved_on" in err for err in errors)


def test_validate_source_pack_requires_intended_audience(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_source_pack(slug)
    payload["intended_audience"] = ""
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("intended_audience" in err for err in errors)


def test_validate_source_pack_requires_disclaimers_when_required(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_source_pack(slug)
    payload["required_disclaimers"] = []
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("disclaimer_requirement=required" in err for err in errors)


def test_validate_source_pack_accepts_unresolved_terminology_status(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_source_pack(slug)
    payload["terminology_status"] = "unresolved"
    payload["terminology_sources"] = []
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert errors == []


def test_validate_source_pack_rejects_legacy_not_required_terminology_status(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_source_pack(slug)
    payload["terminology_status"] = "not-required"
    source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
    _write_json(source_pack_path, payload)

    errors = validator.validate_source_pack(repo_root, slug)

    assert any("terminology_status" in err for err in errors)


def test_validate_eval_result_passes_for_valid_payload(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "flagship-report-section"
    payload = _valid_eval_result(slug)

    _write_valid_eval_support_files(repo_root, slug)

    result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
    _write_json(result_path, payload)

    errors = validator.validate_eval_result(repo_root, slug)

    assert errors == []


def test_validate_eval_result_requires_guardrails_true(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "country-analytical-narrative"
    payload = _valid_eval_result(slug)
    payload["guardrails"]["country_sensitivity"] = False

    _write_valid_eval_support_files(repo_root, slug)

    result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
    _write_json(result_path, payload)

    errors = validator.validate_eval_result(repo_root, slug)

    assert any("guardrails.country_sensitivity" in err for err in errors)


def test_validate_eval_result_rejects_escaping_artifact_path(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "technical-methodology"
    payload = _valid_eval_result(slug)
    payload["benchmark"] = "../../secrets.txt"

    _write_valid_eval_support_files(repo_root, slug)

    result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
    _write_json(result_path, payload)

    errors = validator.validate_eval_result(repo_root, slug)

    assert any("outside repository root" in err for err in errors)


def test_validate_eval_result_rejects_invalid_contract_fields(tmp_path: Path) -> None:
    cases = [
        ("status", "draft", "status must be 'accepted'"),
        (
            "eval_definition",
            ".github/skills/cg-skill-wb-report-writing/evals/types/other.json",
            "eval_definition must match",
        ),
        (
            "benchmark",
            ".github/skills/cg-skill-wb-report-writing/evals/benchmarks/policy-brief.benchmark.json",
            "benchmark must match",
        ),
        (
            "grading",
            ".github/skills/cg-skill-wb-report-writing/evals/grades/policy-brief.grading.json",
            "grading must match",
        ),
        (
            "feedback",
            ".github/skills/cg-skill-wb-report-writing/evals/feedback/policy-brief.feedback.json",
            "feedback must match",
        ),
        ("human_reviewer", "", "human_reviewer must be a non-empty reviewer identity"),
        ("human_reviewed_on", "2026-99-99", "human_reviewed_on must be ISO date"),
    ]

    for index, (field_name, field_value, expected_error) in enumerate(cases):
        repo_root = tmp_path / f"case_{index}"
        slug = "technical-methodology"
        payload = _valid_eval_result(slug)
        payload[field_name] = field_value

        _write_valid_eval_support_files(repo_root, slug)

        result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
        _write_json(result_path, payload)

        errors = validator.validate_eval_result(repo_root, slug)

        assert any(expected_error in err for err in errors)


def test_validate_eval_result_rejects_invalid_assertion_counts(tmp_path: Path) -> None:
    cases = [
        ({"passed": 3}, "assertions.passed must equal assertions.total"),
        ({"failed": 1}, "assertions.failed must be 0"),
    ]

    for index, (assertions_patch, expected_error) in enumerate(cases):
        repo_root = tmp_path / f"assertions_{index}"
        slug = "internal-memo"
        payload = _valid_eval_result(slug)
        payload["assertions"].update(assertions_patch)

        _write_valid_eval_support_files(repo_root, slug)

        result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
        _write_json(result_path, payload)

        errors = validator.validate_eval_result(repo_root, slug)

        assert any(expected_error in err for err in errors)


def test_validate_child_plans_complete_requires_completed_date(tmp_path: Path) -> None:
    repo_root = tmp_path

    for child_path in validator.CHILD_PLAN_PATHS.values():
        absolute = repo_root / child_path
        _write_child_plan(absolute, status="completed", completed_date="2026-07-23")

    internal_memo_path = repo_root / validator.CHILD_PLAN_PATHS["internal-memo"]
    _write_child_plan(internal_memo_path, status="completed", completed_date=None)

    errors = validator.validate_child_plans_complete(repo_root)

    assert any("completed-date" in err for err in errors)


def test_validate_child_plans_complete_rejects_wrong_parent_plan(tmp_path: Path) -> None:
    repo_root = tmp_path

    for child_path in validator.CHILD_PLAN_PATHS.values():
        absolute = repo_root / child_path
        _write_child_plan(absolute, status="completed", completed_date="2026-07-23")

    internal_memo_path = repo_root / validator.CHILD_PLAN_PATHS["internal-memo"]
    internal_memo_path.write_text(
        internal_memo_path.read_text(encoding="utf-8").replace(
            validator.PARENT_PLAN_PATH,
            ".cg-docs/plans/other-parent.md",
        ),
        encoding="utf-8",
    )

    errors = validator.validate_child_plans_complete(repo_root)

    assert any("parent-plan must be" in err for err in errors)


def test_validate_child_plans_complete_rejects_non_completed_status(tmp_path: Path) -> None:
    repo_root = tmp_path

    for child_path in validator.CHILD_PLAN_PATHS.values():
        absolute = repo_root / child_path
        _write_child_plan(absolute, status="completed", completed_date="2026-07-23")

    internal_memo_path = repo_root / validator.CHILD_PLAN_PATHS["internal-memo"]
    _write_child_plan(internal_memo_path, status="active", completed_date="2026-07-23")

    errors = validator.validate_child_plans_complete(repo_root)

    assert any("status must be 'completed'" in err for err in errors)


def test_run_validation_all_combines_requested_checks(tmp_path: Path) -> None:
    repo_root = tmp_path

    for slug in validator.DOCUMENT_TYPES:
        source_pack_path = _skill_root(repo_root) / "references" / "source-packs" / f"{slug}.json"
        _write_json(source_pack_path, _valid_source_pack(slug))

        eval_payload = _valid_eval_result(slug)
        _write_valid_eval_support_files(repo_root, slug)
        result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
        _write_json(result_path, eval_payload)

    for child_path in validator.CHILD_PLAN_PATHS.values():
        absolute = repo_root / child_path
        _write_child_plan(absolute, status="completed", completed_date="2026-07-23")

    errors = validator.run_validation(
        repo_root=repo_root,
        slugs=validator.DOCUMENT_TYPES,
        require_approved=True,
        require_eval_pass=True,
        require_child_plans_complete=True,
        require_parent_execution_report_link=False,
    )

    assert errors == []


def test_main_defaults_repo_root_from_script_location(tmp_path: Path, monkeypatch) -> None:
    recorded: dict[str, Path | list[str]] = {}

    def _fake_run_validation(repo_root, slugs, **kwargs):
        recorded["repo_root"] = repo_root
        recorded["slugs"] = list(slugs)
        recorded["kwargs"] = kwargs
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(validator, "run_validation", _fake_run_validation)

    exit_code = validator.main(["--type", "policy-brief"])

    assert exit_code == 0
    assert recorded["repo_root"] == Path(__file__).resolve().parents[2]
    assert recorded["slugs"] == ["policy-brief"]
    assert recorded["kwargs"] == {
        "require_approved": True,
        "require_eval_pass": False,
        "require_child_plans_complete": False,
        "require_parent_execution_report_link": False,
    }


def test_main_rejects_invalid_root(capsys, tmp_path: Path) -> None:
    missing_root = tmp_path / "missing"

    exit_code = validator.main(["--type", "policy-brief", "--root", str(missing_root)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Repository root does not exist" in captured.err


def test_validate_eval_result_rejects_malformed_companion_payloads(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_eval_result(slug)
    _write_valid_eval_support_files(repo_root, slug)

    grading_path = _skill_root(repo_root) / "evals" / "grades" / f"{slug}.grading.json"
    malformed_grading = {
        "schema_version": 1,
        "document_type": slug,
        "pass_threshold": 1,
        "criteria": [
            {"id": "numeric_fidelity", "required": True},
        ],
    }
    _write_json(grading_path, malformed_grading)

    result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
    _write_json(result_path, payload)

    errors = validator.validate_eval_result(repo_root, slug)

    assert any("grading criteria must include required guardrails" in err for err in errors)


def test_validate_eval_result_rejects_optional_required_guardrail(tmp_path: Path) -> None:
    repo_root = tmp_path
    slug = "policy-brief"
    payload = _valid_eval_result(slug)
    _write_valid_eval_support_files(repo_root, slug)

    grading_path = _skill_root(repo_root) / "evals" / "grades" / f"{slug}.grading.json"
    grading_payload = json.loads(grading_path.read_text(encoding="utf-8"))
    grading_payload["criteria"][0]["required"] = False
    _write_json(grading_path, grading_payload)

    result_path = _skill_root(repo_root) / "evals" / "results" / f"{slug}.json"
    _write_json(result_path, payload)

    errors = validator.validate_eval_result(repo_root, slug)

    assert any("required must be true for required guardrail" in err for err in errors)


def test_validate_parent_execution_report_link_passes_for_consistent_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    report_rel = ".cg-docs/work-reports/wb-report.md"
    _write_parent_plan_with_execution_report(repo_root, report_rel)
    _write_execution_report(
        repo_root / report_rel,
        validator.PARENT_PLAN_PATH,
        status="completed",
    )

    errors = validator.validate_parent_execution_report_link(repo_root)

    assert errors == []


def test_validate_parent_execution_report_link_rejects_mismatched_plan(tmp_path: Path) -> None:
    repo_root = tmp_path
    report_rel = ".cg-docs/work-reports/wb-report.md"
    _write_parent_plan_with_execution_report(repo_root, report_rel)
    _write_execution_report(
        repo_root / report_rel,
        ".cg-docs/plans/other-parent.md",
        status="completed",
    )

    errors = validator.validate_parent_execution_report_link(repo_root)

    assert any("execution-report frontmatter plan must be" in err for err in errors)


def test_validate_parent_execution_report_link_rejects_non_completed_status(tmp_path: Path) -> None:
    repo_root = tmp_path
    report_rel = ".cg-docs/work-reports/wb-report.md"
    _write_parent_plan_with_execution_report(repo_root, report_rel)
    _write_execution_report(
        repo_root / report_rel,
        validator.PARENT_PLAN_PATH,
        status="active",
    )

    errors = validator.validate_parent_execution_report_link(repo_root)

    assert any("execution-report status must be 'completed'" in err for err in errors)


def test_run_validation_includes_parent_execution_report_link_gate(tmp_path: Path) -> None:
    repo_root = tmp_path
    report_rel = ".cg-docs/work-reports/wb-report.md"
    _write_parent_plan_with_execution_report(repo_root, report_rel)
    _write_execution_report(
        repo_root / report_rel,
        validator.PARENT_PLAN_PATH,
        status="completed",
    )

    errors = validator.run_validation(
        repo_root=repo_root,
        slugs=["policy-brief"],
        require_approved=False,
        require_eval_pass=False,
        require_child_plans_complete=False,
        require_parent_execution_report_link=True,
    )

    assert errors == []
