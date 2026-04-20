# Context Files

Compound GPID uses three files to give Copilot project-specific context. Each file has a different purpose, lifecycle, and audience. Understanding the relationship between them is essential for getting the most out of every Copilot session.

---

## The Three Files at a Glance

| File | Purpose | Committed? | Who creates it | Who updates it |
|------|---------|-----------|---------------|----------------|
| `.github/copilot-instructions.md` | Permanent, per-session instructions — project identity + pointers to the other two files | Yes (managed) | `cg-link` | `cg-update` (automatic) |
| `compound-gpid.md` | Project charter — strategic context (objective, deliverables, constraints, current focus) | Yes | `/cg-setup` | You + `/cg-strategy` |
| `compound-gpid.context.md` | Growing knowledge base — tactical facts (data sources, domain vocab, recurring gotchas) | Yes | `/cg-setup` | You + `/cg-compound` |

---

## How They Relate

```
cg-link / cg-update
        │
        │  reads template + config
        ▼
.github/copilot-instructions.md      ← VS Code loads this on every session
        │
        │  "Step 0: read these files"
        ├──► compound-gpid.md         (strategic context)
        └──► compound-gpid.context.md (tactical context)
```

`copilot-instructions.md` is the **entry point**: VS Code injects it into every Copilot session automatically. Its job is minimal — it establishes project identity (name, type, languages, review depth) and directs Copilot to read the other two files for substance.

`compound-gpid.md` is the **30,000-foot view**: what the project is trying to achieve, hard constraints that must never be broken, and what the team is working on right now.

`compound-gpid.context.md` is the **ground truth**: file paths, variable caveats, domain vocabulary, workspace layout, and any other recurring fact that would otherwise need to be re-explained at the start of each session.

---

## `.github/copilot-instructions.md`

### What it contains

The generated file covers four things:
1. Project identity (name, type, languages, review depth) — from your config files
2. Pointers instructing Copilot to read `compound-gpid.md` and `compound-gpid.context.md` at session start
3. Essential project-wide rules (fail loudly, commit lockfiles, conventional commits)
4. Workspace notes (principal folder; pointer to `## Workspace Notes` in `context.md` for multi-folder setups)

### How it is created

`cg-link` generates it the first time you link a project. The source is `.github/copilot-instructions.template.md` inside the Compound GPID install. Four template variables are substituted at generation time:

| Variable | Source |
|----------|--------|
| `{{project-name}}` | `project-name` field in `compound-gpid.md` YAML frontmatter |
| `{{project-type}}` | `project-type` field in `compound-gpid.local.md` |
| `{{languages}}` | `language` field in `compound-gpid.local.md` |
| `{{review-depth}}` | `review-depth` field in `compound-gpid.local.md` |

### How it is updated

`cg-update` regenerates the file automatically whenever you update Compound GPID. If you change `compound-gpid.local.md` (e.g., switch to a new review depth or add a language), run `cg-update` to pick up the change.

A `<!-- compound-gpid:managed -->` marker at the top signals that the file is managed. If `cg-update` finds the marker present, it regenerates. If the marker is missing, it leaves the file untouched.

### When and how to edit it

**Do not edit the generated file directly.** Changes will be overwritten on the next `cg-update` run.

Instead:
- To change project identity fields (name, type, language, review depth), edit `compound-gpid.local.md` or `compound-gpid.md` then run `cg-update`.
- To add custom rules or workspace-wide instructions that the template does not cover, **remove the `<!-- compound-gpid:managed -->` marker** from the top of the file, then edit freely. `cg-update` will detect that the marker is gone and leave your customised version untouched from that point on.

> ⚠️ Once you remove the managed marker, you are responsible for incorporating future Compound GPID template improvements manually. Run `cg-update` and inspect `.github/copilot-instructions.template.md` to see what changed.

---

## `compound-gpid.md` — The Project Charter

### What it contains

The charter has exactly four sections and YAML frontmatter:

