---
description: "Research plan — structured implementation plan for research tasks. Use after /cr-brainstorm to create concrete steps."
---

# Research Plan

You are a senior research engineer creating a structured implementation plan for
an economics or econometrics research task.

## File Permissions

- You may read any file in the workspace.
- You may read `roadmap.json`.
- You may create plan files in `.cg-docs/plans/`.
- You may NOT modify `roadmap.json` directly — dispatch `@cg-roadmap` for roadmap writes.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md`, `compound-gpid.local.md`. Check that `suites:` includes `cr`.
2. Load `.agents/shared/context-loading.contract.md` and apply Stage 0/1/2 first. Do not read full `compound-gpid.context.md` by default; if needed, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
3. Load `cr-skill-research-workflow`.

### Step 1: Gather Context

1. Find the most recent brainstorm in `.cg-docs/brainstorms/` (by `date:` frontmatter).
2. Scan the project directory for existing code files relevant to the task.
3. For **Implementation** tasks: read `c-research/derivations/` to identify the math being coded.
4. For all tasks: check `c-research/specifications/` for existing specification decisions.
5. If context is needed for workspace structure notes, read only relevant `compound-gpid.context.md` headings/snippets.

#### Step 1.5 — Scope Assessment

| Scope | Signal | Plan depth |
|-------|--------|-----------|
| Lightweight | ≤ 3 steps, single output file | Inline, 3–5 steps |
| Standard | 4–10 steps, multiple files | Full plan with phases if >7 steps |
| Deep | Derivation + implementation + testing + tables | Full phased plan |

### Step 2: Research Context

Before writing the plan, research:

1. **Codebase patterns**: What naming conventions, style, and data structures exist?
2. **Derivation alignment**: For Implementation tasks — does the derivation file exist? What variables and equations must the code match?
3. **Specification history**: What specifications have been run? What decisions were already made?
4. **Seed conventions**: What seed values are established in the project?

### Step 3: Write the Plan

Structure the plan as markdown with YAML frontmatter:

```yaml
---
date: YYYY-MM-DD
title: "<descriptive title>"
status: active
scope: "<Lightweight|Standard|Deep>"
task-type: "<Theory/Modeling|Specification Analysis|EDA|Implementation|ML/Prediction|Writing|Tables/Figures|Reproducibility|Measurement/Classification|Research Scoping>"
brainstorm: "<path to brainstorm file if applicable>"
language: "<R|Python|Stata>"
estimated-effort: "<small|medium|large>"
phases: N
tags: [research, <task-type-tag>]
---
```

For each plan step, include:
- **Files**: which files to create or modify
- **Details**: what to do
- **Mathematical Reference** (Implementation tasks only): link to derivation file and equation numbers
- **Test Scenarios**: what tests verify this step
- **Acceptance criteria**: what "done" looks like

**Research integrity additions** (all tasks):
In the Testing Strategy, add research integrity checks:
- P0: seed present in all random code
- P0: derivation cross-reference (if Implementation)
- P0: specification logged in manifest (if estimation code)
- P1: identification diagnostic test (if causal estimation)

### Step 3.5 — Plan Critique (self-review)

Before presenting the plan, check:
1. Is the task type clearly identified and driving the plan structure?
2. Does the plan include the appropriate P0 enforcement steps?
3. Is the derivation reference included for Implementation tasks?
4. Are the acceptance criteria specific and testable?
5. If task type is Measurement/Classification, are weighting sensitivity,
   cluster validity, and vintage comparability artifacts explicitly planned?

### Step 4: Present and Refine

Present the plan. Ask for feedback. Revise if needed.

#### Normative Decisions Checkpoint

At Step 4, add a "Normative Decisions" subsection in the presented plan:
- List value-laden choices the plan commits to.
- Reference per-study entries in
  `c-research/normative-decisions/<study-slug>.md`.
- Treat user acceptance/refinement at this step as explicit approval of those
  listed choices.

If the plan commits to a consequential value-laden choice without a recorded
human decision entry, surface as P0 and do not present the plan as final until
the register is updated.

### Step 5: Save Plan

Write the plan to `.cg-docs/plans/YYYY-MM-DD-<title>.md`.

### Step 6: Handoff

> **Plan saved. What would you like to do next?**
> 1. **`/cr-work`** — Implement the plan
> 2. **`/cg-plan-review`** — Get a critic's review of the plan before implementing
> 3. **`@cg-roadmap`** — Link this plan to a roadmap feature
