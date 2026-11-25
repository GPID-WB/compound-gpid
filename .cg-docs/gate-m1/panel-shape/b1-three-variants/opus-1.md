### B1 opus 1

> [the body of this variant's SKILL.md]


Base directory for this skill: ~/.agents/skills/cg
Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.

Measured: the project is in the `setup` phase. It has no `.cg-docs/config.json` and no active work item.

Typing `/cg` starts the guide.

> code · gpt-6-luna

→ Skill "cg"
→ Read ~/.cg/launcher.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: setup
reason: no .cg-docs/config.json
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: none
packs-missing: none
add-command: none
settings: none
data: none
git: repository
branch: main
changed-files: 0
stops: none
next: read playbooks/setup.md
playbook: ~/.agents/skills/cg/playbooks/setup.md



[exit code: 0]
