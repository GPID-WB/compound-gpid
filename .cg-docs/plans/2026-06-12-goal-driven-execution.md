---
date: 2026-06-12
title: "Goal-driven execution for /cg-plan and /cg-work"
status: completed
completed-date: 2026-06-12
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-06-12-goal-driven-execution.md"
language: "PowerShell/Markdown"
estimated-effort: "large"
phases: 4
completed-phases: [1, 2, 3, 4]
current-phase: 4
execution-report: .cg-docs/work-reports/2026-06-12-goal-driven-execution.md
deviation-policy: ask
tags: [workflow, cg-plan, cg-work, goal-driven-execution, validation, completion-contract]
---

# Plan: Goal-Driven Execution for /cg-plan and /cg-work

## Objective

Transform the `/cg-plan` -> `/cg-work` workflow into a Compound GPID-native
goal-driven execution loop inspired by Codex Goals. `/cg-plan` should create a
plan-as-completion-contract, and `/cg-work` should execute against that
contract until evidence proves completion or a blocked-stop condition is hit.

## Context

The brainstorm
`.cg-docs/brainstorms/2026-06-12-goal-driven-execution.md` selected
**Shared Contract + Thin Prompt Hooks**. The implementation should preserve:

- Phased plan and phased execution behavior.
- Pester safety rules and the canonical safe runner pattern.
- Review routing behavior through `.github/shared/review-routing.contract.md`.
- Recent prompt slimming for `/cg-plan` and `/cg-work`.

Relevant prior lessons:

- Shared contracts are already used successfully for review routing.
- `/cg-plan` and `/cg-work` were intentionally slimmed recently; avoid large
  duplicated prompt sections.
- Prompt-test changes need targeted regression tests for each new branch.
- Completion claims must be backed by real validation evidence, not static
  inspection alone.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Create a shared goal-execution contract that defines completion-contract schema, deviation semantics, evidence gates, execution report schema, and blocked-stop behavior. | brainstorm |
| R2 | Keep `/cg-plan` and `/cg-work` compact by adding thin hooks that load and follow the shared contract. | brainstorm + prompt-slimming context |
| R3 | Add `deviate:ask`, `deviate:auto`, and `deviate:strict` support to `/cg-plan`; default is `ask`; store `auto` as `autonomous`. | brainstorm |
| R4 | Add matching `deviate:` runtime override support to `/cg-work`; absent override uses the plan's `deviation-policy`. | brainstorm |
| R5 | Every saved plan gets a completion contract scaled to plan scope. | brainstorm |
| R6 | `/cg-plan` previews the completion contract before writing the plan; user approval is treated as signing the contract. | brainstorm |
| R7 | Contract verification and constraints use stable ID tables; optional `Phase` column is accepted for phased plans; parsing is header-driven, not position-driven. | brainstorm |
| R8 | `/cg-work` creates and incrementally updates a separate execution report artifact, likely under `.cg-docs/work-reports/`. | brainstorm |
| R9 | Plan files remain the stable contract; `/cg-work` may only write minimal operational metadata and an execution-report pointer to the plan. | brainstorm |
| R10 | `/cg-work` applies a strict evidence gate before marking work complete. Missing required evidence blocks completion unless explicitly user-accepted as an exception. | brainstorm + charter |
| R11 | `/cg-work` durably records deviations, runtime policy overrides, accepted exceptions, evidence, and remaining uncertainty in the execution report. | brainstorm |
| R12 | Phase-level verification is optional but supported; Deep phased plans should recommend phase-level verification rows. | brainstorm + phased execution context |
| R13 | Existing phase parsing, phase boundary, `completed-phases`, and `current-phase` behavior remain intact. | existing phased execution feature |
| R14 | Existing review routing remains intact; `/cg-review` is recommended/available but not required by default after successful goal execution. | roadmap + review-routing contract |
| R15 | Pester guidance must preserve the safe runner pattern and must not add direct `Invoke-Pester` recipes. | project instructions |
| R16 | Documentation explains the new contract/report artifact boundary and `deviate:` arguments. | docs standards |
| R17 | Prompt-tool tests cover shared contract existence/content, prompt hooks, argument parsing docs, report path, evidence gate, and Pester safety preservation. | testing standards |
| R18 | Legacy plans, inline fallback plans, and plans missing completion-contract fields have an explicit compatibility path. | plan review P1.1 |
| R19 | Evidence gates are explicitly inserted before the existing phase, plan, and roadmap completion write points. | plan review P1.2 |
| R20 | The completion contract is subordinate to system/prompt permissions, project charter constraints, Pester safety, review routing, and protected-artifact rules. | plan review P2.5 |
| R21 | Execution reports have deterministic resume, collision, blocked-resume, and missing-pointer behavior. | plan review P2.6 |
| R22 | `.cg-docs/work-reports/` is scaffolded or created safely before use. | plan review P2.7 |
| R23 | `deviate:` parsing handles duplicate, empty, case-variant, and `autonomous` alias inputs deterministically. | plan review P3.1 |

