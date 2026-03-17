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
   with language, project type, and review depth preferences, and scaffolds the `docs/` structure.

### Key path conventions

| Path | Purpose |
|------|---------|
| `C:\WBG\.compound-gpid` | Global clone of this repo |
| `<project>/.github` | Junction pointing to `C:\WBG\.compound-gpid\.github` |
| `<project>/compound-gpid.local.md` | Project-specific config (gitignored) |
| `<project>/docs/` | Brainstorms, plans, and captured solutions |

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

### Step 3: Write Config

Create `compound-gpid.local.md` in the project root with the following format:

```markdown
---
language: "<r|python|stata|both|all|other>"
project-type: "<package|analysis|dashboard|api|tool|other>"
review-depth: "<light|standard|thorough>"
created: "YYYY-MM-DD"
---

# Compound GPID — Project Config

This file configures Compound GPID for this project. It is gitignored and local to your machine.

## Language: <language>
## Project Type: <project-type>
## Review Depth: <review-depth>

## Notes
<Any additional project-specific notes or preferences>
```

### Step 4: Update .gitignore

Check if `compound-gpid.local.md` is in `.gitignore`. If not, add it:

```gitignore
# Compound GPID local config
compound-gpid.local.md
```

### Step 5: Create docs/ Structure

If the `docs/` directory doesn't exist, create the full structure:

```
docs/
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
