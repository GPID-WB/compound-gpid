---
date: 2026-05-22
title: "Compound Research Phase 7: Reproducibility & Replication Package"
status: completed
completed-date: 2026-05-22
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "R"
estimated-effort: "medium"
tags: [research, reproducibility, replication, agent, skill, compound-research]
---

# Plan: Compound Research Phase 7 — Reproducibility & Replication Package

## Objective

Create the `cr-skill-replication-standards` skill and `@cr-replication-package`
agent so that the Reproducibility task type (the 8th in the research taxonomy)
is fully functional — from brainstorm skill routing through work execution to
review dispatch. This bridges the engineering-level reproducibility already
provided by `@cg-reproducibility` (seeds, lockfiles, paths) with
journal-submission-grade replication-package auditing (AEA/AER standards,
5-year READMEs, data documentation, runtime estimates, archive completeness).

## Context

- Phases 1–6 of compound-research are complete and committed on the
  `compound-research` branch (2270/2270 tests passing).
- The Reproducibility task type is defined in `cr-skill-research-workflow`
  and recognized by `cr-brainstorm.prompt.md` (with clarifying questions for
  journal standards, data sensitivity, and target compute environment).
- `cr-review.prompt.md` has placeholder annotations: `@cr-replication-package
  *(Phase 7)*` in Step 2 and the Step 3 dispatch table.
- `cr-brainstorm.prompt.md` currently routes Reproducibility to
  `cr-skill-git-workflow` + `cg-skill-pester-safety` — these must be replaced
  with `cr-skill-replication-standards`.
- `cr-work.prompt.md` has no Reproducibility-specific skill loading or P0
  checks — needs a conditional load clause.
- `@cg-reproducibility` (Haiku 4.5, shared module) handles engineering
  reproducibility. The new `@cr-replication-package` (Sonnet 4.6, research
  module) handles journal-submission replication auditing.

## Requirements

| ID  | Requirement                                              | Source            |
|-----|----------------------------------------------------------|-------------------|
| R1  | Create `cr-skill-replication-standards` skill with AEA/AER replication standards, README templates, lockfile conventions, seed lists, runtime estimates, data documentation, sensitive-data handling | brainstorm |
| R2  | Create `@cr-replication-package` agent that audits replication archives against the skill's standards | brainstorm |
| R3  | Update `cr-brainstorm.prompt.md` to route Reproducibility to `cr-skill-replication-standards` | brainstorm |
| R4  | Update `cr-work.prompt.md` to load `cr-skill-replication-standards` for Reproducibility tasks | brainstorm |
| R5  | Update `cr-review.prompt.md` to remove Phase 7 placeholders and enable `@cr-replication-package` dispatch | brainstorm |
| R6  | Update `copilot-instructions.md` and `docs/reference.md` to register the new skill and agent | convention |
| R7  | Add Pester tests for skill content, agent frontmatter, prompt integration, and dispatch routing | convention |

## Implementation Steps

### 1. Create `cr-skill-replication-standards` skill

