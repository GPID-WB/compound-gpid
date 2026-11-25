"""Tests for install.py.

The hub is copied to a folder named like a Windows OneDrive folder, with
spaces, and HOME (USERPROFILE on Windows) points at a temporary folder that
also has spaces. The real home is never touched.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]


def clean_path() -> str:
    """PATH without a version 1 folder, so no test sees the machine's own install (#220)."""
    return os.pathsep.join(p for p in os.environ.get("PATH", "").split(os.pathsep)
                           if ".compound-gpid" not in p)


@pytest.fixture
def env(tmp_path):
    root = tmp_path.resolve()
    hub = root / "OneDrive - World Bank" / "compound gpid"
    hub.mkdir(parents=True)
    shutil.copy2(HUB / "install.py", hub / "install.py")
    shutil.copytree(HUB / ".claude-plugin", hub / ".claude-plugin")
    shutil.copytree(HUB / "packs" / "core", hub / "packs" / "core",
                    ignore=shutil.ignore_patterns("__pycache__"))
    home = root / "home folder"
    home.mkdir()
    environ = dict(os.environ, HOME=str(home), USERPROFILE=str(home), PATH=clean_path())

    def install(*args):
        done = subprocess.run([sys.executable, str(hub / "install.py"), *map(str, args)],
                              capture_output=True, text=True, env=environ)
        return done.returncode, done.stdout + done.stderr

    return {"hub": hub, "home": home, "root": root, "install": install}


def add_pack(hub: Path, name="lang-x", skills=("x-one",)):
    for skill in skills:
        (hub / "packs" / name / skill).mkdir(parents=True, exist_ok=True)
        (hub / "packs" / name / skill / "SKILL.md").write_text(f"---\nname: {skill}\ndescription: x\n---\n")
    data = {"name": name, "version": "0.1.0", "requires-core": "1.0.0", "skills": list(skills),
            "lenses": [], "tracks": []}
    (hub / "packs" / name / skills[0] / "pack.json").write_text(json.dumps(data))
    index_path = hub / ".claude-plugin" / "marketplace.json"
    index = json.loads(index_path.read_text())
    index["plugins"] = [p for p in index["plugins"] if p["name"] != name]
    index["plugins"].append({"name": name, "version": "0.1.0", "source": f"./packs/{name}"})
    index_path.write_text(json.dumps(index))


def snapshot(folder: Path):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def agents(env, skill="cg"):
    return env["home"] / ".agents" / "skills" / skill


def claude(env, skill="cg"):
    return env["home"] / ".claude" / "skills" / skill


# ---------------------------------------------------------------- install

def test_first_install_puts_core_in_both_folders(env):
    code, out = env["install"]("--packs", "core")
    assert code == 0, out
    assert (agents(env) / "SKILL.md").is_file() and not agents(env).is_symlink()
    assert (claude(env) / "SKILL.md").is_file()
    record = json.loads((env["home"] / ".cg" / "installed.json").read_text())
    assert record["packs"] == {"core": "1.99.0.9000"}
    assert record["hub"] == str(env["hub"])
    assert "cg.py doctor:" in out
    assert (env["home"] / ".cg" / "launcher.json").is_file()


def test_a_second_first_install_is_refused(env):
    env["install"]("--packs", "core")
    code, out = env["install"]("--packs", "core")
    assert code == 1 and "already installed (core)" in out


def test_refuses_a_skill_folder_it_does_not_own(env):
    agents(env).mkdir(parents=True)
    (agents(env) / "SKILL.md").write_text("someone else's")
    code, out = env["install"]("--packs", "core")
    assert code == 1
    assert "refused: ~/.agents/skills/cg exists and was not installed by install.py" in out
    assert (agents(env) / "SKILL.md").read_text() == "someone else's"
    assert not (env["home"] / ".cg" / "installed.json").exists()


def test_refuses_a_copy_another_host_reads(env):
    (env["home"] / ".kilo" / "skills" / "cg").mkdir(parents=True)
    code, out = env["install"]("--packs", "core")
    assert code == 1 and "~/.kilo/skills/cg: a host reads that folder too" in out


