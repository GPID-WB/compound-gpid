"""Checks on the text of the guide, its playbooks and the pointer block (task 1.3).

These hold rules that code can check: ADR 0001 (no file of the core pack names
python3; the pointer block is in AGENTS.md only), the issue's limits (a pointer
block of ten lines at most; every playbook opens with what the agent owns and
ends with a Reply contract), and that what cg.py points at exists. Each rule
is also shown to fail on the mistake it guards against.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[2]
CG = HUB / "packs" / "core" / "cg"
BLOCK = (CG / "templates" / "pointer-block.md").read_text(encoding="utf-8")


def names_python3(text: str) -> bool:
    return re.search(r"python3", text) is not None


def playbook_problems(text: str):
    """What a playbook must hold: an ownership statement first, a Reply contract last."""
    problems = []
    body = text.split("\n---\n", 1)[-1]
    paragraphs = [p.strip() for p in body.split("\n\n")]
    paragraphs = [p for p in paragraphs if p and not p.startswith(("#", "<!--"))]
    if not paragraphs or not paragraphs[0].startswith("**You own"):
        problems.append("the first paragraph is not the ownership statement (**You own ...)")
    if not paragraphs or not paragraphs[-1].startswith("**Reply:**"):
        problems.append("the last paragraph is not the Reply contract (**Reply:** ...)")
    return problems


def test_no_file_of_the_core_pack_names_python3():
    for path in sorted(CG.rglob("*.md")) + sorted(CG.rglob("*.yaml")):
        assert not names_python3(path.read_text(encoding="utf-8")), path
    assert names_python3("Run `python3 cg.py status`.")


def test_every_playbook_states_ownership_and_ends_with_a_reply_contract():
    playbooks = sorted((CG / "playbooks").glob("*.md"))
    assert {p.stem for p in playbooks} >= {"setup", "quick"}
    for path in playbooks:
        assert playbook_problems(path.read_text(encoding="utf-8")) == [], path
    assert len(playbook_problems("# Plan\n\n1. Do the work.\n\nThanks.\n")) == 2


def test_pointer_block_is_ten_lines_at_most_between_its_markers():
    lines = BLOCK.splitlines()
    assert len(lines) <= 10
    assert lines[0].startswith("<!-- cg:start") and lines[-1] == "<!-- cg:end -->"
    assert "/cg" in BLOCK and "launcher.json" in BLOCK


def test_this_repository_holds_the_pointer_block_once_and_only_in_agents_md():
    assert (HUB / "AGENTS.md").read_text(encoding="utf-8").count(BLOCK.strip()) == 1
    assert (HUB / "CLAUDE.md").read_text(encoding="utf-8").strip() == "@AGENTS.md"
    assert not (HUB / ".github" / "copilot-instructions.md").exists()


def test_the_guide_is_user_invoked_and_reads_state_through_the_launcher():
    text = (CG / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in text.split("\n---\n", 1)[0]
    assert "launcher.json" in text and "status --guide --project" in text
    # The pointer block runs plain status, which names no playbook (#223).
    assert "status --project" in BLOCK and "--guide" not in BLOCK


def named_commands(text: str):
    """The cg.py commands a text tells the agent to run, outside HTML comments,
    leaving out lines that say the command is not installed yet."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return {m.group(1) for line in text.splitlines() if "once installed" not in line
            for span in re.findall(r"`([^`]+)`", line)
            for m in re.finditer(r"(?:cg\.py|\"<cg>\")\s+([a-z][a-z-]*)", span)}


def test_what_the_agent_runs_names_only_cg_py_commands_that_exist():
    """Gate M1 (#223): P04 named `cg.py guard`, which arrives in task 2.4; an agent
    that ran it got exit 2 and could not complete quick work. The guide and the
    playbooks name only installed commands. Principles may name planned ones,
    because the guide says to run only what `cg.py --help` lists."""
    parser_help = subprocess.run([sys.executable, str(CG / "scripts" / "cg.py"), "--help"],
                                 capture_output=True, text=True).stdout
    existing = set(re.search(r"\{([a-z,-]+)\}", parser_help).group(1).split(","))
    for path in [CG / "SKILL.md", *sorted((CG / "playbooks").glob("*.md")), *sorted((CG / "templates").glob("*.md"))]:
        unknown = named_commands(path.read_text(encoding="utf-8")) - existing
        assert not unknown, f"{path.relative_to(HUB)} names cg.py {sorted(unknown)}"
    assert "--help" in (CG / "SKILL.md").read_text(encoding="utf-8")
    planned = set()
    for path in sorted((CG / "principles").glob("*.md")):
        planned |= named_commands(path.read_text(encoding="utf-8"))
    assert "guard" in planned - existing  # the case the rule in the guide covers
    assert named_commands("Run `cg.py guard` now.") == {"guard"}
    assert named_commands("- `cg.py guard`, once installed: no skipped checks.") == set()


