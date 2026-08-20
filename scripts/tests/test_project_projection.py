"""Tests for the manifest-driven project projection planner (Phase 3, step 6).

Run from repo root:
    python -m pytest scripts/tests/test_project_projection.py -q
"""
from __future__ import annotations

import copy
import json
import os
import shutil
from pathlib import Path

import pytest

import cg_project_projection as projection
import cg_project_manifest as manifest_module


REPO_ROOT = Path(__file__).resolve().parents[2]
NATIVE_TARGETS = ("claude-code", "codex", "opencode", "kilo")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _real_registry(root: Path) -> None:
    """Copy the real module registry and a minimal v2-compatible registry fixture."""
    _write_json(root / ".github/shared/module-registry.json", {
        "schemaVersion": 2,
        "description": "fixture registry",
        "capabilities": [
            {"id": "r", "owningModule": "cap-language-r", "supportedSuites": ["cg", "cr"],
             "supportedPlatforms": ["kilo", "opencode", "claude-code", "codex", "copilot"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "r"}]},
            {"id": "python", "owningModule": "cap-language-python",
             "supportedSuites": ["cg", "cr"], "supportedPlatforms": ["kilo"],
             "configSelectors": [{"field": "language", "operator": "contains", "value": "python"}]},
        ],
        "modules": [
            {"id": "kernel", "layer": "kernel", "displayName": "Kernel", "description": "k",
             "dependsOn": [], "ownedAssets": [".github/shared/*.contract.md"]},
            {"id": "cap-language-r", "layer": "capability", "displayName": "R", "description": "r",
             "dependsOn": ["kernel"], "ownedAssets": [".github/skills/cg-skill-r-*/"]},
            {"id": "cap-language-python", "layer": "capability", "displayName": "Py", "description": "p",
             "dependsOn": ["kernel"], "ownedAssets": [".github/skills/cg-skill-python-*/"]},
            {"id": "suite-cg", "layer": "suite", "displayName": "CG", "description": "cg",
             "dependsOn": ["cap-language-r"], "ownedAssets": [
                 ".github/prompts/cg-*.prompt.md", ".github/agents/cg-*.agent.md",
                 ".github/skills/cg-skill-brain-query/", ".github/instructions/r.instructions.md"]},
            {"id": "suite-cr", "layer": "suite", "displayName": "CR", "description": "cr",
             "dependsOn": ["cap-language-r"], "ownedAssets": [
                 ".github/prompts/cr-*.prompt.md", ".github/agents/cr-*.agent.md",
                 ".github/skills/cr-skill-evidence/", ".github/instructions/r.instructions.md"]},
        ],
    })


def _small_mapping(root: Path) -> None:
    """A minimal target mapping covering all native platforms plus copilot."""
    gtp_by_id = {
        "copilot": None,
        "claude-code": ".claude",
        "codex": ".agents",
        "opencode": ".opencode",
        "kilo": ".kilo",
    }
    targets = []
    for tid, gtp in gtp_by_id.items():
        output = {
            "commands": f"{gtp}/commands" if gtp else ".github/prompts",
            "skills": f"{gtp}/skills" if gtp else ".github/skills",
            "agents": f"{gtp}/agents" if gtp else ".github/agents",
            "instructions": f"{gtp}/instructions" if gtp else ".github/instructions",
            "shared": f"{gtp}/shared" if gtp else ".github/shared",
        }
        if gtp:
            output["rootAdapter"] = {
                "claude-code": ".claude/CLAUDE.md",
                "codex": ".agents/AGENTS.md",
                "opencode": ".opencode/AGENTS.md",
                "kilo": ".kilo/AGENTS.md",
            }[tid]
            if tid in ("opencode", "kilo"):
                output["config"] = f"{gtp}/{tid}.json"
        target = {
            "id": tid,
            "name": tid,
            "generatedTreePath": gtp,
            "capabilities": {
                f: True for f in (
                    "supportsNativeCommands", "supportsNativeSkills",
                    "supportsNativeSubagents", "supportsMultiVendorModels",
                    "requiresRootAdapter",
                )
            },
            "formats": {
                "commandFormat": f"{tid}-command",
                "skillFormat": f"{tid}-skill",
                "agentFormat": f"{tid}-agent",
            },
            "outputPaths": output,
            "installUnits": [],
        }
        if gtp:
            target["projectRoots"] = {"managed": [gtp], "optionalUser": []}
        targets.append(target)
    _write_json(root / ".github/shared/target-mapping.json", {
        "schemaVersion": 1,
        "description": "fixture target mapping",
        "targets": targets,
    })