def test_refuses_when_installed_as_a_claude_code_plugin(env):
    plugin = env["home"] / ".claude" / "plugins" / "cache" / "compound" / "core" / "2.0" / "cg"
    plugin.mkdir(parents=True)
    (plugin / "SKILL.md").write_text("x")
    (plugin / "pack.json").write_text("{}")
    code, out = env["install"]("--packs", "core")
    assert code == 1 and "'cg' is also installed as a Claude Code plugin" in out


def test_leaves_user_owned_skills_untouched(env):
    mine = env["home"] / ".agents" / "skills" / "my-notes"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("mine")
    theirs = env["home"] / ".claude" / "skills" / "other-tool"
    theirs.mkdir(parents=True)
    (theirs / "SKILL.md").write_text("theirs")
    before = snapshot(env["home"] / ".agents" / "skills"), snapshot(theirs)
    env["install"]("--packs", "core")
    env["install"]("--update")
    env["install"]("--uninstall")
    assert snapshot(env["home"] / ".agents" / "skills") == before[0]
    assert snapshot(theirs) == before[1]


def test_add_and_remove_a_pack(env):
    add_pack(env["hub"])
    env["install"]("--packs", "core")
    code, out = env["install"]("--add", "lang-x")
    assert code == 0, out
    assert (agents(env, "x-one") / "pack.json").is_file()
    code, out = env["install"]("--remove", "core")
    assert code == 1 and "core is needed by the other packs" in out
    code, out = env["install"]("--remove", "lang-x")
    assert code == 0
    assert not agents(env, "x-one").exists() and not claude(env, "x-one").exists()
    assert agents(env).is_dir()


def test_unknown_packs_are_skipped_with_a_note(env):
    code, out = env["install"]("--profile", "economist")
    assert code == 0, out
    assert "note: pack 'lang-stata' is not in this hub; skipped" in out
    assert agents(env).is_dir()


def test_update_copies_again_and_drops_a_skill_the_pack_lost(env):
    add_pack(env["hub"], skills=("x-one", "x-two"))
    env["install"]("--packs", "core,lang-x")
    (env["hub"] / "packs" / "core" / "cg" / "NEW.md").write_text("new")
    shutil.rmtree(env["hub"] / "packs" / "lang-x" / "x-two")
    add_pack(env["hub"], skills=("x-one",))
    code, out = env["install"]("--update")
    assert code == 0, out
    assert (agents(env) / "NEW.md").read_text() == "new"
    assert (claude(env) / "NEW.md").read_text() == "new"
    assert not agents(env, "x-two").exists()


def test_refuses_to_overwrite_an_edited_install(env):
    env["install"]("--packs", "core")
    (agents(env) / "SKILL.md").write_text("my edit")
    for args in (["--update"], ["--uninstall"]):
        code, out = env["install"](*args)
        assert code == 1 and "was changed since it was installed" in out
        assert (agents(env) / "SKILL.md").read_text() == "my edit"
    assert env["install"]("--update", "--force")[0] == 0
    assert (agents(env) / "SKILL.md").read_text() != "my edit"


def test_uninstall_removes_everything_it_installed(env):
    add_pack(env["hub"])
    env["install"]("--packs", "core,lang-x")
    code, out = env["install"]("--uninstall")
    assert code == 0, out
    for skill in ("cg", "x-one"):
        assert not agents(env, skill).exists() and not claude(env, skill).exists()
        assert not claude(env, skill).is_symlink()
    assert not (env["home"] / ".cg").exists()


def test_dry_run_changes_nothing(env):
    code, out = env["install"]("--packs", "core", "--dry-run")
    assert code == 0 and "install core: cg -> ~/.agents/skills/cg" in out
    assert not (env["home"] / ".agents").exists() and not (env["home"] / ".cg").exists()


