# Reference

Detailed contracts for Compound GPID commands, agents, schemas, configuration,
and file structure. Use the focused [Commands](reference/commands.md),
[Agents](reference/agents.md), [Skills](skills/index.md), and
[Files and Artifacts](reference/files.md) pages for quicker navigation.

> See [Workflow](workflow.md) for a full explanation of each prompt step. See [Modular Guide](modular-guide.md) for choosing between the technical (`/cg-*`) and research (`/cr-*`) suites, capability packs, module preferences, and extension rules. See [Installation](installation.md) for setup instructions. See [Context Files](context-files.md) for a detailed guide to `copilot-instructions.md`, `compound-gpid.md`, `compound-gpid.context.md`, and the generated native platform trees (`.claude/`, `.agents/`, `.opencode/`, `.kilo/`). See [Troubleshooting](troubleshooting.md) for known issues.

Compound GPID generates native platform trees for Claude Code, Codex, OpenCode, and Kilo from the canonical `.github/` source. The trees are committed,
release-validated, and distributed through merge-safe per-platform install units.
`cg-link` links all supported platforms by default; use `--platforms` to narrow
the install to a comma-separated list. The `adapters/` directory contains
legacy source adapters that are superseded by the generated trees.

## Native Target Packaging

`.github/` is the canonical input. The generator treats every regular skill
directory as an **atomic skill bundle**: it **includes by default** `SKILL.md`
and all recursively nested regular files. It copies executable files as opaque
bytes, records and preserves executable mode, and guarantees they are **never
executed** during inventory, generation, validation, or cleanup.

In short, the regular-file policy is **include by default**, not an allowlist of
known support filenames.

The mapping defines these target-local runtime and support roots:

| Target | Commands | Skills | Agents | Instructions | Shared/support |
|--------|----------|--------|--------|--------------|----------------|
| Claude Code | `.claude/commands` | `.claude/skills` | `.claude/agents` | `.claude/instructions` | `.claude/shared` |
| Codex | `.agents/commands` | `.agents/skills` | `.agents/subagents` | `.agents/instructions` | `.agents/shared` |
| OpenCode | `.opencode/commands` | `.opencode/skills` | `.opencode/agents` | `.opencode/instructions` | `.opencode/shared` |
| Kilo | `.kilo/commands` | `.kilo/skills` | `.kilo/agents` | `.kilo/instructions` | `.kilo/shared` |

Generation computes a deterministic isolated dependency closure across command
support files, complete skill bundles, agents, instructions, and shared
contracts. A generated target must resolve without the canonical `.github/`
tree; unresolved or unsafe canonical runtime references fail generation.

### Ownership manifest schema

The fixed manifests are `.claude/.compound-gpid-generated.json`,
`.agents/.compound-gpid-generated.json`,
`.opencode/.compound-gpid-generated.json`, and
`.kilo/.compound-gpid-generated.json`. Their schema is:

```json
{
  "schemaVersion": 1,
  "target": "claude-code",
  "policyVersion": 1,
  "files": [
    {
      "path": ".claude/commands/cg-setup.md",
      "source": ".github/prompts/cg-setup.prompt.md",
      "kind": "command",
      "sha256": "<64 lowercase hexadecimal characters>",
      "executable": false
    }
  ]
}
```

Top-level and file-entry fields are fixed; `files` is sorted by `path`, and the
manifest is deterministic and excludes itself. Before mutation, the generator
validates ownership, destinations, and checksums. Stale cleanup is
checksum-guarded: only a prior-manifest-owned stale regular file whose current
hash equals its recorded `sha256` is deleted. Untracked files are preserved.
Files are atomically replaced before stale cleanup, and the manifest is
**written last**, so a later rerun provides safe recovery from interruption.

These source-repository ownership manifests are **distinct from** consumer
`.compound-gpid/managed-files.json`, which controls merge-safe copied install
files used by `cg-link`, `cg-update`, and `cg-unlink`.

### Verification and release gates

