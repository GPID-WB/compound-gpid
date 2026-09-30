---
date: 2026-07-30
title: "CR Measurement/Classification Archetype + Comparability Controls (Responsible Research Partner — Phase 2)"
status: completed
completed-date: 2026-07-31
scope: Deep
brainstorm: ".cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md"
language: "PowerShell/Markdown"
estimated-effort: large
deviation-policy: ask
execution-report: ".cg-docs/work-reports/2026-07-31-cr-measurement-classification-archetype.md"
completed-phases: [1, 2, 3]
current-phase: 3
failing-steps: []
tags: [compound-research, responsible-ai, measurement, classification, composite-indicators, comparability, vintages, p0]
---

# CR Measurement/Classification Archetype + Comparability Controls (Responsible Research Partner — Phase 2)

## Objective

Give the Compound Research (CR) module a first-class **Measurement/Classification**
research archetype — the **9th research task type** — so that composite-indicator,
clustering, and threshold-classification work (the core of policy-relevant
measurement) is held to the same integrity bar as structural econometrics.

Concretely, this phase delivers:

- A methodology skill (`cr-skill-measurement`) grounded in cited standards
  (OECD/JRC composite-indicator handbook, Alkire-Foster multidimensional
  measurement, cluster-validity theory) covering weighting sensitivity, index
  construction, thresholding, and classification validity.
- A verification agent (`@cr-measurement-integrity`) that audits the five
  measurement failure modes: undisclosed weighting, unstable rankings,
  coverage/vintage artifacts, spurious clusters, and broken comparability.
- Registration of **Measurement/Classification** as the 9th task type across the
  classifier, workflow taxonomy, review dispatch, and every hardcoded test
  assertion that currently asserts "all 8 task types".
- **Comparability P0s** (over time **and** across units) plus vintage-versioning
  and change-attribution artifacts under `.cg-docs/research/vintages/`.
- Workflow enforcement in `/cr-work` and dispatch wiring in `/cr-review`.

This is Phase 2 of the CR expansion from a journal-paper econometrics assistant
into a responsible partner for the full research lifecycle of policy-relevant
measurement work.

## Context

The brainstorm
([2026-07-30-cr-responsible-research-partner-measurement.md](.cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md))
selected **Approach 3 (phased, value-first)** and identified Measurement as the
first *new archetype* after the Phase 1 evidence spine. The World Bank
poverty-measurement context makes measurement/classification the highest-value
proving ground: composite indices, poverty thresholds, and country
classifications are consequential, comparison-heavy, and full of hidden
normative choices (weighting, aggregation, cutoffs).

Locked design decisions (from the brainstorm) this plan must honor:

- Measurement/Classification is registered as a **first-class task type**, not a
  sub-case of EDA or Implementation.
- The measurement skill is **grounded in cited, established methodology** (it
  does not reinvent index theory).
- **Comparability is a P0** in two directions: over time and across units.
- Apparent changes must carry **change-attribution** (real change vs
  coverage/vintage/methodology artifact); vintages are **versioned**.
- Verification depth is proportional to the review tier.

### Cross-cutting lessons folded in from the Phase 1 review

- **[P1.1] Agents cannot compute at runtime.** `@cr-measurement-integrity` is a
  read/search agent; it **audits disclosures and artifacts produced by
  `/cr-work`** (weighting-sensitivity tables, cluster-validity outputs, vintage
  manifests) — it does **not** itself run stability/validity computations. The
  computations are the responsibility of `/cr-work` (or a helper it invokes).
- **[P2.1] Full registration surface.** Adding an agent touches, at minimum:
  `copilot-instructions.md` (CR Agents + CR Skills lists), `model-catalog.json`,
  `docs/model-guide.md` (**Agents** assignment table), `docs/reference.md` (if it
  enumerates), the **agent count sentinel** in `model-assignments.Tests.ps1`
  (`Should -Be 26` → `27`), and the hardcoded CR-agent assertions in
  `cr-prompts.Tests.ps1`.
- **[P2.2] Verification realism.** Grep-of-prompt-text proves the text exists,
  not the behavior. Local-static checks (grep/JSON) are separated from
  downstream Pester (which cannot run on this macOS host — PowerShell absent).
- **[P3.1]** `skills-lock.json` is **not** listed as a registration surface (no
  verified consumer).

### Relevant existing surfaces (researched)

