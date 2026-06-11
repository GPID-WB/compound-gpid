---
date: 2026-06-07
title: "Token Optimization Phase 5 - Knowledge Brain and Context Selectivity"
status: completed
scope: "Standard"
language: "Python/Markdown"
estimated-effort: "medium"
tags: [token-cost, knowledge-brain, context-loading, audit, prompts]
phases: 3
---

# Plan: Token Optimization Phase 5 - Knowledge Brain and Context Selectivity

## Objective

Reduce runtime token cost from large generated memory and context artifacts by making Knowledge Brain and project context loading selective, staged, and query-driven. Ordinary prompts should no longer encourage broad/default reads of full Brain artifacts, `compound-gpid.context.md`, or `roadmap.json` unless the workflow has an explicit, justified need.

## Context

Phase 1 created `.cg-docs/cost/context-audit.md` and `.cg-docs/cost/context-audit.json`. Phase 2 removed hard-coded premium Opus defaults from ordinary prompts and validated model-picker behavior. Phase 3 reduced `/cg-review` cost through staged/conditional routing. Phase 4 slimmed `/cg-plan` and `/cg-work`, added model-context behavior, and stabilized review/workflow contracts.

The latest audit, generated 2026-06-07T17:17:42, identifies the largest context files:

| Path | Estimated tokens |
|------|------------------|
| `.cg-docs/brain-index.json` | 133645 |
| `.cg-docs/BRAIN-log.md` | 31654 |
| `.cg-docs/BRAIN-01.md` | 28361 |
| `compound-gpid.context.md` | 14108 |
| `roadmap.json` | 13196 |

Existing prompt and skill hotspots found during planning:

- `.github/prompts/cg-plan.prompt.md`: Step 0 currently says to read `compound-gpid.context.md` if it exists.
- `.github/prompts/cg-work.prompt.md`: Step 0 reads `compound-gpid.context.md`; Step 1.5 and later steps read `roadmap.json` for status updates.
- `.github/prompts/cg-review.prompt.md`: Step 0 reads `compound-gpid.context.md`; Step 1.3 consults Brain before review dispatch.
- `.github/prompts/cg-compound.prompt.md`: Step 0 reads `compound-gpid.context.md`; Step 3b intentionally rebuilds full Brain artifacts; Step 5 re-reads context for enrichment.
- `.github/prompts/cg-resume.prompt.md`: Step 0c reads full `compound-gpid.context.md`; Step 2d reads full `roadmap.json`; Step 2 scans `.cg-docs` metadata.
- `.github/prompts/cg-brainstorm.prompt.md`: Step 0 reads full `compound-gpid.context.md`; Step 0.7 consults Brain.
- `.github/prompts/cg-brain-rebuild.prompt.md`: Step 0 reads full `compound-gpid.context.md`, but its full Brain rebuild behavior is intentional.
- `.github/skills/cg-skill-brain-query/SKILL.md`: already says to read only `BRAIN.md` first and not all `BRAIN-NN.md` files, but it also says "Do NOT use `brain-index.json` directly"; Phase 5 should refine this because `brain-index.json` is the retrieval index for tooling, while agents should not read it wholesale.
- `scripts/cg_audit_context.py`: inventories large files and references, but does not yet flag broad context-loading instructions.

Brain findings used in this plan:

