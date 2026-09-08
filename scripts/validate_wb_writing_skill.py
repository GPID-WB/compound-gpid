#!/usr/bin/env python3
"""Validate fixed evidence artifacts for cg-skill-wb-report-writing.

This validator supports deterministic checks required by the parent/child plan
contracts for the World Bank institutional report-writing skill.

Examples:
    python scripts/validate_wb_writing_skill.py --type policy-brief --require-approved
    python scripts/validate_wb_writing_skill.py --type policy-brief --require-eval-pass
    python scripts/validate_wb_writing_skill.py --all --require-child-plans-complete --require-eval-pass
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PARENT_PLAN_PATH = ".cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md"
DEFAULT_SKILL_ROOT = Path(".github/skills/cg-skill-wb-report-writing")


def _resolve_skill_root(root: Path = Path(".")) -> Path:
    """Resolve the wb-report-writing skill directory namespace-agnostically.

    Prefers the skill directory owned by the ``cap-wb-report-writing`` module in
    the module registry; falls back to the legacy ``cg-skill-wb-report-writing``
    path so pre-registry setups keep working.
    """
    registry_path = root / ".github" / "shared" / "module-registry.json"
    if registry_path.exists():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            for module in registry.get("modules", []):
                if not isinstance(module, dict) or module.get("id") != "cap-wb-report-writing":
                    continue
                for pattern in module.get("ownedAssets", []):
                    if not isinstance(pattern, str) or "wb-report-writing" not in pattern:
                        continue
                    normalized = pattern.rstrip("/")
                    if not normalized.endswith("SKILL.md"):
                        normalized = f"{normalized}/SKILL.md"
                    candidate = root / normalized
                    if candidate.is_file():
                        return candidate.parent
        except (OSError, json.JSONDecodeError):
            pass
    return DEFAULT_SKILL_ROOT


SKILL_ROOT = _resolve_skill_root()
SOURCE_PACK_DIR = SKILL_ROOT / "references" / "source-packs"
EVAL_RESULTS_DIR = SKILL_ROOT / "evals" / "results"

DOCUMENT_TYPES: tuple[str, ...] = (
    "policy-research-working-paper",
    "policy-brief",
    "executive-summary",
    "flagship-report-section",
    "country-analytical-narrative",
    "technical-methodology",
    "internal-memo",
    "data-blog-post",
)

CHILD_PLAN_PATHS: dict[str, str] = {
    "policy-research-working-paper": ".cg-docs/plans/2026-07-23-wb-report-writing-prwp.md",
    "policy-brief": ".cg-docs/plans/2026-07-23-wb-report-writing-policy-brief.md",
    "executive-summary": ".cg-docs/plans/2026-07-23-wb-report-writing-executive-summary.md",
    "flagship-report-section": ".cg-docs/plans/2026-07-23-wb-report-writing-flagship-section.md",
    "country-analytical-narrative": ".cg-docs/plans/2026-07-23-wb-report-writing-country-regional.md",
    "technical-methodology": ".cg-docs/plans/2026-07-23-wb-report-writing-technical-methodology.md",
    "internal-memo": ".cg-docs/plans/2026-07-23-wb-report-writing-internal-memo.md",
    "data-blog-post": ".cg-docs/plans/2026-07-23-wb-report-writing-data-blog.md",
}

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TERMINOLOGY_STATUSES = {"approved", "unresolved"}
DISCLAIMER_REQUIREMENTS = {"required", "not-required"}
REQUIRED_GUARDRAILS = (
    "numeric_fidelity",
    "citation_integrity",
    "institutional_position",
    "data_status_propagation",
    "country_sensitivity",
    "type_specific_checks",
)


def _is_non_empty_string(value: object) -> bool:
    """Return True when value is a non-empty string after trimming."""
    return isinstance(value, str) and bool(value.strip())


def _is_iso_date(value: object) -> bool:
    """Return True when value is a valid YYYY-MM-DD calendar date."""
    if not isinstance(value, str):
        return False

    stripped = value.strip()
    if not ISO_DATE_RE.match(stripped):
        return False

    try:
        date.fromisoformat(stripped)
    except ValueError:
        return False

    return True


def _is_http_url(value: str) -> bool:
    """Return True for http(s) URLs with a network location."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_placeholder_host(value: str) -> bool:
    """Return True when URL host is a known placeholder domain."""
    parsed = urlparse(value)
    host = (parsed.netloc or "").lower()
    return host == "example.org" or host.endswith(".example.org")