## Completion Contract

### Outcome

The workflow prompts define and execute a goal-driven completion contract:
`/cg-plan` produces an approved contract for all saved plans, `/cg-work` uses
that contract as its execution authority, and completion is only recorded when
required evidence is present or explicitly accepted as an exception.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Shared contract exists and defines schema, accepted table variants, deviation policies, report schema, evidence gate, and blocked-stop defaults. | `.github/shared/goal-execution.contract.md` inspection + prompt tests | yes |
| V2 | 2 | `/cg-plan` documents and uses `deviate:` arguments, default `ask`, `auto` -> `autonomous`, contract preview before save, and completion-contract output. | `tests/prompt-tools.Tests.ps1` via safe runner | yes |
| V3 | 3 | `/cg-work` documents and uses `deviate:` override handling, execution report creation/update, strict evidence gate, deviation logging, and accepted exceptions. | `tests/prompt-tools.Tests.ps1` via safe runner | yes |
| V4 | 4 | Docs describe the goal-driven plan/work loop, deviation options, plan/report boundary, and review handoff relationship. | `docs/workflow.md` and `docs/reference.md` inspection + prompt/docs tests | yes |
| V5 | 4 | setup/scaffold behavior covers `.cg-docs/work-reports/` for new and existing projects, or `/cg-work` creates it safely before writing reports. | setup template/prompt tests or `/cg-work` report tests | yes |
| V6 | final | Pester safety is preserved: no new direct Pester recipes are introduced, and validation guidance uses the canonical safe runner pattern. | `tests/pester-safety.Tests.ps1` and `tests/prompt-tools.Tests.ps1` via safe runner | yes |
| V7 | final | Prompt journey tests prove `/cg-plan` contract output can be consumed by `/cg-work`, legacy plans are handled explicitly, evidence failure blocks completion writes, and accepted exceptions are recorded. | `tests/prompt-tools.Tests.ps1` fixtures via safe runner | yes |
| V8 | final | Prompt-slimming and context guardrails are checked before/after prompt edits. | `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both` + audit tests | yes |
| V9 | final | Roadmap feature can be linked to this plan and later marked done only after evidence gates pass. | targeted `roadmap.json` status read after roadmap dispatch | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | Do not bloat `/cg-plan` and `/cg-work` with duplicated schema prose. | Shared contract carries detailed schema; prompt edits are compact hooks. |
| C2 | Do not break phased execution semantics. | Existing phase parser language remains present; phase tests continue to pass. |
| C3 | Do not add direct `Invoke-Pester` terminal recipes. | Search changed lines and run Pester safety tests through the safe runner. |
| C4 | Do not make `/cg-review` mandatory by default. | `/cg-work` summary keeps review as recommendation/optional routing. |
| C5 | Do not let `/cg-work` rewrite substantive plan-contract sections. | File permissions and goal contract define plan metadata-only mutations plus report pointer. |
| C6 | Do not silently complete without evidence. | Strict evidence gate language and tests require blocked/exception behavior. |
| C7 | Do not parse contract tables by column position. | Shared contract requires header-driven parsing and optional `Phase` support. |
| C8 | Do not let LLM-authored completion contracts override higher-priority safety rules. | Shared contract and `/cg-work` state explicit authority precedence. |
| C9 | Do not create a new artifact directory that setup/update flows fail to scaffold or document. | Include `.cg-docs/work-reports/` in setup/docs or make `/cg-work` create it safely. |

