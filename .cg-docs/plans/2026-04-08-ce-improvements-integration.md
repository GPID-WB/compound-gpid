---
date: 2026-04-08
title: "CE-inspired improvements: 3-phase reimplementation on dev"
status: active
brainstorm: ".cg-docs/brainstorms/2026-04-08-ce-improvements-integration.md"
language: "both"
estimated-effort: "large"
tags: [workflow, architecture, review-pipeline, prompts, agents, docs, tests]
---

# Plan: CE-Inspired Improvements — 3-Phase Reimplementation

## Objective

Incorporate all CE-inspired improvements from worktree
`copilot-worktree-2026-04-07T14-48-38` into the main codebase via a `dev`
branch, split into 3 clean, traceable commits. The worktree serves as the
specification; current main serves as the target. Every improvement is
reimplemented fresh against main's current file structure.

## Context

- Worktree: 2 monolithic commits, 27 files, +1,019/−425 lines
- Main: 13 commits ahead of merge base, 69 files diverged
- No feature from current main may be dropped
- No improvement from the worktree may be dropped without evaluation
- Work on `dev` branch; merge to main after full test suite passes

## Requirements

| ID  | Requirement                                                    | Source            |
|-----|----------------------------------------------------------------|-------------------|
| R1  | Add P0 severity tier to all review agents and orchestrator     | Worktree Phase 1  |
| R2  | Upgrade cg-data-quality: silent data corruption → P0           | Worktree Phase 1  |
| R3  | Upgrade cg-version-control: credential exposure → P0           | Worktree Phase 1  |
| R4  | Update copilot-instructions.md priority system                 | Worktree Phase 1  |
| R5  | Update docs/reference.md (P0 in review description)            | Worktree Phase 1  |
| R6  | Update docs/workflow.md (P0 in review description)             | Worktree Phase 1  |
| R7  | Update tests/prompt-tools.Tests.ps1 for P0 patterns            | Worktree Phase 1  |
| R8  | Create cg-adversarial.agent.md                                 | Worktree Phase 2  |
| R9  | Create cg-ideate.prompt.md                                     | Worktree Phase 2  |
| R10 | Create cg-compound-refresh.prompt.md                           | Worktree Phase 2  |
| R11 | Create docs/resume-templates.md (extracted from cg-resume)     | Worktree Phase 2  |
| R12 | Create docs/setup-templates.md (extracted from cg-setup)       | Worktree Phase 2  |
| R13 | Refactor cg-resume.prompt.md to reference resume-templates.md  | Worktree Phase 2  |
| R14 | Refactor cg-setup.prompt.md to reference setup-templates.md    | Worktree Phase 2  |
| R15 | Further trim cg-skill-r-testing/SKILL.md inline examples       | Worktree Phase 2  |
| R16 | Register new prompts/agents in copilot-instructions.md         | Worktree Phase 2  |
| R17 | Register new prompts/agents in docs/reference.md               | Worktree Phase 2  |
| R18 | Register new prompts/agents in docs/workflow.md                | Worktree Phase 2  |
| R19 | Add cg-adversarial to cg-review.prompt.md agents list + thorough tier | Worktree Phase 2 |
| R20 | Add Step 0.5 (prior work check) to cg-brainstorm.prompt.md    | Worktree Phase 3  |
| R21 | Add Step 1.1 (task classification) to cg-brainstorm.prompt.md  | Worktree Phase 3  |
| R22 | Add Step 1.5 (scope assessment) to cg-brainstorm.prompt.md     | Worktree Phase 3  |
| R23 | Add structured handoff with ask_user to cg-brainstorm          | Worktree Phase 3  |
| R24 | Add Step 0.5 (prior work check) to cg-plan.prompt.md           | Worktree Phase 3  |
| R25 | Add Step 1.5 (scope assessment) to cg-plan.prompt.md           | Worktree Phase 3  |
| R26 | Add requirements table to cg-plan template                     | Worktree Phase 3  |
| R27 | Add test scenarios (happy/edge/error) to cg-plan template      | Worktree Phase 3  |
| R28 | Add Step 4.5 (confidence check) to cg-plan.prompt.md           | Worktree Phase 3  |
| R29 | Add structured handoff with ask_user to cg-plan                | Worktree Phase 3  |
| R30 | Add inline plan generation (no plan exists) to cg-work         | Worktree Phase 3  |
| R31 | Add Step 2.2 (discover existing tests) to cg-work              | Worktree Phase 3  |
| R32 | Add Step 3.2 (self-review) to cg-work                          | Worktree Phase 3  |
| R33 | Add structured handoff with ask_user to cg-work                | Worktree Phase 3  |
| R34 | Add Step 1.5 (content-based depth overrides) to cg-review      | Worktree Phase 3  |
| R35 | Add autofix mode to cg-review                                  | Worktree Phase 3  |
| R36 | Add protected artifacts list to cg-review                      | Worktree Phase 3  |
| R37 | Add structured summary with ask_user to cg-review              | Worktree Phase 3  |
| R38 | Full test suite passes after each phase                        | User requirement   |
| R39 | No regressions to existing main features                       | User requirement   |