- The 8 task types are hardcoded in multiple places. Confirmed sites:
  - [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md)
    — taxonomy list.
  - [.github/prompts/cr-brainstorm.prompt.md](.github/prompts/cr-brainstorm.prompt.md)
    Step 1.1 (lines ~34–54) — classifier list + per-type skill-load mapping
    ("one of the 8 research task types").
  - [.github/prompts/cr-review.prompt.md](.github/prompts/cr-review.prompt.md)
    — task-type → agent dispatch table.
  - [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1) — **two** "all 8
    task types" assertions (≈ line 310 "contains all 8 task types"; ≈ line 2427
    "dispatch table covers all 8 task types" with a hardcoded 8-element array).
  - [.github/prompts/cr-plan.prompt.md](.github/prompts/cr-plan.prompt.md) line
    ≈ 63 — the research-plan frontmatter template **hardcodes the `task-type:`
    enum** `"<Theory/Modeling|…|Reproducibility>"` (8 values). **CONFIRMED via
    review.** The 9th type must be added here or Measurement/Classification plans
    cannot flow through `/cr-plan → /cr-work → /cr-review`.
  - [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1) also has **two
    hardcoded `$crAgents` arrays** (structural checks ≈ line 409; `module:
    research` checks ≈ line 864) enumerating all CR agents — **both** must gain
    `cr-measurement-integrity`. **CONFIRMED via review.**
- CR agents follow the frontmatter pattern: `description`, `model: GPT-5.4`,
  `tools: ['read', 'search']`, `user-invocable: false`, `module: research`, plus
  the untrusted-content note for `.cg-docs/research/` files (see
  [cr-research-integrity.agent.md](.github/agents/cr-research-integrity.agent.md)).
- [tests/model-assignments.Tests.ps1](tests/model-assignments.Tests.ps1) has an
  **agent count sentinel** (`$agentFiles.Count | Should -Be 26`, line ≈ 84) and a
  prompt count sentinel (`Should -Be 30`, line ≈ 48).
- [docs/model-guide.md](docs/model-guide.md) has an **Agents** assignment table
  (`| File | Model | Role | Rationale |`, lines ≈ 125–143).
- Native target trees are generated by
  [scripts/cg_generate_targets.py](scripts/cg_generate_targets.py).

## Requirements

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Register Measurement/Classification as the 9th first-class task type, everywhere the 8 are enumerated | Brainstorm (locked) |
| R2 | `cr-skill-measurement` grounded in cited methodology (OECD/JRC, Alkire-Foster, cluster validity) | Brainstorm (locked) |
| R3 | `@cr-measurement-integrity` audits 5 failure modes: weighting disclosure, ranking stability, coverage/vintage artifact, spurious cluster, comparability | Brainstorm |
| R4 | Comparability is P0 in two directions (over time + across units) | Brainstorm (locked) |
| R5 | Vintage versioning + change-attribution artifacts under `.cg-docs/research/vintages/` | Brainstorm (locked) |
| R6 | Agent audits artifacts produced by `/cr-work`; it does not compute statistics itself | Phase-1 review [P1.1] |
| R7 | Verification depth proportional to review tier | Brainstorm (locked) |
| R8 | Wire agent into `/cr-review`; wire skill + comparability enforcement into `/cr-work` | Brainstorm |
| R9 | Research-module gating preserved; engineering-only projects unaffected | Charter; module convention |
| R10 | New agent GPT-5.4; full registration surface synced; sentinels bumped; targets regenerated; tests green | Model governance; parity tests; [P2.1] |
| R11 | Define artifact paths + schemas for weighting-sensitivity and cluster-validity outputs so the agent can audit (not compute) them | Plan review [P1.3/P1.4] |
| R12 | `/cr-review` dispatch scoped to task type / reviewed files, not repo-wide artifact presence | Plan review [P2.2] |

## Implementation Steps

> Globally-numbered steps grouped into three internal phases. `/cg-work phaseA`,
> `phaseB`, `phaseC` may be used to execute a single phase.

## Phase A: Methodology + Taxonomy

### 1. Create `cr-skill-measurement`

