"""Tests for tools/sync_version.py, on a small hub built in a temporary folder."""
import json
import subprocess
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[2]
SCRIPT = HUB / "tools" / "sync_version.py"
URL = "https://example.org/hub"


def put(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def make_hub(root: Path, version="2.0.0", plugin_version=None) -> Path:
    put(root / "plugin.json", {"name": "hub", "version": version, "repository": URL})
    put(root / "packs/core/cg/pack.json", {"name": "core", "version": version})
    put(root / "packs/core/.claude-plugin/plugin.json",
        {"name": "core", "version": plugin_version or version, "repository": URL})
    put(root / ".claude-plugin/marketplace.json",
        {"name": "hub", "plugins": [{"name": "core", "version": version, "source": "./packs/core"}]})
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "install-block.md").write_text(f"git clone {URL}\n")
    return root


def run(root: Path, *args):
    done = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                          capture_output=True, text=True)
    return done.returncode, done.stdout


def test_real_hub_is_in_step():
    code, out = run(HUB, "--check")
    assert code == 0, out


def test_check_fails_on_drift_and_writes_nothing(tmp_path):
    hub = make_hub(tmp_path, plugin_version="1.0.0")
    before = (hub / "packs/core/.claude-plugin/plugin.json").read_text()
    code, out = run(hub, "--check")
    assert code == 1
    assert "DRIFT" in out and "version" in out
    assert (hub / "packs/core/.claude-plugin/plugin.json").read_text() == before


def test_sync_fixes_drift_then_check_passes(tmp_path):
    hub = make_hub(tmp_path, plugin_version="1.0.0")
    code, _ = run(hub)
    assert code == 0
    assert json.loads((hub / "packs/core/.claude-plugin/plugin.json").read_text())["version"] == "2.0.0"
    assert run(hub, "--check")[0] == 0


def test_version_bump_in_pack_json_reaches_every_target(tmp_path):
    hub = make_hub(tmp_path)
    put(hub / "packs/core/cg/pack.json", {"name": "core", "version": "2.1.0"})
    assert run(hub, "--check")[0] == 1
    run(hub)
    assert json.loads((hub / "plugin.json").read_text())["version"] == "2.1.0"
    index = json.loads((hub / ".claude-plugin/marketplace.json").read_text())
    assert index["plugins"][0]["version"] == "2.1.0"


def test_pack_without_index_entry_is_an_error(tmp_path):
    hub = make_hub(tmp_path)
    put(hub / "packs/lang-r/r-shared/pack.json", {"name": "lang-r", "version": "0.1.0"})
    put(hub / "packs/lang-r/.claude-plugin/plugin.json",
        {"name": "lang-r", "version": "0.1.0", "repository": URL})
    code, out = run(hub)
    assert code == 1
    assert "no entry for hub pack 'lang-r'" in out


def test_hub_url_in_two_shipped_files_fails(tmp_path):
    hub = make_hub(tmp_path)
    assert run(hub, "--check")[0] == 0
    (hub / "install.py").write_text(f'HUB = "{URL}"\n')
    code, out = run(hub, "--check")
    assert code == 1
    assert "hub URL appears outside the manifests in 2 files" in out


def test_hub_url_nowhere_outside_the_manifests_fails(tmp_path):
    hub = make_hub(tmp_path)
    (hub / "docs" / "install-block.md").write_text("no URL here\n")
    code, out = run(hub, "--check")
    assert code == 1
    assert "in 0 files (exactly 1, the install block): none" in out


def test_hub_url_in_records_is_ignored(tmp_path):
    hub = make_hub(tmp_path)
    (hub / ".cg-docs").mkdir()
    (hub / ".cg-docs" / "old-plan.md").write_text(URL)
    assert run(hub, "--check")[0] == 0


def test_writes_leave_no_temporary_files(tmp_path):
    hub = make_hub(tmp_path, plugin_version="1.0.0")
    run(hub)
    leftovers = [p for p in hub.rglob("*.tmp")]
    assert leftovers == []
