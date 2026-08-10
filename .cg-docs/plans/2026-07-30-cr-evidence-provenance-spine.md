---
date: 2026-07-30
title: "CR Evidence & Provenance Spine (Responsible Research Partner — Phase 1)"
status: completed
completed-date: 2026-07-31
scope: Deep
brainstorm: ".cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md"
language: "PowerShell/Markdown"
estimated-effort: large
deviation-policy: ask
execution-report: ".cg-docs/work-reports/2026-07-30-cr-evidence-provenance-spine.md"
completed-phases: [1, 2, 3]
current-phase: 3
failing-steps: []
tags: [compound-research, responsible-ai, provenance, evidence, anti-hallucination, citations, p0]
---

# CR Evidence & Provenance Spine (Responsible Research Partner — Phase 1)

## Objective

Give the Compound Research (CR) module an **evidence and provenance spine** so that
every substantive claim in a research output is traceable to a **verified,
in-repo source**, and fabricated or uncited claims are blocked as **P0**. This is
Phase 1 of the CR expansion from a journal-paper econometrics assistant into a
responsible partner for the full research lifecycle of policy-relevant
measurement work.

Concretely, this phase delivers:

- A methodology skill (`cr-skill-evidence-provenance`) defining the
  analysis/composition split, the claim-evidence matrix and provenance-ledger
  schemas, the **repo-local-corpus default**, anti-hallucination rules, and
  tool-agnostic document ingestion (original document remains the authority).
- A verification agent (`@cr-provenance-audit`) that audits sources and
  citation locators.
- Workflow enforcement in `/cr-work` (repo-local corpus default + evidence
  logging + anti-hallucination P0 halt) and dispatch wiring in `/cr-review`.
- Two new P0 error classes in the research-integrity catalog
  (fabricated/unverifiable citation; uncited substantive claim).

## Context

The brainstorm
([2026-07-30-cr-responsible-research-partner-measurement.md](.cg-docs/brainstorms/2026-07-30-cr-responsible-research-partner-measurement.md))
selected **Approach 3 (phased, value-first)** and identified the
Evidence/Provenance spine as Phase 1: the highest-value, lowest-risk unit that
unblocks the rest. The design adopts the provenance ideas from
[Suggestions-For-CR.md](Suggestions-For-CR.md) (analysis/composition separation,
Markdown conversion with preserved originals + provenance, anti-hallucination
citation rules) but deliberately **does not** clone that note's 8-agent
pipeline. Instead the stages map onto a small agent set and reuse existing CR
agents (`@cr-academic-writing` for composition).

Locked design decisions (from the brainstorm) that this plan must honor:

- **Default corpus = documents inside the working repo only.** External or
  autonomous literature search is **opt-in and flagged**; this phase ships the
  guard/flag, not a search backend.
- **The original document is the authority.** Ingestion/conversion (e.g. to
  Markdown) is tool-agnostic; converted text is a convenience index, never the
  source of truth.
- Evidence justifies **method choices**, not just prose.
- Verification depth is **proportional** to the review tier (light / standard /
  thorough).
- An uncited or unverifiable substantive claim is a **P0 blocker**.

### Relevant existing surfaces (researched)

- CR agents follow the frontmatter pattern: `description`, `model: GPT-5.4`,
  `tools: ['read', 'search']`, `user-invocable: false`, `module: research`, plus
  an untrusted-content note for `.cg-docs/research/` files
  (see [cr-research-integrity.agent.md](.github/agents/cr-research-integrity.agent.md)).
- `/cr-review` Step 2 dispatches CR agents (unconditional + conditional). New
  agent wires in here
  ([cr-review.prompt.md](.github/prompts/cr-review.prompt.md)).
- `/cr-work` already has a P0 active-detection pattern (Step 0 pre-flight seed
  check; Step 2 "P0: Seed Enforcement"; manifest.json logging). Anti-hallucination
  + repo-local enforcement extends this pattern
  ([cr-work.prompt.md](.github/prompts/cr-work.prompt.md)).