def test_no_file_of_the_core_pack_holds_an_email_address():
    """The maintainer removed the organization contacts from P12 (#223)."""
    address = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    for path in sorted(CG.rglob("*.md")):
        assert not address.search(path.read_text(encoding="utf-8")), path
    assert address.search("Use of AI: ai@example.org")


def run_cg(home: Path, project: Path, *args):
    environ = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    done = subprocess.run([sys.executable, str(home / ".agents" / "skills" / "cg" / "scripts" / "cg.py"),
                           *args, "--project", str(project)], capture_output=True, text=True, env=environ)
    return done.returncode, done.stdout + done.stderr


def test_status_names_a_playbook_that_exists_before_and_after_setup(tmp_path):
    home, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    shutil.copytree(CG, home / ".agents" / "skills" / "cg", ignore=shutil.ignore_patterns("__pycache__"))
    project.mkdir()
    code, out = run_cg(home, project, "status", "--json", "--guide")
    state = json.loads(out)
    assert code == 0 and state["phase"] == "setup" and Path(state["playbook"]).is_file()
    # What the setup playbook tells the agent to write must be a config that status accepts.
    example = re.search(r"```json\n(.*?)```", (CG / "playbooks" / "setup.md").read_text(encoding="utf-8"), re.S)
    config = json.loads(example.group(1))
    config.update(packs=["core"], **{"requires-core": state["core"]})
    (project / ".cg-docs").mkdir()
    (project / ".cg-docs" / "config.json").write_text(json.dumps(config), encoding="utf-8")
    code, out = run_cg(home, project, "status", "--json", "--guide")
    state = json.loads(out)
    assert code == 0 and state["phase"] == "ready" and state["stops"] == [], out
    assert Path(state["playbook"]).is_file() and state["settings"] == ["<pack>.<setting>=<value>"]


def test_quick_work_gets_a_work_report_with_room_for_evidence(tmp_path):
    home, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    shutil.copytree(CG, home / ".agents" / "skills" / "cg", ignore=shutil.ignore_patterns("__pycache__"))
    project.mkdir()
    code, out = run_cg(home, project, "new", "work-report", "Fix the axis label", "--date", "2026-11-24")
    assert code == 0, out
    text = (project / ".cg-docs" / "work-reports" / "2026-11-24-fix-the-axis-label.md").read_text(encoding="utf-8")
    assert "PLACEHOLDER" not in text and 'title: "Fix the axis label"' in text
    for heading in ("## Checks", "## Evidence", "## Self-review", "## Not checked"):
        assert heading in text


def test_setup_lists_the_files_it_will_write_from_a_dry_run():
    """Rerun of gate M1 (#223): Kilo listed four files and setup wrote five
    (.Rbuildignore in an R package). The list comes from cg.py, not memory."""
    text = (CG / "playbooks" / "setup.md").read_text(encoding="utf-8")
    proposal = text[text.index("## 2. Propose"):text.index("## 3. Confirm")]
    assert "--dry-run" in proposal


def test_quick_work_can_complete_without_a_doctor_command():
    """Rerun of gate M1 (#223): Codex kept a report open because the new project's
    verification profile had no Doctor command, which is "not found" in most new
    projects. Quick work must say that a missing step does not keep it open."""
    text = (CG / "playbooks" / "quick.md").read_text(encoding="utf-8")
    record = text[text.index("## 5. Record"):]
    assert "Doctor" in record and "does not keep the work open" in record


def test_the_pointer_block_gives_the_sentence_on_cg_word_for_word():
    """Rerun of gate M1 (#223): twice Claude Code did not open a plain reply with
    the sentence on /cg when the block only described it."""
    assert '"`/cg` would run this change with checks and a record."' in BLOCK


def test_quick_work_is_not_held_open_by_a_failure_that_was_there_before():
    """Rerun of gate M1 (#223): Codex kept a report open over an R CMD check
    warning on code it had not touched."""
    text = (CG / "playbooks" / "quick.md").read_text(encoding="utf-8")
    assert "before your change" in text[text.index("## 5. Record"):]
