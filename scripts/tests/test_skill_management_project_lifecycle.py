"""Project import and explicit activation lifecycle tests."""
from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from skill_management import planning
from skill_management.operations import import_skill
from skill_management.providers.github import AcquiredBundle, AcquiredFile
from skill_management.services import bundles, provenance as provenance_service, runtime
from scripts.tests.test_project_projection import (
    _canonical_assets,
    _real_registry,
    _small_mapping,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    _real_registry(source)
    _small_mapping(source)
    _canonical_assets(source)
    project = tmp_path / "project"
    project.mkdir()
    (project / "compound-gpid.local.md").write_text(
        '---\nlanguage: "r"\nsuites: [cg]\n---\n# project\n', encoding="utf-8"
    )
    return source, project


def _install_policy(source: Path) -> None:
    shutil.copy2(
        REPO_ROOT / ".github/shared/vendor-policy.json",
        source / ".github/shared/vendor-policy.json",
    )


def _import_arguments(source_path: str) -> dict:
    return {
        "positionals": [
            "https://github.com/outside/public-skills",
            source_path,
            "a" * 40,
        ],
        "license": "MIT",
        "platforms": "kilo",
        "suites": "cg",
    }


def _acquired_bundle(source_path: str) -> AcquiredBundle:
    content = b'---\nname: demo\ndescription: "Demo"\n---\n# Demo\n'
    object_id = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    return AcquiredBundle(
        "https://github.com/outside/public-skills",
        "a" * 40,
        source_path,
        (AcquiredFile("SKILL.md", content, object_id, len(content), "100644"),),
        "c" * 64,
    )


def _candidate(tmp_path: Path) -> bundles.BundleInventory:
    skill = tmp_path / "candidate/demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: demo\ndescription: "Imported demo"\n---\n# Demo\n', encoding="utf-8"
    )
    return bundles.inventory_bundle(
        tmp_path, "candidate/demo", origin="project-imported"
    )


def test_import_operation_plan_writes_only_quarantine_evidence_and_plan(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _roots(tmp_path)
    _install_policy(source)
    acquired = _acquired_bundle("skills/demo")

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return acquired

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    context = SimpleNamespace(project_root=project, source_root=source, role="consumer")
    arguments = _import_arguments("skills/demo")
    outcome = import_skill.handle(
        context=context,
        request={"phase": "plan", "arguments": arguments},
    )

    assert not outcome.findings
    assert outcome.plan_digest
    assert not (project / ".compound-gpid/project-skill-registry.json").exists()
    assert not (project / ".compound-gpid/active-manifest.json").exists()
    assert not (project / ".kilo").exists()
    assert list((project / ".compound-gpid/quarantine").rglob("SKILL.md"))
    assert list((project / ".compound-gpid/vendor-reviews").glob("*.json"))
    assert list((project / ".compound-gpid/skill-plans").glob("*.json"))

    applied = import_skill.handle(
        context=context,
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": outcome.plan_digest,
        },
    )
    assert not applied.findings
    assert applied.data["status"] == "committed"
    assert (project / ".compound-gpid/project-skill-registry.json").is_file()


@pytest.mark.parametrize(
    "source_path",
    ("outside/demo", "skills-archive/demo", "skills"),
)
def test_project_import_rejects_disallowed_root_before_provider_access(
    tmp_path: Path, monkeypatch, source_path: str
) -> None:
    source, project = _roots(tmp_path)
    _install_policy(source)

    class Provider:
        called = False

        def acquire(self, *_args, **_kwargs):
            Provider.called = True
            raise AssertionError("provider must not be called")

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    outcome = import_skill.handle(
        context=SimpleNamespace(
            project_root=project, source_root=source, role="consumer"
        ),
        request={"phase": "plan", "arguments": _import_arguments(source_path)},
    )

    assert outcome.exit_code == 5
    assert outcome.findings
    assert "allowed upstream skill root" in outcome.findings[0].message
    assert Provider.called is False


