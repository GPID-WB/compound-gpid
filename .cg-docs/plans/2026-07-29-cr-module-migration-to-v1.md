---
date: 2026-07-29
title: "Compound Research module migration to v1.0"
status: active
scope: "Deep"
phases: 8
brainstorm: ".cg-docs/brainstorms/2026-07-29-cr-module-migration-to-v1.md"
language: "both"
estimated-effort: "large"
tags: [migration, compound-research, v1-integration, git-workflow, codex-adapter]
deviation-policy: ask
completed-phases: [0, 1]
current-phase: 2
execution-report: ".cg-docs/work-reports/2026-07-29-cr-module-migration-to-v1.md"
---

# Plan: Compound Research Module Migration to v1.0

## Objective

Port the Compound Research (CR) module — 9 agents, 12 skills, 5 prompts, 2 instruction files, and associated .cg-docs artifacts — from the stale `compound-research` branch (v0.10.2) onto a fresh branch from `origin/main` (v1.0.3), then integrate CR with all v1.0 systems (brain, review routing, model catalog, context-loading contracts, active-state, and multi-target generation).

## Context

- The `compound-research` branch is 61 commits ahead / 268 commits behind `origin/main`
- 61 files were modified by both branches — merge/rebase is impractical
- Main v1.0 added: `.agents/` Codex adapter, `.github/shared/` contracts, Brain system, model frontmatter, multi-target generation (`cg_generate_targets.py`)
- The CR intellectual content (research logic, agent behaviors, skill content) is portable; integration glue must be re-applied against v1.0
- `.github/` remains the canonical source; `.agents/`, `.claude/`, `.opencode/` are generated targets

## Requirements

| ID  | Requirement | Source |
|-----|-------------|--------|
| R1  | All CR-only files ported verbatim to new branch from main | brainstorm |
| R2  | .cg-docs/ artifacts carried over as historical documentation | brainstorm |
| R3  | CR module registered in copilot-instructions.md and template | brainstorm |
| R4  | CR prompts adopt context-loading.contract.md staged policy | review finding |
| R5  | Review routing contract extended with research mode | brainstorm |
| R6  | /cg-review dispatches CR agents for research tasks | brainstorm |
| R7  | All CR agents get model: frontmatter per model-catalog conventions | brainstorm |
| R8  | Brain consultation wired into CR prompts | brainstorm |
| R9  | Active-state contract adopted by /cr-work | review finding |
| R10 | Multi-target generation (cg_generate_targets.py) produces CR entries | brainstorm |
| R11 | All existing main tests continue passing | brainstorm |
| R12 | cr-prompts.Tests.ps1 updated and passing | brainstorm |
| R13 | Existing cg-* agents/prompts modified to be research-aware | brainstorm |

## Implementation Steps

## Phase 0: Baseline Verification

### 1. Create fresh branch from origin/main and inspect v1.0 state
- **Requirements**: R1
- **Files**: (git operations + read-only inspection)
- **Details**:
  ```bash
  git checkout -b feat/compound-research-v2 origin/main
  ```
  Then inspect and document:
  - `.github/shared/` — confirm all contracts exist: `context-loading.contract.md`, `review-routing.contract.md`, `active-state.contract.md`, `model-catalog.json`
  - `.github/skills/` — identify Brain skill exact name (search for `brain-query` or `brain`)
  - `scripts/cg_generate_targets.py` — confirm existence, read invocation signature
  - `tests/model-assignments.Tests.ps1` — read current count sentinels (prompt count, agent count)
  - `tests/prompt-tools.Tests.ps1` — check what structural assertions apply to all prompts
  - `.github/copilot-instructions.template.md` — check if `{{modules}}` already exists
  - `.github/instructions/r.instructions.md` — check if `module:` frontmatter already present
  - `cg-review.prompt.md` — locate Brain consultation step and pattern
- **Acceptance criteria**: All integration dependencies confirmed or gaps documented. Exact sentinel values recorded. Brain skill name confirmed. Generation script invocation known. Gate: if any critical system is missing or structurally different from expectations, revise affected phases before proceeding.

## Phase 1: Port CR Content

### 2. Cherry-pick CR-only .github/ files
- **Requirements**: R1
- **Files**: (git operations only)
- **Details**:
  ```bash
  git checkout -b feat/compound-research-v2 origin/main
  ```
- **Acceptance criteria**: New branch exists at v1.0.3 HEAD

