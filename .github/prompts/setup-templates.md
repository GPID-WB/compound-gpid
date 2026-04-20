# Setup Templates Reference

Templates used by `/cg-setup`. Loaded on-demand — do not bulk-load at prompt start.

---

## compound-gpid.context.md Template

```markdown
# Project Context

Additional context for Copilot and the Compound GPID plugin. Edit freely —
this file is committed to git and shared with the team.

## Data Sources
<!-- Where does data come from? File paths, databases, APIs, vintage conventions -->

## Domain Rules
<!-- Project-specific rules that Copilot should always follow -->

## Work in Progress
<!-- Modules, features, or migrations currently underway -->

## Workspace Notes
<!-- Related folders, dependencies on other projects in the VS Code workspace -->
```

> This file is committed to git. Do NOT add it to `.gitignore`.
> It is loaded by Step 0 in every `/cg-*` prompt.

---

## compound-gpid.local.md Template

```markdown
---
language: "<r|python|stata|both|all|other>"
project-type: "<package|analysis|dashboard|api|tool|other>"
review-depth: "<light|standard|thorough>"
created: "YYYY-MM-DD"
cg-schema-version: ""
---
```

> **Note**: `cg-schema-version` is intentionally blank for new projects. `cg-update`
> populates this field with the current schema version when run from the project root.
> `/cg-resume` will nudge the user to run `cg-update` if this field is blank or
> mismatched — that is the intended migration prompt.

# Compound GPID — Project Config

This file configures Compound GPID for this project. It is gitignored and local to your machine.

## Language: <language>
## Project Type: <project-type>
## Review Depth: <review-depth>

## Notes
<Any additional project-specific notes the user mentioned>
```

---

## compound-gpid.md Charter Template

When filling in YAML string fields, escape any `"` characters as `\"`, or wrap values containing double quotes in single quotes.

```markdown
---
project-name: "<name>"
team: "<team-name>"
created: "YYYY-MM-DD"
last-reviewed: "YYYY-MM-DD"
---

# <Project Name>

## Objective

<!-- TODO: Describe what this project is building and who it is for. -->

## Key Deliverables

<!-- TODO: List concrete outputs, e.g. R package, REST API, harmonized dataset. -->

## Constraints

<!-- TODO: Add hard constraints, e.g. reproducibility requirements, data privacy rules. -->

## Current Focus

<!-- TODO: What is the team working on right now? 1-2 sentences. Update whenever priorities shift. -->
```

> These are the only four sections. If content doesn't fit one of them,
> it belongs elsewhere — architecture notes go in `copilot-instructions.md`
> or a skill file; historical decisions go in `.cg-docs/brainstorms/`;
> removed content goes in `.cg-docs/archive/charter-history.md`.

### Charter field formatting rules

- **Objective** (Q5): Place the user's text as 1-3 sentences of prose.
- **Key Deliverables** (Q6): Format as a bulleted Markdown list (`- item`), one deliverable per bullet.
- **Constraints** (Q7): Format as a bulleted Markdown list (`- constraint`), one constraint per bullet.

Do not embellish, rewrite, or add items the user did not mention. Use the user's
wording directly, only correcting obvious typos or grammar.

Set `last-reviewed` to today's date (the date the charter is created).

### Charter placeholder rules

- Team (Q4.5 skipped): use `"DECDG / GPID -- World Bank"` (default)
- Objective (Q5 skipped): `<!-- TODO: Describe what this project is building and who it is for. -->`
- Key Deliverables (Q6 skipped): `<!-- TODO: List concrete outputs, e.g. R package, REST API, harmonized dataset. -->`
- Constraints (Q7 skipped): `<!-- TODO: Add hard constraints, e.g. reproducibility requirements, data privacy rules. -->`
- Current Focus: `<!-- TODO: What is the team working on right now? 1-2 sentences. Update whenever priorities shift. -->`

---

## .cg-docs/ Directory Scaffold

Create the following directories and `.gitkeep` files if they do not already exist:

