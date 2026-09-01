"""Descriptor completeness tests for registered skill-management operations."""
from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import cg_pr_preflight
import cg_skill
from skill_management import contracts


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATIONS = (
    "activate",
    "audit",
    "create",
    "deactivate",
    "deprecate",
    "find",
    "help",
    "import",
    "info",
    "remove",
    "update",
    "validate",
)
CANDIDATE_ROOT = REPO_ROOT / "docs/skills/management"
CANDIDATE_MANIFEST = CANDIDATE_ROOT / "candidates.json"
PUBLIC_NAVIGATION = REPO_ROOT / "docs/navigation.json"
OLD_COMMANDS = ("/cg-find-skill", "/cg-import-skill")
PHASE_EVIDENCE_PYTEST_FILES = frozenset(
    {
        "scripts/tests/test_cg_generate_targets.py",
        "scripts/tests/test_copilot_skill_projection.py",
        "scripts/tests/test_import_skill.py",
        "scripts/tests/test_link_projection_order.py",
        "scripts/tests/test_project_manifest.py",
        "scripts/tests/test_project_projection.py",
        "scripts/tests/test_project_skill_registry.py",
        "scripts/tests/test_skill_catalog.py",
        "scripts/tests/test_skill_management_audit.py",
        "scripts/tests/test_skill_management_completeness.py",
        "scripts/tests/test_skill_management_config_editor.py",
        "scripts/tests/test_skill_management_contracts.py",
        "scripts/tests/test_skill_management_create.py",
        "scripts/tests/test_skill_management_dispatch.py",
        "scripts/tests/test_skill_management_github_provider.py",
        "scripts/tests/test_skill_management_locking.py",
        "scripts/tests/test_skill_management_planning.py",
        "scripts/tests/test_skill_management_project_lifecycle.py",
        "scripts/tests/test_skill_management_read.py",
        "scripts/tests/test_skill_management_release_attestation.py",
        "scripts/tests/test_skill_management_removal.py",
        "scripts/tests/test_skill_management_security.py",
        "scripts/tests/test_skill_management_update.py",
        "scripts/tests/test_skill_management_vendor.py",
        "scripts/tests/test_target_closure.py",
        "scripts/tests/test_target_drift.py",
        "scripts/tests/test_target_mapping.py",
        "scripts/tests/test_target_packaging.py",
    }
)
SKILL_MANAGEMENT_PYTHON_FILES = (
    "scripts/cg_context_budget.py",
    "scripts/cg_generate_targets.py",
    "scripts/cg_project_manifest.py",
    "scripts/cg_project_projection.py",
    "scripts/cg_skill.py",
    "scripts/cg_skill_catalog.py",
    "scripts/cg_validate_modules.py",
    "scripts/skill_management/contracts.py",
    "scripts/skill_management/locking.py",
    "scripts/skill_management/planning.py",
    "scripts/skill_management/operations/_capability_change.py",
    "scripts/skill_management/operations/_common.py",
    "scripts/skill_management/operations/_maintenance.py",
    "scripts/skill_management/operations/activate.py",
    "scripts/skill_management/operations/audit.py",
    "scripts/skill_management/operations/deactivate.py",
    "scripts/skill_management/operations/deprecate.py",
    "scripts/skill_management/operations/create.py",
    "scripts/skill_management/operations/find.py",
    "scripts/skill_management/operations/help.py",
    "scripts/skill_management/operations/import_skill.py",
    "scripts/skill_management/operations/info.py",
    "scripts/skill_management/operations/remove.py",
    "scripts/skill_management/operations/update.py",
    "scripts/skill_management/operations/validate.py",
    "scripts/skill_management/providers/__init__.py",
    "scripts/skill_management/providers/github.py",
    "scripts/skill_management/services/__init__.py",
    "scripts/skill_management/services/admission.py",
    "scripts/skill_management/services/bundles.py",
    "scripts/skill_management/services/catalog.py",
    "scripts/skill_management/services/config_editor.py",
    "scripts/skill_management/services/lifecycle.py",
    "scripts/skill_management/services/maintenance.py",
    "scripts/skill_management/services/registry.py",
    "scripts/skill_management/services/provenance.py",
    "scripts/skill_management/services/references.py",
    "scripts/skill_management/services/release_attestation.py",
    "scripts/skill_management/services/runtime.py",
    "scripts/skill_management/services/validation.py",
)


