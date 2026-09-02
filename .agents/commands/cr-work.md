---
description: "Research work — implement a research plan step by step. Supports /cr-work [phaseX]. Enforces P0 seed, provenance, and specification logging requirements."
---

# Research Work

You are a senior research engineer implementing a research plan created with
`/cr-plan`. Supports `/cr-work [phaseX]`.

## File Permissions

- You may read any file in the workspace.
- You may read `roadmap.json`.
- You may create and modify code files and research output files as required by the plan.
- You may create and modify `c-research/results/manifest.json`.
- You may modify the YAML frontmatter of the plan file (status, completed-date, failing-steps, completed-phases, current-phase fields only).
- You must NOT modify `roadmap.json` directly — dispatch `@cg-roadmap` for roadmap writes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` and `compound-gpid.local.md`. Check that `suites:` includes `cr`.
2. Load `.agents/shared/context-loading.contract.md` and apply Stage 0/1/2 first. Do not read full `compound-gpid.context.md` by default; if needed, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
3. **Always load**: `cr-skill-research-workflow`, `cr-skill-research-integrity`,
   `cr-skill-research-scoping`, and `cr-skill-evidence-provenance`.
4. If the plan task type is **Implementation**: also load `cr-skill-mathematical-derivation`
   for code-math variable mapping conventions and derivation file standards.
5. If the plan task type is **Reproducibility**: also load `cr-skill-replication-standards`
   for AEA archive structure, README templates, lockfile conventions, seed registry,
   data documentation, path portability rules, and sensitive-data checklists.
   Also verify `c-research/replication/` exists — create it silently if absent.
   **P0 check** (pre-flight halt — distinct from Step 2 active seed enforcement): before
   any work begins, scan code files for random operations without a preceding seed
   (see `cr-skill-replication-standards` Section 4). If any are found, halt and require
   seeds to be added before proceeding.
6. If the plan task type is **Tables/Figures**: also load `cr-skill-publication-output`
   for regression table patterns, LaTeX table conventions, figure output standards,
   caption/note discipline, and output file management.
7. If the plan task type is **Measurement/Classification**: also load
  `cr-skill-measurement` and require production of:
  `c-research/measurement/weighting-sensitivity.yaml`,
  `c-research/measurement/cluster-validity.yaml`, and
  `c-research/vintages/<study-slug>-vintage-manifest.yaml`.

### Step 0.5: Consult Brain

Load `cg-skill-brain-query`. Search for known mistakes and anti-patterns from
similar econometric, ML, and research implementation work. Apply only relevant
findings while implementing plan steps.

### Step 1: Load the Plan

Follow the same plan-loading and phase-parsing logic as `/cg-work`. All `/cg-work`
rules for plan loading, phase validation, and sequential enforcement apply here.

### Step 1.2: Parse Phase Argument

Same logic as `/cg-work` — accepted forms: `phase1`, `phase 1`, `Phase 1`.

### Step 1.5: Mark Work Started

Same as `/cg-work` — dispatch `@cg-roadmap` if roadmap feature is at `planned`.

### Step 1.55: Active-State Handoff

Load `.agents/shared/active-state.contract.md`.

- On workflow start, update `.cg-docs/active-state/current.json` with
  `workflow: "/cr-work"`, `status: "active"`, the current plan path,
  execution report path, and the next exact resume command.
- At phase boundaries and blocked stops, refresh evidence statuses,
  unresolved decisions, and `nextCommand`.
- On completion, set `status` to `completed` or `handoff` and include the
  next recommended command so `/cg-resume` can discover and continue
  research work reliably.

### Step 1.6: Build Test Index

Same as `/cg-work` — scan for test files covering each plan step.

### Step 2: Implement Step by Step

For each step, apply all `/cg-work` implementation rules PLUS the following
research-specific enforcement:

> **Lifecycle context.** These P0 gates are the **Execute** stage of the
> responsible research lifecycle (`Scope → Evidence → Theory → Method → Execute →
> Verify → Communicate → Maintain`; see `cr-skill-research-workflow`). Each gate
> below enforces one earlier stage during execution: **Seed** guards
> reproducibility (Maintain), **Evidence and Provenance** the Evidence stage,
> **Measurement and Comparability** the Method stage, **Specification Logging**
> the Verify stage, and the **Normative-Decision Gate** the Scope stage. No gate
> behavior changes — this only names the stage each gate serves.

#### P0: Seed Enforcement (active during work)

Before executing any code that involves randomness, check for an explicit seed:
- R: `set.seed(<n>)` immediately before the random block
- Python: `np.random.seed(<n>)` or `random.seed(<n>)` before the random block; also add
  `torch.manual_seed(<n>)` when using PyTorch and `tensorflow.random.set_seed(<n>)` when using
  TensorFlow — both must be set when both frameworks are imported
- Stata: `set seed <n>` before the random block

**If seed is missing**: halt, add the seed, document it in the specification manifest.
**Seed value**: use a deterministic value (e.g., 42, 12345) and note it in comments.

**Lockfile verification**: Before running estimation, confirm the environment lockfile is
committed and current (`renv.lock` for R, `requirements.txt` / `pyproject.toml` / `uv.lock` for
Python, `code/ado/` for Stata via `repado`). If absent or out-of-date, flag and halt.

#### P0: Evidence and Provenance Enforcement (active during work)

For steps that ingest sources or emit substantive cited claims:

1. Ensure `c-research/evidence/` exists or create it on demand.
2. Maintain evidence artifacts:
  - `c-research/evidence/provenance-ledger.yaml`
  - `c-research/evidence/claim-evidence-matrix.yaml`
3. Enforce repo-local corpus by default. If external sources are used, require
  explicit `origin: external-opt-in` and `external_flag: true`.
4. Before emitting substantive claims, verify a corresponding matrix row exists
  and is marked `status: verified` with resolvable source and locator.
5. Never invent source metadata, quotes, DOIs, or locators. If unverifiable,
  mark `unverified`/`abstained` and halt for correction.

The original source document remains authoritative; converted text is an index.

#### P0: Measurement And Comparability Enforcement (active during work)

For Measurement/Classification tasks:

1. Ensure `c-research/measurement/` and `c-research/vintages/`
  exist or create them on demand.
2. Produce/update required artifacts:
  - `c-research/measurement/weighting-sensitivity.yaml`
  - `c-research/measurement/cluster-validity.yaml`
  - `c-research/vintages/<study-slug>-vintage-manifest.yaml`
3. Before asserting ranking or classification conclusions, verify those claims
  are supported by artifact summaries.
4. Block cross-vintage or cross-unit comparability claims unless coverage,
  harmonization, and method-change attribution are documented.
5. Treat undisclosed weighting for published rankings as blocking.

#### P0: Specification Logging (active during work)

When running estimation code, append to `c-research/results/manifest.json`.
Create the file and the `c-research/results/` directory if absent. Format:
```json
[
  {
    "date": "YYYY-MM-DD",
    "description": "Brief description of the specification",
    "file": "relative/path/to/script.R",
    "seed": 42
  }
]
```
If seed is not applicable (e.g., deterministic OLS), set `"seed": null`.
All four fields (`date`, `description`, `file`, `seed`) are **required**.
**Idempotency**: check whether an entry with the same (`file`, `date`) already exists before
appending. If it does, update it in-place rather than creating a duplicate.

<!-- Manifest schema is also documented in cr-skill-research-workflow/SKILL.md
     Section "Active P0 Detection Mechanisms > 2. Specification Logging".
     Keep both in sync when modifying the schema. -->

#### P0: Derivation Cross-Reference (Implementation tasks only)

When the plan step is an Implementation task:
1. Load the corresponding derivation from `c-research/derivations/`
2. Build a variable mapping table (derivation symbol → code variable)
3. Verify functional form consistency between derivation and code
4. Verify summation/integration limits match

If a discrepancy is found: halt, document it in a comment, and resolve before proceeding.

#### P0: Normative-Decision Gate (active during work)

Before implementing each step, deterministically walk the bounded per-task-type
value-laden decision-point taxonomy (from `cr-skill-research-scoping`). For each
decision point touched by the step, check coverage in the per-study register:
- `c-research/normative-decisions/<study-slug>.md`

Coverage is valid only if all hold:
- same `study` slug
- same decision category
- `applies_to` includes the current plan step or output artifact
- no contradiction with the proposed option

If covered: cite the existing decision ID and proceed.

If not covered: halt and re-escalate to the human for decision, then record a
new entry (`ND-<study-slug>-NNN`) with `study`, `plan`, `applies_to`,
`defensible_options`, `consequences`, `decided_by`, `decision`,
`justification`, and `decided_on` before continuing.

Never auto-default consequential normative choices.

Graceful degradation: run this gate even if Phase-1 evidence spine or Phase-2
measurement flags are absent.

#### Testing

Use the same test patterns as `/cg-work`. For research code, additionally:
- R: `testthat` for analytical functions
- Stata: `assert` + `reldif` for numerical verification
- All: test that random code produces identical output when seed is fixed

#### Commit Checkpoints

Same as `/cg-work` — suggest commits after each step using conventional commits:
`research(scope): description`

### Step 2.5: Phase Boundary

Same as `/cg-work` — update `completed-phases`, offer to continue.

### Step 3: Quality Checks

All `/cg-work` quality checks, plus:
- [ ] All random code blocks have explicit seeds
- [ ] Specification manifest is up to date
- [ ] Derivation cross-reference completed (if Implementation)
- [ ] Identification diagnostic present (if causal estimation)

### Step 3.2: Self-Review

Same as `/cg-work`. Remove debug code, check imports, resolve TODOs.

> "Mechanical self-review complete. **Statistical correctness and identification
> validity require domain review — run `/cr-review` before using results.**"

### Step 3.5: Mark Plan Complete

Same as `/cg-work` — set `status: completed`, add `completed-date`.

### Step 3.7: Update Roadmap Status

Same as `/cg-work`.

### Step 4: Summary

Provide a summary following the `/cg-work` format, then:

> **What would you like to do next?**
> 1. **`/cr-review`** — Run multi-agent research review (code quality + methodology)
> 2. **`/cr-compound`** — Capture a lesson from this work
> 3. **`/cr-plan`** — Plan the next research phase
> 4. **`/cg-review`** — Engineering-only review (skip methodology)

## Local Evidence Workbench Boundary

When a research plan uses repository-local sources, use this existing `/cr-work`
launcher to start or resume the dedicated `research_evidence/` workbench. Do
not create a second `/cr-evidence` launcher in v1.

Before substantive claims or downstream analysis are produced:

1. Use the `nextCommand` value in `.cg-docs/active-state/current.json` only to
  resume the workflow (for example, `/cr-work phase5`). Run Python package
  operations separately with `uv run --project research_evidence ...`, and
  keep `pyproject.toml`/`uv.lock` current.
2. Read only configured project-local resources. Internet search, URL fetching,
  external API model execution, hidden downloads, and external fallbacks are
  out of scope.
3. No external API execution is permitted in v1. Treat original source files as
  authoritative. Preserve source hash, source version, typed locator, quote,
  parser/OCR metadata, verification reason, confidence, and review history.
4. Preserve legacy `external-opt-in` records read-only in
  `external-quarantine.yaml`; never fetch, index, or approve them. A local copy
  needs a new local source-version record and verification event.
5. Keep local retrieval or model proposals as `candidate`. Reject fabricated
  source IDs, non-atomic statements, missing verbatim quotes, ambiguous
  locators, and paraphrases that cannot be independently verified.
6. Import downstream claims only after original-authority quote/locator
  verification and researcher approval. Stale, OCR, table/equation,
  inaccessible, and conflicting evidence remains flagged or abstained.

The workbench API/browser is a derived local management surface. Canonical YAML,
append-only history, journals, and original resources remain authoritative.
