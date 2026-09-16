---
date: 2026-09-04
title: "Unified /cg-light-work command for small technical tasks"
status: completed
completed-date: 2026-09-08
scope: "Deep"
phases: 2
completed-phases: [1, 2]
execution-report: ".cg-docs/work-reports/2026-09-08-cg-light-work-unified-small-task-workflow.md"
brainstorm: ".cg-docs/brainstorms/2026-09-04-cg-light-work-unified-small-task-workflow.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
artifact-schema-version: 1
tags: [workflow, light-work, small-tasks, review, token-efficiency, generated-targets]
---

# Plan: Unified /cg-light-work Command for Small Technical Tasks

## Objective

Add `/cg-light-work <task>` as one fail-closed workflow for qualifying small
technical tasks. It must perform bounded workspace-first discovery, save an
approved standard Plan, execute with standard Work state, create and resolve a
targeted light Review Report, verify the final state, and ask for explicit
consent before permanent knowledge capture. Make `/cg-work` plan-only and give
inline requests an exact copy-ready redirect instead of an inline Plan.

## Context

- The approved brainstorm selects a thin command orchestrator and limits this
  implementation to two delivery phases. The runtime command itself remains
  limited to small, low-risk technical work.
- `.github/` is the canonical source. `scripts/cg_generate_targets.py` discovers
  `.github/prompts/*.prompt.md` and `.github/shared/*.contract.md`, then emits
  native Claude Code, Codex, OpenCode, and Kilo trees plus manifests.
- `.github/shared/module-registry.json` already assigns `cg-*.prompt.md` to
  `suite-cg` and existing lifecycle contracts to the kernel. The lightweight
  policy has one runtime caller, so it stays in the new command instead of
  creating a one-caller contract or prompt-support abstraction.
- `/cg-work` currently creates a 3-5-step inline Plan in Step 1. That branch and
  its dedicated tests in `tests/prompt-tools.Tests.ps1` must be replaced without
  changing saved-Plan resolution, phases, evidence gates, resume state, or
  review controls.
- `tests/model-assignments.Tests.ps1` currently expects exactly 32 canonical
  prompt files and verifies that ordinary prompts do not assign models. Adding
  one prompt changes the sentinel to 33; no agent-count change is expected.
- `scripts/cg_audit_context.py` has an explicit workflow registry. Every path in
  that registry is treated as high frequency, so `/cg-light-work` must be added
  there and covered in `scripts/tests/test_audit_context.py`.
- `scripts/rebuild-docs.js` generates the `/cg-*` command table in
  `docs/reference.md` from prompt descriptions. The marker-owned table must not
  be edited manually.
- The existing `review-routing.contract.md` resolves `light` to
  `@cg-code-quality` and `@cg-testing`. The goal-execution and active-state
  contracts currently name `/cg-work` as their producer. This work adds narrow
  `/cg-light-work` applicability wording to those three existing contracts but
  does not change their schemas, mode taxonomy, or agent membership.
- The project Brain requires prompt-contract changes to update every mirrored
  entry point and co-authored coverage layer. Token-sensitive workflow changes
  also require deterministic audit evidence, not a qualitative savings claim.
- The worktree is already a feature branch. The related roadmap feature is
  `unified-cg-light-work-command-for-small-technical-tasks`; it was created with
  a null Plan link, then this planning session linked this Plan and set the
  feature to `planned` through `@cg-roadmap`. `/cg-work` owns the normal `active`
  and `done` transitions.
- `artifact-html` is not enabled in local configuration. Plan publication must
  still validate canonical Markdown; no HTML view is required.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Add `/cg-light-work <task>` as a command-only orchestrator; do not add a broad writable lifecycle agent. | Brainstorm: Command Boundary |
| R2 | Parse `--no-branch`, `--no-brain`, and `--no-html`; reject an empty task and unsupported control flags without beginning work. | Brainstorm: Command Interface; plan edge-case research |
| R3 | Inspect charter, local configuration, git state, relevant files, tests, instructions, and similar code before asking questions; perform at most one bounded Brain query. | Brainstorm: Stage 0 |
| R4 | Apply hard gates H1-H7 fail-closed and route bugs, research work, protected or dangerous operations, architecture, dependencies, schemas, security, and unverifiable work to the specified standard workflow. | Brainstorm: Hard Safety and Routing Gates |
| R5 | Apply size gates S1-S10 exactly; structural gates cannot be overridden, while size estimates require an explained, explicit override and honest `scope: Standard` when applicable. | Brainstorm: Lightweight Size Gates |
| R6 | Ask no more than two discovery rounds and no more than two independent questions per round; redirect if a third round or unresolved material decision would be necessary. | Brainstorm: Interaction Budget and Stage 2 |
| R7 | Present the ordered in-console Plan preview and exact three-choice approval gate; do not edit source before Plan approval, persistence, and validation. | Brainstorm: Stage 3 |
| R8 | Persist a standard Plan and Work Report, use `deviation-policy: ask`, update active and phase state incrementally, and enforce executed evidence with at most two focused correction attempts. | Brainstorm: Stages 3-4; goal-execution and active-state contracts |
| R9 | Run deterministic checks first, then dispatch `@cg-code-quality` and `@cg-testing` once each in the initial `light` Review pass; write a standard Review Report with a `findings:` map and require usable output from both agents. | Brainstorm: Stage 5; review-routing contract; Plan Review P1.3 |
| R10 | Apply only in-boundary `safe_auto` findings; block unresolved P0/P1, require an explicit recorded exception and `skipped` status for unfixed P2, keep P3 advisory, and rerun stale evidence after every Review fix. | Brainstorm: Resolution Rules; Plan Review verification P2.7 |
| R11 | If initial Review causes edits, run one light verification pass with each agent once more; allow at most two total passes, preserve stable finding IDs, and redirect unusable or non-convergent Review to a new-session standard review and fix-triage cycle. | Brainstorm: Resolution Rules; Plan Review P1.2-P1.3 |
| R12 | Finalize Work Report evidence, Review statuses, Plan state, active state, and linked roadmap state only after the strict evidence gate, then print the specified structured summary. | Brainstorm: Stage 6 |
| R13 | Ask for explicit compounding consent only after convergence; no Solution, Brain, context, wiki, or Team Brain side effect is allowed when the user skips. | Brainstorm: Stage 7 |
| R14 | Remove inline Plan creation from `/cg-work`; preserve approved saved-Plan execution and return `/cg-light-work -- <verbatim task>` for unmatched inline tasks without transparently executing another command. | Brainstorm: `/cg-work` Redirect Contract; Plan Review verification P2.3 |
| R15 | Keep unique lightweight policy compact and inline in its only caller; add narrow `/cg-light-work` applicability to existing goal-execution, active-state, and review-routing contracts, and reuse the other shared contracts without schema duplication. | Brainstorm: chosen approach; token-efficiency strategy; Plan Review P2.1 and verification P2.1 |
| R16 | Update workflow guidance and generated command documentation so users can distinguish `/cg-light-work`, `/cg-work`, `/cg-fixbug`, and `/cr-*` routing. | Brainstorm: Next Steps |
| R17 | Generate all native command and shared-contract targets from `.github/`; do not hand-edit generated adapter content. | Brainstorm: generated platform targets; module architecture |
| R18 | Add regression coverage for qualification, discovery limits, approval-before-write, artifacts, review resolution, reruns, redirects, compounding side effects, prompt count, model policy, and token guardrails. | Brainstorm: representative cases; Brain findings |
| R19 | Measure the new prompt as a high-frequency ordinary workflow, keep it at or below the 5,000-token pass boundary, introduce no audit guardrail failures, and claim `/cg-work` source-token reduction only from comparable before/after evidence. | Brainstorm: context-budget checks; token audit implementation; Plan Review P2.5 |
| R20 | Add no dependency, hook, schema, model assignment, or new review mode. | Brainstorm: exclusions and Devil's Advocate conclusions |