- **Requirements:** R2, R6, R7
- **Files:** `.github/skills/cr-skill-measurement/SKILL.md` (new)
- **Details:**
  - Frontmatter: `name: cr-skill-measurement`, `module: research`,
    `description:` (progressive-disclosure — load for any CR task that builds a
    composite index, clusters/classifies units, sets thresholds, or ranks units).
  - Sections, each anchored to a **cited** methodology (name the source; do not
    reinvent):
    1. **Composite indicators** — OECD/JRC *Handbook on Constructing Composite
       Indicators* ten-step workflow: normalization choices, weighting schemes
       (equal, expert/budget-allocation, data-driven), aggregation (linear vs
       geometric and their compensability implications), and mandatory
       **weighting/uncertainty sensitivity analysis**.
    2. **Multidimensional measurement** — Alkire-Foster dual-cutoff method
       (deprivation cutoffs, poverty cutoff *k*, censored headcount,
       decomposability); indicator/weight choices as normative decisions.
    3. **Clustering & cluster validity** — internal validity indices with named
       sources: silhouette width (Rousseeuw 1987), the gap statistic
       (Tibshirani, Walther & Hastie 2001), and cluster stability under
       resampling/bootstrap (Hennig 2007). The rule: a cluster count/label is a
       **claim requiring validation**, not an output to assert.
    4. **Thresholding / classification** — cutoff justification, boundary
       sensitivity, and misclassification near thresholds.
    5. **Comparability (R4)** — over-time comparability (stable definition,
       coverage, methodology across vintages) and across-unit comparability
       (harmonized definitions/coverage before ranking).
    6. **Division of labor + artifact contracts (R6, R11)** — the skill instructs
       `/cr-work` to *produce*, and `@cr-measurement-integrity` to later *audit*,
       three artifacts with defined schemas under `.cg-docs/research/measurement/`
       (created on demand):
       - `weighting-sensitivity.yaml` — per weighting/aggregation/normalization
         scenario: the scheme, the resulting unit scores/ranks, and a
         rank-stability summary (e.g. max rank shift, rank correlation vs the
         baseline).
       - `cluster-validity.yaml` — chosen *k*, the validity indices computed
         (silhouette/gap), and bootstrap stability (e.g. Jaccard per cluster).
       - vintage manifest (Step 3) under `.cg-docs/research/vintages/`.
       These paths/fields are exactly what the agent reads; the agent never
       recomputes them.
    7. **Verification depth by tier (R7) — audit only (R6, R11)** — light:
       disclosure present + artifact schema well-formed; standard:
       sensitivity/validity artifacts present and their summaries **consistent
       with** the claimed rankings/clusters; thorough: cross-check that the
       stability/validity summary values in the produced artifacts actually
       support the asserted rankings/clusters. **No tier recomputes statistics** —
       every check reads a `/cr-work`-produced value.
- **Test Scenarios:** file exists; `module: research`; cites OECD/JRC +
  Alkire-Foster + a named cluster-validity source (Rousseeuw / gap statistic /
  Hennig); references the `weighting-sensitivity.yaml` + `cluster-validity.yaml`
  artifact schemas; contains weighting sensitivity, thresholding, comparability,
  tier-proportional **audit-only** verification.
- **Tests:** new `Describe` block in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1) mirroring the existing
  skill-content pattern.
- **Acceptance:** V1 passes.

### 2. Register Measurement/Classification as the 9th task type (taxonomy + classifier)

- **Requirements:** R1
- **Files:**
  [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md),
  [.github/prompts/cr-brainstorm.prompt.md](.github/prompts/cr-brainstorm.prompt.md),
  [.github/prompts/cr-plan.prompt.md](.github/prompts/cr-plan.prompt.md)
- **Details:**
  - `cr-skill-research-workflow`: add **Measurement/Classification** to the task
    taxonomy with a one-line scope note; update any "8 task types" prose to "9".
  - `cr-brainstorm` Step 1.1: add Measurement/Classification to the classifier
    list (the `[Theory/Modeling | … | Reproducibility]` line) and to the
    per-type skill-load mapping (`Measurement/Classification →
    cr-skill-measurement`, plus `cr-skill-theory-data-dialogue` where relevant);
    update "one of the 8 research task types" → "9". Add tailored clarifying
    questions for the Measurement/Classification branch.
  - **`cr-plan` (plan review [P1.1]):** add `Measurement/Classification` to the
    hardcoded `task-type:` enum in the research-plan frontmatter template (line
    ≈ 63) and to the Step 3.5 task-type check prose, so measurement plans emit a
    valid `task-type` that `/cr-work` + `/cr-review` route on.
