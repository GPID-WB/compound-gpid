"""Tests for the committed project skill registry and provenance overlay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from skill_management.services import bundles
from skill_management.services import registry


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _canonical_registry() -> dict:
    return {
        "schemaVersion": 2,
        "description": "project overlay fixture",
        "capabilities": [
            {
                "id": "python",
                "owningModule": "cap-python",
                "supportedSuites": ["cg"],
                "supportedPlatforms": [
                    "copilot",
                    "claude-code",
                    "codex",
                    "opencode",
                    "kilo",
                ],
                "sourceProvenance": "canonical/.github",
                "activationCost": "low",
                "taskTriggers": ["language=python"],
                "configSelectors": [
                    {
                        "field": "language",
                        "operator": "contains",
                        "value": "python",
                    }
                ],
            }
        ],
        "modules": [
            {
                "id": "kernel",
                "layer": "kernel",
                "displayName": "Kernel",
                "description": "kernel",
                "dependsOn": [],
                "ownedAssets": [],
            },
            {
                "id": "cap-python",
                "layer": "capability",
                "displayName": "Python",
                "description": "python",
                "dependsOn": ["kernel"],
                "ownedAssets": [".github/skills/canonical-skill/"],
            },
            {
                "id": "suite-cg",
                "layer": "suite",
                "displayName": "CG",
                "description": "cg",
                "dependsOn": ["kernel"],
                "ownedAssets": [],
            },
        ],
    }


def _source_root(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    _write_json(root / registry.MODULE_REGISTRY_PATH, _canonical_registry())
    skill = root / ".github/skills/canonical-skill/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        '---\nname: canonical-skill\ndescription: "Canonical"\n---\n# Canonical\n',
        encoding="utf-8",
    )
    return root


def _project_record(identifier: str, digest: str) -> dict:
    return {
        "id": identifier,
        "origin": "project-imported",
        "owner": "project-local",
        "capability": f"project-skill-{identifier}",
        "activationMode": "explicit-only",
        "sourcePath": f".compound-gpid/skills/{identifier}",
        "supportedSuites": ["cg"],
        "supportedPlatforms": [
            "copilot",
            "claude-code",
            "codex",
            "opencode",
            "kilo",
        ],
        "admission": "approved",
        "lifecycle": "current",
        "provenanceId": identifier,
        "bundleDigest": digest,
    }


def _provenance(identifier: str, digest: str) -> dict:
    return {
        "schema": "cg-skill-provenance-v1",
        "schemaVersion": 1,
        "skillId": identifier,
        "origin": "project-imported",
        "admission": "approved",
        "lifecycle": "current",
        "source": {
            "repository": "https://github.com/example/project-skills",
            "path": identifier,
            "commit": "a" * 40,
            "bundleDigest": digest,
        },
        "history": [
            {
                "sequence": 1,
                "event": "imported",
                "commit": "a" * 40,
                "bundleDigest": digest,
                "approval": {
                    "actor": "project-user",
                    "reviewReference": "project/review/1",
                },
            }
        ],
        "migrations": [],
    }


def add_project_skill(project_root: Path, identifier: str) -> dict:
    skill_root = project_root / ".compound-gpid/skills" / identifier
    skill_root.mkdir(parents=True)
    (skill_root / "SKILL.md").write_text(
        f'---\nname: {identifier}\ndescription: "Project {identifier}"\n---\n'
        f"# {identifier}\n\n[Guide](references/guide.md)\n",
        encoding="utf-8",
    )
    (skill_root / "references").mkdir()
    (skill_root / "references/guide.md").write_text("# Guide\n", encoding="utf-8")
    inventory = bundles.inventory_bundle(
        project_root,
        f".compound-gpid/skills/{identifier}",
        origin="project-imported",
    )
    return _project_record(identifier, inventory.digest)


def write_project_overlay(project_root: Path, records: list[dict]) -> None:
    _write_json(
        project_root / registry.PROJECT_REGISTRY_PATH,
        {
            "schema": "cg-project-skill-registry-v1",
            "schemaVersion": 1,
            "records": sorted(records, key=lambda item: item["id"]),
        },
    )
    for record in records:
        _write_json(
            project_root / registry.PROVENANCE_ROOT / f"{record['id']}.json",
            _provenance(record["id"], record["bundleDigest"]),
        )


def test_absent_project_overlay_is_an_immutable_empty_snapshot(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    snapshot = registry.load_combined_registry_snapshot(project, source)

    assert snapshot.project_records == ()
    assert snapshot.project_bundles == ()
    assert len(snapshot.canonical_digest) == 64
    assert len(snapshot.project_registry_digest) == 64
    assert len(snapshot.provenance_digest) == 64
    assert snapshot.project_registry_digest != snapshot.canonical_digest


def test_valid_project_record_loads_exact_bundle_and_provenance(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    record = add_project_skill(project, "local-one")
    write_project_overlay(project, [record])

    snapshot = registry.load_combined_registry_snapshot(project, source)

    assert [item["id"] for item in snapshot.project_records] == ["local-one"]
    assert [item.identifier for item in snapshot.project_bundles] == ["local-one"]
    assert snapshot.project_capability_by_id("project-skill-local-one")["owner"] == (
        "project-local"
    )
    assert snapshot.provenance_by_id("local-one")["source"]["commit"] == "a" * 40


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda record: record.update(owner="canonical-owner"), "project-local"),
        (lambda record: record.update(activationMode="selector-derived"), "explicit-only"),
        (lambda record: record.update(capability="python"), "capability"),
        (lambda record: record.update(sourcePath="../outside"), "source"),
        (lambda record: record.update(supportedSuites=["unknown"]), "supportedSuites"),
        (lambda record: record.update(supportedPlatforms=["unknown"]), "supportedPlatforms"),
    ],
)
def test_reserved_namespace_and_eligibility_violations_fail_closed(
    tmp_path: Path, mutation, message: str
) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    record = add_project_skill(project, "local-one")
    mutation(record)
    write_project_overlay(project, [record])

    with pytest.raises(registry.RegistryValidationError, match=message):
        registry.load_combined_registry_snapshot(project, source)


def test_canonical_identifier_shadow_fails_closed(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    record = add_project_skill(project, "canonical-skill")
    write_project_overlay(project, [record])

    with pytest.raises(registry.RegistryValidationError, match="shadow"):
        registry.load_combined_registry_snapshot(project, source)


def test_missing_bundle_and_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    record = add_project_skill(project, "local-one")
    write_project_overlay(project, [record])
    (project / ".compound-gpid/skills/local-one/references/guide.md").unlink()

    with pytest.raises(registry.RegistryValidationError, match="bundle|reference|digest"):
        registry.load_combined_registry_snapshot(project, source)


def test_provenance_digest_or_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    record = add_project_skill(project, "local-one")
    write_project_overlay(project, [record])
    path = project / registry.PROVENANCE_ROOT / "local-one.json"
    provenance = json.loads(path.read_text(encoding="utf-8"))
    provenance["source"]["bundleDigest"] = hashlib.sha256(b"other").hexdigest()
    _write_json(path, provenance)

    with pytest.raises(registry.RegistryValidationError, match="provenance|digest"):
        registry.load_combined_registry_snapshot(project, source)


def test_project_registry_path_link_is_never_followed(
    tmp_path: Path, require_symlink_support: None
) -> None:
    source = _source_root(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.json"
    _write_json(
        outside,
        {"schema": "cg-project-skill-registry-v1", "schemaVersion": 1, "records": []},
    )
    path = project / registry.PROJECT_REGISTRY_PATH
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)

    with pytest.raises(registry.RegistryValidationError, match="link|reparse|safe"):
        registry.load_combined_registry_snapshot(project, source)


def test_portable_case_shadow_of_canonical_bundle_fails_closed(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    canonical = source / ".github/skills/LOCAL-ONE/SKILL.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# collision fixture\n", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    record = add_project_skill(project, "local-one")
    write_project_overlay(project, [record])

    with pytest.raises(registry.RegistryValidationError, match="shadow"):
        registry.load_combined_registry_snapshot(project, source)


def test_gitignore_commits_project_inputs_and_ignores_runtime_state() -> None:
    root = Path(__file__).resolve().parents[2]
    lines = {
        line.strip()
        for line in (root / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".compound-gpid/skills/" not in lines
    assert ".compound-gpid/project-skill-registry.json" not in lines
    assert ".compound-gpid/skill-provenance/" not in lines
    assert ".compound-gpid/skill-plans/" in lines
    assert ".compound-gpid/skill-transactions/" in lines
    assert ".compound-gpid/projection-ownership.json" in lines