Required evidence is deterministic and does not depend on installed vendor
tools: isolated fixtures verify dependency closure without `.github/`, the
generator determinism suite proves repeated byte-identical plans/manifests, and
drift tests compare committed trees with canonical inputs. CI runs the native
target Python gate on Windows and macOS. Release publication has a separate
release gate: `create-release.ps1` runs mapping, path-safety, packaging,
ownership, closure, determinism, drift, and platform suites before reading
credentials or calling GitHub.

A real CLI smoke run with `claude`, `codex`, `opencode`, or `kilo` is optional,
additional runtime evidence only. CLI availability is reported separately;
missing real CLI evidence never skips or weakens deterministic isolated
closure, and documentation must not imply runtime proof that was not run.

Optional retrieval backend candidates are documented in
[Retrieval Backend Evaluation](retrieval-backends.md) and tracked in
`.github/shared/retrieval-backends.json`. The registry is evaluation-only:
`native-brain-query` remains the only active backend.

Snapshot and external-research mode candidates are documented in
[Snapshot and External-Research Modes](snapshot-external-research.md) and
tracked in `.github/shared/snapshot-research-modes.json`. The registry is
evaluation-only: `local-workflow` remains the only active mode.

---

## Shell Commands

> Core install commands are available from PowerShell on Windows and from bash/zsh on macOS. The `cg-*-summary` wrappers are bash wrappers in `bin/`; use them from bash/zsh or run `python scripts/cg_summary.py <kind>` directly on Windows.

| Command | Where to run | Purpose |
|---------|-------------|---------|
| `cg-link [--platforms <list>]` | Project root | Link all supported platforms by default: Copilot `.github/`, Claude Code `.claude/`, Codex `.agents/`, OpenCode `.opencode/`, and Kilo `.kilo/`. Use `--platforms copilot` or another comma-separated list to narrow the install. |
| `cg-unlink` | Project root | Remove Compound GPID-managed install units and manifest-managed copied files while preserving user-owned platform content. |
| `cg-update [<version>\|latest\|--list\|--fix]` | Anywhere | Update, pin, unpin, list releases, or repair a Compound GPID installation. |
| `cg-kilo [<kilo arguments>]` | Project root | Certified Kilo launch. For projects with Codex/Claude roots, validates containment and disables external skill discovery only in the child Kilo process; direct launches are unsupported. |
| `cg-brain-init` | Project root | Initialize or configure Team Brain integration and scaffold the central GitHub repository configuration. Usage: `cg-brain-init --repo <owner/name> --manager <github-username>`. |
| `cg-index` | Project root | Build or query the local `.cg-docs/` Knowledge Brain index. |
| `cg-index --brain` | Project root | Rebuild generated Brain artifacts such as `BRAIN.md`, topic files, and `brain-index.json`. |
| `cg-render-artifact <source>` | Project root | Validate and explicitly render one Brainstorm or Plan, even when automatic HTML is disabled. |
| `cg-render-artifact --automatic <source>` | Project root | Always validate; write HTML only when `artifact-html: true` is configured. |
| `cg-render-artifact --validate-only <source>` | Project root | Validate one canonical artifact without writing HTML. |
| `cg-render-artifact --check <source>` | Project root | Print `current` and exit code 0 only for an exact current view; print `missing` or `stale` and exit code 1 otherwise. Input/usage errors return exit code 2. |
| `cg-publish-markdown <source>` | Project root | Publish one project-contained generic Markdown file to the mirrored `.cg-docs/views/documents/` path. |
| `cg-publish-markdown --automatic <source>` | Project root | Validate generic Markdown and publish only when `artifact-html: true` is configured. |
| `cg-publish-markdown --validate-only [--theme reference] <source>` | Project root | Validate generic source, output identity, local resources, and theme without inspecting or writing output. |
| `cg-publish-markdown --check [--theme reference] <source>` | Project root | Reproduce expected schema-2 bytes; return exit code 0 for `current`, 1 for `missing`/`stale`, and 2 for invalid input. |
| `cg-publish-markdown --output <documents-view.html> <source>` | Project root | Publish to one portable relative destination under `.cg-docs/views/documents/`. |
| `cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations` | Project root | Generate context-cost reports, token dashboard artifacts, regression checks, and compact recommendations. |
| `cg-test-summary --root . --format json` | Project root | Summarize `tests/last-run.json` without running tests and store a redacted source artifact. |
| `cg-diff-summary --root . --format md` | Project root | Summarize changed files, hunks, and risk tags while storing the full redacted diff artifact. |
| `cg-log-summary --root . --format json` | Project root | Summarize branch-local first-parent commits and notable files. |
| `cg-tree-summary --root . --max-entries 120 --format md` | Project root | Summarize a bounded repository tree while excluding generated outputs, dependencies, and caches. |
| `cg-problems-summary --root . --input problems.json --format json` | Project root | Summarize optional diagnostics JSON or text; reports unavailable when no diagnostics input is provided. |
| `python scripts/cg_project_manifest.py [--root <path>] [--output <path>] [--platforms copilot,kilo] [--validate] [--check-stale <manifest>] [--ensure-state]` | Project root | `cg-project-manifest` — resolve and validate the canonical committed active project manifest (`.compound-gpid/active-manifest.json`) from the strict config plus the versioned module registry. Records config/registry hashes, schema versions (`config-schema-version`), selected suites, derived and explicit capabilities, the resolved module closure, canonical platform ids, platform eligibility, and the projection plan digest. Immutable selection validity is separated from mutable projection ownership. Exit codes: `0` success, `1` resolution/validation failure, `2` missing or invalid project root. |
| `python scripts/cg_projection_benchmark.py [--root <path>] [--profiles cg-only,cr-only,mixed,capability-python] [--validate]` | Project root | `cg-projection-benchmark` — emit deterministic before-state profile baseline matrices (`.cg-docs/cost/skill-loading-baseline.json` + `.md`) for projection. Per profile: requested command/capability, expected route, expected hard-stop or catalog summary, expected inventory digest, and a supported-host procedure. Token estimates are heuristic (chars/4) and never claim savings; unavailable required host evidence is a blocking `unavailable`, never a zero. Exit codes: `0` success, `1` validation/oracle failure, `2` missing or invalid project root. |