def test_falls_back_to_a_copy_when_links_are_not_allowed(env, monkeypatch):
    monkeypatch.setenv("HOME", str(env["home"]))
    monkeypatch.setenv("USERPROFILE", str(env["home"]))
    spec = importlib.util.spec_from_file_location("hub_install", env["hub"] / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def refuse(*args, **kwargs):
        raise OSError("links not allowed")

    monkeypatch.setattr(module.os, "symlink", refuse)
    monkeypatch.setattr(module, "make_junction", lambda target, link: False)
    monkeypatch.setattr(module, "run_doctor", lambda: 0)
    assert module.main(["--packs", "core"]) == 0
    assert claude(env).is_dir() and not module.is_link(claude(env))
    record = json.loads((env["home"] / ".cg" / "installed.json").read_text())
    assert record["skills"]["cg"]["claude"] == "copy"
    (claude(env) / "SKILL.md").write_text("edited copy")
    assert module.main(["--uninstall"]) == 1
    assert module.main(["--uninstall", "--force"]) == 0
    assert not claude(env).exists()


@pytest.mark.skipif(os.name != "nt", reason="junctions exist only on Windows")
def test_uses_a_junction_on_windows_when_symlinks_are_refused(env, monkeypatch):
    monkeypatch.setenv("HOME", str(env["home"]))
    monkeypatch.setenv("USERPROFILE", str(env["home"]))
    spec = importlib.util.spec_from_file_location("hub_install_j", env["hub"] / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def refuse(*args, **kwargs):
        raise OSError("symbolic links not allowed")

    monkeypatch.setattr(module.os, "symlink", refuse)
    monkeypatch.setattr(module, "run_doctor", lambda: 0)
    assert module.main(["--packs", "core"]) == 0
    assert module.is_link(claude(env)) and not claude(env).is_symlink()
    assert (claude(env) / "SKILL.md").is_file()
    record = json.loads((env["home"] / ".cg" / "installed.json").read_text())
    assert record["skills"]["cg"]["claude"] == "link"
    assert module.main(["--uninstall"]) == 0
    assert not claude(env).exists() and not agents(env).exists()


def load_install(env, monkeypatch, name):
    """install.py loaded in this process, with HOME pointing at the scratch home."""
    monkeypatch.setenv("HOME", str(env["home"]))
    monkeypatch.setenv("USERPROFILE", str(env["home"]))
    monkeypatch.setenv("PATH", clean_path())
    spec = importlib.util.spec_from_file_location(name, env["hub"] / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "run_doctor", lambda: 0)
    return module


def test_a_failed_first_install_can_be_run_again(env, monkeypatch):
    add_pack(env["hub"], skills=("x-one", "x-two", "x-three"))
    module = load_install(env, monkeypatch, "hub_install_fail")
    real_copytree = module.shutil.copytree

    def fail_on_x_two(source, target, *args, **kwargs):
        if Path(source).name == "x-two":
            real_copytree(source, target, *args, **kwargs)  # a half-made copy, as a locked file leaves
            raise PermissionError("Permission denied: x-two/SKILL.md")
        return real_copytree(source, target, *args, **kwargs)

    monkeypatch.setattr(module.shutil, "copytree", fail_on_x_two)
    assert module.main(["--packs", "core,lang-x"]) == 1
    skills = env["home"] / ".agents" / "skills"
    assert sorted(p.name for p in skills.iterdir()) == ["cg", "x-one"]  # no staging folder left
    monkeypatch.setattr(module.shutil, "copytree", real_copytree)
    assert module.main(["--packs", "core,lang-x"]) == 0
    record = json.loads((env["home"] / ".cg" / "installed.json").read_text())
    assert sorted(record["packs"]) == ["core", "lang-x"] and "unfinished" not in record
    assert sorted(record["skills"]) == ["cg", "x-one", "x-three", "x-two"]


def test_update_refuses_a_folder_that_replaced_its_link(env, monkeypatch):
    env["install"]("--packs", "core")
    if not claude(env).is_symlink():
        pytest.skip("this machine made a copy, not a link")
    claude(env).unlink()
    claude(env).mkdir()
    (claude(env) / "SKILL.md").write_text("my own notes")
    for args in (["--update"], ["--uninstall"], ["--update", "--force"]):
        code, out = env["install"](*args)
        assert code == 1, (args, out)
        assert "~/.claude/skills/cg is a folder install.py did not make" in out
        assert (claude(env) / "SKILL.md").read_text() == "my own notes"


# ---------------------------------------------------------------- version 1

def make_v1(env):
    clone = env["home"] / ".compound-gpid"
    (clone / "bin").mkdir(parents=True)
    (clone / "bin" / "cg-link").write_text("")
    (clone / ".github" / "skills" / "cg-plan").mkdir(parents=True)
    (env["home"] / ".zshrc").write_text("export A=1\n# --- Compound GPID ---\nexport PATH=x\n# --- End Compound GPID ---\n")
    skills = env["home"] / ".claude" / "skills"
    skills.mkdir(parents=True)
    try:
        (skills / "cg-plan").symlink_to(clone / ".github" / "skills" / "cg-plan", target_is_directory=True)
    except OSError:
        pytest.skip("this machine does not allow links")
    (skills / "cg-mine").mkdir()
    project = env["root"] / "my project"
    managed = project / ".kilo" / "skills"
    managed.mkdir(parents=True)
    (managed / ".compound-gpid-managed-copy.json").write_text('{"source": ".kilo/skills"}')
    (project / ".kilo" / "notes.md").write_text("mine")
    return clone, project


def test_install_reports_version_1_without_removing_it(env):
    clone, _ = make_v1(env)
    code, out = env["install"]("--packs", "core")
    assert code == 0, out
    assert "version 1 left ~/.claude/skills/cg-plan; install.py --remove-v1 removes it" in out
    assert "version 1 is installed at ~/.compound-gpid" in out
    assert ("-Uninstall" if os.name == "nt" else "scripts/install.sh --uninstall") in out
    assert "~/.zshrc holds the version 1 PATH block" in out
    assert (env["home"] / ".claude" / "skills" / "cg-plan").is_symlink()


def test_remove_v1_removes_only_what_version_1_owned(env):
    clone, project = make_v1(env)
    zshrc = (env["home"] / ".zshrc").read_text()
    code, out = env["install"]("--remove-v1", "--project", project)
    assert code == 0, out
    assert not (env["home"] / ".claude" / "skills" / "cg-plan").is_symlink()
    assert not (project / ".kilo" / "skills").exists()
    assert (project / ".kilo" / "notes.md").read_text() == "mine"
    assert (env["home"] / ".claude" / "skills" / "cg-mine").is_dir()
    assert "cg-mine: named like a version 1 skill but not provably version 1's" in out
    assert clone.is_dir()
    assert (env["home"] / ".zshrc").read_text() == zshrc


# ---------------------------------------------------------------- review findings (#220)

def test_a_scratch_install_sees_no_version_1_from_the_machine(env):
    code, out = env["install"]("--packs", "core")
    assert code == 0 and "version 1" not in out, out


def test_refuses_any_skill_of_a_pack_installed_as_a_claude_code_plugin(env):
    add_pack(env["hub"], skills=("x-one", "x-two"))
    copy = env["home"] / ".claude" / "plugins" / "cache" / "compound" / "lang-x" / "0.1.0" / "x-two"
    copy.mkdir(parents=True)
    (copy / "SKILL.md").write_text("x")
    code, out = env["install"]("--packs", "core,lang-x")
    assert code == 1 and "'x-two' is also installed as a Claude Code plugin" in out


def test_removing_a_pack_that_is_not_installed_says_so(env):
    env["install"]("--packs", "core")
    code, out = env["install"]("--remove", "lang-rr")
    assert code == 1 and "pack 'lang-rr' is not installed" in out


def test_a_failing_doctor_makes_the_install_exit_1(env, monkeypatch):
    module = load_install(env, monkeypatch, "hub_install_doctor")
    monkeypatch.setattr(module, "run_doctor", lambda: 1)
    assert module.main(["--packs", "core"]) == 1
    assert agents(env).is_dir()


def test_the_usage_text_names_no_python3():
    assert "python3" not in (HUB / "install.py").read_text(encoding="utf-8").split('"""')[1]