```
.cg-docs/
├── archive/
│   └── .gitkeep
├── brainstorms/
│   └── .gitkeep
├── plans/
│   └── .gitkeep
├── reviews/
│   └── .gitkeep
├── strategy/
│   └── .gitkeep
└── solutions/
    ├── build-errors/
    │   └── .gitkeep
    ├── bugs/
    │   └── .gitkeep
    ├── data-quality/
    │   └── .gitkeep
    ├── environment-issues/
    │   └── .gitkeep
    ├── git-workflows/
    │   └── .gitkeep
    ├── performance-issues/
    │   └── .gitkeep
    └── testing-patterns/
        └── .gitkeep
```

---

## roadmap.json Initial Skeleton

```json
{
  "schemaVersion": "compound-gpid-roadmap-v1",
  "milestones": []
}
```

This file tracks project milestones and features. Users can add milestones
and ideas by invoking `@cg-roadmap` in Copilot Chat.

---

## Setup Complete Message

```
## Setup Complete ✅

**Language**: <language>
**Project Type**: <project-type>
**Review Depth**: <review-depth>

### Available Commands (in Copilot Chat)
- `/cg-resume`          — Load context and pick up interrupted work
- `/cg-strategy`        — Structure a full project vision into milestones and features
- `/cg-ideate`          — Discover high-value improvements to work on next
- `/cg-brainstorm`      — Clarify fuzzy requirements through guided Q&A
- `/cg-plan`            — Research the codebase and create an implementation plan
- `/cg-work`            — Implement a plan step by step
- `/cg-fixbug`          — Structured bug-fix: reproduce, diagnose, fix, verify, document
- `/cg-review`          — Run multi-agent code review
- `/cg-fix-triage`      — Apply review findings by ID or priority level
- `/cg-compound`        — Capture a solved problem as reusable knowledge
- `/cg-compound-refresh` — Audit and refresh .cg-docs/solutions/ for staleness
- `@cg-roadmap`         — Add milestones, features, and ideas to your project roadmap

### PowerShell Commands (in terminal)
- `cg-update` — Pull latest Compound GPID updates
- `cg-unlink` — Disconnect this project from Compound GPID

### Next Steps

**If you have a vision for the full project scope:**
→ Run `/cg-strategy` to think through your ideas and build an initial
  milestone and feature structure

**If requirements for a specific task are fuzzy:**
→ Run `/cg-brainstorm` to clarify before planning

**If you already know what to build:**
→ Run `/cg-plan` to create an implementation plan
```

---

## Mode B: Missing Directories Scaffold

Check for each of the following directories. Create any that are missing (with a `.gitkeep` inside),
without touching existing files:

```
.cg-docs/archive/
.cg-docs/brainstorms/
.cg-docs/plans/
.cg-docs/solutions/build-errors/
.cg-docs/solutions/bugs/
.cg-docs/solutions/data-quality/
.cg-docs/solutions/environment-issues/
.cg-docs/solutions/git-workflows/
.cg-docs/solutions/performance-issues/
.cg-docs/solutions/testing-patterns/
```

---

## Mode B: Context Summary Format

If `compound-gpid.md` exists:

```markdown
## Project Context

This project is **<project-name>**: <objective>.
Currently focused on: <current-focus>.

**Language**: <language>
**Project Type**: <project-type>
**Review Depth**: <review-depth>

### Prior Work
**Brainstorms** (<count>):
- YYYY-MM-DD: <title>
- ...

**Plans** (<count>):
- YYYY-MM-DD: <title> [status: active/completed]
- ...

**Captured Solutions** (<count> across <N> categories):
- bugs: <count>
- build-errors: <count>
- data-quality: <count>
- environment-issues: <count>
- git-workflows: <count>
- performance-issues: <count>
- testing-patterns: <count>
```

If `compound-gpid.md` does NOT exist, replace the first two lines with:

```
**No project charter found.**
```

And after presenting the summary, offer:

> "Would you like to create a project charter now? This helps Copilot
> understand your project's goals, deliverables, and constraints."