- Knowledge Brain Batch C established the desired read path: check `BRAIN.md`, read the topic index, then open only matched `BRAIN-NN.md` topic sections. Source: `.cg-docs/plans/2026-05-20-knowledge-brain-read-path-batch-c.md`.
- Phase 4 explicitly left Knowledge Brain retrieval unchanged and focused on `/cg-plan` and `/cg-work` prompt slimming. Source: `.cg-docs/plans/2026-06-06-cg-plan-work-context-slimming-phase4.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Ordinary prompts must not default to reading full generated Brain artifacts. | user |
| R2 | Prompts must consult Knowledge Brain through a selective query or summary mechanism. | user |
| R3 | `.cg-docs/brain-index.json`, `.cg-docs/BRAIN-log.md`, and `BRAIN-NN.md` files must be treated as retrieval/index artifacts, not default context. | user |
| R4 | `compound-gpid.context.md` and `roadmap.json` must be read only at the granularity needed by the current workflow. | user |
| R5 | Any context expansion must state why before expanding. | user |
| R6 | `/cg-compound` and `/cg-brain-rebuild` must continue to generate and rebuild Brain artifacts. | user |
| R7 | Do not delete, weaken, or stop generating Knowledge Brain artifacts. | user |
| R8 | Add or refine a shared context-loading contract if useful. | user |
| R9 | Add audit support that flags broad context-loading instructions. | user |
| R10 | Preserve Phase 2 model-governance policy; no premium model usage unless explicitly justified. | user |
| R11 | Preserve Phase 3 review routing and Phase 4 workflow contracts. | user |
| R12 | Include pending `/cg-work review:*` runtime validation as a follow-up validation item without redesigning Phase 4. | user |

## Staged Context-Loading Policy

Use this policy as the target contract for ordinary workflow prompts.

| Stage | Name | Allowed default reads | Expansion rule |
|-------|------|-----------------------|----------------|
| 0 | Minimal bearings | `compound-gpid.md`; `compound-gpid.local.md` if needed for language/review flags; command arguments | No large generated or tactical context artifacts. |
| 1 | Targeted metadata | File lists, YAML frontmatter, titles, status fields, or matching snippets from `.cg-docs` artifacts; `roadmap.json` only through targeted fields needed for the workflow | State why the metadata is needed. Do not read whole bodies unless selected. |
| 2 | Query-first knowledge | `cg-skill-brain-query`, `BRAIN.md` meta-index, matched `BRAIN-NN.md` topic sections only | State search directive and matched topic before opening topic files. |
| 3 | Targeted tactical context | Relevant headings/snippets from `compound-gpid.context.md`; roadmap feature/milestone records relevant to the current plan, feature, or status update | State why the specific section or record is needed. Prefer heading search or structured JSON parsing. |
| 4 | Justified full expansion | Full `compound-gpid.context.md`, full `roadmap.json`, full `BRAIN-log.md`, full `BRAIN-NN.md`, or full `brain-index.json` | Only when the workflow explicitly requires whole-file semantics. State the reason and the expected decision the full read supports. |

Full artifact reads are allowed only for these cases:

- Full `BRAIN.md`: allowed because it is the small meta-index entry point. Do not treat `BRAIN.md` as equivalent to all generated Brain files.
- Full `BRAIN-NN.md`: allowed only when the matched topic spans the file and section-level extraction is impractical; state the matched topic and why section extraction is insufficient.
- Full `BRAIN-log.md`: allowed for chronology/staleness audits or Knowledge Brain maintenance, not ordinary planning/review/work.
- Full `brain-index.json`: allowed for Python tooling, tests, and audit scripts; prompt agents must not read it wholesale. Agents may invoke tooling that queries it.
- Full `compound-gpid.context.md`: allowed for `/cg-setup` creation/update flows, `/cg-compound` enrichment, or workflows explicitly auditing/context-curating the whole file. Ordinary prompts should search headings or snippets first.
- Full `roadmap.json`: allowed for roadmap commands, `/cg-resume` milestone health, and `/cg-work` status verification where structured cross-checks require global state. Even there, parse structured fields and avoid carrying unrelated records forward.

## Default Reads By Workflow

| Workflow | Default behavior after Phase 5 |
|----------|--------------------------------|
| `/cg-plan` | Read charter/local config, scan existing plan metadata, read the latest audit or user-named files, query Brain through `cg-skill-brain-query`, and read only relevant source/prompt files. Do not read full `compound-gpid.context.md` by default. |
| `/cg-work` | Read charter/local config, selected plan body, relevant implementation files, targeted Brain findings, and targeted roadmap feature only when updating plan status. Do not read full context by default. |
| `/cg-review` | Read charter/local config, changed-file scope, review routing contract, targeted Brain findings for changed file types, and relevant plan context. Do not read full context by default. |
| `/cg-compound` | Preserve solution capture and Brain rebuild. Read context selectively for wiki folder/config and enrichment checks; full context read is allowed only when enrichment needs whole-file placement or conflict avoidance. |
| `/cg-resume` | Read charter/local config, `.cg-docs` frontmatter summaries, targeted plan bodies only for active phased plans, and structured roadmap fields for health checks. Read context headings/snippets only for session-relevant workspace notes. |
| `/cg-brainstorm` | Read charter/local config, query Brain for prior explorations, scan project structure, and read relevant files mentioned by the request. Do not read full context by default. |
| `/cg-brain-rebuild` | Preserve full rebuild via `cg-index --brain`; it may confirm output files exist but should not read generated Brain artifacts wholesale after rebuild. |

## Phase 1: Shared Policy And Prompt Rules

### 1. Add A Shared Context-Loading Contract

- **Requirements**: R1, R2, R3, R4, R5, R8
- **Files**:
  - `.github/shared/context-loading.contract.md` (new)
  - `.github/prompts/cg-plan.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-compound.prompt.md`
  - `.github/prompts/cg-resume.prompt.md`
  - `.github/prompts/cg-brainstorm.prompt.md`
  - `.github/prompts/cg-brain-rebuild.prompt.md`
- **Details**:
  - Create a compact shared contract containing the staged policy above.
  - Define "ordinary prompts" and "maintenance prompts".
  - Define the exact expansion statement format, for example: `Context expansion: reading <artifact/section> because <reason>.`
  - Keep the contract short enough to be loaded cheaply.
  - In each listed prompt, replace broad `Read compound-gpid.context.md` language with "load `.github/shared/context-loading.contract.md`; apply Stage 0/1/2 first; read context sections only if relevant."
  - For `/cg-plan`, preserve its model-context note from Phase 4.
  - For `/cg-work`, preserve phase handling, review-mode behavior, and review routing contract usage.
  - For `/cg-review`, preserve staged review routing exactly; only change context-loading instructions.
  - For `/cg-compound`, explicitly preserve Step 3b Brain rebuild and Step 5 enrichment while making context reads targeted.
  - For `/cg-brain-rebuild`, keep `cg-index --brain` as the source of full Brain generation; do not add Brain query behavior.
- **Test Scenarios**:
  - Happy path: ordinary prompt instructions load charter/local config and query Brain without reading large artifacts wholesale.
  - Edge case: a workflow needs a full context or roadmap read and must state why.
  - Error path: no `compound-gpid.context.md` or no `BRAIN.md`; prompts skip silently where current behavior already skips.
- **Tests**:
  - Static grep checks from Phase 3 below.
  - Existing prompt structure tests, if present.
- **Acceptance criteria**:
  - No ordinary workflow prompt contains unconditional "read `compound-gpid.context.md`" wording.
  - Prompts explicitly state when full large artifact reads are allowed.
  - `/cg-compound` and `/cg-brain-rebuild` still instruct Brain generation/rebuild.

### 2. Refine Brain Query Skill For Query-First Retrieval

- **Requirements**: R1, R2, R3, R5, R6, R7
- **Files**:
  - `.github/skills/cg-skill-brain-query/SKILL.md`
  - Optional: `docs/workflow.md`
  - Optional: `docs/reference.md`
- **Details**:
  - Clarify that `BRAIN.md` is the small agent-facing meta-index and `brain-index.json` is a tooling retrieval index.
  - Replace "do not use `brain-index.json` directly" with a more precise rule: agents must not read it wholesale; Python tooling may query it or produce targeted summaries.
  - Add the expansion statement requirement before opening a matched `BRAIN-NN.md` file or `BRAIN-log.md`.
  - Keep the existing topic-index workflow: existence check, read `BRAIN.md`, match topics, deduplicate sub-files, extract only relevant entries.
  - Preserve Team Brain behavior; do not refactor Team Brain internals.
- **Test Scenarios**:
  - Happy path: query finds matched topic and opens only the relevant partition.
  - Edge case: no matching topics; no large artifact expansion occurs.
  - Error path: `BRAIN.md` missing; skip silently.
- **Tests**:
  - Static tests for wording and forbidden broad-read instructions.
- **Acceptance criteria**:
  - Skill tells agents to use query-first Brain retrieval.
  - Skill does not ban tooling use of `brain-index.json`.
  - Skill still protects against reading all Brain partitions blindly.

## Phase 2: Workflow-Specific Selectivity

### 3. Make Context And Roadmap Reads Targeted Per Workflow

- **Requirements**: R4, R5, R11, R12
- **Files**:
  - `.github/prompts/cg-plan.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-compound.prompt.md`
  - `.github/prompts/cg-resume.prompt.md`
  - `.github/prompts/cg-brainstorm.prompt.md`
  - `.github/prompts/cg-brain-rebuild.prompt.md`
  - `.github/shared/review-routing.contract.md` (read-only unless a cross-reference is necessary)
- **Details**:
  - `/cg-plan`: replace full context read with targeted context lookup only when the plan topic needs project-specific tactical facts. Existing plan search should continue to read frontmatter/title metadata first and only selected plan bodies.
  - `/cg-work`: read selected plan body thoroughly, but restrict `compound-gpid.context.md` to sections relevant to the plan files or technologies. Roadmap reads should happen only in Step 1.5/3.7/3.8 and only for matching plan/feature status verification.
  - `/cg-review`: route on changed files and the shared review contract first; consult Brain for file-type/domain gotchas; only read context snippets if changed files intersect documented context.
  - `/cg-compound`: keep solution capture, `cg-index --brain`, wiki update, Team Brain push, and context enrichment. Replace default context read with targeted reads for wiki folder configuration and enrichment placement.
  - `/cg-resume`: keep the direct `roadmap.json` read only because it computes global milestone health and drift. Add an explicit justification comment and ensure it does not carry unrelated roadmap records into the summary. Replace full context read with summary/headings or workspace-note snippets.
  - `/cg-brainstorm`: use Brain query and relevant file scans; defer full context expansion unless the brainstorm is about project conventions, data sources, workspace layout, or context maintenance.
  - `/cg-brain-rebuild`: remove the default full context read unless needed for user config; preserve rebuild command and output verification.
  - Do not alter `/cg-work review:*` behavior except for context-loading wording. Record runtime validation as pending.
- **Test Scenarios**:
  - Happy path: `/cg-plan` on a known task consults Brain and relevant prompt/source files without full context read.
  - Edge case: `/cg-resume` still computes milestone health from roadmap.
  - Error path: roadmap missing; workflows skip roadmap steps as before.
- **Tests**:
  - Static checks for prompt text.
  - Existing prompt-tool tests if they cover prompt required sections.
- **Acceptance criteria**:
  - Each workflow has explicit allowed default reads.
  - Each workflow describes when it may expand to full context or roadmap.
  - Phase 4 review/workflow contracts are preserved.

## Phase 3: Audit, Tests, And Validation

### 4. Add Broad Context-Loading Audit Signals

- **Requirements**: R1, R3, R4, R5, R9, R10
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - `.cg-docs/cost/context-audit.json` (generated after implementation)
  - `.cg-docs/cost/context-audit.md` (generated after implementation)
- **Details**:
  - Add a new audit section, for example `Context Loading Risks`.
  - Flag prompt/agent/skill files that contain broad read instructions for:
    - `.cg-docs`
    - `BRAIN.md`
    - `BRAIN-log.md`
    - `BRAIN-NN.md`
    - `brain-index.json`
    - `compound-gpid.context.md`
    - `roadmap.json`
  - Distinguish allowed/justified patterns from risky patterns:
    - Allowed examples: `read YAML frontmatter`, `scan titles`, `matched topic`, `targeted section`, `structured fields`, `Context expansion:`.
    - Risk examples: `read all`, `read full`, `read .cg-docs`, `read compound-gpid.context.md` without qualification, `read roadmap.json` without workflow-specific reason, `read brain-index.json` in a prompt.
  - Include line snippets or short reasons in JSON and Markdown output.
  - Keep existing model inventory, premium usage checks, duplicate paragraph checks, and dispatch burden checks intact.
- **Test Scenarios**:
  - Happy path: targeted context-loading wording is not flagged.
  - Edge case: `/cg-resume` justified full roadmap read is either not flagged or flagged as justified.
  - Error path: broad "Read `.cg-docs/`" or "Read `brain-index.json`" instruction is flagged.
- **Tests**:
  - `python -m pytest scripts/tests/test_audit_context.py -v`
  - Add unit tests for the new broad context-loading classifier.
- **Acceptance criteria**:
  - Audit report can identify broad context-loading instructions.
  - Audit report still reports no premium model usage.
  - Existing audit tests pass.

### 5. Run Static And Manual Validation

- **Requirements**: R1, R2, R4, R6, R10, R11, R12
- **Files**:
  - `.cg-docs/cost/context-audit.md`
  - `.cg-docs/cost/context-audit.json`
  - `docs/workflow.md`
  - `docs/reference.md`
- **Details**:
  - Run the context audit after implementation and compare the new report to the 2026-06-07 baseline.
  - Run static grep checks for broad loading language:
    - `rg -n "Read \`compound-gpid\\.context\\.md\`|read \`compound-gpid\\.context\\.md\`|Read \`roadmap\\.json\`|read \`roadmap\\.json\`|read .*brain-index\\.json|read all .*\\.cg-docs|read full .*BRAIN" .github docs scripts`
  - Update docs only where they describe context-loading behavior or command reference expectations.
  - Do not continue general prompt slimming outside the selective context-loading scope.
- **Audit Checks To Run**:
  - `python scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
  - Confirm `.cg-docs/cost/context-audit.md` includes the new Context Loading Risks section.
  - Confirm Premium Model Usage remains `None`.
  - Confirm Ordinary Prompt Model-Picker Violations remain `None`.
  - Confirm broad context-loading risks are either gone or justified.