## Implementation Steps

### Step 0: Create dev branch

- **Requirements**: R38, R39
- **Details**: Create `dev/ce-improvements` branch from current main (`fa97cd5`).
  Run full test suite to establish baseline — all tests must pass before any changes.
- **Acceptance criteria**: Branch exists, tests pass

---

### Step 1: Phase 1 — P0 Priority System & Review Agent Hardening

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R38
- **Files to modify** (12 files):
  1. `.github/agents/cg-architecture.agent.md`
  2. `.github/agents/cg-code-quality.agent.md`
  3. `.github/agents/cg-data-quality.agent.md`
  4. `.github/agents/cg-documentation.agent.md`
  5. `.github/agents/cg-performance.agent.md`
  6. `.github/agents/cg-reproducibility.agent.md`
  7. `.github/agents/cg-testing.agent.md`
  8. `.github/agents/cg-version-control.agent.md`
  9. `.github/copilot-instructions.md`
  10. `.github/prompts/cg-review.prompt.md`
  11. `docs/reference.md`
  12. `docs/workflow.md`
- **Files to modify** (1 test file):
  13. `tests/prompt-tools.Tests.ps1`
- **Details**:

  **Agent files (1–8)**: In each agent's output format template, change
  `**[P1|P2|P3]**` → `**[P0|P1|P2|P3]**`. Add a P0 definition line after the
  closing ``` of the output format:
  `P0 = exploitable security vulnerability, silent data corruption, incorrect statistical results, or PII exposure.`

  Special cases:
  - `cg-data-quality`: Change the final line from
    `Silent data corruption is ALWAYS P1.` → two lines:
    `Silent data corruption is ALWAYS P0.`
    `Unvalidated inputs causing incorrect statistical results are ALWAYS P0.`
  - `cg-version-control`: In ### 1. Sensitive Data, change
    `- **P1 CRITICAL**: Are there API keys…` → `- **P0 BLOCKING**: Are there API keys…`
    (and the second P1 CRITICAL → P0 BLOCKING). Change final line from
    `Sensitive data findings are ALWAYS P1.` →
    `Sensitive data and credential exposure findings are ALWAYS P0.`

  **copilot-instructions.md (9)**: In ## Priority System for Review Findings,
  replace the 3-tier list with a 4-tier list:
  - `**P0 — BLOCKING**: Immediate remediation required. Exploitable security vulnerability, PII/credential exposure, silent data corruption, incorrect statistical results affecting published outputs.`
  - `**P1 — CRITICAL**: Must fix before merge. Bugs causing incorrect behavior, missing critical validation, error handling gaps.`
  - P2 and P3 unchanged.

  **cg-review.prompt.md (10)**:
  - Frontmatter description: change `P1/P2/P3` → `P0/P1/P2/P3`
  - Step 3 template: Add a `### P0 — BLOCKING (immediate remediation required)`
    section before P1 with `**[P0.1]**` template
  - After the template, add P0 criteria block (4 bullet points defining when P0 applies)
  - Step 3.5: Change finding ID parsing pattern from `**[P1.`, `**[P2.`, `**[P3.`
    → `**[P0.`, `**[P1.`, `**[P2.`, `**[P3.`
  - Step 4: Change "starting with P1" → "starting with P0, then P1"

  **docs/reference.md (11)**: Command table: change
  `Multi-agent code review with P1/P2/P3 findings` →
  `Multi-agent code review with P0/P1/P2/P3 findings`

  **docs/workflow.md (12)**: Review description: change
  `P1 (critical), P2 (important), P3 (minor)` →
  `P0 (blocking), P1 (critical), P2 (important), P3 (minor)`.
  Add `P0.1` to the compound ID examples.

  **tests/prompt-tools.Tests.ps1 (13)**:
  - Finding ID test: change regex `\[P[123]\.\d+\]` → `\[P[0123]\.\d+\]`
  - Update test description string to mention P0
  - Frontmatter parsing test: add `($content -match [regex]::Escape('**[P0.')) -and`
    to the chain