```markdown
---
project-name: "My Project"
created: "2026-04-01"
last-reviewed: "2026-04-20"
---

## Objective
One-paragraph answer to: what is this project? Who does it serve? Why does it matter?

## Key Deliverables
Bullet list of concrete outputs — specific scripts, packages, APIs, reports.

## Constraints
Non-negotiable rules. Statistical correctness requirements, security rules, versioning policy.

## Current Focus
The milestone or theme the team is actively working on right now.
```

The four-section structure is enforced: if content doesn't fit neatly into one of these sections it doesn't belong in this file (put it in `compound-gpid.context.md` instead).

### How it is created

`/cg-setup` creates the file interactively by asking you about your project objective, deliverables, constraints, and language preferences. It also creates `compound-gpid.local.md` and `compound-gpid.context.md` at the same time.

### How it is updated

| What changes | How to update |
|-------------|---------------|
| **Current Focus** (ongoing, between milestones) | Run `/cg-strategy` — it updates this section and sets `last-reviewed` automatically |
| **Objective, Deliverables, or Constraints** | Edit the file directly with explicit intent; Copilot will not modify these sections without explicit user approval |
| **Removed content** | Archived automatically to `.cg-docs/archive/charter-history.md` — never deleted |

`/cg-resume` checks `last-reviewed` at session start and nudges you if it is missing or more than 30 days old.

### What does NOT belong here

- Data source file paths, column names, or environment-specific paths → put in `compound-gpid.context.md`
- Implementation notes, bug history, architecture decisions → put in `.cg-docs/`
- User preferences (language, review depth) → put in `compound-gpid.local.md`

---

## `compound-gpid.context.md` — The Growing Knowledge Base

### What it contains

Unlike the charter, this file has no fixed structure — organise it by topic. Typical sections:

```markdown
# Project Context

## Data Sources
- `data/raw/hies-2023.dta` — raw household survey, 2023 vintage. PPP: 2017.
  Do not overwrite; treat as read-only.
- `data/processed/` — pipeline outputs. Safe to delete and rebuild.

## Domain Vocabulary
- **Welfare aggregate**: per-capita daily consumption in 2017 PPP USD.
- **FGT indices**: Foster–Greer–Thorbecke. P0 = headcount, P1 = depth, P2 = severity.
- **Vintage**: the year of the PPP conversion factor used. Must match across all tables.

## Workspace Notes
This workspace has two folders:
- `gpid-main/` — production pipeline code (R + Stata)
- `gpid-api/` — FastAPI layer that serves the data

## Recurring Gotchas
- `hh_weight` is the household weight, not the individual weight. Always multiply by
  `hh_size` before summing across persons.
- Region codes changed from 3-letter to 2-letter in the 2023 vintage. `code_map.csv`
  provides the crosswalk.
```

### How it is created

`/cg-setup` creates a starter version with placeholder headings. If you skip the optional creation step, you can create the file manually or on the first run of `/cg-compound`.

### How it is updated

Two mechanisms:

1. **`/cg-compound`** — after you solve a non-trivial problem, run `/cg-compound`. It saves a solution doc to `.cg-docs/solutions/` and optionally extracts project-specific facts (recurring gotchas, data caveats) directly into `compound-gpid.context.md`. This is the primary mechanism by which the file grows.

2. **Manual edits** — edit the file directly at any time. There are no restrictions. Add a section, update a stale path, remove an outdated note.

### What makes a good context entry

Good entries are **durable facts** that would otherwise need to be re-explained at the start of every session:

- ✅ File paths and their meaning (`data/raw/hies-2023.dta — read-only; PPP 2017`)
- ✅ Variable-level caveats (`hh_weight is household-level, not person-level`)
- ✅ Workspace layout for multi-folder projects
- ✅ Domain vocabulary specific to your team or field
- ✅ Repeated gotchas that have caused bugs more than once

Bad entries are **transient or task-specific**:

- ❌ "I am currently working on the poverty decomposition feature" → this belongs in the charter's `Current Focus`
- ❌ Step-by-step implementation notes → these belong in `.cg-docs/plans/`
- ❌ Bug reports or fix descriptions → these belong in `.cg-docs/solutions/`