Windows installs include matching `.cmd` wrappers for the core install commands where platform-specific launch behavior is required.

Generic publishing uses the frozen `reference` theme version 1 and provenance
schema 2. Every destination has one source owner identified by `sourcePath`,
`documentType`, and `outputPath`. Existing corrupt or differently owned output
fails without mutation. Brainstorms and Plans retain strict validation and must
use `cg-render-artifact`; generic publishing cannot act as a schema bypass.

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
| Prompt | Purpose |
|--------|---------|
| `/cg-brain-rebuild` | Rebuild the project knowledge brain (BRAIN.md + indexes). |
| `/cg-brainstorm` | Brainstorm answers about what to build and how. Use when requirements are fuzzy. |
| `/cg-commit-push-pr` | Stage changes into logical commits, push, and open a PR with plan-driven description. |
| `/cg-compound-refresh` | Audit and refresh .cg-docs/solutions/ for staleness, drift, and consolidation opportunities. |
| `/cg-compound` | Capture a solved problem as reusable knowledge. Offers canonical .github/ updates; the user applies them manually after fixing a non-trivial issue. |
| `/cg-devtag` | Create a dev tag (v&lt;MAJOR&gt;.&lt;MINOR&gt;.&lt;PATCH&gt;.9000+) on the current branch and push it to origin. Enables end-to-end installation testing via cg-update before an official release. Developer-only. |
| `/cg-diagnose` | Diagnose VS Code crashes. Inspects logs, classifies the crash category, checks for uncommitted work, and recommends recovery steps. |
| `/cg-find-skill` | Discover skills and capabilities from the manifest-backed catalog. |
| `/cg-fix-problems` | Interactive VS Code diagnostics fixer. Scans all workspace files for errors, warnings, and info diagnostics, lets the user select scope and severity, then applies fixes. Dispatches @cg-fix-problems agent. |
| `/cg-fix-triage` | Apply review findings from a saved review report. Fixes all findings or a subset by ID/priority. |
| `/cg-fixbug` | Structured bug-fix workflow: establish the expected-behavior source in Step 1.5, perform test-gap classification in Step 2.5, and require red-green proof. |
| `/cg-ideate` | Generate, critique, and filter improvement ideas for the project. Use before /cg-brainstorm when you want to discover what to work on next. |
| `/cg-import-skill` | Import an external skill into Compound GPID with quarantine, security scanning, and approval workflow. |
| `/cg-issues` | Manage GitHub Issues linked to roadmap work items. Modes: status (default, read-only), backfill, link, adopt, setup. |
| `/cg-plan-review` | Review an implementation plan for risks, over-engineering, missing edge cases, and flawed assumptions. Use after /cg-plan or on any existing plan. |
| `/cg-plan` | Create a structured implementation plan with research. Use after brainstorming or when requirements are clear. |
| `/cg-release` | Create a GitHub Release for compound-gpid. Detects the next semver tag from git history, drafts curated release notes, checks SCHEMA_VERSION, confirms with the user, and publishes. Developer-only — guarded to the compound-gpid repo; Step 0 stops execution in consumer projects. |
| `/cg-render-doc` | Render a workflow artifact or generic Markdown document to curated HTML. Routes typed artifacts to cg-render-artifact and generic documents to cg-publish-markdown. Supports --theme selection (reference or editorial). |
| `/cg-resume` | Load context and resume interrupted work. Use at the start of a session to pick up where you left off. |
| `/cg-review-repos` | Review external repos for features to integrate into compound-gpid. Developer-only. |
| `/cg-review` | Run multi-agent code review on recent changes. Produces prioritized P0/P1/P2/P3 findings. |
| `/cg-roadmap-view` | Visualize the project roadmap in chat. Supports flags: --milestone, --tasks, --detail, --status, --wip, --plan, --help. Dispatches @cg-roadmap-view agent for rendering. |
| `/cg-setup` | Configure Compound GPID for this project and load context for returning projects. |
| `/cg-strategy` | Strategic project visioning and direction-setting. Use when you have a full project in mind to structure, or when you need to rethink direction mid-project. Dispatches @cg-roadmap for all roadmap writes. |
| `/cg-token-audit` | Analyze Compound GPID token/context usage and suggest cost-efficient workflow choices. |
| `/cg-verify-pr` | Check CI status on current PR, classify failures, and auto-fix with review agents. Use --propose for observe-only diagnosis. |
| `/cg-wiki` | Manage the project wiki: initialize, rebuild pages, restructure sections, check status, or convert to GitHub Wiki format. |
| `/cg-work` | Implement a /cg-plan plan. Supports /cg-work [phaseX], review, and deviate controls. |
<!-- cg:auto:end -->

