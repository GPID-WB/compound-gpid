"""Documentation examples are executable CLI contracts, not live trial evidence."""

import json
import re
import shlex
import subprocess
from pathlib import Path

import pytest
from test_preview import snapshot

from cg_release import cli

ROOT = Path(__file__).resolve().parents[3]
PAGES = [ROOT / "packages/cg-release/README.md", ROOT / "docs/release-controller.md"]


@pytest.mark.parametrize("page", PAGES, ids=["package", "guide"])
def test_documented_four_commands_parse(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    block = re.search(r"<!-- cg-release:examples -->\n```text\n(.*?)\n```", text, re.S)
    assert block, "Missing tested command examples"
    commands = []
    for line in block[1].splitlines():
        executable, *args = shlex.split(line)
        assert executable in {"cg-release", "/cg-release"}
        commands.append(cli.parse_args(args).command)
    assert set(commands) == {"plan", "start", "status", "resume"}
    assert "deferred, not passed" in text
    assert "publisher remains disabled" in text


def test_documented_plan_runs_with_generic_offline_snapshot(
    monkeypatch, capsys, tmp_path
) -> None:
    text = PAGES[0].read_text(encoding="utf-8")
    line = next(
        line for line in text.splitlines() if line.startswith("cg-release plan ")
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "acquire_snapshot", lambda *a, **k: snapshot())
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: pytest.fail("Unexpected provider process")
    )
    assert cli.main(shlex.split(line)[1:]) == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "preview"
    assert list(tmp_path.iterdir()) == []


def test_controller_page_has_public_navigation_entry() -> None:
    manifest = json.loads((ROOT / "docs/navigation.json").read_text(encoding="utf-8"))
    assert (
        sum(
            page["file"] == "release-controller.md"
            for group in manifest["groups"]
            for page in group["pages"]
        )
        == 1
    )


def test_package_installation_link_uses_an_immutable_source_revision() -> None:
    text = PAGES[1].read_text(encoding="utf-8")
    link = re.search(
        r"\[package installation instructions\]\(https://github\.com/GPID-WB/"
        r"compound-gpid/blob/([0-9a-f]{40})/(packages/cg-release/README\.md)\)",
        text,
    )
    assert link, "The unreleased package guide must not link to an absent main path"
    assert (ROOT / link[2]).is_file()


def test_copied_setup_template_is_disabled_and_requires_real_identity(tmp_path) -> None:
    from cg_release.models import Policy, load_record

    template = ROOT / "packages/cg-release/templates/policy.example.json"
    copied = tmp_path / ".release-controller.json"
    copied.write_bytes(template.read_bytes())
    policy = load_record(Policy, copied.read_bytes())
    assert policy.enabled is False
    assert policy.repository_id == 123
    assert "fixture" in PAGES[1].read_text(encoding="utf-8")