- **Test Scenarios:** all three files contain `Measurement/Classification`; the
  `cr-plan` `task-type:` enum includes it; workflow taxonomy and classifier both
  updated.
- **Tests:** extend the research-workflow + cr-brainstorm content `Describe`
  blocks; **update the two "all 8 task types" assertions** in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1) (the "contains all 8
  task types" test ≈ line 310 and the "dispatch table covers all 8 task types"
  array ≈ line 2427) to 9, adding `Measurement/Classification`.
- **Acceptance:** V2 passes.

### 3. Add comparability P0s + vintage layout to integrity + workflow

- **Requirements:** R4, R5
- **Files:**
  [.github/skills/cr-skill-research-integrity/SKILL.md](.github/skills/cr-skill-research-integrity/SKILL.md),
  [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md)
- **Details:**
  - `cr-skill-research-integrity`: add two P0 error classes in the existing
    "Error Class N" style:
    - **Broken Over-Time Comparability** — a measure whose definition, coverage,
      or methodology changed between vintages, presented as a trend without
      change-attribution. Detection: no vintage manifest / no change-attribution
      for a cross-vintage comparison. Remediation: attribute the change or
      relabel as non-comparable.
    - **Broken Across-Unit Comparability** — a measure not harmonized across
      units, presented as a cross-unit ranking/classification. Detection:
      differing definitions/coverage across ranked units without harmonization
      note. Remediation: harmonize or scope the ranking.
  - `cr-skill-research-workflow`: add `.cg-docs/research/vintages/` to the
    directory layout — one manifest per measure vintage recording measure
    definition, coverage, methodology version, source vintage, and
    change-attribution vs the prior vintage; created on demand by `/cr-work`
    (same pattern as `results/manifest.json`). **Across-unit comparability (plan
    review [P2.3]):** the manifest must also carry harmonization fields for
    cross-unit use — per-unit definition/coverage, the harmonization rule
    applied, and missing-indicator treatment — so the across-unit comparability
    check has the metadata it needs (not only time-vintage fields).
- **Test Scenarios:** both comparability P0 strings present; `.cg-docs/research/vintages`
  referenced in the workflow layout.
- **Tests:** extend the research-integrity + research-workflow `Describe` blocks.
- **Acceptance:** V3 passes.

## Phase B: Executable Enforcement

### 4. Create `@cr-measurement-integrity` agent

- **Requirements:** R3, R6, R7, R9, R10
- **Files:** `.github/agents/cr-measurement-integrity.agent.md` (new)
- **Details:**
  - Frontmatter matching the CR agent pattern: `description`, `model: GPT-5.4`,
    `tools: ['read', 'search']`, `user-invocable: false`, `module: research`,
    plus the standard untrusted-content note for `.cg-docs/research/` inputs.
  - **Audits (does not compute — R6)** the five failure modes against artifacts
    produced by `/cr-work`:
    1. **Weighting disclosure** — weights and their normative basis are
       disclosed; undisclosed weighting flagged (links to Phase 3 normative gate).
    2. **Ranking stability** — a weighting/aggregation/normalization
       sensitivity table exists and rankings are robust; unstable-but-asserted
       rankings flagged P1/P0 by tier.
    3. **Coverage/vintage artifact** — apparent changes carry change-attribution
       (real vs coverage/vintage/methodology); missing attribution → P0 (Step 3
       comparability class).
    4. **Spurious cluster** — cluster count/labels backed by validity + stability
       outputs; asserted-without-validation clusters flagged.
    5. **Comparability** — over-time and across-unit comparability verified
       against vintage manifests.
  - Emits `[P0.N]`/`[P1.N]` findings in the standard format; depth follows tier
    (R7).
- **Test Scenarios:** file exists; GPT-5.4; module research; tools read/search;
  `user-invocable: false`; references the five checks; states it audits (not
  computes).