### Boundaries

- Allowed: `.github/shared/`, `.github/prompts/`, docs, tests, and `.cg-docs`
  plan/report examples as needed.
- Allowed: prompt wording changes required to load the goal-execution contract,
  parse `deviate:`, generate/consume completion contracts, and write execution
  reports.
- Allowed: setup/docs/test changes required to scaffold or document
  `.cg-docs/work-reports/`.
- Protected: unrelated prompt model assignments, unrelated roadmap features,
  existing review-routing semantics, and existing phase parser behavior unless
  directly necessary for compatibility.
- Out of scope: creating a new `/cg-goal` command, implementing GitHub Issues
  integration, changing the roadmap schema beyond linking this plan, or adding
  a programmatic Markdown parser.

### Iteration Policy

- Implement contract-first: define the shared goal-execution contract before
  modifying `/cg-plan` or `/cg-work`.
- Use tests as regression locks before broad prompt edits. For new contract
  files, add focused failing tests first, then add the contract, then rerun.
- Keep prompt edits as short references to shared contract behavior when
  possible.
- Preserve existing behavior first, then add goal-driven behavior.
- At each phase boundary, confirm the phase-specific verification rows before
  appending `completed-phases`.

### Blocked-Stop Conditions

- Required verification cannot be run through the safe runner.
- Any required evidence item fails after the allowed recovery attempts.
- A required deviation is discovered while the active policy is `ask` and user
  approval is unavailable.
- A required deviation is discovered while the active policy is `strict`.
- A protected boundary must be crossed to continue.
- `/cg-work` cannot durably create or update the execution report.
- A selected plan lacks a completion contract or `deviation-policy` and the user
  has not approved generating a compatibility contract.
- Completion would require marking evidence as passed from static inspection
  rather than an executed check.

## Phase 1: Shared Goal-Execution Contract

### 1. Add failing tests for the shared contract

- **Requirements**: R1, R7, R17, R20, R21, R23
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add a focused `Describe` block for
    `.github/shared/goal-execution.contract.md` before creating the contract.
  - Assert required sections and values exist:
    `Completion Contract`, `Verification Surface`, `deviate:ask`,
    `deviate:auto`, `deviate:strict`, `deviate:autonomous`,
    `deviation-policy`, `autonomous`, `Execution Report`,
    `.cg-docs/work-reports`, `strict evidence gate`, `header-driven`,
    `Phase`, `Authority Precedence`, `Legacy Plan Compatibility`, and
    `Report Resume`.
  - Keep regexes specific enough to avoid common-word false positives.
- **Test Scenarios**:
  - Happy path: required sections are present.
  - Edge case: both non-phased and phased table variants are documented.
  - Error path: missing report path, authority precedence, or evidence gate
    fails the test.
