---
name: cg-skill-setup
description: "Configure Compound GPID for your project. Sets language preferences, project type, and review depth."
---

# Compound GPID Setup

> **Note**: This skill provides reference configuration knowledge consumed by prompts and agents.
> For interactive project setup, use the `/cg-setup` prompt in Copilot Chat instead.

Interactive setup to configure this project for the Compound GPID workflow.

## Installation Model

Compound GPID uses a **global clone + per-project junction** model on Windows:

1. **Global install** (once per machine): The repo is cloned to `C:\WBG\.compound-gpid`.
   Running `install.ps1` creates `cg-link`, `cg-unlink`, and `cg-update` as batch wrappers
   in `C:\WBG\.compound-gpid\bin\` and adds that directory to the user's PATH.

2. **Per-project link** (once per project): Running `cg-link` from a project root creates a
   directory junction from `.github/` in the project to `C:\WBG\.compound-gpid\.github/`.
   This makes all prompts, agents, and skills visible to VS Code and Copilot.

3. **Updates** (as needed): Running `cg-update` from anywhere runs `git pull` in the global clone.
   Because all projects point to the same shared directory via junctions, the update is
   instantly visible in every linked project — no per-project update step required.

4. **Per-project config**: Running `/cg-setup` in Copilot Chat creates `compound-gpid.local.md`
   with language, project type, and review depth preferences, and scaffolds the `.cg-docs/` structure.

### Key path conventions

| Path | Purpose | Committed? |
|------|---------|-----------|
| `compound-gpid.md` | Project charter: objectives, deliverables, constraints, current focus | Yes |
| `compound-gpid.local.md` | Shared config: language, review depth, and active suites | Yes (committed) |
| `.cg-docs/` | Brainstorms, plans, captured solutions | Yes |
| `c-research/` | Root-level CR research outputs, created when `cr` is active | Yes |
| `roadmap.json` | Milestone/feature tracking (future) | Yes |

## Optional Model Advisory Preferences

`compound-gpid.local.md` may contain a `model-advisory` block with user-selected
example IDs and effort preferences. Load `.opencode/shared/model-advisory.contract.md`
before interpreting it. The block is advisory only: the platform picker remains
authoritative, and setup must never write a runtime model, switch a model, set
reasoning effort, or create a dispatch rule from these values. Invalid or
unknown values should be reported and ignored in favor of bundled or
capability-only guidance.

## Process

## Configuration Workflow

### Step 1: Check Existing Config

Check if `compound-gpid.local.md` already exists in the project root.
- If it exists, read it and ask if the user wants to update it.
- If it doesn't exist, proceed with setup.

### Step 2: Ask Questions (One at a Time)

**Question 1: Language Preference**

> What is your preferred programming language for this project?
> 1. **R** (data.table + ggplot2)
> 2. **Python** (polars/numpy + plotnine/seaborn)
> 3. **Stata** (local macros + repkit for reproducibility)
> 4. **Both** (R and Python)
> 5. **All** (R, Python, and Stata)
> 6. **Other** (specify)

**Question 1b (only if R is selected): R Syntax Dialect**

> What R syntax style do you prefer for this project?
> 1. **data.table + collapse** — fast data manipulation and statistics; standard for GPID team. *(default, recommended)*
> 2. **tidyverse** — dplyr/tidyr verbs throughout; use when external coauthors need to read the code. Note: collapse is still used for weighted grouped statistics since there is no native tidyverse equivalent.

**Question 2: Project Type**

> What type of project is this?
> 1. **Package** (R package or Python package for distribution)
> 2. **Analysis** (data analysis, research, report)
> 3. **Dashboard** (Shiny, Streamlit, or similar)
> 4. **API** (REST API, web service)
> 5. **Tool** (CLI tool, utility, automation)
> 6. **Other** (specify)

**Question 3: Review Depth**

> What review depth do you want as default?
> 1. **Light** — `code-quality` + `testing` agents only. Best for quick fixes and small changes.
> 2. **Standard** — All 8 review agents. Best for most work. *(recommended)*
> 3. **Thorough** — All 8 agents + cross-referencing past learnings. Best for major features and refactors.

**Question 3.5: Active Suites**

> Which workflow suites should this project activate?
> 1. **Technical only** — `suites: [cg]` *(default)*
> 2. **Research only** — `suites: [cr]`
> 3. **Technical + research** — `suites: [cg, cr]`

### Step 3: Write Config

Ask Question 3.5 before writing the config, then substitute the selected value
for the `suites:` placeholder. The written frontmatter must contain exactly
`[cg]`, `[cr]`, or `[cg, cr]`; select `[cr]` or `[cg, cr]` whenever the project
requires research workflows.

Create `compound-gpid.local.md` in the project root with the following format:

```markdown
---
language: "<r|python|stata|both|all|other>"
suites: [<cg|cr|cg, cr>]
r-syntax: "<data.table-collapse|tidyverse>"  # Only when language includes R
project-type: "<package|analysis|dashboard|api|tool|other>"
review-depth: "<light|standard|thorough>"
created: "YYYY-MM-DD"
cg-schema-version: ""
---