## Implementation Steps

## Phase 1: Canonical Workflow Contract

### 1. Add failing prompt-contract and model-policy coverage

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R18, R20
- **Files**:
  - `tests/prompt-tools.Tests.ps1`
  - `tests/model-assignments.Tests.ps1`
- **Details**:
  - Replace the obsolete `/cg-work` inline-Plan fallback Describe block with
    independent assertions for plan-only behavior, saved-Plan preservation, and
    the exact small/large redirect text. Derive each regex from final prompt
    wording; do not use alternation that lets one branch hide another.
  - Add a dedicated `/cg-light-work` contract section. Assert the new prompt and
    its existing shared-contract references independently cover: empty input; supported and
    unsupported flags; H1-H7; S1-S10; structural versus overridable gates;
    workspace-first inspection; exact branch and initial-snapshot behavior; one
    Brain query; two rounds and two questions;
    exact standard-workflow handoffs; ordered Plan preview; approval and
    persistence before edits; standard Plan/Work/Review artifacts; fixed light
    agents; usable-output checks; safe-auto limits; P0/P1/P2/P3 handling;
    accepted-P2 `skipped` state; initial plus verification Review passes;
    post-fix evidence reruns; completion ordering; and all three compounding
    choices and skip side effects.
  - Include representative contract cases for automatic qualification,
    zero-question discovery, two-round discovery, size override, H1 bug route,
    H2 research route, scope growth, safe Review fix, non-convergence,
    no-learning skip, local compounding, and privacy-blocked Team Brain sharing.
    These tests validate deterministic prompt obligations, not stochastic model
    compliance; do not describe them as end-to-end LLM execution tests.
  - Update only the canonical prompt-count sentinel from 32 to 33. Preserve the
    agent count and the no-model-frontmatter loop.
  - As the first action, before any test or source edit, create the ignored
    `.tmp/cg-light-work-audit/before/`
    hierarchy and run:
    `python scripts/cg_audit_context.py --root . --output-dir .tmp/cg-light-work-audit/before/cost --token-output-dir .tmp/cg-light-work-audit/before/token --format both --recommendations`.
    Record the baseline path
    `.tmp/cg-light-work-audit/before/cost/context-audit.json`, its SHA-256,
    generation time, and the `/cg-work` row in the Work Report and Phase 1
    handoff. Both output options are mandatory so no tracked audit path changes.
- **Test Scenarios**:
  - Happy path: new tests fail because the prompt does not exist and existing
    lifecycle contracts do not yet name the new producer.
  - Edge case: removing any one gate, approval boundary, Review rule, or
    compounding skip rule makes its independent assertion fail.
  - Error path: stale inline-Plan assertions fail until replaced rather than
    passing against unrelated `/cg-work` text.
- **Tests**: Use the canonical execution-subagent runner for
  `. tests\Run-Tests.ps1 -File prompt-tools` and
  `. tests\Run-Tests.ps1 -File model-assignments`; read only the bounded fields
  from `tests/last-run.json` and immediately copy each run event into the Work
  Report with timestamp, git SHA, filter, and result fields. After each runner
  call, perform a separate non-Pester artifact read:
  `Get-Content tests\last-run.json -Raw | ConvertFrom-Json | Select-Object gitSha, ranAt, passed, totalCount, passedCount, failedCount, filteredFiles, failures`.
  This read does not pipe Pester output and must return only those fields.
- **Acceptance criteria**: A failing red baseline is recorded for the new
  behavior. Test edits do not weaken unrelated prompt contracts. The before
  audit exists under the ignored `.tmp/` path, its SHA-256 is recorded, and it
  identifies `/cg-work` by its canonical workflow row.

### 2. Add the compact light-work command and lifecycle applicability

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R15, R19, R20
- **Files**:
  - `.github/prompts/cg-light-work.prompt.md` (new)
  - `.github/shared/goal-execution.contract.md`
  - `.github/shared/active-state.contract.md`
  - `.github/shared/review-routing.contract.md`