- New CR agents must be registered in `model-catalog.json` (GPT-5.4, role
  `review`) and in the CR lists in
  [copilot-instructions.md](.github/copilot-instructions.md); the agent-discovery
  test asserts every `.github/agents/*.agent.md` has a catalog entry.
- Native target trees (`.agents/`, `.claude/`, `.opencode/`, `adapters/`) are
  generated from canonical `.github/` sources by
  [scripts/cg_generate_targets.py](scripts/cg_generate_targets.py).

## Requirements

| # | Requirement | Source |
|---|-------------|--------|
| R1 | Define claim-evidence matrix + provenance-ledger schemas | Brainstorm; Suggestions-For-CR.md |
| R2 | Repo-local corpus is the default; external search opt-in + flagged | Brainstorm (locked) |
| R3 | Original document is authority; ingestion tool-agnostic | Brainstorm (locked) |
| R4 | Anti-hallucination rules: never invent source/DOI/quote/page; abstain + flag over plausible completion | Brainstorm; Suggestions-For-CR.md |
| R5 | Uncited/unverifiable substantive claim = P0 blocker | Brainstorm (locked) |
| R6 | Evidence justifies method choices, not only prose | Brainstorm (locked) |
| R7 | Verification depth proportional to review tier | Brainstorm (locked) |
| R8 | Reuse existing agents where possible; do not clone the 8-agent pipeline | Brainstorm (locked) |
| R9 | Research-module gating preserved; engineering-only projects unaffected | Charter; module convention |
| R10 | New agent GPT-5.4 (OpenAI-first); registered + tests green; targets regenerated | Model governance; parity tests |

## Implementation Steps

> Globally-numbered steps grouped into three internal phases. `/cg-work phaseA`,
> `phaseB`, `phaseC` may be used to execute a single phase.

## Phase A: Methodology + Schemas

### 1. Create `cr-skill-evidence-provenance`

- **Requirements:** R1, R2, R3, R4, R6, R7, R8
- **Files:** `.github/skills/cr-skill-evidence-provenance/SKILL.md` (new)
- **Details:**
  - Frontmatter: `name: cr-skill-evidence-provenance`, `module: research`,
    `description:` (progressive-disclosure style — say when to load: any CR task
    that ingests documents, makes cited claims, or justifies a method choice
    from a source).
  - Sections:
    1. **Analysis / composition split** — analysis produces a verified
       claim-evidence matrix; composition may only assert claims that already
       exist and are `verified` in the matrix. A checkpoint separates the two.
    2. **Repo-local corpus default (R2)** — the evidence corpus is documents
       inside the working repo. External/autonomous search is opt-in; any
       external source must be recorded with `origin: external-opt-in` and
       `external_flag: true`.
    3. **Provenance ledger / source manifest schema (R1, R3)** — YAML at
       `.cg-docs/research/evidence/provenance-ledger.yaml`:
       ```yaml
       sources:
         - id: S003
           title: "..."
           authors: ["..."]
           year: 2020
           origin: repo-local            # repo-local | external-opt-in
           original_path: "data/refs/source.pdf"   # authority
           converted_path: ".cg-docs/research/evidence/converted/source.md"
           conversion_tool: "markitdown@x.y"        # tool-agnostic
           sha256: "<hash of original>"
           external_flag: false
           ingested_on: 2026-07-30
       ```
    4. **Claim-evidence matrix schema (R1, R6)** — YAML at
       `.cg-docs/research/evidence/claim-evidence-matrix.yaml`:
       ```yaml
       claims:
         - id: C001
           statement: "..."
           type: empirical              # empirical | methodological | normative
           status: verified             # verified | unverified | flagged | abstained
           evidence:
             - source_id: S003
               locator: "Table 2, p. 14"
               quote: "..."             # verbatim from converted markdown
               supports: true
           verified_by: cr-provenance-audit
           verified_on: 2026-07-30
       ```
       Note `type: methodological` is how R6 (evidence for method choices) is
       represented.
    5. **Ingestion pattern (R3)** — original document is authority; conversion
       to Markdown (default tool: Microsoft `markitdown`, documented as
       **optional**, not a required plugin dependency) produces a page-aware
       index under `converted/`; record `sha256` of the original and the
       `conversion_tool`.
    6. **Anti-hallucination rules (R4)** — never invent a source, DOI, quote,
       page, or locator; if a claim cannot be tied to a verified source, mark it
       `unverified`/`abstained` and flag it — never emit a plausible completion;
       quotes must be verbatim from `converted_path`.
    7. **Verification depth by tier (R7)** — light: schema/well-formedness +
       spot-check; standard: every substantive claim has ≥1 verified source with
       a resolvable locator; thorough: also verify quote-verbatim + locator
       resolves to the cited page.
