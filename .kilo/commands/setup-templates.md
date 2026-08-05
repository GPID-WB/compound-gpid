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

## Wiki Configuration
<!-- folder: wiki -->
<!-- audience: developers | researchers | end-users -->
<!-- tone: technical | conversational | formal -->
```

> This file is committed to git. Do NOT add it to `.gitignore`.
> It is loaded by Step 0 in every `/cg-*` prompt.

---

## compound-gpid.local.md Template

```markdown
---
language: "<r|python|stata|both|all|other>"
r-syntax: "<data.table-collapse|tidyverse>"
project-type: "<package|analysis|dashboard|api|tool|other>"
review-depth: "<light|standard|thorough>"
created: "YYYY-MM-DD"
cg-schema-version: ""
model-advisory:
  enabled: true
  examples: {}
  preferences: {}
---
```

> **Note**: Only include `r-syntax` if language is **R**, **Both**, or **All**. Omit this field for Python, Stata, or Other projects.
> **Note**: `cg-schema-version` is intentionally blank for new projects. `cg-update`
> populates this field with the current schema version when run from the project root.
> `/cg-resume` will nudge the user to run `cg-update` if this field is blank or
> mismatched — that is the intended migration prompt.
> `model-advisory` is optional user preference data. It can select advisory
> examples and effort language, but it never selects or changes the runtime model.

```markdown
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
- **YAML string fields**: Always wrap `project-name` and all YAML string fields in double quotes. If the value contains `"`, use single-quoted YAML strings instead. Example: `project-name: 'My Tool: v2 "beta"'`.

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
├── solutions/
│   ├── build-errors/
│   │   └── .gitkeep
│   ├── bugs/
│   │   └── .gitkeep
│   ├── data-quality/
│   │   └── .gitkeep
│   ├── environment-issues/
│   │   └── .gitkeep
│   ├── git-workflows/
│   │   └── .gitkeep
│   ├── performance-issues/
│   │   └── .gitkeep
│   └── testing-patterns/
│       └── .gitkeep
└── work-reports/
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
.cg-docs/work-reports/
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

---

## Charter Quality Gate

Run this gate in **Mode A** (before writing the charter) and **Mode B** (after reading the charter).

### How to use this gate

**Mode A** — validate the final charter content after the hybrid approve flow (Step A4), before writing to disk. If any blockers are found, loop back to the failing section and ask the user to provide content. Do not write the charter until all blockers are resolved.

**Mode B** — run the checks at Step B1.1.1. **Store results internally. Do NOT output anything at this step.** Defer all output to Step B3 (context summary), where blockers and warnings are appended to the summary.

### Blockers (P0/P1 — halt and require fix)

| Rule | Check | Remediation question |
|------|-------|----------------------|
| `project-name` missing | `project-name:` field is absent or empty in YAML frontmatter | "What is the name of this project?" |
| `<!-- TODO` placeholder | Any of these exact placeholder strings remain in the charter body: `<!-- TODO: Describe`, `<!-- TODO: List`, `<!-- TODO: Add`, `<!-- TODO: What` | Re-present the affected section and ask the user to replace the placeholder with real content |
| Empty `## Objective` | The `## Objective` heading is present but has no non-whitespace content before the next `##` | "In 1–3 sentences, what is this project building? Who is it for?" |

All blockers must be resolved before the charter is written. If a blocker cannot be resolved (user declines to answer), do not write the charter.

### Warnings (P2/P3 — note but proceed)

| Rule | Check |
|------|-------|
| `last-reviewed` blank | `last-reviewed:` field is absent or empty in YAML frontmatter |
| Empty optional sections | `## Constraints`, `## Key Deliverables`, or `## Current Focus` present but containing only whitespace or `<!-- TODO` content that was removed |

Warnings do not block writing. In **Mode B**, include them in the context summary as:
> "Charter note: [list warnings] (advisory — not blocking)."

### Mode B deferred-output format

At Step B1.1.1: run all checks silently. Store results internally. Do NOT output anything.

At Step B3, append to the context summary:
- If blockers found:
  > "⚠️ Your charter has issues that should be fixed:
  > - [list each blocker]
  > Would you like to fix them now? (yes / no)"
  If yes: ask the remediation question for each blocker and rewrite those sections. Set `last-reviewed` to today.
  If no: note and continue.
- If only warnings: include inline in the context summary as a note.
- If all clear: proceed silently (no output).

---

## Charter from Scanner Results

Used by Mode A Step A3 to render a charter draft from `@cg-project-scanner` output.

### Field mapping (scanner output → charter)

| Scanner field | Charter destination |
|---------------|-------------------|
| `Charter Draft Content > Project Name` | frontmatter `project-name:` |
| `Charter Draft Content > Objective` | `## Objective` body |
| `Charter Draft Content > Key Deliverables` | `## Key Deliverables` body |
| `Charter Draft Content > Constraints` | `## Constraints` body |
| `Setup Recommendations > Language` (action: skip or confirm) | `compound-gpid.local.md` `language:` field |
| `Setup Recommendations > Project type` (action: skip or confirm) | `compound-gpid.local.md` `project-type:` field |

