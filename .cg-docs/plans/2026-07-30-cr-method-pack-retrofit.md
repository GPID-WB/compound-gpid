---
date: 2026-07-30
title: "CR Method-Pack Retrofit + Lifecycle Orchestration (Responsible Research Partner — Phase 4)"
status: completed
completed-date: 2026-07-31
scope: Deep
brainstorm: ".cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md"
language: "PowerShell/Markdown"
estimated-effort: large
deviation-policy: ask
execution-report: ".cg-docs/work-reports/2026-07-31-cr-method-pack-retrofit.md"
completed-phases: [1, 2, 3]
current-phase: 3
failing-steps: []
tags: [compound-research, responsible-ai, refactor, method-packs, lifecycle, orchestration, backward-compatibility]
---

# CR Method-Pack Retrofit + Lifecycle Orchestration (Responsible Research Partner — Phase 4)

## Objective

Refactor CR's existing method-specific flows (structural econometrics, ML) into
interchangeable **method packs** running under a single **responsible research
lifecycle**, and converge `/cr-review` dispatch onto that model — so the
responsible-AI backbone built in Phases 1–3 (evidence/provenance, measurement
integrity, normative gates) is applied **structurally and uniformly** rather than
duplicated per method.

Concretely, this phase delivers:

- A documented **unified lifecycle**: `Scope → Evidence → Theory → Method →
  Execute → Verify → Communicate → Maintain`, with the (now 9) task types and
  existing skills/agents mapped onto its stages.
- A **method-pack** model — expressed as **documentation cross-linking** — that
  describes the structural-econometrics and ML flows as packs under the shared
  lifecycle, **without changing their existing behavior** and without moving any
  files. Fuller pack framing (routing changes) is deferred until Phases 1–3 are
  merged and participating (P3.1).
- `/cr-review` dispatch **augmented** with lifecycle/pack framing **around** the
  existing task-type dispatch table, preserving every existing agent-routing
  assertion verbatim (additive, not a rewrite).
- A final regression + parity pass, certifiable only in a PowerShell-capable
  environment (attached as an external merge-gate artifact — see V6/V7).

This is Phase 4 — the coherence/consolidation investment — of the CR expansion
from a journal-paper econometrics assistant into a responsible partner for the
full research lifecycle of policy-relevant measurement work.

## Context

The brainstorm
([2026-07-30-cr-responsible-research-partner-measurement.md](.cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md))
placed the method-pack retrofit **last** on purpose: Phases 1–3 add capability
(evidence, measurement, normative gates) as parallel surfaces; Phase 4 pays down
the resulting coherence debt by giving all methods one lifecycle spine and one
dispatch model. Because Phases 1–3 already touched the workflow taxonomy,
integrity catalog, and review dispatch, this phase is primarily a
**structure-preserving refactor** — the highest-regression-risk phase, so it is
sequenced where the surfaces are most stable.

Locked design decisions (from the brainstorm) this plan must honor:

- The lifecycle spine is `Scope → Evidence → Theory → Method → Execute → Verify
  → Communicate → Maintain`.
- Structural econometrics and ML become **method packs** under that spine.
- `/cr-review` dispatch **converges** on the pack model.
- This is a **refactor**: existing structural/ML behavior and every existing
  test assertion must remain green (strict backward compatibility).

### Cross-cutting lessons folded in from the Phase 1 review

- **[P2.1] Registration surface.** If any agent is renamed/moved/regrouped, the
  full surface applies (`copilot-instructions.md`, `model-catalog.json`,
  `docs/model-guide.md`, `docs/reference.md`, the **count sentinel**, and the
  hardcoded CR-agent arrays in `cr-prompts.Tests.ps1`). Default: **do not
  rename/move agents** — reorganize *documentation and dispatch*, not files.
- **[P2.2] Verification realism.** Local-static grep/JSON checks are separated
  from downstream Pester (PowerShell absent on this macOS host). Backward-compat
  is proven by the existing suite staying green — which can only be confirmed
  where Pester runs.
- **[P3.1]** `skills-lock.json` is not a registration surface.

### Hard prerequisites (Phases 1–3 must be merged first)

This phase **consolidates** surfaces that Phases 1–3 create; it does not create
them. Phase 4 is therefore **blocked** until Phases 1–3 are merged:

- **Phase 1 (evidence/provenance)** must have landed `cr-skill-evidence-provenance`
  + `@cr-provenance-audit` and the evidence P0 gate.
- **Phase 2 (measurement)** must have landed the **9th task type
  (Measurement/Classification)**, `cr-skill-measurement`, and
  `@cr-measurement-integrity`. **The 9-type taxonomy is owned by Phase 2 — this
  plan assumes it and does not perform the 8→9 migration** (P2.2).
- **Phase 3 (scoping/normative)** must have landed `cr-skill-research-scoping` +
  the normative gate.

**Gate rule:** at the start of each step, verify the surfaces it references exist;
if a referenced Phase-1/2/3 surface is **absent**, **stop and report** (do not
invent it, do not partially wrap it). See Blocked-Stop Conditions.

### Relevant existing surfaces (researched)

- `cr-skill-research-workflow` holds the task taxonomy + `/cr-review` dispatch
  concept ([cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md)).
- `/cr-review` has the task-type → agent dispatch table
  ([cr-review.prompt.md](.github/prompts/cr-review.prompt.md)); its assertions in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1) include per-row routing
  checks (e.g. Theory/Modeling → `@cr-identification-audit` + `@cr-econometric-reasoning`;
  Tables/Figures → `@cr-publication-output`) and a "dispatch table covers all N
  task types" array. **These must all still pass unchanged.**
- Structural/ML skills + agents: `cr-skill-structural-econometrics`,
  `cr-skill-ml-economics`, `@cr-econometric-reasoning`, `@cr-identification-audit`,
  `@cr-ml-methodology`.
- `/cr-work` + `/cr-brainstorm` reference the workflow taxonomy and would
  reference the lifecycle spine.
- Native target trees generated by
  [scripts/cg_generate_targets.py](scripts/cg_generate_targets.py).

## Requirements

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Document the unified lifecycle spine (8 stages) in `cr-skill-research-workflow` | Brainstorm (locked) |
| R2 | Map the 9 task types (9th owned by Phase 2 — assumed, not created here) + existing skills/agents onto lifecycle stages | Brainstorm; Phase-4 review [P2.2] |
| R3 | Express structural-econometrics + ML flows as method packs under the spine | Brainstorm (locked) |
| R4 | Add lifecycle/pack framing *around* the `/cr-review` dispatch table (additive; existing routing table untouched) | Brainstorm (locked); Phase-4 review [P1.2] |
| R5 | `/cr-work` + `/cr-brainstorm` reference the unified lifecycle | Brainstorm |
| R6 | Strict backward compatibility: existing behavior + every existing assertion unchanged | Brainstorm (locked); refactor discipline |
| R7 | Do not rename/move agent files (avoid the full registration-surface churn) unless unavoidable | Phase-1 review [P2.1] |
| R8 | Docs synced (`reference.md`; `model-guide.md` only if agents move) | Model governance; [P2.1] |
| R9 | Research-module gating preserved | Charter; module convention |
| R10 | Targets regenerated; full Pester suite green (no regression) | Parity tests; [P2.2] |
| R11 | Phase 4 is **blocked on Phases 1–3 merged**; each step verifies its referenced surface exists and stops if absent | Phase-4 review [P1.1/P2.2] |
| R12 | Scope this phase to **minimal lifecycle cross-linking** (documentation); defer fuller pack framing / routing changes until Phases 1–3 are merged and participating | Phase-4 review [P3.1] |

## Implementation Steps

> Globally-numbered steps grouped into three internal phases. `/cg-work phaseA`,
> `phaseB`, `phaseC` may be used to execute a single phase.

## Phase A: Lifecycle Spine + Pack Mapping

### 1. Document the unified lifecycle spine

- **Requirements:** R1, R2
- **Files:**
  [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md)
- **Details:**
  - Add a **Responsible Research Lifecycle** section defining the eight stages
    `Scope → Evidence → Theory → Method → Execute → Verify → Communicate →
    Maintain`, and for each stage list the responsible surface(s):
    - Scope → `cr-skill-research-scoping` + normative gate (Phase 3)
    - Evidence → `cr-skill-evidence-provenance` + `@cr-provenance-audit` (Phase 1)
    - Theory → `cr-skill-structural-econometrics` / `cr-skill-mathematical-derivation`
    - Method → the method pack (structural / ML / measurement)
    - Execute → `/cr-work` P0 gates (seed, evidence, measurement, normative)
    - Verify → `/cr-review` agents + `@cr-mathematical-verification`
    - Communicate → `cr-skill-academic-writing` / `cr-skill-publication-output`
    - Maintain → `cr-skill-replication-standards` + vintages
  - Map all **9 task types** onto the stages (additive — do not remove or rename
    task types).
