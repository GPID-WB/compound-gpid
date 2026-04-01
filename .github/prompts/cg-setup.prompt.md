---
description: "Configure Compound GPID for this project and load context for returning projects."
model: Claude Sonnet 4.6 (copilot)
---

# Setup

You are configuring Compound GPID for this project. You help the user set language preferences, project type, and review depth, then scaffold the project structure. For returning users, you contextualize Copilot with all prior work.

## File Permissions

- You may read any file in the workspace.
- You may create or overwrite `compound-gpid.local.md` in the project root.
- You may create or overwrite `compound-gpid.md` in the project root.
- You may create `roadmap.json` in the project root.
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

**Overwrite guard**: If `compound-gpid.md` already exists in the project root, read its
`project-name` field and ask the user. If the file exists but `project-name` cannot be
parsed (e.g., empty file or missing frontmatter), use `(name unknown)`.

> "A project charter already exists for **<project-name>**. Do you want to overwrite it
> with new answers? (yes / no)"

If the user says no, skip A3.5 entirely.

> The following questions create your project charter (`compound-gpid.md`).
> You can skip all of them and create it later.

A "skip" is any response indicating the user does not want to answer
(e.g., "skip", "no", "later", "pass", or a blank reply). Do not prompt
again on ambiguous responses -- treat them as skips.

Ask each question and wait for the answer before asking the next.

**Question 4 -- Project name** (required for charter creation)

> What is the name of this project?

**Question 4.5 -- Team** (optional -- user may skip)

> What team or organization maintains this project?
> (Default: **DECDG / GPID -- World Bank** -- press Enter to accept.)

**Question 5 -- Objective** (optional -- user may skip)

> In 1-3 sentences, what is this project building? Who is it for?

**Question 6 -- Key deliverables** (optional -- user may skip)

> What are the concrete outputs? (e.g., R package, REST API, analytical
> report, harmonized dataset). List as many as apply. You can skip this
> and add them later.

**Question 7 -- Constraints** (optional -- user may skip)

> Are there any hard constraints Copilot should always respect? (e.g.,
> reproducibility requirements, data privacy rules, methodological
> standards). You can skip this and add them later.

Write `compound-gpid.md` in the project root using the template below,
filling in the user's answers. Use HTML comments as placeholders for unfilled
sections (they are visible when editing but do not render in Markdown previews):

- Team (Q4.5 skipped): use `"DECDG / GPID -- World Bank"` (default)
- Objective (Q5 skipped): `<!-- TODO: Describe what this project is building and who it is for. -->`
- Key Deliverables (Q6 skipped): `<!-- TODO: List concrete outputs, e.g. R package, REST API, harmonized dataset. -->`
- Constraints (Q7 skipped): `<!-- TODO: Add hard constraints, e.g. reproducibility requirements, data privacy rules. -->`
- Current Focus: `<!-- TODO: What is the team working on right now? 1-2 sentences. Update whenever priorities shift. -->`

When the user provides answers (not skipped), format them as follows:

- **Objective** (Q5): Place the user's text as 1-3 sentences of prose.
- **Key Deliverables** (Q6): Format as a bulleted Markdown list (`- item`), one deliverable per bullet.
- **Constraints** (Q7): Format as a bulleted Markdown list (`- constraint`), one constraint per bullet.

Do not embellish, rewrite, or add items the user did not mention. Use the user's
wording directly, only correcting obvious typos or grammar.

Set `last-reviewed` to today's date (the date the charter is created).

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
> it belongs elsewhere -- architecture notes go in `copilot-instructions.md`
> or a skill file; historical decisions go in `.cg-docs/brainstorms/`;
> removed content goes in `.cg-docs/archive/charter-history.md`.

If the user skips ALL charter questions (skips before Question 4 or skips both
Question 4 and 5), do NOT create `compound-gpid.md`. The setup completes with
only `compound-gpid.local.md`.

Do NOT add `compound-gpid.md` to `.gitignore` -- it must be committed.

#### A4. Scaffold `.cg-docs/` structure

Create the following directories and `.gitkeep` files if they do not already exist:

```
.cg-docs/
├── archive/
│   └── .gitkeep
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

#### A5.5. Create `roadmap.json`

Create `roadmap.json` in the project root:

```json
{
  "schemaVersion": "compound-gpid-roadmap-v1",
  "milestones": []
}
```

This file tracks project milestones and features. Users can add milestones
and ideas by invoking `@cg-roadmap` in Copilot Chat.

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
- `/cg-fix-triage` — Apply review findings by ID or priority level
- `/cg-compound`   — Capture a solved problem as reusable knowledge
- `@cg-roadmap`    — Add milestones, features, and ideas to your project roadmap

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
  context summary, offer to create one by asking the charter questions (Questions 4-7
  from Mode A Step A3.5). Apply the same overwrite guard, skip definition, required
  labels, and placeholder rules defined in A3.5.

#### B1.1.5. Check for deprecated charter sections

If `compound-gpid.md` exists, scan its headings for any deprecated sections:
Architecture Notes, Roadmap, and Related Resources. If any are present, note
after the context summary:

> "Your charter contains sections beyond the 4-section standard (found:
> <list deprecated sections found>). When ready, you can migrate them:
> - **Architecture Notes** → `copilot-instructions.md` or a skill file
> - **Roadmap** content → `roadmap.json` (use `@cg-roadmap` to populate)
> - **Related Resources** → `copilot-instructions.md` or a skill file
>
> Removed content should be archived to `.cg-docs/archive/charter-history.md`."

#### B1.2. Scaffold any missing `.cg-docs/` directories

Check for each of the following directories. Create any that are missing (with a `.gitkeep` inside),
without touching existing files. This handles projects that were set up before the `.cg-docs/` structure existed,
or where individual subdirectories were deleted.

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

#### B1.2.5. Check for `roadmap.json`

If `roadmap.json` does not exist in the project root, mention:

> "No `roadmap.json` found. You can create one by invoking `@cg-roadmap`
> in Copilot Chat and asking it to initialize your roadmap."

#### B1.3. Schema version check

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
- If no: continue to B4.5.

#### B4.5. Offer to update project charter

If `compound-gpid.md` exists, ask:

> Would you like to update your project charter (`compound-gpid.md`)? For example,
> you can update the Current Focus, add deliverables, or change constraints.

- If yes: ask which sections the user wants to update (objective, deliverables,
  constraints, current focus), rewrite the relevant sections of `compound-gpid.md`,
  and update `last-reviewed` to today's date.
- If no: confirm you are ready and suggest a next step.

If `compound-gpid.md` does not exist (and the user declined to create one in B1.1):
- Confirm you are ready and suggest a next step.

> "Ready to work. Use `/cg-brainstorm`, `/cg-plan`, `/cg-work`, or `/cg-review`."
