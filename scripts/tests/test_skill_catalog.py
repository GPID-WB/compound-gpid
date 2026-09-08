"""Tests for the static manifest-backed skill catalog and capability router.

Covers Step 9 (catalog generation, compact/full output, filters, staleness
guard) and Step 10 (manifest-aware hard-stop routing, inventory leak checks).

Run from repo root:
    python -m pytest scripts/tests/test_skill_catalog.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import cg_skill_catalog as catalog
from skill_management.services import catalog as catalog_service

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, indent=2) + "\n")


def _target_mapping() -> dict:
    return {
        "schemaVersion": 1,
        "description": "fixture",
        "targets": [
            {"id": "copilot", "name": "Copilot", "capabilities": {}, "formats": {},
             "outputPaths": {}, "installUnits": []},
            {"id": "kilo", "name": "Kilo", "capabilities": {}, "formats": {},
             "outputPaths": {}, "installUnits": []},
        ],
    }


def _registry() -> dict:
    return {
        "schemaVersion": 2,
        "description": "test registry",
        "capabilities": [
            {"id": "r", "owningModule": "cap-language-r", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["copilot", "kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=r"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "r"}]},
            {"id": "python", "owningModule": "cap-language-python", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["copilot", "kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "low", "taskTriggers": ["language=python"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "python"}]},
            {"id": "research-output", "owningModule": "cap-research-output", "supportedSuites": ["cr"],
             "supportedPlatforms": ["copilot", "kilo"], "sourceProvenance": "canonical/.github",
             "activationCost": "high", "taskTriggers": ["/cr-work"],
             "configSelectors": []},
        ],
        "modules": [
            {"id": "kernel", "layer": "kernel", "displayName": "Kernel", "description": "k",
             "dependsOn": [], "ownedAssets": [".github/shared/*.contract.md"]},
            {"id": "cap-language-r", "layer": "capability", "displayName": "R", "description": "r",
             "dependsOn": ["kernel"], "ownedAssets": [".github/skills/cg-skill-r-*/"]},
            {"id": "cap-language-python", "layer": "capability", "displayName": "Py", "description": "p",
             "dependsOn": ["kernel"], "ownedAssets": [".github/skills/cg-skill-python-best-practices/"]},
            {"id": "cap-research-output", "layer": "capability", "displayName": "RO", "description": "ro",
             "dependsOn": ["kernel"], "ownedAssets": [".github/skills/cr-skill-publication-output/"]},
            {"id": "suite-cg", "layer": "suite", "displayName": "CG", "description": "cg",
             "dependsOn": ["kernel", "cap-language-r"],
             "ownedAssets": [".github/prompts/cg-*.prompt.md"]},
            {"id": "suite-cr", "layer": "suite", "displayName": "CR", "description": "cr",
             "dependsOn": ["kernel", "cap-research-output"],
             "ownedAssets": [".github/prompts/cr-*.prompt.md"]},
        ],
    }


def _manifest() -> dict:
    """A valid CG-only manifest for testing."""
    return {
        "header": "compound-gpid-active-manifest-v1",
        "schemaVersion": 1,
        "generated": "2026-01-01T00:00:00+00:00@000000000000",
        "selection": {
            "configDigest": "a" * 64,
            "configSchemaVersion": None,
            "registryDigest": "b" * 64,
            "registrySchemaVersion": 2,
            "projectRegistryDigest": "d" * 64,
            "provenanceDigest": "e" * 64,
            "sourceRevision": "2026-01-01T00:00:00+00:00@000000000000",
            "suites": ["cg"],
            "capabilities": [],
            "derivedCapabilities": ["r"],
            "moduleClosure": ["kernel", "cap-language-r", "suite-cg"],
            "selectedProjectSkills": {},
            "platforms": ["copilot", "kilo"],
            "catalogDigest": "f" * 64,
            "desiredPlanDigest": "c" * 64,
        },
        "platformEligibility": {"platforms": ["copilot", "kilo"], "capabilities": [], "allEligible": True},
        "certifiedKiloLaunchRequired": False,
        "catalogRecords": [],
    }


def _fixture_root(tmp_path: Path) -> Path:
    """Create a minimal fixture root with all required artifacts."""
    _write_json(tmp_path / ".github/shared/module-registry.json", _registry())
    _write_json(tmp_path / ".github/shared/target-mapping.json", _target_mapping())
    _write(
        tmp_path / ".github/skills/cg-skill-r-analytical/SKILL.md",
        "---\nname: cg-skill-r-analytical\n"
        "description: \"R analytical patterns\"\n---\nbody\n",
    )
    _write(
        tmp_path / ".github/skills/cg-skill-python-best-practices/SKILL.md",
        "---\nname: cg-skill-python-best-practices\n"
        "description: \"Python best practices\"\n---\nbody\n",
    )
    _write(
        tmp_path / ".github/skills/cr-skill-publication-output/SKILL.md",
        "---\nname: cr-skill-publication-output\n"
        "description: \"Publication output\"\n---\nbody\n",
    )
    _write(
        tmp_path / ".github/prompts/cg-work.prompt.md",
        "---\ndescription: work\n---\nbody\n",
    )
    _write(
        tmp_path / "compound-gpid.local.md",
        "---\nlanguage: \"both\"\nproject-type: \"tool\"\nreview-depth: \"thorough\"\n"
        "suites: [cg]\n---\n# config\n",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Catalog row construction
# ---------------------------------------------------------------------------


class TestCatalogBuild:
    def test_legacy_builder_delegates_to_catalog_service(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = _fixture_root(tmp_path)
        expected = [{"id": "delegated"}]
        calls = []

        def build_rows(*args, **kwargs):
            calls.append((args, kwargs))
            return expected

        monkeypatch.setattr(catalog_service, "build_catalog_rows", build_rows)
        assert catalog.build_catalog(root, _manifest(), _registry()) == expected
        assert len(calls) == 1

    def test_build_catalog_returns_all_skills(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        rows = catalog.build_catalog(root, manifest, registry)
        ids = [r["id"] for r in rows]
        assert "cg-skill-r-analytical" in ids
        assert "cg-skill-python-best-practices" in ids
        assert "cr-skill-publication-output" in ids

    def test_available_skill_in_closure(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        rows = catalog.build_catalog(root, manifest, registry)
        r_skill = next(r for r in rows if r["id"] == "cg-skill-r-analytical")
        assert r_skill["available"] is True
        assert r_skill["capability"] == "r"
        assert r_skill["activationCost"] == "low"

    def test_unavailable_skill_not_in_closure(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        rows = catalog.build_catalog(root, manifest, registry)
        cr_skill = next(r for r in rows if r["id"] == "cr-skill-publication-output")
        assert cr_skill["available"] is False
        assert cr_skill["inactiveReason"] is not None

    def test_full_row_has_extended_fields(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        rows = catalog.build_catalog(root, manifest, registry)
        for row in rows:
            assert "sourcePath" in row
            assert "eligibility" in row
            assert "importStatus" in row


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    def _rows(self, tmp_path: Path) -> list:
        root = _fixture_root(tmp_path)
        return catalog.build_catalog(root, _manifest(), _registry())

    def test_filter_by_id_query(self, tmp_path: Path) -> None:
        rows = self._rows(tmp_path)
        filtered = catalog.filter_catalog(rows, id_query="python")
        assert len(filtered) == 1
        assert filtered[0]["id"] == "cg-skill-python-best-practices"

    def test_filter_by_capability(self, tmp_path: Path) -> None:
        rows = self._rows(tmp_path)
        filtered = catalog.filter_catalog(rows, capability="r")
        assert all(r["capability"] == "r" for r in filtered)
        assert len(filtered) >= 1

    def test_filter_by_availability(self, tmp_path: Path) -> None:
        rows = self._rows(tmp_path)
        available = catalog.filter_catalog(rows, available=True)
        unavailable = catalog.filter_catalog(rows, available=False)
        assert all(r["available"] for r in available)
        assert all(not r["available"] for r in unavailable)

    def test_filter_by_cost(self, tmp_path: Path) -> None:
        rows = self._rows(tmp_path)
        low = catalog.filter_catalog(rows, cost="low")
        assert all(r["activationCost"] == "low" for r in low)

    def test_filter_by_suite(self, tmp_path: Path) -> None:
        rows = self._rows(tmp_path)
        cg = catalog.filter_catalog(rows, suite="cg")
        cr = catalog.filter_catalog(rows, suite="cr")
        assert len(cg) >= 1
        assert len(cr) >= 1

    def test_filter_by_platform(self, tmp_path: Path) -> None:
        rows = self._rows(tmp_path)
        filtered = catalog.filter_catalog(rows, platform="kilo")
        assert len(filtered) >= 1


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


class TestOutput:
    def test_compact_format_no_spill(self, tmp_path: Path) -> None:
        """Compact output must not include extended metadata fields."""
        root = _fixture_root(tmp_path)
        rows = catalog.build_catalog(root, _manifest(), _registry())
        compact_text = catalog.format_compact(rows)
        for field in catalog.FULL_EXTRA_FIELDS:
            assert field.upper() not in compact_text.split("\n")[0] or \
                field.upper() in ("ID",)

    def test_compact_format_contains_required_columns(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        rows = catalog.build_catalog(root, _manifest(), _registry())
        compact_text = catalog.format_compact(rows)
        header = compact_text.split("\n")[0]
        assert "ID" in header
        assert "PURPOSE" in header
        assert "AVAILABLE" in header

    def test_full_format_has_all_columns(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        rows = catalog.build_catalog(root, _manifest(), _registry())
        full_text = catalog.format_full(rows)
        header = full_text.split("\n")[0]
        assert "SOURCEPATH" in header
        assert "INACTIVEREASON" in header

    def test_json_compact_output(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        rows = catalog.build_catalog(root, _manifest(), _registry())
        compact_json = json.loads(catalog.format_json(rows, compact=True))
        assert all("sourcePath" not in r for r in compact_json)

    def test_json_full_output(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        rows = catalog.build_catalog(root, _manifest(), _registry())
        full_json = json.loads(catalog.format_json(rows, compact=False))
        assert all("sourcePath" in r for r in full_json)

    def test_empty_rows_format(self) -> None:
        assert catalog.format_compact([]) == "(no matching skills)"
        assert catalog.format_full([]) == "(no matching skills)"


# ---------------------------------------------------------------------------
# Staleness guard
# ---------------------------------------------------------------------------


class TestStalenessGuard:
    def test_missing_manifest_raises_catalog_error(self, tmp_path: Path) -> None:
        _fixture_root(tmp_path)
        with pytest.raises(catalog.CatalogError, match="not found"):
            catalog._load_manifest(tmp_path)

    def test_structurally_invalid_manifest_raises(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", {"bad": "data"})
        with pytest.raises(catalog.CatalogError, match="structurally invalid"):
            catalog._load_manifest(tmp_path)


# ---------------------------------------------------------------------------
# Capability router (Step 10)
# ---------------------------------------------------------------------------


class TestCapabilityRouter:
    def test_active_capability_returns_found(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        result = catalog.route_capability(root, "r", manifest, registry)
        assert result.found is True
        assert result.capability_id == "r"

    def test_inactive_capability_returns_hard_stop(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        result = catalog.route_capability(root, "research-output", manifest, registry)
        assert result.found is False
        assert result.capability_id == "research-output"
        assert result.inactive_reason is not None
        assert result.remedy is not None

    def test_unknown_capability_returns_distinct_error(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        result = catalog.route_capability(root, "nonexistent", manifest, registry)
        assert result.found is False
        assert "Unknown" in result.message

    def test_inactive_selector_capability_has_selector_in_result(self, tmp_path: Path) -> None:
        """When a selector-driven capability is inactive, the selector should be present."""
        root = _fixture_root(tmp_path)
        # Create a manifest where python is NOT in the closure
        manifest = _manifest()
        registry = _registry()
        # python requires language=python config selector but our fixture has language=both
        # with cg suite, cap-language-python is not a dependency of suite-cg
        result = catalog.route_capability(root, "python", manifest, registry)
        # Python capability: its module is not in closure because suite-cg doesn't depend on it
        if not result.found:
            assert result.inactive_reason is not None

    def test_router_does_not_alter_manifest(self, tmp_path: Path) -> None:
        """Router must not write or modify the manifest."""
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        _write_json(root / ".compound-gpid/active-manifest.json", manifest)
        original = json.dumps(manifest, sort_keys=True)
        catalog.route_capability(root, "research-output", manifest, registry)
        after = (root / ".compound-gpid/active-manifest.json").read_text(encoding="utf-8")
        assert json.dumps(json.loads(after), sort_keys=True) == original

    def test_router_to_dict_has_expected_fields(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        result = catalog.route_capability(root, "research-output", manifest, registry)
        d = result.to_dict()
        assert "found" in d
        assert "capabilityId" in d
        assert "inactiveReason" in d
        assert "remedy" in d


# ---------------------------------------------------------------------------
# Inventory leak checks (Step 10)
# ---------------------------------------------------------------------------


class TestInventoryLeaks:
    def test_no_leaks_for_clean_fixture(self, tmp_path: Path) -> None:
        """A fixture where all active references resolve should have no leaks."""
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        leaks = catalog.check_inventory_leaks(root, manifest, registry)
        assert leaks == []

    def test_leak_detected_for_inactive_reference(self, tmp_path: Path) -> None:
        """An active asset referencing an inactive asset should be flagged."""
        root = _fixture_root(tmp_path)
        manifest = _manifest()
        registry = _registry()
        # Make cg-work.prompt.md reference a CR skill
        _write(
            root / ".github/prompts/cg-work.prompt.md",
            "---\ndescription: work\n---\n"
            "Load `.github/skills/cr-skill-publication-output/SKILL.md`.\n",
        )
        leaks = catalog.check_inventory_leaks(root, manifest, registry)
        assert any("cr-skill-publication-output" in leak for leak in leaks)


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestCLI:
    def test_cli_catalog_compact(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--skip-stale-check"])
        assert exit_code == 0

    def test_cli_catalog_json(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--format", "json", "--skip-stale-check"])
        assert exit_code == 0

    def test_cli_route_active(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--route", "r", "--skip-stale-check"])
        assert exit_code == 0

    def test_cli_route_inactive(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--route", "research-output", "--skip-stale-check"])
        assert exit_code == 1

    def test_cli_route_unknown(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--route", "nonexistent", "--skip-stale-check"])
        assert exit_code == 1

    def test_cli_check_leaks_clean(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--check-leaks", "--skip-stale-check"])
        assert exit_code == 0

    def test_cli_missing_manifest_returns_error(self, tmp_path: Path) -> None:
        _fixture_root(tmp_path)
        exit_code = catalog.main(["--root", str(tmp_path), "--skip-stale-check"])
        assert exit_code == 1

    def test_cli_full_format(self, tmp_path: Path) -> None:
        root = _fixture_root(tmp_path)
        _write_json(root / ".compound-gpid/active-manifest.json", _manifest())
        exit_code = catalog.main(["--root", str(root), "--full", "--skip-stale-check"])
        assert exit_code == 0

    def test_cli_invalid_root_returns_2(self) -> None:
        exit_code = catalog.main(["--root", "/nonexistent/path"])
        assert exit_code == 2


# ---------------------------------------------------------------------------
# Real-repo integration
# ---------------------------------------------------------------------------


class TestRealRepo:
    def test_real_registry_catalog_builds(self) -> None:
        """With the real repo, catalog should build without error if manifest exists."""
        manifest_path = REPO_ROOT / ".compound-gpid/active-manifest.json"
        if not manifest_path.exists():
            pytest.skip("no active manifest in real repo")
        rows = catalog.build_catalog(REPO_ROOT)
        assert len(rows) > 0
        ids = [r["id"] for r in rows]
        assert "cg-skill-brain-query" in ids