- **Requirements**: R1
- **Files**: `.github/skills/cr-skill-replication-standards/SKILL.md` (new)
- **Details**:
  - Frontmatter: `name`, `module: research`, `description` (within length cap)
  - Section 1: AEA Data and Code Availability Policy — directory structure
    conventions (`/code/`, `/data/raw/`, `/data/derived/`, `/output/`),
    master-script pattern (`main.R`/`main.do`/`main.py`), expected runtime
    documentation, software/hardware requirements
  - Section 2: README for Replication — long-lived README template covering
    data sources (with access instructions), software requirements (with
    versions), instructions to replicate (step-by-step), expected output,
    computational requirements (runtime, memory, storage), data citations
  - Section 3: Dependency lockfiles — `renv.lock` for R, `uv.lock`/
    `poetry.lock` for Python, `code/ado/` for Stata (via `repado`). Rule:
    every language used must have a committed lockfile
  - Section 4: Seed management — seed registry pattern (single file listing
    all seeds and where they're used), cross-reference with
    `.cg-docs/research/results/manifest.json`
  - Section 5: Data documentation — codebook (variable names, types,
    definitions, units, missingness), data dictionary, data access
    instructions for restricted-access data, PII/sensitivity checklist
  - Section 6: Absolute-path and platform-portability checks — forbidden
    patterns (`C:\`, `/Users/`, `~`, hardcoded home), required patterns
    (`here::here()`, `pathlib.Path`, `reproot`)
  - Section 7: Sensitive-data handling — `.gitignore` rules for data,
    synthetic/simulated data alternatives, data-use-agreement documentation,
    de-identification verification
  - Section 8: Archive packaging — file inventory checklist, what to include
    vs exclude, compression and submission conventions
  - Section 9: Review criteria — bulleted checklist the agent uses to audit
    (maps to agent checks)
- **Test Scenarios**:
  - ✅ Happy path: skill loads and contains all 9 sections
  - 🛑 Edge case: description within length cap
  - ❌ Error path: missing `module: research` tag
- **Tests**: frontmatter validity, section headings present, description
  length, module tag
- **Acceptance criteria**: `SKILL.md` exists, has valid frontmatter, all 9
  sections present

### 2. Create `@cr-replication-package` agent

- **Requirements**: R2
- **Files**: `.github/agents/cr-replication-package.agent.md` (new)
- **Details**:
  - Frontmatter: `description`, `model: Claude Sonnet 4.6 (copilot)`,
    `tools: ['read', 'search']`, `user-invocable: false`, `module: research`
  - Load instructions: `cr-skill-research-workflow`,
    `cr-skill-research-integrity`, `cr-skill-replication-standards`
  - Untrusted-content note (standard prompt-injection guard)
  - Empty-file guard (standard)
  - Review Protocol with 8 checks:
    1. **Archive structure (P1)** — directory layout matches AEA convention,
       master script exists and is runnable
    2. **README completeness (P1)** — all required sections present (data
       sources, software, instructions, runtime, data citations)
    3. **Dependency lockfiles (P1)** — every language used has a committed
       lockfile
    4. **Seed registry (P0)** — all random operations have documented seeds,
       cross-referenced with manifest.json
    5. **Data documentation (P1)** — codebook present, variable definitions
       complete, access instructions for restricted data
    6. **Path portability (P1)** — no absolute paths, no platform-specific
       paths
    7. **Sensitive data (P0)** — no PII in committed files, data-use
       agreements documented, `.gitignore` covers data directories
    8. **File inventory (P2)** — all files referenced in README exist, no
       orphan files in archive that aren't documented
  - Output format: standard P0/P1/P2/P3 finding format (same as other
    CR agents)
- **Test Scenarios**:
  - ✅ Happy path: agent dispatches and returns findings
  - 🛑 Edge case: no `.cg-docs/research/replication/` directory exists
  - ❌ Error path: prompt injection in research files
- **Tests**: frontmatter fields, model assignment, module tag, tool
  restrictions, load instructions present, check count, untrusted-content
  guard, empty-file guard
- **Acceptance criteria**: agent file exists with valid frontmatter, all 8
  checks documented, security guards present

### 3. Update `cr-brainstorm.prompt.md` — skill routing

- **Requirements**: R3
- **Files**: `.github/prompts/cr-brainstorm.prompt.md` (modify)
- **Details**:
  - Change Reproducibility skill routing from
    `cr-skill-git-workflow`, `cg-skill-pester-safety` to
    `cr-skill-replication-standards`
  - The clarifying questions for Reproducibility (journal standards, data
    sensitivity, compute environment) are already correct — no change needed
- **Test Scenarios**:
  - ✅ Happy path: skill routing line matches `cr-skill-replication-standards`
  - 🛑 Edge case: old routing text removed completely
- **Tests**: content assertion for new routing, negative assertion for old
  routing
- **Acceptance criteria**: Reproducibility routes to
  `cr-skill-replication-standards` only

### 4. Update `cr-work.prompt.md` — skill loading for Reproducibility

- **Requirements**: R4
- **Files**: `.github/prompts/cr-work.prompt.md` (modify)
- **Details**:
  - Add a conditional load clause alongside the existing Implementation
    clause (line ~29): "If the plan task type is **Reproducibility**: also
    load `cr-skill-replication-standards`"
  - Add a Reproducibility-specific P0 check in the pre-execution section:
    verify `.cg-docs/research/replication/` directory exists (create if
    absent), verify seed registry cross-references manifest.json
- **Test Scenarios**:
  - ✅ Happy path: Reproducibility task loads the skill
  - 🛑 Edge case: skill loads only for Reproducibility, not other types
- **Tests**: content assertion for conditional load clause, content assertion
  for replication directory check
- **Acceptance criteria**: `cr-work.prompt.md` loads
  `cr-skill-replication-standards` for Reproducibility tasks

### 5. Update `cr-review.prompt.md` — enable `@cr-replication-package` dispatch

- **Requirements**: R5
- **Files**: `.github/prompts/cr-review.prompt.md` (modify)
- **Details**:
  - Step 2: Remove `*(Phase 7 — not yet available)*` annotation from
    `@cr-replication-package` line
  - Step 3 dispatch table: Remove `*(Phase 7)*` from Reproducibility row,
    leaving `@cr-replication-package` as the active dispatch target
  - Keep the conditional dispatch pattern (dispatch only when task type is
    Reproducibility)
- **Test Scenarios**:
  - ✅ Happy path: Phase 7 annotations removed, agent is active
  - 🛑 Edge case: no regression in other dispatch rows
- **Tests**: negative assertion for `Phase 7` annotation, positive assertion
  for `@cr-replication-package` without annotation
- **Acceptance criteria**: `@cr-replication-package` is dispatched for
  Reproducibility tasks without Phase 7 qualifier

### 6. Update documentation and add tests

- **Requirements**: R6, R7
- **Files**:
  - `.github/copilot-instructions.md` (modify) — add `cr-skill-replication-standards` to CR skills list
  - `docs/reference.md` (modify) — add skill and agent entries
  - `tests/cr-prompts.Tests.ps1` (modify) — add Describe blocks for new
    skill and agent, add integration tests for prompt updates
- **Details**:
  - `copilot-instructions.md`: Add `cr-skill-replication-standards` entry in
    the "Compound Research (CR) Skills" section with description and load
    context
  - `docs/reference.md`: Add entries for `cr-skill-replication-standards`
    and `@cr-replication-package`
  - Tests to add:
    - **Skill tests**: frontmatter validity (`name`, `module`, `description`),
      section headings (all 9), description length within cap
    - **Agent tests**: frontmatter fields (`description`, `model`, `tools`,
      `user-invocable`, `module`), model is Sonnet 4.6, tools are
      `['read', 'search']`, untrusted-content guard present, empty-file
      guard present, check count (8 checks), load instructions for 3 skills
    - **Prompt integration tests**: `cr-brainstorm.prompt.md` routes
      Reproducibility to `cr-skill-replication-standards` (positive),
      does not route to `cg-skill-pester-safety` for Reproducibility
      (negative); `cr-work.prompt.md` contains Reproducibility conditional
      load; `cr-review.prompt.md` does not contain `Phase 7` annotation
      (negative), does contain `@cr-replication-package` without qualifier
      (positive)
    - **Dispatch table test**: Reproducibility row dispatches
      `@cr-replication-package` (update existing Phase 7 annotation test)
- **Test Scenarios**:
  - ✅ Happy path: all tests pass
  - 🛑 Edge case: existing tests unbroken
- **Acceptance criteria**: all new and existing tests pass

## Testing Strategy

- Follow the established pattern from Phases 3–6: structural Pester tests
  for frontmatter, section headings, content assertions, and dispatch routing.
- Run full test suite via `. tests/Run-Tests.ps1` at the end of
  implementation.
- Key assertion categories:
  1. Skill file exists with correct frontmatter and all sections
  2. Agent file exists with correct frontmatter, security guards, and checks
  3. Prompt skill routing is updated (positive and negative assertions)
  4. Dispatch table annotations are removed
  5. Documentation entries exist

## Documentation Checklist

- [x] Skill file has frontmatter description
- [ ] `copilot-instructions.md` updated with skill entry
- [ ] `docs/reference.md` updated with skill and agent entries
- [ ] Agent load instructions reference the skill

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Existing Phase 7 annotation tests break when annotations are removed | High | Update the existing annotation test to assert absence instead of presence |
| `@cg-reproducibility` and `@cr-replication-package` overlap on seed/lockfile checks | Medium | Clearly delineate: `@cg-reproducibility` = engineering checks (seeds exist, lockfiles committed, paths relative); `@cr-replication-package` = journal-submission checks (archive structure, README completeness, data documentation, runtime estimates). Agent description makes this explicit |
| Skill content too long for context window | Low | Follow existing skill pattern — reference sections, not full specifications. Keep under 400 lines |

## Out of Scope

- Docker/container environment for replication (future enhancement)
- Automated replication-package generation (this phase is auditing only)
- Journal-specific `.cls`/`.sty` templates
- Data download automation
- CI/CD integration for replication verification
