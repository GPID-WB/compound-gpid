"""Tests for tools/lint_skills.py, tools/validate_pack.py and tools/check_budgets.py.

Each rule is shown to fail on the mistake it guards against (SCOPE.md), on a
small pack built in a temporary folder.
"""
import json
import subprocess
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[2]
GOOD_SKILL = '---\nname: {name}\ndescription: "Weighted statistics in R."\n---\n\n# {name}\n\nBody.\n'


def run(script, *args, cwd=HUB):
    done = subprocess.run([sys.executable, str(HUB / "tools" / script), *map(str, args)],
                          capture_output=True, text=True, cwd=cwd)
    return done.returncode, done.stdout


def make_pack(root: Path, name="lang-x", skills=("x-one",), lead=None, **overrides) -> Path:
    pack = root / "packs" / name
    for skill in skills:
        (pack / skill).mkdir(parents=True)
        (pack / skill / "SKILL.md").write_text(GOOD_SKILL.format(name=skill))
    data = {"name": name, "version": "0.1.0", "requires-core": "2.0.0",
            "skills": list(skills), "lenses": [], "tracks": [], **overrides}
    (pack / (lead or skills[0]) / "pack.json").write_text(json.dumps(data))
    return pack


# ---------------------------------------------------------------- lint_skills

def test_lint_passes_on_the_hub():
    code, out = run("lint_skills.py", HUB / "packs")
    assert code == 0, out


def test_lint_passes_on_a_good_pack(tmp_path):
    assert run("lint_skills.py", make_pack(tmp_path))[0] == 0


def test_lint_fails_on_a_non_portable_key(tmp_path):
    pack = make_pack(tmp_path)
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text().replace("description:", "user-invocable: false\ndescription:"))
    code, out = run("lint_skills.py", pack)
    assert code == 1
    assert "frontmatter key 'user-invocable' is not portable" in out


def test_lint_fails_when_name_and_folder_differ(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "SKILL.md").write_text(GOOD_SKILL.format(name="x-two"))
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "does not match the folder 'x-one'" in out


def test_lint_fails_on_non_ascii_frontmatter(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "SKILL.md").write_text('---\nname: x-one\ndescription: "Pobreza — R"\n---\n',
                                             encoding="utf-8")
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "not ASCII" in out


def test_lint_reports_a_file_that_is_not_utf8(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "notes.md").write_bytes("Pobreza — R\n".encode("cp1252"))
    (pack / "x-one" / "SKILL.md").write_bytes('---\nname: x-one\ndescription: "—"\n---\n'.encode("cp1252"))
    code, out = run("lint_skills.py", pack)
    assert code == 1
    assert out.count("not UTF-8") == 2


def test_lint_fails_on_an_unquoted_colon(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "SKILL.md").write_text("---\nname: x-one\ndescription: Use this: always\n---\n")
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "holds ': '" in out


def test_lint_fails_on_a_skill_over_its_line_budget(tmp_path):
    pack = make_pack(tmp_path)
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text() + "line\n" * 500)
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "over its budget of 500" in out


def test_lint_fails_on_the_guide_over_100_lines(tmp_path):
    pack = make_pack(tmp_path, name="core", skills=("cg",))
    skill = pack / "cg" / "SKILL.md"
    skill.write_text(skill.read_text() + "line\n" * 95)
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "the guide's SKILL.md is" in out


def test_lint_fails_on_a_lens_over_60_lines(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "lenses").mkdir()
    (pack / "x-one" / "lenses" / "weights.md").write_text("line\n" * 61)
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "a lens is 61 lines, over its budget of 60" in out


def test_lint_fails_on_a_dead_link(tmp_path):
    pack = make_pack(tmp_path)
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text() + "See [the guide](references/missing.md).\n")
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "'references/missing.md' points at nothing" in out


def test_lint_fails_on_a_link_into_another_skill(tmp_path):
    pack = make_pack(tmp_path, skills=("x-one", "x-two"))
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text() + "See [two](../x-two/SKILL.md) and [web](https://example.org).\n")
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "leaves the skill folder 'x-one'" in out
    assert "example.org" not in out


def test_lint_ignores_links_in_code(tmp_path):
    pack = make_pack(tmp_path)
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text() + "```\n[x](nowhere.md)\n```\nInline `[y](nowhere.md)`.\n")
    assert run("lint_skills.py", pack)[0] == 0


def test_lint_fails_on_a_principle_without_its_sections(tmp_path):
    pack = make_pack(tmp_path, name="core", skills=("cg",))
    (pack / "cg" / "principles").mkdir()
    (pack / "cg" / "principles" / "P99-x.md").write_text("# P99\n\n## In production\n\n## Verifier: `x`\n")
    code, out = run("lint_skills.py", pack)
    assert code == 1
    assert "no '## Evidence it leaves' section" in out and "no '## Deterministic checks' section" in out
    assert "no '## Verifier' section" not in out


def test_lint_fails_on_a_pack_folder_without_skill(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "stray").mkdir()
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "without a SKILL.md" in out


# ---------------------------------------------------------------- validate_pack