- **Test Scenarios:** file exists; `module: research`; contains both schema
  blocks; contains repo-local default; contains anti-hallucination rules;
  contains tier-proportional verification.
- **Tests:** new `Describe` block in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1) mirroring the existing
  skill-content pattern (`Get-Frontmatter`, `Should -Be $true` regex checks).
- **Acceptance:** V1 passes.

### 2. Extend research-integrity catalog with evidence P0s

- **Requirements:** R4, R5
- **Files:**
  [.github/skills/cr-skill-research-integrity/SKILL.md](.github/skills/cr-skill-research-integrity/SKILL.md)
- **Details:** Add two error classes to the P0 catalog, matching the existing
  "Error Class N: <name>" heading style:
  - **Fabricated / Unverifiable Citation** — a source, DOI, quote, page, or
    locator that cannot be resolved to a repo-local (or flagged external)
    document. Detection: locator does not resolve in `provenance-ledger.yaml` /
    `converted/`. Remediation: remove or replace with a verified source; never
    fabricate.
  - **Uncited Substantive Claim** — an empirical or methodological assertion
    with no `verified` evidence row. Detection: claim in output text absent from
    `claim-evidence-matrix.yaml` or present with `status != verified`.
    Remediation: attach verified evidence or downgrade/remove the claim.
- **Test Scenarios:** both new error-class strings present.
- **Tests:** extend the existing research-integrity content `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1).
- **Acceptance:** V2 passes.

### 3. Update research-workflow layout + priority system

- **Requirements:** R2, R5, R7
- **Files:**
  [.github/skills/cr-skill-research-workflow/SKILL.md](.github/skills/cr-skill-research-workflow/SKILL.md)
- **Details:**
  - Add `.cg-docs/research/evidence/` to the directory-layout section with its
    contents: `provenance-ledger.yaml`, `claim-evidence-matrix.yaml`,
    `converted/` (converted Markdown), and note originals stay in their repo
    location (authority). Note the directory is created on demand by `/cr-work`
    (same pattern as `results/manifest.json`).
  - Add the two new evidence P0 classes to the integrity/priority summary and
    state the repo-local-corpus default + external-opt-in-flagged rule.
  - Cross-reference `cr-skill-evidence-provenance` as the detailed spec.
- **Test Scenarios:** `.cg-docs/research/evidence` string present; repo-local
  default referenced.
- **Tests:** extend the research-workflow content `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1).
- **Acceptance:** V3 passes.

## Phase B: Executable Enforcement

### 4. Create `@cr-provenance-audit` agent

