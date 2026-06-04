---
date: 2026-05-20
title: "Knowledge Brain Read Path — Batch C"
status: completed
completed-phases: [1, 2]
completed-date: 2026-05-20
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-20-knowledge-brain-read-path-batch-c.md"
language: "PowerShell"
estimated-effort: "medium"
tags: [brain, read-path, prompt-integration, skill, brain-query, knowledge-brain]
phases: 2
---

# Plan: Knowledge Brain Read Path — Batch C

## Objective

Wire the brain read path so that every major command consults `.cg-docs/BRAIN.md`
before acting, surfacing relevant institutional knowledge (takeaways, gotchas,
patterns, edge cases) adapted to the current task. Create a `cg-skill-brain-query`
skill that teaches agents *how* to navigate, extract, evaluate, and prioritize
brain entries, while each prompt specifies *what* to search for.

## Context

- Batch A delivered the brain engine (`scripts/brain/`) that indexes 400 entities
  into BRAIN.md, topic-partitioned sub-files (BRAIN-01.md…), BRAIN-log.md,
  and brain-index.json.
- Batch B wired triggers: `/cg-brain-rebuild` for explicit rebuilds and
  auto-rebuild in `/cg-compound` Step 3b.
- No prompt currently reads the brain — it's produced but never consumed.
- The brainstorm decided: skill owns "how" (full protocol), prompts own "what"
  (short search directive). Placement varies per prompt (after task context).
- `--no-brain` flag for opt-out. Always attempt search otherwise.

## Requirements

| ID  | Requirement                                                        | Source      |
|-----|--------------------------------------------------------------------|-------------|
| R1  | Create `cg-skill-brain-query` SKILL.md with full protocol          | brainstorm  |
| R2  | Skill covers: navigation, extraction, evaluation, prioritization   | brainstorm  |
| R3  | Skill covers: contradiction resolution, staleness detection        | brainstorm  |
| R4  | Skill covers: citation format and no-match reporting               | brainstorm  |
| R5  | Add `--no-brain` flag parsing to all 6 target prompts              | brainstorm  |
| R6  | Add "Consult Brain" step to `/cg-brainstorm` (after Step 0.5)      | brainstorm  |
| R7  | Add "Consult Brain" step to `/cg-plan` (after Step 1 gathers ctx)  | brainstorm  |
| R8  | Add "Consult Brain" step to `/cg-work` (after Step 1 loads plan)   | brainstorm  |
| R9  | Add "Consult Brain" step to `/cg-review` (after Step 1 scope)      | brainstorm  |
| R10 | Add "Consult Brain" step to `/cg-fix-triage` (after Step 1 report) | brainstorm  |
| R11 | Add "Consult Brain" step to `/cg-compound` (after Step 1 context)  | brainstorm  |
| R12 | Graceful absence: skip silently if BRAIN.md doesn't exist          | brainstorm  |
| R13 | Each prompt's brain step is 4-6 lines (lean)                       | brainstorm  |
| R14 | Tests verify flag parsing and brain step presence in all 6 prompts  | convention  |

## Implementation Steps

## Phase 1: Skill and prompt integration

### 1. Create `cg-skill-brain-query` SKILL.md

- **Requirements**: R1, R2, R3, R4
- **Files**: `.github/skills/cg-skill-brain-query/SKILL.md` (new)
- **Details**:
  Create the skill directory and SKILL.md with:
  - Frontmatter: `name: cg-skill-brain-query`, description covering purpose
  - **When to Load** section: loaded by any prompt with a "Consult Brain" step
  - **Protocol** section with numbered steps:
    1. Check: if `.cg-docs/BRAIN.md` does not exist → skip silently, done
    2. Read `.cg-docs/BRAIN.md` Topic Index table
    3. Match task keywords against topic names and keyword lists
    4. For each matched topic: open the linked BRAIN-NN.md sub-file
       **Deduplicate**: if multiple matched topics link to the same sub-file,
       read it once only.
    5. Extract relevant entries (takeaways, gotchas, patterns, edge cases)
    6. Evaluate: assess logical soundness and relevance to current task
    7. Prioritize: rank by specificity, recency, and relevance
    8. Resolve contradictions: prefer newer + more specific; check `supersedes` edges
    9. Detect staleness: discard entries whose context no longer applies
    10. Cite: note source artifact path for each incorporated finding
    11. If nothing relevant found: state "No relevant brain entries found" and proceed
  - **Contradiction Resolution** section: rules for when entries conflict
  - **Staleness Signals** section: what makes an entry outdated
  - **Output Format** section: how to present findings to the agent's working context
  - **Anti-patterns** section: don't read all sub-files blindly, don't apply
    findings without evaluation, don't use `brain-index.json` directly (it is
    for the `cg-index` Python tooling, not for agent navigation)
- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Contains protocol steps, contradiction rules, staleness signals
  - 🛑 Edge: skill doesn't reference modifying brain files (read-only)
- **Acceptance criteria**: Skill file exists, loadable, covers all protocol aspects

### 2. Add `--no-brain` flag parsing to all 6 target prompts

- **Requirements**: R5
- **Files**: 6 prompt files (modify Step 0 in each):
  - `.github/prompts/cg-brainstorm.prompt.md`
  - `.github/prompts/cg-plan.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-fix-triage.prompt.md`
  - `.github/prompts/cg-compound.prompt.md`
- **Details**:
  Add `--no-brain` to the existing flag-parsing step in each prompt (Step 0
  for brainstorm, plan, work, review, fix-triage; **Step 0.5** for compound):
  - In prompts that already parse flags (brainstorm has `--no-branch`, plan has
    `--no-phases`, compound has `--propose`/`--no-enrich` in Step 0.5): append
    `--no-brain` to the existing flag list.
  - In prompts without explicit flag parsing (work, review, fix-triage): add a
    new flag-parsing bullet to Step 0.
  - Pattern: "If `--no-brain` is present, set `brain-enabled = false`. Otherwise
    set `brain-enabled = true`."
  - **Important**: For `/cg-review` and `/cg-fix-triage`, also update the
    "Recognized:" warning string that fires for unrecognized arguments:
    - `/cg-review` Step 1: append `, \`--no-brain\`` to the recognized list.
    - `/cg-fix-triage` Step 2: append `, \`--no-brain\`` to the recognized list
      so that `--no-brain` is not treated as an unrecognized scope argument.
- **Test Scenarios**:
  - ✅ Each prompt mentions `--no-brain` in its flag-parsing step
  - ✅ `/cg-review` recognized-arguments string includes `--no-brain`
  - ✅ `/cg-fix-triage` recognized-arguments string includes `--no-brain`
  - 🛑 Edge: flag is parsed before the brain consultation step (ordering)
- **Acceptance criteria**: All 6 prompts parse `--no-brain`; review and fix-triage recognized-argument strings updated

### 3. Add "Consult Brain" step to `/cg-brainstorm`

- **Requirements**: R6, R12, R13
- **Files**: `.github/prompts/cg-brainstorm.prompt.md`
- **Details**:
  Add a new step after Step 0.5 (Check for Prior Work) and before Step 1
  (Lightweight Research). Call it **Step 0.7: Consult Brain** — this number is
  vacant in brainstorm (existing sub-steps are 0.5, then 1, 1.1, 1.5, 1.7).

  Content (~5 lines):
  ```
  ### Step 0.7: Consult Brain

  If `brain-enabled = false`, skip this step.

  Load `cg-skill-brain-query`. Search the brain for: prior explorations of this
  topic, abandoned approaches and the reasons they failed, related decisions
  from past brainstorms. Incorporate relevant findings into your context for
  the remainder of this session.
  ```
- **Test Scenarios**:
  - ✅ Step exists between Step 0.5 and Step 1
  - ✅ Contains `cg-skill-brain-query` reference
  - ✅ Contains `brain-enabled = false` guard
  - ✅ Search directive mentions prior explorations/abandoned approaches
- **Acceptance criteria**: Step present with guard + skill ref + directive

### 4. Add "Consult Brain" step to `/cg-plan`

