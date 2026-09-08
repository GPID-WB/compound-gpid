---
date: 2026-07-30
title: "CR Scoping Front-End + Normative-Decision Gates (Responsible Research Partner — Phase 3)"
status: completed
completed-date: 2026-07-31
scope: Deep
brainstorm: ".cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md"
language: "PowerShell/Markdown"
estimated-effort: large
deviation-policy: ask
execution-report: ".cg-docs/work-reports/2026-07-30-cr-scoping-normative-gates.md"
completed-phases: [1, 2, 3]
current-phase: 3
failing-steps: []
tags: [compound-research, responsible-ai, scoping, normative-decisions, value-transparency, gates, p0]
---

# CR Scoping Front-End + Normative-Decision Gates (Responsible Research Partner — Phase 3)

## Objective

Give the Compound Research (CR) module a **scoping front-end** and a
**normative-decision gate backbone**, so that consequential value-laden
methodological choices are made **visible, contestable, and recorded** — never
smuggled in behind a technical result.

Concretely, this phase delivers:

- A methodology skill (`cr-skill-research-scoping`) for problem framing,
  competing conceptual frames, theory priors, and success criteria, producing a
  **scoping memo** under `.cg-docs/research/scoping/`.
- A first-class, per-study normative-decisions artifact schema — sharded at
  `.cg-docs/research/normative-decisions/<study-slug>.md` (the choice, its
  defensible alternatives, consequences including ranking shifts, the **human**
  decision, and its justification, each with a stable ID + `applies_to` links).
- **P0 gate logic** that surfaces value-laden choices for explicit human
  approval at `/cr-brainstorm` and `/cr-plan`, and **re-escalates** when a new
  normative choice appears mid-work in `/cr-work`.
- Active detection of **normative-choice smuggling** as a P0 in the
  research-integrity catalog.

This is Phase 3 of the CR expansion from a journal-paper econometrics assistant
into a responsible partner for the full research lifecycle of policy-relevant
measurement work.

## Context

The brainstorm
([2026-07-30-cr-responsible-research-partner-measurement.md](.cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md))
selected **Approach 3 (phased, value-first)** and placed the scoping front-end +
normative-gate backbone as Phase 3 — the piece that makes the whole partner
"responsible" rather than merely "rigorous". Poverty and measurement work is
saturated with normative choices (which deprivations count, where a threshold
sits, how dimensions are weighted). The tool's job is **not** to make those
choices, but to force them into the open and route them to a human.

Locked design decisions (from the brainstorm) this plan must honor:

- The tool **surfaces and records** normative choices; the **human decides**.
  A normative decision cannot be silently defaulted.
- Value-laden choices are approved via a **spec-contract gate** at
  `/cr-brainstorm` and `/cr-plan`, and re-triggered on new choices in `/cr-work`.
- **Normative-choice smuggling** (defaulting a value judgment as if it were a
  technical inevitability) is an **actively-detected P0**.
- Scoping produces a durable **scoping memo** capturing problem framing,
  competing frames, priors, and success criteria.

### Cross-cutting lessons folded in from the Phase 1 review

- **[P1.3] Durable, per-study storage for gate state.** The normative-decision
  record needs a real home, **sharded per study** at
  `.cg-docs/research/normative-decisions/<study-slug>.md` (and the scoping memo
  under `.cg-docs/research/scoping/<slug>.md`), created on demand by the prompts —
  not an ephemeral flag. Records carry stable IDs + `study`/`plan` slug +
  `applies_to` links so a single register never becomes an unscoped dumping ground.
- **[P1.4] Broaden gate triggers.** The gate must fire on value-laden choices in
  **any** research task type (not only when a plan exists) — including Writing
  and Tables/Figures framing choices.
- **[R8 reuse + Phase-3 P1.2] Deterministic gate first; agents audit the record.**
  Primary detection is **deterministic workflow logic** — the prompts enumerate a
  bounded, per-task-type taxonomy of value-laden decision points and check each
  against the register (a read/search agent cannot see a choice that was never
  recorded). `@cr-research-integrity` (P0 catalog owner) and/or
  `@cr-specification-analysis` are the **audit backstop** — they flag consequential
  choices *visible in outputs/plans* that lack a matching recorded decision, so
  **no new agent, no count-sentinel bump** unless review shows one is unavoidable.
