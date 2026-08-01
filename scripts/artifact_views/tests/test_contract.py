"""Contract tests for version 1 Brainstorm and Plan artifacts."""
from __future__ import annotations

from pathlib import Path
import re

from artifact_views.schema import (
    ARTIFACT_SCHEMA_VERSION,
    BLOCK_GRAMMAR,
    BRAINSTORM_SCOPES,
    BRAINSTORM_SCHEMA,
    BRAINSTORM_STATUSES,
    DEVIATION_POLICIES,
    INLINE_GRAMMAR,
    PLAN_INVARIANTS,
    PLAN_SCOPES,
    PLAN_SCHEMA,
    PLAN_STATUSES,
    STATUS_METADATA_COMMENT,
    ArtifactKind,
    SchemaSupport,
    is_non_substantive_metadata,
    schema_for,
    schema_support,
)

FIXTURES = Path(__file__).parent / "fixtures"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def test_contract_defines_version_one_for_both_artifact_types() -> None:
    assert ARTIFACT_SCHEMA_VERSION == 1
    assert BRAINSTORM_SCHEMA.version == 1
    assert BRAINSTORM_SCHEMA.kind is ArtifactKind.BRAINSTORM
    assert PLAN_SCHEMA.version == 1
    assert PLAN_SCHEMA.kind is ArtifactKind.PLAN
    assert schema_for(ArtifactKind.BRAINSTORM) is BRAINSTORM_SCHEMA
    assert schema_for(ArtifactKind.PLAN) is PLAN_SCHEMA


def test_brainstorm_contract_requires_identity_and_decision_sections() -> None:
    assert BRAINSTORM_SCHEMA.required_frontmatter == (
        "artifact-schema-version",
        "date",
        "title",
        "status",
        "scope",
    )
    assert BRAINSTORM_SCHEMA.required_sections == (
        "Context",
        "Requirements",
        "Approaches Considered",
        "Decision",
        "Next Steps",
    )


def test_plan_contract_requires_execution_and_completion_sections() -> None:
    assert PLAN_SCHEMA.required_frontmatter == (
        "artifact-schema-version",
        "date",
        "title",
        "status",
        "scope",
        "deviation-policy",
    )
    assert PLAN_SCHEMA.required_sections == (
        "Objective",
        "Context",
        "Requirements",
        "Testing Strategy",
        "Documentation Checklist",
        "Risks & Mitigations",
        "Out of Scope",
        "Completion Contract",
    )
    assert PLAN_SCHEMA.required_completion_sections == (
        "Outcome",
        "Verification Surface",
        "Constraints",
        "Boundaries",
        "Iteration Policy",
        "Blocked-Stop Conditions",
    )


def test_contract_closes_the_block_grammar() -> None:
    assert BLOCK_GRAMMAR == (
        "atx_heading",
        "paragraph",
        "blank_line",
        "ordered_list",
        "unordered_list",
        "task_list",
        "pipe_table",
        "fenced_code",
        "blockquote",
        "thematic_break",
        "raw_html",
    )


def test_contract_closes_the_inline_grammar() -> None:
    assert INLINE_GRAMMAR == (
        "literal_text",
        "backslash_escape",
        "emphasis",
        "strong_emphasis",
        "code_span",
        "link",
        "autolink",
        "hard_line_break",
        "soft_line_break",
    )


def test_standard_and_deep_plan_invariants_are_executable_vocabulary() -> None:
    assert PLAN_INVARIANTS == (
        "unique_requirement_ids",
        "unique_verification_ids",
        "unique_constraint_ids",
        "globally_unique_consecutive_steps",
        "unique_consecutive_phases",
        "one_phase_owner_per_phased_step",
        "declared_requirement_mappings",
        "complete_requirement_coverage",
        "declared_verification_phase_mappings",
        "required_verification_evidence",
    )


def test_schema_version_support_is_explicit() -> None:
    assert schema_support(1) is SchemaSupport.STRICT
    assert schema_support("1") is SchemaSupport.STRICT
    assert schema_support(None) is SchemaSupport.COMPATIBLE_LEGACY
    assert schema_support(2) is SchemaSupport.UNSUPPORTED
    assert schema_support("future") is SchemaSupport.UNSUPPORTED
    assert schema_support(True) is SchemaSupport.UNSUPPORTED


def test_only_the_exact_status_comment_is_non_substantive() -> None:
    assert STATUS_METADATA_COMMENT == (
        "<!-- Valid status values: decided, in-progress, abandoned -->"
    )
    assert is_non_substantive_metadata(STATUS_METADATA_COMMENT)
    assert not is_non_substantive_metadata(
        "<!-- Valid status values: decided, in-progress -->"
    )
    assert not is_non_substantive_metadata(f" {STATUS_METADATA_COMMENT}")
    assert not is_non_substantive_metadata("<div>source content</div>")


def test_contract_fixture_matrix_is_present() -> None:
    expected = {
        "strict_brainstorm.md",
        "strict_plan.md",
        "strict_deep_plan.md",
        "unknown_version.md",
        "duplicate_ids.md",
        "orphan_mapping.md",
        "malformed_completion_table.md",
        "ambiguous_heading.md",
        "unclosed_fence.md",
    }
    assert {path.name for path in FIXTURES.glob("*.md")} >= expected


def test_documented_state_vocabularies_match_executable_contract() -> None:
    brainstorm_prompt = (
        REPOSITORY_ROOT / ".github/prompts/cg-brainstorm.prompt.md"
    ).read_text(encoding="utf-8")
    plan_prompt = (
        REPOSITORY_ROOT / ".github/prompts/cg-plan.prompt.md"
    ).read_text(encoding="utf-8")
    goal_contract = (
        REPOSITORY_ROOT / ".github/shared/goal-execution.contract.md"
    ).read_text(encoding="utf-8")
    workflow_docs = (REPOSITORY_ROOT / "docs/workflow.md").read_text(encoding="utf-8")

    status_match = re.search(
        r"<!-- Valid status values: (.+?) -->",
        brainstorm_prompt,
    )
    assert status_match is not None
    documented_brainstorm_statuses = {
        value.strip() for value in status_match.group(1).split(",")
    }
    scope_match = re.search(r'scope: "<([^>]+)>"', brainstorm_prompt)
    assert scope_match is not None
    documented_brainstorm_scopes = set(scope_match.group(1).split("|"))
    plan_scope_match = re.search(r'scope: "<(Lightweight\|Standard\|Deep)>"', plan_prompt)
    deviation_match = re.search(r'deviation-policy: "<([^>]+)>"', plan_prompt)
    assert plan_scope_match is not None and deviation_match is not None
    documented_deviations = set(deviation_match.group(1).split("|"))
    contract_deviations = set(
        re.findall(r"(?m)^\| `(ask|autonomous|strict)` \|", goal_contract)
    )
    plan_status_match = re.search(
        r"Plan `status` values are exactly: ([^\n]+)",
        workflow_docs,
    )
    assert plan_status_match is not None
    documented_plan_statuses = set(re.findall(r"`([^`]+)`", plan_status_match.group(1)))

    assert documented_brainstorm_statuses == set(BRAINSTORM_STATUSES)
    assert documented_brainstorm_scopes == set(BRAINSTORM_SCOPES)
    assert set(plan_scope_match.group(1).split("|")) == set(PLAN_SCOPES)
    assert documented_deviations == set(DEVIATION_POLICIES)
    assert contract_deviations == set(DEVIATION_POLICIES)
    assert documented_plan_statuses == set(PLAN_STATUSES)
