"""Make one fresh copy of the toy R project for each coding agent (gate, #223).

Usage: <python> spike/gate/make_toy.py [--dest DIR] [--hosts claude,codex,kilo,copilot]

Each copy is DIR/toy-r-<host>, a git repository with one commit, so every
agent starts from the same state and none sees another's work. DIR defaults
to ~/temp/cg-gate, a throwaway folder outside any synced folder: delete it
after the gate. Nothing is overwritten: an existing copy stops the script.

The script also prints the value to give the agent in the gate task, the
weighted share of households below the line, computed here from the CSV and
independently of any R code the agent writes.
"""
import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

TOY = Path(__file__).resolve().parent / "toy-r"
LINE = 3.00
HOSTS = ["claude", "codex", "kilo", "copilot"]


def headcounts(csv_path: Path, line: float = LINE):
    """(weighted, unweighted) share of households with welfare below the line."""
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = [(float(r["welfare"]), float(r["weight"])) for r in csv.DictReader(handle)]
    weighted = sum(w for y, w in rows if y < line) / sum(w for _, w in rows)
    unweighted = sum(1 for y, _ in rows if y < line) / len(rows)
    return weighted, unweighted


def inside_cg_docs(folder: Path):
    """A folder above that holds .cg-docs/: cg.py status would take it for the project."""
    for candidate in (folder, *folder.parents):
        if (candidate / ".cg-docs").is_dir():
            return candidate
    return None


def git(folder: Path, *args):
    identity = ["-c", "user.name=Gate kit", "-c", "user.email=gate@example.invalid"]
    subprocess.run(["git", *identity, "-C", str(folder), *args], check=True, capture_output=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dest", default=str(Path.home() / "temp" / "cg-gate"))
    parser.add_argument("--hosts", default=",".join(HOSTS))
    args = parser.parse_args(argv)
    dest = Path(args.dest).expanduser().resolve()
    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()]
    above = inside_cg_docs(dest)
    if above:
        print(f"refused: {above} holds .cg-docs/, so cg.py status would take it for the project; "
              f"choose a folder outside it")
        return 1
    targets = [dest / f"toy-r-{host}" for host in hosts]
    existing = [t for t in targets if t.exists()]
    if existing:
        print("refused, these exist already: " + ", ".join(map(str, existing)))
        return 1
    if shutil.which("git") is None:
        print("refused: git is not installed")
        return 1
    for target in targets:
        shutil.copytree(TOY, target)
        git(target, "init", "-q")
        git(target, "add", "-A")
        git(target, "commit", "-q", "-m", "toy project for the gate")
        print(f"made {target}")
    weighted, unweighted = headcounts(TOY / "inst" / "extdata" / "survey.csv")
    print(f"\nThe value to give the agent: the weighted headcount ratio at {LINE:.2f} is {weighted:.6f}")
    print(f"(an unweighted share would give {unweighted:.6f}, so a result equal to that ignored the weights)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
