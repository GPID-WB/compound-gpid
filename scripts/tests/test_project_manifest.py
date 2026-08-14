"""Tests for the active project manifest resolver (Step 5, R3/R4/R12/R13).

Run from repo root:
    python -m pytest scripts/tests/test_project_manifest.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_project_manifest as manifest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _create_file(repo_root: Path, rel_path: str, content: str = "body\n") -> None:
    path = repo_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _target_mapping() -> dict:
    return {
        "schemaVersion": 1,
        "description": "fixture target mapping",
        "targets": [
            {"id": "copilot", "name": "GitHub Copilot", "capabilities": {}, "formats": {}, "outputPaths": {}, "installUnits": []},
            {"id": "kilo", "name": "Kilo", "capabilities": {}, "formats": {}, "outputPaths": {}, "installUnits": []},
        ],
    }


def _registry() -> dict:
    return {
        "schemaVersion": 2,
        "description": "fixture registry",
        "capabilities": [
            {"id": "r", "owningModule": "cap-language-r", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["copilot", "kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=r"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "r"}]},
            {"id": "python", "owningModule": "cap-language-python", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["copilot", "kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=python"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "python"}]},
        ],
        "modules": [
            {"id": "kernel", "layer": "kernel", "displayName": "Kernel", "description": "k",
             "dependsOn": [], "ownedAssets": [".github/shared/*.contract.md"]},
            {"id": "cap-language-r", "layer": "capability", "displayName": "R", "description": "r",
             "dependsOn": ["kernel"], "ownedAssets": [".github/skills/cg-skill-r-*/"]},
            {"id": "cap-language-python", "layer": "capability", "displayName": "Py", "description": "p",
             "dependsOn": ["kernel"], "ownedAssets": []},
            {"id": "suite-cg", "layer": "suite", "displayName": "CG", "description": "cg",
             "dependsOn": ["kernel"], "ownedAssets": [".github/prompts/cg-*.prompt.md"]},
        ],
    }


def _repo_root(tmp_path: Path) -> Path:
    _write_json(tmp_path / ".github/shared/module-registry.json", _registry())
    _write_json(tmp_path / ".github/shared/target-mapping.json", _target_mapping())
    _create_file(tmp_path, ".github/skills/cg-skill-r-analytical/SKILL.md", "---\ndescription: R\n---\nbody\n")
    _create_file(tmp_path, ".github/prompts/cg-work.prompt.md", "---\ndescription: work\n---\nbody\n")
    _create_file(tmp_path, "compound-gpid.local.md", (
        "---\nlanguage: \"both\"\nproject-type: \"tool\"\nreview-depth: \"thorough\"\n"
        "suites: [cg]\n---\n# config\n"
    ))
    return tmp_path


class TestResolution:
    def test_resolve_produces_complete_manifest(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        resolved = manifest.resolve_active_manifest(root)
        assert manifest.validate_manifest(resolved) == []
        selection = resolved["selection"]
        assert selection["suites"] == ["cg"]
        assert "kernel" in selection["moduleClosure"]
        assert "suite-cg" in selection["moduleClosure"]
        assert selection["platforms"] == ["copilot", "kilo"]
        assert selection["configDigest"]
        assert selection["registryDigest"]
        assert selection["desiredPlanDigest"]
        assert resolved["catalogRecords"]

    def test_absent_suites_defaults_to_cg_once(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        config_path = root / "compound-gpid.local.md"
        config_path.write_text("---\nlanguage: \"both\"\n---\n# config\n", encoding="utf-8")
        resolved = manifest.resolve_active_manifest(root)
        assert resolved["selection"]["suites"] == ["cg"]
        assert resolved["selection"]["configSchemaVersion"] is None

    def test_restricted_language_selector_limits_closure(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        config_path = root / "compound-gpid.local.md"
        config_path.write_text("---\nlanguage: \"r\"\nsuites: [cg]\n---\n# config\n", encoding="utf-8")
        resolved = manifest.resolve_active_manifest(root)
        closure = resolved["selection"]["moduleClosure"]
        assert "cap-language-r" in closure
        assert "cap-language-python" not in closure

    def test_explicit_capability_augments_closure(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        config_path = root / "compound-gpid.local.md"
        config_path.write_text(
            "---\nlanguage: \"r\"\nsuites: [cg]\ncapabilities: [python]\n---\n# config\n",
            encoding="utf-8",
        )
        resolved = manifest.resolve_active_manifest(root)
        closure = resolved["selection"]["moduleClosure"]
        assert "cap-language-r" in closure
        assert "cap-language-python" in closure

    def test_unknown_explicit_capability_fails_closed(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        config_path = root / "compound-gpid.local.md"
        config_path.write_text(
            "---\nlanguage: \"r\"\nsuites: [cg]\ncapabilities: [sas]\n---\n# config\n",
            encoding="utf-8",
        )
        with pytest.raises(manifest.ManifestResolutionError, match="unknown explicit capability"):
            manifest.resolve_active_manifest(root)

    def test_unknown_platform_fails_closed(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        with pytest.raises(manifest.ManifestResolutionError, match="unknown platform"):
            manifest.resolve_active_manifest(root, platforms=["tablet"])

    def test_malformed_config_fails_closed(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        config_path = root / "compound-gpid.local.md"
        config_path.write_text("---\nunknown-key: \"x\"\n---\n# config\n", encoding="utf-8")
        with pytest.raises(manifest.ManifestResolutionError, match="unrecognized config key"):
            manifest.resolve_active_manifest(root)

    def test_platform_eligibility_reported(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        resolved = manifest.resolve_active_manifest(root)
        eligibility = resolved["platformEligibility"]
        assert eligibility["platforms"] == ["copilot", "kilo"]
        assert eligibility["allEligible"] is True


class TestDeterminismAndStaleness:
    def test_independent_runs_byte_stable(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        first = manifest.resolve_active_manifest(root)
        second = manifest.resolve_active_manifest(root)
        assert json.dumps(first["selection"], sort_keys=True) == json.dumps(second["selection"], sort_keys=True)
        assert manifest.manifest_stale(first, second) == []
        # The recorded generated/source stamps are evidence; the selection is
        # byte-stable and sourceRevision uses the deterministic sentinel in
        # non-git environments.
        assert second["selection"]["sourceRevision"] == "unknown-revision"
        first_clean = {k: v for k, v in first.items() if k not in ("generated",)}
        second_clean = {k: v for k, v in second.items() if k not in ("generated",)}
        assert manifest.canonical_manifest_bytes(first_clean) == manifest.canonical_manifest_bytes(second_clean)

    def test_config_change_detected_as_stale(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        committed = manifest.resolve_active_manifest(root)
        config_path = root / "compound-gpid.local.md"
        config_path.write_text("---\nlanguage: \"r\"\nsuites: [cg]\n---\n# config\n", encoding="utf-8")
        current = manifest.resolve_active_manifest(root)
        stale = manifest.manifest_stale(committed, current)
        assert "configDigest" in stale
        assert "desiredPlanDigest" in stale

    def test_platform_change_detected_as_stale(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        committed = manifest.resolve_active_manifest(root)
        current = manifest.resolve_active_manifest(root, platforms=["copilot"])
        stale = manifest.manifest_stale(committed, current)
        assert "platforms" in stale
        assert "desiredPlanDigest" in stale

    def test_registry_change_detected_as_stale(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        committed = manifest.resolve_active_manifest(root)
        registry_path = root / ".github/shared/module-registry.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["description"] = "changed"
        _write_json(registry_path, registry)
        current = manifest.resolve_active_manifest(root)
        stale = manifest.manifest_stale(committed, current)
        assert "registryDigest" in stale

    def test_ownership_drift_does_not_invalidate_selection(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        resolved = manifest.resolve_active_manifest(root)
        # A user-modified projected file only affects ownership state, never the
        # immutable selection record.
        ownership = root / ".compound-gpid/projection-ownership.json"
        ownership.parent.mkdir(parents=True, exist_ok=True)
        ownership.write_text('{"user-edited": true}', encoding="utf-8")
        again = manifest.resolve_active_manifest(root)
        assert manifest.validate_manifest(again) == []
        assert manifest.manifest_stale(resolved, again) == []
        assert ownership.read_text(encoding="utf-8").strip() == '{"user-edited": true}'


class TestValidation:
    def test_invalid_manifest_shape_fails_with_recovery_fields(self) -> None:
        errors = manifest.validate_manifest({"header": "wrong"})
        assert any("header" in error for error in errors)
        errors = manifest.validate_manifest({"header": manifest.HEADER, "selection": {}})
        assert any("selection missing" in error for error in errors)

    def test_non_dict_manifest_fails(self) -> None:
        errors = manifest.validate_manifest([])
        assert any("must be a JSON object" in error for error in errors)

    def test_wrong_typed_selection_fields_fail(self) -> None:
        resolved = {
            "header": manifest.HEADER,
            "selection": {
                "configDigest": "x",
                "registryDigest": "y",
                "registrySchemaVersion": "one",
                "sourceRevision": "s",
                "suites": "cg",
                "moduleClosure": ["kernel"],
                "platforms": ["kilo"],
                "desiredPlanDigest": "not-a-digest",
            },
        }
        errors = manifest.validate_manifest(resolved)
        assert any("must be an integer" in error for error in errors)
        assert any("must be a list of strings" in error for error in errors)
        assert any("64-char hex digest" in error for error in errors)

    def test_invalid_ownership_shape_fails(self) -> None:
        assert manifest.validate_ownership_state("not-an-object")
        assert manifest.validate_ownership_state({"schemaVersion": 9})
        assert manifest.validate_ownership_state({"schemaVersion": 1})  # missing entries

    def test_invalid_transaction_journal_fails(self) -> None:
        assert manifest.validate_transaction_journal("x")
        assert manifest.validate_transaction_journal({"schemaVersion": 9})

    def test_ensure_state_is_idempotent_and_never_overwrites(self, tmp_path: Path) -> None:
        root = _repo_root(tmp_path)
        resolved = manifest.resolve_active_manifest(root)
        manifest.ensure_managed_state(root, resolved)
        ownership = root / ".compound-gpid/projection-ownership.json"
        assert ownership.exists()
        original = ownership.read_text(encoding="utf-8")
        ownership.write_text('{"user": "content"}', encoding="utf-8")
        manifest.ensure_managed_state(root, resolved)
        assert ownership.read_text(encoding="utf-8").strip() == '{"user": "content"}'


class TestRealRepo:
    def test_real_repo_resolves_and_validates(self) -> None:
        resolved = manifest.resolve_active_manifest(REPO_ROOT)
        assert manifest.validate_manifest(resolved) == [], \
            manifest.validate_manifest(resolved)
        selection = resolved["selection"]
        assert {"suite-cg", "suite-cr"} <= set(selection["moduleClosure"])
        assert "cap-language-r" in selection["moduleClosure"]  # language: both
        assert selection["platforms"] == manifest.canonical_platform_ids(REPO_ROOT)
        assert resolved["certifiedKiloLaunchRequired"] is False