- **Tests**:
  - Use safe runner targeted at `prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - Tests fail before the contract exists and pass after Step 2 adds it.

### 2. Create the shared goal-execution contract

- **Requirements**: R1, R5, R7, R8, R10, R11, R12, R18, R20, R21, R22, R23
- **Files**: `.github/shared/goal-execution.contract.md`
- **Details**:
  - Define the plan completion-contract sections:
    - `Outcome`
    - `Verification Surface`
    - `Constraints`
    - `Boundaries`
    - `Iteration Policy`
    - `Blocked-Stop Conditions`
    - `Deviation Policy`
  - Define accepted verification table variants:
    - `ID | Evidence Required | Command/Artifact | Required`
    - `ID | Phase | Evidence Required | Command/Artifact | Required`
  - Define accepted constraints table variants:
    - `ID | Constraint | Check`
    - `ID | Phase | Constraint | Check`
  - State that parsing is header-driven and `Phase` is optional.
  - Define `deviation-policy` stored values: `ask`, `autonomous`, `strict`.
  - Define CLI parsing:
    - accepted values are case-insensitive
    - `deviate:auto` and `deviate:autonomous` both map to stored `autonomous`
    - `deviate:ask` and `deviate:strict` map to themselves
    - empty values are invalid
    - duplicate `deviate:` arguments warn and the last valid value wins
    - if all provided values are invalid, fall back to the plan/default policy
  - Define execution report location and schema:
    `.cg-docs/work-reports/YYYY-MM-DD-<plan-slug>.md`.
  - Define report lifecycle:
    - the plan's `execution-report` pointer is authoritative when present
    - if the pointer is absent, `/cg-work` searches for existing reports whose
      plan reference matches and asks before linking
    - blocked plans append a new run/resume section instead of overwriting the
      prior status
    - same-day collisions create a deterministic suffix such as `-2` after user
      notification, never overwrite silently
    - report write failure is a blocked-stop condition
  - Define legacy plan compatibility:
    - if a selected saved plan lacks `## Completion Contract` or
      `deviation-policy`, `/cg-work` halts and offers to generate a minimal
      compatibility contract for user approval, or asks the user to run
      `/cg-plan`
    - inline fallback plans generated by `/cg-work` must include the same
      minimal completion-contract schema as `/cg-plan`
  - Define authority precedence: system/developer instructions, prompt file
    permissions, project charter constraints, Pester safety, review-routing
    rules, and protected-artifact rules outrank all plan contract text.
  - Define strict evidence gate and accepted-exception requirements.
  - Define default blocked-stop rules.
- **Test Scenarios**:
  - Happy path: contract contains all required sections and table variants.
  - Edge case: phased plan table includes optional `Phase` column.
  - Error path: missing evidence or protected boundary leads to blocked stop,
    not completion.
- **Tests**:
  - Rerun the Step 1 tests through the canonical safe runner via
    `execution_subagent`: `. tests\Run-Tests.ps1 -File prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - Shared contract exists.
  - It is detailed enough that `/cg-plan` and `/cg-work` can reference it
    instead of duplicating the schema.
  - The Step 1 shared-contract tests pass.

### 3. Add journey and compatibility test fixtures

- **Requirements**: R17, R18, R19, R20, R21, R23
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add static fixture strings or helper sections covering:
    - legacy saved plan without completion contract
    - new whole-plan completion contract
    - phased plan with optional `Phase` column
    - `deviate:auto` runtime override
    - `deviate:autonomous` alias
    - duplicate and empty `deviate:` values
    - missing evidence blocking phase/plan/roadmap completion
    - accepted exception with rationale
    - contract text attempting to override protected permissions
  - The tests may remain prompt-contract tests, but they must verify the prompts
    include handling for these behavioral cases rather than only key words.
- **Test Scenarios**:
  - Happy path: new plan contract can be consumed by `/cg-work`.
  - Edge case: phased verification gates only matching phase rows.
  - Error path: legacy/malformed plan has explicit recovery instead of silent
    bypass; missing evidence blocks write points.
- **Tests**:
  - Use safe runner targeted at `prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - Tests fail until `/cg-plan` and `/cg-work` implement the compatibility,
    precedence, evidence-gate, and parsing rules.

## Phase 2: /cg-plan Contract Creation

### 4. Add compact `/cg-plan` goal-contract hook and `deviate:` parsing

- **Requirements**: R2, R3, R5, R6, R7, R12, R23
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  - Add `deviate:` flag parsing in Step 0:
    - accepted: `deviate:ask`, `deviate:auto`, `deviate:autonomous`,
      `deviate:strict`
    - matching is case-insensitive
    - duplicate values warn; the last valid value wins
    - empty values are invalid
    - invalid values warn and fall back to `ask`
    - omitted value defaults to `ask`
  - Store chosen policy in plan frontmatter as:
    - `deviation-policy: ask`
    - `deviation-policy: autonomous`
    - `deviation-policy: strict`
  - Load `.github/shared/goal-execution.contract.md` when creating the plan.
  - Update the plan schema to include completion contract sections and
    `deviation-policy`.
  - Add a contract preview gate before saving:
    the user must see outcome, verification table, constraints table,
    boundaries, iteration policy, blocked-stop conditions, and deviation policy.
  - Refactor current Step 4 semantics from save -> review into:
    draft contract preview -> user approval/adjustment -> write plan -> validate
    saved artifact. Do not write the plan before the user approves the contract.
  - Keep the prompt hook compact; do not paste the full shared contract schema
    into `/cg-plan`.