- **Test Scenarios**:
  - ✅ Happy path: Pester tests pass for P0 pattern detection
  - 🛑 Edge case: P0 definition line doesn't break agent file parsing
  - ❌ Error path: Regex `[P[0123]` correctly matches P0, doesn't match P4+
- **Tests**: Run `Invoke-Pester tests/prompt-tools.Tests.ps1 -Quiet`
- **Acceptance criteria**: All tests pass; every agent file has `P0|P1|P2|P3`
  format; copilot-instructions.md has 4-tier system (R1–R7)
- **Commit**: `feat(review): add P0 blocking severity tier to review pipeline`

---

### Step 2: Phase 2 — New Prompts, Agent & Template Extraction

- **Requirements**: R8–R19, R38
- **Files to create** (5 new files):
  1. `.github/agents/cg-adversarial.agent.md`
  2. `.github/prompts/cg-ideate.prompt.md`
  3. `.github/prompts/cg-compound-refresh.prompt.md`
  4. `docs/resume-templates.md`
  5. `docs/setup-templates.md`
- **Files to modify** (7 files):
  6. `.github/prompts/cg-resume.prompt.md` (extract templates)
  7. `.github/prompts/cg-setup.prompt.md` (extract templates)
  8. `.github/skills/cg-skill-r-testing/SKILL.md` (further trimming)
  9. `.github/copilot-instructions.md` (register new prompts)
  10. `.github/prompts/cg-review.prompt.md` (add cg-adversarial)
  11. `docs/reference.md` (add new entries)
  12. `docs/workflow.md` (add ideate step + compound-refresh)
- **Details**:

  **cg-adversarial.agent.md (1)**: Use worktree's file as specification. Create
  with frontmatter (name, description, model: Claude Sonnet 4.6, tools: [],
  user-invokable: false). Five focus areas: Input Boundaries, Data Corruption
  Vectors, Concurrency & State, Error Propagation, Security & Privacy. Output
  format uses P0/P1/P2 only (no P3). Rules section.

  **cg-ideate.prompt.md (2)**: Use worktree as spec. Model: Claude Opus 4.6.
  Steps: Get Bearings → Gather Signals (3 parallel explore agents) → Generate
  Ideas (8–12) → Adversarial Filter → Rank and Present → Handoff.

  **cg-compound-refresh.prompt.md (3)**: Use worktree as spec. Model: Claude
  Sonnet 4.6. Audits `.cg-docs/solutions/` for staleness, drift, consolidation.
  Classifies: Keep/Update/Consolidate/Replace/Delete. Archives to
  `.cg-docs/archive/`.

  **docs/resume-templates.md (4)**: Extract from cg-resume.prompt.md:
  Session Context Header (with/without charter), Pending Work Sections (all
  subsections), Next Action Suggestions. Adapt P0 references (pending review
  findings should include `<open-P0-count> blocking`).

  **docs/setup-templates.md (5)**: Extract from cg-setup.prompt.md:
  compound-gpid.local.md Template, compound-gpid.md Charter Template (with
  placeholder rules, field formatting rules), .cg-docs/ Directory Scaffold,
  roadmap.json Initial Skeleton, Setup Complete Message, Mode B scaffolds.

  **cg-resume.prompt.md (6)**: Replace inline template blocks (Session Context,
  Pending Work, Next Actions) with references to `docs/resume-templates.md`.
  Expected reduction: ~269 → ~169 lines. Preserve all Step logic.

  **cg-setup.prompt.md (7)**: Replace inline template blocks (A3, A3.5, A4,
  A5.5, A6, B1.2, B3) with references to `docs/setup-templates.md`.
  Expected reduction: ~456 → ~251 lines. Preserve all Step logic.

  **cg-skill-r-testing/SKILL.md (8)**: Trim Snapshot Testing section to
  1-line summary + reference link. Trim Mocking section to 1-line + reference.
  Trim Test Fixtures section to 1-line + reference. Remove some Quick Reference
  table rows (keep essential ones). Current: 427 lines → target: ~373 lines.

  **copilot-instructions.md (9)**: Add to Workflow Entry Points table:
  `| Discover what to work on next | /cg-ideate |`
  `| Refresh knowledge base | /cg-compound-refresh |`

  **cg-review.prompt.md (10)**: Add `'cg-adversarial'` to YAML agents list.
  Add to Thorough tier: `@cg-adversarial — Actively tries to break the code…`

  **docs/reference.md (11)**: Add to prompt table: cg-ideate (Claude Opus 4.6)
  and cg-compound-refresh (Claude Sonnet 4.6). Add to agent table:
  cg-adversarial (Sonnet 4.6, thorough only).

  **docs/workflow.md (12)**: Update loop diagram to include Ideate and Refresh.
  Add ### 0. Ideate section. Add ### 6b. Compound Refresh section.