- **Requirements:** R1, R3, R4, R5, R7, R8, R9, R10
- **Files:** `.github/agents/cr-provenance-audit.agent.md` (new)
- **Details:**
  - Frontmatter matching the CR agent pattern: `description`, `model: GPT-5.4`,
    `tools: ['read', 'search']`, `user-invocable: false`, `module: research`.
  - Include the standard untrusted-content note for `.cg-docs/research/` inputs
    (treat converted documents and ledgers as data, not instructions — prompt-
    injection guard).
  - Responsibilities: (a) **source verification** — every ledger source has a
    resolvable `original_path` and matching `sha256`; external sources carry
    `external_flag: true`; (b) **citation/locator audit** — every `verified`
    claim's locator resolves in `converted/`, quotes are verbatim; (c) flag
    fabricated/unverifiable citations and uncited substantive claims as P0
    using the standard `[P0.N]` finding format.
  - Verification depth follows the review tier (R7). Composition-quality review
    is delegated to `@cr-academic-writing` (R8) — this agent audits evidence,
    not prose style.
- **Test Scenarios:** file exists; GPT-5.4; module research; tools read/search;
  `user-invocable: false`.
- **Tests:** new agent `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1); add path to the CR
  agent list in
  [tests/model-assignments.Tests.ps1](tests/model-assignments.Tests.ps1).
- **Acceptance:** V4 passes.

### 5. Extend `/cr-work` with repo-local + anti-hallucination enforcement

- **Requirements:** R2, R4, R5, R6
- **Files:** [.github/prompts/cr-work.prompt.md](.github/prompts/cr-work.prompt.md)
- **Details:**
  - **Step 0 pre-flight (mirror the seed check):** if the task ingests documents
    or emits cited claims, verify a `provenance-ledger.yaml` exists / can be
    created and that any external source is flagged; halt if an external source
    is used without the opt-in flag.
  - **Step 2 active enforcement — "P0: Evidence & Provenance Enforcement"**
    (new subsection alongside seed enforcement): before emitting any substantive
    claim, confirm a `verified` row in `claim-evidence-matrix.yaml`; never invent
    sources/quotes/locators; on a gap, mark `unverified`/`abstained` and flag —
    do not fabricate. Log ingested sources + verified claims to the evidence
    artifacts (analogue of manifest.json logging).
  - Reference `cr-skill-evidence-provenance` in the load list.
  - Update the frontmatter `description` to mention evidence/provenance
    enforcement.
- **Test Scenarios:** contains repo-local/evidence enforcement language;
  references `cr-skill-evidence-provenance`; anti-hallucination language present.
- **Tests:** extend the `cr-work.prompt.md - P0 enforcement` `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1).
- **Acceptance:** V5 passes.

### 6. Wire `@cr-provenance-audit` into `/cr-review`

- **Requirements:** R7, R8
- **Files:** [.github/prompts/cr-review.prompt.md](.github/prompts/cr-review.prompt.md)
- **Details:**
  - In **Step 2**, add a conditional (file-presence) dispatch: dispatch
    `@cr-provenance-audit` when `.cg-docs/research/evidence/` exists **or** when a
    Writing / Tables-Figures task is under review; otherwise skip with the
    standard "`@cr-provenance-audit` skipped — no evidence artifacts found" note.
  - Add a row/mention so the Writing task type includes `@cr-provenance-audit`
    alongside `@cr-academic-writing` (R8: prose vs evidence separation).
  - Keep depth proportional (R7): only run verbatim/locator resolution at
    thorough depth.
- **Test Scenarios:** `@cr-provenance-audit` referenced in the prompt.
- **Tests:** add an `It "references @cr-provenance-audit"` to the
  `cr-review.prompt.md - agent orchestration` `Describe` in
  [tests/cr-prompts.Tests.ps1](tests/cr-prompts.Tests.ps1).
- **Acceptance:** V6 passes.

## Phase C: Registration, Generation, Tests

### 7. Register agent + skill (instructions + catalog)

- **Requirements:** R9, R10
- **Files:**
  [.github/copilot-instructions.md](.github/copilot-instructions.md),
  [.github/shared/model-catalog.json](.github/shared/model-catalog.json)
- **Details:**
  - `copilot-instructions.md`: add `cr-provenance-audit` to the **CR Agents**
    list and `cr-skill-evidence-provenance` to the **CR Skills** list (with a
    one-line description each).
  - `model-catalog.json`: add an `assignments` entry
    `{ path: ".github/agents/cr-provenance-audit.agent.md", preferredModel:
    "GPT-5.4", role: "review", ... }` consistent with sibling CR agent entries.
