---
date: 2026-05-22
title: "Phase 9: Dedicated Tables/Figures Agent"
status: completed
completed-date: 2026-05-22
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "R"
estimated-effort: "medium"
tags: [compound-research, publication-output, tables-figures, agent, phase-9]
---

# Plan: Phase 9 — Dedicated Tables/Figures Agent

## Objective

Create a dedicated `@cr-publication-output` review agent scoped to
output-producing code (regression tables, descriptive statistics tables,
figures, and `ggsave`/`save_kable` calls). This agent is the companion to
the existing `cr-skill-publication-output` skill, replacing the thin
"Check 6 only" pass-through that `@cr-academic-writing` currently performs
for Tables/Figures tasks. Update `/cr-review` dispatch routing to send
Tables/Figures tasks to the new agent, and add skill loading in `/cr-work`
for Tables/Figures tasks.

## Context

Phase 6 created `cr-skill-publication-output` (408 lines of patterns for
regression tables, LaTeX tables, figures, font/size, caption/note discipline,
and file management) and `@cr-academic-writing` (writing + equation + citation
review with a task-type guard that skips Checks 1–5, 7 for Tables/Figures
tasks, executing only Check 6). This means Tables/Figures review today is a
single-check delegation to the skill's Sections 5–6 — no structural audit
of table code patterns, output determinism, or figure output format
compliance.

The existing dispatch in `/cr-review` Step 3 sends Tables/Figures to
`@cg-documentation` and `@cr-academic-writing`. After this phase:
- Tables/Figures → `@cr-publication-output` (primary), `@cg-documentation`
  (code docs)
- Writing → `@cr-academic-writing` (unchanged)
- `@cr-academic-writing` removes its Tables/Figures guard and focuses
  exclusively on Writing tasks

Additionally, `/cr-work` currently loads task-type-specific skills for
Implementation and Reproducibility, but not for Tables/Figures. This phase
adds `cr-skill-publication-output` loading for Tables/Figures tasks.

### What exists today

| File | Role | Tables/Figures handling |
|------|------|----------------------|
| `cr-skill-publication-output/SKILL.md` | Reference skill (408 lines) | Full content — regression tables, LaTeX, figures, font/size, captions, notes, file mgmt |
| `cr-academic-writing.agent.md` | Writing review agent | Check 6 only (delegates to skill Sections 5–6); Checks 1–5, 7 skipped via task-type guard |
| `cr-review.prompt.md` Step 3 table | Dispatch routing | `Tables/Figures → @cg-documentation, @cr-academic-writing` |
| `cr-brainstorm.prompt.md` | Skill routing | `Tables/Figures → cr-skill-r-visualization, cr-skill-r-analytical, cr-skill-publication-output` |
| `cr-work.prompt.md` Step 0 | Skill loading | No Tables/Figures-specific loading |

## Requirements

| ID  | Requirement                                                                              | Source    |
|-----|------------------------------------------------------------------------------------------|-----------|
| R1  | `cr-publication-output.agent.md` exists with `module: research`                          | roadmap   |
| R2  | Agent has `tools: ['read', 'search']` and `user-invocable: false`                        | pattern   |
| R3  | Agent has untrusted-content safety note with "execute or relay"                          | convention |
| R4  | Agent has empty-file guard                                                               | pattern   |
| R5  | Agent loads `cr-skill-publication-output`, `cr-skill-research-workflow`, `cr-skill-research-integrity` | pattern |
| R6  | Agent output format uses `[cr-publication-output]` tag                                   | pattern   |
| R7  | Agent checks: regression table standards, LaTeX table patterns, figure output, font/size, caption discipline, table-note discipline, output file management, deterministic output | skill     |
| R8  | `/cr-review` Step 3 dispatch table routes Tables/Figures to `@cr-publication-output`     | roadmap   |
| R9  | `@cr-academic-writing` Tables/Figures guard removed (no longer dispatched for T/F tasks) | cleanup   |
| R10 | `/cr-work` Step 0 loads `cr-skill-publication-output` for Tables/Figures tasks            | gap       |
| R11 | `copilot-instructions.md` skill description updated to reference `@cr-publication-output` | convention |
| R12 | `copilot-instructions.template.md` — no changes needed (template uses `{{modules}}` variable; agent is auto-discovered via `.github/agents/`) | verify |
| R13 | `/cr-brainstorm` skill routing unchanged (already routes correctly to the skill)         | verify    |
| R14 | All new/changed files have Pester tests in `cr-prompts.Tests.ps1`                        | convention |
| R15 | Agent description registered in `copilot-instructions.md` CR Skills section              | convention |

