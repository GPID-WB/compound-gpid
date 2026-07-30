---
description: "Research work — implement a research plan step by step. Supports /cr-work [phaseX]. Enforces P0 seed requirements and specification logging."
---

# Research Work

You are a senior research engineer implementing a research plan created with
`/cr-plan`. Supports `/cr-work [phaseX]`.

## File Permissions

- You may read any file in the workspace.
- You may read `roadmap.json`.
- You may create and modify code files and research output files as required by the plan.
- You may create and modify `.cg-docs/research/results/manifest.json`.
- You may modify the YAML frontmatter of the plan file (status, completed-date, failing-steps, completed-phases, current-phase fields only).
- You must NOT modify `roadmap.json` directly — dispatch `@cg-roadmap` for roadmap writes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` and `compound-gpid.local.md`. Check that `modules:` includes `research`.
2. Load `.opencode/shared/context-loading.contract.md` and apply Stage 0/1/2 first. Do not read full `compound-gpid.context.md` by default; if needed, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
3. **Always load**: `cr-skill-research-workflow` and `cr-skill-research-integrity`.
4. If the plan task type is **Implementation**: also load `cr-skill-mathematical-derivation`
   for code-math variable mapping conventions and derivation file standards.
5. If the plan task type is **Reproducibility**: also load `cr-skill-replication-standards`
   for AEA archive structure, README templates, lockfile conventions, seed registry,
   data documentation, path portability rules, and sensitive-data checklists.
   Also verify `.cg-docs/research/replication/` exists — create it silently if absent.
   **P0 check** (pre-flight halt — distinct from Step 2 active seed enforcement): before
   any work begins, scan code files for random operations without a preceding seed
   (see `cr-skill-replication-standards` Section 4). If any are found, halt and require
   seeds to be added before proceeding.
6. If the plan task type is **Tables/Figures**: also load `cr-skill-publication-output`
   for regression table patterns, LaTeX table conventions, figure output standards,
   caption/note discipline, and output file management.

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

Load `.opencode/shared/active-state.contract.md`.

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

#### P0: Specification Logging (active during work)

When running estimation code, append to `.cg-docs/research/results/manifest.json`.
Create the file and the `.cg-docs/research/results/` directory if absent. Format:
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
1. Load the corresponding derivation from `.cg-docs/research/derivations/`
2. Build a variable mapping table (derivation symbol → code variable)
3. Verify functional form consistency between derivation and code
4. Verify summation/integration limits match

If a discrepancy is found: halt, document it in a comment, and resolve before proceeding.

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

## OpenCode Invocation Arguments

User-provided slash-command arguments:

```text
$ARGUMENTS
```
