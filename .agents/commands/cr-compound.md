---
description: "Research compound \u2014 capture a solved research problem for future reuse. Extends /cg-compound with research-specific categories: identification, specification, derivation, ml-methodology, reproducibility."
---

# Research Compound

You are capturing a solved research problem as reusable institutional knowledge.
This mirrors `/cg-compound` with an extended category list for economics and
econometrics work.

## File Permissions

- You may read any file in the workspace.
- You may create solution files in `.cg-docs/solutions/`.
- You may NOT modify code or analysis files.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md` and `compound-gpid.local.md`. Check that `suites:` includes `cr`.
If `compound-gpid.local.md` does not exist or `suites:` does not include `cr`, warn:
   > "Research module is not enabled. Run `/cg-setup` to add it, or proceed anyway?"
2. Load `.agents/shared/context-loading.contract.md` and apply Stage 0/1/2 first. Do not read full `compound-gpid.context.md` by default; if needed, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
3. Load `cg-skill-compound-docs` for the capture conventions.

### Step 1: Capture the Problem

Ask the user:
1. **What was the problem?** (1–2 sentences)
2. **What was the solution?** (code snippet, procedure, or key insight)
3. **Why does this work?** (brief explanation)
4. **What are the failure modes?** (when this solution doesn't apply)

### Step 2: Select Category

Choose the most specific matching category:

**Research categories** (preferred for economics/econometrics work):
| Category | When to use |
|----------|-------------|
| `identification` | Solutions to identification problems (IV validity, RDD validity, DiD assumptions) |
| `specification` | Specification choices with theoretical justification (functional form, control selection) |
| `derivation` | Analytical derivations: proofs, algebraic manipulations, limit results |
| `ml-methodology` | ML applications in economics (causal ML, prediction with interpretation) |
| `reproducibility` | Replication package setup, seed management, environment isolation |

**Engineering categories** (inherited from `/cg-compound`):
| Category | When to use |
|----------|-------------|
| `bugs` | Code defects and their fixes |
| `build-errors` | Environment, package, or compilation errors |
| `performance-issues` | Slow code and optimization solutions |
| `testing-patterns` | Test structure and assertion patterns |
| `data-quality` | Data cleaning, imputation, validation patterns |
| `environment-issues` | renv, conda, virtual environment problems |
| `git-workflows` | Version control patterns and recovery |

### Step 3: Write the Solution File

Write to `.cg-docs/solutions/<category>/YYYY-MM-DD-<brief-title>.md`:

```yaml
---
date: YYYY-MM-DD
title: "<descriptive title>"
category: "<category>"
task-type: "<Theory/Modeling|Specification Analysis|EDA|Implementation|ML/Prediction|Writing|Tables/Figures|Reproducibility|Measurement/Classification|Research Scoping>"
tags: [<relevant tags>]
---
```

Include:
- **Problem statement** — what went wrong or was unclear
- **Solution** — the fix or approach with code examples
- **Why it works** — the principle or mechanism
- **When to use** — applicability conditions
- **When NOT to use** — failure modes and counter-examples
- **References** — relevant papers, packages, or documentation

### Step 4: Confirm and Handoff

Confirm the file was written. Then:

> "Lesson captured in `.cg-docs/solutions/<category>/<filename>.md`.
> This will be surfaced by `@cg-learnings-researcher` in future thorough reviews."

> **What would you like to do next?**
> 1. **Continue working** — return to `/cr-work` or `/cr-plan`
> 2. **`/cr-compound`** — Capture another lesson
> 3. **`/cg-compound-refresh`** — Audit and consolidate all captured lessons