def _load_json(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Load JSON and return either parsed dict or validation errors."""
    if not path.exists():
        return None, [f"{label}: file not found at {path.as_posix()}"]

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label}: invalid JSON ({exc})"]

    if not isinstance(payload, dict):
        return None, [f"{label}: top-level JSON must be an object"]

    return payload, []


def _resolve_repo_path(
    repo_root: Path,
    raw_value: object,
    field_name: str,
    *,
    require_exists: bool,
) -> tuple[Path | None, list[str]]:
    """Resolve and validate a repo-relative path.

    Rejects absolute paths, path traversal, and paths that escape repository root.
    """
    errors: list[str] = []
    if not _is_non_empty_string(raw_value):
        return None, [f"{field_name}: must be a non-empty string path"]

    value = str(raw_value).strip()
    if _is_http_url(value):
        return None, [f"{field_name}: URL is not allowed for this field"]

    rel_path = Path(value)
    if rel_path.is_absolute() or rel_path.drive:
        errors.append(f"{field_name}: absolute paths are not allowed ({value})")
        return None, errors

    if ".." in rel_path.parts:
        errors.append(
            f"{field_name}: path resolves outside repository root ({value})"
        )
        return None, errors

    repo_root_resolved = repo_root.resolve()
    resolved = (repo_root / rel_path).resolve()
    try:
        resolved.relative_to(repo_root_resolved)
    except ValueError:
        errors.append(f"{field_name}: path resolves outside repository root ({value})")
        return None, errors

    if require_exists:
        if not resolved.exists():
            errors.append(f"{field_name}: referenced path does not exist ({value})")
        elif not resolved.is_file():
            errors.append(f"{field_name}: referenced path must be a file ({value})")

    return resolved, errors


def _validate_url_or_repo_path(
    repo_root: Path,
    raw_value: object,
    field_name: str,
) -> list[str]:
    """Validate a value as either a stable URL or an existing repo path."""
    if not _is_non_empty_string(raw_value):
        return [f"{field_name}: must be a non-empty string"]

    value = str(raw_value).strip()
    if _is_http_url(value):
        if _is_placeholder_host(value):
            return [
                f"{field_name}: placeholder host 'example.org' is not allowed"
            ]
        return []

    _, errors = _resolve_repo_path(
        repo_root,
        value,
        field_name,
        require_exists=True,
    )
    return errors


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Parse simple YAML frontmatter key-value pairs from a markdown file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"') and len(value) >= 2:
            value = value[1:-1]
        if value.startswith("'") and value.endswith("'") and len(value) >= 2:
            value = value[1:-1]
        data[key] = value

    return data


def _validate_slug(slug: str) -> list[str]:
    """Return unknown-slug error if slug is not part of the fixed contract."""
    if slug not in DOCUMENT_TYPES:
        allowed = ", ".join(DOCUMENT_TYPES)
        return [f"Unknown document type slug '{slug}'. Allowed: {allowed}"]
    return []


def validate_source_pack(repo_root: Path, slug: str) -> list[str]:
    """Validate source-pack JSON for a single document type."""
    errors = _validate_slug(slug)
    if errors:
        return errors

    source_pack_path = repo_root / SOURCE_PACK_DIR / f"{slug}.json"
    payload, load_errors = _load_json(source_pack_path, f"source-pack {slug}")
    if load_errors:
        return load_errors
    assert payload is not None

    if payload.get("schema_version") != 1:
        errors.append("source-pack schema_version must be 1")

    if payload.get("document_type") != slug:
        errors.append(
            f"source-pack document_type must be '{slug}', found '{payload.get('document_type')}'"
        )

    status = payload.get("status")
    if status != "approved":
        errors.append(
            f"source-pack status must be 'approved', found '{status}'"
        )

    if not _is_non_empty_string(payload.get("approved_by")):
        errors.append("source-pack approved_by must be a non-empty reviewer identity")

    if not _is_iso_date(payload.get("approved_on")):
        errors.append("source-pack approved_on must be ISO date YYYY-MM-DD")

    if not _is_non_empty_string(payload.get("intended_audience")):
        errors.append("source-pack intended_audience must be a non-empty string")

    disclaimer_requirement = payload.get("disclaimer_requirement")
    if disclaimer_requirement not in DISCLAIMER_REQUIREMENTS:
        errors.append(
            "source-pack disclaimer_requirement must be 'required' or 'not-required'"
        )

    required_disclaimers = payload.get("required_disclaimers")
    if not isinstance(required_disclaimers, list):
        errors.append("source-pack required_disclaimers must be a list")
        required_disclaimers = []

    if disclaimer_requirement == "required" and len(required_disclaimers) < 1:
        errors.append(
            "source-pack disclaimer_requirement=required requires at least one disclaimer"
        )

    for index, disclaimer in enumerate(required_disclaimers):
        if not _is_non_empty_string(disclaimer):
            errors.append(
                f"source-pack required_disclaimers[{index}] must be a non-empty string"
            )

    terminology_status = payload.get("terminology_status")
    if terminology_status not in TERMINOLOGY_STATUSES:
        errors.append(
            "source-pack terminology_status must be 'approved' or 'unresolved'"
        )

    terminology_sources = payload.get("terminology_sources")
    if not isinstance(terminology_sources, list):
        errors.append("source-pack terminology_sources must be a list")
        terminology_sources = []

    if terminology_status == "approved" and len(terminology_sources) < 1:
        errors.append(
            "source-pack terminology_status=approved requires at least one terminology source"
        )

    for index, source in enumerate(terminology_sources):
        errors.extend(
            _validate_url_or_repo_path(
                repo_root,
                source,
                f"source-pack terminology_sources[{index}]",
            )
        )

    exemplars = payload.get("exemplars")
    if not isinstance(exemplars, list):
        errors.append("source-pack exemplars must be a list")
        exemplars = []

    if len(exemplars) not in {2, 3}:
        errors.append("source-pack exemplars must contain exactly 2 or 3 records")

    for index, exemplar in enumerate(exemplars):
        prefix = f"source-pack exemplars[{index}]"
        if not isinstance(exemplar, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        if not _is_non_empty_string(exemplar.get("title")):
            errors.append(f"{prefix}.title must be a non-empty string")

        errors.extend(
            _validate_url_or_repo_path(
                repo_root,
                exemplar.get("source"),
                f"{prefix}.source",
            )
        )

        if not _is_iso_date(exemplar.get("retrieved_on")):
            errors.append(f"{prefix}.retrieved_on must be ISO date YYYY-MM-DD")

        relevant_sections = exemplar.get("relevant_sections")
        if not isinstance(relevant_sections, list) or len(relevant_sections) == 0:
            errors.append(f"{prefix}.relevant_sections must be a non-empty list")
        else:
            for section_index, section in enumerate(relevant_sections):
                if not _is_non_empty_string(section):
                    errors.append(
                        f"{prefix}.relevant_sections[{section_index}] must be non-empty"
                    )

        if not _is_non_empty_string(exemplar.get("authority_rationale")):
            errors.append(f"{prefix}.authority_rationale must be a non-empty string")

    return errors


def validate_eval_result(repo_root: Path, slug: str) -> list[str]:
    """Validate eval result JSON for a single document type."""
    errors = _validate_slug(slug)
    if errors:
        return errors

    result_path = repo_root / EVAL_RESULTS_DIR / f"{slug}.json"
    payload, load_errors = _load_json(result_path, f"eval-result {slug}")
    if load_errors:
        return load_errors
    assert payload is not None

    if payload.get("schema_version") != 1:
        errors.append("eval-result schema_version must be 1")

    if payload.get("document_type") != slug:
        errors.append(
            f"eval-result document_type must be '{slug}', found '{payload.get('document_type')}'"
        )

    status = payload.get("status")
    if status != "accepted":
        errors.append(f"eval-result status must be 'accepted', found '{status}'")

    expected_eval_definition = f"{SKILL_ROOT.as_posix()}/evals/types/{slug}.json"
    expected_benchmark = f"{SKILL_ROOT.as_posix()}/evals/benchmarks/{slug}.benchmark.json"
    expected_grading = f"{SKILL_ROOT.as_posix()}/evals/grades/{slug}.grading.json"
    expected_feedback = f"{SKILL_ROOT.as_posix()}/evals/feedback/{slug}.feedback.json"
    eval_definition = payload.get("eval_definition")
    if eval_definition != expected_eval_definition:
        errors.append(
            "eval-result eval_definition must match "
            f"{expected_eval_definition}"
        )

    if payload.get("benchmark") != expected_benchmark:
        errors.append(
            "eval-result benchmark must match "
            f"{expected_benchmark}"
        )

    if payload.get("grading") != expected_grading:
        errors.append(
            "eval-result grading must match "
            f"{expected_grading}"
        )

    if payload.get("feedback") != expected_feedback:
        errors.append(
            "eval-result feedback must match "
            f"{expected_feedback}"
        )

    resolved_paths: dict[str, Path] = {}
    for field_name in ("eval_definition", "benchmark", "grading", "feedback"):
        resolved_path, path_errors = _resolve_repo_path(
            repo_root,
            payload.get(field_name),
            f"eval-result {field_name}",
            require_exists=True,
        )
        errors.extend(path_errors)
        if resolved_path is not None and not path_errors:
            resolved_paths[field_name] = resolved_path

    for field_name, resolved_path in resolved_paths.items():
        companion_payload, companion_errors = _load_json(
            resolved_path,
            f"eval-result {field_name}",
        )
        if companion_errors:
            errors.extend(companion_errors)
            continue
        assert companion_payload is not None

        if companion_payload.get("schema_version") != 1:
            errors.append(
                f"eval-result {field_name} schema_version must be 1"
            )

        if companion_payload.get("document_type") != slug:
            errors.append(
                f"eval-result {field_name} document_type must be '{slug}'"
            )

        if field_name == "eval_definition":
            operation_coverage = companion_payload.get("operation_coverage")
            if not isinstance(operation_coverage, list) or len(operation_coverage) == 0:
                errors.append(
                    "eval-result eval_definition operation_coverage must be a non-empty list"
                )
            else:
                for index, operation in enumerate(operation_coverage):
                    if not _is_non_empty_string(operation):
                        errors.append(
                            "eval-result eval_definition operation_coverage"
                            f"[{index}] must be a non-empty string"
                        )

        if field_name == "benchmark":
            if not _is_non_empty_string(companion_payload.get("baseline")):
                errors.append(
                    "eval-result benchmark baseline must be a non-empty string"
                )
            if not _is_non_empty_string(companion_payload.get("comparison")):
                errors.append(
                    "eval-result benchmark comparison must be a non-empty string"
                )

            required_checks = companion_payload.get("required_checks")
            if not isinstance(required_checks, list) or len(required_checks) == 0:
                errors.append(
                    "eval-result benchmark required_checks must be a non-empty list"
                )
            else:
                for index, check_name in enumerate(required_checks):
                    if not _is_non_empty_string(check_name):
                        errors.append(
                            "eval-result benchmark required_checks"
                            f"[{index}] must be a non-empty string"
                        )

        if field_name == "grading":
            pass_threshold = companion_payload.get("pass_threshold")
            if not isinstance(pass_threshold, int) or pass_threshold <= 0:
                errors.append(
                    "eval-result grading pass_threshold must be a positive integer"
                )

            criteria = companion_payload.get("criteria")
            if not isinstance(criteria, list) or len(criteria) == 0:
                errors.append(
                    "eval-result grading criteria must be a non-empty list"
                )
            else:
                criteria_ids: set[str] = set()
                for index, criterion in enumerate(criteria):
                    prefix = f"eval-result grading criteria[{index}]"
                    if not isinstance(criterion, dict):
                        errors.append(f"{prefix} must be an object")
                        continue

                    criterion_id = criterion.get("id")
                    if not _is_non_empty_string(criterion_id):
                        errors.append(f"{prefix}.id must be a non-empty string")
                    else:
                        criteria_ids.add(str(criterion_id).strip())

                    required_value = criterion.get("required")
                    if not isinstance(required_value, bool):
                        errors.append(f"{prefix}.required must be a boolean")
                    elif (
                        _is_non_empty_string(criterion_id)
                        and str(criterion_id).strip() in REQUIRED_GUARDRAILS
                        and required_value is not True
                    ):
                        errors.append(
                            f"{prefix}.required must be true for required guardrail"
                        )

                missing_guardrails = [
                    key for key in REQUIRED_GUARDRAILS if key not in criteria_ids
                ]
                if missing_guardrails:
                    errors.append(
                        "eval-result grading criteria must include required guardrails: "
                        + ", ".join(missing_guardrails)
                    )

        if field_name == "feedback":
            if not _is_non_empty_string(companion_payload.get("summary")):
                errors.append(
                    "eval-result feedback summary must be a non-empty string"
                )

            reviewer_notes = companion_payload.get("reviewer_notes")
            if not isinstance(reviewer_notes, list) or len(reviewer_notes) == 0:
                errors.append(
                    "eval-result feedback reviewer_notes must be a non-empty list"
                )
            else:
                for index, note in enumerate(reviewer_notes):
                    if not _is_non_empty_string(note):
                        errors.append(
                            "eval-result feedback reviewer_notes"
                            f"[{index}] must be a non-empty string"
                        )

    assertions = payload.get("assertions")
    if not isinstance(assertions, dict):
        errors.append("eval-result assertions must be an object")
    else:
        total = assertions.get("total")
        passed = assertions.get("passed")
        failed = assertions.get("failed")

        if not isinstance(total, int) or total <= 0:
            errors.append("eval-result assertions.total must be a positive integer")
        if not isinstance(passed, int):
            errors.append("eval-result assertions.passed must be an integer")
        if not isinstance(failed, int):
            errors.append("eval-result assertions.failed must be an integer")

        if isinstance(total, int) and isinstance(passed, int) and passed != total:
            errors.append("eval-result assertions.passed must equal assertions.total")
        if failed != 0:
            errors.append("eval-result assertions.failed must be 0")

    guardrails = payload.get("guardrails")
    if not isinstance(guardrails, dict):
        errors.append("eval-result guardrails must be an object")
    else:
        for key in REQUIRED_GUARDRAILS:
            value = guardrails.get(key)
            if value is not True:
                errors.append(f"eval-result guardrails.{key} must be true")

    if payload.get("human_accepted") is not True:
        errors.append("eval-result human_accepted must be true")

    if not _is_non_empty_string(payload.get("human_reviewer")):
        errors.append("eval-result human_reviewer must be a non-empty reviewer identity")

    if not _is_iso_date(payload.get("human_reviewed_on")):
        errors.append("eval-result human_reviewed_on must be ISO date YYYY-MM-DD")

    return errors


def validate_child_plans_complete(repo_root: Path) -> list[str]:
    """Validate that all child plans are completed and linked to this parent plan."""
    errors: list[str] = []
    for slug, rel_path in CHILD_PLAN_PATHS.items():
        absolute = repo_root / rel_path
        if not absolute.exists():
            errors.append(f"child-plan {slug}: file not found at {rel_path}")
            continue

        frontmatter = _parse_frontmatter(absolute)
        parent_plan = frontmatter.get("parent-plan", "")
        status = frontmatter.get("status", "")
        completed_date = frontmatter.get("completed-date", "")

        if parent_plan != PARENT_PLAN_PATH:
            errors.append(
                f"child-plan {slug}: parent-plan must be '{PARENT_PLAN_PATH}'"
            )

        if status != "completed":
            errors.append(f"child-plan {slug}: status must be 'completed'")

        if not _is_iso_date(completed_date):
            errors.append(
                f"child-plan {slug}: completed-date must be ISO date YYYY-MM-DD"
            )

    return errors


def validate_parent_execution_report_link(repo_root: Path) -> list[str]:
    """Validate parent-plan execution-report linkage and reciprocal metadata."""
    errors: list[str] = []
    parent_plan_path = repo_root / PARENT_PLAN_PATH
    if not parent_plan_path.exists():
        return [f"parent-plan file not found at {PARENT_PLAN_PATH}"]

    parent_frontmatter = _parse_frontmatter(parent_plan_path)
    execution_report_value = parent_frontmatter.get("execution-report", "")
    resolved_report_path, path_errors = _resolve_repo_path(
        repo_root,
        execution_report_value,
        "parent-plan execution-report",
        require_exists=True,
    )
    if path_errors:
        errors.extend(path_errors)
        return errors
    assert resolved_report_path is not None

    report_frontmatter = _parse_frontmatter(resolved_report_path)
    expected_report_plan = PARENT_PLAN_PATH
    observed_report_plan = report_frontmatter.get("plan", "")
    if observed_report_plan != expected_report_plan:
        errors.append(
            "execution-report frontmatter plan must be "
            f"'{expected_report_plan}'"
        )

    status = report_frontmatter.get("status", "")
    if status != "completed":
        errors.append("execution-report status must be 'completed'")

    report_rel = resolved_report_path.relative_to(repo_root).as_posix()
    if execution_report_value.strip() != report_rel:
        errors.append(
            "parent-plan execution-report path must be normalized repo-relative "
            f"'{report_rel}'"
        )

    return errors


def run_validation(
    repo_root: Path,
    slugs: list[str] | tuple[str, ...],
    *,
    require_approved: bool,
    require_eval_pass: bool,
    require_child_plans_complete: bool,
    require_parent_execution_report_link: bool,
) -> list[str]:
    """Run selected validations and return collected errors."""
    errors: list[str] = []
    for slug in slugs:
        slug_errors = _validate_slug(slug)
        if slug_errors:
            errors.extend(slug_errors)
            continue

        if require_approved:
            errors.extend(validate_source_pack(repo_root, slug))

        if require_eval_pass:
            errors.extend(validate_eval_result(repo_root, slug))

    if require_child_plans_complete:
        errors.extend(validate_child_plans_complete(repo_root))

    if require_parent_execution_report_link:
        errors.extend(validate_parent_execution_report_link(repo_root))

    return errors


def build_parser() -> argparse.ArgumentParser:
    """Build command line parser for the validator."""
    parser = argparse.ArgumentParser(
        description="Validate cg-skill-wb-report-writing source packs, evals, and child plan completion."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--type",
        dest="document_type",
        metavar="SLUG",
        help="Validate one document type slug.",
    )
    mode.add_argument(
        "--all",
        action="store_true",
        help="Validate all configured document types.",
    )

    parser.add_argument(
        "--require-approved",
        action="store_true",
        help="Require approved source-pack checks.",
    )
    parser.add_argument(
        "--require-eval-pass",
        action="store_true",
        help="Require accepted eval-result checks.",
    )
    parser.add_argument(
        "--require-child-plans-complete",
        action="store_true",
        help="Require all child plans completed with parent linkage.",
    )
    parser.add_argument(
        "--require-parent-report-link",
        action="store_true",
        help="Require parent plan execution-report linkage and reciprocal report metadata.",
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent.parent),
        help="Repository root path (default: repository root derived from this script).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run validation CLI and return process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        sys.stderr.write(f"Repository root does not exist: {repo_root}\n")
        return 2

    slugs: list[str] | tuple[str, ...]
    if args.all:
        slugs = DOCUMENT_TYPES
    else:
        slugs = [args.document_type]

    require_approved = args.require_approved
    require_eval_pass = args.require_eval_pass
    require_child_plans_complete = args.require_child_plans_complete
    require_parent_execution_report_link = args.require_parent_report_link

    if not (
        require_approved
        or require_eval_pass
        or require_child_plans_complete
        or require_parent_execution_report_link
    ):
        require_approved = True

    errors = run_validation(
        repo_root=repo_root,
        slugs=slugs,
        require_approved=require_approved,
        require_eval_pass=require_eval_pass,
        require_child_plans_complete=require_child_plans_complete,
        require_parent_execution_report_link=require_parent_execution_report_link,
    )

    if errors:
        for error in errors:
            sys.stderr.write(f"{error}\n")
        return 1

    selected = ", ".join(slugs)
    sys.stdout.write(f"Validation passed for: {selected}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