- **Manual VS Code Copilot Validation**:
  - `/cg-plan` on a task with known prior Knowledge Brain entries: confirm it reads `BRAIN.md`, selects matched topic(s), opens only relevant Brain section(s), and states any context expansion reason.
  - `/cg-work phase1 review:manual` on the approved implementation plan: confirm it does not dispatch review agents and does not read full Brain/context artifacts by default.
  - `/cg-work phase1 review:auto` or another `review:*` mode after implementation: confirm Phase 4 review-mode routing still resolves correctly. This is a pending Phase 4 runtime validation item and should remain scoped to validation, not redesign.
  - `/cg-review light` on a small prompt/doc diff: confirm staged routing remains light and Brain consultation is targeted.
  - `/cg-compound --no-enrich` after a small solved issue in a disposable branch/test fixture: confirm solution capture still works and Brain rebuild behavior remains available.
  - `/cg-brain-rebuild`: confirm it runs `cg-index --brain`, verifies output existence/counts, and does not read generated Brain artifacts wholesale.
  - `/cg-resume`: confirm roadmap health still renders, with explicit reason for structured roadmap read.
- **Acceptance criteria**:
  - Static validation passes.
  - Existing tests pass.
  - Manual runtime validation confirms prompts recover relevant prior knowledge when needed without broad default memory loading.

