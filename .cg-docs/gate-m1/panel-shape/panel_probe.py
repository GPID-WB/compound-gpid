"""One-off probe for gate failure 1 (#223): a typed /cg that reaches the model
as the text of SKILL.md in the human's message, without the words "/cg".

Kilo's panel and Posit Assistant deliver the command that way (measured in
Kilo's session store, session ses_decbeb3e...). Kilo's command line passes the
literal "/cg", so run_cli_gate.py does not exercise this path. This probe runs
the same steps B to D through run_cli_gate.run_agent, with the guide message
replaced by the panel's shape:

    <body of the installed SKILL.md, no frontmatter>
    Base directory for this skill: <folder>
    Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.
    <what the human typed after /cg, when there is any>

Usage: python3 panel_probe.py HUB DEST OUT [kilo-model]
"""
import json
import sys
from pathlib import Path

hub, dest, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
model = sys.argv[4] if len(sys.argv) > 4 else ""
sys.path.insert(0, str(hub / "spike" / "gate"))
sys.path.insert(0, str(hub / "spike" / "host-matrix"))
import make_toy  # noqa: E402
import run_cli_gate as gate  # noqa: E402
from run_cli_checks import find_program, sanitize  # noqa: E402

SKILL = Path.home() / ".agents" / "skills" / "cg"


def panel_message(self, request=""):
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip("\n")
    text = (f"{body}\n\n\nBase directory for this skill: {SKILL}\n"
            "Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.")
    return f"{text}\n\n{request}" if request else text


gate.Agent.guide = panel_message
if make_toy.main(["--dest", str(dest), "--hosts", "kilo"]) != 0:
    sys.exit(1)
project = dest.expanduser().resolve() / "toy-r-kilo"
checks, log = gate.run_agent(gate.Agent("kilo", find_program("kilo"), model), project)
out.mkdir(parents=True, exist_ok=True)
# The transcript quotes the whole guide in each prompt. In the copies kept as
# evidence that text was replaced by a one-line marker afterwards.
text = sanitize("\n".join(log), project)
(out / "kilo-panel.md").write_text(text, encoding="utf-8")
(out / "results.json").write_text(json.dumps({"kilo-panel": checks}, indent=2) + "\n", encoding="utf-8")
for check, ok in checks.items():
    print(f"  {'pass' if ok else 'FAIL'}  {check}", flush=True)
sys.exit(0 if all(checks.values()) else 1)