### 2. Cherry-pick CR-only .github/ files
- **Requirements**: R1
- **Files to add** (29 files):
  - `.github/agents/cr-academic-writing.agent.md`
  - `.github/agents/cr-econometric-reasoning.agent.md`
  - `.github/agents/cr-identification-audit.agent.md`
  - `.github/agents/cr-mathematical-verification.agent.md`
  - `.github/agents/cr-ml-methodology.agent.md`
  - `.github/agents/cr-publication-output.agent.md`
  - `.github/agents/cr-replication-package.agent.md`
  - `.github/agents/cr-research-integrity.agent.md`
  - `.github/agents/cr-specification-analysis.agent.md`
  - `.github/prompts/cr-brainstorm.prompt.md`
  - `.github/prompts/cr-compound.prompt.md`
  - `.github/prompts/cr-plan.prompt.md`
  - `.github/prompts/cr-review.prompt.md`
  - `.github/prompts/cr-work.prompt.md`
  - `.github/skills/cr-skill-academic-writing/SKILL.md`
  - `.github/skills/cr-skill-identification-strategies/SKILL.md`
  - `.github/skills/cr-skill-mathematical-derivation/SKILL.md`
  - `.github/skills/cr-skill-ml-economics/SKILL.md`
  - `.github/skills/cr-skill-publication-output/SKILL.md`
  - `.github/skills/cr-skill-replication-standards/SKILL.md`
  - `.github/skills/cr-skill-research-eda/SKILL.md`
  - `.github/skills/cr-skill-research-integrity/SKILL.md`
  - `.github/skills/cr-skill-research-workflow/SKILL.md`
  - `.github/skills/cr-skill-structural-econometrics/SKILL.md`
  - `.github/skills/cr-skill-symbolic-verification/SKILL.md`
  - `.github/skills/cr-skill-theory-data-dialogue/SKILL.md`
  - `.github/instructions/latex.instructions.md`
  - `.github/instructions/math.instructions.md`
  - `tests/cr-prompts.Tests.ps1`
- **Details**:
  ```bash
  git checkout compound-research -- \
    .github/agents/cr-academic-writing.agent.md \
    .github/agents/cr-econometric-reasoning.agent.md \
    .github/agents/cr-identification-audit.agent.md \
    .github/agents/cr-mathematical-verification.agent.md \
    .github/agents/cr-ml-methodology.agent.md \
    .github/agents/cr-publication-output.agent.md \
    .github/agents/cr-replication-package.agent.md \
    .github/agents/cr-research-integrity.agent.md \
    .github/agents/cr-specification-analysis.agent.md \
    .github/prompts/cr-brainstorm.prompt.md \
    .github/prompts/cr-compound.prompt.md \
    .github/prompts/cr-plan.prompt.md \
    .github/prompts/cr-review.prompt.md \
    .github/prompts/cr-work.prompt.md \
    .github/skills/cr-skill-academic-writing/SKILL.md \
    .github/skills/cr-skill-identification-strategies/SKILL.md \
    .github/skills/cr-skill-mathematical-derivation/SKILL.md \
    .github/skills/cr-skill-ml-economics/SKILL.md \
    .github/skills/cr-skill-publication-output/SKILL.md \
    .github/skills/cr-skill-replication-standards/SKILL.md \
    .github/skills/cr-skill-research-eda/SKILL.md \
    .github/skills/cr-skill-research-integrity/SKILL.md \
    .github/skills/cr-skill-research-workflow/SKILL.md \
    .github/skills/cr-skill-structural-econometrics/SKILL.md \
    .github/skills/cr-skill-symbolic-verification/SKILL.md \
    .github/skills/cr-skill-theory-data-dialogue/SKILL.md \
    .github/instructions/latex.instructions.md \
    .github/instructions/math.instructions.md \
    tests/cr-prompts.Tests.ps1
  ```
- **Test Scenarios**:
  - ✅ All 29 files land in working tree
  - 🛑 No existing main files overwritten
  - ❌ If any file doesn't exist on compound-research, git errors — fix path
- **Acceptance criteria**: `git status` shows 29 new untracked/staged files, no modifications to existing files