### `/cg-commit-push-pr` Base And Preflight Contract

Use `--base <branch>` when the intended PR target is not the repository default.
The prompt resolves one `$baseBranch` before generation or staging with this
precedence: existing PR `baseRefName`, explicit `--base`, then the repository
default branch. If the existing PR base conflicts with explicit input, it reports
both values and uses the actual existing PR base.

The prepare gate runs `cg_pr_preflight.py --phase prepare --base <branch>
--run-native-target` before staging. After commits, the committed gate runs the
same preflight with `--phase committed --base <branch> --run-native-target`
before push. Nonzero or partial results block the operation; a successful
`generic-not-applicable` Kilo result is a neutral capability outcome for generic
behavior and does not claim certified-host integration.

`gh` creation always receives `--base <branch>`. The VS Code GitHub Pull Request
extension must resolve and honor the same `baseBranch`; if it cannot, the prompt
halts with a manual `gh pr create --base <branch> --body-file <file>` route rather
than silently selecting a different base.

### `/cg-verify-pr` Exact Diagnosis And Repair Contract

`/cg-verify-pr` requests the open PR's actual `baseRefName` in the same
`statusCheckRollup` metadata query and halts if that base is unavailable. It uses
that `$baseBranch` for every fetch, merge-base, rebase, changed-file comparison,
preflight, and trailer-history operation; it never infers a base from a remote
symbolic ref.

For each failed check, the prompt reads its `detailsUrl` and accepts only a
GitHub Actions job URL containing both identifiers. It retrieves the exact failed
job with:

```text
gh run view <run-id> --job <job-id> --log-failed
```