def test_project_import_normalizes_nested_allowed_path_before_provider_access(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _roots(tmp_path)
    _install_policy(source)
    requested_paths = []

    class Provider:
        def acquire(self, _origin, _commit, source_path, _limits):
            requested_paths.append(source_path)
            return _acquired_bundle(source_path)

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    outcome = import_skill.handle(
        context=SimpleNamespace(
            project_root=project, source_root=source, role="consumer"
        ),
        request={
            "phase": "plan",
            "arguments": _import_arguments("skills//nested/./demo/"),
        },
    )

    assert not outcome.findings
    assert requested_paths == ["skills/nested/demo"]


def test_project_import_apply_revalidates_changed_allowed_roots(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _roots(tmp_path)
    _install_policy(source)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired_bundle("skills/demo")

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    context = SimpleNamespace(
        project_root=project, source_root=source, role="consumer"
    )
    arguments = _import_arguments("skills/demo")
    planned = import_skill.handle(
        context=context, request={"phase": "plan", "arguments": arguments}
    )
    policy_path = source / ".github/shared/vendor-policy.json"
    policy = json.loads(policy_path.read_text("utf-8"))
    policy["allowedUpstreamSkillRoots"] = [".github/skills/"]
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    applied = import_skill.handle(
        context=context,
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )

    assert applied.exit_code == 5
    assert "allowed upstream skill root" in applied.findings[0].message
    assert not (project / ".compound-gpid/project-skill-registry.json").exists()


def test_import_is_inactive_then_activate_and_deactivate_use_one_transaction(
    tmp_path: Path,
) -> None:
    source, project = _roots(tmp_path)
    inventory = _candidate(tmp_path)
    import_plan = runtime.plan_project_import(
        project,
        source,
        inventory,
        origin="https://github.com/outside/public-skills",
        source_path="skills/demo",
        commit="a" * 40,
        suites=("cg",),
        platforms=("copilot", "claude-code", "codex", "opencode", "kilo"),
    )
    assert import_plan.arguments["origin"] == (
        "https://github.com/outside/public-skills"
    )
    import_record = planning.store_plan(project, import_plan)
    planning.apply_plan(project, import_plan, import_record.digest)

    registry = json.loads(
        (project / ".compound-gpid/project-skill-registry.json").read_text("utf-8")
    )
    assert registry["records"][0]["id"] == "demo"
    manifest = json.loads(
        (project / ".compound-gpid/active-manifest.json").read_text("utf-8")
    )
    assert manifest["selection"]["selectedProjectSkills"] == {}
    assert not (project / ".kilo/skills/demo/SKILL.md").exists()

    activate = runtime.plan_capability_change(
        project, source, "project-skill-demo", activate=True
    )
    activate_record = planning.store_plan(project, activate)
    planning.apply_plan(project, activate, activate_record.digest)
    for relative in (
        ".github/skills/demo/SKILL.md",
        ".claude/skills/demo/SKILL.md",
        ".agents/skills/demo/SKILL.md",
        ".opencode/skills/demo/SKILL.md",
        ".kilo/skills/demo/SKILL.md",
    ):
        assert (project / relative).is_file(), relative
    active_manifest = json.loads(
        (project / ".compound-gpid/active-manifest.json").read_text("utf-8")
    )
    assert active_manifest["selection"]["selectedProjectSkills"] == {
        "project-skill-demo": "demo"
    }

    deactivate = runtime.plan_capability_change(
        project, source, "project-skill-demo", activate=False
    )
    deactivate_record = planning.store_plan(project, deactivate)
    planning.apply_plan(project, deactivate, deactivate_record.digest)
    assert not (project / ".kilo/skills/demo/SKILL.md").exists()
    assert not (project / ".github/skills/demo/SKILL.md").exists()
    assert (project / ".compound-gpid/skills/demo/SKILL.md").is_file()


def test_selector_derived_and_dependency_required_deactivation_are_blocked(
    tmp_path: Path,
) -> None:
    source, project = _roots(tmp_path)
    config = project / "compound-gpid.local.md"
    config.write_text(
        '---\nlanguage: "r"\nsuites: [cg]\ncapabilities: [r]\n---\n',
        encoding="utf-8",
    )
    try:
        runtime.plan_capability_change(project, source, "r", activate=False)
    except runtime.RuntimePlanningError as error:
        assert "selector-derived" in str(error)
    else:
        raise AssertionError("selector-derived capability deactivation was allowed")

    config.write_text(
        '---\nlanguage: "stata"\nsuites: [cg]\ncapabilities: [r]\n---\n',
        encoding="utf-8",
    )
    try:
        runtime.plan_capability_change(project, source, "r", activate=False)
    except runtime.RuntimePlanningError as error:
        assert "dependency-required" in str(error)
    else:
        raise AssertionError("dependency-required capability deactivation was allowed")


def test_deprecated_project_skill_cannot_be_newly_activated(tmp_path: Path) -> None:
    source, project = _roots(tmp_path)
    for identifier, commit in (("demo", "a" * 40), ("replacement", "b" * 40)):
        candidate_root = tmp_path / f"candidate-{identifier}"
        skill = candidate_root / "candidate" / identifier
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f'---\nname: {identifier}\ndescription: "{identifier}"\n---\n',
            encoding="utf-8",
        )
        inventory = bundles.inventory_bundle(
            candidate_root, f"candidate/{identifier}", origin="project-imported"
        )
        plan = runtime.plan_project_import(
            project,
            source,
            inventory,
            origin="https://github.com/example/skills",
            source_path=f"skills/{identifier}",
            commit=commit,
            suites=("cg",),
            platforms=("kilo",),
        )
        record = planning.store_plan(project, plan)
        planning.apply_plan(project, plan, record.digest)

    registry_path = project / ".compound-gpid/project-skill-registry.json"
    registry_value = json.loads(registry_path.read_text("utf-8"))
    demo = next(item for item in registry_value["records"] if item["id"] == "demo")
    demo["lifecycle"] = "deprecated"
    demo["successorId"] = "replacement"
    registry_path.write_text(
        json.dumps(registry_value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    provenance_path = project / ".compound-gpid/skill-provenance/demo.json"
    provenance = json.loads(provenance_path.read_text("utf-8"))
    provenance = provenance_service.append_deprecation(
        provenance,
        "replacement",
        "project-user",
        "review=" + "c" * 40,
        "c" * 40,
    )
    provenance_path.write_text(
        json.dumps(provenance, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    try:
        runtime.plan_capability_change(
            project, source, "project-skill-demo", activate=True
        )
    except runtime.RuntimePlanningError as error:
        assert "deprecated" in str(error)
    else:
        raise AssertionError("deprecated project skill activation was allowed")


def test_only_one_of_two_project_bundles_is_selected(tmp_path: Path) -> None:
    source, project = _roots(tmp_path)
    for identifier in ("one", "two"):
        candidate_root = tmp_path / identifier
        skill = candidate_root / "candidate" / identifier
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f'---\nname: {identifier}\ndescription: "{identifier}"\n---\n# {identifier}\n',
            encoding="utf-8",
        )
        inventory = bundles.inventory_bundle(
            candidate_root, f"candidate/{identifier}", origin="project-imported"
        )
        plan = runtime.plan_project_import(
            project,
            source,
            inventory,
            origin="https://github.com/example/skills",
            source_path=f"skills/{identifier}",
            commit=("a" if identifier == "one" else "b") * 40,
            suites=("cg",),
            platforms=("kilo",),
        )
        record = planning.store_plan(project, plan)
        planning.apply_plan(project, plan, record.digest)

    activation = runtime.plan_capability_change(
        project, source, "project-skill-one", activate=True
    )
    record = planning.store_plan(project, activation)
    planning.apply_plan(project, activation, record.digest)

    assert (project / ".kilo/skills/one/SKILL.md").is_file()
    assert not (project / ".kilo/skills/two/SKILL.md").exists()