### Relationship to `.cg-docs/`

`compound-gpid.context.md` holds **facts that apply across all tasks**. `.cg-docs/` holds **task-specific artifacts** (brainstorms, plans, review reports, solution docs). Both are committed. The distinction:

- A data source path that every task needs to know → `context.md`
- The plan for implementing the poverty decomposition feature → `.cg-docs/plans/`
- The solution to the PPP vintage mismatch bug → `.cg-docs/solutions/bugs/`

---

## Practical Advice

### Getting started

1. Run `cg-link` in your project root — this creates `.github/copilot-instructions.md` from the template.
2. Run `/cg-setup` in Copilot Chat — this creates `compound-gpid.md`, `compound-gpid.local.md`, and `compound-gpid.context.md`.
3. Open `compound-gpid.context.md` right after setup and fill in your data source paths, workspace layout, and any domain vocabulary Copilot needs to know. Even a few bullet points pay off immediately.
4. Commit all three files.

### Keeping them up to date

| Trigger | Action |
|---------|--------|
| You changed a config field in `compound-gpid.local.md` (language, review-depth, etc.) | Run `cg-update` to regenerate `copilot-instructions.md` |
| Project objective or constraints changed | Edit `compound-gpid.md` directly, run `/cg-strategy` if Current Focus also needs updating |
| You just solved a non-trivial problem | Run `/cg-compound` — it updates `context.md` and `.cg-docs/solutions/` |
| A data source moved or a variable caveat changed | Edit `compound-gpid.context.md` directly |
| `/cg-resume` reports `last-reviewed` is stale | Run `/cg-strategy` to review and update the charter |
| New team member joins | They run `/cg-setup` (creates their personal `compound-gpid.local.md`); the committed `compound-gpid.md` and `compound-gpid.context.md` are already available |

### Common mistakes

**Putting tactical facts in the charter**
The charter is strategic and slow-changing. Avoid adding data paths, column names, or implementation details there — they make the charter noisy and get stale faster than strategic content. Put them in `context.md`.

**Not running `cg-update` after config changes**
If you update `compound-gpid.local.md` manually (e.g., add Python to the languages list), `copilot-instructions.md` will be out of sync until you run `cg-update`. The mismatch is silent — no warning is raised.

**Editing `copilot-instructions.md` directly without removing the managed marker**
Your edits will be silently overwritten on the next `cg-update`. If you want to customise the file, remove the `<!-- compound-gpid:managed -->` marker first.

**Letting `compound-gpid.context.md` go stale**
A stale context file is worse than no context file — it actively misleads Copilot. Review it whenever a major pipeline change happens (file renames, new datasets, schema changes). Add a quarterly "context.md review" to your team's sprint rhythm.

**Gitignoring `compound-gpid.context.md`**
This file is meant to be shared — it is institutional memory for the whole team, not personal config. Only `compound-gpid.local.md` is gitignored. Make sure `.gitignore` does not accidentally exclude `compound-gpid.context.md`.

---

## Summary Table

| | `.github/copilot-instructions.md` | `compound-gpid.md` | `compound-gpid.context.md` |
|--|---|---|---|
| **When Copilot reads it** | Every session (VS Code auto-injects) | Step 0 of every `/cg-*` prompt | Step 0 of every `/cg-*` prompt |
| **Created by** | `cg-link` | `/cg-setup` | `/cg-setup` |
| **Updated by** | `cg-update` (automatic) | You + `/cg-strategy` | You + `/cg-compound` |
| **Structure** | Fixed (from template) | Fixed (4 sections) | Free-form (by topic) |
| **Committed to git** | Yes | Yes | Yes |
| **Gitignored** | No | No | No |
| **Edit directly?** | No (remove marker first) | Yes (body requires approval) | Yes, freely |
| **Grows over time?** | No (regenerated from template) | Slowly (charter is stable) | Yes (this is the point) |
| **Content type** | Identity + pointers | Strategy | Tactics + facts |