Missing, non-Actions, unparseable, or unavailable URLs/logs use a manual route:
open the check provider's details page, obtain the exact run/job IDs and failed
step output, and do not select a latest run by workflow name or recency.

Auto-fix first runs `git status --porcelain` and stops on any pre-existing staged,
unstaged, or untracked change. After a clean baseline, the prompt runs
`scripts/cg_pr_preflight.py` with `$baseBranch` and the PR changed files to select
the exact focused local reproduction. A certified-host Kilo failure confirmed by
the exact job log may use the certified-host remediation path; Kilo
`generic-not-applicable` is neutral capability evidence, and generic linker
failure is never Kilo integration proof.

Only post-baseline targeted paths are staged. One verification pass creates
exactly one `fix(ci)` commit with one unique `CI-Fix-Round: <PR>/<N>` trailer in
`$mergeBase..HEAD`; historical `fix(ci):` subjects do not count. A rebase uses
the resolved PR base, and `--force-with-lease` is used only after that rebase.

Certified-host Kilo evidence is separate from generic CI. Configure the protected
repository variables `CG_KILO_CERTIFIED_RUNNER`, `CG_KILO_CERTIFIED_VERSION`, and
`CG_KILO_CERTIFIED_SHA256`, and require maintainer approval for the
`cg-kilo-certified` environment. The certified job runs only on a protected
default-branch push or an explicitly requested workflow dispatch for that same
default branch, checks out that trusted ref, compares the preflight-reported
executable version and SHA-256 before launch, and uploads `kilo-preflight.json`
and inventory evidence. Missing configuration produces a neutral
`generic-not-applicable` summary; generic CI never claims real-host integration.

### Research Suite Commands

These commands are owned by `suite-cr` and are available when `suites:` in
`compound-gpid.local.md` includes `cr`. The research suite composes shared
language, review, knowledge, and publication capabilities without depending on
the technical command suite.

<!-- cg:auto:research-commands -->
| Prompt | Purpose |
|--------|---------|
| `/cr-brainstorm` | Research brainstorm — clarify fuzzy research requirements. Classifies task type (theory, EDA, implementation, ML, writing, etc.) and guides methodology decisions. Use for economics and econometrics research tasks. |
| `/cr-compound` | Research compound — capture a solved research problem for future reuse. Extends /cg-compound with research-specific categories: identification, specification, derivation, ml-methodology, reproducibility. |
| `/cr-plan` | Research plan — structured implementation plan for research tasks. Use after /cr-brainstorm to create concrete steps. |
| `/cr-review` | Research review — multi-agent code and methodology review. Orchestrates cg-* agents (code quality, testing, reproducibility) and cr-* agents (research integrity, mathematical verification, identification audit, econometric reasoning). Produces prioritized P0/P1/P2/P3 findings. |
| `/cr-work` | Research work — implement a research plan step by step. Supports /cr-work [phaseX]. Enforces P0 seed, provenance, and specification logging requirements. |
<!-- cg:auto:end -->

The research lifecycle is `Scope -> Evidence -> Theory -> Method -> Execute ->
Verify -> Communicate -> Maintain`. Use `/cr-review`, not `/cg-review`, for
research-domain agent routing.

### `cg-index --brain` — Diagnostic Warnings

`cg-index --brain` writes scan-pass warnings to stderr during execution:

| Message | Meaning |
|---------|---------|
| `[cg-index] WARNING: Skipping <file>: ...` | File could not be read and was excluded from the Brain index. |
| `[cg-index] WARNING: Skipping <file>: no frontmatter found` | File lacks a `---` frontmatter block and was excluded from the index. |
| `[cg-index] WARNING: <file>: missing required field(s): ...` | Frontmatter is missing required metadata such as `title` or `date`. |
| `[cg-index] WARNING: Duplicate frontmatter key <key>` | Frontmatter repeats a key; the last value is used. |
| `[cg-index] WARNING: roadmap feature ... has no id` | A roadmap feature lacks an `id` and is skipped for Brain linking. |

To capture warnings: `cg-index --brain 2>brain-warnings.txt`.

### `cg-index query` — Budgeted Knowledge Brain Retrieval

