"""Check the size budgets in SCOPE.md that are about tooling and packs.

Usage: python tools/check_budgets.py [--pack PACK_FOLDER] [--root PATH]

Checked here (line budgets of skill files are in tools/lint_skills.py):
- a pack's tooling, excluding tests: core at most 4,000 lines (ADR 0007), any other
  pack at most 1,500;
- hub tooling (tools/ and install.py), excluding tests: at most 2,000;
- tests at most 1.5 times the code they cover, per group: tests/<pack>/
  covers packs/<pack>/, tests/hub/ covers tools/ and install.py;
- `pack.json` at most six keys;
- user-invoked skills in core (`disable-model-invocation: true`): one.

Tooling is every file with a code extension (CODE_SUFFIXES). Lines are
counted as `wc -l` counts them. Going over any budget is an error. Exit code 1 on any error.
"""
import json
import re
import sys
from pathlib import Path

CODE_SUFFIXES = {".py", ".sh", ".ps1", ".cmd", ".bat", ".js", ".ts"}
PACK_BUDGET = {"core": 4000}
DEFAULT_PACK_BUDGET = 1500
HUB_BUDGET = 2000
TEST_RATIO = 1.5
PACK_KEYS_MAX = 6
CORE_USER_INVOKED_MAX = 1


def is_test(path: Path) -> bool:
    """path is relative to the folder being counted."""
    return "tests" in path.parts or path.name.startswith("test_") or path.name.endswith("_test.py")


def count_lines(files) -> int:
    total = 0
    for path in files:
        try:
            total += path.read_bytes().count(b"\n")
        except OSError:
            pass
    return total


def code_files(folder: Path, tests: bool, base: Path):
    if not folder.exists():
        return []
    files = [folder] if folder.is_file() else sorted(folder.rglob("*"))
    return [p for p in files if p.is_file() and p.suffix in CODE_SUFFIXES
            and "__pycache__" not in p.parts and is_test(p.relative_to(base)) == tests]


def check_pack(pack: Path, errors, report):
    code = count_lines(code_files(pack, False, pack))
    budget = PACK_BUDGET.get(pack.name, DEFAULT_PACK_BUDGET)
    report.append(f"pack {pack.name}: tooling {code} of {budget} lines")
    if code > budget:
        errors.append(f"pack {pack.name}: tooling is {code} lines, over its budget of {budget}")
    for manifest in sorted(pack.glob("*/pack.json")):
        try:
            keys = len(json.loads(manifest.read_text(encoding="utf-8")))
        except (ValueError, TypeError):
            continue  # an unreadable pack.json is the validator's to report
        if keys > PACK_KEYS_MAX:
            errors.append(f"{manifest}: {keys} keys, over the budget of {PACK_KEYS_MAX}")
    if pack.name == "core":
        invoked = []
        for skill in sorted(pack.glob("*/SKILL.md")):
            front = skill.read_text(encoding="utf-8").split("\n---", 1)[0]
            if re.search(r"^disable-model-invocation:\s*true\s*$", front, re.M):
                invoked.append(skill.parent.name)
        if len(invoked) > CORE_USER_INVOKED_MAX:
            errors.append(f"core has {len(invoked)} user-invoked skills ({', '.join(invoked)}), "
                          f"over the budget of {CORE_USER_INVOKED_MAX}")
    return code


def check_tests(root: Path, name: str, code: int, errors, report):
    tests = count_lines(code_files(root / "tests" / name, True, root))
    if not tests:
        return
    limit = int(code * TEST_RATIO)
    report.append(f"tests/{name}: {tests} lines for {code} lines of code (at most {limit})")
    if tests > limit:
        errors.append(f"tests/{name}: {tests} lines, over {TEST_RATIO} times the {code} lines they cover")


def main(argv):
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path(__file__).resolve().parent.parent
    errors, report = [], []
    if "--pack" in argv:
        check_pack(Path(argv[argv.index("--pack") + 1]), errors, report)
    else:
        for pack in sorted(p for p in (root / "packs").iterdir() if p.is_dir()):
            check_tests(root, pack.name, check_pack(pack, errors, report), errors, report)
        hub = count_lines(code_files(root / "tools", False, root) + code_files(root / "install.py", False, root))
        report.append(f"hub tooling (tools/, install.py): {hub} of {HUB_BUDGET} lines")
        if hub > HUB_BUDGET:
            errors.append(f"hub tooling (tools/, install.py) is {hub} lines, over its budget of {HUB_BUDGET}")
        check_tests(root, "hub", hub, errors, report)
    for line in report:
        print(line)
    for line in errors:
        print(f"ERROR {line}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