def _copy(path: Path, root: Path) -> None:
    destination = root / path.relative_to(REPO_ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(path.read_bytes())


def _one_operation_root(tmp_path: Path, operation: str = "find") -> Path:
    for relative in (
        ".github/shared/skill-management/contracts/operation-descriptor-v1.schema.json",
        f".github/shared/skill-management/contracts/{operation}-v1.schema.json",
        f".github/shared/skill-management/operations/{operation}.json",
        f".github/skills/cg-skill-management/workflows/{operation}.md",
        f"docs/skills/management/commands/{operation}.md",
        f"scripts/skill_management/operations/{operation}.py",
        "scripts/tests/test_skill_management_read.py",
    ):
        _copy(REPO_ROOT / relative, tmp_path)
    return tmp_path


def _candidate_pages(root: Path = REPO_ROOT) -> tuple[dict, ...]:
    manifest = json.loads(
        (root / "docs/skills/management/candidates.json").read_text(encoding="utf-8")
    )
    assert manifest["schemaVersion"] == "compound-gpid-docs-candidates-v1"
    return tuple(manifest["pages"])


def _slugify(value: str) -> str:
    value = re.sub(r"<[^>]*>", "", value.casefold())
    value = re.sub(r"[`*_]", "", value)
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    return re.sub(r"(^-|-$)", "", re.sub(r"[\s-]+", "-", value))


def _markdown_links(content: str) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for match in re.finditer(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]+\")?\)", content)
    )


def _example_commands(content: str) -> tuple[str, ...]:
    examples = content.partition("## Examples")[2].partition("\n## ")[0]
    blocks = re.findall(r"```(?:text|powershell)\n(.*?)```", examples, re.DOTALL)
    return tuple(
        line.strip()
        for block in blocks
        for line in block.splitlines()
        if line.strip().startswith("python scripts/cg_skill.py ")
    )


def _assert_example_matches_contract(record: contracts.OperationDescriptor, command: str) -> str:
    tokens = shlex.split(command, posix=True)
    assert tokens[:2] == ["python", "scripts/cg_skill.py"]
    namespace = cg_skill._parser().parse_args(tokens[2:])  # pylint: disable=protected-access
    assert namespace.operation == record.operation
    phase, _, remaining = cg_skill._select_phase(  # pylint: disable=protected-access
        record.descriptor, namespace.operation_arguments
    )
    arguments = cg_skill._parse_operation_arguments(  # pylint: disable=protected-access
        remaining, record.contract["$defs"]["arguments"]
    )
    findings = contracts.validate_instance(
        arguments,
        cg_skill._root_operation_schema(  # pylint: disable=protected-access
            record.contract["$defs"]["arguments"],
            f"cg-skill-{record.operation}-arguments-doc-test-v1",
        ),
    )
    assert findings == (), (command, findings)
    return phase


def test_every_registered_operation_through_phase_6_is_complete() -> None:
    records, findings = contracts.discover_operation_descriptors(REPO_ROOT)

    assert findings == ()
    assert tuple(record.operation for record in records) == OPERATIONS
    assert contracts.descriptor_completeness_findings(REPO_ROOT) == ()


def test_candidate_manifest_has_unique_complete_metadata_and_exact_page_inventory() -> None:
    pages = _candidate_pages()
    ids = [page["id"] for page in pages]
    files = [page["file"] for page in pages]
    markdown = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in CANDIDATE_ROOT.rglob("*.md")
    )

    assert len(ids) == len(set(ids))
    assert len(files) == len(set(files))
    assert sorted(files) == markdown
    for page in pages:
        assert re.fullmatch(r"[a-z0-9-]+", page["id"])
        assert page["title"].strip()
        assert page["description"].strip()
        content = (REPO_ROOT / page["file"]).read_text(encoding="utf-8")
        assert content.startswith(f"# {page['title']}\n")