Use `cg-index query` when a workflow needs prior project knowledge without opening generated Brain partitions by hand:

```bash
cg-index query --intent plan --query "workflow token baseline" --budget 600 --format md
cg-index query --intent review --query "Pester safe runner" --changed-file tests/Run-Tests.ps1 --budget 600 --format json
```

The query mode returns a short answer, selected artifact paths, snippets, selection and exclusion reasons, stale or conflict flags, confidence, and a heuristic token estimate. It is local and deterministic; it does not use vector search, external services, or optional retrieval backends.

### Command Output Summary Wrappers

Use the `cg-*-summary` wrappers when a workflow needs compact evidence from noisy local command surfaces while retaining the full source output on disk:

```bash
cg-test-summary --root . --format json
cg-diff-summary --root . --format md
cg-log-summary --root . --format json
cg-tree-summary --root . --max-entries 80 --format md
cg-problems-summary --root . --input diagnostics.json --format json
```

The wrappers are local stdlib tooling. They do not call external services, mutate GitHub, or replace required validation commands. `cg-test-summary` only reads existing `tests/last-run.json`; it does not run Pester, pytest, R, or Stata. Full raw/source outputs are redacted for common secret-looking patterns and written under `.cg-docs/token/outputs/YYYYMMDD-HHMMSS-<kind>/`. Keep that directory for short-lived validation evidence, not durable project knowledge; record final decisions in plans, reviews, work reports, and solutions instead.

### `cg-token-audit` / `cg-audit-context` — Context and Model-Governance Audit

```bash
cg-token-audit --root . --output-dir .cg-docs/cost --format both --recommendations
python scripts/cg_audit_context.py [--root PATH] [--output-dir PATH] [--format json|md|both] [--baseline context-audit.json] [--recommendations] [--token-output-dir PATH] [--no-token-artifacts]
```

Inventories context-contributing files, estimates token burden with a chars/4 heuristic, checks executable model metadata and advisory provenance, detects duplicate paragraph blocks, and benchmarks the tracked `/cg-*` workflows plus Knowledge Brain/context lookup behavior.

Use `--baseline` with a previous `context-audit.json` to render before/after benchmark deltas. Use `--recommendations` to also write `.cg-docs/cost/token-advice.md`. The token regression check reports `baseline` when no previous comparable audit is supplied, `pass` when a comparable run has no deterministic guardrail failures, and `fail` when guardrail failures are present.

Workflow baseline artifacts:

| Artifact | Purpose |
|----------|---------|
| `.cg-docs/token/TOKEN-BUDGET.md` | Human-readable workflow baseline, observability boundaries, and no-savings-claim policy. |
| `.cg-docs/token/TOKEN-DASHBOARD.md` | Compact maintainer dashboard with regression status, highest workflow budgets, and warning/context summaries. |
| `.cg-docs/token/token-audit.json` | Canonical JSON baseline payload with workflow telemetry, benchmarks, guardrails, and warning classifications. |
| `.cg-docs/token/context-map.json` | Workflow-to-context map of deterministic file, skill, agent, tool, and context-loading signals. |
| `.cg-docs/token/regression-check.json` | Machine-readable token regression status derived from deterministic guardrails and optional baseline comparison. |
| `.cg-docs/token/workflow-costs.csv` | Spreadsheet-friendly workflow rows for tracked workflows. |
| `.cg-docs/token/large-context-warnings.md` | Large prompt/instruction/skill and repeated-context warnings without copying large bodies. |

Model-advisory guardrails report executable model metadata, invalid advisory provenance or effort labels, missing user-control language, and stale stage coverage. Runtime-only quantities such as command-output size, picker availability, and summary size remain explicit observed/not_observed fields until instrumentation exists.

Exit codes: `0` success, `1` fatal error, `2` missing or invalid project root.

### Active-State Handoff Records

Long-running workflows may write a compact restart aid at
`.cg-docs/active-state/current.json`. The schema is defined in
`.github/shared/active-state.contract.md`. Records contain artifact paths,
current phase, evidence status, unresolved decisions, and an exact
`nextCommand`; they must not copy transcripts, raw command output, full review
findings, or full report bodies. `/cg-resume` reads the record when present and
validates referenced paths before using it. `/cg-diagnose` may include the same
compact pointers in crash recovery handoffs, but remains read-only.

