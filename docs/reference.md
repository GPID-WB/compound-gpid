# Reference

Quick reference for all Compound GPID commands, agents, skills, configuration, and file structure.

> See [Workflow](workflow.md) for a full explanation of each prompt step. See [Installation](installation.md) for setup instructions. See [Context Files](context-files.md) for a detailed guide to `copilot-instructions.md`, `compound-gpid.md`, `compound-gpid.context.md`, and the Codex / Claude Code `AGENTS.md` adapter. See [Troubleshooting](troubleshooting.md) for known issues.

---

## Shell Commands

> Available from PowerShell on Windows and from bash/zsh on macOS.

<!-- cg:auto:shell-commands -->
| Command | Where to run | Purpose |
|---------|-------------|---------|
| `cg-link` | Project root | Create per-subdirectory junctions in `.github/` and generate `copilot-instructions.md` from template - enables all Copilot prompts in this project |
| `cg-unlink` | Project root | Remove CG-managed junctions (existing `.github/` content is preserved) |
| `cg-update` | Anywhere | Update to latest (or stay on pinned version). Accepts optional version argument — see Version Management below. |
| `cg-update <version>` | Anywhere | Pin to a specific release tag, e.g. `cg-update v0.2.0` |
| `cg-update latest` | Anywhere | Unpin and return to tracking main |
| `cg-update --list` | Anywhere | Browse available GitHub Releases |
| `cg-update --fix` | Anywhere | Repair a broken installation — cleans untracked files, discards local changes, and pulls latest |
| `cg-brain-init` | Project root | Initialize or configure Team Brain integration for the current project |
| `cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations` | Project root | Generate legacy `.cg-docs/cost/` reports, additive `.cg-docs/token/` workflow baseline artifacts, and compact token-efficiency advice |
| `cg-test-summary --root . --format json` | Project root | Summarize existing `tests/last-run.json` without running tests; stores the redacted source artifact under `.cg-docs/token/outputs/` |
| `cg-diff-summary --root . --format md` | Project root | Summarize changed files, hunks, risk tags, and store the full redacted `git diff` under `.cg-docs/token/outputs/` |
| `cg-log-summary --root . --format json` | Project root | Summarize branch-local first-parent commits and notable files |
| `cg-tree-summary --root . --max-entries 120 --format md` | Project root | Summarize a bounded repository tree while excluding generated outputs and common dependency/cache folders |
| `cg-problems-summary --root . --input problems.json --format json` | Project root | Summarize optional diagnostics JSON/text; reports unavailable when no diagnostics file is provided |
<!-- cg:auto:end -->

---

## Version Management