- **[P2.2] Verification realism.** Local-static grep/JSON checks are separated
  from downstream Pester (PowerShell absent on this macOS host).
- **[P3.1]** `skills-lock.json` is not a registration surface.

### Relevant existing surfaces (researched)

- `/cr-brainstorm` Step 1.1 already classifies the task type and asks tailored
  questions; the normative gate slots in as a scoping/approval step
  ([cr-brainstorm.prompt.md](.github/prompts/cr-brainstorm.prompt.md)).
- `/cr-plan` **has no completion-contract/approval seam** — its Step 4 is
  "Present and Refine" ("Present the plan. Ask for feedback. Revise if needed.").
  The normative lock therefore attaches to that existing Present-and-Refine step
  as a lightweight approval checkpoint, not to a contract gate that does not exist
  ([cr-plan.prompt.md](.github/prompts/cr-plan.prompt.md) line ~94).
- `/cr-work` has a Step 0 pre-flight + Step 2 P0 active-detection pattern (seed,
  and — after Phase 1 — evidence) to mirror for a normative re-escalation gate
  ([cr-work.prompt.md](.github/prompts/cr-work.prompt.md)).
- `@cr-research-integrity` owns the P0 error catalog; `@cr-specification-analysis`
  already audits specification/decision documentation
  ([cr-research-integrity.agent.md](.github/agents/cr-research-integrity.agent.md),
  [cr-specification-analysis.agent.md](.github/agents/cr-specification-analysis.agent.md)).
- `cr-skill-research-integrity` + `cr-skill-research-workflow` hold the P0
  catalog and directory layout.

### Phase prerequisites and self-sufficiency

- **Phase 3 is self-sufficient.** The scoping front-end and normative gate operate
  on their own bounded decision-point taxonomy and do not require Phases 1–2 to be
  merged first.
- **Soft touchpoints degrade gracefully.** The `/cr-work` re-escalation gate mirrors
  the seed/evidence P0 pattern; if the Phase-1 evidence spine is absent, the
  normative gate still runs on its own logic. The Phase-2 measurement flag
  ("undisclosed weighting") is *consumed if present* and simply not available if
  Phase 2 has not landed — no hard dependency, no failure.
- **No forward assumptions.** This plan does not assume Phase 4 (method packs /
  lifecycle orchestration) and touches no surface Phase 4 owns.

## Requirements

| # | Requirement | Source |
|---|-------------|--------|
| R1 | `cr-skill-research-scoping`: problem framing, competing frames, theory priors, success criteria; produces scoping memo | Brainstorm (locked) |
| R2 | Scoping memo home: `.cg-docs/research/scoping/<slug>.md`; normative record sharded per study: `.cg-docs/research/normative-decisions/<study-slug>.md` | Brainstorm; [P1.3] |
| R3 | `normative-decisions.md` schema: choice, defensible options, consequences (incl. ranking shifts), human decision, justification | Brainstorm (locked) |
| R4 | Normative gate at `/cr-brainstorm` + `/cr-plan` (human approval of value-laden choices) | Brainstorm (locked) |
| R5 | `/cr-work` re-escalates on a new normative choice mid-work (active detection) | Brainstorm (locked) |
| R6 | Normative-choice smuggling is an actively-detected P0 | Brainstorm (locked) |
| R7 | Gate triggers on value-laden choices across all task types, not only when a plan exists | Phase-1 review [P1.4] |
| R8 | Prefer extending `@cr-research-integrity` / `@cr-specification-analysis`; add a new agent only if unavoidable | Brainstorm (reuse); [R8] |
| R9 | Human decides; the tool never silently defaults a normative choice | Brainstorm (locked) |
| R10 | Research-module gating preserved; targets regenerated; tests green | Charter; parity tests |
| R11 | Primary detection is deterministic workflow logic: `/cr-brainstorm` + `/cr-work` enumerate a bounded, per-task-type taxonomy of value-laden decision points and check each against the register; agents audit the *recorded* register (a read/search agent cannot see an unrecorded choice) | Phase-3 review [P1.2] |
| R12 | Bounded trigger taxonomy per task type + an explicit coverage rule for when an existing decision ID already covers the current step (so the gate is executable, not a judgment call) | Phase-3 review [P2.1] |
| R13 | Normative records carry stable IDs + `study`/`plan` slug + `applies_to`; the register is sharded per study at `.cg-docs/research/normative-decisions/<study-slug>.md` | Phase-3 review [P1.3/P3.1] |
| R14 | Writing + Tables/Figures tasks require a scoping memo + decision register; `/cr-review` compares those outputs against the register (no framing-choice bypass) | Phase-3 review [P2.3] |
| R15 | Phase 3 is self-sufficient; Phase-1 (evidence) + Phase-2 (measurement flag) are graceful-degradation touchpoints, not hard prerequisites | Phase-3 review [P2.2] |