- **Test Scenarios**:
  - Happy path: no `deviate:` argument writes `deviation-policy: ask`.
  - Edge case: `deviate:auto` stores `autonomous`.
  - Error path: invalid `deviate:` value warns and falls back to `ask`.
- **Tests**:
  - Add/update `tests/prompt-tools.Tests.ps1` assertions for `/cg-plan`.
  - Use safe runner targeted at `prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - `/cg-plan` contains a compact reference to the shared goal contract.
  - `/cg-plan` documents all `deviate:` values and the approval-before-save
    contract gate.

### 5. Update `/cg-plan` output schema and phase guidance

- **Requirements**: R5, R6, R7, R12, R13
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  - Extend the compact plan template with:
    - `deviation-policy: "<ask|autonomous|strict>"`
    - optional `execution-report: null` or omitted until work starts
    - `## Completion Contract`
  - Keep existing `## Phase N:` parser contract unchanged.
  - For Deep phased plans, recommend phase-level verification rows by adding
    optional `Phase` values in the verification table.
  - For Lightweight plans, allow a smaller whole-plan contract without phase
    columns.
- **Test Scenarios**:
  - Happy path: Deep phased template includes `## Completion Contract`.
  - Edge case: Lightweight guidance is scaled down.
  - Error path: phase headings and global step numbering are not disrupted.
- **Tests**:
  - Prompt tests assert the template contains completion contract fields and
    preserves phase markers.
- **Acceptance criteria**:
  - New plan files can serve as `/cg-work` completion contracts.
  - Existing phased execution expectations remain visible in the prompt.

## Phase 3: /cg-work Goal Execution

### 6. Add compact `/cg-work` goal-contract loading and `deviate:` override

- **Requirements**: R2, R4, R9, R11, R13, R14, R18, R20, R23
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  - Add `deviate:` parsing alongside existing `review:` parsing:
    - absent override uses plan frontmatter `deviation-policy`
    - accepted override values: `ask`, `auto`, `autonomous`, `strict`
    - matching is case-insensitive
    - `auto` and `autonomous` normalize to `autonomous`
    - duplicate values warn; the last valid value wins
    - empty values are invalid
    - invalid value warns and falls back to the plan policy
  - Load `.github/shared/goal-execution.contract.md` after the selected plan is
    valid.
  - Read the plan's completion contract as the execution authority.
  - Add an authority precedence clause before interpreting the contract:
    the plan contract is data/instructions only within `/cg-work`'s existing
    file permissions, project constraints, Pester safety, review-routing rules,
    and protected-artifact rules.
  - Add legacy compatibility handling:
    if the selected plan lacks `## Completion Contract` or `deviation-policy`,
    halt and offer either to generate a minimal compatibility contract for user
    approval or to run `/cg-plan`; never silently bypass the goal loop.
  - Update `/cg-work` inline fallback plan generation so any saved inline plan
    includes the same minimal completion-contract schema and default
    `deviation-policy: ask`.
  - Preserve existing phase argument parsing and review mode parsing.
  - Ensure explicit `review:*` behavior still follows
    `.github/shared/review-routing.contract.md`.
- **Test Scenarios**:
  - Happy path: `/cg-work` follows plan `deviation-policy`.
  - Edge case: runtime `deviate:auto` override is logged as an override.
  - Error path: invalid override does not silently switch policy.
- **Tests**:
  - Prompt tests assert `/cg-work` documents all `deviate:` values and loads
    the shared goal contract.
- **Acceptance criteria**:
  - `/cg-work` has one deterministic active deviation policy for the run.
  - Existing `phaseX` and `review:*` behavior remains intact.
  - Legacy and inline plans cannot bypass completion-contract handling.