## Testing Strategy

- Unit test the new audit classifier in `scripts/tests/test_audit_context.py`.
- Run the full audit generator and inspect both Markdown and JSON outputs.
- Use safe project test patterns. If Pester tests are needed, use the repository's safe runner only; do not invoke `Invoke-Pester` directly.
- Treat prompt-only Markdown edits as static-validation-heavy unless existing prompt tests cover them.

## Documentation Checklist

- Update `docs/workflow.md` only if it describes default context loading, Brain consultation, or command behavior affected by Phase 5.
- Update `docs/reference.md` only if command reference text says prompts read full context by default.
- Consider adding a short note to `docs/context-files.md` that `compound-gpid.context.md` is a tactical knowledge base but should be loaded selectively by prompts.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompts become too sparse and miss relevant prior knowledge. | Agents repeat mistakes or ignore known patterns. | Keep query-first Brain consultation mandatory for workflows that already have Consult Brain steps; validate manually with known prior entries. |
| Audit flags legitimate maintenance behavior as risky. | Noise reduces usefulness of the audit. | Classify justified full reads separately from risky broad reads. |
| `/cg-compound` or `/cg-brain-rebuild` behavior is accidentally weakened. | Knowledge Brain stops updating correctly. | Acceptance criteria and manual validation explicitly preserve rebuild behavior. |
| `/cg-resume` cannot compute roadmap health without full JSON. | Session startup loses useful status context. | Allow structured full `roadmap.json` parsing for `/cg-resume` with explicit justification and limited carry-forward. |
| Prompt edits unintentionally alter Phase 4 review-mode behavior. | Runtime review validation regresses. | Do not modify review routing logic; validate `/cg-work review:*` separately as a follow-up. |

## Out of Scope

- Refactoring Team Brain.
- Redesigning Knowledge Brain internals.
- Removing or weakening `.cg-docs` institutional-memory behavior.
- Stopping generation of `brain-index.json`, `BRAIN.md`, `BRAIN-01.md`, or `BRAIN-log.md`.
- Changing Phase 2 model governance.
- Redesigning `/cg-review` routing.
- General prompt slimming beyond selective context-loading changes.
- Redesigning Phase 4; only validate the pending `/cg-work review:*` runtime behavior.

## Acceptance Criteria

- Ordinary prompts no longer encourage broad/default loading of full Knowledge Brain artifacts.
- Context expansion rules are explicit and include a reason before expanding.
- `compound-gpid.context.md` and `roadmap.json` reads are targeted or justified by workflow.
- `/cg-compound` and `/cg-brain-rebuild` still work and still preserve Brain artifact generation/rebuild.
- The audit can identify broad context-loading instructions.
- Premium model usage remains absent or explicitly justified.
- Ordinary model-picker violations remain absent.
- Existing tests pass.
- Manual VS Code runtime validation confirms prompts still recover relevant prior knowledge when needed.
- Pending `/cg-work review:*` runtime validation is tracked as a follow-up validation item, with no Phase 4 redesign.