def _canonical_assets(root: Path) -> None:
    _write(root / ".github/prompts/cg-work.prompt.md", "---\ndescription: work\n---\nbody\n")
    _write(root / ".github/prompts/cr-work.prompt.md", "---\ndescription: cr work\n---\nbody\n")
    _write(root / ".github/agents/cg-agent.agent.md", "---\ndescription: agent\n---\nbody\n")
    _write(root / ".github/agents/cr-agent.agent.md", "---\ndescription: cr agent\n---\nbody\n")
    _write(root / ".github/skills/cg-skill-r-analytical/SKILL.md", "---\ndescription: R\n---\nbody\n")
    _write(root / ".github/skills/cg-skill-python-core/SKILL.md", "---\ndescription: Py\n---\nbody\n")
    _write(root / ".github/skills/cr-skill-evidence/SKILL.md", "---\ndescription: CR\n---\nbody\n")
    _write(root / ".github/instructions/r.instructions.md", "# R\n")
    _write(root / ".github/shared/context-loading.contract.md", "# ctx\n")


def _repo_root(tmp_path: Path, *, suites: str = "[cg]", languages: str = "r",
               platforms: str = "kilo") -> tuple[Path, dict]:
    root = tmp_path / "source"
    _real_registry(root)
    _small_mapping(root)
    _canonical_assets(root)
    _write(root / "compound-gpid.local.md", (
        f"---\nlanguage: \"{languages}\"\nsuites: {suites}\n"
        f"---\n# config\n"
    ))
    resolved = manifest_module.resolve_active_manifest(root, platforms=platforms.split(","))
    manifest_module.ensure_managed_state(root, resolved)
    (root / ".compound-gpid").mkdir(parents=True, exist_ok=True)
    (root / ".compound-gpid/active-manifest.json").write_text(
        manifest_module.canonical_manifest_bytes(resolved), encoding="utf-8"
    )
    return root, resolved


