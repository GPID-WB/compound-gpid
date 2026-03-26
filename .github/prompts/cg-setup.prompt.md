# Setup

You are configuring Compound GPID for this project. You help the user set language preferences, project type, and review depth, then scaffold the project structure. For returning users, you contextualize Copilot with all prior work.

## File Permissions

- You may read any file in the workspace.
- You may create or overwrite `compound-gpid.local.md` in the project root.
- You may create or overwrite `compound-gpid.md` in the project root.
- You may create new files and directories under `.cg-docs/`.
- You may append lines to `.gitignore` and `.Rbuildignore`.
- You must not modify any other existing file.
- You must not create files outside the project root or `.cg-docs/`.

## Process

### Step 1: Detect Project State

Check whether `compound-gpid.local.md` exists in the project root.

- If it **does not exist**: this is a **new project** — follow Mode A.
- If it **does exist**: this is a **returning project** — follow Mode B.

---

### Mode A: New Project Setup

#### A1. Confirm junction is in place

If this prompt is running, the `.github/` junction already exists — that is the only way this prompt is available in Copilot Chat. Acknowledge this to the user:

> "Compound GPID is linked to this project. Let's configure it."

#### A2. Ask questions one at a time

Ask each question and wait for the answer before asking the next.

**Question 1 — Language**

> What is your preferred programming language for this project?
>
> 1. **R** (collapse + data.table + ggplot2)
> 2. **Python** (polars/numpy + plotnine/seaborn)
> 3. **Stata** (local macros + repkit for reproducibility)
> 4. **Both** (R and Python)
> 5. **All** (R, Python, and Stata)
> 6. **Other** (specify)

**Question 2 — Project type**

> What type of project is this?
>
> 1. **Package** (R package or Python package for distribution)
> 2. **Analysis** (data analysis, research, report)
> 3. **Dashboard** (Shiny, Streamlit, or similar)
> 4. **API** (REST API, web service)
> 5. **Tool** (CLI tool, utility, automation)
> 6. **Other** (specify)

**Question 3 — Review depth**

> What review depth do you want as default?
>
> 1. **Light** — `cg-code-quality` + `cg-testing` only. Best for quick fixes.
> 2. **Standard** — All 8 review agents. Best for most work. *(recommended)*
> 3. **Thorough** — All 8 agents + cross-referencing past learnings. Best for major features.

#### A3. Create `compound-gpid.local.md`

Write the config file to the project root:

```markdown
---
language: "<r|python|stata|both|all|other>"
project-type: "<package|analysis|dashboard|api|tool|other>"
review-depth: "<light|standard|thorough>"
created: "YYYY-MM-DD"
cg-schema-version: ""
---

# Compound GPID — Project Config

This file configures Compound GPID for this project. It is gitignored and local to your machine.

## Language: <language>
## Project Type: <project-type>
## Review Depth: <review-depth>

## Notes
<Any additional project-specific notes the user mentioned>
```

#### A3.5. Create project charter (`compound-gpid.md`)

> The following questions create your project charter (`compound-gpid.md`).
> You can skip all of them and create it later.

Ask each question and wait for the answer before asking the next.

**Question 4 — Project name**

> What is the name of this project?

**Question 5 — Objective**

> In 1–3 sentences, what is this project building? Who is it for?

**Question 6 — Key deliverables** (optional — user may skip)

> What are the concrete outputs? (e.g., R package, REST API, analytical
> report, harmonized dataset). List as many as apply. You can skip this
> and add them later.

**Question 7 — Constraints** (optional — user may skip)

> Are there any hard constraints Copilot should always respect? (e.g.,
> reproducibility requirements, data privacy rules, methodological
> standards). You can skip this and add them later.

Write `compound-gpid.md` in the project root using the template below,
filling in the user's answers. Leave unfilled sections with placeholder text:

- Architecture Notes: `<Describe the project structure here, or let Copilot fill this in after examining the codebase.>`
- Current Focus: `<What is the team working on right now? Update this section as priorities change.>`
- Roadmap: `<Add milestones here. In the future, create roadmap.json for structured tracking.>`
- Related Resources: `<Add links to external docs, specs, or methodology references.>`

```markdown
---
project-name: "<name>"
team: "DECDG / GPID — World Bank"
created: "YYYY-MM-DD"
last-updated: "YYYY-MM-DD"
---

# <Project Name>

## Objective

<1–3 sentences from Question 5>

## Key Deliverables

<Bulleted list from Question 6, or placeholder>

## Constraints

<Bulleted list from Question 7, or placeholder>

## Architecture Notes

<Describe the project structure here, or let Copilot fill this in after examining the codebase.>

## Current Focus

<What is the team working on right now? Update this section as priorities change.>

## Roadmap

<Add milestones here. In the future, create roadmap.json for structured tracking.>

## Related Resources

<Add links to external docs, specs, or methodology references.>
```