- **Test Scenarios:** lifecycle section present with all 8 stage names; existing
  taxonomy strings unchanged.
- **Tests:** new `It`s for the lifecycle stages in the research-workflow
  `Describe`; **existing** task-type assertions still pass.
- **Acceptance:** V1 passes; no existing assertion regresses.

### 2. Define the method-pack model

- **Requirements:** R3, R6, R7
- **Files:**
  [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md)
- **Details:**
  - Add a **Method Packs** subsection describing a pack as "a Theory+Method+Verify
    bundle plugged into the shared lifecycle", and register the existing flows as
    packs **by reference to their current files** (no file moves — R7):
    - **Structural pack** → `cr-skill-structural-econometrics`,
      `@cr-econometric-reasoning`, `@cr-identification-audit`.
    - **ML pack** → `cr-skill-ml-economics`, `@cr-ml-methodology`.
    - **Measurement pack** → `cr-skill-measurement`, `@cr-measurement-integrity`
      (Phase 2).
  - State that packs share the same Scope/Evidence/Normative/Verify/Communicate
    stages — the responsible backbone is not re-implemented per pack.
  - **Scope discipline (P3.1):** this is **documentation cross-linking only** — no
    routing changes, no new dispatch behavior, no file moves. Fuller pack framing
    (packs participating in routing) is explicitly deferred to a later phase once
    Phases 1–3 are merged and exercised.
- **Test Scenarios:** Method Packs subsection names the three packs and maps each
  to its existing skill/agent files.
- **Tests:** new `It`s in the research-workflow `Describe`.
- **Acceptance:** V2 passes.

## Phase B: Dispatch Convergence

### 3. Add lifecycle/pack framing *around* the existing `/cr-review` dispatch table

- **Requirements:** R4, R6
- **Files:** [.github/prompts/cr-review.prompt.md](.github/prompts/cr-review.prompt.md)
- **Details:**
  - **Do not edit the existing task-type → agent dispatch table.** Its rows are
    matched by hardcoded per-row regex assertions and a "dispatch table covers all
    N task types" array in [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1)
    (e.g. Theory/Modeling → `@cr-identification-audit` + `@cr-econometric-reasoning`;
    ML/Prediction → `@cr-ml-methodology`; Measurement/Classification →
    `@cr-measurement-integrity`; Tables/Figures → `@cr-publication-output`).
    Editing the table risks breaking those regexes.
  - Instead, add a **new, additive** "Lifecycle & Method Packs" subsection
    *above/around* the table that (a) names the eight lifecycle stages, (b) groups
    the existing task types under Method-pack headings for orientation, and (c)
    notes that unconditional stages (Scope/Evidence/Verify) apply to every pack.
    The existing table remains the single source of routing truth, verbatim.
- **Test Scenarios:** every existing per-row routing assertion still matches
  **byte-for-byte**; the "dispatch table covers all N task types" array still
  matches; the new framing is additive.
- **Tests:** run the existing `cr-review` dispatch `Describe` unchanged; add at
  most additive `It`s for the lifecycle framing (do not alter existing ones).
- **Acceptance:** V3 passes; **zero** existing dispatch assertions regress.

### 4. Reference the lifecycle in `/cr-work` + `/cr-brainstorm`

- **Requirements:** R5, R6
- **Files:**
  [.github/prompts/cr-work.prompt.md](.github/prompts/cr-work.prompt.md),
  [.github/prompts/cr-brainstorm.prompt.md](.github/prompts/cr-brainstorm.prompt.md)
- **Details:**
  - `/cr-work`: add a one-paragraph note that its P0 gates (seed, evidence,
    measurement, normative) are the **Execute**-stage enforcement of the shared
    lifecycle; map each existing gate to its stage. No gate behavior changes.
  - `/cr-brainstorm`: note that task classification selects a **method pack**
    within the lifecycle. No classifier behavior changes.
- **Test Scenarios:** both prompts reference the lifecycle; no existing behavior
  assertion regresses.