## Implementation Steps

> Globally-numbered steps grouped into three internal phases. `/cg-work phaseA`,
> `phaseB`, `phaseC` may be used to execute a single phase.

## Phase A: Scoping Skill + Normative Schema

### 1. Create `cr-skill-research-scoping`

- **Requirements:** R1, R2
- **Files:** `.github/skills/cr-skill-research-scoping/SKILL.md` (new)
- **Details:**
  - Frontmatter: `name: cr-skill-research-scoping`, `module: research`,
    `description:` (progressive-disclosure — load at the start of any CR task, or
    when a research question is fuzzy or value-laden).
  - Sections:
    1. **Problem framing** — restate the policy/measurement question, its
       decision context, and who is affected.
    2. **Competing conceptual frames** — enumerate at least two defensible
       framings and what each makes visible/invisible.
    3. **Theory priors** — state priors/assumptions the analysis will rely on.
    4. **Success criteria** — what a credible answer looks like *before* seeing
       results (guards against specification searching).
    5. **Scoping memo schema (R2)** — Markdown at
       `.cg-docs/research/scoping/<slug>.md` capturing the four sections above
       plus an initial register of anticipated normative choices, each carrying a
       stable ID + `study`/`plan` slug and recorded to the per-study shard
       `.cg-docs/research/normative-decisions/<study-slug>.md` (R13).
- **Test Scenarios:** file exists; `module: research`; contains problem framing,
  competing frames, priors, success criteria, scoping-memo path.
- **Tests:** new `Describe` block in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1).
- **Acceptance:** V1 passes.

### 2. Define the `normative-decisions.md` artifact + P0 class

- **Requirements:** R3, R6, R9
- **Files:**
  [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md),
  [.github/skills/cr-skill-research-integrity/SKILL.md](.github/skills/cr-skill-research-integrity/SKILL.md)
- **Details:**
  - `cr-skill-research-workflow`: add `.cg-docs/research/normative-decisions/`
    (sharded per study) and `.cg-docs/research/scoping/` to the directory layout.
    Document the normative-decision entry schema (stable ID + study/plan scope +
    `applies_to` back-links — R13):
    ```
    ## ND-<study-slug>-001 — <short name>
    - study: <study-slug>
    - plan: <plan-file-slug or "none">
    - applies_to: [<scoping-memo path>, <plan step/section>, ...]
    - choice: <the value-laden decision>
    - defensible_options: [<option A>, <option B>, ...]
    - consequences: <who/what is affected; expected ranking/threshold shifts>
    - decided_by: <human name/role>            # never "default"
    - decision: <the chosen option>
    - justification: <why, in value terms>
    - decided_on: 2026-07-30
    ```
  - `cr-skill-research-integrity`: add a P0 error class **Normative-Choice
    Smuggling** in the existing "Error Class N" style — a value-laden choice
    (weighting, threshold, inclusion/exclusion, framing) presented as a technical
    default with no `normative-decisions.md` entry and no human decision.
    Detection: a consequential choice affecting results/rankings with
    `decided_by` absent or `= default`. Remediation: surface the choice, record
    defensible options + consequences, route to a human.