- **Test Scenarios:** catalog has the new assignment (GPT-5.4, role review);
  instructions list both names.
- **Tests:** extend the CR-agent list in
  [tests/model-assignments.Tests.ps1](tests/model-assignments.Tests.ps1) to
  include the new path.
- **Acceptance:** V7, V8 pass.

### 8. Regenerate native target trees

- **Requirements:** R9, R10
- **Files (generated):** `.agents/`, `.claude/`, `.opencode/`, `adapters/`
- **Details:** run `python3 scripts/cg_generate_targets.py --all` to propagate
  the new agent/skill + edited prompts/skills/instructions + catalog into all
  native trees. Do **not** hand-edit generated files. If generation reports an
  unmapped asset, add the mapping in
  `.github/shared/target-mapping.json` and re-run.
- **Test Scenarios:** parity checks pass; no stray generated diffs.
- **Tests:** [tests/parity.Tests.ps1](tests/parity.Tests.ps1) and any
  generation/registration parity tests.
- **Acceptance:** V9 passes.

### 9. Run full test suite via safe runner

- **Requirements:** R10, C5
- **Files:** —
- **Details:** run the canonical safe runner (`. tests\Run-Tests.ps1`) and read
  `tests/last-run.json`. **Pester safety rules apply** — no directory runs, no
  `-PassThru | Select-Object` pipelines, no `2>&1` pipelines. On this macOS host
  PowerShell is not installed (exit 127); if it cannot run here, hand V9/V10 to
  the user or an `execution_subagent`.
- **Test Scenarios:** all `Describe` blocks green; new + existing CR tests pass.
- **Tests:** whole suite.
- **Acceptance:** V10 passes (0 failures in `tests/last-run.json`).

## Testing Strategy

- **Static/contract tests (Pester):** frontmatter + content assertions for the
  new skill and agent; new `It`s for `/cr-work` enforcement language and
  `/cr-review` dispatch; catalog assignment + agent-discovery coverage; parity.
- **Behavioral validation (manual, post-merge):** run `/cr-work` on a small
  fixture research task with a repo-local PDF to confirm the ledger + matrix are
  produced and an uncited claim is blocked; run `/cr-review` to confirm
  `@cr-provenance-audit` fires and flags a planted fabricated citation as P0.
- **Runner:** always the canonical `. tests\Run-Tests.ps1` → `tests/last-run.json`.

## Documentation Checklist

- [ ] New skill self-documents its schemas and rules (no separate doc file).
- [ ] `copilot-instructions.md` CR Agents + CR Skills lists updated.
- [ ] `cr-skill-research-workflow` directory-layout section updated.
- [ ] All new files carry a creation date (`date:` frontmatter or header).
- [ ] `docs/reference.md` CR agent/skill listing updated if it enumerates them
      (verify during Phase C; update if the docs-sync test requires it).

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Hidden registration surfaces (skills-lock.json, docs sync, parity mirrors) cause test failures | Iteration policy `ask`: run tests, update the surface the test names, re-run. Phase C explicitly checks parity + catalog. |
| Regeneration touches many files / unexpected diffs | Run generator once, review diff; do not hand-edit generated trees; stop + report if scope unexpectedly widens. |
| PowerShell unavailable on macOS host blocks V9/V10 | Defer test execution to the user or an `execution_subagent`; all edits are static and reviewable without running. |
| Scope creep into Measurement archetype / normative gates | Boundaries section makes those out-of-scope; they have their own roadmap features + plans. |
| `markitdown` treated as a hard dependency | Skill documents it as optional/tool-agnostic; original document is authority; no runtime dep added to plugin core. |
| Over-blocking (false-positive P0 on legitimate uncited background) | "Substantive claim" is scoped to empirical/methodological assertions; verification depth is tier-proportional (light does spot-checks only). |