- **Test Scenarios**:
  - ✅ Happy path: New files exist, prompt-tools tests pass, resume/setup still
    function with extracted templates
  - 🛑 Edge case: References to template files use correct paths
  - ❌ Error path: cg-review agents list correctly includes cg-adversarial
- **Tests**: Run full test suite via `tests/Run-Tests.ps1`
- **Acceptance criteria**: 5 new files exist; cg-resume reduced to ~169 lines;
  cg-setup reduced to ~251 lines; all tests pass (R8–R19)
- **Commit**: `feat(prompts): add ideation, adversarial review, compound-refresh; extract templates`

---

### Step 3: Phase 3 — Existing Prompt Enhancements (Smart Workflows)

- **Requirements**: R20–R37, R38
- **Files to modify** (4 files):
  1. `.github/prompts/cg-brainstorm.prompt.md`
  2. `.github/prompts/cg-plan.prompt.md`
  3. `.github/prompts/cg-work.prompt.md`
  4. `.github/prompts/cg-review.prompt.md`
- **Details**:

  **cg-brainstorm.prompt.md (1)**:
  - After Step 0 block, insert **Step 0.5: Check for Prior Work** — scan
    `.cg-docs/brainstorms/` for existing brainstorms matching the topic.
    Offer continue or start fresh.
  - After Step 1 (Lightweight Research), insert **Step 1.1: Task Classification**
    — classify as Software/Data task (proceed normally) or Non-software task
    (switch to Thinking Partner mode with adapted questions and handoff).
  - After Step 1.1, insert **Step 1.5: Scope Assessment** — classify as
    Lightweight/Standard/Deep. Tell user the scope, adapt question depth.
  - Replace Step 5c (Handoff) with structured `ask_user` pattern offering
    /cg-plan, charter update, and /cg-brainstorm options.

  **cg-plan.prompt.md (2)**:
  - After Step 0 block, insert **Step 0.5: Check for Prior Work** — scan
    `.cg-docs/plans/` for matching plans. Offer refine/follow-up/start fresh.
  - After Step 1 block, insert **Step 1.5: Scope Assessment** — classify as
    Lightweight/Standard/Deep. Adapt research depth and plan detail.
  - In Step 3 plan template:
    - Add `## Requirements` section with ID/Requirement/Source table between
      Context and Implementation Steps
    - Add `- **Requirements**: R1, R2` to each step template
    - Add `- **Test Scenarios**: ✅ Happy path / 🛑 Edge case / ❌ Error path`
    - Update acceptance criteria to reference requirement IDs
  - After Step 4, insert **Step 4.5: Confidence Check** — evaluate
    Completeness, Testability, Dependencies, Risk coverage, Scope clarity.
    Report confidence as High/Medium/Low.
  - Replace Step 6 (Handoff) with structured `ask_user` pattern offering
    /cg-work, /cg-review, /cg-brainstorm options.

  **cg-work.prompt.md (3)**:
  - In Step 1, add **"If no plan exists"** branch — generate lightweight
    inline plan (3–5 steps), present for confirmation, skip roadmap linking.
  - In Step 2, renumber and insert **Step 2.2: Discover existing tests** —
    search for related test files before coding (test-<module>.R, etc.).
  - In Step 2, update Step 2.4 (Test) to run discovered tests AND new tests.
  - After Step 3 quality checks, insert **Step 3.2: Self-Review** — search
    for leftover debug code (print, console.log, browser(), cat("DEBUG)),
    missing tests for new public functions, broken imports, incomplete TODOs.
  - Replace Step 4 final handoff with structured `ask_user` pattern offering
    /cg-review, /cg-compound, /cg-fixbug, /cg-plan options.

  **cg-review.prompt.md (4)**:
  - After Step 1, insert **Step 1.5: Content-Based Depth Overrides** with 4
    auto-escalation rules:
    1. Data pipeline → always include @cg-data-quality
    2. ≥50 non-test lines → escalate light→standard
    3. Security-sensitive → always include @cg-version-control
    4. Statistical output → always include @cg-data-quality + @cg-reproducibility
  - In Step 1, add `mode:autofix` argument parsing
  - In Step 4, add **Autofix Mode** branch: classify findings as safe_auto /
    manual / advisory. Auto-apply safe fixes, present manual ones, note advisory.
  - After Stata skill check block, add **Protected artifacts** list (5 items:
    .cg-docs/, compound-gpid.md, compound-gpid.local.md, roadmap.json,
    SCHEMA_VERSION) — discard findings recommending deletion of these.
  - Replace Step 5 summary with structured `ask_user` pattern.

- **Test Scenarios**:
  - ✅ Happy path: Each prompt's additions are syntactically valid markdown
  - 🛑 Edge case: Prior work detection with no existing brainstorms/plans
  - ❌ Error path: Autofix mode with zero findings produces clean summary
- **Tests**: Run full test suite via `tests/Run-Tests.ps1`
- **Acceptance criteria**: All 4 prompts have the new sections; no old sections
  removed; all tests pass (R20–R37)
- **Commit**: `feat(prompts): add smart workflows — prior work, scope assessment, auto-escalation, self-review`

---

### Step 4: Final Verification

- **Requirements**: R38, R39
- **Details**: Run full test suite. Verify no regressions. Review final diff
  summary. Prepare for merge to main.
- **Tests**: Full suite via `tests/Run-Tests.ps1`
- **Acceptance criteria**: All tests pass; diff against main shows only
  intentional additions; no file deletions that weren't template extractions

## Testing Strategy

- **After each phase**: Run full test suite (`tests/Run-Tests.ps1`)
- **Phase 1 specific**: `tests/prompt-tools.Tests.ps1` (P0 pattern matching)
- **Phase 2 specific**: `tests/prompt-tools.Tests.ps1` (new file detection if
  applicable), manual verification of template reference integrity
- **Phase 3 specific**: Manual review that all new sections are well-formed
  markdown with no orphaned references
- **Final**: Full test suite + manual diff review

## Documentation Checklist

- [ ] docs/reference.md updated with new prompts and agents
- [ ] docs/workflow.md updated with new loop and step descriptions
- [ ] copilot-instructions.md updated with new entry points and P0 system
- [ ] New prompt files include proper frontmatter (description, model)
- [ ] New agent file includes proper frontmatter (description, model, tools)

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Template extraction breaks cg-resume/cg-setup behavior | Medium | Verify references are exact; test manually by reading both prompt and template |
| P0 additions break existing test regex patterns | Low | Tests are updated in Phase 1 before any other changes |
| cg-review.prompt.md has too many additions → token bloat | Medium | Phase 1 (P0) and Phase 2 (cg-adversarial) are small additions; Phase 3 additions are structural, not content-heavy |
| Main branch receives more commits during dev work | Low | Dev branch is short-lived; rebase if needed before merge |
| Worktree improvements conflict with R dialect skills architecture | Low | R dialect skills are in separate files; worktree didn't touch them |

## Out of Scope

- Modifying R dialect skill files (cg-skill-r-collapse, cg-skill-r-datatable, etc.)
- Modifying cg-strategy.prompt.md
- Modifying PowerShell scripts (install.ps1, create-release.ps1, etc.)
- Modifying roadmap.json directly (use @cg-roadmap)
- Adding new tests beyond what's needed for P0 pattern matching
- Changing model tier assignments
