"""Deprecation and reference-safe removal tests for Phase 6."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from skill_management import planning
from skill_management.operations import deprecate, remove
from skill_management.services import bundles, lifecycle, references, registry, runtime
from scripts.tests.test_skill_management_project_lifecycle import _roots
from scripts.tests.test_skill_management_contracts import (
    PORTABLE_PROTECTED_MIGRATION_ALIASES,
    PROTECTED_MIGRATION_PATHS,
    SUPPORTED_MIGRATION_PATHS,
)
from scripts.tests.test_skill_management_create import (
    _arguments as create_arguments,
    _canonical_root,
    _context as canonical_context,
)
from skill_management.operations import create


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(root: Path, message: str) -> str:
    _git(root, "add", ".compound-gpid", "compound-gpid.local.md")
    marker = root / "grace-marker.txt"
    if marker.exists():
        _git(root, "add", "grace-marker.txt")
    _git(
        root,
        "-c",
        "user.name=Phase Six",
        "-c",
        "user.email=phase6@example.test",
        "commit",
        "-m",
        message,
    )
    return _git(root, "rev-parse", "HEAD")


def _import(
    project: Path, source: Path, tmp_path: Path, identifier: str, commit: str
) -> None:
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
    stored = planning.store_plan(project, plan)
    planning.apply_plan(project, plan, stored.digest)


def _project(tmp_path: Path) -> tuple[Path, Path, SimpleNamespace]:
    source, project = _roots(tmp_path)
    _import(project, source, tmp_path, "demo-skill", "a" * 40)
    _import(project, source, tmp_path, "next-skill", "b" * 40)
    _git(project, "init")
    _commit(project, "initial skills")
    context = SimpleNamespace(
        project_root=project,
        source_root=source,
        role="consumer",
        can_write_canonical=False,
        write_context_errors=("consumer project",),
    )
    return source, project, context


def _deprecate(context: SimpleNamespace) -> str:
    arguments = {
        "positionals": ["demo-skill", "next-skill"],
        "approver": "project-reviewer",
        "review_reference": "review=" + "c" * 40,
    }
    planned = deprecate.handle(
        context=context, request={"phase": "plan", "arguments": arguments}
    )
    assert not planned.findings
    applied = deprecate.handle(
        context=context,
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )
    assert not applied.findings
    return str(applied.data["deprecatedRecordDigest"])


def _migration(project: Path, expected: bytes) -> Path:
    path = project / ".compound-gpid/skill-migrations/demo-to-next.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {
        "schema": "cg-skill-migration-v1",
        "schemaVersion": 1,
        "id": "demo-to-next",
        "skillId": "demo-skill",
        "edits": [
            {
                "path": "docs/use.md",
                "expectedSha256": hashlib.sha256(expected).hexdigest(),
                "replacement": "Use next-skill.\n",
            }
        ],
        "reviewer": "project-reviewer",
        "approvalReference": "review=" + "d" * 40,
    }
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _migration_record(path: str, current: bytes) -> lifecycle.MigrationRecord:
    value = {
        "id": "demo-to-next",
        "edits": [
            {
                "path": path,
                "expectedSha256": hashlib.sha256(current).hexdigest(),
                "replacement": "Use next-skill.\n",
            }
        ],
    }
    return lifecycle.MigrationRecord("migration.json", value, "f" * 64)


@pytest.mark.parametrize(
    "path", PROTECTED_MIGRATION_PATHS + PORTABLE_PROTECTED_MIGRATION_ALIASES
)
def test_migration_planning_rejects_protected_targets_without_writing(
    tmp_path: Path, path: str
) -> None:
    current = b"Use demo-skill.\n"
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(current)

    with pytest.raises(lifecycle.LifecyclePlanningError, match="bounded project"):
        lifecycle._migration_actions(  # pylint: disable=protected-access
            tmp_path, (_migration_record(path, current),)
        )

    assert target.read_bytes() == current


@pytest.mark.parametrize("path", SUPPORTED_MIGRATION_PATHS)
def test_migration_planning_allows_normal_documentation_and_references(
    tmp_path: Path, path: str
) -> None:
    current = b"Use demo-skill.\n"
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(current)

    actions = lifecycle._migration_actions(  # pylint: disable=protected-access
        tmp_path, (_migration_record(path, current),)
    )

    assert len(actions) == 1
    assert actions[0].path == path
    assert actions[0].mutation is not None
    assert actions[0].mutation.before == current
    assert target.read_bytes() == current


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable mode assertion")
def test_migration_planning_rejects_executable_document_without_writing(
    tmp_path: Path,
) -> None:
    current = b"Use demo-skill.\n"
    target = tmp_path / "docs/use.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(current)
    target.chmod(0o755)

    with pytest.raises(lifecycle.LifecyclePlanningError, match="executable"):
        lifecycle._migration_actions(  # pylint: disable=protected-access
            tmp_path, (_migration_record("docs/use.md", current),)
        )

    assert target.read_bytes() == current


@pytest.mark.parametrize(
    "current",
    (
        b"\xff\xfe",
        b"x" * (references.MAX_REFERENCE_FILE_BYTES + 1),
    ),
    ids=("non-utf8", "oversized"),
)
def test_migration_planning_rejects_unbounded_or_non_text_document_without_writing(
    tmp_path: Path, current: bytes
) -> None:
    target = tmp_path / "docs/use.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(current)

    with pytest.raises(lifecycle.LifecyclePlanningError, match="bounded regular"):
        lifecycle._migration_actions(  # pylint: disable=protected-access
            tmp_path, (_migration_record("docs/use.md", current),)
        )

    assert target.read_bytes() == current


def test_migration_loading_rejects_portable_unicode_path_aliases(
    tmp_path: Path,
) -> None:
    migration_root = tmp_path / "migrations"
    migration_root.mkdir()
    paths = ("docs/Caf\u00e9.md", "DOCS/Cafe\u0301.md")
    for index, path in enumerate(paths):
        value = {
            "schema": "cg-skill-migration-v1",
            "schemaVersion": 1,
            "id": f"demo-to-next-{index}",
            "skillId": "demo-skill",
            "edits": [
                {
                    "path": path,
                    "expectedSha256": "a" * 64,
                    "replacement": "Use next-skill.\n",
                }
            ],
            "reviewer": "project-reviewer",
            "approvalReference": "review=" + "d" * 40,
        }
        (migration_root / f"{index}.json").write_text(
            json.dumps(value) + "\n", encoding="utf-8"
        )

    with pytest.raises(lifecycle.LifecyclePlanningError, match="collide portably"):
        lifecycle.load_migrations(
            tmp_path,
            tuple(f"migrations/{index}.json" for index in range(2)),
            "demo-skill",
        )


def test_deprecation_rejects_self_cross_origin_and_cycles(tmp_path: Path) -> None:
    source, project, _context = _project(tmp_path)
    snapshot = registry.load_combined_registry_snapshot(project, source)

    with pytest.raises(lifecycle.LifecyclePlanningError, match="itself"):
        lifecycle.plan_deprecation(
            project,
            source,
            "demo-skill",
            "demo-skill",
            "reviewer",
            "review=" + "a" * 40,
            role="consumer",
        )
    canonical_id = snapshot.canonical_bundles[0].identifier
    with pytest.raises(lifecycle.LifecyclePlanningError, match="origin"):
        lifecycle.plan_deprecation(
            project,
            source,
            "demo-skill",
            canonical_id,
            "reviewer",
            "review=" + "a" * 40,
            role="consumer",
        )


def test_active_deprecated_skill_warns_and_removal_is_blocked(tmp_path: Path) -> None:
    source, project, context = _project(tmp_path)
    activation = runtime.plan_capability_change(
        project, source, "project-skill-demo-skill", activate=True
    )
    stored = planning.store_plan(project, activation)
    planning.apply_plan(project, activation, stored.digest)

    arguments = {
        "positionals": ["demo-skill", "next-skill"],
        "approver": "project-reviewer",
        "review_reference": "review=" + "c" * 40,
    }
    planned = deprecate.handle(
        context=context, request={"phase": "plan", "arguments": arguments}
    )
    assert planned.data["activeWarning"] is True
    deprecate.handle(
        context=context,
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )
    blocked = remove.handle(
        context=context,
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["demo-skill"],
                "approver": "project-reviewer",
                "review_reference": "review=" + "d" * 40,
            },
        },
    )

    assert blocked.findings
    assert blocked.exit_code == 6
    assert "active" in blocked.findings[0].message.casefold()


def test_project_removal_applies_digest_bound_migration_and_reserves_id(
    tmp_path: Path,
) -> None:
    source, project, context = _project(tmp_path)
    deprecated_digest = _deprecate(context)
    _commit(project, "deprecate demo")
    (project / "grace-marker.txt").write_text("later\n", encoding="utf-8")
    later = _commit(project, "later reviewed revision")
    active_reference = b"Use demo-skill.\n"
    (project / "docs").mkdir()
    (project / "docs/use.md").write_bytes(active_reference)
    migration = _migration(project, active_reference)
    user_file = project / ".kilo/skills/demo-skill/user.txt"
    user_file.parent.mkdir(parents=True, exist_ok=True)
    user_file.write_text("user-owned\n", encoding="utf-8")
    arguments = {
        "positionals": ["demo-skill"],
        "approver": "project-reviewer",
        "review_reference": "review=" + "e" * 40,
        "migrations": migration.relative_to(project).as_posix(),
    }

    planned = remove.handle(
        context=context, request={"phase": "plan", "arguments": arguments}
    )
    assert not planned.findings
    assert planned.data["remainingReferences"] == []
    applied = remove.handle(
        context=context,
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )

    assert not applied.findings
    assert not (project / ".compound-gpid/skills/demo-skill/SKILL.md").exists()
    assert not list((project / ".compound-gpid/skills/demo-skill").rglob("*"))
    assert (project / "docs/use.md").read_text(encoding="utf-8") == "Use next-skill.\n"
    assert user_file.read_text(encoding="utf-8") == "user-owned\n"
    registry_value = json.loads(
        (project / ".compound-gpid/project-skill-registry.json").read_text("utf-8")
    )
    assert "demo-skill" not in {item["id"] for item in registry_value["records"]}
    provenance = json.loads(
        (project / ".compound-gpid/skill-provenance/demo-skill.json").read_text(
            "utf-8"
        )
    )
    assert provenance["lifecycle"] == "removed"
    assert provenance["deprecatedRecordDigest"] == deprecated_digest
    assert provenance["tombstone"]["recordDigest"] == deprecated_digest
    assert provenance["tombstone"]["removedRevision"] == later
    assert provenance["migrations"][0]["status"] == "applied"

    candidate_root = tmp_path / "reuse"
    skill = candidate_root / "candidate/demo-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: demo-skill\ndescription: "Reuse"\n---\n', encoding="utf-8"
    )
    candidate = bundles.inventory_bundle(
        candidate_root, "candidate/demo-skill", origin="project-imported"
    )
    with pytest.raises(runtime.RuntimePlanningError, match="reserved|exists"):
        runtime.plan_project_import(
            project,
            source,
            candidate,
            origin="https://github.com/example/skills",
            source_path="skills/demo-skill",
            commit="f" * 40,
            suites=("cg",),
            platforms=("kilo",),
        )


def test_stale_migration_digest_blocks_without_editing_reference(
    tmp_path: Path,
) -> None:
    _source, project, context = _project(tmp_path)
    _deprecate(context)
    _commit(project, "deprecate demo")
    (project / "grace-marker.txt").write_text("later\n", encoding="utf-8")
    _commit(project, "later reviewed revision")
    current = b"Use demo-skill.\n"
    (project / "docs").mkdir()
    reference = project / "docs/use.md"
    reference.write_bytes(current)
    migration = _migration(project, b"different bytes\n")

    outcome = remove.handle(
        context=context,
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["demo-skill"],
                "approver": "project-reviewer",
                "review_reference": "review=" + "e" * 40,
                "migrations": migration.relative_to(project).as_posix(),
            },
        },
    )

    assert outcome.findings
    assert "digest" in outcome.findings[0].message.casefold()
    assert reference.read_bytes() == current


def test_zero_reference_rescan_blocks_uncovered_active_reference(
    tmp_path: Path,
) -> None:
    _source, project, context = _project(tmp_path)
    _deprecate(context)
    _commit(project, "deprecate demo")
    (project / "grace-marker.txt").write_text("later\n", encoding="utf-8")
    _commit(project, "later reviewed revision")
    (project / "docs").mkdir()
    (project / "docs/use.md").write_text("Use demo-skill.\n", encoding="utf-8")

    outcome = remove.handle(
        context=context,
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["demo-skill"],
                "approver": "project-reviewer",
                "review_reference": "review=" + "e" * 40,
            },
        },
    )

    assert outcome.findings
    assert outcome.exit_code == 6
    assert "zero" in outcome.findings[0].message.casefold()


def test_modified_checksum_owned_projection_blocks_without_deletion(
    tmp_path: Path,
) -> None:
    _source, project, context = _project(tmp_path)
    _deprecate(context)
    _commit(project, "deprecate demo")
    (project / "grace-marker.txt").write_text("later\n", encoding="utf-8")
    _commit(project, "later reviewed revision")
    destination = project / ".kilo/skills/demo-skill/SKILL.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("modified user bytes\n", encoding="utf-8")
    ownership = {
        "schemaVersion": 1,
        "entries": {
            ".kilo/skills/demo-skill/SKILL.md": {
                "sha256": "a" * 64,
            }
        },
    }
    ownership_path = project / ".compound-gpid/projection-ownership.json"
    ownership_path.write_text(json.dumps(ownership) + "\n", encoding="utf-8")

    outcome = remove.handle(
        context=context,
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["demo-skill"],
                "approver": "project-reviewer",
                "review_reference": "review=" + "e" * 40,
            },
        },
    )

    assert outcome.findings
    assert "modified" in outcome.findings[0].message.casefold()
    assert destination.read_text(encoding="utf-8") == "modified user bytes\n"


def test_non_git_project_requires_explicit_bounded_grace_exception(
    tmp_path: Path,
) -> None:
    source, project = _roots(tmp_path)
    _import(project, source, tmp_path, "demo-skill", "a" * 40)
    _import(project, source, tmp_path, "next-skill", "b" * 40)
    context = SimpleNamespace(
        project_root=project,
        source_root=source,
        role="consumer",
        can_write_canonical=False,
        write_context_errors=("consumer project",),
    )
    _deprecate(context)
    blocked = remove.handle(
        context=context,
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["demo-skill"],
                "approver": "project-reviewer",
                "review_reference": "review=" + "e" * 40,
            },
        },
    )
    assert blocked.findings
    planned = remove.handle(
        context=context,
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["demo-skill"],
                "approver": "project-reviewer",
                "review_reference": "review=" + "e" * 40,
                "grace_exception": True,
                "grace_reason": "Reviewed non-Git project lifecycle.",
            },
        },
    )
    assert not planned.findings
    assert planned.data["graceEvidence"].startswith("project-grace-exception:")


def test_plugin_removal_preserves_tombstone_and_blocks_reuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _canonical_root(tmp_path)
    arguments = create_arguments()
    create_plan = create.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": arguments},
    )
    create.handle(
        context=canonical_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": create_plan.plan_digest,
        },
    )
    snapshot = registry.load_combined_registry_snapshot(root, root)
    successor = next(
        item.identifier
        for item in snapshot.canonical_bundles
        if item.identifier not in {"permanent-demo", "cg-skill-management"}
    )
    deprecate_arguments = {
        "positionals": ["permanent-demo", successor],
        "approver": "maintainer@example.com",
        "review_reference": "review=" + "c" * 40,
    }
    deprecated = deprecate.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": deprecate_arguments},
    )
    assert not deprecated.findings
    deprecate.handle(
        context=canonical_context(root),
        request={
            "phase": "apply",
            "arguments": deprecate_arguments,
            "planDigest": deprecated.plan_digest,
        },
    )

    class Grace:
        summary = "plugin:v1.0.0@" + "d" * 40 + "->v1.1.0@" + "e" * 40
        removed_revision = "e" * 40

    monkeypatch.setattr(
        lifecycle.release_attestation,
        "verify_plugin_grace",
        lambda *_args, **_kwargs: Grace(),
    )
    remove_arguments = {
        "positionals": ["permanent-demo"],
        "approver": "maintainer@example.com",
        "review_reference": "review=" + "f" * 40,
    }
    planned = remove.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": remove_arguments},
    )
    assert not planned.findings
    applied = remove.handle(
        context=canonical_context(root),
        request={
            "phase": "apply",
            "arguments": remove_arguments,
            "planDigest": planned.plan_digest,
        },
    )
    assert not applied.findings
    assert not (root / ".github/skills/permanent-demo/SKILL.md").exists()
    tombstone = json.loads(
        (
            root
            / ".github/shared/skill-management/provenance/permanent-demo.json"
        ).read_text("utf-8")
    )
    assert tombstone["lifecycle"] == "removed"

    reused = create.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": arguments},
    )
    assert reused.findings
    assert "reserved" in reused.findings[0].message.casefold()