def test_validate_passes_on_the_hub():
    code, out = run("validate_pack.py")
    assert code == 0, out


def test_validate_passes_on_a_good_pack(tmp_path):
    code, out = run("validate_pack.py", make_pack(tmp_path, skills=("x-one", "x-two")))
    assert code == 0, out


def test_validate_fails_on_a_seventh_key(tmp_path):
    code, out = run("validate_pack.py", make_pack(tmp_path, homepage="x"))
    assert code == 1 and "not in the contract homepage" in out


def test_validate_fails_on_an_unlisted_or_missing_skill(tmp_path):
    pack = make_pack(tmp_path, skills=("x-one", "x-two"))
    data = json.loads((pack / "x-one" / "pack.json").read_text())
    data["skills"] = ["x-one", "x-three"]
    (pack / "x-one" / "pack.json").write_text(json.dumps(data))
    code, out = run("validate_pack.py", pack)
    assert code == 1
    assert "folder 'x-two' is in the pack but not in skills" in out
    assert "skill 'x-three' has no folder" in out


def test_validate_fails_on_a_lens_with_an_unknown_principle(tmp_path):
    lens = {"id": "weights", "file": "lenses/weights.md", "principle": "P99", "when": "*.R"}
    pack = make_pack(tmp_path, lenses=[lens])
    (pack / "x-one" / "lenses").mkdir()
    (pack / "x-one" / "lenses" / "weights.md").write_text("Check the weights.\n")
    code, out = run("validate_pack.py", pack)
    assert code == 1 and "principle 'P99' is not one of core's principles" in out
    lens["principle"] = "P10"
    (pack / "x-one" / "pack.json").write_text(json.dumps(
        {**json.loads((pack / "x-one" / "pack.json").read_text()), "lenses": [lens]}))
    assert run("validate_pack.py", pack)[0] == 0


def test_validate_fails_on_a_playbook_outside_the_lead(tmp_path):
    track = {"track": "research", "playbook": "../x-two/SKILL.md"}
    code, out = run("validate_pack.py", make_pack(tmp_path, skills=("x-one", "x-two"), tracks=[track]))
    assert code == 1 and "is not a file inside x-one/" in out


def test_validate_fails_on_a_skill_name_used_twice(tmp_path):
    one = make_pack(tmp_path, name="lang-a", skills=("shared-x",))
    two = make_pack(tmp_path, name="lang-b", skills=("shared-x",))
    code, out = run("validate_pack.py", one, two)
    assert code == 1 and "skill name 'shared-x' is used by more than one pack" in out


def test_validate_fails_when_the_linter_fails(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "SKILL.md").write_text("no frontmatter\n")
    code, out = run("validate_pack.py", pack)
    assert code == 1 and "lint_skills.py failed" in out


def test_validate_fails_when_the_glossary_check_fails(tmp_path):
    pack = make_pack(tmp_path)
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text() + "The orchestrator runs it.\n")
    code, out = run("validate_pack.py", pack)
    assert code == 1 and "check_glossary.py failed" in out


# ---------------------------------------------------------------- check_budgets

def test_budgets_pass_on_the_hub():
    code, out = run("check_budgets.py")
    assert code == 0, out


def test_budgets_fail_on_pack_tooling_over_1500_lines(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "scripts").mkdir()
    (pack / "x-one" / "scripts" / "tool.py").write_text("x = 1\n" * 1501)
    (pack / "x-one" / "scripts" / "tests").mkdir()
    (pack / "x-one" / "scripts" / "tests" / "test_tool.py").write_text("x = 1\n" * 5000)
    code, out = run("check_budgets.py", "--pack", pack)
    assert code == 1 and "tooling is 1501 lines, over its budget of 1500" in out


def test_budgets_fail_on_tests_over_1_5_times_the_code(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "scripts").mkdir()
    (pack / "x-one" / "scripts" / "tool.py").write_text("x = 1\n" * 10)
    (tmp_path / "tests" / "lang-x").mkdir(parents=True)
    (tmp_path / "tests" / "lang-x" / "test_tool.py").write_text("x = 1\n" * 15)
    assert run("check_budgets.py", "--root", tmp_path)[0] == 0
    (tmp_path / "tests" / "lang-x" / "test_tool.py").write_text("x = 1\n" * 16)
    code, out = run("check_budgets.py", "--root", tmp_path)
    assert code == 1 and "tests/lang-x: 16 lines, over 1.5 times the 10 lines" in out


def test_budgets_fail_on_two_user_invoked_skills_in_core(tmp_path):
    pack = make_pack(tmp_path, name="core", skills=("cg", "cg-extra"))
    for skill in ("cg", "cg-extra"):
        path = pack / skill / "SKILL.md"
        path.write_text(path.read_text().replace("---\n\n", "disable-model-invocation: true\n---\n\n", 1))
    code, out = run("check_budgets.py", "--pack", pack)
    assert code == 1 and "core has 2 user-invoked skills" in out


def test_budgets_fail_on_a_seventh_key(tmp_path):
    code, out = run("check_budgets.py", "--pack", make_pack(tmp_path, homepage="x"))
    assert code == 1 and "7 keys, over the budget of 6" in out