- **Test Scenarios:** normative schema (with ID + `study`/`plan` + `applies_to`) +
  smuggling P0 strings present; `.cg-docs/research/normative-decisions/` (sharded)
  + `.cg-docs/research/scoping` referenced.
- **Tests:** extend the research-workflow + research-integrity `Describe` blocks.
- **Acceptance:** V2 passes.

## Phase B: Gate Wiring

### 3. Add the normative gate to `/cr-brainstorm`

- **Requirements:** R4, R7, R9
- **Files:** [.github/prompts/cr-brainstorm.prompt.md](.github/prompts/cr-brainstorm.prompt.md)
- **Details:**
  - Add a **scoping + normative-surfacing** step after task classification: load
    `cr-skill-research-scoping`, draft/append the scoping memo, and
    **deterministically enumerate** the bounded, per-task-type taxonomy of
    value-laden decision points for the chosen task type (all types — R7, R11).
    This enumeration is workflow logic, not model inference — the prompt walks a
    fixed checklist so a choice cannot be silently skipped.
  - For each enumerated decision point, first check whether an existing decision
    ID already covers it (R12 coverage rule); if not, present defensible options +
    consequences and require an explicit human decision, recording it to the
    per-study shard `.cg-docs/research/normative-decisions/<study-slug>.md` with a
    stable ID + `applies_to` back-link (R13). Never auto-select (R9).
- **Test Scenarios:** references `cr-skill-research-scoping`, scoping memo, the
  bounded per-task-type decision-point enumeration, and the
  normative-decisions gate/approval.
- **Tests:** extend the `cr-brainstorm.prompt.md` content `Describe`.
- **Acceptance:** V3 passes.

### 4. Attach a normative-approval checkpoint to `/cr-plan` Step 4 (Present and Refine)

- **Requirements:** R4, R7, R9
- **Files:** [.github/prompts/cr-plan.prompt.md](.github/prompts/cr-plan.prompt.md)
- **Details:**
  - **`/cr-plan` has no completion-contract/approval seam** — its Step 4 is
    "Present and Refine" ("Present the plan. Ask for feedback. Revise if needed.",
    line ~94). The normative lock therefore attaches to that existing step as a
    lightweight approval checkpoint, **not** to a contract gate that does not exist.
  - In Step 4 (Present and Refine), add a **Normative Decisions** subsection: the
    plan must list the value-laden choices it commits to and reference their
    per-study `normative-decisions/<study-slug>.md` entries; the human's
    accept/refine response to the presented plan = approval of those choices. A
    plan that commits to a value-laden choice with no recorded human decision is
    surfaced as a P0 and cannot be presented as final until recorded.
  - Add a constraint template line so generated plans carry a normative-decision
    constraint where relevant.
- **Test Scenarios:** references normative decisions in the Present-and-Refine
  step; references the per-study register path.
- **Tests:** extend the `cr-plan.prompt.md` content `Describe`.
- **Acceptance:** V4 passes.

### 5. Add the mid-work re-escalation gate to `/cr-work`

- **Requirements:** R5, R6, R9
- **Files:** [.github/prompts/cr-work.prompt.md](.github/prompts/cr-work.prompt.md)
- **Details:**
  - **Step 2 active enforcement — "P0: Normative-Decision Gate"** (new
    subsection): before implementing a step, walk the bounded per-task-type
    decision-point taxonomy (R11/R12); for each point that the step touches, apply
    the coverage rule — if an existing decision ID in the per-study
    `normative-decisions/<study-slug>.md` shard already covers it, proceed; if the
    step introduces a value-laden choice **not** already recorded, halt and
    re-escalate to the human (mirror the seed/evidence P0 pattern). Do not default
    the choice. Record the resolved decision (with a stable ID + `applies_to`
    back-link) before proceeding.
  - **Graceful degradation (R15):** the gate runs on its own taxonomy even if the
    Phase-1 evidence spine or Phase-2 measurement flag is absent.
  - Reference `cr-skill-research-scoping` in the load list for scoping/normative
    reasoning.
