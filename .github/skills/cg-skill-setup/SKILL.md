---
name: cg-skill-setup
description: "Configure Compound GPID for your project. Sets language preferences, project type, and review depth."
---

# Compound GPID Setup

Interactive setup to configure this project for the Compound GPID workflow.

## Process

### Step 1: Check Existing Config

Check if `compound-gpid.local.md` already exists in the project root.
- If it exists, read it and ask if the user wants to update it.
- If it doesn't exist, proceed with setup.

### Step 2: Ask Questions (One at a Time)

**Question 1: Language Preference**

> What is your preferred programming language for this project?
> 1. **R** (data.table + ggplot2)
> 2. **Python** (polars/numpy + plotnine/seaborn)
> 3. **Both** (R and Python)
> 4. **Other** (specify)

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
language: "<r|python|both|other>"
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