def test_operation_page_identity_roles_phases_and_options_come_from_descriptors() -> None:
    pages = {page["file"]: page for page in _candidate_pages()}
    records, findings = contracts.discover_operation_descriptors(REPO_ROOT)
    assert findings == ()

    for record in records:
        relative = str(record.descriptor["documentation"])
        page = pages[relative]
        assert page["id"] == f"skill-management-{record.operation}"
        assert page["title"] == f"`cg-skill {record.operation}`"
        content = (REPO_ROOT / relative).read_text(encoding="utf-8")
        roles = ", ".join(f"`{role}`" for role in record.descriptor["roles"])
        phases = ", ".join(f"`{phase}`" for phase in record.descriptor["phases"])
        assert f"**Roles:** {roles}" in content
        assert f"**Phases:** {phases}" in content
        expected_options = {
            "--" + name.replace("_", "-")
            for name in record.contract["$defs"]["arguments"]["properties"]
            if name != "positionals"
        }
        if "apply" in record.descriptor["phases"]:
            expected_options.add("--apply")
        assert expected_options <= set(re.findall(r"--[a-z][a-z0-9-]*", content))


def test_every_documented_example_matches_executable_dispatch_grammar() -> None:
    records, findings = contracts.discover_operation_descriptors(REPO_ROOT)
    assert findings == ()
    for record in records:
        content = (REPO_ROOT / record.descriptor["documentation"]).read_text(
            encoding="utf-8"
        )
        phases = {
            _assert_example_matches_contract(record, command)
            for command in _example_commands(content)
        }
        expected = set(record.descriptor["phases"])
        assert expected <= phases, record.operation


def test_executable_help_matches_descriptor_roles_phases_and_page_paths() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/cg_skill.py",
            "--project-root",
            str(REPO_ROOT),
            "--source-root",
            str(REPO_ROOT),
            "--format",
            "json",
            "help",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    records, findings = contracts.discover_operation_descriptors(REPO_ROOT)
    assert findings == ()
    assert result["data"]["operations"] == [
        {
            "operation": record.operation,
            "roles": record.descriptor["roles"],
            "phases": record.descriptor["phases"],
            "workflow": record.descriptor["workflow"],
            "documentation": record.descriptor["documentation"],
        }
        for record in records
    ]


def test_candidate_links_resolve_and_every_page_is_reachable_from_index() -> None:
    candidate_files = {page["file"] for page in _candidate_pages()}
    graph = {relative: set() for relative in candidate_files}
    for relative in sorted(candidate_files):
        path = REPO_ROOT / relative
        content = path.read_text(encoding="utf-8")
        for href in _markdown_links(content):
            assert not re.match(r"^(?:https?:|mailto:)", href, re.IGNORECASE)
            target_text, _, fragment = href.partition("#")
            target = (path.parent / target_text).resolve() if target_text else path
            assert target.is_file(), (relative, href)
            target_relative = target.relative_to(REPO_ROOT).as_posix()
            if target_relative in candidate_files:
                graph[relative].add(target_relative)
            if fragment and target.suffix == ".md":
                headings = {
                    _slugify(match.group(1))
                    for match in re.finditer(
                        r"^#{1,6}\s+(.+)$", target.read_text(encoding="utf-8"), re.MULTILINE
                    )
                }
                assert fragment == _slugify(fragment)
                assert fragment in headings, (relative, href)

    reached = set()
    pending = ["docs/skills/management/index.md"]
    while pending:
        relative = pending.pop()
        if relative in reached:
            continue
        reached.add(relative)
        pending.extend(sorted(graph[relative] - reached))
    assert reached == candidate_files


def test_candidates_remain_unlinked_and_old_names_stay_in_migration_only() -> None:
    public = json.loads(PUBLIC_NAVIGATION.read_text(encoding="utf-8"))
    public_pages = [page for group in public["groups"] for page in group["pages"]]
    candidate_pages = _candidate_pages()
    assert {page["id"] for page in candidate_pages}.isdisjoint(
        {page["id"] for page in public_pages}
    )
    assert {page["file"][len("docs/") :] for page in candidate_pages}.isdisjoint(
        {page["file"] for page in public_pages}
    )

    occurrences = {name: [] for name in OLD_COMMANDS}
    for page in candidate_pages:
        content = (REPO_ROOT / page["file"]).read_text(encoding="utf-8")
        for old_name in OLD_COMMANDS:
            if old_name in content:
                occurrences[old_name].append(page["file"])
    assert occurrences == {
        old_name: ["docs/skills/management/migration.md"] for old_name in OLD_COMMANDS
    }
    for old_name in OLD_COMMANDS:
        stem = old_name[1:]
        assert (REPO_ROOT / f".github/prompts/{stem}.prompt.md").is_file()
        if old_name == "/cg-find-skill":
            assert (REPO_ROOT / f"bin/{stem}").is_file()
            assert (REPO_ROOT / f"bin/{stem}.cmd").is_file()