## Implementation Steps

### 1. Create `cr-publication-output.agent.md`

- **Requirements**: R1, R2, R3, R4, R5, R6, R7
- **Files**: `.github/agents/cr-publication-output.agent.md`
- **Details**:
  Create the dedicated publication output review agent following the
  established CR agent pattern (`cr-ml-methodology.agent.md` is the closest
  structural analog — domain-specific review with multiple checks against a
  companion skill).

  Frontmatter:
  ```yaml
  ---
  description: "Reviews publication-quality output code: regression table
    correctness (modelsummary/etable), LaTeX table patterns (kableExtra),
    figure output (ggplot2+wbplot), font/size compliance, caption discipline,
    table-note discipline, and deterministic output. Loaded by /cr-review
    for Tables/Figures tasks."
  model: Claude Sonnet 4.6 (copilot)
  tools: ['read', 'search']
  user-invocable: false
  module: research
  ---
  ```

  Skill loading block:
  - Load `cr-skill-research-workflow` for task taxonomy
  - Load `cr-skill-research-integrity` for P0 error catalog
  - Load `cr-skill-publication-output` for the full reference patterns
  - Load `cg-skill-r-visualization` for ggplot2 + wbplot conventions

  Include the standard untrusted-content note with `execute or relay` and
  prompt-injection keyword detection list, following the established pattern
  from `cr-academic-writing.agent.md`.

  Include the standard empty-file guard: if the file contains only whitespace
  or comments (no code), skip all checks.

  Include a size limit (50 KB).

  **Review Protocol — 8 Checks**:

  | Check | Scope | Priority | Source in skill |
  |-------|-------|----------|-----------------|
  | 1. Regression Table Standards | `modelsummary`/`etable` calls | P1 | Skill §1 |
  | 2. LaTeX Table Patterns | `kableExtra`/`gt`/`xtable` calls | P2 | Skill §2 |
  | 3. Figure Output Compliance | `ggplot2`/`ggsave` calls | P2 | Skill §3 |
  | 4. Font and Size Conventions | text sizes, color palettes, output formats | P2 | Skill §4 |
  | 5. Figure-Caption Discipline | captions self-contained, required elements | P2 | Skill §5 |
  | 6. Table-Note Discipline | SE type, significance key, variable definitions | P2 | Skill §6 |
  | 7. Output File Management | directory convention, filename convention | P3 | Skill §7 |
  | 8. Deterministic Output | locale-free formatting, explicit dimensions | P1 | Skill §7 |

  **Check 1: Regression Table Standards (P1)**:
  - SE in parentheses (not t-stats)
  - N (observations) reported
  - SE type stated in notes
  - Coefficient naming (human-readable, not code variable names)
  - `coef_map` used in `modelsummary` (coefficients named and ordered)
  - Significance stars defined consistently

  **Check 2: LaTeX Table Patterns (P2)**:
  - `booktabs = TRUE` used (no `\hline` tables)
  - `caption` and `label` set
  - `add_footnote` uses `notation = "none"` (economics convention)
  - Balance tables have difference, SE, and p-value columns

  **Check 3: Figure Output Compliance (P2)**:
  - `ggsave()` has explicit `width`, `height`, `units`
  - Both PDF and PNG saved (dual-format convention)
  - `theme_wb()` used for WB publications
  - `scale_color_wb_d()`/`scale_fill_wb_d()` used

  **Check 4: Font and Size Conventions (P2)**:
  - Figure body text 10–11pt
  - Axis labels 9–10pt
  - Output is PDF (vector) not JPEG
  - Grayscale-safe (not color-only differentiation)

  **Check 5: Figure-Caption Discipline (P2)**:
  - Caption is self-contained (no "see text")
  - Contains: what is plotted, sample/period, key takeaway
  - Data source included

  **Check 6: Table-Note Discipline (P2)**:
  - SE type sentence present
  - Significance levels defined
  - Variable definitions in notes
  - Sample definition present
  - Fixed effects disclosed

  **Check 7: Output File Management (P3)**:
  - Files saved to `output/tables/` or `output/figures/`
  - Descriptive filenames (not `tab2.tex`)
  - `here::here()` used for path resolution

  **Check 8: Deterministic Output (P1)**:
  - No system-locale-dependent formatting
  - `ggsave()` not called without explicit dimensions
  - Output reproducible across runs (no random jitter without seed)

