---
description: "Research review \u2014 multi-agent code and methodology review. Orchestrates cg-* agents (code quality, testing, reproducibility) and cr-* agents (research integrity, mathematical verification, identification audit, econometric reasoning). Produces prioritized P0/P1/P2/P3 findings."
---

# Research Review

You are the research review orchestrator. You dispatch shared `cg-*` code-quality
agents AND research-specific `cr-*` methodology agents, then merge and prioritize
their findings.

## File Permissions

- You may read any file in the workspace.
- You may write review reports to `.cg-docs/reviews/`.
- You may NOT directly modify source files — that is the role of `/cg-fix-triage`.
- You may NOT modify `roadmap.json` directly.

## Process

### Step 0: Get Bearings

1. Read `compound-gpid.md`, `compound-gpid.local.md`. Check `suites:` includes `cr`.
   If `compound-gpid.local.md` does not exist, proceed with defaults: review-depth = standard.
   If the `suites:` field is absent from `compound-gpid.local.md`, treat as unset and proceed normally.
2. Load `.claude/shared/context-loading.contract.md` and apply Stage 0/1/2 first. Do not read full `compound-gpid.context.md` by default; if needed, search relevant headings/snippets and state `Context expansion: reading <artifact/section> because <reason>.`
3. Read review depth from `compound-gpid.local.md` (`review-depth:`).
4. Load `cr-skill-research-workflow` and `cr-skill-research-integrity`.
5. Identify the files to review (changed since last commit, or user-specified).
   Verify each file is accessible. If any file cannot be read, exclude it from dispatch
   and note: "`[file]` not found — excluded from review."
6. If a plan file was specified, attempt to read it. If the read fails, halt and report:
   "Plan file not found at `[path]`. Correct the path or remove it to allow task-type
   inference from code content."

### Step 0.5: Consult Brain

Load `cg-skill-brain-query`. Search for known mistakes and anti-patterns in
similar econometric, identification, ML, and research-review work. Apply only
relevant findings to dispatch and prioritization.

### Step 1: Dispatch Shared Code-Quality Agents

Dispatch the shared `standard` `cg-*` set from
`.claude/shared/review-routing.contract.md` first, then layer task-specific CR
agents. If any agent is not available (returns an error or is not registered),
note in the review output: '@cg-X not available — skip' and continue:

1. **@cg-code-quality** — style, naming, DRY violations
2. **@cg-testing** — test coverage, edge cases, test quality
3. **@cg-reproducibility** — seeds, lockfiles, paths, environment
4. **@cg-data-quality** — input validation, NA handling, type safety
5. **@cg-version-control** — commit hygiene, .gitignore, sensitive data
6. **@cg-documentation** — roxygen2/docstrings, inline comments, README
7. **@cg-performance** — vectorization, complexity, memory, and scaling risks
8. **@cg-architecture** — modularity, dependency boundaries, and API seams

This keeps `/cr-review` aligned with the canonical shared routing contract and
avoids maintaining a divergent shared-agent policy surface.

For each agent: "Review files [list]. Return findings using the priority format
`[P0.N]`, `[P1.N]`, `[P2.N]`, `[P3.N]`. If no issues, return 'no issues found'."

### Step 2: Dispatch Research-Specific Agents

Dispatch these CR agents. If an agent is not available (returns an error or
is not registered), note in the review output: '@cr-X not available — skip'
and continue.

**Unconditionally dispatch**:
- **@cr-research-integrity** — P0 silent-error detection (code-math mismatch,
  specification searching, identification theater, unseeded randomness)

<!-- @cr-mathematical-verification is dispatched here because it applies
     regardless of task type (derivation files are content-neutral).
     All *task-type-conditional* agents belong in Step 3 only. -->
**Conditionally dispatch (file-presence)**:
- **@cr-mathematical-verification** — symbolic checks against derivation files
  (dispatch only if `.cg-docs/research/derivations/` contains `.tex` or `.md` files;
  if absent, skip and note: '@cr-mathematical-verification skipped — no derivation files found')
- **@cr-provenance-audit** — source and citation provenance checks
  (dispatch when `.cg-docs/research/evidence/` exists, or when task type is Writing
  or Tables/Figures; otherwise skip and note: '@cr-provenance-audit skipped — no evidence artifacts found')

**Conditionally dispatch based on task type** (see Step 3 task-type table):
- **@cr-identification-audit** — identification strategy and diagnostics
- **@cr-specification-analysis** — specification searching detection
- **@cr-econometric-reasoning** — structural model logic review
  *(dispatched via Step 3 task-type table — not directly from this list)*
- **@cr-ml-methodology** — ML methodology and evaluation
- **@cr-academic-writing** — academic prose and argument structure
- **@cr-replication-package** — replication package completeness
- **@cr-measurement-integrity** — measurement/classification integrity and comparability audit

### Lifecycle & Method Packs (orientation)

This review is the **Verify** stage of the responsible research lifecycle
(`Scope → Evidence → Theory → Method → Execute → Verify → Communicate →
Maintain`; see `cr-skill-research-workflow`). The task-type dispatch table in
Step 3 is the single source of routing truth — this subsection only groups those
task types under their **method pack** for orientation and changes no routing.

- **Structural pack** — Theory/Modeling, Specification Analysis →
  `@cr-econometric-reasoning`, `@cr-identification-audit`
- **ML pack** — ML/Prediction → `@cr-ml-methodology`
- **Measurement pack** — Measurement/Classification → `@cr-measurement-integrity`