- **Tests:** new agent `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1); **add
  `cr-measurement-integrity` to BOTH hardcoded `$crAgents` arrays** in that file
  (structural checks ≈ line 409; `module: research` checks ≈ line 864 — plan
  review [P1.2]); add the path to the CR agent list in
  [tests/model-assignments.Tests.ps1](tests/model-assignments.Tests.ps1) and
  **bump the agent count sentinel `Should -Be 26` → `27`**.
- **Acceptance:** V4 passes.

### 5. Extend `/cr-work` with measurement + comparability enforcement

- **Requirements:** R3, R4, R5, R6, R8
- **Files:** [.github/prompts/cr-work.prompt.md](.github/prompts/cr-work.prompt.md)
- **Details:**
  - Load `cr-skill-measurement` when the task type is Measurement/Classification.
  - **Step 2 active enforcement — "P0: Measurement & Comparability Enforcement"**
    (new subsection): for measurement tasks, `/cr-work` must **produce**
    (a) a weighting/aggregation sensitivity table, (b) cluster-validity/stability
    outputs when clustering, and (c) a vintage manifest under
    `.cg-docs/research/vintages/` for any measure compared over time or across
    units; a cross-vintage or cross-unit comparison **without** the manifest +
    change-attribution halts as P0.
  - Update the frontmatter `description` to mention measurement/comparability
    enforcement.
- **Test Scenarios:** contains measurement/comparability enforcement language;
  references `cr-skill-measurement`; references `.cg-docs/research/vintages`.
- **Tests:** extend the `cr-work.prompt.md - P0 enforcement` `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1).
- **Acceptance:** V5 passes.

### 6. Wire `@cr-measurement-integrity` into `/cr-review`

- **Requirements:** R7, R8
- **Files:** [.github/prompts/cr-review.prompt.md](.github/prompts/cr-review.prompt.md)
- **Details:**
  - Add a **Measurement/Classification** row to the task-type → agent dispatch
    table routing to `@cr-measurement-integrity`.
  - Add a **scoped** conditional dispatch (plan review [P2.2]): run
    `@cr-measurement-integrity` when the task type is Measurement/Classification
    **or** when the reviewed/changed files intersect
    `.cg-docs/research/measurement/` or `.cg-docs/research/vintages/` — **not**
    merely because those directories exist somewhere in the repo (which would
    over-fire on historical artifacts). Otherwise skip with the standard
    "skipped — no measurement artifacts in scope" note.
  - Keep depth proportional (R7) and **audit-only** (R6): at thorough depth the
    agent cross-checks the produced sensitivity/validity summaries against the
    asserted rankings — it does not recompute them.
- **Test Scenarios:** `@cr-measurement-integrity` referenced; Measurement/Classification
  dispatch row present.
- **Tests:** add `It` assertions to the `cr-review.prompt.md` orchestration +
  dispatch-table `Describe` blocks (including the updated "9 task types" array).
- **Acceptance:** V6 passes.

## Phase C: Registration, Generation, Tests

### 7. Register agent + skill (instructions + catalog + model-guide + reference)

- **Requirements:** R9, R10
- **Files:**
  [.github/copilot-instructions.md](.github/copilot-instructions.md),
  [.github/shared/model-catalog.json](.github/shared/model-catalog.json),
  [docs/model-guide.md](docs/model-guide.md),
  [docs/reference.md](docs/reference.md)
- **Details:**
  - `copilot-instructions.md`: add `cr-measurement-integrity` to **CR Agents**,
    `cr-skill-measurement` to **CR Skills**, and add Measurement/Classification to
    the **Research Task Taxonomy (now 9 types)** list.
  - `model-catalog.json`: add an `assignments` entry
    `{ path: ".github/agents/cr-measurement-integrity.agent.md", preferredModel:
    "GPT-5.4", role: "review", ... }` consistent with sibling CR agents.
  - `docs/model-guide.md`: add a row to the **Agents** assignment table
    (`| cr-measurement-integrity.agent.md | GPT-5.4 | review | … |`).
  - `docs/reference.md`: add the agent + skill + 9th task type where CR
    agents/skills/task types are enumerated (verify against the docs-sync test).
- **Test Scenarios:** catalog has new assignment (GPT-5.4, review); instructions
  list both names + the 9th type; model-guide table has the row.
- **Tests:** extend the CR-agent list + the model-guide table assertions in
  [tests/model-assignments.Tests.ps1](tests/model-assignments.Tests.ps1).
- **Acceptance:** V7, V8 pass.

### 8. Regenerate native target trees

- **Requirements:** R9, R10
- **Files (generated):** `.agents/`, `.claude/`, `.opencode/`, `adapters/`
- **Details:** run `python3 scripts/cg_generate_targets.py --all`. Do **not**
  hand-edit generated files. If generation reports an unmapped asset, add the
  mapping in `.github/shared/target-mapping.json` and re-run.