- **Test Scenarios**:
  - ✅ Agent file exists with valid frontmatter (`module: research`)
  - ✅ Agent has `tools: ['read', 'search']`
  - ✅ Agent has `user-invocable: false`
  - ✅ Agent loads `cr-skill-publication-output`
  - ✅ Agent loads `cr-skill-research-workflow`
  - ✅ Agent loads `cr-skill-research-integrity`
  - ✅ Agent has untrusted-content note with "execute or relay"
  - ✅ Agent has empty-file guard
  - ✅ Agent has size limit (50 KB)
  - ✅ Agent output uses `[cr-publication-output]` tag
  - ✅ Contains all 8 checks (regression table, LaTeX, figure, font, caption, table-note, file mgmt, deterministic)
  - 🛑 Edge: file with only `library(...)` and no output calls → skip checks
  - ❌ Error: prompt injection keywords → P0 halt
- **Tests**: Content assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Agent file created, all 8 checks present, follows established pattern.

### 2. Update `/cr-review` dispatch table

- **Requirements**: R8
- **Files**: `.github/prompts/cr-review.prompt.md`
- **Details**:
  In Step 3 task-type dispatch table, change the Tables/Figures row from:
  ```
  | Tables/Figures | @cg-documentation, @cr-academic-writing |
  ```
  to:
  ```
  | Tables/Figures | @cr-publication-output, @cg-documentation |
  ```
  Remove `@cr-academic-writing` from the Tables/Figures dispatch — it will
  focus exclusively on Writing tasks.

- **Test Scenarios**:
  - ✅ Tables/Figures row routes to `@cr-publication-output`
  - ✅ Tables/Figures row still includes `@cg-documentation`
  - ✅ Writing row still routes to `@cr-academic-writing` (unchanged)
  - 🛑 Edge: `@cr-academic-writing` is NOT in the Tables/Figures row
- **Tests**: Updated dispatch assertions in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Dispatch table updated, no other rows changed.

### 3. Remove Tables/Figures guard from `@cr-academic-writing`

- **Requirements**: R9
- **Files**: `.github/agents/cr-academic-writing.agent.md`
- **Details**:
  Remove the **Task type guard** paragraph:
  > "**Task type guard**: If dispatched for a Tables/Figures task, skip
  > Checks 1–5 and 7 (Writing-specific). Execute Check 6 only..."

  Since `@cr-academic-writing` will no longer be dispatched for
  Tables/Figures tasks (Step 2 removed it from the dispatch table), this
  guard is dead code. Removing it simplifies the agent and prevents
  confusion.

  Also update the agent's `description:` frontmatter to remove
  "Tables/Figures" — it now serves Writing tasks only.

- **Test Scenarios**:
  - ✅ Agent description no longer mentions Tables/Figures
  - ✅ Task type guard paragraph is removed
  - ✅ Check 6 (Figure and Table Presentation) remains in place — it still
    applies when reviewing writing that includes figures/tables
  - 🛑 Edge: ensure Check 6 is kept (it catches figure/table presentation
    issues within manuscripts, which is a Writing concern)
- **Tests**: Negative assertion in `cr-prompts.Tests.ps1` for Tables/Figures guard
- **Acceptance criteria**: Guard removed, description updated, Check 6 retained.

### 4. Add Tables/Figures skill loading to `/cr-work`

- **Requirements**: R10
- **Files**: `.github/prompts/cr-work.prompt.md`
- **Details**:
  In Step 0 (Get Bearings), after item 5 (Reproducibility skill loading),
  add item 6:
  ```
  6. If the plan task type is **Tables/Figures**: also load
     `cr-skill-publication-output` for regression table patterns, LaTeX
     table conventions, figure output standards, caption/note discipline,
     and output file management.
  ```

