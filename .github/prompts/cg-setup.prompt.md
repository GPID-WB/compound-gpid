---
description: "Configure Compound GPID for this project and load context for returning projects."
model: Claude Haiku 4.5 (copilot)
# Model: Haiku 4.5 — configuration task; reasoning=2, creativity=1. See docs/model-guide.md (2026-04-07 audit).
---

# Setup

You are configuring Compound GPID for this project. You help the user set language preferences, project type, and review depth, then scaffold the project structure. For returning users, you contextualize Copilot with all prior work.

## File Permissions

- You may read any file in the workspace.
- You may create or overwrite `compound-gpid.local.md` in the project root.
- You may create or overwrite `compound-gpid.md` in the project root.
- You may create `compound-gpid.context.md` in the project root.
- You may create `roadmap.json` in the project root.
- You may create new files and directories under `.cg-docs/`.
- You may append lines to `.gitignore` and `.Rbuildignore`.
- You must not modify any other existing file.
- You must not create files outside the project root or `.cg-docs/`.

## Process

### Step 1: Detect Project State

If `compound-gpid.local.md` exists in the project root: **returning project** — follow Mode B. Otherwise: **new project** — follow Mode A.

---

### Mode A: New Project Setup

#### A1. Confirm junction is in place

1. Check if `.github/prompts/setup-templates.md` exists. If not, stop: "Setup template file missing — re-run `cg-link` to restore it."
2. Acknowledge: > "Compound GPID is linked to this project. Let's configure it."

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

Read `.github/prompts/setup-templates.md` (load once — it covers all templates used through Step A6 and Mode B). Write `compound-gpid.local.md` to the project root using the **compound-gpid.local.md Template** from `setup-templates.md`.

#### A3.5. Create project charter (`compound-gpid.md`)

**Overwrite guard**: If `compound-gpid.md` already exists, read its `project-name` field and ask:
> "A project charter already exists for **<project-name>**. Do you want to overwrite it with new answers? (yes / no)"
If the user says no, skip A3.5 entirely. If `project-name` cannot be parsed, use `(name unknown)`.

> The following questions create your project charter (`compound-gpid.md`). You can skip all of them and create it later.

A "skip" is any response indicating the user does not want to answer (e.g., "skip", "no", "later", "pass", or blank). Treat ambiguous responses as skips.

Ask each question and wait for the answer before asking the next.

**Question 4 — Project name** (required for charter creation)

> What is the name of this project?

**Question 4.5 — Team** (optional -- user may skip)

> What team or organization maintains this project?
> (Default: **DECDG / GPID -- World Bank** -- press Enter to accept.)

**Question 5 — Objective** (optional -- user may skip)

> In 1-3 sentences, what is this project building? Who is it for?

**Question 6 — Key deliverables** (optional -- user may skip)

> What are the concrete outputs? (e.g., R package, REST API, analytical
> report, harmonized dataset). List as many as apply. You can skip this
> and add them later.

**Question 7 — Constraints** (optional -- user may skip)

> Are there any hard constraints Copilot should always respect? (e.g.,
> reproducibility requirements, data privacy rules, methodological
> standards). You can skip this and add them later.

Write `compound-gpid.md` using the **compound-gpid.md Charter Template** from `setup-templates.md`, filling in the user's answers. If the user skips ALL charter questions (skips before Question 4 or skips Q4), do NOT create `compound-gpid.md`. Do NOT add `compound-gpid.md` to `.gitignore`.

#### A3.6. Create `compound-gpid.context.md`

**Overwrite guard**: If `compound-gpid.context.md` already exists, skip this step.

Create `compound-gpid.context.md` using the **compound-gpid.context.md Template** from `setup-templates.md`. Do NOT add it to `.gitignore` — it is institutional knowledge and must be committed.

#### A3.7. Ask about workspace folders (optional)

> Are there other folders in your VS Code workspace related to this project? If so, describe each folder and what it contains. (Press Enter to skip.)

If the user provides descriptions and `compound-gpid.context.md` exists: append to `## Workspace Notes`:
```markdown
- **<folder-name>**: <description>
```
If `compound-gpid.context.md` does not exist: > "Folder descriptions cannot be saved — no `compound-gpid.context.md` exists. Re-run `/cg-setup` and choose to create it."

#### A4. Scaffold `.cg-docs/` structure

Using the **.cg-docs/ Directory Scaffold** from `setup-templates.md`, create the listed directories and `.gitkeep` files if they do not already exist.

#### A4.5. Update `.Rbuildignore` (R packages only)