### 3. Port CR-only .cg-docs artifacts
- **Requirements**: R2
- **Files to add** (42 files — DIGEST.md excluded, will be regenerated by cg-index):
  - `.cg-docs/brainstorms/2026-05-13-compound-research-extension.md`
  - `.cg-docs/plans/2026-05-14-compound-research-phase1-phase2.md`
  - `.cg-docs/plans/2026-05-14-compound-research-phase3-agents.md`
  - `.cg-docs/plans/2026-05-14-compound-research-phase4-skills.md`
  - `.cg-docs/plans/2026-05-20-compound-research-phase5-ml-economics.md`
  - `.cg-docs/plans/2026-05-22-compound-research-phase6-writing-publication.md`
  - `.cg-docs/plans/2026-05-22-compound-research-phase7-reproducibility-replication.md`
  - `.cg-docs/plans/2026-05-22-compound-research-phase8-integration-docs.md`
  - `.cg-docs/plans/2026-05-22-compound-research-phase9-publication-output-agent.md`
  - `.cg-docs/reviews/2026-05-14-compound-research-phase1-phase2-review.md`
  - `.cg-docs/reviews/2026-05-14-compound-research-phase3-agents-review.md`
  - `.cg-docs/reviews/2026-05-14-compound-research-phase3-agents-thorough-review.md`
  - `.cg-docs/reviews/2026-05-14-compound-research-phase4-skills-review.md`
  - `.cg-docs/reviews/2026-05-15-compound-research-fix-commit-review.md`
  - `.cg-docs/reviews/2026-05-20-compound-research-phase5-ml-economics-review-2.md`
  - `.cg-docs/reviews/2026-05-20-compound-research-phase5-ml-economics-review.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase6-writing-publication-review-2.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase6-writing-publication-review.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase7-reproducibility-replication-review-2.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase7-reproducibility-replication-review.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase8-integration-docs-review-2.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase8-integration-docs-review.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase9-publication-output-agent-review-2.md`
  - `.cg-docs/reviews/2026-05-22-compound-research-phase9-publication-output-agent-review.md`
  - `.cg-docs/reviews/2026-05-22-install-stale-function-migration-review.md`
  - `.cg-docs/solutions/bugs/2026-05-14-empty-file-bypasses-graceful-skip-produces-false-negative.md`
  - `.cg-docs/solutions/bugs/2026-05-14-python-regex-raw-string-double-backslash-excludes-letters.md`
  - `.cg-docs/solutions/bugs/2026-05-20-optim-hessian-returns-negative-ll-hessian-must-be-positive-definite.md`
  - `.cg-docs/solutions/bugs/2026-05-22-bash-heredoc-multiline-compound-command-invalid-syntax.md`
  - `.cg-docs/solutions/data-quality/2026-05-14-yaml-frontmatter-allowlist-validation-pattern.md`
  - `.cg-docs/solutions/data-quality/2026-05-20-welfare-column-three-step-guard-existence-na-positivity.md`
  - `.cg-docs/solutions/data-quality/2026-05-21-mice-m1-is-single-imputation-not-multiple.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-14-depth-restricted-mode-bypasses-domain-agents-need-forced-dispatch-exception.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-14-dispatch-table-must-cover-all-taxonomy-entries.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-20-agent-step-carveout-must-not-contradict-global-deferral-policy.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-20-pester-hoist-file-reads-to-context-scope.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-21-agent-flag-as-format-drift-whole-file-audit.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-22-multi-task-type-agent-needs-execution-mode-guard.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-22-pester-hoist-expensive-computation-to-outer-scope.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-22-review-criteria-must-be-in-correct-domain-section.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-22-skill-agent-forbidden-pattern-table-must-be-kept-in-sync.md`
  - `.cg-docs/solutions/testing-patterns/2026-05-22-test-reimplements-logic-with-correct-code-masks-bug.md`
  - `.cg-docs/strategy/2026-05-14-compound-research-roadmap.md`