# Compound GPID — Project Config

This file configures Compound GPID for this project. It is version-controlled and shared across the team.

## Language: <language>
## Project Type: <project-type>
## Review Depth: <review-depth>

## Notes
<Any additional project-specific notes or preferences>
```

### Step 3.5: Create project charter (compound-gpid.md)

After writing the local config, optionally create a committed project charter.

- Ask Questions 4-7 (project name, objective, key deliverables, constraints).
  - Q4 (project name) is required for charter creation.
  - Q5 (objective) is optional -- user may skip.
  - Q6 (key deliverables) and Q7 (constraints) are optional.
- **Overwrite guard**: if `compound-gpid.md` already exists, read its `project-name`
  field and confirm before overwriting. If the file exists but `project-name` cannot
  be parsed, use `(name unknown)`.
- Use HTML comment placeholders (`<!-- TODO: ... -->`) for skipped fields.
- Do NOT add `compound-gpid.md` to `.gitignore` -- it must be committed.
- If the user skips all charter questions, do not create the file.

### Step 4: Protect shared configuration

Ensure `compound-gpid.local.md` is not ignored. It declares team-wide language,
suite, and review defaults and must remain version-controlled.

### Step 5: Create .cg-docs/ Structure

If the `.cg-docs/` directory doesn't exist, create the full structure:

```
.cg-docs/
├── brainstorms/
│   └── .gitkeep
├── plans/
│   └── .gitkeep
└── solutions/
    ├── build-errors/
    │   └── .gitkeep
    ├── performance-issues/
    │   └── .gitkeep
    ├── testing-patterns/
    │   └── .gitkeep
    ├── data-quality/
    │   └── .gitkeep
    ├── environment-issues/
    │   └── .gitkeep
    └── git-workflows/
        └── .gitkeep
```

If the research suite is enabled (`suites:` includes `cr`), create the
root-level `c-research/` artifact-type directories (`evidence/`,
`manuscripts/`, `normative-decisions/`, `scoping/`, `derivations/`,
`specifications/`, `results/`, `replication/`, `eda/`, `measurement/`, and
`vintages/`). These are research outputs only; keep data and other inputs
outside the tree. If `cr` is disabled later, preserve an existing
`c-research/` workspace and its contents.

### Step 6: Confirm

```markdown
## Setup Complete ✅

**Language**: <language>
**Project Type**: <project-type>
**Review Depth**: <review-depth>

### Available Commands
- `/cg-brainstorm` — Clarify fuzzy requirements
- `/cg-plan` — Create an implementation plan
- `/cg-work` — Implement a plan step by step
- `/cg-review` — Run multi-agent code review
- `/cg-compound` — Capture a solved problem

### Next Steps
- Start with `/cg-brainstorm` if requirements are fuzzy
- Start with `/cg-plan` if you know what to build
- Jump to `/cg-work` if the plan already exists
```