If the user selected **Package** and language is **R**, **Both**, or **All**: check if `.Rbuildignore` exists (create if not) and append the following line if not already present:

```
^\.cg-docs$
```

#### A5. Update `.gitignore`

Check if `.gitignore` exists (create if not). Append if not already present:

```gitignore
# Compound GPID local config (user-specific, never commit)
compound-gpid.local.md
```

#### A5.5. Create `roadmap.json`

Create `roadmap.json` in the project root using the **roadmap.json Initial Skeleton** from `setup-templates.md`. Users can add milestones and ideas via `@cg-roadmap`.

#### A6. Print Setup Complete

Using the **Setup Complete Message** from `setup-templates.md`, display it with the user's configured language, project type, and review depth.

---

### Mode B: Returning Project — Contextualize Copilot

#### B1. Read existing config

Read `compound-gpid.local.md` and report current settings (language, project type, review depth).

#### B1.1. Read project charter

- If `compound-gpid.md` exists: read it and extract `project-name`, Objective, and Current Focus for the context summary (Step B3).
- If it does not exist: note no charter. After the context summary, offer to create one using Questions 4–7 (including 4.5) from Mode A Step A3.5 — same overwrite guard, skip definition, and placeholder rules apply.

#### B1.1.3. Check for `compound-gpid.context.md`

- If it does not exist: offer to create it:
  > "No `compound-gpid.context.md` found. This file stores project-specific context that grows over time. Create it now? (yes / no)"
  - If yes: create using the **compound-gpid.context.md Template** from `setup-templates.md`. Do NOT add it to `.gitignore` — it is institutional knowledge and must be committed.
  - If no: skip silently.
- If it exists: skip silently.

#### B1.1.5. Check for deprecated charter sections

If `compound-gpid.md` exists, scan headings for deprecated sections: Architecture Notes, Roadmap, Related Resources. If any are present, note after the context summary:
> "Your charter contains sections beyond the 4-section standard (found: <list>). When ready, you can migrate them:
> - **Architecture Notes** → `copilot-instructions.md` or a skill file
> - **Roadmap** content → `roadmap.json` (use `@cg-roadmap` to populate)
> - **Related Resources** → `copilot-instructions.md` or a skill file
>
> Removed content should be archived to `.cg-docs/archive/charter-history.md`. The user should manually perform this archiving — this prompt does not do it."

#### B1.2. Scaffold any missing `.cg-docs/` directories

Using the **Mode B: Missing Directories Scaffold** from `setup-templates.md`, create any missing directories (with `.gitkeep`), without touching existing files.

#### B1.2.5. Check for `roadmap.json`

If `roadmap.json` does not exist, mention: > "No `roadmap.json` found. This project was likely set up with an older version of Compound GPID. To add it, invoke `@cg-roadmap` and ask it to initialize your roadmap."

#### B1.3. Schema version check

If `compound-gpid.local.md` is missing a `cg-schema-version` field, note: > "This project may need a structural migration. Run `cg-update` from this project's root to apply any pending migrations."

#### B2. Scan existing work

Scan and collect YAML frontmatter (or filename) titles and dates from:
- `.cg-docs/brainstorms/` — date and title
- `.cg-docs/plans/` — date, title, and status
- `.cg-docs/solutions/` — category, date, and title

#### B3. Present context summary

Present a structured summary to orient Copilot and the user. Using the **Mode B: Context Summary Format** from `setup-templates.md` (read it now with `read_file` if not already in context), fill in the scanned data.

#### B4. Offer to update config

Ask:

> Would you like to update any configuration (language, project type, or review depth)?

- If yes: ask the relevant questions (only those the user wants to change) and rewrite `compound-gpid.local.md`.
- If no: continue to B4.5.

#### B4.5. Offer to update project charter

If `compound-gpid.md` exists, ask:
> "Would you like to update your project charter (`compound-gpid.md`)? For example, update the Current Focus, add deliverables, or change constraints."
- If yes: ask which sections to update (objective, deliverables, constraints, current focus), rewrite those sections, and set `last-reviewed` to today.
- If no (or charter does not exist and user declined to create one): continue to B4.7.

#### B4.7. Ask about workspace folders (optional)

> Are there other folders in your VS Code workspace related to this project? If so, describe each folder and what it contains. (Press Enter to skip.)

If the user provides descriptions and `compound-gpid.context.md` exists: append to its `## Workspace Notes` section:
```markdown
- **<folder-name>**: <description>
```
If `compound-gpid.context.md` does not exist, offer to create it first (see B1.1.3).

> "Ready to work. Use `/cg-brainstorm`, `/cg-plan`, `/cg-work`, or `/cg-review`."