- **Requirements**: R7, R12, R13
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  Add after Step 1 (Gather Context) and before Step 1.5 (Scope Assessment).
  Call it **Step 1.3: Consult Brain** (no collision — Step 1.5 follows).

  Content (~5 lines):
  ```
  ### Step 1.3: Consult Brain

  If `brain-enabled = false`, skip this step.

  Load `cg-skill-brain-query`. Search the brain for: existing solutions that
  cover sub-tasks of this plan, failed plans for similar features and why they
  failed, patterns and conventions relevant to the implementation area.
  Incorporate relevant findings into your planning context.
  ```
- **Test Scenarios**:
  - ✅ Step exists between Step 1 and Step 1.5
  - ✅ Contains guard, skill ref, and plan-specific directive
- **Acceptance criteria**: Step present with correct placement and content

### 5. Add "Consult Brain" step to `/cg-work`

- **Requirements**: R8, R12, R13
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  Add after Step 1 (Load the Plan) completes — specifically after Step 1.2
  (Parse Phase Argument). Call it **Step 1.3: Consult Brain**.

  Content (~5 lines):
  ```
  ### Step 1.3: Consult Brain

  If `brain-enabled = false`, skip this step.

  Load `cg-skill-brain-query`. Search the brain for: gotchas and edge cases
  from similar implementation work, patterns that apply to the files being
  modified, known pitfalls in the technology area of this plan. Incorporate
  relevant findings as constraints for your implementation.
  ```
- **Test Scenarios**:
  - ✅ Step exists after plan loading
  - ✅ Search directive mentions gotchas/edge cases/patterns
- **Acceptance criteria**: Step present after Step 1.2 with correct content

### 6. Add "Consult Brain" step to `/cg-review`

- **Requirements**: R9, R12, R13
- **Files**: `.github/prompts/cg-review.prompt.md`
- **Details**:
  Add after Step 1 (Determine Scope) identifies changed files. Place as
  **Step 1.3: Consult Brain** (before Step 1.5 Content-Based Depth Overrides).

  Content (~5 lines):
  ```
  ### Step 1.3: Consult Brain

  If `brain-enabled = false`, skip this step.

  Load `cg-skill-brain-query`. Search the brain for: known mistakes and
  anti-patterns documented for the file types and domains being reviewed,
  past review findings in similar code areas, patterns that reviewers should
  verify. Pass relevant findings to review agents as additional context.
  ```
- **Test Scenarios**:
  - ✅ Step exists between Step 1 and Step 1.5
  - ✅ Directive mentions known mistakes/anti-patterns
- **Acceptance criteria**: Step present with correct placement

### 7. Add "Consult Brain" step to `/cg-fix-triage`

- **Requirements**: R10, R12, R13
- **Files**: `.github/prompts/cg-fix-triage.prompt.md`
- **Details**:
  Add after Step 1 (Load Review Report) parses findings. The existing Step 0.5
  loads language skills. Place as **Step 1.3: Consult Brain** (after Step 1
  loads report, before Step 2 determines scope).

  Content (~5 lines):
  ```
  ### Step 1.3: Consult Brain

  If `brain-enabled = false`, skip this step.

  Load `cg-skill-brain-query`. Search the brain for: known fixes for the
  specific findings in this report, solutions that address the same code
  patterns flagged by reviewers, past fix-triage sessions that resolved
  similar issues. Incorporate as fix guidance for each finding.
  ```
- **Test Scenarios**:
  - ✅ Step exists after Step 1, before Step 2
  - ✅ Directive mentions known fixes/similar findings
- **Acceptance criteria**: Step present with correct placement

### 8. Add "Consult Brain" step to `/cg-compound`

- **Requirements**: R11, R12, R13
- **Files**: `.github/prompts/cg-compound.prompt.md`
- **Details**:
  Add after Step 1 (Gather Context) understands the solution. Place as
  **Step 1.5: Consult Brain** (before Step 2 Categorize).

  Content (~5 lines):
  ```
  ### Step 1.5: Consult Brain

  If `brain-enabled = false`, skip this step.

  Load `cg-skill-brain-query`. Search the brain for: existing solutions that
  this new entry might supersede or contradict, related entries that should
  cross-reference this solution, patterns this solution contributes to.
  Flag any supersession or contradiction for the user before writing.
  ```