For token-optimization release candidates, complete
`.cg-docs/cost/token-optimization-release-checklist.md` after generating the
audit. Keep non-blocking issues in
`.cg-docs/cost/token-optimization-follow-ups.md` so release blockers and future
cleanup stay separate.

> **Model guidance**: See [Model Guide](model-guide.md) for stage capability profiles, effort suggestions, provenance, and user-controlled selection.

> **Project Charter**: All `/cg-*` prompts automatically read `compound-gpid.md` at session start (if it exists). If missing, prompts remind you to run `/cg-setup` to optionally create one. Prompts work without a charter — the reminder is advisory.

> **Prior-work awareness**: `/cg-brainstorm` checks `.cg-docs/brainstorms/` and `/cg-plan` checks `.cg-docs/plans/` for related prior work before starting. If a match is found, you can continue from it, follow up, or start fresh.

> **Scope assessment**: `/cg-brainstorm`, `/cg-plan`, and `/cg-work` all classify the task scope (Lightweight / Standard / Deep) and adapt their behavior accordingly. `/cg-work` declines to generate inline plans for Standard/Deep tasks — use `/cg-plan` first.

### Plugin Development (developer-only)

> **Consumer project users**: The prompts below are for compound-gpid maintenance
> only. `/cg-release` and `/cg-review-repos` appear in your autocomplete because
> they are distributed via junctions, but they **will not run** outside the
> compound-gpid repo — Step 0 stops them immediately. Do not use these prompts in
> consumer projects.

| Prompt | Purpose | Distribution |
|--------|---------|-------------|
| `/cg-release [vX.Y.Z[.build]]` | Create a stable release from `main` or a four-component prerelease from `dev`. Detects the next tag unless an exact tag is supplied, drafts release notes from `.cg-docs/`, checks `SCHEMA_VERSION`, and publishes to GitHub Releases. | **Distributed** via junctions to consumer projects, but Step 0 stops execution immediately if not run inside compound-gpid. |
| `/cg-review-repos [--full]` | Review external repos for features to integrate into compound-gpid. Default (delta) mode reviews only releases newer than the last review. `--full` performs a deep initial assessment of all repos — required before delta mode can be used. Updates `.cg-docs/competitive-reviews/repos.json` after each run. | **Distributed** via junctions to consumer projects, but Step 0 stops execution immediately if not run inside compound-gpid. |

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

| Agent | Focus |
|-------|-------|
| `cg-code-quality` | Style, linting, DRY, naming |
| `cg-testing` | Coverage, edge cases, test quality |
| `cg-documentation` | roxygen2/docstrings/do-file headers, README, comments |
| `cg-version-control` | Commit hygiene, branching, secrets |
| `cg-reproducibility` | Lockfiles, relative paths, seeds, repkit |
| `cg-performance` | Vectorization, memory, algorithm complexity |
| `cg-architecture` | Project structure, modularity, dependencies |
| `cg-data-quality` | Input validation, types, missing values |
| `cg-learnings-researcher` | Cross-reference past solutions (`full` / `thorough` alias only) |
| `cg-adversarial` | Adversarial testing: edge cases, data corruption, security (`full` / `thorough` alias only) |

> Review agents are primarily dispatched by `/cg-review`. `/cg-verify-pr` also dispatches `@cg-testing` (test failure analysis) and `@cg-code-quality` (build error analysis) as part of CI triage. Agents are NOT user-invokable and do not appear in the Copilot Chat agent dropdown.

### Research Review Agents

Research agents are owned by `suite-cr` and dispatched conditionally by
`/cr-review`. They are not imported into `/cg-review`.