### 7. Add execution report creation and incremental update rules

- **Requirements**: R8, R9, R11, R21, R22
- **Files**: `.github/prompts/cg-work.prompt.md`, `.github/shared/goal-execution.contract.md`
- **Details**:
  - In `/cg-work`, create the execution report early after plan validation and
    roadmap active-status handling.
  - Use path pattern:
    `.cg-docs/work-reports/YYYY-MM-DD-<plan-slug>.md`.
  - Ensure the directory exists before writing:
    if `.cg-docs/work-reports/` is missing, create it and include `.gitkeep`
    if the report file is not created immediately; report write failure as
    blocked.
  - Add plan frontmatter write permission for a minimal `execution-report`
    pointer.
  - Report identity is plan-bound:
    - use the existing `execution-report` pointer when present
    - if absent, search existing reports for a matching plan reference and ask
      before linking
    - if no report exists, create a new report
    - if a generated path collides, notify and append `-2`, `-3`, etc.; never
      overwrite silently
    - if a blocked report is resumed, append a new run/resume section rather
      than replacing prior final status
  - Define report sections:
    - plan reference
    - active deviation policy and runtime override if any
    - completed steps/phases
    - deviations
    - accepted exceptions
    - evidence table mirroring verification IDs
    - constraints check
    - remaining uncertainty
    - final status: `completed` or `blocked`
  - Update the report incrementally after phase completion, deviation decisions,
    accepted exceptions, test/evidence runs, and blocked stops.
- **Test Scenarios**:
  - Happy path: report is created and linked before implementation starts.
  - Edge case: resumed phased work updates the existing report.
  - Error path: inability to write report is a blocked-stop condition.
- **Tests**:
  - Prompt tests assert report path, report sections, and plan pointer rules.
- **Acceptance criteria**:
  - The plan remains the contract.
  - The execution report is the durable accountability artifact.
  - Resume/collision behavior preserves prior accountability evidence.

### 8. Add strict evidence gate and deviation handling to `/cg-work`

- **Requirements**: R10, R11, R12, R13, R15, R19
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  - Insert contract evidence checks at the concrete existing write points:
    - before Step 2.5 appends a phase number to `completed-phases`, check any
      required verification rows whose optional `Phase` matches the current
      phase
    - before Step 3.5 writes `status: completed`, check all required
      final/whole-plan verification rows
    - before Step 3.7 dispatches roadmap `done`, require the same final evidence
      gate to have passed or have explicit accepted exceptions
  - If evidence is missing or failed:
    - block completion, or
    - record an explicit user-accepted exception with rationale.
  - Deviations:
    - `ask`: pause before deviating; record decision.
    - `autonomous`: allow justified deviation; record decision and impact.
    - `strict`: do not deviate; blocked-stop unless the plan is revised.
  - Keep Pester commands routed through the existing safe runner guidance.
- **Test Scenarios**:
  - Happy path: all required verification IDs have evidence and completion
    proceeds.
  - Edge case: optional phase verification gates only the relevant phase.
  - Error path: missing evidence blocks completion.
- **Tests**:
  - Prompt tests assert evidence-gate language, accepted-exception requirement,
    and blocked-stop behavior.
  - Pester safety tests remain passing.
- **Acceptance criteria**:
  - `/cg-work` cannot mark plan/roadmap complete without evidence or an
    explicit accepted exception.
  - Existing phase/status/roadmap completion paths are contract-gated, not only
    test-gated.

## Phase 4: Documentation, Roadmap, and Validation

### 9. Update setup/scaffold behavior and user-facing documentation

- **Requirements**: R16, R22
- **Files**: `.github/prompts/setup-templates.md`, `.github/prompts/cg-setup.prompt.md`, `docs/workflow.md`, `docs/reference.md`
- **Details**:
  - Add `.cg-docs/work-reports/` to the `.cg-docs` scaffold in setup templates,
    including `.gitkeep` guidance if the directory can be empty.
  - If setup scaffolding is intentionally not changed, `/cg-work` must create
    the directory safely before writing and docs must state that behavior.
  - Explain plan-as-completion-contract behavior.
  - Document `deviate:` arguments for `/cg-plan` and `/cg-work`.
  - Explain the plan/report artifact boundary.
  - Explain that `/cg-review` remains available but no longer required as the
    default post-work step when evidence gates pass.
  - Add `.cg-docs/work-reports/` to artifact documentation if relevant.
