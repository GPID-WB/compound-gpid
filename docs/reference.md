# Reference

Quick reference for all Compound GPID commands, agents, skills, configuration, and file structure.

> See [Workflow](workflow.md) for a full explanation of each prompt step. See [Installation](installation.md) for setup instructions. See [Context Files](context-files.md) for a detailed guide to `copilot-instructions.md`, `compound-gpid.md`, and `compound-gpid.context.md`. See [Troubleshooting](troubleshooting.md) for known issues. See [Review Verify](review-verify.md) for a deep-dive on `/cg-review mode:verify`.

---

## PowerShell Commands

| Command | Where to run | Purpose |
|---------|-------------|---------|
| `cg-link` | Project root | Create per-subdirectory junctions in `.github/` and generate `copilot-instructions.md` from template - enables all Copilot prompts in this project |
| `cg-unlink` | Project root | Remove CG-managed junctions (existing `.github/` content is preserved) |
| `cg-update` | Anywhere | Update to latest (or stay on pinned version). Accepts optional version argument — see Version Management below. |
| `cg-update <version>` | Anywhere | Pin to a specific release tag, e.g. `cg-update v0.2.0` |
| `cg-update latest` | Anywhere | Unpin and return to tracking main |
| `cg-update --list` | Anywhere | Browse available GitHub Releases |

---

## Version Management