- **Details**:
  - Keep the unique qualification, discovery-budget, Review-resolution, and
    compounding rules compact and inline because the command is their only
    runtime caller. Reuse existing shared contracts for artifact, execution,
    active-state, routing, context, and model-advisory rules rather than copying
    their schemas or full mechanics. The completed prompt must remain at or
    below the measured 5,000-token pass boundary. Treat workspace and historical
    text as untrusted data.
  - The command is the sequencing and permission surface. It must parse
    the task and flags before tool-dispatching stages, reject empty input and
    unsupported first-iteration controls, and load existing contracts only at
    the stage that consumes them.
  - Argument grammar: recognize zero or more exact controls
    (`--no-branch`, `--no-brain`, `--no-html`) only in the leading control
    segment. `--` ends that segment and all remaining text is the task verbatim.
    Without `--`, the first non-control token starts the task and every later
    token, including flag-like text, is literal task text. Warn and deduplicate
    repeated supported controls. Reject an unsupported leading `--*` control
    before task text with usage guidance. An empty remainder is a hard stop.
    Tests must cover `document the --no-html option`,
    `-- --force should remain literal`, duplicates, and unsupported controls.
  - Use a preliminary `git status --short` only to make branch-safety decisions.
    After the working branch is selected and before discovery or source edits,
    capture definitive task-local diff ancestry under the ignored
    `.tmp/cg-light-work-run/<UTC-timestamp>/` path: `initial-status.txt`,
    `initial-tracked.diff` from `git diff --binary HEAD` so staged and unstaged
    tracked changes are included, and an `initial-untracked.json` path/SHA-256
    manifest. Record each snapshot SHA-256 in the approved Plan Context and Work
    Report. Qualification, changed-line counts, file boundaries, deterministic
    checks, and Review must compare final state to this snapshot so pre-existing
    changes are not attributed to the light-work run.
  - Exact branch algorithm, after argument parsing and before discovery:
    a non-git workspace or repository without a resolvable `HEAD` stops with a
    standard-workflow/setup handoff because task-local diff and Review evidence
    cannot be established; `--no-branch` skips branch mutation but not the
    definitive initial snapshot; detached HEAD stops unless the user reattaches or
    explicitly reruns with `--no-branch`.
    Determine the default branch with
    `git symbolic-ref refs/remotes/origin/HEAD --short`, strip `origin/`, then
    fall back to existing `main`, then existing `master`. Derive
    `type/short-description`; replace spaces with `-`, remove characters in
    `~^:?*[\`, replace `..` with `-`, strip `@{`, collapse repeated `-`, trim
    separators, and limit the full name to 60 characters. Ask for a name if the
    result is empty.
  - On a clean default branch, auto-create and switch to the derived branch. On
    a dirty default branch, show the initial changed paths and ask `stash`,
    `branch anyway`, or `stop`. On an existing feature branch, retain it; if it
    is dirty, warn with the preliminary paths and defer overlap evaluation until
    bounded discovery identifies predicted task files. If the derived name
    already exists, ask whether to switch. Any other create/switch/stash failure
    is reported verbatim and blocks source edits. Branch-safety prompts do not
    consume a discovery round.
  - Run Stage 0 facts and one bounded Brain query once. Do not invoke the full
    Brain steps of each composed lifecycle prompt.
  - After bounded discovery and before Plan preview or source edits, compare
    predicted task files with the definitive snapshot. No overlap continues.
    A tracked-file overlap can use the captured full binary diff and requires an
    explicit `continue here`, `standard workflow`, or `stop` decision recorded
    in the Plan. Any pre-existing untracked-file overlap must stop and route to
    the standard workflow because the path/hash manifest cannot reconstruct a
    task-local content diff; lightweight approval cannot override it.
  - Evaluate H1-H7 before S1-S10. Unknown risk fails closed. A hard or structural
    failure stops with the exact specific route and copy-ready prompt. Only
    S3-S5, S7, and S8 estimates can reach the explicit size-override gate.
  - Store failed gates and override approval in the Plan and Work Report. Never
    store `scope: Lightweight` when honest scope is Standard.
  - Enforce the exact Plan approval gate and successful canonical Markdown
    validation before source edits. A normal run creates no Brainstorm.
  - Reuse `/cg-work` mechanics through the shared goal-execution and active-state
    contracts rather than copying all `/cg-work` prose. Preserve the stricter
    lightweight limits and stop if actual work crosses them.
  - Add narrow applicability wording to the goal-execution, active-state, and
    review-routing contracts so `/cg-light-work` can produce the same Plan,
    Work Report, active-state, and light Review records. Do not change schemas,
    state values, routes, precedence, or agent sets.
  - Review is mandatory after final implementation evidence. Resolve `light`
    through `review-routing.contract.md`, run deterministic checks first, then
    dispatch the two agents once each for the initial pass. Validate each output
    for presence (a finding or explicit no-issues statement), changed-file
    context, and at least two non-header lines. Empty, garbled, off-topic, or
    otherwise unusable output is recorded under `Incomplete Reviews` as
    `not run`; it blocks clean completion and redirects to `/cg-review light` in
    a new session without automatic retry, model switch, or inferred success.
  - Normalize stable finding IDs and save one standard Review Report whose
    frontmatter statuses are `open`, `fixed`, or `skipped`; finding bodies
    retain `safe_auto`, `manual`, or `advisory` tags. Apply safe fixes and rerun
    affected deterministic evidence. If any Review-driven edit occurred, run
    one verification pass, dispatching each light agent at most once more.
    Reappearing issues retain IDs, resolved IDs become `fixed`, and new findings
    receive the next ID within priority. Non-convergence means unusable output,
    any open P0/P1, an unexcepted P2, or a new in-scope fix that would require a
    third pass.
  - When the user explicitly accepts an unfixed P2 exception, set that finding
    to `skipped` in Review Report frontmatter and record the rationale and
    approval in both the finding body and Work Report. Reserve `open` for work
    that is still unresolved.
  - A post-Review edit invalidates affected evidence. Rerun those checks. The
    initial and verification passes are the two-pass maximum; each agent can be
    dispatched at most twice total.
  - Apply completion writes in the specified order only after final executed
    evidence and finding gates pass. Roadmap writes use `@cg-roadmap` only.
  - Run the compounding gate last. Show candidate learning and every proposed
    side effect before consent. Skip means no permanent knowledge mutation.
  - Omit `model:` frontmatter. Include the ordinary runtime model-context note
    and capability-only handoff guidance without selecting or switching models.
- **Test Scenarios**:
  - Happy path: a one-file low-risk task qualifies, needs no questions, saves
    artifacts in order, passes Review, and offers compounding.
  - Edge cases: exactly-at-limit estimates qualify; one-over-limit estimates
    require override; structural gate failure cannot be overridden; empty task,
    third discovery round, unsafe Review fix, stale evidence, and report-write
    failure stop.
  - Error paths: bug and research requests route to `/cg-fixbug` and
    `/cr-brainstorm`; unsafe or non-convergent work routes to the standard cycle;
    skipped compounding causes no Solution, Brain, context, wiki, or Team Brain
    write.
- **Tests**: Re-run the two targeted safe-runner files from Step 1.
- **Acceptance criteria**: All Step 1 tests pass. The prompt is a thin router
  whose unique policy remains at or below 5,000 measured tokens, existing
  lifecycle contracts explicitly permit the new producer without schema
  changes, and no prompt assigns a model.

### 3. Make `/cg-work` plan-only without changing saved-Plan execution

- **Requirements**: R14, R15, R18, R19, R20
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  - Preserve Plan search and keyword-title selection for approved saved Plans.
    Preserve phase parsing, artifact preflight, Work Report, active state,
    evidence, roadmap, Review mode, and resume behavior.
  - Remove inline scope classification, inline Plan creation, its confirmation,
    and the obsolete skip instructions.
  - Distinguish recognized `/cg-work` controls from free-text task payload. If
    no valid Plan is selected and free text remains, stop without mutation and
    print `/cg-light-work -- <verbatim user task>`. The mandatory `--` protects
    leading supported or unsupported flag-like task text from the new command's
    control parser. Insert the user's task verbatim only as inert quoted command
    data; do not execute it or add inferred facts. If there is no task payload,
    route to `/cg-plan` rather than inventing a `/cg-light-work` task.
  - Ensure the small-task recommendation does not bypass keyword matching for a
    relevant approved Plan and does not imply that large or ambiguous work can
    use the lightweight override.
- **Test Scenarios**:
  - Happy path: an approved matching Plan continues through normal `/cg-work`.
  - Edge cases: inline text with flags is preserved in a copy-ready command;
    leading `--no-html` and `--force` payloads follow the `--` delimiter; empty
    input with no Plan points to `/cg-plan`; a keyword-matched Plan still
    requires user selection before execution.
  - Error path: the redirect does not create a Plan, edit source, dispatch
    `/cg-light-work`, or continue into Work state.
- **Tests**: Use the canonical execution-subagent runner for
  `. tests\Run-Tests.ps1 -File prompt-tools`.
- **Acceptance criteria**: The exact delimited redirect is present, all inline-Plan text
  and obsolete tests are absent, and all saved-Plan execution tests still pass.

### 4. Close the canonical phase with independent evidence

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R18, R19, R20
- **Files**:
  - Product files: no new files beyond Steps 1-3.
  - Workflow state: this Plan's permitted phase frontmatter, its linked
    Work Report selected by the Plan's authoritative `execution-report` field
    or the goal-execution collision rules, `.cg-docs/active-state/current.json`,
    and `roadmap.json` only through an approved `@cg-roadmap` status/link
    mutation. Record the resolved Work Report path in the phase handoff.
- **Details**:
  - Run both targeted Pester files once after all Phase 1 edits through the
    execution-subagent safe runner; do not run Pester directly.
    Capture each result immediately in the Work Report as an immutable run event
    with timestamp, git SHA, filter, pass/fail counts, and failure summary;
    `tests/last-run.json` is only the mutable transport artifact. Use the exact
    separate non-Pester field read from Step 1 after each run.
  - Run the module ownership/dependency/cross-suite validator, `git diff --check`,
    and inspect product paths against the Phase 1 boundary. Inventory workflow
    state separately so required Plan, Work Report, active-state, and roadmap
    writes are not classified as product-scope violations.
  - Before phase completion, verify the before-audit file still exists and its
    SHA-256 matches the Work Report. Record the exact canonical prompt,
    lifecycle contracts, `/cg-work` redirect, resolved Work Report path,
    baseline path, and baseline hash as handoff artifacts for Phase 2. The
    target command's future task-local snapshots are behavior implemented in
    Step 2; they are not prerequisites for this Plan's own Phase 2.
  - Accept the automatic `/cg-work` full-suite phase-boundary gate. Do not add a
    second full-suite run inside this step. Capture that run as an immutable
    Work Report event before `tests/last-run.json` can be overwritten.
  - Do not generate adapters or update user documentation in this phase. Their
    absence is expected and must be stated in the Work Report, not misreported
    as parity success.
- **Test Scenarios**:
  - Happy path: targeted tests and diff check pass with only Phase 1 files.
  - Edge case: generated trees are stale but Phase 1 remains resumable because
    the Work Report names generation as Phase 2 work.
  - Error path: any failed targeted test blocks the phase boundary.
- **Tests**: Targeted safe-runner results, module validator, automatic full-suite
  phase-boundary result, and `git diff --check`.
- **Acceptance criteria**: Phase 1 evidence rows pass, no unsupported file was
  modified, required workflow-state writes are accounted for separately, and
  Phase 2 can resume from explicit canonical sources plus a verified baseline.

## Phase 2: Audit, Documentation, Generation, and Release Gates

**Phase 2 entry gate**: Before any Phase 2 edit, read the Phase 1 handoff and
require `.tmp/cg-light-work-audit/before/cost/context-audit.json` to exist and
match its SHA-256 recorded in the Work Report. Also resolve the Work Report
through the Plan's authoritative `execution-report` pointer or goal-execution
collision rules. A missing or mismatched baseline blocks all Steps 5-8 because
pre-change evidence cannot be recreated honestly.

### 5. Register and test the high-frequency workflow audit

- **Requirements**: R18, R19, R20
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
- **Details**:
  - Add `/cg-light-work` and its canonical path to `WORKFLOW_REGISTRY`. Let the
    existing derived benchmark and high-frequency sets consume that row; do not
    create a second parallel registry.
  - Add the new path to `ORDINARY_CONTEXT_GUARDRAIL_PROMPTS` so an unqualified
    broad read receives the same failure policy as peer ordinary workflows.
  - Add tests that the row is unique, appears in workflow telemetry and token
    artifacts, receives high-frequency warning/failure thresholds, keeps model
    picker behavior advisory, reports the two-agent Review burden accurately,
    treats its staged context wording as justified, and fails broad default
    context reads.
  - Do not weaken existing `/cg-work` review-route or context-loading guardrails.
    If audit parsing needs a narrow update for the new fixed light Review, cover
    the new branch explicitly rather than broadening all prompt exceptions.
- **Test Scenarios**:
  - Happy path: the new workflow gets a complete benchmark row.
  - Edge case: a duplicate ID/path or missing prompt is reported deterministically.
  - Error path: `<=5000` estimated tokens passes, `5001-6000` warns, and `>6000`
    fails; forbidden model metadata or broad context loading remains a failure.
- **Tests**: `python -m pytest scripts/tests/test_audit_context.py -q`.
- **Acceptance criteria**: Python tests pass and no new workflow registry,
  model-governance, context-loading, or Review-burden regression is hidden.

### 6. Update user workflow guidance and regenerate command reference

- **Requirements**: R2, R3, R4, R5, R6, R13, R14, R15, R16, R20
- **Files**:
  - `.github/copilot-instructions.md`
  - `tests/prompt-tools.Tests.ps1`
  - `docs/workflow.md`
  - `docs/workflows/index.md`
  - `docs/workflows/design.md`
  - `docs/workflows/deliver.md`
  - `docs/getting-started/index.md`
  - `docs/reference/commands.md`
  - `docs/reference.md` (targeted manual prose plus generated marker interior)
- **Details**:
  - Add `/cg-light-work` to the technical entry-point guidance and explain the
    route boundary: qualified small technical work only; reproducible bugs use
    `/cg-fixbug`; research/statistical/publication work uses `/cr-*`; larger,
    ambiguous, security, schema, dependency, or destructive work uses the
    standard Brainstorm -> Plan -> Work cycle.
  - Remove statements that `/cg-work` creates inline Plans. State that it
    executes approved saved Plans and redirects unmatched inline tasks.
    In `docs/reference.md`, manually update only stale prose outside managed
    markers; keep command-table rows generator-owned. Add a focused assertion
    that the old `/cg-work` scope-classification and inline-Plan statement is
    absent.
  - Document the two user gates, durable artifacts, mandatory fixed light Review,
    Review/fix cap, and explicit compounding opt-in without reproducing every
    H/S gate from the command.
  - Add `/cg-light-work` to the focused Commands table. Keep `/cg-work` plan-only
    there and include the `/cg-fixbug` and `/cr-*` boundaries.
  - Run `node scripts/rebuild-docs.js` to regenerate the command table from
    canonical prompt descriptions. Never hand-edit marker-owned rows.
  - Run `node scripts/rebuild-docs.js --check` and the docs automation tests.
- **Test Scenarios**:
  - Happy path: all navigation pages give one consistent route.
  - Edge case: generated `docs/reference.md` includes `/cg-light-work` once and
    changes only the identified stale manual paragraph outside markers. All
    unrelated manual prose outside markers remains byte-for-byte; the focused
    Commands page lists the route once.
  - Error path: stale inline-Plan claims or a stale marker-owned table fail
    focused content checks or the docs rebuild check.
- **Tests**: `npm run test:docs-automation`, `node scripts/rebuild-docs.js --check`,
  and the canonical safe runner for `prompt-tools`.
- **Acceptance criteria**: Documentation is current, concise, route-consistent,
  and free of inline-Plan claims; generated sections are current.

### 7. Generate native adapters and verify modular parity

- **Requirements**: R15, R17, R18, R19, R20
- **Files**:
  - `scripts/tests/test_context_budget.py`
  - `scripts/tests/test_cg_generate_targets.py`
  - `.agents/commands/cg-light-work.md` (generated)
  - `.claude/commands/cg-light-work.md` (generated)
  - `.opencode/commands/cg-light-work.md` (generated)
  - `.kilo/commands/cg-light-work.md` (generated)
  - Generated `cg-work.md` command copies in all four adapter trees
  - Generated updated goal-execution, active-state, and review-routing contract
    copies in all four adapter shared trees
  - `.agents/.compound-gpid-generated.json` (generated)
  - `.claude/.compound-gpid-generated.json` (generated)
  - `.opencode/.compound-gpid-generated.json` (generated)
  - `.kilo/.compound-gpid-generated.json` (generated)
- **Details**:
  - Recheck module ownership before generation. The prompt must resolve to
    `suite-cg`; existing lifecycle contracts remain kernel-owned; no ambiguous
    or unowned canonical asset is allowed.
  - Run `python scripts/cg_validate_modules.py --check-ownership --check-dependencies --check-cross-suite`.
  - Run `python scripts/cg_generate_targets.py --root . --all`. Do not manually
    edit adapter files or manifests.
  - Verify target-specific argument placeholders and rewritten contract paths
    while preserving one normalized command body across platforms.
  - Verify active-suite filtering with existing generator/context-budget tests;
    add exact assertions that CG-only projections include the new command,
    CR-only projections exclude it, and all four command-tree destinations plus
    manifest provenance are correct. Do not run a filtered destructive
    generation over the full checked-out tree.
- **Test Scenarios**:
  - Happy path: each platform has one command, the updated `/cg-work`, updated
    existing lifecycle contracts, and manifest provenance to canonical
    `.github/` paths.
  - Edge case: CG-only filtering includes the command; CR-only filtering excludes
    it without an inactive-reference leak.
  - Error path: ownership conflict, stale generated output, path rewrite error,
    or manifest mismatch blocks completion.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_context_budget.py scripts/tests/test_target_drift.py -q`.
- **Acceptance criteria**: Module validation and generation succeed, targeted
  Python tests pass, and generated diffs contain no manual divergence.

### 8. Run final evidence, compare token audits, and prepare handoff

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20
- **Files**: Verification only; audit outputs remain in an isolated temporary
  directory unless a separate approved task requests committed audit artifacts.
- **Details**:
  - Confirm that the Phase 2 entry gate remained valid; do not defer its first
    evaluation to this step.
  - Run the post-change audit exactly as:
    `python scripts/cg_audit_context.py --root . --output-dir .tmp/cg-light-work-audit/after/cost --token-output-dir .tmp/cg-light-work-audit/after/token --format both --recommendations --baseline .tmp/cg-light-work-audit/before/cost/context-audit.json`.
    Record the after report path and SHA-256 in the Work Report.
  - Require: no new guardrail failures; `/cg-light-work` at or below the
    5,000-token high-frequency pass boundary; `/cg-work` source prompt tokens lower than
    the comparable before row; no forbidden model metadata; and no claim about
    actual runtime tokens, credits, or total cost that the static audit cannot
    observe.
  - Run the targeted Python, Node, and Pester checks from prior steps. Do not add
    a separate full run: the executor's automatic final Phase 2 boundary runs
    the canonical full Pester suite once. Read `tests/last-run.json` immediately;
    `filteredFiles` must be null, then copy its timestamp, git SHA, result fields,
    and failure summary into the Work Report as the immutable final event. After
    that automatic boundary, `/cg-work` must evaluate V8 and all final rows before
    its Step 3.5 Plan-completion write.
  - Run `git diff --check`, inspect all changed/untracked paths against this Plan,
    and confirm generated views were not loaded into model context.
  - Verify the Plan remains linked to the exact brainstorm and that roadmap
    linkage created during planning still points to this Plan. Do not require
    the final `done` transition here; `/cg-work` Step 3.7 owns it after the final
    evidence gate.
- **Test Scenarios**:
  - Happy path: all targeted and full gates pass; audit comparison is valid.
  - Edge case: static audit reports an existing unrelated warning; record it
    separately and require zero newly introduced failures or unreviewed `fix`
    warnings in changed scope.
  - Error path: partial Pester run, missing baseline, token threshold breach,
    generated drift, docs drift, or whitespace errors block completion.
- **Tests**:
  - `python -m pytest scripts/tests/test_audit_context.py scripts/tests/test_cg_generate_targets.py scripts/tests/test_context_budget.py scripts/tests/test_target_drift.py -q`
  - `npm run test:docs-automation`
  - `node scripts/rebuild-docs.js --check`
  - Automatic final phase-boundary execution-subagent full runner, followed by
    bounded `tests/last-run.json` fields including `filteredFiles`
  - Post-change `cg_audit_context.py` run with the Step 1 baseline
  - `git diff --check`
- **Acceptance criteria**: Before the phase boundary, V4-V7, V9, and V10 pass,
  generated targets and docs are current, and inputs for V8 are ready. The
  automatic Phase 2 boundary then supplies V8; `/cg-work` rechecks all final
  rows and constraints before marking the Plan complete or preparing commit/PR
  handoff.

## Testing Strategy

- Follow red-green discipline for deterministic prompt obligations: add or
  replace focused contract assertions before changing canonical prompt text.
- Use independent assertions for each H/S gate and each consequential boundary.
  Do not use broad regex alternation or sibling text that can make a stale arm
  pass.
- Treat Pester as a safe-runner-only system. All Pester execution goes through an
  execution subagent using `tests/Run-Tests.ps1`; never invoke Pester directly or
  inject verbose output into the main session.
- Use Python tests for audit registry, high-frequency thresholds, generated
  targets, module filtering, and drift. Use Node tests for marker-owned docs.
- Keep deterministic contract fixtures distinct from manual model-behavior
  scenarios. The former are required automated evidence; the latter remain
  representative acceptance cases and must not be reported as executed unless
  actually run on a supported platform.
- Run targeted checks after each concern. Accept one automatic full Pester gate
  at each `/cg-work` phase boundary, with no duplicate full run inside a phase.
  Each result becomes an immutable Work Report run event; only the final gate
  may use the current mutable `tests/last-run.json` as transport evidence.

## Documentation Checklist

- [ ] Add `/cg-light-work` to technical workflow entry points.
- [ ] Explain qualification and the two interaction gates without duplicating
      the full command contract across documentation pages.
- [ ] Route reproducible bugs to `/cg-fixbug` and research/statistical work to
      `/cr-*` consistently.
- [ ] Remove every user-facing claim that `/cg-work` creates inline Plans.
- [ ] Explain that `/cg-work` executes approved saved Plans and redirects inline
      tasks without dispatching another command.
- [ ] Document Plan, Work Report, Review Report, and optional Solution outputs.
- [ ] Update `docs/reference/commands.md` with the small-task, Plan-only Work,
      bug, and research routes.
- [ ] Regenerate `docs/reference.md` from prompt frontmatter and validate marker
      ownership.
- [ ] Do not update the charter body; the feature aligns with its existing
      technical workflow, token-efficiency, evidence, and knowledge goals.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| The compact prompt omits a required unique rule | Unsafe work can enter the lightweight path or behavior can differ by platform | Independent contract assertions, existing shared-contract references, and target-drift tests |
| The inline command grows above its high-frequency budget | Routine small work becomes context-heavy or fails the audit gate | Reuse existing lifecycle contracts, keep only unique policy inline, and block above 5,000 measured tokens |
| `/cg-work` redirect logic captures a valid saved-Plan request | Existing planned work becomes unusable or the wrong command is suggested | Preserve and test saved-Plan search/selection before the unmatched inline-task redirect |
| H/S gate overlap or unknown risk is treated as an overridable size estimate | Security, research, schema, bug, or architecture work can bypass the standard cycle | Evaluate H1-H7 first, make H/S structural gates non-overridable, and test each gate independently |
| Static prompt tests are mistaken for end-to-end agent compliance | The feature can be declared proven without runtime behavior evidence | Label tests as contract evidence, retain representative scenarios, and never report unexecuted model behavior as passed |
| Review fixes leave earlier evidence stale or Review Report statuses inconsistent | Completion can be recorded against obsolete checks or unresolved findings | Invalidate affected evidence after edits, rerun it, update frontmatter statuses, and cap Review/fix iterations at two |
| One Review agent returns empty, garbled, or off-topic output | Mandatory Review can be reported complete without an actual second opinion | Apply presence/context/volume checks, record `Incomplete Reviews`, block completion, and redirect without automatic retry |
| Compounding runs before convergence or after a skip | Unverified or unwanted knowledge enters Solutions, Brain, context, wiki, or Team Brain | Put the consent gate last and assert no side effects for skip/no-learning paths |
| Adapter or docs generation is edited manually or becomes stale | Platforms expose different commands or documentation disagrees with behavior | Generate from canonical sources only; use module, drift, manifest, and docs marker checks |
| Static prompt-source measurements are presented as actual runtime cost | A misleading token-savings claim is made | Compare the same static audit before/after, report prompt-source and reference evidence only, and avoid runtime-cost claims |
| Pester is run directly, duplicated within a phase, or cited through overwritten state | VS Code can freeze and historical evidence can be lost | Use execution-subagent safe runners, one automatic full gate per phase, and immutable Work Report run events |

## Initial Plan Review Resolution

| Finding | Resolution in this Plan |
|---------|-------------------------|
| P1.1 | Step 4 and V3 now separate product files from required Plan, Work Report, active-state, and roadmap workflow-state writes. |
| P1.2 | Step 2 defines one initial light Review and one conditional verification pass, stable ID handling, and exact non-convergence rules. |
| P1.3 | Step 2 adds presence, context, and volume checks; unusable output is `not run`, blocks completion, and redirects without automatic retry. |
| P2.1 | Unique policy now remains inline in its only caller; only narrow applicability updates are made to existing lifecycle contracts. |
| P2.2 | Step 2 now defines non-git, detached HEAD, default branch, feature branch, all dirty states, name conflict, failure, `--no-branch`, and task-local snapshots. |
| P2.3 | Step 2 now defines a leading-control grammar, `--` delimiter, duplicate handling, literal post-task flags, and empty/unsupported handling. |
| P2.4 | Steps 1 and 4 plus the Phase 2 entry gate and Step 8 use exact ignored before/after paths, mandatory output options, Work Report hashes, and a resume preflight. |
| P2.5 | Step 5 adds the ordinary-workflow guardrail and uses the implemented `<=5000`, `5001-6000`, and `>6000` boundaries consistently. |
| P2.6 | Steps 4 and 8 plus Testing Strategy accept one automatic full Pester gate per phase and remove the duplicate final run. |
| P2.7 | V1/V2 and Step 4 use immutable Work Report run events; only final V8 reads the current mutable `tests/last-run.json`. |
| P2.8 | Step 6 and the Documentation Checklist now include `docs/reference/commands.md` and focused route assertions. |

## Verification Plan Review Resolution

| Finding | Resolution in this Plan |
|---------|-------------------------|
| P1.1 | A Phase 2 entry gate now verifies baseline and initial-diff hashes before any Step 5-8 edit. |
| P1.2 | Step 6 permits targeted manual `docs/reference.md` prose edits while retaining generator ownership of marker interiors. |
| P1.3 | Step 8 accepts only pre-boundary evidence; V8 and final rows are checked after the automatic phase boundary and before completion. |
| P2.1 | The one-caller support abstraction was removed; unique lightweight policy stays in the compact prompt and must pass the measured budget. |
| P2.2 | Step 2 records initial status, tracked diff, and untracked hashes; it defines dirty handling for every branch type and exact default/name rules. |
| P2.3 | Step 3 now always emits `/cg-light-work -- <verbatim task>` and tests leading supported and unsupported flag-like payloads. |
| P2.4 | Step 4 resolves the Work Report through `execution-report` or collision rules and records the actual path in the handoff. |
| P2.5 | Steps 1 and 4 define an exact separate non-Pester read for all immutable run-event fields. |
| P2.6 | Step 7 now owns changes to `test_context_budget.py` and `test_cg_generate_targets.py` and requires exact destination/projection assertions. |
| P2.7 | Step 2 maps an accepted unfixed P2 to `skipped` and records its rationale and approval in the report body and Work Report. |
| P3.1 | Step 8 now ends in completed-state and commit/PR handoff readiness, not a Phase 1 restart suggestion. |

## Final Convergence Review Resolution

| Finding | Resolution in this Plan |
|---------|-------------------------|
| P1.1 | Step 4 and the Phase 2 entry gate now require only this implementation run's audit baseline; future command snapshots are not handoff prerequisites. |
| P1.2 | Roadmap linkage is an explicit planning-session handoff precondition; Step 8 checks the link while `/cg-work` Step 3.7 retains final status ownership. |
| P1.3 | Dirty-path overlap is evaluated after discovery; tracked overlap needs an explicit decision, and untracked overlap cannot continue in the light path. |
| P2.1 | Step 6 permits only the identified stale manual paragraph to change and preserves all unrelated out-of-marker prose byte-for-byte. |

## Out of Scope

- A broad writable lifecycle sub-agent or any new agent.
- `/cg-autopilot`, hooks, unattended command chaining, or automatic command
  dispatch across sessions.
- New review modes, changes to review agent membership, or changes to the
  review-routing precedence taxonomy.
- New Plan, Work Report, Review Report, Solution, active-state, or roadmap
  schemas.
- Reproducible bug execution, research/statistical work, security-sensitive
  work, schema or dependency changes, releases, publishing, deployment,
  install/update/link/unlink, or destructive operations in the light path.
- New runtime or development dependencies.
- Model or reasoning-effort assignments in prompt/agent metadata.
- Committing, pushing, opening a pull request, or publishing a release.
- Implementing deferred `brainstorm-depth-grill-mode` or
  `brainstorm-plan-id-traceability` roadmap ideas.

## Completion Contract

### Outcome

`/cg-light-work <task>` is available from canonical and generated platform
command surfaces as a fail-closed, two-gate workflow for qualifying small
technical tasks, with standard Plan, Work Report, and light Review Report
traceability. `/cg-work` executes approved saved Plans only and returns the exact
copy-ready redirect for unmatched inline tasks.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Qualification, discovery, approval, execution, Review, resolution, compounding, and `/cg-work` redirect obligations pass independent contract tests | Immutable `prompt-tools` run event in the Work Report, captured from the safe-runner result | yes |
| V2 | 1 | The canonical prompt count is 33, the new prompt has no model assignment, and no agent count changed | Immutable `model-assignments` run event in the Work Report, captured from the safe-runner result | yes |
| V3 | 1 | Phase 1 product changes stay within the approved prompt, lifecycle-contract, and test files; required workflow-state writes are inventoried separately; no whitespace errors exist | `git diff --check`; product and workflow-state path inventories in Work Report | yes |
| V4 | 2 | `/cg-light-work` is a unique measured high-frequency workflow with covered token, context, model, and Review-burden guardrails | `python -m pytest scripts/tests/test_audit_context.py -q`; post-change audit | yes |
| V5 | 2 | Workflow guidance and marker-owned command documentation are current and route-consistent | `npm run test:docs-automation`; `node scripts/rebuild-docs.js --check`; focused prompt tests | yes |
| V6 | 2 | Claude Code, Codex, OpenCode, and Kilo command/contract outputs and manifests match canonical sources with valid ownership and suite filtering | Module validator; generator; targeted generation/context/drift pytest files | yes |
| V7 | final | Comparable audit shows no new failures, `/cg-light-work` at or below 5,000 prompt tokens, `/cg-work` prompt tokens lower than before, and no forbidden model metadata | Before/after `cg_audit_context.py` artifacts in isolated temporary directories | yes |
| V8 | final | The complete repository Pester gate passes after final edits and is not a filtered run | Execution-subagent `. tests\Run-Tests.ps1`; `tests/last-run.json` with `passed: true`, `failedCount: 0`, `filteredFiles: null` | yes |
| V9 | final | All planned Python and Node checks pass and final changed paths have no whitespace errors | Commands from Step 8; `git diff --check` | yes |
| V10 | final | Before work starts, the Plan is linked to the matching roadmap feature through the roadmap manager; the link remains valid and no P1/P2 Plan Review finding remains | Targeted roadmap feature read; final Plan Review summary | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | No broad lifecycle sub-agent, hook, dependency, schema, review mode, or model assignment is added. | Canonical file/dependency diff and focused tests |
| C2 | 1 | Existing `/cg-work` Plan selection, phases, evidence, reports, active state, resume, roadmap, and review controls remain intact. | Focused `/cg-work` regression assertions |
| C3 | 1 | H1-H7 and S1/S2/S6/S9/S10 cannot be overridden; unknown risk fails closed. | Independent gate assertions |
| C4 | 1 | No source edit occurs before approved Plan persistence and canonical Markdown validation. | Prompt ordering assertions |
| C5 | 2 | `.github/` is canonical; adapter files and marker-owned docs are generated, not hand-edited. | Manifest provenance, target drift, and docs marker checks |
| C6 | 2 | The suite-owned `/cg-light-work` prompt is absent from CR-only projects and creates no inactive-reference leak. | Context-budget and target-generation suite-filter tests |
| C7 | final | No token or cost saving is claimed beyond comparable static audit evidence. | Before/after audit and Work Report wording review |
| C8 | final | No phase, Plan, report, or roadmap completion is based on static inspection alone. | Required executed evidence and Work Report statuses |
| C9 | final | Existing uncommitted brainstorm and roadmap work is preserved; unrelated changes are not reverted or rewritten. | Final path and diff review |

### Boundaries

- Allowed: the canonical compact `/cg-light-work` prompt and narrow updates to
  existing lifecycle contracts;
  `/cg-work` redirect; focused prompt/model/audit tests; workflow documentation;
  deterministic generated docs and adapters; token-audit registration; and
  roadmap linkage through `@cg-roadmap`.
- Out of scope: new agents, hooks, dependencies, schemas, review modes, model
  assignments, high-risk or research execution, autopilot behavior, commits,
  pushes, pull requests, and release work.

### Iteration Policy

1. Implement only the current phase; Phase 2 starts after Phase 1 required
   evidence passes and its handoff artifacts are recorded.
2. Add deterministic contract tests before changing prompt behavior.
3. Use `deviation-policy: ask`; record the decision and impact before any
   deviation from files, behavior, or evidence in this Plan.
4. Use at most two focused correction attempts for a failed implementation or
   verification concern. Do not weaken tests or acceptance criteria to pass.
5. After any Review-driven edit, rerun every affected syntax, lint, test,
   generation, docs, token, and diff check before using the evidence.
6. Keep Review/fix convergence to two iterations. If it does not converge,
   stop and hand off to the standard `/cg-review` and `/cg-fix-triage` cycle.

### Blocked-Stop Conditions

- The Plan cannot pass renderer-independent canonical Markdown validation.
- Required verification cannot run through the safe runner, or a required row
  fails after the permitted focused recovery attempts.
- A change requires a file, behavior, dependency, schema, review mode, model
  assignment, or protected boundary outside this Plan and approval is absent.
- Module ownership, suite filtering, generated parity, or docs marker ownership
  is ambiguous or invalid.
- The before audit is missing or not comparable, preventing the required R19
  before/after claim.
- `/cg-light-work` exceeds the 5,000-token high-frequency pass boundary or
  introduces a new audit guardrail failure that is not resolved.
- The full Pester result is partial (`filteredFiles` is non-null), failed, or
  cannot be read from `tests/last-run.json`.
- A required Plan deviation is discovered under `ask` and approval is
  unavailable, or implementation would require static-inspection-only evidence.
- `/cg-work` cannot durably create or update its Work Report, Review Report,
  Plan state, or required active-state record.
- A P0/P1 finding remains open, a P2 remains without an explicit recorded
  exception, or Review/fix does not converge in two iterations.