## Out of Scope

- Measurement/Classification archetype and comparability P0s (Phase 2).
- Scoping front-end + normative-gate backbone (Phase 3).
- Responsible-lifecycle method-pack retrofit (Phase 4).
- Team evidence library / cross-project compounding (separate roadmap feature
  `cr-team-evidence-library`).
- An actual autonomous external-literature-search backend (only the opt-in
  flag/guard ships now).
- Charter edits (already completed in the brainstorm handoff).

## Completion Contract

### Outcome

CR gains an evidence/provenance subsystem — a methodology skill, a
citation/source-audit agent, workflow-level repo-local-corpus + anti-hallucination
enforcement, and integrity-catalog entries — so every substantive claim in a
research output is traceable to a verified in-repo source, and fabricated or
uncited claims are blocked as P0. All native targets regenerated; full Pester
suite green.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | A | `cr-skill-evidence-provenance/SKILL.md` exists, `module: research`, contains claim-evidence matrix + provenance ledger schemas, anti-hallucination rules, repo-local default | file + grep | yes |
| V2 | A | `cr-skill-research-integrity` has new error classes (fabricated citation; uncited claim) | grep | yes |
| V3 | A | `cr-skill-research-workflow` documents `.cg-docs/research/evidence/` + evidence P0 | grep | yes |
| V4 | B | `cr-provenance-audit.agent.md` exists, `model: GPT-5.4`, `module: research`, `tools: ['read','search']`, `user-invocable: false` | grep | yes |
| V5 | B | `/cr-work` contains repo-local-corpus default + anti-hallucination/evidence enforcement | grep | yes |
| V6 | B | `/cr-review` dispatches `@cr-provenance-audit` | grep | yes |
| V7 | C | `copilot-instructions.md` lists `cr-provenance-audit` + `cr-skill-evidence-provenance` | grep | yes |
| V8 | C | `model-catalog.json` has `cr-provenance-audit` assignment (GPT-5.4, role review) | json check | yes |
| V9 | final | Multi-target regeneration run; parity holds | `python3 scripts/cg_generate_targets.py --all` + `parity.Tests.ps1` | yes |
| V10 | final | Full Pester suite green via safe runner | `. tests\Run-Tests.ps1` → `tests/last-run.json` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No regression in existing CR agents/prompts/skills | existing `cr-prompts.Tests.ps1` + `model-assignments.Tests.ps1` stay green |
| C2 | New agent is GPT-5.4 (OpenAI-first; no Haiku) | catalog + frontmatter |
| C3 | Engineering-only projects unaffected (research gating preserved) | `module: research` on all new/changed surfaces |
| C4 | No new required third-party runtime dep (markitdown documented as optional) | skill text review |
| C5 | Pester run only via the canonical safe runner | no directory runs / no `-PassThru` pipelines |

### Boundaries

- **In:** the new skill + agent, edits to the four CR surface files +
  `copilot-instructions.md` + `model-catalog.json` + the two test files, and
  target regeneration.
- **Out:** Measurement/Classification archetype (Phase 2), scoping front-end +
  normative-gate backbone (Phase 3), method-pack retrofit (Phase 4), team
  evidence library, an actual autonomous external-search backend (only the
  opt-in flag/guard is in scope), and charter edits (already done).

### Iteration Policy

1. `deviation-policy: ask` — surface required deviations before acting.
2. If a test names an extra registration surface (e.g. `skills-lock.json`,
   docs sync, parity mirror), update that surface and re-run.
3. If regeneration touches unexpected files, stop and report before continuing.

### Blocked-Stop Conditions

- Pester cannot be run through the safe runner (PowerShell not installed on this
  Mac — may defer V9/V10 to the user or a subagent).
- Parity fails after regeneration and cannot be reconciled.
- A required deviation is discovered under `ask` without user approval.
- Any required verification item fails after allowed recovery attempts.