- **Test Scenarios**:
  - Happy path: reference docs list new arguments and report location.
  - Edge case: docs distinguish plan default from runtime override.
  - Error path: docs do not imply review is mandatory; missing report directory
    does not cause silent failure.
- **Tests**:
  - Prompt/docs tests for scaffold/report path if existing test structure covers
    docs content.
  - Otherwise validate by targeted inspection and include in execution report.
- **Acceptance criteria**:
  - Users can understand how to use `deviate:` and where execution evidence
    lives.
  - New or existing projects have a reliable `.cg-docs/work-reports/` path.

### 10. Run safe validation, benchmark guardrails, and preserve Pester guardrails

- **Requirements**: R15, R17
- **Files**: `tests/prompt-tools.Tests.ps1`, `tests/pester-safety.Tests.ps1`, `scripts/cg_audit_context.py`, `.cg-docs/cost/`
- **Details**:
  - Use the canonical safe runner through `execution_subagent`.
  - Targeted validation:
    - `. tests\Run-Tests.ps1 -File prompt-tools.Tests.ps1`
    - `. tests\Run-Tests.ps1 -File pester-safety.Tests.ps1`
  - Full-suite validation when ready:
    - `. tests\Run-Tests.ps1`
  - Inspect `tests/last-run.json` for `passed`, `failedCount`, `failures`,
    and `filteredFiles`.
  - Run prompt/context benchmark guardrails before and after prompt edits:
    - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
  - Check that prompt/context audit does not reintroduce premium model defaults,
    broad context loading, prompt-size regression, or unconditional review
    dispatch.
- **Test Scenarios**:
  - Happy path: targeted tests pass.
  - Edge case: full-suite result is not treated as complete if filtered.
  - Error path: no direct Pester command is introduced; audit regression is not
    ignored.
- **Tests**:
  - Safe runner commands above.
- **Acceptance criteria**:
  - Targeted tests pass.
  - Full safe runner passes or any environment limitation is explicitly
    reported with remaining uncertainty.
  - Context audit artifacts are regenerated and reviewed for regressions.

### 11. Link roadmap feature and finalize handoff

- **Requirements**: R14, R17
- **Files**: `roadmap.json` via `@cg-roadmap`, this plan file
- **Details**:
  - Link this plan to roadmap feature `goal-driven-execution` in milestone
    `workflow-maturity`.
  - During `/cg-work`, mark the feature active when implementation starts and
    done only after evidence gates pass.
  - Recommend `/cg-plan-review` before implementation because this is a Deep
    cross-cutting prompt feature.
- **Test Scenarios**:
  - Happy path: roadmap feature links to this plan.
  - Edge case: feature has `plan: null` before linking.
  - Error path: roadmap status is not marked done before evidence passes.
- **Tests**:
  - Targeted `roadmap.json` read after roadmap dispatch.
- **Acceptance criteria**:
  - Roadmap link is established or the user is told to run `@cg-roadmap`
    directly if dispatch is unavailable.

## Testing Strategy

- Add tests before or alongside each prompt behavior change.
- Prefer focused static prompt tests in `tests/prompt-tools.Tests.ps1`.
- Preserve `tests/pester-safety.Tests.ps1` as the guard against unsafe Pester
  patterns.
- Use the canonical safe runner via `execution_subagent`; do not introduce
  direct `Invoke-Pester` recipes.
- Treat static file inspection as supporting evidence, not a substitute for
  safe-runner test results.

## Documentation Checklist

- [ ] `.github/prompts/setup-templates.md` or `/cg-work` runtime behavior
      guarantees `.cg-docs/work-reports/` exists before writing.