- **Test Scenarios:** contains the normative-decision gate / re-escalation
  language, the coverage-rule check, and references the per-study
  `normative-decisions/` shard.
- **Tests:** extend the `cr-work.prompt.md - P0 enforcement` `Describe`.
- **Acceptance:** V5 passes.

### 6. Extend integrity-agent detection (reuse; no new agent)

- **Requirements:** R6, R8
- **Files:**
  [.github/agents/cr-research-integrity.agent.md](.github/agents/cr-research-integrity.agent.md),
  [.github/agents/cr-specification-analysis.agent.md](.github/agents/cr-specification-analysis.agent.md)
- **Details:**
  - **Agents are the audit backstop, not the primary gate (R11).** Primary
    prevention is the deterministic enumeration in `/cr-brainstorm` + `/cr-work`;
    the agents flag what is *visible in outputs/plans* but unrecorded — they cannot
    see a choice that was never surfaced.
  - `@cr-research-integrity`: add Normative-Choice Smuggling to its P0 detection
    responsibilities — scan outputs/plans for consequential value-laden choices
    lacking a matching entry (stable ID + human `decided_by`) in the per-study
    `normative-decisions/<study-slug>.md` shard.
  - `@cr-specification-analysis`: cross-reference the scoping memo + per-study
    normative register when auditing specification/decision documentation.
  - **No new agent** (R8) → **no count-sentinel change**; if review concludes a
    dedicated agent is unavoidable, escalate under `ask` before adding it (and
    then the full registration surface + sentinel bump would apply).
- **Test Scenarios:** both agents reference normative-choice smuggling / scoping.
- **Tests:** extend the agent `Describe` blocks in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1). No change to the
  agent count sentinel in
  [tests/model-assignments.Tests.ps1](tests/model-assignments.Tests.ps1).
- **Acceptance:** V6 passes.

## Phase C: Registration, Generation, Tests

### 7. Register skill + wire `/cr-review` (instructions + reference)

- **Requirements:** R6, R7, R10
- **Files:**
  [.github/copilot-instructions.md](.github/copilot-instructions.md),
  [.github/prompts/cr-review.prompt.md](.github/prompts/cr-review.prompt.md),
  [docs/reference.md](docs/reference.md)
- **Details:**
  - `copilot-instructions.md`: add `cr-skill-research-scoping` to **CR Skills**;
    note the Normative-Choice Smuggling P0 in the research-integrity summary.
  - `/cr-review`: ensure the normative-decisions audit runs via the (extended)
    `@cr-research-integrity` unconditional dispatch; for **Writing + Tables/Figures**
    tasks, require a scoping memo + decision register and have the review **compare
    the output's framing/inclusion/threshold choices against the recorded register**
    (R14), flagging any unrecorded consequential choice as P0 (closes the framing
    bypass).
  - `docs/reference.md`: add the scoping skill + normative-decision artifact where
    CR skills/artifacts are enumerated.
  - **No `model-catalog.json` / `model-guide.md` change** — no new agent (R8).
- **Test Scenarios:** instructions list the scoping skill; `/cr-review`
  references the normative audit.
- **Tests:** extend the relevant content `Describe` blocks.
- **Acceptance:** V7 passes.

### 8. Regenerate native target trees

- **Requirements:** R10
- **Files (generated):** `.agents/`, `.claude/`, `.opencode/`, `adapters/`
- **Details:** run `python3 scripts/cg_generate_targets.py --all`. Do **not**
  hand-edit generated files. If generation reports an unmapped asset, add the
  mapping in `.github/shared/target-mapping.json` and re-run.
- **Test Scenarios:** parity checks pass; no stray generated diffs.
- **Tests:** [tests/parity.Tests.ps1](tests/parity.Tests.ps1).
- **Acceptance:** V8 passes.

### 9. Run full test suite via safe runner

- **Requirements:** R10, C5
- **Files:** —
- **Details:** run `. tests\Run-Tests.ps1` and read `tests/last-run.json`.
  **Pester safety rules apply.** On this macOS host PowerShell is not installed
  (exit 127); if it cannot run here, hand V8/V9 to the user or an
  `execution_subagent`.
