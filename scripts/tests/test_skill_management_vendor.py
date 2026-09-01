"""Plugin vendoring tests through the shared admission transaction path."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from skill_management.operations import import_skill
from skill_management.providers.github import AcquiredBundle, AcquiredFile
from scripts.tests.test_skill_management_create import (
    _arguments as create_arguments,
    _canonical_root,
    _context,
)


def _acquired(commit: str = "b" * 40) -> AcquiredBundle:
    content = b'---\nname: vendored-demo\ndescription: "Vendored demo"\n---\n# Demo\n'
    object_id = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    return AcquiredBundle(
        "https://github.com/kilo-org/kilocode",
        commit,
        "skills/vendored-demo",
        (AcquiredFile("SKILL.md", content, object_id, len(content), "100644"),),
        "c" * 64,
    )


def _arguments(**overrides) -> dict:
    metadata = create_arguments(
        positionals=[
            "https://github.com/Kilo-Org/kilocode",
            "skills/vendored-demo",
            "b" * 40,
        ],
        scope="plugin",
        owner="cap-new-skill",
        capability="vendored-demo",
        triggers="vendored-demo",
        license="MIT",
    )
    metadata.pop("description")
    metadata.update(overrides)
    return metadata


def test_plugin_vendoring_uses_allowlist_audit_and_common_transaction(
    tmp_path: Path, monkeypatch
) -> None:
    root = _canonical_root(tmp_path)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired()

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    arguments = _arguments()
    planned = import_skill.handle(
        context=_context(root), request={"phase": "plan", "arguments": arguments}
    )

    assert not planned.findings
    assert not (root / ".github/skills/vendored-demo").exists()
    assert "plugin-vendor" in planned.data["reviewEvidence"]
    applied = import_skill.handle(
        context=_context(root),
        request={
            "phase": "apply",
            "arguments": arguments,
            "planDigest": planned.plan_digest,
        },
    )
    assert not applied.findings
    assert (root / ".github/skills/vendored-demo/SKILL.md").is_file()
    provenance = json.loads(
        (
            root
            / ".github/shared/skill-management/provenance/vendored-demo.json"
        ).read_text("utf-8")
    )
    assert provenance["source"]["repository"] == "https://github.com/kilo-org/kilocode"
    event = provenance["history"][0]
    assert event["event"] == "imported"
    assert event["policyDigest"]
    assert event["reviewEvidenceDigest"]
    manifest = json.loads(
        (root / ".compound-gpid/active-manifest.json").read_text("utf-8")
    )
    row = next(
        item for item in manifest["catalogRecords"] if item["id"] == "vendored-demo"
    )
    assert row["available"] is False


def test_plugin_vendoring_rejects_consumer_and_outside_allowlist(
    tmp_path: Path, monkeypatch
) -> None:
    root = _canonical_root(tmp_path)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired()

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    consumer = import_skill.handle(
        context=_context(root, maintainer=False),
        request={"phase": "plan", "arguments": _arguments()},
    )
    assert consumer.findings
    assert consumer.exit_code == 4

    outside = _arguments(
        positionals=[
            "https://github.com/outside/public-skills",
            "skills/vendored-demo",
            "b" * 40,
        ]
    )
    blocked = import_skill.handle(
        context=_context(root), request={"phase": "plan", "arguments": outside}
    )
    assert blocked.findings
    assert blocked.exit_code == 5
    assert "allowlist" in blocked.findings[0].message.casefold()


def test_project_plan_digest_cannot_be_reused_for_plugin_vendoring(
    tmp_path: Path, monkeypatch
) -> None:
    root = _canonical_root(tmp_path)

    class Provider:
        def acquire(self, *_args, **_kwargs):
            return _acquired()

    monkeypatch.setattr(import_skill, "GitHubProvider", Provider)
    project_arguments = {
        "positionals": [
            "https://github.com/Kilo-Org/kilocode",
            "skills/vendored-demo",
            "b" * 40,
        ],
        "license": "MIT",
        "suites": "cg",
        "platforms": "kilo",
    }
    project = import_skill.handle(
        context=_context(root),
        request={"phase": "plan", "arguments": project_arguments},
    )
    assert project.plan_digest

    plugin = import_skill.handle(
        context=_context(root),
        request={
            "phase": "apply",
            "arguments": _arguments(),
            "planDigest": project.plan_digest,
        },
    )
    assert plugin.findings
    assert not (root / ".github/skills/vendored-demo").exists()