- **Tests:** additive `It`s; existing `Describe`s unchanged.
- **Acceptance:** V4 passes.

## Phase C: Docs, Generation, Tests

### 5. Sync docs

- **Requirements:** R8, R9
- **Files:**
  [.github/copilot-instructions.md](.github/copilot-instructions.md),
  [docs/reference.md](docs/reference.md)
- **Details:**
  - `copilot-instructions.md`: add a short **Responsible Research Lifecycle**
    note to the CR module section listing the eight stages and the three method
    packs (documentation only — no agent list change unless an agent moved).
  - `docs/reference.md`: document the lifecycle + packs where CR is described.
  - **No `model-catalog.json` / `model-guide.md` change** unless an agent file
    was renamed/moved (default: none — R7).
- **Test Scenarios:** instructions + reference mention the lifecycle/packs.
- **Tests:** extend the relevant content `Describe` blocks; count sentinels
  unchanged.
- **Acceptance:** V5 passes.

### 6. Regenerate native target trees

- **Requirements:** R9, R10
- **Files (generated):** `.agents/`, `.claude/`, `.opencode/`, `adapters/`
- **Details:** run `python3 scripts/cg_generate_targets.py --all`. Do **not**
  hand-edit generated files. If generation reports an unmapped asset, add the
  mapping in `.github/shared/target-mapping.json` and re-run.
- **Test Scenarios:** parity checks pass; no stray generated diffs.
- **Tests:** [tests/parity.Tests.ps1](tests/parity.Tests.ps1).
- **Acceptance:** V6 passes.

### 7. Run full test suite via safe runner (regression gate)

- **Requirements:** R6, R10, C4
- **Files:** —
- **Details:** run `. tests\Run-Tests.ps1` and read `tests/last-run.json`.
  **Pester safety rules apply.** Because this phase is a refactor, the pass/fail
  bar is **zero regressions** in the existing suite. On this macOS host
  PowerShell is not installed (exit 127); if it cannot run here, hand V6/V7 to
  the user or an `execution_subagent` — backward-compat cannot be certified
  without a green run.
- **Test Scenarios:** all `Describe` blocks green; **no** previously-passing
  assertion now fails.
- **Tests:** whole suite.
- **Acceptance:** V7 passes (0 failures in `tests/last-run.json`).

## Testing Strategy

- **Regression-first (Pester):** the primary bar is that the **entire existing
  suite stays green**; new `It`s are strictly additive (lifecycle stages, pack
  names, lifecycle references) and never replace existing routing/behavior
  assertions. **This bar is certifiable only where PowerShell runs** — on this
  macOS host it is deferred to a downstream merge-gate (attach a green
  `tests/last-run.json`); it is not a claim this plan can close locally.
- **Behavioral validation (manual, post-merge):** run `/cr-review` on a
  structural, an ML, and a measurement task and confirm identical agent routing
  to pre-refactor; spot-check `/cr-work` gate behavior is unchanged.
- **Runner:** always the canonical `. tests\Run-Tests.ps1` → `tests/last-run.json`.

## Documentation Checklist

- [ ] `cr-skill-research-workflow` documents the lifecycle + method packs.
- [ ] `copilot-instructions.md` + `docs/reference.md` describe the lifecycle/packs.
- [ ] No agent file renamed/moved (so no `model-guide.md`/catalog/sentinel churn).
- [ ] All edited files retain accurate dates; this plan carries `date:`.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Refactor silently changes agent routing → regression | R6/C1: routing pairs are preserved verbatim; existing dispatch `Describe` runs unchanged; zero-regression bar. |
| Temptation to rename/reorganize agent files | R7/C2: default is no file moves; a move triggers the full [P2.1] surface + sentinel and must be escalated under `ask`. |
| Lifecycle framing contradicts an existing "8/9 task types" assertion | Additive only; existing taxonomy strings left intact; new `It`s don't replace old ones. |
| Regeneration touches many files | Run generator once, review diff; never hand-edit generated trees; stop + report if scope widens. |
| PowerShell unavailable on macOS host blocks the regression gate | Backward-compat cannot be certified locally; defer V6/V7 to user or `execution_subagent` and flag as blocking for merge. |
| Depends on Phases 1–3 surfaces not yet merged | **Hard prerequisite (R11/C5):** Phase 4 is blocked until Phases 1–3 merge; each step verifies its referenced surface and **stops** if absent — no "forthcoming" placeholders. |