- **Details**:
  ```bash
  git checkout compound-research -- \
    .cg-docs/brainstorms/2026-05-13-compound-research-extension.md \
    .cg-docs/plans/2026-05-14-compound-research-phase1-phase2.md \
    .cg-docs/plans/2026-05-14-compound-research-phase3-agents.md \
    .cg-docs/plans/2026-05-14-compound-research-phase4-skills.md \
    .cg-docs/plans/2026-05-20-compound-research-phase5-ml-economics.md \
    .cg-docs/plans/2026-05-22-compound-research-phase6-writing-publication.md \
    .cg-docs/plans/2026-05-22-compound-research-phase7-reproducibility-replication.md \
    .cg-docs/plans/2026-05-22-compound-research-phase8-integration-docs.md \
    .cg-docs/plans/2026-05-22-compound-research-phase9-publication-output-agent.md \
    .cg-docs/reviews/2026-05-14-compound-research-phase1-phase2-review.md \
    .cg-docs/reviews/2026-05-14-compound-research-phase3-agents-review.md \
    .cg-docs/reviews/2026-05-14-compound-research-phase3-agents-thorough-review.md \
    .cg-docs/reviews/2026-05-14-compound-research-phase4-skills-review.md \
    .cg-docs/reviews/2026-05-15-compound-research-fix-commit-review.md \
    .cg-docs/reviews/2026-05-20-compound-research-phase5-ml-economics-review-2.md \
    .cg-docs/reviews/2026-05-20-compound-research-phase5-ml-economics-review.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase6-writing-publication-review-2.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase6-writing-publication-review.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase7-reproducibility-replication-review-2.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase7-reproducibility-replication-review.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase8-integration-docs-review-2.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase8-integration-docs-review.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase9-publication-output-agent-review-2.md \
    .cg-docs/reviews/2026-05-22-compound-research-phase9-publication-output-agent-review.md \
    .cg-docs/reviews/2026-05-22-install-stale-function-migration-review.md \
    .cg-docs/solutions/bugs/2026-05-14-empty-file-bypasses-graceful-skip-produces-false-negative.md \
    .cg-docs/solutions/bugs/2026-05-14-python-regex-raw-string-double-backslash-excludes-letters.md \
    .cg-docs/solutions/bugs/2026-05-20-optim-hessian-returns-negative-ll-hessian-must-be-positive-definite.md \
    .cg-docs/solutions/bugs/2026-05-22-bash-heredoc-multiline-compound-command-invalid-syntax.md \
    .cg-docs/solutions/data-quality/2026-05-14-yaml-frontmatter-allowlist-validation-pattern.md \
    .cg-docs/solutions/data-quality/2026-05-20-welfare-column-three-step-guard-existence-na-positivity.md \
    .cg-docs/solutions/data-quality/2026-05-21-mice-m1-is-single-imputation-not-multiple.md \
    .cg-docs/solutions/testing-patterns/2026-05-14-depth-restricted-mode-bypasses-domain-agents-need-forced-dispatch-exception.md \
    .cg-docs/solutions/testing-patterns/2026-05-14-dispatch-table-must-cover-all-taxonomy-entries.md \
    .cg-docs/solutions/testing-patterns/2026-05-20-agent-step-carveout-must-not-contradict-global-deferral-policy.md \
    .cg-docs/solutions/testing-patterns/2026-05-20-pester-hoist-file-reads-to-context-scope.md \
    .cg-docs/solutions/testing-patterns/2026-05-21-agent-flag-as-format-drift-whole-file-audit.md \
    .cg-docs/solutions/testing-patterns/2026-05-22-multi-task-type-agent-needs-execution-mode-guard.md \
    .cg-docs/solutions/testing-patterns/2026-05-22-pester-hoist-expensive-computation-to-outer-scope.md \
    .cg-docs/solutions/testing-patterns/2026-05-22-review-criteria-must-be-in-correct-domain-section.md \
    .cg-docs/solutions/testing-patterns/2026-05-22-skill-agent-forbidden-pattern-table-must-be-kept-in-sync.md \
    .cg-docs/solutions/testing-patterns/2026-05-22-test-reimplements-logic-with-correct-code-masks-bug.md \
    .cg-docs/strategy/2026-05-14-compound-research-roadmap.md
  ```
- **Test Scenarios**:
  - ✅ All 42 files land correctly
  - 🛑 Main's Brain files (BRAIN.md, BRAIN-01.md, etc.) untouched
  - 🛑 Main's existing .cg-docs/ content (DIGEST.md, etc.) untouched
- **Acceptance criteria**: `git diff --cached --name-only | wc -l` shows ~71 new files total (29 + 42); no modifications to existing files

### 4. Update test sentinels for new file counts
- **Requirements**: R11
- **Files**: `tests/model-assignments.Tests.ps1`
- **Details**: Update prompt-count and agent-count sentinels to reflect the 5 new CR prompts and 9 new CR agents added in Step 2. Use the exact sentinel values recorded during Phase 0 Step 1 inspection, incremented by the CR additions.
- **Test Scenarios**:
  - ✅ Updated sentinels match actual file count
  - 🛑 Only sentinel values changed, no other test logic modified
- **Acceptance criteria**: `model-assignments.Tests.ps1` passes with CR files present

### 5. Commit Phase 1
- **Requirements**: R1, R2
- **Details**:
  ```bash
  git add -A
  git commit -m "feat(cr): port compound-research intellectual content from v0.10 branch

  Port 9 CR agents, 5 CR prompts, 12 CR skills, 2 instruction files,
  1 test file, and 42 .cg-docs artifacts (plans, reviews, solutions,
  strategy) from the compound-research branch (v0.10.2).

  Updated model-assignments test sentinels for new file counts.
  No other modifications to existing v1.0 files. Integration follows
  in subsequent commits."
  ```
- **Acceptance criteria**: Clean commit, all main tests pass (run full suite to verify)

## Phase 2: Basic CR Registration

