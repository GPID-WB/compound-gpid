"""Tests for renderer-independent artifact validation."""
from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import pytest

from artifact_views.errors import (
    ArtifactParseError,
    ArtifactReadError,
    ArtifactValidationError,
)
from artifact_views.schema import ArtifactKind
from artifact_views.validator import MAX_VALIDATION_ERRORS, validate_path, validate_source

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _validation_messages(error: ArtifactValidationError) -> str:
    return "\n".join(item.message for item in error.errors)


@pytest.mark.parametrize(
    ("fixture_name", "kind"),
    (
        ("strict_brainstorm.md", ArtifactKind.BRAINSTORM),
        ("strict_plan.md", ArtifactKind.PLAN),
        ("strict_deep_plan.md", ArtifactKind.PLAN),
    ),
)
def test_strict_fixtures_validate(fixture_name: str, kind: ArtifactKind) -> None:
    document = validate_source(
        _fixture(fixture_name),
        Path(f".cg-docs/{kind.value}s/{fixture_name}"),
        kind,
    )
    assert document.identity.kind is kind


def test_compatible_legacy_plan_validates_when_unambiguous() -> None:
    source = _fixture("strict_plan.md").replace(
        "artifact-schema-version: 1\n",
        "",
        1,
    )
    document = validate_source(
        source,
        Path(".cg-docs/plans/legacy.md"),
        ArtifactKind.PLAN,
    )
    assert document.identity.schema_version is None


def test_unknown_future_version_fails_with_recovery_guidance() -> None:
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            _fixture("unknown_version.md"),
            Path(".cg-docs/brainstorms/future.md"),
            ArtifactKind.BRAINSTORM,
        )
    rendered = str(caught.value)
    assert "Unsupported artifact schema version 2" in rendered
    assert "renderer that supports version 2" in rendered


def test_duplicate_ids_fail_validation() -> None:
    with pytest.raises(ArtifactValidationError, match="Duplicate requirement ID 'R1'"):
        validate_source(
            _fixture("duplicate_ids.md"),
            Path(".cg-docs/plans/duplicate.md"),
            ArtifactKind.PLAN,
        )


def test_orphan_mapping_and_uncovered_requirement_are_both_reported() -> None:
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            _fixture("orphan_mapping.md"),
            Path(".cg-docs/plans/orphan.md"),
            ArtifactKind.PLAN,
        )
    messages = _validation_messages(caught.value)
    assert "unknown requirement ID 'R2'" in messages
    assert "Requirement 'R1' is not mapped" in messages


def test_malformed_required_verification_table_fails() -> None:
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            _fixture("malformed_completion_table.md"),
            Path(".cg-docs/plans/malformed.md"),
            ArtifactKind.PLAN,
        )
    assert "Command/Artifact" in _validation_messages(caught.value)


def test_repeated_required_heading_is_ambiguous() -> None:
    with pytest.raises(ArtifactValidationError, match="exactly once.*Context"):
        validate_source(
            _fixture("ambiguous_heading.md"),
            Path(".cg-docs/brainstorms/ambiguous.md"),
            ArtifactKind.BRAINSTORM,
        )


def test_unclosed_fence_fails_before_semantic_validation() -> None:
    with pytest.raises(ArtifactParseError, match="Unclosed fenced code block"):
        validate_source(
            _fixture("unclosed_fence.md"),
            Path(".cg-docs/brainstorms/unclosed.md"),
            ArtifactKind.BRAINSTORM,
        )


def test_duplicate_and_unknown_step_mappings_fail() -> None:
    source = _fixture("strict_plan.md").replace(
        "**Requirements**: R1, R2",
        "**Requirements**: R1, R1, R9",
    )
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            source,
            Path(".cg-docs/plans/mappings.md"),
            ArtifactKind.PLAN,
        )
    messages = _validation_messages(caught.value)
    assert "maps requirement 'R1' more than once" in messages
    assert "unknown requirement ID 'R9'" in messages
    assert "Requirement 'R2' is not mapped" in messages


def test_nonconsecutive_steps_and_phases_fail() -> None:
    source = _fixture("strict_deep_plan.md").replace(
        "## Phase 2: Validation",
        "## Phase 3: Validation",
    ).replace(
        "### 2. Validate the schema",
        "### 3. Validate the schema",
    )
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            source,
            Path(".cg-docs/plans/nonconsecutive.md"),
            ArtifactKind.PLAN,
        )
    messages = _validation_messages(caught.value)
    assert "Phase numbers must be consecutive" in messages
    assert "Step numbers must be consecutive" in messages