`## Current Focus` — not scannable from project signals. Always insert the `<!-- TODO: What is the team working on right now? 1-2 sentences. Update whenever priorities shift. -->` placeholder.

For any field the scanner reports as `"not detected"`: insert the standard `<!-- TODO -->` placeholder. The quality gate (Mode A Step A4) will catch any remaining placeholders before writing.

### Confidence-action mapping

Use this table when processing the scanner's `Setup Recommendations` section:

| Confidence | Action  | UX behavior |
|------------|---------|-------------|
| high       | skip    | Set value silently. Inform user in a summary line: "Detected: \<value\> (\<evidence\>)" |
| medium     | confirm | Pre-fill and ask: "I detected \<value\>. Correct? (yes / change)" |
| low        | ask     | Show full question menu (from Fallback: Manual Questions). Mention the signal: "I found \<signal\> — is this \<interpretation\>?" |

Review depth is always `ask` regardless of scanner output — it is not detectable from files.

### Hybrid approve flow

After rendering the charter draft, present it in a fenced code block and offer three options:

```
Here's your project charter draft based on what I found:

<fenced code block containing the full draft compound-gpid.md>

**Options:**
1. **Approve as-is** — Write this charter and continue setup
2. **Walk through section by section** — Review and edit each section
3. **Start from scratch** — Ignore scanner results, ask questions manually
   (uses the Fallback: Manual Questions flow)
```

**Option 1 (Approve as-is)**: proceed directly to Step A4 (quality gate).

**Option 2 (Walk through)**: iterate over these sections in order:
- Objective, Key Deliverables, Constraints, Current Focus
- For each: display the inferred content, ask "Approve this section or edit it?"
- If "edit": accept freeform text as a replacement for that section's body.
- After all sections: proceed to Step A4 (quality gate).

**Option 3 (Start from scratch)**: display
> "Ignoring scanner results. Let's go through the setup questions."
Jump to the **Fallback: Manual Questions** block (Q4–Q7). After Q7, proceed to Step A4 (quality gate).

---

## Pre-flight Health Check

Used by Mode A Step A0.5. Run before dispatching `@cg-project-scanner`. Silent on success — only output on failure.

### Checks

Check for the existence of all four managed directories. All checks must pass to proceed:

| Directory | Failure message |
|-----------|----------------|
| `.github/prompts/` (must exist and contain `*.prompt.md` files) | "Prompts not visible — the junction may be broken or VS Code needs a restart. Re-run `cg-link` from the project root. (Run `cg-link` from the project root in the VS Code terminal — the script is in the `bin/` folder of your Compound GPID installation, or on PATH if you ran `install.ps1`.)" |
| `.github/skills/` | "Skills directory missing — `cg-link` may have partially failed. Re-run `cg-link`. (Run `cg-link` from the project root in the VS Code terminal — the script is in the `bin/` folder of your Compound GPID installation, or on PATH if you ran `install.ps1`.)" |
| `.github/agents/` | "Agents directory missing — `cg-link` may have partially failed. Re-run `cg-link`. (Run `cg-link` from the project root in the VS Code terminal — the script is in the `bin/` folder of your Compound GPID installation, or on PATH if you ran `install.ps1`.)" |
| `.github/instructions/` | "Instructions directory missing — `cg-link` may have partially failed. Re-run `cg-link`. (Run `cg-link` from the project root in the VS Code terminal — the script is in the `bin/` folder of your Compound GPID installation, or on PATH if you ran `install.ps1`.)" |

### Behavior

- All checks pass: proceed silently. Do not mention the health check to the user.
- Any check fails: display the failure message for the failing check and **stop setup**. Do not proceed to scanner dispatch or any subsequent step.

---

## Roadmap Bootstrap from Charter

Used by Mode A Step A5.7 after the charter has been written (or skipped).

### Trigger conditions

**If the charter was NOT written** (user skipped all charter questions and Step A4.5 was skipped or declined): create an empty `roadmap.json` skeleton using the existing **roadmap.json Initial Skeleton** template from this file. This is the only path to an empty skeleton.

**If the charter was written** with a non-empty, non-placeholder `## Current Focus` section: create `roadmap.json` with one milestone seeded from the Current Focus content.

> Note: The `<!-- TODO -->` placeholder case cannot reach this step because the quality gate (Step A4) eliminates all `<!-- TODO -->` occurrences before A4.5 writes the charter.

### Seeded milestone JSON structure

```json
{
  "schemaVersion": "compound-gpid-roadmap-v1",
  "milestones": [
    {
      "id": "<slugified-current-focus-first-5-words>",
      "title": "<first sentence of Current Focus>",
      "objective": "<full Current Focus content>",
      "status": "in-progress",
      "features": [
        {
          "id": "initial-focus",
          "title": "<first sentence of Current Focus>",
          "status": "in-progress",
          "plan": null
        }
      ]
    }
  ]
}
```

**Slugifying rules**: take the first 5 words of the Current Focus, lowercase, replace spaces and punctuation with hyphens, strip leading/trailing hyphens.

**JSON string escaping**: When embedding Current Focus text into JSON `title` and `objective` string values, escape `"` as `\"`, `\` as `\\`, and replace literal newlines with `\n`. Verify the resulting JSON is valid before writing.