| Agent | Focus |
|-------|-------|
| `cr-research-integrity` | P0 silent research errors and integrity gates |
| `cr-provenance-audit` | Claim-evidence traceability and citation provenance |
| `cr-mathematical-verification` | Derivation-to-code consistency |
| `cr-identification-audit` | Identification strategy and required diagnostics |
| `cr-econometric-reasoning` | Structural and econometric model logic |
| `cr-ml-methodology` | Validation design, leakage, inference, and interpretation |
| `cr-specification-analysis` | Theory-data implications and specification discipline |
| `cr-measurement-integrity` | Indicator, threshold, clustering, and comparability integrity |
| `cr-academic-writing` | Economics-paper structure, notation, and citations |
| `cr-publication-output` | Publication tables, figures, notes, and deterministic output |
| `cr-replication-package` | Replication archive completeness, safety, and portability |

> ℹ️ For stage capability guidance and user-controlled effort selection, see [Model Guide](model-guide.md).

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
| `@cg-release-scanner` | Classifies commits by conventional commit prefix, lists relevant `.cg-docs/` entries within the scan window, and returns a structured categorized report for `/cg-release` | Claude Haiku 4.5 | No |

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

The [Skills Catalog](skills/index.md) is the public, goal-oriented inventory and
documents availability labels and source-of-truth maintenance. The table below
is retained as a compact technical summary.

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
| `cg-skill-wb-report-writing` | Progressive-disclosure World Bank institutional report-writing router with source-pack preflight, marker safety, and operation/type routing across PRWP, policy briefs, executive summaries, flagship sections, country narratives, technical methodology, internal memos, and data blogs. |
| `cg-skill-fix-triage-migrate` | Migration mode for `/cg-fix-triage --migrate`: backfills `findings:` tracking frontmatter on legacy review files. Does NOT apply fixes. |
| `cg-skill-project-scanner` | Project scanner signal catalog for `/cg-setup`: language/framework detection (Tier 1), project type signals (Tier 2), charter-draft content extraction (Tier 3). Dispatched by `@cg-project-scanner`. |
| `cg-skill-brain-query` | Selective Knowledge Brain query protocol for relevance, stale/conflicting evidence, and source citation. Loaded by Consult Brain steps. |
| `cg-skill-pester-safety` | Compound GPID workspace safety rules for Pester execution and the canonical test runner. Internal and environment-specific. |
| `cg-skill-wiki` | Wiki manifest, ownership, managed-section, conflict, template, and conversion rules. Loaded before `@cg-wiki` operations. |
| `cg-skill-windows-cmd-python-detection` | Safe Python candidate detection and Windows Store stub rejection for `bin/*.cmd` launchers. Internal and Windows-specific. |

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
| `suites` | `[cg]` (default/absent), `[cr]`, `[cg, cr]` | Active suite configuration for the modular architecture. Selects which workflow prompts/skills are loaded into routine sessions; the generator context-budget filter and `cg_migrate_config.py` use this field. |
| `artifact-html` | `true`, `false` | Explicit opt-in for automatic Brainstorm/Plan and generic Markdown HTML writes. Missing or invalid values default disabled (invalid values warn). Validation, explicit render, and `--check` remain available. |
| `cg-schema-version` | date string | Auto-managed by `cg-update`. Do not edit manually. |

### `compound-gpid.context.md`

A committed, growing knowledge base for project-specific context. Created by `/cg-setup`. Extended by `/cg-compound` after each significant task. Ordinary prompts load targeted headings or snippets when tactical facts are relevant instead of reading the whole file by default.

Typical contents: data source locations and caveats, domain vocabulary, workspace folder descriptions, variable-level notes, recurring gotchas. Unlike the charter (`compound-gpid.md`), `compound-gpid.context.md` has no fixed structure — organise it by topic.

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
│   ├── shared/               → junction to C:\WBG\.compound-gpid\.github\shared\
│   ├── copilot-instructions.md  # generated from template (managed marker); regenerated by cg-link/cg-update
│   └── workflows/            # your own GitHub Actions (untouched by cg-link)
├── .claude/                  # Claude Code install units: commands/skills/agents linked; root files copied if managed
├── .agents/                  # Codex install units: commands/skills/subagents linked; root files copied if managed
├── .opencode/                # OpenCode install units: commands/skills/agents linked; config copied if managed
├── .kilo/                    # Kilo install units: commands/skills/agent linked; config copied if managed
├── .compound-gpid/managed-files.json  # sidecar checksums for copied strict config/root files
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