- **Test Scenarios:** parity checks pass; no stray generated diffs.
- **Tests:** [tests/parity.Tests.ps1](tests/parity.Tests.ps1).
- **Acceptance:** V9 passes.

### 9. Run full test suite via safe runner

- **Requirements:** R10, C6
- **Files:** —
- **Details:** run `. tests\Run-Tests.ps1` and read `tests/last-run.json`.
  **Pester safety rules apply** — no directory runs, no `-PassThru | Select-Object`
  pipelines, no `2>&1` pipelines. On this macOS host PowerShell is not installed
  (exit 127); if it cannot run here, hand V9/V10 to the user or an
  `execution_subagent`.
- **Test Scenarios:** all `Describe` blocks green; the updated "9 task types"
  assertions + new measurement tests pass.
- **Tests:** whole suite.
- **Acceptance:** V10 passes (0 failures in `tests/last-run.json`).

## Testing Strategy

- **Static/contract tests (Pester):** frontmatter + content for the new skill
  and agent; the 8→9 task-type assertion updates (both sites); comparability P0
  strings; `/cr-work` + `/cr-review` wiring; catalog + model-guide + count
  sentinel; parity.
- **Behavioral validation (manual, post-merge):** run `/cr-work` on a small
  composite-index fixture to confirm a weighting-sensitivity table + vintage
  manifest are produced and an unattributed cross-vintage comparison is blocked;
  run `/cr-review` to confirm `@cr-measurement-integrity` fires and flags a
  planted undisclosed-weighting/spurious-cluster case.
- **Runner:** always the canonical `. tests\Run-Tests.ps1` → `tests/last-run.json`.

## Documentation Checklist

- [ ] New skill self-documents its cited methodology and schemas.
- [ ] `copilot-instructions.md` CR Agents + CR Skills + 9-type taxonomy updated.
- [ ] `docs/model-guide.md` Agents table + `docs/reference.md` updated.
- [ ] `cr-skill-research-workflow` taxonomy + vintage layout updated.
- [ ] All new files carry a creation date (`date:` frontmatter or header).

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Hidden "8 task types" assertion sites beyond the two confirmed cause test failures | Iteration policy `ask`: run tests, update the exact site the test names, re-run. Step 2 targets both confirmed sites. |
| Agent asked to compute stability itself (unimplementable) | [P1.1] baked into R6/C3: agent audits `/cr-work`-produced artifacts only. |
| Count-sentinel / model-guide drift breaks `model-assignments.Tests.ps1` | Step 7 explicitly bumps the sentinel (26→27) and adds the model-guide row. |
| Regeneration touches many files | Run generator once, review diff; never hand-edit generated trees; stop + report if scope widens. |
| PowerShell unavailable on macOS host blocks V9/V10 | Defer to user or `execution_subagent`; all edits are static/reviewable. |
| Scope creep into normative gates (Phase 3) | Normative-choice *detection* is Phase 3; here the agent only *flags* undisclosed weighting, deferring the gate. |
| Measurement skill reinvents index theory | R2/C4: every section cites an established source; skill is a router to methodology, not a new method. |
| Two audit checks (ranking stability, spurious cluster) not implementable without artifact contracts | R11/Step 1.6 defines `weighting-sensitivity.yaml` + `cluster-validity.yaml` schemas that `/cr-work` produces and the agent audits. |
| Dispatch over-fires on historical measurement artifacts | R12/Step 6 scopes dispatch to task-type or reviewed-file intersection, not repo-wide directory presence. |
| `/cr-plan` task-type enum omits the 9th type, breaking plan→work→review flow | Step 2 adds `Measurement/Classification` to the `cr-plan` `task-type:` enum (line ≈ 63). |

## Out of Scope

- Scoping front-end + normative-decision gate backbone (Phase 3) — this phase
  only *flags* undisclosed weighting, it does not build the approval gate.
- Method-pack retrofit / lifecycle orchestration (Phase 4).
- The actual Beyond-GDP / measurement analysis (a research deliverable, not tool
  build).
- Second measurement use-case validation (`cr-second-measurement-use-case-validation`).
- Team evidence library (`cr-team-evidence-library`).
- A statistics/clustering execution backend — `/cr-work` uses the project's own
  R/Python/Stata toolchain; this phase ships the *contract*, not a solver.

## Completion Contract

### Outcome

