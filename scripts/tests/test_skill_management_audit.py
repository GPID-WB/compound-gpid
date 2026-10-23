"""Complete validation, audit, and reference-service tests for Phase 6."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from skill_management import contracts
from skill_management.operations import audit
from skill_management.services import references, validation
from scripts.tests.test_skill_management_read import _commit_manifest, _context, _root


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _target(root: Path) -> references.ReferenceTarget:
    return references.ReferenceTarget(
        identifier="demo-skill",
        origin="project-imported",
        source_path=".compound-gpid/skills/demo-skill",
        capability="project-skill-demo-skill",
        provenance_path=".compound-gpid/skill-provenance/demo-skill.json",
        source_root=root,
    )


def test_reference_scan_classifies_roots_and_strips_only_contract_fences(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / ".compound-gpid/skills/demo-skill/SKILL.md",
        '---\nname: demo-skill\ndescription: "Demo"\n---\n',
    )
    _write(tmp_path / "roadmap.json", '{"description":"demo-skill"}\n')
    _write(tmp_path / "compound-gpid.context.md", "Use demo-skill.\n")
    _write(tmp_path / "adapters/codex/AGENTS.md", "Load demo-skill.\n")
    _write(
        tmp_path / ".github/prompts/example.prompt.md",
        "```text\ndemo-skill\n```\n",
    )
    _write(
        tmp_path / ".compound-gpid/skill-migrations/demo.json",
        '{"skillId":"demo-skill"}\n',
    )
    _write(tmp_path / ".cg-docs/plans/old.md", "Historical demo-skill.\n")
    _write(tmp_path / "docs/example.md", "```text\ndemo-skill\n```\n")

    report = references.scan_references(tmp_path, tmp_path, (_target(tmp_path),))

    rows = {(item.path, item.classification) for item in report.references}
    assert ("roadmap.json", "active") in rows
    assert ("compound-gpid.context.md", "active") in rows
    assert ("adapters/codex/AGENTS.md", "active") in rows
    assert (".compound-gpid/skill-migrations/demo.json", "migration") in rows
    assert (".cg-docs/plans/old.md", "historical") in rows
    assert ("docs/example.md", "active") in rows
    assert not any(
        item.path == ".github/prompts/example.prompt.md"
        for item in report.references
    )
    assert not any(
        item.path.startswith(".compound-gpid/skills/demo-skill/")
        for item in report.references
    )


def test_staged_reference_rescan_uses_exact_future_bytes(tmp_path: Path) -> None:
    _write(tmp_path / "docs/live.md", "Use demo-skill.\n")
    target = _target(tmp_path)
    current = references.scan_references(tmp_path, tmp_path, (target,))
    staged = references.scan_references(
        tmp_path,
        tmp_path,
        (target,),
        staged={
            ("project", "docs/live.md"): b"Use replacement-skill.\n",
        },
    )

    assert [item.path for item in current.active] == ["docs/live.md"]
    assert staged.active == ()
    assert current.digest != staged.digest


def test_validation_reports_missing_provenance_and_stale_manifest(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    _commit_manifest(root)
    _write(
        root / "compound-gpid.local.md",
        '---\nlanguage: "r"\nsuites: [cg]\n---\n# Changed\n',
    )

    report = validation.validate_skills(root, root, identifier=None)
    codes = {item.code for item in report.findings}

    assert report.manifest_health == "stale"
    assert "manifest.stale" in codes
    assert "provenance.missing" in codes
    assert tuple(report.validated_ids) == tuple(sorted(report.validated_ids))
    assert report.findings == contracts.sort_findings(report.findings)


def test_validation_reports_invalid_selector_with_stable_remediation(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    path = root / ".github/shared/module-registry.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["capabilities"][0]["configSelectors"][0]["operator"] = "mutable"
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    report = validation.validate_skills(root, root, identifier=None)

    assert any(item.code == "registry.invalid" for item in report.findings)
    assert all(item.remediation for item in report.findings)


def test_audit_is_read_only_and_has_no_mutable_update_filter(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    outcome = audit.handle(
        context=SimpleNamespace(project_root=root, source_root=root, role="consumer"),
        request={
            "phase": "read",
            "arguments": {"provenance": True, "references": True},
        },
    )
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    schema = contracts.load_contract(
        Path(__file__).resolve().parents[2],
        contracts.CONTRACTS_ROOT / "audit-v1.schema.json",
    )

    assert before == after
    assert outcome.data["filters"] == ["provenance", "references"]
    assert "updates" not in schema["$defs"]["arguments"]["properties"]
    assert outcome.data["auditedIds"] == sorted(outcome.data["auditedIds"])


def test_audit_reference_rows_and_json_are_deterministic(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _write(root / "compound-gpid.context.md", "Use cg-skill-python-example.\n")
    context = _context(root)
    request = {
        "phase": "read",
        "arguments": {
            "positionals": ["cg-skill-python-example"],
            "references": True,
        },
    }

    first = audit.handle(context=context, request=request)
    second = audit.handle(context=context, request=request)

    assert first.data == second.data
    assert contracts.canonical_json_bytes(first.data) == contracts.canonical_json_bytes(
        second.data
    )
    assert any(
        item["path"] == "compound-gpid.context.md"
        and item["classification"] == "active"
        for item in first.data["references"]
    )