## Out of Scope

- New method packs (Bayesian, causal-ML) — only structural, ML, and measurement
  are wrapped.
- New archetypes or task types (Phase 2 added the last one).
- Any behavior change to existing structural/ML/measurement flows.
- Governance features: second measurement use-case validation; team evidence
  library.
- Agent file renames/moves (kept out unless review proves unavoidable).

## Completion Contract

### Outcome

CR's structural-econometrics, ML, and measurement flows are expressed as
interchangeable method packs under a single documented lifecycle
(`Scope → Evidence → Theory → Method → Execute → Verify → Communicate →
Maintain`), and `/cr-review` dispatch is reorganized onto that model with **every
existing routing preserved** — so the responsible-AI backbone is structural, not
duplicated. No agent files moved; native targets regenerated; and the
zero-regression guarantee is delivered as an **external merge-gate artifact** (a
green `tests/last-run.json` from a PowerShell-capable environment), since it
cannot be certified on this macOS host.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | A | `cr-skill-research-workflow` has the 8-stage lifecycle section; existing taxonomy unchanged | grep | yes |
| V2 | A | Method Packs subsection names structural / ML / measurement packs mapped to existing files | grep | yes |
| V3 | B | `/cr-review` reorganized onto lifecycle/packs; **all existing per-row routing + "all N task types" assertions still pass** | grep + test | yes |
| V4 | B | `/cr-work` + `/cr-brainstorm` reference the lifecycle; no behavior assertion regresses | grep | yes |
| V5 | C | `copilot-instructions.md` + `docs/reference.md` describe the lifecycle/packs | grep | yes |
| V6 | final | Multi-target regeneration run; parity holds — **downstream merge-gate** (PowerShell absent locally; attach `parity.Tests.ps1` result from a PowerShell-capable env) | `python3 scripts/cg_generate_targets.py --all` + `parity.Tests.ps1` | yes (downstream) |
| V7 | final | Full existing Pester suite green — **zero regressions** — as an **external merge-gate artifact**; attach `tests/last-run.json` from a PowerShell-capable env (uncertifiable on this macOS host) | `. tests\Run-Tests.ps1` → `tests/last-run.json` | yes (downstream) |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | Strict backward compatibility — existing behavior + every existing assertion unchanged | full existing suite green |
| C2 | No agent file renamed/moved (no catalog/model-guide/sentinel churn) | `git status` shows no agent-file renames; sentinels unchanged |
| C3 | Engineering-only projects unaffected (research gating preserved) | `module: research` on changed surfaces |
| C4 | Pester run only via the canonical safe runner | no directory runs / no `-PassThru` pipelines |
| C5 | Phase 4 proceeds only after Phases 1–3 are merged; the 9-type taxonomy is assumed (owned by Phase 2), not created here | referenced surfaces present before each step; stop if absent |

### Boundaries

- **In:** the lifecycle + method-pack documentation in `cr-skill-research-workflow`,
  `/cr-review` dispatch reorganization (routing-preserving), lifecycle references
  in `/cr-work` + `/cr-brainstorm`, docs sync, and target regeneration.
- **Out:** new method packs, new task types, any behavior change, agent file
  moves, governance features.

### Iteration Policy

1. `deviation-policy: ask` — refactor risk is high; surface any behavior-changing
   deviation **immediately**.
2. If a change would alter an existing routing/behavior assertion, **stop** — the
   refactor must be presentation-only.
3. If regeneration touches unexpected files, stop and report before continuing.

### Blocked-Stop Conditions

- **Phases 1–3 are not all merged** (their surfaces — evidence spine, 9th task
  type + measurement pack, scoping/normative gate — are absent). Phase 4
  consolidates those surfaces and cannot proceed without them; **stop and report**.
- A referenced Phase-1/2/3 surface is absent at a given step (do not invent or
  partially wrap it) — stop and report.
- Any previously-passing assertion regresses and cannot be reconciled without a
  behavior change.
- A required change would rename/move an agent file (escalate under `ask`).
- Pester cannot be run through the safe runner (PowerShell not installed on this
  Mac — backward-compat uncertifiable locally; defer V6/V7 and flag as
  merge-blocking).
- Parity fails after regeneration and cannot be reconciled.