Compound GPID supports pinning to specific [GitHub Releases](https://github.com/GPID-WB/compound-gpid/releases) so you can choose between stability and bleeding-edge.

| Command | Effect | Persists? |
|---------|--------|-----------|
| `cg-update` | Use current preference (default: latest) | — |
| `cg-update v0.2.0` | Pin to release `v0.2.0` | Yes — writes to `.cg-version` |
| `cg-update latest` | Unpin and track `main` | Yes — writes to `.cg-version` |
| `cg-update --list` | Browse available releases | No |

**How it works:** the version preference is stored per-machine in `.cg-version` inside your global install directory. This file is gitignored. Pinned users see a yellow hint when a newer release is available at the end of every `cg-update` run.

> **Full details**: see the [Version Management](versioning.md) page.

---

## Copilot Chat Prompts

| Prompt | Model | Purpose |
|--------|-------|---------|
| `/cg-setup` | Claude Haiku 4.5 | Configure project or load context for returning projects |
| `/cg-strategy` | Claude Opus 4.6 | Full project visioning and direction-setting. Structures ideas into milestones, or rethinks the roadmap mid-project. Dispatches `@cg-roadmap` for all writes. **Requires `compound-gpid.md`** — run `/cg-setup` first. |
| `/cg-ideate` | Claude Opus 4.6 | Generate, critique, and filter improvement ideas for the project. Use when you don't have a specific task in mind. |
| `/cg-brainstorm` | Claude Opus 4.6 | Clarify fuzzy requirements through guided questions. Automatically checks `.cg-docs/brainstorms/` for prior work on the same topic before starting fresh. Classifies task as software or non-software (Thinking Partner mode). Assesses scope (Lightweight / Standard / Deep) and adapts question depth accordingly. |
| `/cg-plan` | Claude Opus 4.6 | Research + structured implementation plan. Automatically checks `.cg-docs/plans/` for prior work before starting fresh. Assesses implementation scope (Lightweight / Standard / Deep) and adapts plan detail. Includes confidence check before finalizing. |
| `/cg-plan-review` | Claude Opus 4.6 | Review an implementation plan for risks, over-engineering, missing edge cases, and flawed assumptions. Can review existing plans standalone or be run right after `/cg-plan`. Dispatches `@cg-plan-critic`. |
| `/cg-work` | Claude Sonnet 4.6 | Step-by-step implementation from plan. For Lightweight tasks with no plan, generates a short inline plan first. Builds a test index before implementing, runs mechanical self-review (Step 3.2) after all steps complete, and auto-marks roadmap features as `active`. If all features in a milestone are marked done, marks the milestone complete via `@cg-roadmap` (Step 3.8) and notifies the user to run `/cg-strategy` to review direction. |
| `/cg-fixbug` | Claude Sonnet 4.6 | Structured bug-fix: intake → reproduce (hard stop) → diagnose → fix (hard stop) → document. Checks prior bug solutions at intake. |
| `/cg-review [light\|standard\|thorough] [mode:autofix\|mode:verify]` | Mixed | Multi-agent code review with P0/P1/P2/P3 findings. Depth overrides config; content-based auto-escalation applies automatically (pipeline files, statistical functions, secrets, large diffs). `mode:autofix` applies safe mechanical fixes automatically. `mode:verify` switches to verification mode — re-runs a `light` review with suppression of expected fix-consequence P2/P3 findings; P0/P1 and new cross-file breakage are always reported. Arguments can be combined: `/cg-review light mode:autofix`. Note: `mode:autofix` and `mode:verify` are mutually exclusive — if both are passed, `mode:verify` wins. When `mode:verify` is active, any depth argument is ignored — verify always runs at `light`. |
| `/cg-fix-triage [IDs\|PRIORITY\|--migrate]` | Claude Sonnet 4.6 | Apply review findings by ID or priority level. If the report has more than 15 open findings and no arguments are given, warns before proceeding and recommends priority batches (`P0 P1`, `P2`, `P3`); respond `batch` to get the commands and stop, or `yes` to proceed. Use `--migrate` to backfill per-finding status tracking on legacy review files (pre-v0.4.3). |
| `/cg-fix-problems` | Claude Sonnet 4.6 | Interactive VS Code diagnostics fixer. Scans all workspace files for errors, warnings, and info diagnostics, lets you select scope and severity, then dispatches `@cg-fix-problems` to apply fixes. Auto mode is dispatched silently by `/cg-work` when `get_errors` returns errors in files touched by the current implementation step (errors only, 2-round budget). |
| `/cg-compound` | Claude Sonnet 4.6 | Capture solutions as reusable knowledge in `.cg-docs/solutions/`. Cross-references related existing solutions. |
| `/cg-compound-refresh` | Claude Sonnet 4.6 | Audit `.cg-docs/solutions/` for staleness, drift, and consolidation opportunities. Archives instead of deleting. |
| `/cg-resume` | Claude Haiku 4.5 | Load context, check schema version, scan pending work (active plans, open review findings, in-progress git changes), and resume interrupted sessions. Shows roadmap milestone progress. |
| `/cg-diagnose` | Claude Sonnet 4.6 | Post-crash forensics. Inspects VS Code logs (`main.log`, `renderer.log`, `exthost.log`), classifies the crash category (Pester / listener leak / rapid edits / extension host / unknown), checks for uncommitted work, and recommends recovery steps. Hands off to `/cg-resume`. |

> **Model selection**: See [Model Guide](model-guide.md) for tier assignments, decision criteria, and override guidance for all 31 prompt and agent files.

> **Project Charter**: All `/cg-*` prompts automatically read `compound-gpid.md` at session start (if it exists). If missing, prompts remind you to run `/cg-setup` to optionally create one. Prompts work without a charter — the reminder is advisory.

> **Prior-work awareness**: `/cg-brainstorm` checks `.cg-docs/brainstorms/` and `/cg-plan` checks `.cg-docs/plans/` for related prior work before starting. If a match is found, you can continue from it, follow up, or start fresh.

> **Scope assessment**: `/cg-brainstorm`, `/cg-plan`, and `/cg-work` all classify the task scope (Lightweight / Standard / Deep) and adapt their behavior accordingly. `/cg-work` declines to generate inline plans for Standard/Deep tasks — use `/cg-plan` first.

### Plugin Development (developer-only)

> **Consumer project users**: The prompts below are for compound-gpid maintenance
> only. `/cg-review-repos` appears in your autocomplete because it is distributed
> via junctions, but it **will not run** outside the compound-gpid repo — Step 0
> stops it immediately. Do not use these prompts in consumer projects.

| Prompt | Model | Purpose | Distribution |
|--------|-------|---------|-------------|
| `/cg-release` | Claude Sonnet 4.6 | Create a GitHub Release for compound-gpid. Detects next semver tag, drafts release notes from `.cg-docs/`, checks `SCHEMA_VERSION`, and publishes to GitHub Releases. | **Not distributed** — lives at the `compound-gpid` repo root only. |
| `/cg-review-repos [--full]` | Claude Opus 4.6 | Review external repos for features to integrate into compound-gpid. Default (delta) mode reviews only releases newer than the last review. `--full` performs a deep initial assessment of all repos — required before delta mode can be used. Updates `.cg-docs/competitive-reviews/repos.json` after each run. | **Distributed** via junctions to consumer projects, but Step 0 stops execution immediately if not run inside compound-gpid. |

### Competitive Review System

`/cg-review-repos` uses a registry file (`.cg-docs/competitive-reviews/repos.json`) to
track which repos are monitored and when each was last reviewed. The registry stores the
last-reviewed release tag per repo so delta reviews only scan new releases.

**Adding a new repo**: Edit `repos.json` and add an entry with the following fields:
- `id` — unique identifier, alphanumeric + hyphens only
- `url` — repo URL (must begin with `https://github.com/`)
- `releasesUrl` — releases page URL (must begin with `https://github.com/` and end with `/releases`)
- `shortName` — unique display label, 1–10 alphanumeric characters only (no hyphens, spaces, or special characters)
- `lastReviewedRelease` — set to `null` for new entries
- `lastReviewDate` — set to `null` for new entries

The registry root must also include `"schemaVersion": "compound-gpid-competitive-reviews-v1"`.

> **Schema version sync**: The `schemaVersion` value in `repos.json` and the expected
> value hardcoded in Step 1 of `cg-review-repos.prompt.md` must always match. When
> bumping the schema version, update both files together.

Also add a column to the concept mapping table in Step 1.5 of
`.github/prompts/cg-review-repos.prompt.md` for the new repo's terminology.

Then run `/cg-review-repos --full` to establish a baseline.

**Review cadence**: Run `/cg-review-repos` (delta mode) every 1–2 weeks to check for new
releases. Run `--full` only when adding a new repo or doing a periodic deep audit.

**Outputs**: Per-repo full-review files (`.cg-docs/competitive-reviews/YYYY-MM-DD-<id>-full-review.md`)
and delta reports (`.cg-docs/competitive-reviews/YYYY-MM-DD-delta-review.md`).
After a `--full` run, `lastFullReview` at the root of `repos.json` is set to today's date
(YYYY-MM-DD), recording the last complete audit across all repos. On partial failure,
`lastFullReview` is set to `null` and a `lastFullReviewNote` field records which repos failed.
`lastFullReviewNote` is removed on the next successful full run.
Per-repo `lastReviewDate` fields are the durable record of individual repo review history.
`lastFullReview` reflects only the most recent successful full-suite run.

> **Distribution note**: `/cg-review-repos` is distributed to consumer projects via
> junctions (it lives in `.github/prompts/` along with all other prompts). It will appear
> in the Copilot Chat autocomplete for any project using compound-gpid. The Step 0
> guardrail stops execution cleanly with an explanatory message if the prompt is invoked
> outside the compound-gpid repo — no action is taken in consumer projects.

---

## Review Agents

| Agent | Focus | Model |
|-------|-------|-------|
| `cg-code-quality` | Style, linting, DRY, naming | Haiku 4.5 |
| `cg-testing` | Coverage, edge cases, test quality | Haiku 4.5 |
| `cg-documentation` | roxygen2/docstrings/do-file headers, README, comments | Haiku 4.5 |
| `cg-version-control` | Commit hygiene, branching, secrets | Haiku 4.5 |
| `cg-reproducibility` | Lockfiles, relative paths, seeds, repkit | Haiku 4.5 |
| `cg-performance` | Vectorization, memory, algorithm complexity | Sonnet 4.6 |
| `cg-architecture` | Project structure, modularity, dependencies | Sonnet 4.6 |
| `cg-data-quality` | Input validation, types, missing values | Sonnet 4.6 |
| `cg-learnings-researcher` | Cross-reference past solutions (thorough only) | Haiku 4.5 |
| `cg-adversarial` | Adversarial testing: edge cases, data corruption, security (thorough only) | Sonnet 4.6 |

> All review agents are dispatched exclusively by `/cg-review`. They are NOT user-invokable and do not appear in the Copilot Chat agent dropdown.

> ℹ️ For model assignment rationale, tier criteria, and override guidance, see [Model Guide](model-guide.md).

### Auto-Escalation Rules

In addition to the configured depth tier, `/cg-review` automatically applies these content-based overrides:

| Trigger | Override |
|---------|----------|
| Changed files include `**/pipeline*.{R,py}`, `**/extract*.{R,py}`, `**/load*.{R,py}`, or any file in a `**/scripts/**` directory | Always adds `@cg-data-quality` (even in `light`) |
| Changed files touch authentication, secrets, or credentials | Always adds `@cg-version-control` |
| Changed files call statistical functions (`fmean`, `fsum`, `fgini`, `svymean`, `reghdfe`, `lm`, etc.) or generate summary tables | Always adds `@cg-data-quality` + `@cg-reproducibility` |
| ≥ 50 non-test lines changed | Escalates `light` → `standard` |
| ≥ 200 non-test lines changed | Suggests `thorough` to user (does not auto-apply) |

When any override fires, the prompt tells you: `"Auto-escalation applied: [reason]. Running [agents] in addition to the base depth."`

### Per-Finding Status Tracking

Review reports saved to `.cg-docs/reviews/` include YAML frontmatter that tracks each finding's status:

```yaml
---
plan: .cg-docs/plans/2026-04-01-my-feature.md
findings:
  P0.1: open
  P1.1: fixed
  P2.1: skipped
---
```

| Status | Meaning |
|--------|---------|
| `open` | Not yet addressed — will appear in the next `/cg-fix-triage` run |
| `fixed` | Applied by `/cg-fix-triage`; excluded from future sessions |
| `skipped` | Deliberately deferred; `/cg-resume` still counts them as pending |

> **Legacy review files** (from before v0.4.3) do not have the `findings:` key. Run `/cg-fix-triage --migrate` once to backfill status tracking on all legacy files.

Used by `/cg-review`, `/cg-fix-triage`, and all review agents. Each finding gets a compound ID (e.g., `P0.1`, `P1.2`) for selective fixing.

| Level | Label | Meaning | Action |
|-------|-------|---------|--------|
| **P0** | BLOCKING | Exploitable security vulnerability, PII/credential exposure, silent data corruption, incorrect statistical results | Immediate remediation required — must fix before anything else |
| **P1** | CRITICAL | Bugs causing incorrect behavior, missing critical validation, error handling gaps | Must fix before merge |
| **P2** | IMPORTANT | Performance problems, missing tests, poor documentation | Should fix |
| **P3** | MINOR | Style improvements, minor refactors, suggestions | Nice to have |

> Use `/cg-fix-triage P0` to fix all blocking findings, `/cg-fix-triage P0 P1` to fix blocking and critical, or `/cg-fix-triage P1.2 P2.3` to fix specific IDs.

---

## Plan Review Agent

| Agent | Focus | Model | User-invocable |
|-------|-------|-------|----------------|
| `@cg-plan-critic` | Plan review: assumptions, over-engineering, missing edge cases, scope creep, dependency accuracy | Sonnet 4.6 | No |

> `@cg-plan-critic` is dispatched exclusively by `/cg-plan-review`. It is **not user-invokable** directly. It reads the plan and actual codebase to verify assumptions, checking for over-engineering, missing edge cases, scope creep, and flawed dependencies.

---

## Roadmap Agent

| Agent | Focus | Model | User-invokable |
|-------|-------|-------|----------------|
| `@cg-roadmap` | Manages `roadmap.json`: add/remove milestones and features, link plans, update statuses | Haiku 4.5 | **Yes** |

> `@cg-roadmap` is the **only** agent users interact with directly. Invoke it in Copilot Chat to manage your project roadmap. Other prompts (`/cg-plan`, `/cg-work`, `/cg-brainstorm`) dispatch it automatically for roadmap updates (when `roadmap.json` exists).

### `roadmap.json` Schema

| Field | Type | Values |
|-------|------|--------|
| `milestones[].status` | derived | `planned`, `in-progress`, `done` |
| `features[].status` | set | `idea`, `planned`, `active`, `done` |

Milestone status is computed by `@cg-roadmap` from feature statuses (never set directly by users). Feature `active` maps to milestone `in-progress`. After all features in a milestone are marked `done`, `/cg-work` dispatches `@cg-roadmap` to mark the milestone as `done` (see Step 3.8). IDs are kebab-case and immutable after creation. `features[].plan` is a nullable path to a `.cg-docs/plans/` file.

---

## Skills

| Skill | Contents |
|-------|---------|
| `cg-skill-setup` | Project configuration wizard |
| `cg-skill-r-collapse` | **collapse statistical computing**: `fmean`/`fsum`/`fmedian`/`fnth` and all Fast Statistical Functions, GRP objects, TRA transformation types, `fwithin`/`fbetween`/`fscale`, `flag`/`fdiff`/`fgrowth`, `collap()`, `fsummarise`/`fmutate`. Dialect-neutral: works on data.table, tibble, and data.frame. |
| `cg-skill-r-datatable` | **data.table manipulation**: `DT[i,j,by]` syntax, `:=` in-place mutation, `fread`/`fwrite`, joins, `melt`/`dcast` reshaping, `.SD`/`.SDcols`, `fifelse`/`fcase`/`fcoalesce`, keys and indices. |
| `cg-skill-r-tidyverse` | **tidyverse patterns**: dplyr 1.2+ (`.by`, `join_by`, `across`/`pick`/`reframe`), native pipe `\|>`, `pivot_longer`/`pivot_wider`, `readr` I/O, `stringr`, `purrr`. Load for `r-syntax: "tidyverse"` projects. |
| `cg-skill-r-visualization` | **ggplot2 + wbplot**: World Bank visualization conventions, `theme_wb()`, `WBCOLORS`, `scale_color_wb_d()`, `scale_fill_wb_c()`, GPID chart types. |
| `cg-skill-r-analytical` | **Analytical domain patterns**: `haven` (Stata migration), `fixest` (econometrics), `modelsummary` (tables), welfare/poverty measurement, FGT indices, survey analysis. Syntax-neutral — works with any dialect. |
| `cg-skill-r-technical` | **Infrastructure & packages**: roxygen2, package dev, `plumber` APIs, `shiny`, `targets` pipelines, `httr2` clients, `renv`/`pak`. Syntax-neutral. |
| `cg-skill-r-shared` | Base R style rules universal to all dialects: `<-` assignment, `snake_case`, `TRUE`/`FALSE`, `rlang`/`cli` error handling. |
| `cg-skill-r-testing` | testthat 3+ patterns: `test_that()`, `describe()`/`it()`, fixtures, mocking (`local_mocked_bindings()`), snapshots, BDD-style testing. Dialect-aware: data.table examples for collapse/data.table projects, tibble examples for tidyverse projects. |
| `cg-skill-python-best-practices` | polars, numpy, pytest, type hints, `uv`/`poetry` |
| `cg-skill-stata-best-practices` | Comprehensive Stata reference: universal coding principles (compound quotes, macro expansion traps, stored results, `subpop()` vs `if`, clustering), data management, econometrics, causal inference, graphics, Mata, reproducibility (`repkit`: `repado`, `reproot`, `reprun`, `repscan`, `lint`), and 21 community packages (`reghdfe`, `estout`, `did`, `rdrobust`, etc.). ALWAYS load when writing or reviewing `.do` or `.ado` files. |
| `cg-skill-git-workflow` | Branching, commits, PR templates, `.gitignore` |
| `cg-skill-brainstorming` | Requirement elicitation and decision capture |
| `cg-skill-compound-docs` | Knowledge capture and categorization system |
| `cg-skill-fix-triage-migrate` | Migration mode for `/cg-fix-triage --migrate`: backfills `findings:` tracking frontmatter on legacy review files. Does NOT apply fixes. |

---

## Configuration

Run `/cg-setup` in Copilot Chat after running `cg-link`. The prompt asks:
- **Language**: R, Python, Stata, or any combination
- **R syntax dialect** (if R is selected): `data.table-collapse` (default) or `tidyverse`
- **Project type**: Package, analysis, dashboard, API, tool
- **Review depth**: Light, standard, or thorough
- **Project charter** (optional): project name, objective, deliverables, constraints

This creates `compound-gpid.local.md` (gitignored, user-specific config), optionally
`compound-gpid.md` (committed, shared project charter), and optionally `compound-gpid.context.md`
(committed, growing project knowledge base) in your project root, and scaffolds the `.cg-docs/` directory.

### Configuration Fields

All fields are stored as YAML frontmatter in `compound-gpid.local.md`:

| Field | Values | Description |
|-------|--------|-------------|
| `language` | `"r"`, `"python"`, `"stata"`, `"both"`, or combination | Language(s) used in the project |
| `r-syntax` | `"data.table-collapse"` (default), `"tidyverse"` | R dialect for skill routing. Determines which R syntax skills are loaded for `.R` files. Use `"tidyverse"` for projects with external coauthors who only know dplyr. |
| `project-type` | `"package"`, `"analysis"`, `"dashboard"`, `"api"`, `"tool"` | Project type |
| `review-depth` | `"light"`, `"standard"`, `"thorough"` | Depth of `/cg-review` (see Review Depth Tiers in `copilot-instructions.md`) |
| `cg-schema-version` | date string | Auto-managed by `cg-update`. Do not edit manually. |

### `compound-gpid.context.md`

A committed, growing knowledge base for project-specific context. Created by `/cg-setup`. Extended by `/cg-compound` after each significant task. Read by all prompts in Step 0.

Typical contents: data source locations and caveats, domain vocabulary, workspace folder descriptions, variable-level notes, recurring gotchas. Unlike the charter (`compound-gpid.md`), `context.md` has no fixed structure — organise it by topic.

---

## Directory Structure

After linking and configuring, your project will contain:

```
your-project/
├── .github/
│   ├── prompts/              → junction to C:\WBG\.compound-gpid\.github\prompts\
│   ├── skills/               → junction to C:\WBG\.compound-gpid\.github\skills\
│   ├── agents/               → junction to C:\WBG\.compound-gpid\.github\agents\
│   ├── instructions/         → junction to C:\WBG\.compound-gpid\.github\instructions\
│   ├── copilot-instructions.md  # generated from template (managed marker); regenerated by cg-link/cg-update
│   └── workflows/            # your own GitHub Actions (untouched by cg-link)
├── compound-gpid.md          # Project charter (4 sections: Objective, Key Deliverables, Constraints, Current Focus). YAML: project-name, team, created, last-reviewed. Committed -- shared.
├── compound-gpid.context.md  # Growing project knowledge base (data sources, domain vocab, workspace notes). Committed -- institutional memory.
├── compound-gpid.local.md    # Your user config (gitignored)
├── roadmap.json              # Milestone & feature tracker (committed)
└── .cg-docs/                 # Compound GPID knowledge base (committed -- institutional memory)
    ├── archive/              # Archived charter sections removed by the user (not loaded at session start)
    ├── brainstorms/          # /cg-brainstorm outputs
    ├── competitive-reviews/  # /cg-review-repos registry (repos.json) and assessment outputs
    ├── plans/                # /cg-plan outputs
    ├── reviews/              # /cg-review outputs (review reports for /cg-fix-triage)
    ├── strategy/             # /cg-strategy session records
    └── solutions/            # /cg-compound outputs
        ├── build-errors/
        ├── bugs/
        ├── performance-issues/
        ├── testing-patterns/
        ├── data-quality/
        ├── environment-issues/
        └── git-workflows/
```

---

**Archive file format** (`.cg-docs/archive/charter-history.md`): Content removed from
the charter is appended with a date heading and source section label:

````markdown
## Archived YYYY-MM-DD
**Removed from**: <section name>
<removed content>
````

> **Something not working?** See [Troubleshooting](troubleshooting.md).

---

## `.cg-docs/` Document Frontmatter Schema

Each document type in `.cg-docs/` uses a defined set of `status` enum values. These are enforced
by convention now and will be validated automatically in a future `evals` milestone.

| Document type | Path | Valid `status` values |
|---------------|------|-----------------------|
| Brainstorm | `.cg-docs/brainstorms/` | `open`, `decided`, `abandoned` |
| Plan | `.cg-docs/plans/` | `draft`, `active`, `completed`, `abandoned` |
| Solution | `.cg-docs/solutions/` | `draft`, `applied` |
| Review | `.cg-docs/reviews/` | Per-finding status in `findings:` frontmatter key: `open`, `fixed`, `skipped` |
| Verify Review | `.cg-docs/reviews/` (filename: `<stem>-verify-review.md`) | Same `findings:` map as Review, plus `parent-review: <path>` (prior review file) and `type: verification` |