def test_step_before_first_phase_has_no_valid_phase_owner() -> None:
    source = _fixture("strict_deep_plan.md").replace(
        "## Phase 1: Contract\n\n",
        "",
        1,
    ).replace(
        "## Phase 2: Validation",
        "## Phase 1: Contract\n\n## Phase 2: Validation",
        1,
    )
    with pytest.raises(ArtifactValidationError, match="Step 1 has no phase owner"):
        validate_source(
            source,
            Path(".cg-docs/plans/orphan-step.md"),
            ArtifactKind.PLAN,
        )


def test_required_evidence_and_phase_mapping_must_be_usable() -> None:
    source = _fixture("strict_deep_plan.md").replace(
        "| V1 | 1 | Contract tests pass. | `pytest -q scripts/artifact_views/tests/test_contract.py` | yes |",
        "| V1 | 9 | Contract tests pass. |  | yes |",
    )
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            source,
            Path(".cg-docs/plans/evidence.md"),
            ArtifactKind.PLAN,
        )
    messages = _validation_messages(caught.value)
    assert "unknown phase 9" in messages
    assert "non-empty Command/Artifact" in messages


def test_validation_requires_tests_metadata_for_each_step() -> None:
    source = _fixture("strict_plan.md").replace(
        "- **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`\n",
        "",
    )
    with pytest.raises(ArtifactValidationError, match="Step 1.*Tests metadata"):
        validate_source(
            source,
            Path(".cg-docs/plans/no-tests.md"),
            ArtifactKind.PLAN,
        )


def test_multiline_tests_metadata_is_structurally_usable() -> None:
    source = _fixture("strict_plan.md").replace(
        "- **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`",
        "- **Tests**:\n  - `pytest -q scripts/artifact_views/tests/test_parser.py`",
    )
    document = validate_source(
        source,
        Path(".cg-docs/plans/multiline-tests.md"),
        ArtifactKind.PLAN,
    )
    assert document.tests[0].command.startswith("- `pytest")


def test_lightweight_contract_accepts_outcome_and_verification_only() -> None:
    source = _fixture("strict_plan.md").replace('scope: "Standard"', 'scope: "Lightweight"')
    source = source.split("### Constraints", 1)[0].rstrip() + "\n"

    document = validate_source(
        source,
        Path(".cg-docs/plans/lightweight.md"),
        ArtifactKind.PLAN,
    )

    assert document.frontmatter.get("scope") == "Lightweight"


@pytest.mark.parametrize("scope", ("deep", "Extended", "", 1))
def test_invalid_plan_scope_fails(scope) -> None:
    rendered_scope = str(scope) if not isinstance(scope, str) else scope
    source = _fixture("strict_plan.md").replace('scope: "Standard"', f"scope: {rendered_scope}")

    with pytest.raises(ArtifactValidationError, match="scope"):
        validate_source(
            source,
            Path(".cg-docs/plans/invalid-scope.md"),
            ArtifactKind.PLAN,
        )


@pytest.mark.parametrize(
    ("fixture", "kind", "old", "new", "message"),
    (
        ("strict_brainstorm.md", ArtifactKind.BRAINSTORM, "status: decided", "status: approved", "status"),
        ("strict_brainstorm.md", ArtifactKind.BRAINSTORM, 'scope: "Standard"', "scope: Operational", "scope"),
        ("strict_plan.md", ArtifactKind.PLAN, "status: active", "status: planned", "status"),
        ("strict_plan.md", ArtifactKind.PLAN, 'deviation-policy: "ask"', "deviation-policy: auto", "deviation policy"),
    ),
)
def test_invalid_state_vocabularies_fail(
    fixture: str,
    kind: ArtifactKind,
    old: str,
    new: str,
    message: str,
) -> None:
    source = _fixture(fixture).replace(old, new, 1)

    with pytest.raises(ArtifactValidationError, match=message):
        validate_source(
            source,
            Path(f".cg-docs/{kind.value}s/invalid-state.md"),
            kind,
        )


