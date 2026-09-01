"""Imported project and plugin skill update tests for Phase 5."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

from skill_management import planning
from skill_management.operations import create, import_skill, update
from skill_management.providers.github import AcquiredBundle, AcquiredFile
from skill_management.services import bundles, runtime
from scripts.tests.test_project_projection import (
    _canonical_assets,
    _real_registry,
    _small_mapping,
)
from scripts.tests.test_skill_management_create import (
    _arguments as create_arguments,
    _canonical_root,
    _context as canonical_context,
)
from scripts.tests.test_skill_management_vendor import (
    _acquired as vendor_acquired,
    _arguments as vendor_arguments,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _project(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    _real_registry(source)
    _small_mapping(source)
    _canonical_assets(source)
    shutil.copy2(
        REPO_ROOT / ".github/shared/vendor-policy.json",
        source / ".github/shared/vendor-policy.json",
    )
    project = tmp_path / "project"
    project.mkdir()
    (project / "compound-gpid.local.md").write_text(
        '---\nlanguage: "r"\nsuites: [cg]\n---\n', encoding="utf-8"
    )
    candidate = tmp_path / "candidate/demo"
    candidate.mkdir(parents=True)
    (candidate / "SKILL.md").write_text(
        '---\nname: demo\ndescription: "Imported demo"\n---\n# Demo\n',
        encoding="utf-8",
    )
    (candidate / "references").mkdir()
    (candidate / "references/old.md").write_text("# Old\n", encoding="utf-8")
    inventory = bundles.inventory_bundle(
        tmp_path, "candidate/demo", origin="project-imported"
    )
    import_plan = runtime.plan_project_import(
        project,
        source,
        inventory,
        origin="https://github.com/outside/public-skills",
        source_path="skills/demo",
        commit="a" * 40,
        suites=("cg",),
        platforms=("kilo",),
        license_id="MIT",
    )
    stored = planning.store_plan(project, import_plan)
    planning.apply_plan(project, import_plan, stored.digest)
    return source, project


def _acquired(
    *, commit: str = "b" * 40, secret: bool = False
) -> AcquiredBundle:
    skill = b'---\nname: demo\ndescription: "Imported demo v2"\n---\n# Demo v2\n'
    if secret:
        skill += b'api_key = "abcdefgh12345678"\n'
    resources = {"SKILL.md": skill, "references/new.md": b"# New\n"}
    files = []
    for path, content in sorted(resources.items()):
        object_id = hashlib.sha1(
            b"blob " + str(len(content)).encode("ascii") + b"\0" + content
        ).hexdigest()
        files.append(AcquiredFile(path, content, object_id, len(content), "100644"))
    return AcquiredBundle(
        "https://github.com/outside/public-skills",
        commit,
        "skills/demo",
        tuple(files),
        "d" * 64,
    )


def _context(source: Path, project: Path) -> SimpleNamespace:
    return SimpleNamespace(
        source_root=source,
        project_root=project,
        role="consumer",
        can_write_canonical=False,
        write_context_errors=("consumer project",),
    )


def _arguments(commit: str = "b" * 40) -> dict:
    return {
        "positionals": ["demo", commit],
        "license": "MIT",
        "approver": "project-reviewer",
        "review_reference": "reviewed-commit=" + commit,
    }


def test_project_update_requires_full_new_sha_and_appends_redacted_history(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _project(tmp_path)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired()

    monkeypatch.setattr(update, "GitHubProvider", Provider)
    before = json.loads(
        (project / ".compound-gpid/skill-provenance/demo.json").read_text("utf-8")
    )
    planned = update.handle(
        context=_context(source, project),
        request={"phase": "plan", "arguments": _arguments()},
    )

    assert not planned.findings
    assert planned.data["diff"] == sorted(
        planned.data["diff"], key=lambda item: item["path"]
    )
    serialized = json.dumps(planned.data["diff"], sort_keys=True)
    assert "Demo v2" not in serialized
    assert "api_key" not in serialized
    assert {item["change"] for item in planned.data["diff"]} == {
        "added",
        "modified",
        "removed",
    }
    applied = update.handle(
        context=_context(source, project),
        request={
            "phase": "apply",
            "arguments": _arguments(),
            "planDigest": planned.plan_digest,
        },
    )
    assert not applied.findings
    after = json.loads(
        (project / ".compound-gpid/skill-provenance/demo.json").read_text("utf-8")
    )
    assert after["history"][:-1] == before["history"]
    assert after["history"][-1]["sequence"] == 2
    assert after["history"][-1]["event"] == "updated"
    assert after["history"][-1]["commit"] == "b" * 40
    assert after["history"][-1]["diff"] == planned.data["diff"]
    assert after["source"]["repository"] == before["source"]["repository"]
    assert after["source"]["path"] == before["source"]["path"]
    assert not (project / ".compound-gpid/skills/demo/references/old.md").exists()
    assert (project / ".compound-gpid/skills/demo/references/new.md").is_file()


def test_same_sha_is_noop_and_short_sha_is_rejected(tmp_path: Path) -> None:
    source, project = _project(tmp_path)

    same = update.handle(
        context=_context(source, project),
        request={"phase": "plan", "arguments": _arguments("a" * 40)},
    )
    assert not same.findings
    assert same.changed is False
    assert same.data["status"] == "unchanged"
    assert same.plan_digest is None

    short = update.handle(
        context=_context(source, project),
        request={"phase": "plan", "arguments": _arguments("b" * 12)},
    )
    assert short.findings
    assert "full sha" in short.findings[0].message.casefold()


def test_update_rejects_new_secret_without_mutating_live_bundle(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _project(tmp_path)
    before = (project / ".compound-gpid/skills/demo/SKILL.md").read_bytes()

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired(secret=True)

    monkeypatch.setattr(update, "GitHubProvider", Provider)
    outcome = update.handle(
        context=_context(source, project),
        request={"phase": "plan", "arguments": _arguments()},
    )

    assert outcome.findings
    assert outcome.exit_code == 5
    assert (project / ".compound-gpid/skills/demo/SKILL.md").read_bytes() == before


def test_policy_change_after_plan_makes_update_stale(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _project(tmp_path)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired()

    monkeypatch.setattr(update, "GitHubProvider", Provider)
    arguments = _arguments()
    planned = update.handle(
        context=_context(source, project),
        request={"phase": "plan", "arguments": arguments},
    )
    policy_path = source / ".github/shared/vendor-policy.json"
    policy = json.loads(policy_path.read_text("utf-8"))
    policy["maxBundleSizeBytes"] -= 1
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    applied = update.handle(
        context=_context(source, project),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )
    assert applied.findings
    assert not (project / ".compound-gpid/skills/demo/references/new.md").exists()


def test_active_project_update_converges_selected_projection(
    tmp_path: Path, monkeypatch
) -> None:
    source, project = _project(tmp_path)
    activate = runtime.plan_capability_change(
        project, source, "project-skill-demo", activate=True
    )
    stored = planning.store_plan(project, activate)
    planning.apply_plan(project, activate, stored.digest)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired()

    monkeypatch.setattr(update, "GitHubProvider", Provider)
    arguments = _arguments()
    planned = update.handle(
        context=_context(source, project),
        request={"phase": "plan", "arguments": arguments},
    )
    applied = update.handle(
        context=_context(source, project),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )

    assert not applied.findings
    assert (project / ".kilo/skills/demo/SKILL.md").read_bytes() == (
        project / ".compound-gpid/skills/demo/SKILL.md"
    ).read_bytes()


def _vendor_update_candidate() -> AcquiredBundle:
    content = b'---\nname: vendored-demo\ndescription: "Vendored demo v2"\n---\n# V2\n'
    object_id = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    return AcquiredBundle(
        "https://github.com/kilo-org/kilocode",
        "c" * 40,
        "skills/vendored-demo",
        (AcquiredFile("SKILL.md", content, object_id, len(content), "100644"),),
        "e" * 64,
    )


def test_active_plugin_update_preserves_identity_and_converges_targets(
    tmp_path: Path, monkeypatch
) -> None:
    root = _canonical_root(tmp_path)

    class VendorProvider:
        def acquire(self, *_args, **_kwargs):
            return vendor_acquired()

    monkeypatch.setattr(import_skill, "GitHubProvider", VendorProvider)
    vendor_args = vendor_arguments()
    vendor_plan = import_skill.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": vendor_args},
    )
    vendor_apply = import_skill.handle(
        context=canonical_context(root),
        request={
            "phase": "apply",
            "arguments": vendor_args,
            "planDigest": vendor_plan.plan_digest,
        },
    )
    assert not vendor_apply.findings
    activate = runtime.plan_capability_change(
        root, root, "vendored-demo", activate=True, role="maintainer"
    )
    stored = planning.store_plan(root, activate)
    planning.apply_plan(root, activate, stored.digest)

    class UpdateProvider:
        def acquire(self, *_args, **_kwargs):
            return _vendor_update_candidate()

    monkeypatch.setattr(update, "GitHubProvider", UpdateProvider)
    arguments = {
        "positionals": ["vendored-demo", "c" * 40],
        "license": "MIT",
        "approver": "maintainer@example.com",
        "review_reference": "reviewed-commit=" + "c" * 40,
    }
    planned = update.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": arguments},
    )
    applied = update.handle(
        context=canonical_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )

    assert not applied.findings
    assert (root / ".kilo/skills/vendored-demo/SKILL.md").read_bytes() == (
        root / ".github/skills/vendored-demo/SKILL.md"
    ).read_bytes()
    provenance = json.loads(
        (
            root
            / ".github/shared/skill-management/provenance/vendored-demo.json"
        ).read_text("utf-8")
    )
    assert provenance["skillId"] == "vendored-demo"
    assert provenance["origin"] == "plugin-canonical"
    assert provenance["source"]["path"] == "skills/vendored-demo"
    assert [item["sequence"] for item in provenance["history"]] == [1, 2]


def test_locally_created_permanent_skill_has_no_update_source(
    tmp_path: Path,
) -> None:
    root = _canonical_root(tmp_path)
    arguments = create_arguments()
    planned = create.handle(
        context=canonical_context(root),
        request={"phase": "plan", "arguments": arguments},
    )
    applied = create.handle(
        context=canonical_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )
    assert not applied.findings

    outcome = update.handle(
        context=canonical_context(root),
        request={
            "phase": "plan",
            "arguments": {
                "positionals": ["permanent-demo", "c" * 40],
                "license": "MIT",
                "approver": "maintainer@example.com",
                "review_reference": "reviewed-commit=" + "c" * 40,
            },
        },
    )
    assert outcome.findings
    assert "locally created" in outcome.findings[0].message.casefold()
