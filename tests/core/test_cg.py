"""Tests for packs/core/cg/scripts/cg.py.

Each test builds an installed layout in a temporary home folder: the cg skill
copied into ~/.agents/skills, other packs beside it. HOME and USERPROFILE point
at that folder, so the real home is never read or written.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]
CG = HUB / "packs" / "core" / "cg"


def install_core(home: Path, version="2.0.0") -> Path:
    skills = home / ".agents" / "skills"
    target = skills / "cg"
    shutil.copytree(CG, target, ignore=shutil.ignore_patterns("__pycache__"))
    data = json.loads((target / "pack.json").read_text())
    data.update(version=version, **{"requires-core": version})
    (target / "pack.json").write_text(json.dumps(data))
    return skills


def add_pack(skills: Path, name: str, lead: str, requires="2.0.0", **extra):
    folder = skills / lead
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(f"---\nname: {lead}\ndescription: x\n---\n")
    data = {"name": name, "version": "0.1.0", "requires-core": requires,
            "skills": [lead], "lenses": [], "tracks": [], **extra}
    (folder / "pack.json").write_text(json.dumps(data))


@pytest.fixture
def env(tmp_path):
    home = tmp_path.resolve() / "home"
    project = tmp_path.resolve() / "project"
    home.mkdir()
    project.mkdir()
    skills = install_core(home)
    environ = dict(os.environ, HOME=str(home), USERPROFILE=str(home))

    def cg(*args, cwd=project):
        done = subprocess.run([sys.executable, str(skills / "cg" / "scripts" / "cg.py"), *args],
                              capture_output=True, text=True, cwd=cwd, env=environ)
        return done.returncode, done.stdout + done.stderr

    return {"home": home, "project": project, "skills": skills, "cg": cg}


# ---------------------------------------------------------------- packs

def test_packs_in_the_hub_lists_core():
    done = subprocess.run([sys.executable, str(CG / "scripts" / "cg.py"), "packs", "--json"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stdout
    names = [p["name"] for p in json.loads(done.stdout)["packs"]]
    assert "core" in names


def test_packs_finds_packs_beside_cg(env):
    add_pack(env["skills"], "lang-r", "r-shared")
    code, out = env["cg"]("packs")
    assert code == 0, out
    assert out.splitlines()[0].startswith("core 2.0.0")
    assert out.splitlines()[1].startswith("lang-r 0.1.0")


def test_packs_reports_a_pack_needing_newer_core(env):
    add_pack(env["skills"], "lang-r", "r-shared", requires="2.1.0")
    code, out = env["cg"]("packs")
    assert code == 1
    assert "pack 'lang-r' needs core 2.1.0, installed core is 2.0.0" in out


def test_packs_reports_keys_outside_the_contract(env):
    add_pack(env["skills"], "lang-r", "r-shared", seventh="x")
    code, out = env["cg"]("packs")
    assert code == 1
    assert "keys outside the contract seventh" in out


def test_packs_reports_unreadable_pack_json(env):
    (env["skills"] / "broken").mkdir()
    (env["skills"] / "broken" / "pack.json").write_text("{not json")
    code, out = env["cg"]("packs")
    assert code == 1
    assert "unreadable" in out


# ---------------------------------------------------------------- status

def test_status_without_config_opens_setup(env):
    code, out = env["cg"]("status")
    assert code == 0, out
    assert "phase: setup" in out
    assert out.rstrip().endswith(str((env["skills"] / "cg").resolve() / "playbooks" / "setup.md"))


def test_status_is_identical_on_repeat_runs(env):
    plans = env["project"] / ".cg-docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "2026-01-02-a.md").write_text("---\nstatus: draft\n---\n")
    first = env["cg"]("status")
    assert first == env["cg"]("status")
    assert env["cg"]("status", "--json") == env["cg"]("status", "--json")


def test_status_names_missing_packs_and_the_command(env):
    docs = env["project"] / ".cg-docs"
    docs.mkdir()
    (docs / "config.json").write_text(json.dumps({"packs": ["core", "lang-r"]}))
    code, out = env["cg"]("status", "--json")
    state = json.loads(out)
    assert code == 0
    assert state["phase"] == "ready"
    assert state["packs-missing"] == ["lang-r"]
    call = "& " if os.name == "nt" else ""  # PowerShell needs '&' before a quoted path
    assert state["add-command"] == f'{call}"{sys.executable}" install.py --add lang-r'


def test_status_prints_pack_settings(env):
    docs = env["project"] / ".cg-docs"
    docs.mkdir()
    (docs / "config.json").write_text(json.dumps(
        {"packs": ["core"], "settings": {"lang-r": {"r-syntax": "tidyverse"}}}))
    code, out = env["cg"]("status")
    assert code == 0, out
    assert "settings: lang-r.r-syntax=tidyverse" in out
    (docs / "config.json").write_text(json.dumps({"packs": ["core"]}))
    assert "settings: none" in env["cg"]("status")[1]


def test_status_stops_on_malformed_settings(env):
    docs = env["project"] / ".cg-docs"
    docs.mkdir()
    (docs / "config.json").write_text(json.dumps({"settings": {"lang-r": {"r-syntax": 2}}}))
    code, out = env["cg"]("status")
    assert code == 1 and "settings.lang-r must map names to text values" in out


def test_status_stops_when_project_needs_newer_core(env):
    docs = env["project"] / ".cg-docs"
    docs.mkdir()
    (docs / "config.json").write_text(json.dumps({"requires-core": "3.0.0"}))
    code, out = env["cg"]("status")
    assert code == 1
    assert "this project needs core 3.0.0, installed core is 2.0.0" in out
    assert "next: stop and show the human the stops" in out


def test_status_stops_on_a_pack_needing_newer_core(env):
    add_pack(env["skills"], "lang-r", "r-shared", requires="9.0.0")
    code, out = env["cg"]("status")
    assert code == 1
    assert "needs core 9.0.0" in out


def test_status_reads_version_1_frontmatter(env):
    plans = env["project"] / ".cg-docs" / "plans"
    plans.mkdir(parents=True)
    (plans / "2026-03-01-old.md").write_text(
        "---\ndate: 2026-03-01\nstatus: completed\nphases:\n  - one\nfindings: {}\n---\n")
    (plans / "2026-04-01-open.md").write_text(
        '---\ntitle: "Open plan"\nstatus: draft   # comment\ncompleted-phases: [1, 2]\n---\n')
    (plans / "undated-notes.md").write_text("---\nstatus: active\n---\n")
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["active"] == ".cg-docs/plans/2026-04-01-open.md"
    assert state["open-artifacts"] == 2
    assert state["waiting-on-human"] == [".cg-docs/plans/2026-04-01-open.md (status draft)"]


# ---------------------------------------------------------------- new

def test_new_creates_one_file_with_frontmatter(env):
    code, out = env["cg"]("new", "plan", "Poverty", "headcount", "2024", "--date", "2026-11-24")
    assert code == 0, out
    path = env["project"] / ".cg-docs" / "plans" / "2026-11-24-poverty-headcount-2024.md"
    text = path.read_text()
    assert text.startswith('---\ntype: plan\ntitle: "Poverty headcount 2024"\ndate: 2026-11-24\nstatus: draft\n---\n')
    assert "# Poverty headcount 2024" in text


def test_new_never_overwrites(env):
    env["cg"]("new", "intent", "Same", "--date", "2026-11-24")
    path = env["project"] / ".cg-docs" / "brainstorms" / "2026-11-24-same.md"
    path.write_text("edited by the human")
    code, out = env["cg"]("new", "intent", "Same", "--date", "2026-11-24")
    assert code == 1
    assert "not overwritten" in out
    assert path.read_text() == "edited by the human"


def test_new_escapes_quotes_in_the_title(env):
    env["cg"]("new", "decision", 'Use "PPP 2021"', "--date", "2026-11-24")
    path = env["project"] / ".cg-docs" / "decisions" / "2026-11-24-use-ppp-2021.md"
    assert 'title: "Use \\"PPP 2021\\""' in path.read_text()


def test_new_rejects_a_bad_date_and_type(env):
    assert env["cg"]("new", "plan", "x", "--date", "24/11/2026")[0] == 2
    assert env["cg"]("new", "memo", "x")[0] == 2


def test_new_leaves_no_temporary_files(env):
    env["cg"]("new", "review", "A review", "--date", "2026-11-24")
    assert list(env["project"].rglob("*.tmp")) == []


# ---------------------------------------------------------------- doctor

def test_doctor_writes_the_launcher_once(env):
    code, out = env["cg"]("doctor")
    assert "launcher written" in out
    launcher = json.loads((env["home"] / ".cg" / "launcher.json").read_text())
    assert Path(launcher["python"]).is_file()
    if sys.prefix == sys.base_prefix:
        assert launcher["python"] == sys.executable
    assert launcher["cg"] == str((env["skills"] / "cg" / "scripts" / "cg.py").resolve())
    assert launcher["core"] == "2.0.0"
    assert "launcher up to date" in env["cg"]("doctor")[1]


def test_doctor_passes_on_a_clean_install(env):
    code, out = env["cg"]("doctor")
    assert code == 0, out
    assert "core runs from ~/.agents/skills" in out


def test_doctor_warns_on_folders_named_like_version_1_and_points_at_install(env):
    (env["home"] / ".claude" / "skills" / "cg-plan").mkdir(parents=True)
    (env["home"] / ".claude" / "skills" / "cg-spike-hello").mkdir()
    code, out = env["cg"]("doctor")
    assert code == 0, out
    line = next(l for l in out.splitlines() if "cg-plan" in l)
    assert line.startswith("warn ") and "2 folders named like version 1 skills (cg-plan, cg-spike-hello)" in line
    assert "install.py --remove-v1" in line


def test_doctor_records_the_interpreter_outside_a_virtual_environment(env, tmp_path):
    venv = tmp_path.resolve() / "project venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    done = subprocess.run([str(python), str(env["skills"] / "cg" / "scripts" / "cg.py"), "doctor"],
                          capture_output=True, text=True, cwd=env["project"],
                          env=dict(os.environ, HOME=str(env["home"]), USERPROFILE=str(env["home"])))
    launcher = json.loads((env["home"] / ".cg" / "launcher.json").read_text())
    recorded = Path(launcher["python"])
    assert recorded.is_file(), done.stdout
    assert venv not in recorded.resolve().parents and venv not in recorded.parents, launcher["python"]


def test_doctor_does_not_write_the_launcher_from_the_hub(env):
    done = subprocess.run([sys.executable, str(CG / "scripts" / "cg.py"), "doctor"],
                          capture_output=True, text=True, cwd=env["project"],
                          env=dict(os.environ, HOME=str(env["home"]), USERPROFILE=str(env["home"])))
    assert "launcher not written" in done.stdout
    assert not (env["home"] / ".cg" / "launcher.json").exists()


def test_status_knows_a_repository_before_its_first_commit(env):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    subprocess.run(["git", "init", "-q", str(env["project"])], check=True)
    state = json.loads(env["cg"]("status", "--json")[1])
    assert state["git"] == "repository", state
    assert state["branch"] not in ("", "HEAD") and state["commits"] == "none"
    assert not (env["project"] / ".git" / "index.lock").exists()


def test_doctor_flags_a_stale_copy(env):
    stale = env["home"] / ".claude" / "skills" / "cg"
    shutil.copytree(env["skills"] / "cg", stale)
    assert env["cg"]("doctor")[0] == 0
    (stale / "SKILL.md").write_text("old")
    code, out = env["cg"]("doctor")
    assert code == 1
    assert "the copy in ~/.claude/skills differs" in out


def test_doctor_flags_a_project_copy(env):
    shutil.copytree(env["skills"] / "cg", env["project"] / ".github" / "skills" / "cg")
    code, out = env["cg"]("doctor")
    assert code == 1
    assert "cg: also found in project .github/skills" in out


def test_doctor_accepts_the_link_layout(env):
    claude = env["home"] / ".claude" / "skills"
    claude.mkdir(parents=True)
    try:
        (claude / "cg").symlink_to(env["skills"] / "cg", target_is_directory=True)
    except OSError:
        pytest.skip("this machine does not allow links")
    code, out = env["cg"]("doctor")
    assert code == 0, out
    assert "cg: user ~/.agents/skills, user ~/.claude/skills" in out


# ---------------------------------------------------------------- review findings (#218)

def load_cg():
    import importlib.util
    spec = importlib.util.spec_from_file_location("cg_module", CG / "scripts" / "cg.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_status_from_a_subfolder_finds_the_project_root(env):
    docs = env["project"] / ".cg-docs"
    docs.mkdir()
    (docs / "config.json").write_text(json.dumps({"packs": ["core"]}))
    (env["project"] / "R").mkdir()
    state = json.loads(env["cg"]("status", "--json", "--project", str(env["project"] / "R"))[1])
    assert state["phase"] == "ready" and state["project"] == str(env["project"]), state


def test_status_of_a_folder_that_does_not_exist_is_an_error(env):
    code, out = env["cg"]("status", "--project", str(env["project"] / "nowhere"))
    assert code == 2 and "no such folder" in out


def test_status_stops_on_a_config_of_the_wrong_shape(env):
    docs = env["project"] / ".cg-docs"
    docs.mkdir()
    for config, words in (({"packs": "lang-r"}, "packs must be a list of pack names"),
                          ({"packs": ["lang-r", 3]}, "packs must be a list of pack names"),
                          ({"requires-core": 2}, "requires-core must be a version")):
        (docs / "config.json").write_text(json.dumps(config))
        code, out = env["cg"]("status")
        assert code == 1 and words in out and "Traceback" not in out, (config, out)
        assert "packs-missing: none" in out


def test_the_add_command_runs_as_printed_in_powershell():
    cg = load_cg()
    assert cg.add_command(["lang-r"], windows=True).startswith('& "')
    assert not cg.add_command(["lang-r"], windows=False).startswith("&")


def test_new_keeps_a_title_with_braces_and_a_hash_as_written(env):
    title = "Compare {date} and {heading} #12"
    env["cg"]("new", "plan", title, "--date", "2026-11-24")
    path = next((env["project"] / ".cg-docs" / "plans").glob("*.md"))
    assert load_cg().flat_frontmatter(path)["title"] == title
    assert "# " + title in path.read_text()


def test_the_usage_text_names_no_python3():
    assert "python3" not in (CG / "scripts" / "cg.py").read_text(encoding="utf-8")