CR gains a first-class Measurement/Classification archetype — a cited-methodology
skill, a five-check measurement-integrity audit agent, comparability P0s with
vintage/change-attribution artifacts, and full workflow/review wiring — so
composite-index, clustering, and classification work is checked for weighting
disclosure, ranking stability, coverage/vintage artifacts, spurious clusters, and
backward-compatible comparability. The 9th task type is registered everywhere the
8 were enumerated; all native targets regenerated; full Pester suite green.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | A | `cr-skill-measurement/SKILL.md` exists, `module: research`, cites OECD/JRC + Alkire-Foster + a named cluster-validity source; defines the `weighting-sensitivity.yaml` + `cluster-validity.yaml` artifact schemas; covers weighting sensitivity, thresholding, comparability | file + grep | yes |
| V2 | A | Measurement/Classification registered in `cr-skill-research-workflow`, `/cr-brainstorm` Step 1.1, and the `/cr-plan` `task-type:` enum; both "all 8 task types" tests + both `$crAgents` arrays updated | grep + test | yes |
| V3 | A | `cr-skill-research-integrity` has both comparability P0 classes; `.cg-docs/research/vintages/` (with across-unit harmonization fields) in workflow layout | grep | yes |
| V4 | B | `cr-measurement-integrity.agent.md` exists, GPT-5.4, module research, read/search, `user-invocable: false`, states it audits (not computes) | grep | yes |
| V5 | B | `/cr-work` contains measurement + comparability enforcement, `cr-skill-measurement` load, and production of `weighting-sensitivity.yaml` / `cluster-validity.yaml` / vintage manifest | grep | yes |
| V6 | B | `/cr-review` dispatch has Measurement/Classification → `@cr-measurement-integrity`, scoped to task-type/reviewed-file intersection (not repo-wide presence) | grep | yes |
| V7 | C | `copilot-instructions.md` lists agent + skill + 9th type; `docs/model-guide.md` Agents table has the row | grep | yes |
| V8 | C | `model-catalog.json` has `cr-measurement-integrity` assignment (GPT-5.4, review); agent count sentinel bumped to 27 | json + grep | yes |
| V9 | final | Multi-target regeneration run; parity holds | `python3 scripts/cg_generate_targets.py --all` + `parity.Tests.ps1` | yes (downstream) |
| V10 | final | Full Pester suite green via safe runner — **downstream-required** (PowerShell absent locally; attach `tests/last-run.json` from a PowerShell-capable env) | `. tests\Run-Tests.ps1` → `tests/last-run.json` | yes (downstream) |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No regression in existing 8 task types / CR agents | existing `cr-prompts.Tests.ps1` + `model-assignments.Tests.ps1` stay green |
| C2 | New agent GPT-5.4 (OpenAI-first); catalog + model-guide + sentinel consistent | catalog + frontmatter + model-guide |
| C3 | Agent audits `/cr-work`-produced artifacts; it does not compute statistics itself | agent text review [P1.1] |
| C4 | Measurement skill cites established methodology; does not reinvent it | skill text review |
| C5 | Engineering-only projects unaffected (research gating preserved) | `module: research` on all new/changed surfaces |
| C6 | Pester run only via the canonical safe runner | no directory runs / no `-PassThru` pipelines |

### Boundaries

- **In:** the measurement skill + agent, the 9th task type across all enumerated
  sites (workflow, classifier, review dispatch, both test assertions),
  comparability P0s + vintage artifacts, `/cr-work` + `/cr-review` wiring, full
  registration surface (`copilot-instructions.md`, `model-catalog.json`,
  `docs/model-guide.md`, `docs/reference.md`, count sentinel), and target
  regeneration.
- **Out:** normative-decision gate (Phase 3), method-pack retrofit (Phase 4), the
  actual measurement analysis, second-use-case validation, team evidence library,
  a clustering/statistics execution backend.

### Iteration Policy

1. `deviation-policy: ask` — surface required deviations before acting.
2. If a test names an extra "8 task types" site or registration surface, update
   exactly that site and re-run.
3. If regeneration touches unexpected files, stop and report before continuing.

### Blocked-Stop Conditions

- Pester cannot be run through the safe runner (PowerShell not installed on this
  Mac — may defer V9/V10 to the user or a subagent).
- Parity fails after regeneration and cannot be reconciled.
- A required deviation is discovered under `ask` without user approval.
- Any required verification item fails after allowed recovery attempts.