### 5. Add CR module section to copilot-instructions.md
- **Requirements**: R3
- **Files**: `.github/copilot-instructions.md`
- **Details**: Add after the existing "Review Depth Tiers" section:
  - "Compound Research (CR) Skills" section listing all CR skills with their task-type assignments
  - `/cr-*` command reference table
  - Research task taxonomy (8 types)
  - Research integrity priority note (P0 for silent research errors)
  - CR agent list
  - `modules: [research]` activation note
- **Test Scenarios**:
  - ✅ copilot-instructions.md remains valid markdown
  - 🛑 Existing sections unmodified
  - ❌ Section placement conflicts with v1.0's new "Brain Consultation" section — place CR section after Brain
- **Acceptance criteria**: CR skills, agents, and prompts are discoverable by Copilot

### 6. Merge CR additions into copilot-instructions.template.md
- **Requirements**: R3
- **Files**: `.github/copilot-instructions.template.md`
- **Details**: **Verify first** (Phase 0 recorded whether `{{modules}}` already exists). If absent: add `{{modules}}` template variable and "Active Modules" section (from CR branch's version). If already present: skip. Keep main's existing template structure intact.
- **Acceptance criteria**: Template includes modules variable; running cg-update with `modules: [research]` produces correct output

### 7. Add module: shared frontmatter to instruction files
- **Requirements**: R3
- **Files**: `.github/instructions/r.instructions.md`, `.github/instructions/python.instructions.md`, `.github/instructions/stata.instructions.md`
- **Details**: **Verify first** (Phase 0 recorded whether `module:` frontmatter already exists). If absent: add `module: shared` to YAML frontmatter of each file (one-line addition after `applyTo:` in each). If already present: skip. Do not modify file body.
- **Acceptance criteria**: Each file has `module: shared` in frontmatter; body unchanged from main's version

### 8. Adopt context-loading contract in CR prompts
- **Requirements**: R4
- **Files**: `.github/prompts/cr-brainstorm.prompt.md`, `cr-plan.prompt.md`, `cr-work.prompt.md`, `cr-review.prompt.md`, `cr-compound.prompt.md`
- **Details**: Update each CR prompt's "Step 0: Get Bearings" to reference `.github/shared/context-loading.contract.md` and follow staged policy (Stage 0 reads for compound-gpid.md, compound-gpid.local.md; Stage 1 for metadata). Match the pattern used in v1.0's `cg-review.prompt.md`.
- **Test Scenarios**:
  - ✅ CR prompts reference context-loading contract
  - 🛑 Existing CR logic preserved
- **Acceptance criteria**: Each CR prompt's Step 0 includes context-loading contract reference

### 9. Update cr-prompts.Tests.ps1 for v1.0 structure
- **Requirements**: R12
- **Files**: `tests/cr-prompts.Tests.ps1`
- **Details**: Update test assertions for any path changes, new frontmatter fields, or structural patterns that differ between v0.10 and v1.0. Ensure tests validate the new context-loading references.
- **Test Scenarios**:
  - ✅ All CR prompt tests pass
  - 🛑 Existing main test suite still passes
- **Tests**: Run `tests/cr-prompts.Tests.ps1`
- **Acceptance criteria**: `Invoke-Pester tests/cr-prompts.Tests.ps1 -Quiet` passes

### 9b. Fix prompt-tools.Tests.ps1 failures from CR prompt additions
- **Requirements**: R11, R12
- **Files**: `tests/prompt-tools.Tests.ps1`, possibly CR prompt files
- **Details**: `prompt-tools.Tests.ps1` auto-discovers all prompts in `.github/prompts/` and validates structural patterns (frontmatter fields, required sections, model assignments). The 5 new CR prompts will be discovered and may fail on: missing `model:` frontmatter, unexpected step naming, or missing contract references. Inspect failures and fix either:
  - The CR prompt files (add missing frontmatter/structure to match v1.0 conventions), OR
  - The test file (add CR-specific exclusions if CR legitimately differs)
- **Test Scenarios**:
  - ✅ `prompt-tools.Tests.ps1` passes with CR prompts present
  - 🛑 No test logic weakened for non-CR prompts
- **Acceptance criteria**: Full test suite green including prompt-tools structural validation

### 10. Commit Phase 2
- **Details**:
  ```bash
  git commit -m "feat(cr): register CR module in v1.0 copilot-instructions and adopt contracts"
  ```
- **Acceptance criteria**: CR prompts are functional in isolation; all tests green

## Phase 3: Review Routing Integration

### 11. Add research mode to review-routing contract
- **Requirements**: R5
- **Files**: `.github/shared/review-routing.contract.md`
- **Details**: Add to Modes table:
  | `research` | all `standard` agents plus `@cr-research-integrity`, `@cr-mathematical-verification`, `@cr-identification-audit`, `@cr-econometric-reasoning`, `@cr-ml-methodology`, `@cr-specification-analysis`, `@cr-academic-writing`, `@cr-publication-output`, `@cr-replication-package` |
  Add to Risk Classes table: `research` → `research` mode.
  Add to Trigger Taxonomy: research-related file patterns, `/cr-*` invocations.
- **Test Scenarios**:
  - ✅ Contract is valid markdown table
  - ✅ Research mode dispatches all CR agents
  - 🛑 Existing modes unchanged
- **Acceptance criteria**: review-routing.contract.md includes research mode with all CR agents listed

### 12. Update /cg-review to dispatch CR agents for research tasks
- **Requirements**: R6
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**: Add research task detection logic (check for `modules: [research]` in compound-gpid.local.md, detect research file patterns). When research mode applies, dispatch CR agents alongside or instead of standard agents per routing contract.
- **Test Scenarios**:
  - ✅ Research mode detected when modules includes research
  - ✅ CR agents dispatched for research-typed code
  - 🛑 Non-research reviews unaffected
- **Acceptance criteria**: `/cg-review` on a research file dispatches CR review agents

### 13. Commit Phase 3
- **Details**:
  ```bash
  git commit -m "feat(cr): integrate research mode into review-routing contract"
  ```

## Phase 4: Model Catalog + Agent Frontmatter

### 14. Update model: frontmatter in all CR agents
- **Requirements**: R7
- **Files**: All 9 `.github/agents/cr-*.agent.md`
- **Details**: CR agents currently have `model: Claude Sonnet 4.6 (copilot)` from the v0.10 branch. **Replace** with `model: GPT-5.4` to match v1.0's model-catalog conventions (research review agents are reasoning-heavy, matching the review model assignment). Also verify frontmatter follows v1.0 pattern: `description`, `model`, `tools`, `user-invocable`.
  - All 9 CR agents use GPT-5.4 (review/reasoning tier) — they are all review agents, not coding assistants.
- **Test Scenarios**:
  - ✅ Each agent has `model: GPT-5.4` (not Claude naming)
  - ✅ Model matches catalog's review tier
  - 🛑 Agent body content unchanged
- **Acceptance criteria**: All 9 CR agents have `model: GPT-5.4` in frontmatter; no Claude model names remain

### 15. Update model-catalog.json with CR model policy
- **Requirements**: R7
- **Files**: `.github/shared/model-catalog.json`
- **Details**: Add entry documenting CR agent model assignment rationale (research review = reasoning tier = GPT-5.4). Add CR-specific note if needed.
- **Acceptance criteria**: Model catalog documents CR model assignments

### 16. Commit Phase 4
- **Details**:
  ```bash
  git commit -m "feat(cr): add model frontmatter to CR agents per model-catalog conventions"
  ```

## Phase 5: Brain + Shared Contracts Integration

### 17. Add Consult Brain steps to CR prompts
- **Requirements**: R8
- **Files**: `.github/prompts/cr-review.prompt.md`, `.github/prompts/cr-work.prompt.md`
- **Details**: Use the Brain skill name and invocation pattern confirmed in Phase 0 Step 1. Add "Step N.N: Consult Brain" sections matching the exact pattern found in v1.0's `cg-review.prompt.md`. Search directive: "known mistakes and anti-patterns for the research domain, past review findings in similar econometric/ML code."
  - **Gate**: If Phase 0 could not confirm the Brain skill name, inspect `.github/skills/` on the current branch before proceeding. If no Brain skill exists, skip this step and note as deferred.
- **Test Scenarios**:
  - ✅ Brain consultation step present and correctly structured
  - ✅ References correct skill name (confirmed in Phase 0)
  - 🛑 Rest of prompt logic unchanged
- **Acceptance criteria**: CR review and work prompts include Brain consultation using verified skill name

### 18. Adopt active-state contract in /cr-work
- **Requirements**: R9
- **Files**: `.github/prompts/cr-work.prompt.md`
- **Details**: Add active-state JSON write on workflow start (status: active) and completion (status: completed/handoff). Follow pattern from v1.0's active-state.contract.md. This enables `/cg-resume` to discover and resume CR work sessions.
- **Test Scenarios**:
  - ✅ /cr-work writes active-state on start
  - ✅ /cr-work updates active-state on completion
  - ✅ /cg-resume can discover CR work sessions
- **Acceptance criteria**: /cr-work produces active-state JSON per contract schema

### 19. Commit Phase 5
- **Details**:
  ```bash
  git commit -m "feat(cr): integrate Brain consultation and active-state contract into CR prompts"
  ```

## Phase 6: Multi-Target Generation

### 20. Run cg_generate_targets.py to produce CR adapter entries
- **Requirements**: R10
- **Files**: `scripts/cg_generate_targets.py` (confirmed in Phase 0), generated outputs in `.agents/`, `.claude/`, `.opencode/`
- **Details**: Use the invocation signature confirmed in Phase 0 Step 1. The generation script reads from `.github/` and produces platform-specific outputs. With CR files now in `.github/`, re-running the script should auto-generate:
  - `.agents/commands/cr-*.md` (5 command files)
  - `.agents/subagents/cr-*.toml` (9 agent files)
  - `.agents/skills/cr-skill-*/SKILL.md` (12 skill files)
  - Equivalent entries for `.claude/` and `.opencode/` targets
  - Updated `.compound-gpid-generated.json`
  - **Gate**: If Phase 0 found the script doesn't exist at the expected path, locate it first or create the adapter entries manually.
- **Test Scenarios**:
  - ✅ Script runs without errors
  - ✅ All CR entries appear in generated targets
  - ✅ Existing entries unchanged
  - 🛑 If script doesn't auto-discover new files, may need to add CR patterns to its discovery logic
- **Acceptance criteria**: All 3 target directories contain CR entries; `.compound-gpid-generated.json` lists them

### 21. Verify and fix generation script if needed
- **Requirements**: R10
- **Files**: `scripts/cg_generate_targets.py` (may need modification)
- **Details**: If the script uses hardcoded `cg-` prefixes for discovery, add `cr-` prefix support. Check for pattern filters that exclude `cr-*` files.
- **Acceptance criteria**: Script correctly discovers and generates for both `cg-` and `cr-` prefixed assets

### 22. Commit Phase 6
- **Details**:
  ```bash
  git commit -m "feat(cr): generate multi-target adapter entries for CR module"
  ```

## Phase 7: Cross-Integration Polish

### 23. Make existing cg-* agents research-aware
- **Requirements**: R13
- **Files**: `.github/agents/cg-reproducibility.agent.md`, `.github/agents/cg-data-quality.agent.md`, `.github/agents/cg-testing.agent.md`, `.github/agents/cg-performance.agent.md`
- **Details**: Add research-context awareness to relevant existing agents:
  - `cg-reproducibility`: recognize research reproducibility (seeds for simulation/bootstrap, replication archive structure)
  - `cg-data-quality`: recognize survey data patterns (weights, PPP, welfare variables)
  - `cg-testing`: recognize research test patterns (Monte Carlo, parameter recovery)
  - `cg-performance`: recognize research performance patterns (large-p computation, bootstrap)
- **Test Scenarios**:
  - ✅ Agents include research-aware sections
  - 🛑 Non-research behavior unchanged
- **Acceptance criteria**: Modified agents produce relevant findings when reviewing research code

### 24. Update cg-work.prompt.md for research task routing
- **Requirements**: R13
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**: Add detection logic: if task is research-typed (econometrics, ML, structural estimation) and `modules: [research]` is active, suggest redirecting to `/cr-work`. Do not force — offer as guidance.
- **Acceptance criteria**: `/cg-work` on a research task mentions `/cr-work` availability

### 25. 🛑 Update compound-gpid.md Current Focus (requires user approval)
- **Requirements**: R3
- **Files**: `compound-gpid.md`
- **Details**: **STOP** — Present proposed Current Focus update text to user for approval before modifying. Per project convention: "Do not modify the body of compound-gpid.md without explicit user approval."
  Proposed text: "Compound Research module ported to v1.0 and integrated with Brain, review routing, model catalog, context-loading contracts, active-state, and multi-target generation. Engineering milestones continue in parallel."
- **Acceptance criteria**: User approves text; charter updated

### 26. Final test pass
- **Requirements**: R11, R12
- **Files**: All test files
- **Details**: Run full test suite. All existing main tests + cr-prompts.Tests.ps1 must pass.
- **Tests**: `. tests/Run-Tests.ps1`
- **Acceptance criteria**: Zero test failures

### 27. Commit Phase 7
- **Details**:
  ```bash
  git commit -m "feat(cr): complete v1.0 cross-integration — research-aware agents, routing, tests green"
  ```

## Testing Strategy

- **Phase 0**: No tests — read-only inspection, documenting what exists on main
- **Phase 1**: Run full test suite after sentinel updates (verifies additive port doesn't break anything)
- **Phase 2**: Run `cr-prompts.Tests.ps1` + `prompt-tools.Tests.ps1` + full suite
- **Phase 3–5**: Run full test suite after each phase commit
- **Phase 6**: Verify generated files match expected structure; run full suite
- **Phase 7**: Full test suite — the final gate

Test types:
- Pester tests for prompt structure validation (file existence, frontmatter, required sections)
- `model-assignments.Tests.ps1` for count sentinels and model naming
- `prompt-tools.Tests.ps1` for structural validation of all prompts including CR
- Manual verification of Copilot dispatch (CR prompts load correct skills and agents)
- Script execution test for `cg_generate_targets.py`

## Documentation Checklist

- [ ] copilot-instructions.md updated with CR module documentation
- [ ] copilot-instructions.template.md updated with modules variable
- [ ] README.md updated if needed (mention CR module availability)
- [ ] docs/reference.md updated with /cr-* commands
- [ ] docs/manual.md updated with research workflow section

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| CR prompts reference v0.10 patterns (step numbers, dispatch syntax) that don't exist in v1.0 | CR prompts silently fail or produce wrong behavior | Phase 0 inspection surfaces these; fix in Phase 2 before testing |
| cg_generate_targets.py uses hardcoded cg- prefix filtering | CR files excluded from generation | Phase 0 confirms script existence and reads its discovery logic; fix in Phase 6 Step 21 |
| model-assignments.Tests.ps1 count sentinels break with new CR files | Tests fail immediately after Phase 1 port | Step 4 updates sentinels before commit; values confirmed in Phase 0 |
| prompt-tools.Tests.ps1 auto-discovers CR prompts and applies structural assertions | Unexpected test failures in Phase 2 | Step 9b explicitly addresses this; Phase 0 inspects what assertions apply |
| Brain skill name differs from expected `cg-skill-brain-query` | Phase 5 Step 17 produces broken reference | Phase 0 confirms exact skill name; Step 17 has a gate to defer if unresolved |
| DIGEST.md regeneration needed after solution port | Knowledge index stale until cg-index runs | Excluded from port; note to run cg-index after Phase 1 |
| CR agents have Claude model names that conflict with v1.0's GPT convention | model-assignments tests fail; model-guide drift | Step 14 explicitly replaces (not adds) model field |
| Active-state schema doesn't have /cr-work as a recognized workflow | /cg-resume doesn't find CR sessions | Add /cr-work to any workflow allowlists in Step 18 |
| Charter edit in Step 25 executed without approval | Violates project governance | Step 25 has explicit STOP gate requiring user approval |

## Out of Scope

- Modifying the old `compound-research` branch (kept as historical reference)
- Expanding CR skills to sub-directory structure (references/, workflows/) — cosmetic, future task
- Adding new CR agents beyond the original 9
- Writing Brain entries for research domain (accumulates organically via /cr-compound)
- Updating roadmap.json (done post-plan via @cg-roadmap)
- PR to main (personal working branch for now)

## Completion Contract

### Outcome

Phase 2 establishes baseline CR registration in v1.0 by wiring CR module discovery and context-loading contract references into core instruction and prompt surfaces, with CR prompt tests updated accordingly and no regressions to existing prompt-tooling expectations.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V2.1 | 2 | CR module registration docs integrated in core instruction surfaces | `.github/copilot-instructions.md`, `.github/copilot-instructions.template.md` diff review | yes |
| V2.2 | 2 | Shared language instruction files include module frontmatter | `.github/instructions/r.instructions.md`, `.github/instructions/python.instructions.md`, `.github/instructions/stata.instructions.md` frontmatter inspection | yes |
| V2.3 | 2 | All CR prompts reference context-loading contract in Step 0 bearings | `.github/prompts/cr-*.prompt.md` content checks | yes |
| V2.4 | 2 | CR prompt tests reflect v1.0 structure updates | `tests/cr-prompts.Tests.ps1` diff review | yes |
| V2.5 | 2 | Prompt tooling structure remains valid for CR additions | `tests/prompt-tools.Tests.ps1` targeted review and (if available) safe test evidence | yes |

### Boundaries

- Do not modify protected assets outside the scoped files required for Phase 2.
- Preserve existing v1.0 behavior for non-CR prompts, agents, and shared contracts.
- Keep `.github/` as source-of-truth; do not hand-edit generated adapter targets in this phase.

### Blocked-Stop Conditions

- Required Phase 2 evidence row cannot be satisfied and no accepted exception is approved.
- A change needed for Phase 2 would violate protected-asset or file-permission rules.
- Prompt/test structural regressions cannot be resolved within the phase without broadening scope.