class TestPlanOnlyReadsManifest:
    def test_plan_is_pure_and_side_effect_free(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path)
        mapping = projection.load_target_mapping(root)
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root), mapping=mapping)
        assert isinstance(plan, projection.ProjectionPlan)
        # Nothing was written to the filesystem.
        assert not (root / ".claude").exists()
        assert not (root / ".kilo").exists()

    def test_platforms_come_exclusively_from_manifest(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo,opencode")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        assert set(plan.platforms) == {"kilo", "opencode"}
        assert set(plan.by_platform) == {"kilo", "opencode"}

    def test_kilo_only_manifest_cannot_emit_another_target(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        destinations = {entry.destination for entry in plan.entries}
        assert all(dest.startswith(".kilo/") for dest in destinations)
        assert not any(dest.startswith(".claude/") for dest in destinations)
        assert not any(dest.startswith(".agents/") for dest in destinations)
        assert not any(dest.startswith(".opencode/") for dest in destinations)

    def test_manifest_digest_and_desired_plan_digest_recorded(self, tmp_path: Path) -> None:
        root, resolved = _repo_root(tmp_path)
        plan = projection.build_projection_plan(root, resolved)
        assert plan.desired_plan_digest == resolved["selection"]["desiredPlanDigest"]
        assert len(plan.manifest_digest) == 64

    def test_unknown_platform_fails_closed(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path)
        manifest = projection.load_active_manifest(root)
        manifest["selection"]["platforms"] = ["tablet"]
        manifest["selection"]["desiredPlanDigest"] = "0" * 64
        with pytest.raises(projection.ProjectionError, match="unknown platform"):
            projection.build_projection_plan(root, manifest)

    def test_missing_active_manifest_fails(self, tmp_path: Path) -> None:
        root = tmp_path / "empty"
        root.mkdir()
        with pytest.raises(projection.ProjectionError, match="not found"):
            projection.load_active_manifest(root)

    def test_unknown_capability_fails_closed(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path)
        manifest = projection.load_active_manifest(root)
        manifest["selection"]["capabilities"] = ["sas-quantiles"]
        with pytest.raises(projection.ProjectionError, match="unknown capability"):
            projection.build_projection_plan(root, manifest)

    def test_detached_capability_fails_closed(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path)
        manifest = projection.load_active_manifest(root)
        # Register an unknown explicit capability so its owner is not in closure.
        manifest["selection"]["capabilities"] = ["python"]
        manifest["selection"]["moduleClosure"] = [
            m for m in manifest["selection"]["moduleClosure"] if m != "cap-language-python"
        ]
        with pytest.raises(projection.ProjectionError, match="not in the resolved module closure"):
            projection.build_projection_plan(root, manifest)

    def test_output_collision_fails_during_planning(self, tmp_path: Path) -> None:
        root, manifest = _repo_root(tmp_path, platforms="kilo")
        mapping = projection.load_target_mapping(root)
        for target in mapping["targets"]:
            if target["id"] == "kilo":
                target["outputPaths"]["commands"] = ".kilo/skills"
        with pytest.raises(projection.ProjectionError):
            projection.build_projection_plan(root, manifest, mapping=mapping)


class TestClosureFiltering:
    def test_distinct_inventories_per_profile(self, tmp_path: Path) -> None:
        cg_root = tmp_path / "cg"
        _real_registry(cg_root)
        _small_mapping(cg_root)
        _canonical_assets(cg_root)
        _write(cg_root / "compound-gpid.local.md", '---\nlanguage: "r"\nsuites: [cg]\n---\n# config\n')
        cg_manifest = manifest_module.resolve_active_manifest(cg_root, platforms=["kilo"])
        cg_plan = projection.build_projection_plan(cg_root, cg_manifest)

        cr_root = tmp_path / "cr"
        _real_registry(cr_root)
        _small_mapping(cr_root)
        _canonical_assets(cr_root)
        _write(cr_root / "compound-gpid.local.md", '---\nlanguage: "r"\nsuites: [cr]\n---\n# config\n')
        cr_manifest = manifest_module.resolve_active_manifest(cr_root, platforms=["kilo"])
        cr_plan = projection.build_projection_plan(cr_root, cr_manifest)

        cg_names = {entry.destination for entry in cg_plan.entries}
        cr_names = {entry.destination for entry in cr_plan.entries}
        assert any(name.startswith(".kilo/commands/cg-") for name in cg_names)
        assert any(name.startswith(".kilo/commands/cr-") for name in cr_names)
        assert cg_names != cr_names

    def test_inactive_assets_absent_from_plan(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo", suites="[cg]", languages="r")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        destinations = {entry.destination for entry in plan.entries}
        # cr skills and prompts are not in the cg+r closure.
        assert not any(name.startswith(".kilo/skills/cr-skill-") for name in destinations)
        assert not any(name.startswith(".kilo/skills/cg-skill-python-") for name in destinations)
        assert not any(name.startswith(".kilo/commands/cr-") for name in destinations)

    def test_capability_augments_inventory(self, tmp_path: Path) -> None:
        root = tmp_path / "with-py"
        _real_registry(root)
        _small_mapping(root)
        _canonical_assets(root)
        _write(root / "compound-gpid.local.md",
               '---\nlanguage: "r"\nsuites: [cg]\ncapabilities: [python]\n---\n# config\n')
        manifest = manifest_module.resolve_active_manifest(root, platforms=["kilo"])
        plan = projection.build_projection_plan(root, manifest)
        destinations = {entry.destination for entry in plan.entries}
        assert any(name.startswith(".kilo/skills/cg-skill-python-") for name in destinations)


class TestFullProfileByteParity:
    def test_full_profile_preserves_current_target_output(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms=",".join(NATIVE_TARGETS))
        manifest = projection.load_active_manifest(root)
        plan = projection.build_projection_plan(root, manifest)

        mapping = projection.load_target_mapping(root)
        restricted = {
            "schemaVersion": 1,
            "description": "full",
            "targets": [t for t in mapping["targets"] if t["id"] in NATIVE_TARGETS],
        }
        assets = projection._load_canonical_assets(root, manifest)
        generation_plan = __import__("cg_generate_targets", fromlist=["build_generation_plan"]).build_generation_plan(
            root, restricted, assets
        )
        full_entries = {entry.destination: entry.content for entry in generation_plan.entries}
        planned = {entry.destination: entry.content for entry in plan.entries}
        assert planned == full_entries


class TestDeclaredRootsValidation:
    def test_managed_optional_collision_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "source"
        _real_registry(root)
        _small_mapping(root)
        _canonical_assets(root)
        mapping = projection.load_target_mapping(root)
        # Make copilot's optional user root collide with kilo's managed root.
        for target in mapping["targets"]:
            if target["id"] == "copilot":
                target["projectRoots"] = {"managed": [], "optionalUser": [".kilo"]}
        with pytest.raises(projection.ProjectionError, match="collision"):
            projection.validate_declared_roots(mapping)

    def test_unsafe_root_rejected(self, tmp_path: Path) -> None:
        mapping = {"targets": [{"id": "x", "projectRoots": {"managed": ["../escape"], "optionalUser": []}}]}
        with pytest.raises(projection.ProjectionError, match="traversal|escape"):
            projection.validate_declared_roots(mapping)


class TestStagingAndVerify:
    def test_publish_and_verify_round_trip(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        manifest = projection.load_active_manifest(root)
        plan = projection.build_projection_plan(root, manifest)
        ownership = projection.publish_projection(root, plan)
        assert ownership["schemaVersion"] == 1
        problems = projection.verify_projection(root)
        assert problems == []

    def test_publish_is_recoverable_noop_after_commit(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        assert projection.recover_projection(root) != {}

    def test_full_suite_publish_many_platforms(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms=",".join(NATIVE_TARGETS))
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        ownership = projection.publish_projection(root, plan)
        for platform in NATIVE_TARGETS:
            assert ownership["activeAdapters"][platform]

    def test_publish_materializes_live_project_root(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        assert (root / ".kilo/commands/cg-work.md").exists()
        assert (root / ".kilo/AGENTS.md").exists()
        assert (root / ".kilo/skills/cg-skill-r-analytical/SKILL.md").exists()


class TestSynchronizer:
    def test_modified_managed_file_is_preserved(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        managed = root / ".kilo/commands/cg-work.md"
        original = managed.read_bytes()
        managed.write_bytes(b"user-modified-content")
        second = projection.build_projection_plan(root, projection.load_active_manifest(root))
        ownership = projection.publish_projection(root, second)
        # The user's edit is preserved AND it is dropped from the new ownership
        # map (so it can never be silently deleted later).
        assert managed.read_bytes() == b"user-modified-content"
        assert ".kilo/commands/cg-work.md" not in ownership.get("entries", {})
        # The original content never reappears over the user's edit.
        assert managed.read_bytes() != original

    def test_unchanged_stale_managed_file_is_removed(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        stale = root / ".kilo/commands/cg-work.md"
        _ = stale  # stays current; ownership records it as managed
        second = projection.build_projection_plan(root, projection.load_active_manifest(root))
        # Force the second plan to drop cg-work by removing the source prompt.
        (root / ".github/prompts/cg-work.prompt.md").unlink()
        rebuilt = manifest_module.resolve_active_manifest(root, platforms=["kilo"])
        ownership = projection.publish_projection(root, projection.build_projection_plan(root, rebuilt))
        assert not stale.exists()
        assert ".kilo/commands/cg-work.md" not in ownership.get("entries", {})

    def test_stale_modified_file_is_preserved(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        stale = root / ".kilo/commands/cg-work.md"
        stale.write_bytes(b"user-modified")
        (root / ".github/prompts/cg-work.prompt.md").unlink()
        rebuilt = manifest_module.resolve_active_manifest(root, platforms=["kilo"])
        projection.publish_projection(root, projection.build_projection_plan(root, rebuilt))
        assert stale.read_bytes() == b"user-modified"

    @pytest.mark.usefixtures("require_symlink_support")
    def test_destination_symlink_swap_is_rejected(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        outside = tmp_path / "outside.md"
        outside.write_bytes(b"outside")
        leafter = root / ".kilo/commands/cg-work.md"
        leafter.unlink()
        leafter.symlink_to(outside)
        with pytest.raises((projection.ProjectionError, OSError), match="link|reparse"):
            projection.publish_projection(root, projection.build_projection_plan(root, projection.load_active_manifest(root)))

    def test_hard_link_destination_is_rejected(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        target = tmp_path / "original.md"
        target.write_bytes(b"hard-linked-content")
        leaf = root / ".kilo/commands/cg-work.md"
        leaf.unlink()
        try:
            os.link(str(target), str(leaf))
        except (OSError, NotImplementedError):
            pytest.skip("hard links unavailable on this host")
        with pytest.raises(projection.ProjectionError, match="hard link"):
            projection.publish_projection(root, projection.build_projection_plan(root, projection.load_active_manifest(root)))


class TestInterruptionRecovery:
    TX_1 = "a" * 32
    TX_2 = "b" * 32
    TX_3 = "c" * 32

    def test_crash_before_first_pointer_switch_recovers_coherent(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        tx_id = self.TX_1
        projection.recover_projection(root)
        staging = projection._stage_tree(root, plan, tx_id)
        journal = {
            "schemaVersion": 1,
            "state": "prepared",
            "transactionId": tx_id,
            "platforms": {
                "kilo": {
                    "root": ".kilo",
                    "plannedHashes": {e.destination: e.sha256 for e in plan.by_platform["kilo"]},
                    "state": "staged",
                }
            },
        }
        projection._write_managed_json(root, projection.TRANSACTION_JOURNAL_PATH, journal)
        # Simulate crash: there is NO generation dir (rename never happened).
        st = staging
        assert st.is_dir()
        # Recovery sees a prepared journal with no generation; it rolls back.
        projection.recover_projection(root)
        assert not (root / projection.GENERATIONS_DIRNAME / tx_id).exists()
        assert projection._read_managed_json(root, projection.TRANSACTION_JOURNAL_PATH).get("state") == "rolled-back"

    def test_crash_between_platform_switches_rolls_back(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms=",".join(NATIVE_TARGETS))
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        tx_id = self.TX_2
        staging = projection._stage_tree(root, plan, tx_id)
        gen_dir = root / projection.GENERATIONS_DIRNAME / tx_id
        gen_dir.mkdir(parents=True, exist_ok=True)
        # Only kilo got renamed into the generation (simulated partial publish).
        os.rename(str(staging / ".kilo"), str(gen_dir / ".kilo"))
        # Journal records all platforms, generation only partially present -> rollback.
        journal = {
            "schemaVersion": 1,
            "state": "prepared",
            "transactionId": tx_id,
            "platforms": {
                p: {"root": f".{p}" if p != "claude-code" else ".claude",
                    "plannedHashes": {e.destination: e.sha256 for e in plan.by_platform[p]},
                    "state": "staged"}
                for p in plan.platforms
            },
        }
        projection._write_managed_json(root, projection.TRANSACTION_JOURNAL_PATH, journal)
        projection.recover_projection(root)
        assert not (root / projection.GENERATIONS_DIRNAME / tx_id).exists()
        assert projection._read_managed_json(root, projection.TRANSACTION_JOURNAL_PATH).get("state") == "rolled-back"

    def test_crash_after_last_switch_before_commit_completes(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        tx_id = self.TX_3
        staging = projection._stage_tree(root, plan, tx_id)
        gen_dir = root / projection.GENERATIONS_DIRNAME / tx_id
        gen_dir.mkdir(parents=True, exist_ok=True)
        os.rename(str(staging / ".kilo"), str(gen_dir / ".kilo"))
        journal = {
            "schemaVersion": 1,
            "state": "prepared",
            "transactionId": tx_id,
            "platforms": {
                "kilo": {
                    "root": ".kilo",
                    "plannedHashes": {e.destination: e.sha256 for e in plan.by_platform["kilo"]},
                    "state": "staged",
                }
            },
        }
        projection._write_managed_json(root, projection.TRANSACTION_JOURNAL_PATH, journal)
        projection.recover_projection(root)
        assert projection._read_managed_json(root, projection.TRANSACTION_JOURNAL_PATH).get("state") == "committed"
        assert (root / ".kilo/commands/cg-work.md").exists()

    def test_invalid_transaction_id_fails_closed(self, tmp_path: Path) -> None:
        """A crafted journal transactionId must never resolve a path or delete."""
        root, _ = _repo_root(tmp_path, platforms="kilo")
        marker = root / "keep-me.txt"
        marker.write_text("precious")
        journal = {
            "schemaVersion": 1,
            "state": "prepared",
            "transactionId": "../..",
            "platforms": {"kilo": {"root": "nope", "state": "staged"}},
        }
        projection._write_managed_json(root, projection.TRANSACTION_JOURNAL_PATH, journal)
        with pytest.raises(projection.ProjectionError, match="invalid transactionId"):
            projection.recover_projection(root)
        assert marker.exists()
        assert root.exists()

    def test_journal_root_escape_fails_closed(self, tmp_path: Path) -> None:
        """A generations dir symlinked outside containment is refused."""
        root, _ = _repo_root(tmp_path, platforms="kilo")
        outside = root / "keep.md"
        outside.write_text("precious")
        tx_id = "d" * 32
        generations_dir = root / projection.GENERATIONS_DIRNAME
        if generations_dir.exists() and not generations_dir.is_symlink():
            _remove_tree_no_follow(generations_dir)
        poison = root.parent / "poison-generations"
        poison.mkdir(exist_ok=True)
        (poison / "poison.md").write_text("poison")
        try:
            generations_dir.symlink_to(poison)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unavailable on this host")
        journal = {
            "schemaVersion": 1,
            "state": "prepared",
            "transactionId": tx_id,
            "platforms": {"kilo": {"root": ".kilo", "state": "staged"}},
        }
        projection._write_managed_json(root, projection.TRANSACTION_JOURNAL_PATH, journal)
        with pytest.raises(projection.ProjectionError, match="generation"):
            projection.recover_projection(root)
        assert outside.exists()
        assert (poison / "poison.md").read_text() == "poison"
        assert (root / "keep.md").exists()

    def test_journal_planned_destination_escape_fails_closed(self, tmp_path: Path) -> None:
        """Recovery completion must reject planned destinations outside the root."""
        root, _ = _repo_root(tmp_path, platforms="kilo")
        tx_id = "e" * 32
        gen_dir = root / projection.GENERATIONS_DIRNAME / tx_id
        # Fabricate a generation arena with a file outside any declared root.
        (gen_dir / ".kilo").mkdir(parents=True)
        outside = root / "compound-gpid.md"
        outside.write_text("# charter\n")
        evil = gen_dir / ".kilo" / "escape.md"
        evil.write_text("evil")
        journal = {
            "schemaVersion": 1,
            "state": "prepared",
            "transactionId": tx_id,
            "platforms": {
                "kilo": {
                    "root": ".kilo",
                    "plannedHashes": {
                        ".kilo/escape.md": projection._regular_file_hash(evil),
                        # A destination outside the platform root is rejected.
                        "../compound-gpid.md": projection._regular_file_hash(outside),
                    },
                    "state": "staged",
                }
            },
        }
        projection._write_managed_json(root, projection.TRANSACTION_JOURNAL_PATH, journal)
        with pytest.raises(projection.ProjectionError, match="invalid|outside|unsafe|escape"):
            projection.recover_projection(root)
        assert outside.exists()

    def test_rejected_publish_leaves_recoverable_journal(self, tmp_path: Path) -> None:
        """A rejected publish (link/hard-link) must not wedge the journal."""
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        target = tmp_path / "original.md"
        target.write_bytes(b"hard-linked-content")
        leaf = root / ".kilo/commands/cg-work.md"
        leaf.unlink()
        try:
            os.link(str(target), str(leaf))
        except (OSError, NotImplementedError):
            pytest.skip("hard links unavailable on this host")
        with pytest.raises(projection.ProjectionError, match="hard link"):
            projection.publish_projection(root, projection.build_projection_plan(root, projection.load_active_manifest(root)))
        # The journal must not be left prepared; the next sync must succeed.
        journal = projection._read_managed_json(root, projection.TRANSACTION_JOURNAL_PATH)
        assert journal.get("state") != "prepared"
        projection.recover_projection(root)
        assert projection._read_managed_json(root, projection.TRANSACTION_JOURNAL_PATH).get("state") != "prepared"

    def test_cross_platform_republish_does_not_delete_other_platform(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo,opencode")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        opencode_file = root / ".opencode/commands/cg-work.md"
        assert opencode_file.exists()
        # Republish with the same plan; opencode files must survive the kilo step.
        again = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, again)
        assert opencode_file.exists()
        kilo_file = root / ".kilo/commands/cg-work.md"
        assert kilo_file.exists()

    def test_first_publish_preserves_user_file(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        destination = root / ".kilo/commands/cg-work.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"user-authored-content")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        ownership = projection.publish_projection(root, plan)
        assert destination.read_bytes() == b"user-authored-content"
        warnings = ownership.get("warnings", [])
        assert any("user-owned" in warning for warning in warnings)
        assert ".kilo/commands/cg-work.md" not in ownership.get("entries", {})


class TestVerifyDrift:
    def test_drifted_projected_file_is_reported(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        managed = root / ".kilo/commands/cg-work.md"
        managed.write_bytes(b"user-drift")
        problems = projection.verify_projection(root)
        assert any("drifted" in problem for problem in problems)

    def test_absent_owned_file_is_reported(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        managed = root / ".kilo/commands/cg-work.md"
        managed.unlink()
        problems = projection.verify_projection(root)
        assert any("drifted" in problem or "missing" in problem.lower() for problem in problems)

    @pytest.mark.usefixtures("require_symlink_support")
    def test_replaced_by_symlink_is_reported(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        managed = root / ".kilo/commands/cg-work.md"
        outside = tmp_path / "outside-content.md"
        outside.write_bytes(b"outside")
        managed.unlink()
        managed.symlink_to(outside)
        problems = projection.verify_projection(root)
        assert any("not a regular file" in problem for problem in problems)

    def test_empty_entries_state_reports_healthy(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        ownership = {
            "schemaVersion": 1,
            "generated": "x",
            "entries": {},
            "activeAdapters": {},
        }
        projection._write_managed_json(root, projection.OWNERSHIP_STATE_PATH, ownership)
        assert projection.verify_projection(root) == []


class TestRealRepo:
    def test_real_repo_plan_resolves(self) -> None:
        manifest = manifest_module.resolve_active_manifest(REPO_ROOT)
        assert manifest["selection"]["platforms"] == manifest_module.canonical_platform_ids(REPO_ROOT)
        plan = projection.build_projection_plan(REPO_ROOT, manifest)
        assert plan.platforms
        assert plan.entries


class TestManifestFreshness:
    def _fresh_manifest(self, tmp_path: Path) -> tuple[Path, dict]:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        manifest = projection.load_active_manifest(root)
        return root, manifest

    def test_registry_digest_mismatch_fails_closed(self, tmp_path: Path) -> None:
        root, manifest = self._fresh_manifest(tmp_path)
        manifest["selection"]["registryDigest"] = "0" * 64
        with pytest.raises(projection.ProjectionError, match="stale"):
            projection.build_projection_plan(root, manifest)

    def test_registry_schema_mismatch_fails_closed(self, tmp_path: Path) -> None:
        root, manifest = self._fresh_manifest(tmp_path)
        manifest["selection"]["registrySchemaVersion"] = 99
        with pytest.raises(projection.ProjectionError, match="stale"):
            projection.build_projection_plan(root, manifest)

    def test_desired_plan_digest_tamper_fails_closed(self, tmp_path: Path) -> None:
        root, manifest = self._fresh_manifest(tmp_path)
        manifest["selection"]["desiredPlanDigest"] = "f" * 64
        with pytest.raises(projection.ProjectionError, match="stale|digest"):
            projection.build_projection_plan(root, manifest)

    def test_fresh_manifest_plan_succeeds(self, tmp_path: Path) -> None:
        root, manifest = self._fresh_manifest(tmp_path)
        projection.build_projection_plan(root, manifest)


class TestCopilotExclusion:
    def test_copilot_only_selection_fails_early(self, tmp_path: Path) -> None:
        root = tmp_path / "source"
        _real_registry(root)
        _small_mapping(root)
        _canonical_assets(root)
        _write(root / "compound-gpid.local.md", '---\nlanguage: "r"\nsuites: [cg]\n---\n# config\n')
        manifest = manifest_module.resolve_active_manifest(root, platforms=["copilot"])
        with pytest.raises(projection.ProjectionError, match="no platforms with a generated projection tree"):
            projection.build_projection_plan(root, manifest)

    def test_copilot_is_excluded_from_projected_platforms(self, tmp_path: Path) -> None:
        root, manifest = _repo_root(tmp_path, platforms="kilo,opencode,copilot")
        plan = projection.build_projection_plan(root, manifest)
        assert set(plan.platforms) == {"kilo", "opencode"}


class TestStateDirContainment:
    def test_symlinked_state_dir_is_rejected(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        state_dir = root / ".compound-gpid"
        if state_dir.is_dir() and not state_dir.is_symlink():
            for entry in state_dir.iterdir():
                if entry.is_dir() and not entry.is_symlink():
                    projection._remove_tree_no_follow(entry)
                else:
                    entry.unlink(missing_ok=True)
            state_dir.rmdir()
        outside = root.parent / "outside-state"
        outside.mkdir(exist_ok=True)
        try:
            state_dir.symlink_to(outside)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks unavailable on this host")
        with pytest.raises(projection.ProjectionError, match="compound-gpid"):
            projection.publish_projection(root, plan)


class TestVerifyAdaptersAndManagedRootBound:
    def test_entries_without_active_adapters_reported(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        ownership = projection._read_managed_json(root, projection.OWNERSHIP_STATE_PATH)
        ownership["activeAdapters"] = {}
        projection._write_managed_json(root, projection.OWNERSHIP_STATE_PATH, ownership)
        problems = projection.verify_projection(root)
        assert any("activeAdapters" in problem for problem in problems)

    def test_unlink_rejects_forged_outside_entry(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        forged = root / "compound-gpid.md"
        forged.write_text("# charter\n")
        ownership = projection._read_managed_json(root, projection.OWNERSHIP_STATE_PATH)
        ownership["entries"]["compound-gpid.md"] = {
            "sha256": projection._regular_file_hash(forged),
            "platform": "kilo",
        }
        projection._write_managed_json(root, projection.OWNERSHIP_STATE_PATH, ownership)
        removed, warnings = projection.unlink_consumer_projection(root)
        assert forged.exists()
        assert any("outside declared managed roots" in warning for warning in warnings)


class TestCliPipeline:
    def test_cli_plan_succeeds(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        assert projection.main(["--project-root", str(root), "--plan"]) == 0

    def test_cli_sync_publishes_and_verifies(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        assert projection.main(["--project-root", str(root), "--sync"]) == 0
        problems = projection.verify_projection(root)
        assert problems == []

    def test_cli_verify_fresh_project_is_noop(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        assert projection.main(["--project-root", str(root), "--verify"]) == 0

    def test_sync_consumer_projection_returns_ownership_and_plan(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo,opencode")
        ownership, plan = projection.sync_consumer_projection(root, root)
        assert ownership["schemaVersion"] == 1
        assert set(plan.platforms) == {"kilo", "opencode"}

    def test_unlink_removes_only_checksum_owned(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        managed = root / ".kilo/commands/cg-work.md"
        assert managed.exists()
        removed, warnings = projection.unlink_consumer_projection(root)
        assert removed > 0
        assert not managed.exists()
        assert warnings == []

    def test_unlink_preserves_user_modified(self, tmp_path: Path) -> None:
        root, _ = _repo_root(tmp_path, platforms="kilo")
        plan = projection.build_projection_plan(root, projection.load_active_manifest(root))
        projection.publish_projection(root, plan)
        managed = root / ".kilo/commands/cg-work.md"
        managed.write_bytes(b"user-edited")
        removed, warnings = projection.unlink_consumer_projection(root)
        assert managed.read_bytes() == b"user-edited"
        assert any("user-modified" in warning for warning in warnings)