- **Test Scenarios**:
  - ✅ Step exists after Step 1, before Step 2
  - ✅ Directive mentions supersede/contradict
- **Acceptance criteria**: Step present with correct placement

## Phase 2: Tests and registration

### 9. Write Pester tests for brain integration

- **Requirements**: R14
- **Files**: `tests/prompt-tools.Tests.ps1` (modify — add new Describe block)
- **Details**:
  Add a `Describe "Brain integration"` block with:
  - Test: each of 6 prompts contains `--no-brain`
  - Test: each of 6 prompts contains `Consult Brain` step header
    Match pattern: `($content -match '(?i)Consult Brain')` — robust to
    renumbering (does not hardcode step numbers)
  - Test: each of 6 prompts contains `cg-skill-brain-query` reference
  - Test: each of 6 prompts contains `brain-enabled = false` guard
  - Test: `/cg-review` recognized-arguments string includes `--no-brain`
  - Test: `/cg-fix-triage` recognized-arguments string includes `--no-brain`
  - Test: `cg-skill-brain-query` SKILL.md exists with valid frontmatter
  - Test: skill contains "contradiction" and "staleness" coverage
  - Test: skill does not contain write/modify instructions (read-only)
- **Test Scenarios**:
  - ✅ All tests pass when features are correctly implemented
  - 🛑 Edge: tests use `($content -match '(?i)Consult Brain')` — no step
    number dependency; robust to renumbering
  - ❌ Error: test fails clearly if a prompt is missing the brain step
- **Acceptance criteria**: All new tests pass; existing tests still pass

### 10. Register skill in copilot-instructions.md skill catalog

- **Requirements**: R1
- **Files**: `.github/copilot-instructions.md` (modify)
- **Details**:
  The skill is auto-discovered by VS Code from `.github/skills/cg-skill-brain-query/SKILL.md`.
  However, add a mention in the copilot-instructions.md under the skill
  loading guidance so agents know when to load it:
  "Load `cg-skill-brain-query` when executing a 'Consult Brain' step in any
  major prompt."
- **Test Scenarios**:
  - ✅ copilot-instructions.md mentions `cg-skill-brain-query`
- **Acceptance criteria**: Skill is referenced in instructions

## Testing Strategy

- **Unit tests** (Pester): text-matching assertions on prompt file contents
  verifying presence of flag parsing, step headers, skill references, and guards.
- **Structural test**: SKILL.md exists, has valid frontmatter, covers required
  protocol sections.
- **Read-only assertion**: skill file contains no language suggesting writes to
  BRAIN.md or brain-index.json.
- Run via canonical `execution_subagent` + `tests/Run-Tests.ps1` pattern.

## Documentation Checklist

- [x] Skill SKILL.md (self-documenting — the skill IS the documentation)
- [ ] No README changes needed (internal plugin feature)
- [ ] No external user docs needed (brain is consumed transparently)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Context budget overflow from brain reads | Agent reads too many sub-files | Skill protocol limits to matched topics only; anti-pattern section warns against reading all |
| Step numbering collisions | New step number conflicts with existing | Verify numbering in each prompt before insertion; use unused numbers |
| Stale BRAIN.md gives bad advice | Outdated entries mislead the agent | Staleness detection in skill protocol; recency preference in prioritization |
| Brain search adds latency to all commands | Slower startup for every invocation | Search is a file read + keyword match — fast; no external calls |
| Prompts grow too large | Token budget for prompt files | Each step is 4-6 lines — minimal impact (~30 lines total across 6 files) |

## Out of Scope

- Changes to the brain engine (`scripts/brain/`) or its output format
- Cross-project team brain consultation (Batch D)
- Writing back to brain artifacts from prompts (read-only)
- Auto-skip heuristics for when to bypass brain consultation
- Changes to agents (only prompts and the new skill)