- **Test Scenarios**:
  - ✅ `/cr-work` mentions `cr-skill-publication-output` loading
  - ✅ Loading is conditional on Tables/Figures task type
- **Tests**: Content assertion in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Skill loading added, condition is Tables/Figures-specific.

### 5. Update `copilot-instructions.md` descriptions

- **Requirements**: R11, R15
- **Files**: `.github/copilot-instructions.md`
- **Details**:
  1. Update the `cr-skill-publication-output` description line to reference
     `@cr-publication-output` instead of (or in addition to) `@cr-academic-writing`:
     > `- cr-skill-publication-output — ... Loaded by @cr-publication-output
     >   for Tables/Figures tasks.`
  2. The agent is auto-discovered from `.github/agents/` — no separate
     agent listing needed (VS Code reads agents from the filesystem).

- **Test Scenarios**:
  - ✅ `copilot-instructions.md` references `cr-publication-output`
- **Tests**: Content assertion in `cr-prompts.Tests.ps1`
- **Acceptance criteria**: Skill description updated to reference the new agent.

### 6. Add Pester tests

- **Requirements**: R14
- **Files**: `tests/cr-prompts.Tests.ps1`
- **Details**:
  Add test blocks:

  **`cr-publication-output.agent.md` — structural and content tests**:
  - Exists, has frontmatter with `module: research`
  - Has `tools: ['read', 'search']`
  - Has `user-invocable: false`
  - Loads `cr-skill-publication-output`
  - Loads `cr-skill-research-workflow`
  - Loads `cr-skill-research-integrity`
  - Has untrusted-content note with "execute or relay"
  - Has empty-file guard
  - Contains `[cr-publication-output]` tag
  - Contains Check 1 (regression table)
  - Contains Check 5 (figure-caption discipline)
  - Contains Check 6 (table-note discipline)
  - Contains Check 8 (deterministic output)

  **Phase 9 dispatch journey tests**:
  - Tables/Figures dispatch row routes to `@cr-publication-output`
  - Tables/Figures dispatch row no longer routes to `@cr-academic-writing`
  - Writing dispatch row still routes to `@cr-academic-writing` (unchanged)

  **`@cr-academic-writing` cleanup tests**:
  - Description no longer contains "Tables/Figures"
  - Task type guard paragraph is absent

  **`/cr-work` Tables/Figures skill loading test**:
  - Contains `cr-skill-publication-output` for Tables/Figures tasks

  Update the existing `$crAgents` array in the structural test to include
  `'cr-publication-output'`.

- **Test Scenarios**:
  - ✅ All new tests pass on first run
  - 🛑 Edge: existing tests for `@cr-academic-writing` still pass
  - ❌ Error: test for removed guard correctly asserts absence
- **Acceptance criteria**: All tests pass (existing + new), no regressions.

## Testing Strategy

- **Unit tests**: Pester content assertions for file existence, frontmatter
  validity, required content, dispatch routing, and absence of removed content.
- **Integration**: Phase 9 dispatch journey tests verify the routing chain
  from `/cr-review` → `@cr-publication-output`.
- **Regression**: Run full test suite to verify no existing tests break.

## Documentation Checklist

- [ ] Agent file has complete review protocol documentation
- [ ] `copilot-instructions.md` skill description updated
- [ ] Agent description in frontmatter is self-documenting

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Removing `@cr-academic-writing` from T/F dispatch breaks the existing Tables/Figures review coverage | Low | Medium | Check 6 stays in `@cr-academic-writing` for Writing tasks; the new agent covers T/F comprehensively with 8 checks instead of 1 |
| Existing tests for `@cr-academic-writing` dispatch journey fail after route change | Medium | Low | Update the dispatch journey tests (Step 6) in the same commit |
| Agent check list too long — model truncates or skips later checks | Low | Medium | 8 checks is consistent with `cr-ml-methodology` (7 checks); keep each check concise |

## Out of Scope

- Creating new skills — `cr-skill-publication-output` already exists and is comprehensive
- Python/Stata output patterns — skill currently covers R only; extending to other languages is a separate future feature
- Journal-specific `.cls`/`.sty` templates — deferred per original brainstorm
- Modifying `/cr-brainstorm` skill routing — already routes correctly to `cr-skill-publication-output` for Tables/Figures