def test_result_code_table_matches_stable_implementation_codes() -> None:
    content = (CANDIDATE_ROOT / "index.md").read_text(encoding="utf-8")
    documented = {
        match.group(1): int(match.group(2))
        for match in re.finditer(r"^\| `([a-z-]+)` \| (\d+) \|", content, re.MULTILINE)
    }
    assert documented == contracts.EXIT_CODES


def test_authoritative_preflight_and_ci_register_phase_evidence() -> None:
    assert PHASE_EVIDENCE_PYTEST_FILES <= set(cg_pr_preflight.NATIVE_PYTEST_FILES)
    management_tests = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "scripts/tests").glob("test_skill_management*.py")
    }
    assert management_tests <= set(cg_pr_preflight.NATIVE_PYTEST_FILES)

    workflow = (REPO_ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    assert "scripts/cg_pr_preflight.py" in workflow
    assert "ubuntu-24.04" in workflow
    assert "python38-compat:" in workflow
    assert 'python-version: "3.8"' in workflow
    for relative in (
        "scripts/tests/test_skill_management_contracts.py",
        "scripts/tests/test_skill_management_planning.py",
        "scripts/tests/test_project_skill_registry.py",
        "scripts/tests/test_import_skill.py",
        "scripts/tests/test_cg_generate_targets.py",
        "scripts/tests/test_project_projection.py",
    ):
        assert relative in workflow


def test_release_prompt_delegates_to_authoritative_full_preflight() -> None:
    content = (REPO_ROOT / ".github/prompts/cg-release.prompt.md").read_text(
        encoding="utf-8"
    )
    assert (
        "python scripts/cg_pr_preflight.py --phase committed --full-gate "
        "--run-native-target"
    ) in content
    assert "-m pytest scripts/tests/test_target_mapping.py" not in content


def test_missing_declared_documentation_is_a_completeness_error(tmp_path: Path) -> None:
    root = _one_operation_root(tmp_path)
    (root / "docs/skills/management/commands/find.md").unlink()

    findings = contracts.descriptor_completeness_findings(root)

    assert [finding.code for finding in findings] == ["descriptor.incomplete"]
    assert "documentation" in findings[0].message.lower()
    assert findings[0].remediation


def test_runtime_planned_descriptor_state_is_rejected(tmp_path: Path) -> None:
    root = _one_operation_root(tmp_path)
    path = root / ".github/shared/skill-management/operations/find.json"
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    descriptor["state"] = "planned"
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    findings = contracts.descriptor_completeness_findings(root)

    assert [finding.code for finding in findings] == ["descriptor.invalid"]
    assert "contract.const" in findings[0].message


def test_wrong_documented_option_is_a_completeness_error(tmp_path: Path) -> None:
    root = _one_operation_root(tmp_path)
    path = root / "docs/skills/management/commands/find.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("--exact", "--typo"),
        encoding="utf-8",
    )

    findings = contracts.descriptor_completeness_findings(root)

    assert [finding.code for finding in findings] == ["descriptor.documentation"]
    assert "--exact" in findings[0].message


def test_descriptor_paths_are_readable_canonical_files() -> None:
    records, findings = contracts.discover_operation_descriptors(REPO_ROOT)
    assert findings == ()
    for record in records:
        descriptor = record.descriptor
        declared = (
            descriptor["workflow"],
            descriptor["contract"],
            descriptor["documentation"],
            *descriptor["tests"],
        )
        for relative in declared:
            assert (REPO_ROOT / relative).is_file(), relative


def test_skill_management_python_uses_python_38_grammar() -> None:
    for relative in SKILL_MANAGEMENT_PYTHON_FILES:
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        ast.parse(source, filename=relative, feature_version=(3, 8))
