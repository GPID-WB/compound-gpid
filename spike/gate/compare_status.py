"""Compare what cg.py status reports in each agent's copy of the toy project (gate, #223).

Usage: <python> spike/gate/compare_status.py [--dest DIR] [--launcher PATH] [--collect [--into DIR]]

Runs `status --json` on every DIR/toy-r-* folder, with the interpreter and
cg.py that ~/.cg/launcher.json records, so it runs the installed copy, as
the guide does. It compares the fields that setup decides and that must not
depend on the agent: core, phase, packs expected and missing, settings,
stops, git. It also lists each copy's work reports and their status, the
record that quick work leaves. Exit code 1 when a compared field differs,
or when a copy has no completed work report.

With --collect, each copy's .cg-docs/ (records only, never data) is copied
into the hub at .cg-docs/gate-m1/<copy>/ (or --into DIR), so the evidence
can be committed. A copy already collected is left as it is.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SAME = ["core", "phase", "packs-expected", "packs-missing", "settings", "stops", "git"]


def status(launcher: dict, project: Path) -> dict:
    done = subprocess.run([launcher["python"], launcher["cg"], "status", "--json", "--project", str(project)],
                          capture_output=True, text=True)
    try:
        return json.loads(done.stdout)
    except ValueError:
        return {"error": (done.stdout + done.stderr).strip()[:300]}


def work_reports(project: Path):
    reports = []
    for path in sorted((project / ".cg-docs" / "work-reports").glob("*.md")):
        match = re.search(r"^status:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
        reports.append((path.name, match.group(1) if match else "none"))
    return reports


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dest", default=str(Path.home() / "temp" / "cg-gate"))
    parser.add_argument("--launcher", default=str(Path.home() / ".cg" / "launcher.json"))
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--into", default=str(Path(__file__).resolve().parents[2] / ".cg-docs" / "gate-m1"))
    args = parser.parse_args(argv)
    launcher_path = Path(args.launcher).expanduser()
    if not launcher_path.is_file():
        print(f"no launcher at {launcher_path}: install with install.py first")
        return 1
    launcher = json.loads(launcher_path.read_text(encoding="utf-8"))
    copies = sorted(Path(args.dest).expanduser().glob("toy-r-*"))
    if not copies:
        print(f"no toy-r-* folders in {args.dest}: run make_toy.py first")
        return 1
    states = {c.name: status(launcher, c) for c in copies}
    failed = False
    print("Fields that must be the same in every copy:")
    for field in SAME:
        values = {name: json.dumps(state.get(field, state.get("error")), sort_keys=True)
                  for name, state in states.items()}
        same = len(set(values.values())) == 1
        failed |= not same
        print(f"  {'same' if same else 'DIFF'}  {field}")
        if not same:
            for name, value in values.items():
                print(f"          {name}: {value}")
    print("\nWork reports (quick work must leave one, completed):")
    for copy in copies:
        reports = work_reports(copy)
        done = any(s == "completed" for _, s in reports)
        failed |= not done
        listed = "; ".join(f"{n} ({s})" for n, s in reports) or "none"
        print(f"  {'ok  ' if done else 'MISS'}  {copy.name}: {listed}")
    if args.collect:
        for copy in copies:
            target = Path(args.into) / copy.name
            if (copy / ".cg-docs").is_dir() and not target.exists():
                shutil.copytree(copy / ".cg-docs", target)
                print(f"collected {target}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