@pytest.mark.parametrize("value", ("true", "7", "[active]", "null"))
@pytest.mark.parametrize(
    ("fixture", "kind", "field", "valid_value", "message"),
    (
        ("strict_brainstorm.md", ArtifactKind.BRAINSTORM, "status", "decided", "status"),
        ("strict_plan.md", ArtifactKind.PLAN, "status", "active", "status"),
        (
            "strict_plan.md",
            ArtifactKind.PLAN,
            "deviation-policy",
            '"ask"',
            "deviation policy",
        ),
    ),
)
def test_non_string_state_vocabularies_fail(
    value: str,
    fixture: str,
    kind: ArtifactKind,
    field: str,
    valid_value: str,
    message: str,
) -> None:
    source = _fixture(fixture).replace(
        f"{field}: {valid_value}",
        f"{field}: {value}",
        1,
    )

    with pytest.raises(ArtifactValidationError, match=message):
        validate_source(
            source,
            Path(f".cg-docs/{kind.value}s/non-string-state.md"),
            kind,
        )


@pytest.mark.parametrize("required", ("true", "required", "", "YES!"))
def test_invalid_required_value_fails(required: str) -> None:
    source = _fixture("strict_plan.md").replace("| yes |", f"| {required} |", 1)

    with pytest.raises(ArtifactValidationError, match="Required.*yes.*no"):
        validate_source(
            source,
            Path(".cg-docs/plans/invalid-required.md"),
            ArtifactKind.PLAN,
        )


def test_blank_verification_id_is_retained_and_rejected() -> None:
    source = _fixture("strict_plan.md").replace("| V1 | Parser tests pass.", "|  | Parser tests pass.")

    with pytest.raises(ArtifactValidationError, match="verification ID"):
        validate_source(
            source,
            Path(".cg-docs/plans/blank-verification-id.md"),
            ArtifactKind.PLAN,
        )


def test_fenced_examples_cannot_satisfy_step_metadata() -> None:
    source = _fixture("strict_plan.md").replace(
        "- **Requirements**: R1, R2\n"
        "- **Files**: `scripts/artifact_views/parser.py`\n"
        "- **Details**: Parse blocks and validate mappings.\n"
        "- **Test Scenarios**: happy path, edge case, error path\n"
        "- **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`",
        "```markdown\n"
        "- **Requirements**: R1, R2\n"
        "- **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`\n"
        "```",
    )

    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            source,
            Path(".cg-docs/plans/fenced-metadata.md"),
            ArtifactKind.PLAN,
        )

    messages = _validation_messages(caught.value)
    assert "no requirement mapping" in messages
    assert "Tests metadata" in messages


def test_indented_fenced_examples_in_lists_cannot_satisfy_step_metadata() -> None:
    source = _fixture("strict_plan.md").replace(
        "- **Requirements**: R1, R2\n"
        "- **Files**: `scripts/artifact_views/parser.py`\n"
        "- **Details**: Parse blocks and validate mappings.\n"
        "- **Test Scenarios**: happy path, edge case, error path\n"
        "- **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`",
        "- Example metadata:\n"
        "  ```markdown\n"
        "  - **Requirements**: R1, R2\n"
        "  - **Tests**: `pytest -q scripts/artifact_views/tests/test_parser.py`\n"
        "  ```",
    )

    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            source,
            Path(".cg-docs/plans/indented-fenced-metadata.md"),
            ArtifactKind.PLAN,
        )

    messages = _validation_messages(caught.value)
    assert "no requirement mapping" in messages
    assert "Tests metadata" in messages


def test_validation_error_collection_is_bounded() -> None:
    source = _fixture("strict_plan.md")
    for section in (
        "Objective",
        "Context",
        "Testing Strategy",
        "Documentation Checklist",
        "Risks & Mitigations",
        "Out of Scope",
    ):
        source = source.replace(f"## {section}", f"## Missing {section}")
    source = source.replace("**Requirements**: R1, R2", "**Requirements**: R9, R9")
    with pytest.raises(ArtifactValidationError) as caught:
        validate_source(
            source,
            Path(".cg-docs/plans/many-errors.md"),
            ArtifactKind.PLAN,
        )
    assert 1 < len(caught.value.errors) <= MAX_VALIDATION_ERRORS


def test_validate_path_reports_invalid_utf8_as_read_error(tmp_path: Path) -> None:
    source = tmp_path / "invalid.md"
    source.write_bytes(b"\xff\xfe")
    with pytest.raises(ArtifactReadError, match="strict UTF-8"):
        validate_path(source, ArtifactKind.PLAN)


def test_validation_api_has_no_renderer_dependency() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(repository_root / "scripts")
    command = (
        "import sys; import artifact_views.validator; "
        "forbidden={'artifact_views.renderer','artifact_views.templates',"
        "'artifact_views.config'}; "
        "loaded=forbidden.intersection(sys.modules); "
        "assert not loaded, sorted(loaded)"
    )

    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