If the user skips ALL charter questions (skips before Question 4 or skips Question 4 and 5),
do NOT create `compound-gpid.md`. The setup completes with only `compound-gpid.local.md`.

Do NOT add `compound-gpid.md` to `.gitignore` — it must be committed.

#### A4. Scaffold `.cg-docs/` structure

Create the following directories and `.gitkeep` files if they do not already exist:

```
.cg-docs/
├── brainstorms/
│   └── .gitkeep
├── plans/
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

#### A4.5. Update `.Rbuildignore` (R packages only)

If the user selected **Package** as project type AND the language is **R** or **Both**:

Check if `.Rbuildignore` exists. If it does not, create it. Append the following line if it is not already present:

```
^\.cg-docs$
```

This prevents `.cg-docs/` from being included in the built R package.

#### A5. Update `.gitignore`

Check if `.gitignore` exists. If it does not, create it. Append the following lines if they are not already present:

```gitignore
# Compound GPID local config (user-specific, never commit)
compound-gpid.local.md
```

#### A6. Print Setup Complete

```
## Setup Complete ✅

**Language**: <language>
**Project Type**: <project-type>
**Review Depth**: <review-depth>

### Available Commands (in Copilot Chat)
- `/cg-resume`     — Load context and pick up interrupted work
- `/cg-brainstorm` — Clarify fuzzy requirements through guided Q&A
- `/cg-plan`       — Research the codebase and create an implementation plan
- `/cg-work`       — Implement a plan step by step
- `/cg-fixbug`     — Structured bug-fix: reproduce, diagnose, fix, verify, document
- `/cg-review`     — Run multi-agent code review
- `/cg-compound`   — Capture a solved problem as reusable knowledge

### PowerShell Commands (in terminal)
- `cg-update` — Pull latest Compound GPID updates
- `cg-unlink` — Disconnect this project from Compound GPID

### Next Steps
- Start with `/cg-brainstorm` if requirements are fuzzy
- Start with `/cg-plan` if you know what to build
- Jump to `/cg-work` if a plan already exists
```

---

### Mode B: Returning Project — Contextualize Copilot

#### B1. Read existing config

Read `compound-gpid.local.md` and report the current settings (language, project type, review depth).

#### B1.1. Read project charter

Check if `compound-gpid.md` exists in the project root.

- If it exists: read it and extract the `project-name`, Objective, and Current Focus
  for use in the context summary (Step B3).
- If it does not exist: note that no project charter exists. After presenting the
  context summary, offer to create one by asking the charter questions (Questions 4–7
  from Mode A Step A3.5).

#### B1.5. Scaffold any missing `.cg-docs/` directories

Check for each of the following directories. Create any that are missing (with a `.gitkeep` inside),
without touching existing files. This handles projects that were set up before the `.cg-docs/` structure existed,
or where individual subdirectories were deleted.

```
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

#### B1.6. Schema version check

Check if `compound-gpid.local.md` contains a `cg-schema-version` field. If the field is missing or empty, add a note:

> "This project may need a structural migration. Run `cg-update` from this project's root to apply any pending migrations."

#### B2. Scan existing work

Scan the following directories and collect the titles and dates from the YAML frontmatter (or filename) of each file:

- `.cg-docs/brainstorms/` — list each brainstorm with date and title
- `.cg-docs/plans/` — list each plan with date, title, and status
- `.cg-docs/solutions/` — list each solution by category, date, and title

#### B3. Present context summary

Present a structured summary to orient Copilot and the user.

If `compound-gpid.md` exists, use this format:

```
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

If `compound-gpid.md` does NOT exist, use the same format but replace the first two lines with:

```
**No project charter found.**
```

And after presenting the summary, offer:

> "Would you like to create a project charter now? This helps Copilot
> understand your project's goals, deliverables, and constraints."

#### B4. Offer to update config

Ask:

> Would you like to update any configuration (language, project type, or review depth)?

- If yes: ask the relevant questions (only those the user wants to change) and rewrite `compound-gpid.local.md`.
- If no: confirm you are ready and suggest a next step:
  > "Ready to work. Use `/cg-brainstorm`, `/cg-plan`, `/cg-work`, or `/cg-review`."