- **Test Scenarios:** all `Describe` blocks green; new scoping/normative tests
  pass.
- **Tests:** whole suite.
- **Acceptance:** V9 passes (0 failures in `tests/last-run.json`).

## Testing Strategy

- **Static/contract tests (Pester):** frontmatter + content for the scoping
  skill; normative schema (ID + `study`/`plan` + `applies_to`) + smuggling P0
  strings; gate wiring in `/cr-brainstorm`, `/cr-plan` (Present-and-Refine),
  `/cr-work`; the bounded per-task-type decision-point taxonomy; extended
  integrity-agent detection; instructions/reference sync; parity. **No
  count-sentinel change** (no new agent). Static grep proves the gate is
  **documented and wired**, not that it is runtime-unbypassable — the contract
  claim is scoped accordingly.
- **Behavioral fixture tests (downstream-required; PowerShell absent locally):**
  add fixtures exercising the gate's decision logic — (a) a value-laden choice
  with **no** recorded approval must block/escalate; (b) a **reused** decision ID
  that legitimately covers the step must pass without re-escalation; (c) a
  **new** choice not covered by any ID must re-escalate. These prove "cannot be
  auto-satisfied" behaviorally; mark them downstream-required and attach
  `tests/last-run.json` from a PowerShell-capable env.
- **Behavioral validation (manual, post-merge):** run `/cr-brainstorm` on a
  measurement question and confirm a scoping memo + normative-decision entries
  are produced and a value-laden choice cannot be auto-defaulted; run `/cr-work`
  and confirm a newly-introduced normative choice re-escalates; run `/cr-review`
  and confirm smuggling is flagged P0.
- **Runner:** always the canonical `. tests\Run-Tests.ps1` → `tests/last-run.json`.

## Documentation Checklist

- [ ] Scoping skill self-documents the memo + normative-decision schemas.
- [ ] `copilot-instructions.md` CR Skills + integrity summary updated.
- [ ] `cr-skill-research-workflow` layout (scoping/ + per-study normative-decisions/).
- [ ] `docs/reference.md` updated where CR skills/artifacts are enumerated.
- [ ] All new files carry a creation date (`date:` frontmatter or header).

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Gate becomes noise (fires on trivial choices) | Scope to *consequential* value-laden choices (affecting results/rankings/inclusion); tie severity to review tier. |
| Reuse path insufficient → pressure to add an agent | R8/Step 6 default is reuse; adding an agent is escalated under `ask` and would pull in the full [P2.1] surface + sentinel bump. |
| Human-approval requirement bypassed by auto-default | R9/C2: `decided_by` cannot be `default`; smuggling P0 detects the bypass; V10 fixtures prove it behaviorally. |
| Bounded decision-point taxonomy misses a novel value-laden choice | Agents (backstop) flag consequential unrecorded choices visible in outputs; the taxonomy is versioned in the skill and extended when a gap is found. |
| Regeneration touches many files | Run generator once, review diff; never hand-edit generated trees; stop + report if scope widens. |
| PowerShell unavailable on macOS host blocks V8/V9/V10 | Defer to user or `execution_subagent`; all edits static/reviewable. |
| Overlap with Phase 2 weighting-disclosure flag | Phase 2 *flags* undisclosed weighting; Phase 3 turns the flag into a recorded human decision — complementary, not duplicated. |

## Out of Scope

- Measurement/Classification archetype + comparability controls (Phase 2) — this
  phase consumes measurement's "undisclosed weighting" flag but does not build
  the measurement skill/agent.
- Method-pack retrofit / lifecycle orchestration (Phase 4).
- The actual research analysis.
- Second measurement use-case validation; team evidence library.
- A new dedicated normative-audit agent (reuse existing agents unless review
  proves one unavoidable).

## Completion Contract

### Outcome

