"""Repeat step B1 with the panel's message shape, for several variants of the guide.

Usage: python3 panel_b1.py HUB DEST OUT MODEL N name=SKILL-file [name=SKILL-file ...]

For each variant: copy its SKILL.md over the installed one, then N times make a
fresh toy copy and send Kilo the guide's body as the human's message (a bare
/cg in Kilo's panel). Pass: the reply is a setup proposal (it names
data.table-collapse), nothing is written, and it does not tell the human to
type /cg. The installed SKILL.md is left as the last variant: restore it after.
"""
import json
import shutil
import sys
from pathlib import Path

hub, dest, out, model, n = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], int(sys.argv[5])
variants = [a.split("=", 1) for a in sys.argv[6:]]
sys.path.insert(0, str(hub / "spike" / "gate"))
sys.path.insert(0, str(hub / "spike" / "host-matrix"))
import make_toy  # noqa: E402
import run_cli_gate as gate  # noqa: E402
from run_cli_checks import find_program, sanitize  # noqa: E402

SKILL = Path.home() / ".agents" / "skills" / "cg"
out.mkdir(parents=True, exist_ok=True)
results = {}
for name, source in variants:
    shutil.copyfile(source, SKILL / "SKILL.md")
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip("\n")
    message = (f"{body}\n\n\nBase directory for this skill: {SKILL}\n"
               "Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.")
    results[name] = []
    for i in range(1, n + 1):
        folder = dest / f"{name}-{i}"
        if make_toy.main(["--dest", str(folder), "--hosts", "kilo"]) != 0:
            sys.exit(1)
        project = folder.expanduser().resolve() / "toy-r-kilo"
        log = []
        reply = gate.turn(gate.Agent("kilo", find_program("kilo"), model), project, message, True, log, f"B1 {name} {i}")
        answer = reply.split("> code ·", 1)[0]
        said_type_cg = "Type `/cg`" in answer or "type `/cg`" in answer or "typing `/cg`" in answer
        ok = "data.table-collapse" in answer and not (project / ".cg-docs").exists() and not said_type_cg
        results[name].append(ok)
        text = sanitize("\n".join(log), project).replace(body, "[the body of this variant's SKILL.md]")
        (out / f"{name}-{i}.md").write_text(text, encoding="utf-8")
        print(f"{name} {i}: {'pass' if ok else 'FAIL'}", flush=True)
(out / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
