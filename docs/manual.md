# Compound GPID — Documentation

All documentation lives here in `docs/`. Start with [Installation](installation.md) if you are new, or pick a page from the table below.

## Pages

| File | Contents |
|------|---------|
| [installation.md](installation.md) | Install, link, configure, and upgrade from an old version |
| [versioning.md](versioning.md) | Version management — pin to a release, browse tags, return to main |
| [workflow.md](workflow.md) | Engineering and research workflow loops — `/cg-*` (Brainstorm → Plan → Work → Review → Compound) and `/cr-*` (research loop for econometrics, ML, writing, and replication). Covers how to use each command, when to use it, scenarios, and when NOT to use it. |
| [context-files.md](context-files.md) | Deep dive on the three context files — `copilot-instructions.md`, `compound-gpid.md`, and `compound-gpid.context.md` — how they relate, how they are created and updated, and practical management advice |
| [reference.md](reference.md) | Quick-reference tables: all commands, agents, skills, configuration fields, auto-escalation rules, directory structure, and document schemas |
| [troubleshooting.md](troubleshooting.md) | Known issues and step-by-step fixes |

## Quick orientation

Compound GPID is a structured workflow for AI-assisted development. The typical path through a task is:

**Engineering** (`/cg-*`):
```
/cg-brainstorm → /cg-plan → /cg-plan-review → /cg-work → /cg-review → /cg-fix-triage → /cg-compound
```

**Research** (`/cr-*`, requires `modules: "engineering, research"` in `compound-gpid.local.md`):
```
/cr-brainstorm → /cr-plan → /cr-work → /cr-review → /cr-compound
```

Short on time? Use [Reference](reference.md) to look up a specific command. Starting fresh? See [Installation](installation.md). Resuming interrupted work? Run `/cg-resume` in Copilot Chat.