- [ ] `docs/workflow.md` explains the goal-driven execution loop.
- [ ] `docs/reference.md` documents `/cg-plan deviate:*` and
      `/cg-work deviate:*`.
- [ ] Docs explain `.cg-docs/work-reports/`.
- [ ] Docs clarify that `/cg-review` remains available but is no longer the
      default mandatory post-work step.
- [ ] Any new frontmatter field is added to the relevant reference section.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt bloat reverses recent slimming work. | Higher token cost and more brittle prompts. | Put detailed schema in shared contract; keep prompt hooks compact. |
| `/cg-work` misreads flexible tables. | False completion or false block. | Require header-driven parsing and test accepted table variants. |
| Evidence gate conflicts with phased execution. | Phases may complete without proof or block too aggressively. | Gate phase-specific rows at phase boundaries and final rows at plan completion. |
| New report artifact is not created reliably. | Deviations/evidence are lost. | Create report early and treat write failure as blocked-stop. |
| Deviation override becomes unaudited. | Accountability is weakened. | Record runtime override and all deviations in execution report. |
| Pester guidance regresses to unsafe commands. | VS Code crash risk. | Preserve safe runner language and run pester-safety tests. |
| Review routing is accidentally changed. | Cost/routing regressions. | Keep review-routing contract unchanged and test `/cg-work review:*` hooks still reference it. |
| Legacy plans bypass the new goal loop. | Existing or inline plans may complete without a contract. | Add explicit legacy-plan halt/recovery and require inline fallback plans to include minimal contracts. |
| The plan contract is treated as higher authority than prompt safety rules. | Malformed plan text could weaken file permissions or Pester safety. | Add authority precedence to shared contract and `/cg-work`; test hostile contract fixtures. |
| Report reruns overwrite prior blocked evidence. | Accountability record is corrupted. | Make report identity plan-bound, use the plan pointer first, and append run/resume sections. |

## Out of Scope

- Creating a new `/cg-goal` command.
- Replacing `/cg-review`; it remains available for adversarial/cross-model
  review.
- Implementing GitHub Issues integration.
- Changing roadmap schema beyond linking this plan to the existing feature.
- Building a programmatic Markdown parser.
- Refactoring unrelated prompts, agents, skills, or docs.

## Review Findings Addressed

This revision incorporates the `/cg-plan-review` findings:

- **P1.1**: Added legacy-plan and inline-plan compatibility requirements,
  shared-contract rules, `/cg-work` behavior, and journey tests.
- **P1.2**: Added exact evidence-gate insertion points before
  `completed-phases`, `status: completed`, and roadmap `done`.
- **P2.1**: Added explicit `/cg-plan` draft preview -> approval -> write ->
  validate ordering.
- **P2.2**: Reordered Phase 1 to write failing shared-contract tests before
  creating the contract.
- **P2.3**: Added cross-prompt journey/fixture tests beyond static term checks.
- **P2.4**: Added `scripts/cg_audit_context.py` benchmark guardrails.
- **P2.5**: Added authority precedence requirements and hostile-contract tests.
- **P2.6**: Added report identity, resume, collision, missing-pointer, and
  blocked-resume semantics.
- **P2.7**: Added `.cg-docs/work-reports/` scaffold/create-before-use coverage.
- **P3.1**: Added deterministic parsing for duplicate, empty, case-variant,
  `auto`, and `autonomous` `deviate:` values.

## /cg-work Execution Handoff

Recommended execution sequence:

1. `/cg-plan-review` on this plan before implementation, because the work is a
   Deep prompt-architecture change.
2. `/cg-work phase1 .cg-docs/plans/2026-06-12-goal-driven-execution.md`
3. `/cg-work phase2 .cg-docs/plans/2026-06-12-goal-driven-execution.md`
4. `/cg-work phase3 .cg-docs/plans/2026-06-12-goal-driven-execution.md`
5. `/cg-work phase4 .cg-docs/plans/2026-06-12-goal-driven-execution.md`

If executing all at once, use:

```text
/cg-work .cg-docs/plans/2026-06-12-goal-driven-execution.md
```

Use `deviate:ask` unless the user explicitly chooses a different policy.
