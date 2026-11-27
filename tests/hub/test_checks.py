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
    data = {"name": name, "version": "0.1.0", "requires-core": "1.0.0",
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
    assert code == 1 and "unquoted value holds ':'" in out


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


def test_lint_reads_a_pack_folder_without_pack_json_as_a_pack(tmp_path):
    pack = make_pack(tmp_path)
    (pack / "x-one" / "pack.json").unlink()
    (pack / "x-one" / "references").mkdir()
    (pack / "x-one" / "references" / "notes.md").write_text("Notes.\n")
    skill = pack / "x-one" / "SKILL.md"
    skill.write_text(skill.read_text().replace("description:", "user-invocable: false\ndescription:"))
    code, out = run("lint_skills.py", pack)
    assert code == 1
    assert "'user-invocable' is not portable" in out and "without a SKILL.md" not in out


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
    manifest = json.loads((pack / "x-one" / "pack.json").read_text())
    # The shape of `when` (ADR 0003, 2026-11-27): patterns as text, or an object with files and a track.
    for when, good in (("*.R", True), ({"files": "*.R, R/", "track": "research"}, True), ({"files": "*.R"}, True),
                       (["*.R"], False), ("", False), ({"track": "research"}, False), ({"files": "*.R", "stage": "plan"}, False),
                       ({"files": 3}, False)):
        (pack / "x-one" / "pack.json").write_text(json.dumps({**manifest, "lenses": [{**lens, "when": when}]}))
        code, out = run("validate_pack.py", pack)
        assert (code == 0) == good and ("when must be file patterns as text" in out) != good, (when, out)
    # Its id names its verifier, <pack>.<id>, in a line that code prints to run: one name, used once (review of #228).
    for ids, good in ((["weights"], True), (["weights", "survey-design"], True), (["two words"], False), ([3], False),
                      (["a.b"], False), (["weights", "weights"], False)):
        lenses = [{**lens, "id": name} for name in ids]
        (pack / "x-one" / "pack.json").write_text(json.dumps({**manifest, "lenses": lenses}))
        code, out = run("validate_pack.py", pack)
        assert (code == 0) == good and ("id must be" in out) != good, (ids, out)


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


def test_budgets_fail_on_hub_tooling_over_2000_lines(tmp_path):
    make_pack(tmp_path)
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "a.py").write_text("x = 1\n" * 1500)
    (tmp_path / "install.py").write_text("x = 1\n" * 500)
    assert run("check_budgets.py", "--root", tmp_path)[0] == 0
    (tmp_path / "install.py").write_text("x = 1\n" * 501)
    code, out = run("check_budgets.py", "--root", tmp_path)
    assert code == 1 and "hub tooling (tools/, install.py) is 2001 lines, over its budget of 2000" in out


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


# ---------------------------------------------------------------- review findings (#222, #217)

def set_description(pack, line):
    (pack / "x-one" / "SKILL.md").write_text(f"---\nname: x-one\n{line}\n---\n\nBody.\n")


def test_lint_fails_on_unquoted_values_a_strict_parser_rejects_or_cuts(tmp_path):
    pack = make_pack(tmp_path)
    for value, char in (("[beta] Weighted statistics in R", "["), ("!important R things", "!"),
                        ("Use for C #sharp and R", "#")):
        set_description(pack, f"description: {value}")
        code, out = run("lint_skills.py", pack)
        assert code == 1 and f"unquoted value holds '{char}'" in out, (value, out)
    set_description(pack, 'description: "Use for C #sharp and R"\nallowed-tools: [Read, Grep]')
    assert run("lint_skills.py", pack)[0] == 0


def test_lint_refuses_a_folded_description(tmp_path):
    pack = make_pack(tmp_path)
    for header in (">-", ">", "|"):
        set_description(pack, f"description: {header}\n  Folded text " + "x" * 1100)
        code, out = run("lint_skills.py", pack)
        assert code == 1 and "write it as one quoted line" in out, (header, out)


def test_lint_fails_on_a_plain_path_into_another_skill(tmp_path):
    pack = make_pack(tmp_path, skills=("x-one", "x-two"))
    skill = pack / "x-one" / "SKILL.md"
    base = skill.read_text()
    for line in ("Read `../x-two/SKILL.md` first.", "Read ../x-two/SKILL.md first."):
        skill.write_text(base + line + "\n")
        code, out = run("lint_skills.py", pack)
        assert code == 1 and "path '../x-two/SKILL.md' leaves the skill folder 'x-one'" in out, (line, out)
    (pack / "x-one" / "references").mkdir()
    (pack / "x-one" / "references" / "a.md").write_text("Back to `../SKILL.md`.\n")
    skill.write_text(base)
    assert run("lint_skills.py", pack)[0] == 0
    (pack / "x-one" / "references" / "a.md").write_text("See [it](../missing.md).\n")
    code, out = run("lint_skills.py", pack)
    assert code == 1 and "'../missing.md' points at nothing" in out


def test_validate_fails_on_a_pack_needing_a_newer_core_than_the_hub(tmp_path):
    code, out = run("validate_pack.py", make_pack(tmp_path, **{"requires-core": "99.0.0"}))
    assert code == 1 and "requires-core 99.0.0 is newer than the hub's core" in out


def test_glossary_check_with_no_argument_checks_the_hub_from_any_folder(tmp_path):
    code, out = run("check_glossary.py", cwd=tmp_path)
    assert code == 0, out
    assert "README.md" in out or "files," in out
    assert int(out.split(" files,")[0].split()[-1]) > 30


def test_sync_version_finds_the_hub_from_any_folder(tmp_path):
    code, out = run("sync_version.py", "--check", cwd=tmp_path)
    assert code == 0 and "manifests in step" in out, out


def test_no_pack_file_names_a_version_1_command():
    """Version 1 commands such as /cg-fixbug do not exist in version 2 (#221).

    Frontmatter is skipped: a derived-from field cites version 1 files as sources.
    """
    import re
    found = []
    for path in sorted((HUB / "packs").rglob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        start = lines.index("---", 1) + 1 if lines[:1] == ["---"] else 0
        found += [f"{path.relative_to(HUB)}:{n}" for n, line in enumerate(lines[start:], start + 1)
                  if re.search(r"/cg-[a-z]|\bcg-fixbug\b", line)]
    assert found == []