CR gains a scoping front-end and a normative-decision gate backbone — a scoping
skill + memo, a `normative-decisions.md` artifact, human-approval gates at
`/cr-brainstorm` and `/cr-plan`, a mid-work re-escalation gate in `/cr-work`, and
active P0 detection of normative-choice smuggling (via extended existing agents)
— so consequential value judgments are visible, contestable, and recorded rather
than silently defaulted. No new agent; native targets regenerated; full Pester
suite green.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | A | `cr-skill-research-scoping/SKILL.md` exists, `module: research`, covers framing/frames/priors/success-criteria + scoping-memo path + the bounded per-task-type decision-point taxonomy | file + grep | yes |
| V2 | A | `cr-skill-research-workflow` documents the per-study `normative-decisions/` schema (ID + `study`/`plan` + `applies_to`) + `scoping/`; `cr-skill-research-integrity` has the Normative-Choice Smuggling P0 | grep | yes |
| V3 | B | `/cr-brainstorm` deterministically enumerates value-laden decision points + records human approvals to the per-study shard | grep | yes |
| V4 | B | `/cr-plan` Step 4 (Present and Refine) locks value-laden choices to the per-study `normative-decisions/` register | grep | yes |
| V5 | B | `/cr-work` has the P0 normative re-escalation gate with the coverage-rule check | grep | yes |
| V6 | B | `@cr-research-integrity` (+`@cr-specification-analysis`) audit the recorded register for normative-choice smuggling (backstop, not primary gate) | grep | yes |
| V7 | C | `copilot-instructions.md` lists the scoping skill + smuggling P0; `/cr-review` compares Writing/Tables outputs against the register; `docs/reference.md` updated | grep | yes |
| V8 | final | Multi-target regeneration run; parity holds | `python3 scripts/cg_generate_targets.py --all` + `parity.Tests.ps1` | yes (downstream) |
| V9 | final | Full Pester suite green via safe runner — **downstream-required** (PowerShell absent locally; attach `tests/last-run.json` from a PowerShell-capable env) | `. tests\Run-Tests.ps1` → `tests/last-run.json` | yes (downstream) |
| V10 | final | Behavioral fixtures prove the gate cannot be auto-satisfied (missing-approval blocks; reused-ID passes; new-choice escalates) — **downstream-required** | fixture tests in `tests/cr-prompts.Tests.ps1` → `tests/last-run.json` | yes (downstream) |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No regression in existing CR agents/prompts/skills | existing `cr-prompts.Tests.ps1` + `model-assignments.Tests.ps1` stay green |
| C2 | Human decides; `decided_by` never `default`; gate cannot be auto-satisfied (behaviorally proven by the V10 fixtures — static review proves only wiring) | schema + prompt text review + V10 fixtures (downstream) |
| C3 | No new agent (reuse existing) → agent count sentinel unchanged | `model-assignments.Tests.ps1` sentinel stays 26 (or Phase-2 value) |
| C4 | Engineering-only projects unaffected (research gating preserved) | `module: research` on all new/changed surfaces |
| C5 | Pester run only via the canonical safe runner | no directory runs / no `-PassThru` pipelines |

### Boundaries

- **In:** the scoping skill + memo, `normative-decisions.md` schema + smuggling
  P0, gate wiring in `/cr-brainstorm` + `/cr-plan` + `/cr-work`, extended
  detection in existing integrity agents, instructions/reference sync, and target
  regeneration.
- **Out:** measurement archetype (Phase 2), method-pack retrofit (Phase 4), the
  actual research, second-use-case validation, team evidence library, a new
  dedicated normative-audit agent.

### Iteration Policy

1. `deviation-policy: ask` — surface required deviations before acting.
2. If a test names an extra registration surface, update exactly that surface and
   re-run.
3. If the reuse path proves insufficient and a new agent seems required, **stop
   and escalate** (adding an agent changes the count sentinel + registration
   surface).

### Blocked-Stop Conditions

- Pester cannot be run through the safe runner (PowerShell not installed on this
  Mac — may defer V8/V9 to the user or a subagent).
- Parity fails after regeneration and cannot be reconciled.
- A required deviation (including "add a new agent") is discovered under `ask`
  without user approval.
- Any required verification item fails after allowed recovery attempts.