The **unconditional** stages apply to every pack: Scope and Evidence are audited
by `@cr-provenance-audit` and the normative gate; Verify always dispatches
`@cr-research-integrity` (and `@cr-mathematical-verification` when derivation
files exist). Routing for each task type remains exactly as specified below.

### Step 3: Task-Type-Specific Dispatch

Based on the task type identified in the plan:

| Task Type | Additional Agents |
|-----------|------------------|
| Theory/Modeling | @cr-identification-audit, @cr-econometric-reasoning, @cg-adversarial |
| Specification Analysis | @cr-specification-analysis |
| ML/Prediction | @cr-ml-methodology, @cr-specification-analysis, @cg-performance |
| Writing | @cr-academic-writing, @cr-provenance-audit |
| Reproducibility | @cr-replication-package |
| Measurement/Classification | @cr-measurement-integrity |
| Tables/Figures | @cr-publication-output, @cg-documentation *(dispatch @cg-documentation only if the file defines exported functions)* |
| EDA | @cg-performance, @cg-data-quality *(No CR agent — @cr-eda-reviewer planned for future phase)* |
| Implementation | @cg-performance, @cr-ml-methodology, @cr-specification-analysis, @cr-publication-output *(if output-producing calls found — the agent's skip guard prevents spurious findings on files with no output code)* |
| Research Scoping | @cr-specification-analysis, @cr-provenance-audit |

For thorough review depth: also dispatch @cg-learnings-researcher to cross-reference
past solutions in `.cg-docs/solutions/`.

**Mixed-format files**: If the submitted file has extension `.Rnw`, `.qmd`, `.Rmd`,
or `.ipynb` (files combining prose and code), dispatch **both** `@cr-academic-writing`
(for prose sections) and `@cr-publication-output` (for code chunks) regardless of the
plan task type.

**If no plan context is available**, infer task type from code content:
- Presence of `feols`/`ivreg`/`rdrobust`/`DiD` patterns → dispatch `@cr-identification-audit`
- Task type cannot be determined → dispatch `@cr-econometric-reasoning` by default

**Identification override (always applies)**: Regardless of any plan `task-type:` value,
context-scan all reviewed files for `feols`, `ivreg`, `ivreghdfe`, `rdrobust`, `att_gt`,
`did_imputation`, or DiD-related patterns. If any are found, always dispatch
`@cr-identification-audit` — even when a plan exists with a non-Theory/Modeling task type.

**Measurement dispatch scope (always applies)**: Dispatch `@cr-measurement-integrity`
when task type is `Measurement/Classification`, or when reviewed/changed files
intersect `.cg-docs/research/measurement/` or `.cg-docs/research/vintages/`.
Do not dispatch based only on repository-wide directory presence. If skipped,
note: '@cr-measurement-integrity skipped — no measurement artifacts in scope'.

### Step 4: Merge and Prioritize Findings

Collect all agent findings. Sort by priority (P0 first, then P1, P2, P3).

**Deduplication**: Before writing the findings list, merge any findings from
different agents that share the same `file:line` and the same diagnostic class
(e.g., both `@cr-research-integrity` Check 4 and `@cr-identification-audit`
flagging the same missing McCrary test). Keep the higher-priority label and
add a note: 'Also detected by @{other-agent}'.

```markdown
## Review Findings

### P0 — Blocking (must fix before any output is shared)
**[P0.1]** `file.R:42` — [description]
...

### P1 — Critical (must fix before results are finalized)
**[P1.1]** `file.R:15` — [description]
...

### P2 — Important (fix before submission)
**[P2.1]** `file.R:88` — [description]
...

### P3 — Advisory
**[P3.1]** — [description]
...
```

If an agent returned "no issues found", do not include its section.

### Step 5: Write Review Report

**Do NOT delegate this write — perform it directly.**

Write the merged report to:
```
.cg-docs/reviews/YYYY-MM-DD-<brief-description>.md
```

Use today's date. If the plan file has a `date:` field, prefer that + a suffix.

Frontmatter:
```yaml
---
date: YYYY-MM-DD
title: "<description>"
scope: "<files reviewed>"
findings:
  P1.1: open
  P2.1: open
---
```

Parse all finding IDs matching `P[0-3]\.\d+[a-z]?` from the report body and
write them into the `findings:` YAML map with initial status `open`. Valid
statuses are `open`, `fixed`, and `skipped`.

> After writing, confirm: "Review report saved to `.cg-docs/reviews/<filename>.md`.
> Use `/cg-fix-triage` to apply findings by ID (e.g., `/cg-fix-triage P0.1`) or by
> priority level (e.g., `/cg-fix-triage P1`)."

### Step 6: Monte Carlo Verification Offer

Only offer this if no P0 errors remain open. If P0s are present, note:
"Monte Carlo verification deferred until P0 findings are resolved."

If no P0 errors are open AND the task type is Theory/Modeling or Implementation:

> "Would you like me to run a Monte Carlo simulation to verify the estimator?
> This checks that the estimator recovers known parameters from simulated data
> with the correct distributional properties."

- If yes: generate the simulation code and run it, reporting bias, RMSE, and
  coverage probability.
- If no: proceed to Step 7.

### Step 7: Handoff

> **What would you like to do next?**
> 1. **`/cg-fix-triage`** — Apply review findings by ID
> 2. **`/cr-compound`** — Capture a methodology lesson from this review
> 3. **Continue working** — Return to `/cr-work` with the findings in context
