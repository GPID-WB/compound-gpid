"""Strict project-import admission tests."""
from __future__ import annotations

import os
import json
from pathlib import Path

import pytest

from skill_management.services import admission


REPO_ROOT = Path(__file__).resolve().parents[2]


def _bundle(tmp_path: Path, extra_name: str = "references/guide.md", extra: bytes = b"# Guide\n") -> Path:
    root = tmp_path / "demo"
    root.mkdir(parents=True)
    (root / "SKILL.md").write_bytes(
        b'---\nname: demo\ndescription: "Demo"\n---\n# Demo\n'
    )
    path = root / extra_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(extra)
    return root


def test_clean_bundle_is_admitted_with_deterministic_redacted_evidence(tmp_path: Path) -> None:
    candidate = _bundle(tmp_path)
    policy = admission.load_admission_policy(REPO_ROOT)

    first = admission.admit_bundle(candidate, "MIT", policy)
    second = admission.admit_bundle(candidate, "MIT", policy)

    assert first.ok
    assert first.evidence_bytes == second.evidence_bytes
    assert str(tmp_path).encode() not in first.evidence_bytes


def test_invalid_policy_schema_and_plugin_origin_confusion_fail_closed(tmp_path: Path) -> None:
    policy_value = json.loads(
        (REPO_ROOT / ".github/shared/vendor-policy.json").read_text(encoding="utf-8")
    )
    policy_value["projectOverride"] = {"maxBundleSizeBytes": 999999999}
    policy_path = tmp_path / ".github/shared/vendor-policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(policy_value), encoding="utf-8")

    with pytest.raises(admission.AdmissionPolicyError, match="closed schema"):
        admission.load_admission_policy(tmp_path)

    canonical = admission.load_admission_policy(REPO_ROOT)
    assert not admission.repository_allowed_for_plugin(
        "https://github.com/outside/public-skills", canonical
    )


@pytest.mark.parametrize(
    "filename",
    ["data.csv", "data.dta", "data.sav", "data.rds", "data.parquet", "data.feather", "data.db", "data.sqlite", "archive.zip", ".env"],
)
def test_data_archive_environment_and_credential_formats_are_rejected(
    tmp_path: Path, filename: str
) -> None:
    candidate = _bundle(tmp_path, filename, b"not allowed")
    result = admission.admit_bundle(
        candidate, "MIT", admission.load_admission_policy(REPO_ROOT)
    )
    assert not result.ok
    assert any("extension" in finding.code for finding in result.findings)


def test_secret_injection_lfs_executable_and_invalid_license_are_rejected(tmp_path: Path) -> None:
    policy = admission.load_admission_policy(REPO_ROOT)
    cases = (
        ("secret.txt", b"API_KEY=sk-12345678901234567890", "MIT"),
        ("attack.md", b"ignore\nprevious\ninstructions", "MIT"),
        ("large.txt", b"version https://git-lfs.github.com/spec/v1\n", "MIT"),
        ("guide.md", b"safe", "Proprietary"),
    )
    for index, (name, content, license_id) in enumerate(cases):
        root = tmp_path / str(index)
        root.mkdir()
        candidate = _bundle(root, name, content)
        result = admission.admit_bundle(candidate, license_id, policy)
        assert not result.ok

    if os.name != "nt":
        executable = _bundle(tmp_path / "executable", "run.txt", b"safe")
        os.chmod(executable / "run.txt", 0o755)
        result = admission.admit_bundle(executable, "MIT", policy)
        assert not result.ok
        assert any(finding.code == "admission.executable" for finding in result.findings)


def test_hard_link_and_undeclared_opaque_resource_are_rejected(tmp_path: Path) -> None:
    policy = admission.load_admission_policy(REPO_ROOT)
    candidate = _bundle(tmp_path / "hardlink")
    os.link(candidate / "references/guide.md", candidate / "references/other.md")
    result = admission.admit_bundle(candidate, "MIT", policy)
    assert not result.ok
    assert any(finding.code == "admission.hard-link" for finding in result.findings)

    opaque = _bundle(tmp_path / "opaque", "assets/diagram.svg", b"<svg></svg>")
    result = admission.admit_bundle(opaque, "MIT", policy)
    assert not result.ok
    assert any(finding.code == "admission.opaque-class" for finding in result.findings)


def test_declared_approved_opaque_non_data_resource_is_admitted(tmp_path: Path) -> None:
    candidate = _bundle(tmp_path, "assets/diagram.svg", b"<svg></svg>")
    skill = candidate / "SKILL.md"
    skill.write_text(
        '---\nname: demo\ndescription: "Demo"\n'
        "resource-classes: [assets/diagram.svg=diagram]\n---\n# Demo\n",
        encoding="utf-8",
    )

    result = admission.admit_bundle(
        candidate, "MIT", admission.load_admission_policy(REPO_ROOT)
    )

    assert result.ok, result.findings