Compound GPID supports pinning to specific [GitHub Releases](https://github.com/GPID-WB/compound-gpid/releases) so you can choose between stability and bleeding-edge.

| Command | Effect | Persists? |
|---------|--------|-----------|
| `cg-update` | Use current preference (default: latest) | — |
| `cg-update v0.2.0` | Pin to release `v0.2.0` | Yes — writes to `.cg-version` |
| `cg-update latest` | Unpin and track `main` | Yes — writes to `.cg-version` |
| `cg-update --list` | Browse available releases | No |
| `cg-update --fix` | Repair broken installation (clean + pull) | No |

**How it works:** the version preference is stored per-machine in `.cg-version` inside your global install directory. This file is gitignored. Pinned users see a yellow hint when a newer release is available at the end of every `cg-update` run.

> **Full details**: see the [Version Management](versioning.md) page.

---

## Copilot Chat Prompts

<!-- cg:auto:commands -->
| Prompt | Model | Purpose |
|--------|-------|---------|
| `/cg-setup` | Claude Haiku 4.5 | Configure project or load context for returning projects |
| `/cg-strategy` | Copilot model picker | Full project visioning and direction-setting. Structures ideas into milestones, or rethinks the roadmap mid-project. Dispatches `@cg-roadmap` for all writes. When GitHub Issues are enabled, recommends `/cg-issues backfill` for newly added or changed unlinked work items; it never creates issues automatically. **Requires `compound-gpid.md`** — run `/cg-setup` first. |
| `/cg-ideate` | Copilot model picker | Generate, critique, and filter improvement ideas for the project. Use when you don't have a specific task in mind. |
| `/cg-brainstorm [--no-branch]` | Copilot model picker | Clarify fuzzy requirements through guided questions. **Auto-branch at Step 1.7** — on the default branch, automatically creates and switches to a feature branch before any clarifying questions (no prompt). On a feature branch, prompts stay or new. If the workspace is not a git repo, offers `git init` first. Use `--no-branch` to skip branching entirely. Automatically checks `.cg-docs/brainstorms/` for prior work on the same topic before starting fresh. Classifies task as software or non-software (Thinking Partner mode). Assesses scope (Lightweight / Standard / Deep) and adapts question depth accordingly. After proposing approaches, runs an always-on devil's advocate challenge covering problem validity, simplicity, effort-value, and charter alignment before the decision is finalized. |
| `/cg-plan [--no-phases] [deviate:<policy>]` | Copilot model picker | Research + structured implementation plan. **Branch offer at Step 0.7** — before gathering context, offers to create a git branch derived from your request. Automatically checks `.cg-docs/plans/` for prior work before starting fresh. Assesses implementation scope (Lightweight / Standard / Deep) and adapts plan detail. **Phases by default** — all plans are automatically organized into numbered phases unless `--no-phases` is passed or the plan has ≤ 2 steps. **Completion contract** — every saved plan includes a `## Completion Contract` section (Outcome, Verification Surface, Constraints, Boundaries, Iteration Policy, Blocked-Stop Conditions). The contract is previewed for user approval before the plan is saved. Use `deviate:ask` (default), `deviate:auto` (autonomous), or `deviate:strict` to set the deviation policy stored in plan frontmatter as `deviation-policy`. Includes confidence check before finalizing. |
| `/cg-plan-review` | Copilot model picker | Review an implementation plan for risks, over-engineering, missing edge cases, and flawed assumptions. Can review existing plans standalone or be run right after `/cg-plan`. Dispatches `@cg-plan-critic`. |
| `/cg-work [phaseX] [review:<mode>] [deviate:<policy>]` | GPT-5.3-Codex | Step-by-step implementation from plan, guided by the plan's completion contract. Accepts an optional `phaseX` argument (e.g., `/cg-work phase2`) to execute a specific phase of a phased plan; without an argument, executes all remaining phases sequentially. **Goal-driven execution** — reads the plan's `## Completion Contract` as execution authority; completion is only recorded when required evidence passes or an explicit accepted exception is logged in the execution report (`.cg-docs/work-reports/`). **Deviation policy** — uses the plan's `deviation-policy` frontmatter value by default; override at runtime with `deviate:ask`, `deviate:auto`/`deviate:autonomous` (both stored as `autonomous`), or `deviate:strict`. Deviation decisions and accepted exceptions are recorded in the execution report. Legacy plans without a contract are halted with an offer to generate a minimal compatibility contract. Review handoff is mode-aware: default/`review:manual` recommends a routed `/cg-review` command without dispatching review agents, `review:auto` dispatches route-appropriate agents using the shared review-routing contract, and `review:none` suppresses review handoff. `/cg-review` remains available but is no longer required as the default post-work step when evidence gates pass. Builds a test index before implementing, runs mechanical self-review (Step 3.2) after all steps complete, and auto-marks roadmap features as `active`. If all features in a milestone are marked done, marks the milestone complete via `@cg-roadmap` (Step 3.8). |
| `/cg-fixbug` | GPT-5.3-Codex | Structured bug-fix: intake → expected-behavior source (Step 1.5, MANDATORY) → reproduce with diagnostic fork (hard stop) → test-gap classification (Step 2.5) → diagnose → fix with red-green proof (hard stop) → document. Checks prior bug solutions at intake. |
| `/cg-review [light\|standard\|data-risk\|architecture\|full] [--report-only\|mode:autofix\|mode:verify]` | GPT-5.4 | Multi-agent code review with P0/P1/P2/P3 findings. Uses staged routing by default: small low-risk changes route to `light`, normal changes to `standard`, statistical/survey/poverty/welfare/joins/aggregation/reproducibility-sensitive changes to `data-risk`, architecture/performance-heavy changes to `architecture`, and security/release/high-risk or explicit requests to `full`. `thorough` remains accepted as a backward-compatible alias for `full`. **Autofix is the default** — safe mechanical fixes (`[safe_auto]`) are applied automatically; statistical functions, welfare/income variables, and weight parameters are never auto-fixed (escalated to `[manual]`). Use `--report-only` to disable autofix and present findings one-at-a-time for Fix/Skip/Discuss. `mode:autofix` is now a no-op (accepted for backward compatibility). `mode:verify` switches to verification mode — re-runs a `light` review with suppression of expected fix-consequence P2/P3 findings; P0/P1 and new cross-file breakage are always reported. Note: `--report-only` and `mode:verify` are mutually exclusive — if both are passed, `mode:verify` wins. |
| `/cg-fix-triage [IDs\|PRIORITY\|--migrate]` | GPT-5.3-Codex | Apply review findings by ID or priority level. If the report has more than 15 open findings and no arguments are given, warns before proceeding and recommends priority batches (`P0 P1`, `P2`, `P3`); respond `batch` to get the commands and stop, or `yes` to proceed. Use `--migrate` to backfill per-finding status tracking on legacy review files (pre-v0.4.3). |
| `/cg-fix-problems` | GPT-5.3-Codex | Interactive VS Code diagnostics fixer. Scans all workspace files for errors, warnings, and info diagnostics, lets you select scope and severity, then dispatches `@cg-fix-problems` to apply fixes. Auto mode is dispatched silently by `/cg-work` when `get_errors` returns errors in files touched by the current implementation step (errors only, 2-round budget). |
| `/cg-compound [--no-enrich] [--propose]` | GPT-5.4 | Capture solutions as reusable knowledge in `.cg-docs/solutions/`. Cross-references related existing solutions. **Auto-enriches by default** — automatically writes key findings to `compound-gpid.context.md` (no prompt) and updates the project wiki (folder configured via `## Wiki Configuration` in `compound-gpid.context.md`) when the captured solution has user-facing implications. In Step 6, offers to suggest updates to `.github/instructions/` or `.github/skills/` files (the user applies them manually). Use `--no-enrich` to skip `compound-gpid.context.md` and wiki enrichment. Use `--propose` to review proposed wiki changes before they are applied. |
| `/cg-compound-refresh` | GPT-5.4 | Audit `.cg-docs/solutions/` for staleness, drift, and consolidation opportunities. Archives instead of deleting. |
| `/cg-brain-rebuild` | GPT-5.4 | Rebuild the project knowledge brain (`BRAIN.md` + `BRAIN-NN.md` partitions + `BRAIN-log.md` + `brain-index.json`) by running `cg-index --brain`. Use directly after pulling `.cg-docs/` changes from collaborators, after manually editing solution files, after a `/cg-compound` run where brain rebuild was skipped, or when the brain is stale. Verifies success by exit code (primary), stdout stats line (secondary), and `BRAIN.md` existence (tertiary). |
| `/cg-wiki [init\|rebuild\|restructure\|convert\|status\|help] [--propose]` | GPT-5.4 | Manage the project wiki (`wiki/` by default). No args = status table. `init` bootstraps the wiki on an existing project (creates `_wiki.yml` and all wiki pages from a project-type template). `rebuild` regenerates all auto-managed pages from current codebase + charter. `rebuild <page-id>` targets a single page. `restructure` lets you add/remove/reorder pages interactively. `convert` generates GitHub Wiki–compatible layout (Home.md, _Sidebar.md). `--propose` shows diffs before writing. Wiki initialized at `/cg-setup` or `/cg-wiki init`; updated automatically by `/cg-compound`. |
| `/cg-token-audit` | Claude Haiku 4.5 | Advisory token/context usage analysis. Runs `cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations`, writes legacy `.cg-docs/cost/` reports plus additive `.cg-docs/token/` workflow baseline artifacts, then summarizes `.cg-docs/cost/token-advice.md`. Does not modify project configuration or source files. |
| `/cg-resume` | Claude Haiku 4.5 | Load context, check schema version, scan pending work (active plans, open review findings, in-progress git changes), and resume interrupted sessions. Shows roadmap milestone progress. Displays linked GitHub issue numbers (read-only) alongside active features when present, and may suggest `/cg-issues link` or `/cg-issues backfill` when relevant current work is unlinked. |
| `/cg-roadmap-view [--milestone\|--tasks\|--detail\|--status\|--wip\|--plan\|--help] [<name>]` | Claude Haiku 4.5 | Display the project roadmap in chat. Flags control the view: no flags = summary table; `--wip` = in-progress milestones; `--milestone <name>` = single milestone detail; `--tasks [<name>]` = feature lists; `--detail <name>` = single feature; `--detail <name> --plan` = feature plus linked plan summary; `--status idea\|planned\|active\|done` = features by status. Names are fuzzy-matched. |
| `/cg-diagnose` | GPT-5.3-Codex | Post-crash forensics. Inspects VS Code logs (`main.log`, `renderer.log`, `exthost.log`), classifies the crash category (Pester / listener leak / rapid edits / extension host / unknown), checks for uncommitted work, and recommends recovery steps. Hands off to `/cg-resume`. |
| `/cg-issues [status\|backfill\|link\|adopt\|setup]` | Claude Haiku 4.5 | Manage GitHub Issues linked to roadmap work items. `status` (default, read-only): display linked issues and unlinked features. `backfill`: create or link issues for unlinked features after explicit confirmation. `link`: attach an existing issue to a feature. `adopt`: import a GitHub issue as a new roadmap feature. `setup`: configure `githubIssues` in `roadmap.json`. Requires `gh` CLI and authentication. Degrades gracefully when `gh` is unavailable. Dispatches `@cg-roadmap` for all roadmap writes. |
| `/cg-commit-push-pr` | GPT-5.3-Codex | Stage changes into logical commits (grouped by file type: code, tests, docs, config, plans), generate conventional commit messages, push, and open a PR with a plan-driven description. Adds `Refs #` or `Closes #` to the PR body when features have linked GitHub issues (`Closes #` only with explicit user confirmation). Proposes commit splits interactively. Requires `gh` CLI for PR creation — degrades gracefully with install instructions if missing. |
| `/cg-verify-pr [--propose]` | GPT-5.3-Codex | Check CI status on the current branch's PR and auto-fix failures. Classifies failures (lint/type errors → `@cg-fix-problems`; test failures → `@cg-testing`; build errors → `@cg-code-quality`; platform-specific). One fix round per invocation; 2-round cap tracked via `fix(ci):` commit count. Re-invoke after CI re-runs to apply a second round. Use `--propose` for observe-only diagnosis (no commits or pushes). |

### `cg-index --brain` — Diagnostic Warnings

`cg-index --brain` writes scan-pass warnings to **stderr** during execution:

| Message | Meaning |
|---------|---------|
| `[cg-index] WARNING: Skipping <file>: …` | File could not be read (UnicodeDecodeError, OSError) — excluded from brain index. |
| `[cg-index] WARNING: Skipping <file>: no frontmatter found` | File lacks a `---` YAML block — excluded from index. |
| `[cg-index] WARNING: <file>: missing required field(s): …` | Frontmatter is missing `title` or `date` — included but may sort incorrectly. |
| `[cg-index] WARNING: Duplicate frontmatter key '<key>'` | Frontmatter has a repeated key — only the last value is used. |
| `[cg-index] WARNING: roadmap feature … has no 'id'; skipping` | Roadmap feature entry lacks an `id` field — not linked in the brain. |

To capture warnings: `cg-index --brain 2>brain-warnings.txt`.

### `cg-index query` — Budgeted Knowledge Brain Retrieval

Use `cg-index query` when a workflow needs prior project knowledge without
opening generated Brain partitions by hand:

```bash
cg-index query --intent plan --query "workflow token baseline" --budget 600 --format md
cg-index query --intent review --query "Pester safe runner" --changed-file tests/Run-Tests.ps1 --budget 600 --format json
```

The query mode returns a short answer, selected artifact paths, snippets,
selection/exclusion reasons, stale/conflict flags, confidence, and a heuristic
token estimate. It is local and deterministic; it does not use vector search,
external services, or optional retrieval backends. If query mode is unavailable
or insufficient, fall back to the `BRAIN.md` topic index and matched
`BRAIN-NN.md` sections.

### Command Output Summary Wrappers

Use the `cg-*-summary` wrappers when a workflow needs compact evidence from
noisy local command surfaces while retaining the full source output on disk:

```bash
cg-test-summary --root . --format json
cg-diff-summary --root . --format md
cg-log-summary --root . --format json
cg-tree-summary --root . --max-entries 80 --format md
cg-problems-summary --root . --input diagnostics.json --format json
```

The wrappers are local stdlib tooling. They do not call external services,
mutate GitHub, or replace required validation commands. `cg-test-summary`
only reads existing `tests/last-run.json`; it does not run Pester, pytest, R,
or Stata. Full raw/source outputs are redacted for common secret-looking
patterns and written under `.cg-docs/token/outputs/YYYYMMDD-HHMMSS-<kind>/`.
Keep that directory for short-lived validation evidence, not durable project
knowledge; record final decisions in plans, reviews, work reports, and
solutions instead. Treat any token-saving benefit as a hypothesis until
measured against the same workflow probe in this repository.

### `cg-token-audit` / `cg-audit-context` — Context and Model-Governance Audit

```
cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations
python scripts/cg_audit_context.py [--root PATH] [--output-dir PATH] [--format json|md|both] [--baseline context-audit.json] [--recommendations] [--token-output-dir PATH] [--no-token-artifacts]
```

Inventories context-contributing files, estimates token burden (chars/4 heuristic), counts prompt and agent references, inventories model declarations, enriches declarations from `.github/shared/model-catalog.json`, detects duplicate paragraph blocks, and benchmarks `/cg-brainstorm`, `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-fix-triage`, `/cg-compound`, `/cg-resume`, `/cg-diagnose`, `/cg-token-audit`, and Knowledge Brain/context lookup behavior. Runtime-only quantities such as command-output size and summary size are marked `not_observed` until explicit instrumentation exists. The audit writes legacy reports to `.cg-docs/cost/` (default `--output-dir`) and additive workflow baseline artifacts to `.cg-docs/token/` by default. Requires `scripts/brain/` from this repository. The installed `cg-token-audit` wrapper runs the same script from any linked project; pass `--root .` from the project root so the consumer project is audited.

Use `--baseline` with a previous `context-audit.json` to render before/after benchmark deltas. Use `--recommendations` to also write `.cg-docs/cost/token-advice.md`, a compact advisory report with fix/accept/docs-only warning classifications and token-efficiency recommendations. Use `--token-output-dir PATH` to move the workflow baseline artifacts, or `--no-token-artifacts` for a legacy-only run. The generated Markdown includes Benchmark Summary, Guardrails, Reviewed Warning Classifications, Token Efficiency Recommendations, Context Loading Risks, Review Dispatch Burden, Model Inventory, and a release-readiness checklist.

Workflow baseline artifacts:

| Artifact | Purpose |
|----------|---------|
| `.cg-docs/token/TOKEN-BUDGET.md` | Human-readable workflow baseline, observability boundaries, and the no-savings-claim policy |
| `.cg-docs/token/token-audit.json` | Canonical JSON baseline payload with workflow telemetry, benchmark, guardrails, and warning classifications |
| `.cg-docs/token/context-map.json` | Workflow-to-context map of deterministic file, skill, agent, tool, and context-loading signals |
| `.cg-docs/token/workflow-costs.csv` | Spreadsheet-friendly workflow rows for the nine tracked `/cg-*` workflows |
| `.cg-docs/token/large-context-warnings.md` | Large prompt/instruction/skill and repeated-context warnings without copying large bodies |

Model-governance guardrails report unknown or stale model names, missing catalog
assignments, invalid roles, OpenAI-first violations, Haiku/Sonnet role
violations, support gaps, and model-guide drift. Inherited model-picker prompts
are a deliberate exception: a missing `model:` frontmatter key matches
`Copilot model picker` in `docs/model-guide.md` only when the catalog role is
`inherited`.

Exit codes: `0` success, `1` fatal error, `2` missing or invalid project root.
<!-- cg:auto:end -->

For token-optimization release candidates, complete
`.cg-docs/cost/token-optimization-release-checklist.md` after generating the
audit. Keep non-blocking issues in
`.cg-docs/cost/token-optimization-follow-ups.md` so release blockers and future
cleanup stay separate.

> **Model selection**: See [Model Guide](model-guide.md) for model selection guidance and escalation criteria.

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
| `/cg-review-repos [--full]` | Copilot model picker | Review external repos for features to integrate into compound-gpid. Default (delta) mode reviews only releases newer than the last review. `--full` performs a deep initial assessment of all repos — required before delta mode can be used. Updates `.cg-docs/competitive-reviews/repos.json` after each run. | **Distributed** via junctions to consumer projects, but Step 0 stops execution immediately if not run inside compound-gpid. |

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
| `cg-code-quality` | Style, linting, DRY, naming | GPT-5.3-Codex |
| `cg-testing` | Coverage, edge cases, test quality | GPT-5.3-Codex |
| `cg-documentation` | roxygen2/docstrings/do-file headers, README, comments | Claude Haiku 4.5 |
| `cg-version-control` | Commit hygiene, branching, secrets | Claude Haiku 4.5 |
| `cg-reproducibility` | Lockfiles, relative paths, seeds, repkit | Claude Haiku 4.5 |
| `cg-performance` | Vectorization, memory, algorithm complexity | GPT-5.4 |
| `cg-architecture` | Project structure, modularity, dependencies | GPT-5.4 |
| `cg-data-quality` | Input validation, types, missing values | GPT-5.4 |
| `cg-learnings-researcher` | Cross-reference past solutions (`full` / `thorough` alias only) | Claude Haiku 4.5 |
| `cg-adversarial` | Adversarial testing: edge cases, data corruption, security (`full` / `thorough` alias only) | GPT-5.4 |

> Review agents are primarily dispatched by `/cg-review`. `/cg-verify-pr` also dispatches `@cg-testing` (test failure analysis) and `@cg-code-quality` (build error analysis) as part of CI triage. Agents are NOT user-invokable and do not appear in the Copilot Chat agent dropdown.

> ℹ️ For model selection guidance and escalation criteria, see [Model Guide](model-guide.md).

### Review Routing Rules

`/cg-review` uses staged routing from changed-file risk signals:

| Trigger | Resolved mode |
|---------|----------|
| Small docs/prompt wording/metadata-only or low-risk test changes | `light` |
| Ordinary implementation, prompt, or test changes without high-risk signals | `standard` |
| Pipeline/extract/load scripts, statistical functions (`fmean`, `fsum`, `fgini`, `svymean`, `reghdfe`, `lm`, etc.), summary tables, survey/poverty/welfare/weights/joins/aggregation, or reproducibility-sensitive changes | `data-risk` |
| Architecture, dependencies, module boundaries, performance, memory, API contracts, or large refactors | `architecture` |
| Authentication, secrets, credentials, release automation, publishing, install/update paths, linking/unlinking paths, schema changes, or destructive filesystem behavior | `full` |
| ≥ 50 non-test lines changed with otherwise low risk | raises `light` → `standard` |
| ≥ 200 non-test lines changed without higher-risk trigger | recommends `full` to user (does not auto-apply unless explicitly requested) |

When any route fires, the prompt tells you the reason, resolved mode, and
mandatory emphasis. Explicit review modes win when present: `/cg-review light`
resolves to `light`, and `/cg-review full` resolves to `full`. Auto
risk-class routing applies only when no explicit mode is requested. Agents
should still mention high-risk signals in their review focus. `thorough`
remains a backward-compatible alias for `full`.

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
| `@cg-plan-critic` | Plan review: assumptions, over-engineering, missing edge cases, scope creep, dependency accuracy, and phase structure (logical ordering, independent testability, completion criteria, cross-phase handoffs) | Sonnet 4.6 | No |

> `@cg-plan-critic` is dispatched exclusively by `/cg-plan-review`. It is **not user-invokable** directly. It reads the plan and actual codebase to verify assumptions, checking for over-engineering, missing edge cases, scope creep, flawed dependencies, and (for phased plans) phase structure quality.

---

## Project Scanner Agent

| Agent | Focus | Model | User-invocable |
|-------|-------|-------|----------------|
| `@cg-project-scanner` | Scans project file structure to detect languages, frameworks, project type, and charter-relevant content. Returns structured analysis for `/cg-setup` and other prompts | Claude Haiku 4.5 | No |

> `@cg-project-scanner` is dispatched by `/cg-setup` (Phase 2) and other prompts that need project analysis. It is **not user-invokable** directly. It reads the project file tree, matches signals against the `cg-skill-project-scanner` catalog, extracts charter-draft content from README and DESCRIPTION, and returns a structured markdown report with language detection, project type, and per-question setup recommendations.

---

## Release Scanner Agent

| Agent | Focus | Model | User-invocable |
|-------|-------|-------|----------------|
| `@cg-release-scanner` | Classifies commits by conventional commit prefix, scans `.cg-docs/` entries within the scan window, and returns a structured categorized report for `/cg-release` | Claude Haiku 4.5 | No |

> `@cg-release-scanner` is dispatched exclusively by `/cg-release`. It is **not user-invokable** directly. It receives the pre-collected git commit log and window parameters from the orchestrating prompt, classifies commits (feat/fix/docs/breaking), matches `.cg-docs/` plan and solution entries by keyword, and returns a structured markdown report with Semver Impact recommendation and SCHEMA_VERSION signals.

---

## Roadmap Agent

| Agent | Focus | Model | User-invocable |
|-------|-------|-------|----------------|
| `@cg-roadmap` | Manages `roadmap.json`: add/remove milestones and features, link plans, update statuses | Haiku 4.5 | **Yes** |

> `@cg-roadmap` is the **only** agent users interact with directly (via `@cg-roadmap` in Copilot Chat) to manage your project roadmap. Prompts like `/cg-issues`, `/cg-plan`, and `/cg-work` dispatch it automatically for roadmap updates when `roadmap.json` exists.

### `roadmap.json` Schema

| Field | Type | Values |
|-------|------|--------|
| `milestones[].objective` | required string | One sentence describing why the milestone exists. `@cg-roadmap` validates this field is present before every write. |
| `milestones[].status` | derived | `planned`, `in-progress`, `done` |
| `features[].status` | set | `idea`, `planned`, `active`, `done` |
| `githubIssues` | object | Optional top-level GitHub Issues config block (see below) |
| `features[].github` | object | Optional per-feature GitHub issue linkage (see below) |

Milestone status is computed by `@cg-roadmap` from feature statuses (never set directly by users). Feature `active` maps to milestone `in-progress`. After all features in a milestone are marked `done`, `/cg-work` dispatches `@cg-roadmap` to mark the milestone as `done` (see Step 3.8). IDs are kebab-case and immutable after creation. `features[].plan` is a nullable path to a `.cg-docs/plans/` file.

#### `githubIssues` block (optional)

Stored as a top-level key in `roadmap.json`. All sub-fields are optional.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable GitHub Issues integration for this project |
| `repo` | string | — | `owner/repo` identifying the GitHub repository |
| `labelPrefix` | string | `—` | Prefix for auto-created labels (e.g. `"cg:"`) — absent/null means no prefix |
| `autoCreate` | bool | `false` | If `true`, `/cg-issues backfill` may offer batch creation (still requires per-issue confirmation) |

Configure with `/cg-issues setup` or `/cg-setup`. `@cg-roadmap` is the only agent that writes this block.

GitHub Issues are supplementary tracking handles for roadmap work items. The roadmap remains authoritative for feature status and plan links. Workflow prompts should only recommend issue setup/backfill/linking when useful; they do not create issues automatically.

#### `features[].github` block (optional)

Per-feature GitHub issue linkage. All sub-fields are optional; omit the entire block when no issue is linked.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `repo` | string | — | `owner/repo` — overrides top-level when issue lives in a different repo |
| `issueNumber` | integer | — | Positive integer GitHub issue number |
| `issueUrl` | string | — | Full URL: `https://github.com/owner/repo/issues/<number>` |
| `createdAt` | string | — | ISO date `yyyy-MM-dd` when the link was created |

Attach with `/cg-issues link` or `/cg-issues backfill`. Adding `github` metadata never changes `features[].status`.

After an initial backfill, normal maintenance is delta-based: `/cg-strategy`, `/cg-plan`, `/cg-work`, and `/cg-resume` should surface missing issue links for newly relevant work and hand off to `/cg-issues`, while `/cg-commit-push-pr` uses linked issue metadata for `Refs #` or confirmed `Closes #` PR references.

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
| `cg-skill-stata-testing` | Stata testing & reproducibility patterns: inline assertions (`assert`, `capture`, `_rc`, exit codes), data validation (`isid`, `duplicates`, `misstable`), econometric result verification (`_b[]`, `reldif`, `test`), `reprun`/`repkit` reproducibility workflows, test scaffolding (`foreach`, `preserve`/`restore`), and 9 testing-specific anti-patterns. Load when writing, reviewing, or debugging test blocks in `.do`/`.ado` files. |
| `cg-skill-git-workflow` | Branching, commits, PR templates, `.gitignore` |
| `cg-skill-brainstorming` | Requirement elicitation and decision capture |
| `cg-skill-compound-docs` | Knowledge capture and categorization system |
| `cg-skill-fix-triage-migrate` | Migration mode for `/cg-fix-triage --migrate`: backfills `findings:` tracking frontmatter on legacy review files. Does NOT apply fixes. |
| `cg-skill-project-scanner` | Project scanner signal catalog for `/cg-setup`: language/framework detection (Tier 1), project type signals (Tier 2), charter-draft content extraction (Tier 3). Dispatched by `@cg-project-scanner`. |

---

## Configuration

Run `/cg-setup` in Copilot Chat after running `cg-link`. The prompt asks:
- **Language**: R, Python, Stata, or any combination
- **R syntax dialect** (if R is selected): `data.table-collapse` (default) or `tidyverse`
- **Project type**: Package, analysis, dashboard, API, tool
- **Review depth**: Light, standard, or thorough (`thorough` is treated as the `full` route)
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
| `review-depth` | `"light"`, `"standard"`, `"thorough"` | Legacy depth default for `/cg-review`; `thorough` maps to the `full` route. Explicit routed modes can be passed at invocation time. |
| `cg-schema-version` | date string | Auto-managed by `cg-update`. Do not edit manually. |

### `compound-gpid.context.md`

A committed, growing knowledge base for project-specific context. Created by `/cg-setup`. Extended by `/cg-compound` after each significant task. Ordinary prompts load targeted headings or snippets when tactical facts are relevant instead of reading the whole file by default.

Typical contents: data source locations and caveats, domain vocabulary, workspace folder descriptions, variable-level notes, recurring gotchas. Unlike the charter (`compound-gpid.md`), `compound-gpid.context.md` has no fixed structure — organise it by topic.

---

## Directory Structure

After linking and configuring, your project will contain:

```
your-project/
├── AGENTS.md                 # optional Codex / Claude Code adapter; not used by GitHub Copilot
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
    ├── cost/                 # context/model audit reports and release-readiness checklists
    ├── inbox/                # unprocessed strategy ideas; not approved roadmap items until promoted via /cg-strategy
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

`.cg-docs/inbox/` is only a holding area. Do not treat files there as approved
roadmap items until a separate strategy or roadmap session promotes them.

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

### Plan Frontmatter: Phase Fields

Phased plans (created with `/cg-plan` when the user requests phases) carry additional frontmatter fields for tracking cross-session execution:

| Field | Type | Written by | Read by | Notes |
|-------|------|-----------|---------|-------|
| `phases` | integer | `/cg-plan` Step 3.5 | (not read at runtime — informational only for human readers) | **Convenience hint** — may become stale if phases are restructured. The authoritative phase count is always derived by counting `## Phase` headers in the document body. Never use this field as the source of truth for validation. |
| `completed-phases` | YAML flow sequence of unquoted integers, e.g. `[1, 2]` | `/cg-work` Step 2.5 | `/cg-work` Step 1.2, `/cg-resume` Step 2a | **Authoritative completion record.** Written first at phase boundary (before `current-phase`). A plan with a non-empty list and `status: active` is "paused between phases" — this is the normal cross-session state. |
| `current-phase` | integer | `/cg-work` Step 2.5 | (informational only) | Written after `completed-phases`. Set to N+1 after completing phase N; removed when the final phase completes. |
