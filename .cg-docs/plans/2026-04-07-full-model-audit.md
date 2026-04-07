---
date: 2026-04-07
title: "Full model audit across prompts and agents"
status: completed
completed-date: 2026-04-07
brainstorm: ".cg-docs/brainstorms/2026-04-07-full-model-audit.md"
language: "PowerShell"
estimated-effort: "medium"
tags: [performance, model-audit, tokens, prompts, agents, review]
---

# Plan: Full Model Audit Across Prompts and Agents

## Objective

Audit all 22 model-assigned files (12 prompts + 10 agents) in Compound GPID
to ensure each uses the cheapest Claude tier that preserves output quality.
Produce a documented model assignment table, apply high-confidence frontmatter
changes, create a user-facing model selection guide, and add retry guidance
to `/cg-review` for subagent failures. Quality is non-negotiable — token
efficiency is the primary optimization, speed is secondary.

## Context

- **Brainstorm decision**: Approach 3 — Heuristic classification + targeted
  empirical validation ([brainstorm](.cg-docs/brainstorms/2026-04-07-full-model-audit.md))
- **Current state**: 3 Opus prompts, 8 Sonnet prompts + 4 Sonnet agents,
  1 Haiku prompt + 6 Haiku agents
- **Priority order**: Quality > Tokens > Speed
- **Out of scope**: automated fallback, GPT models, `compound-gpid.local.md`
  overrides, duplicated escalation agents

### Current Model Inventory

| File | Current Model | Type |
|------|---------------|------|
| cg-strategy.prompt.md | Opus 4.6 | prompt |
| cg-plan.prompt.md | Opus 4.6 | prompt |
| cg-brainstorm.prompt.md | Opus 4.6 | prompt |
| cg-work.prompt.md | Sonnet 4.6 | prompt |
| cg-setup.prompt.md | Sonnet 4.6 | prompt |
| cg-review.prompt.md | Sonnet 4.6 | prompt |
| cg-fixbug.prompt.md | Sonnet 4.6 | prompt |
| cg-fix-triage.prompt.md | Sonnet 4.6 | prompt |
| cg-devtag.prompt.md | Sonnet 4.6 | prompt |
| cg-compound.prompt.md | Sonnet 4.6 | prompt |
| cg-resume.prompt.md | Haiku 4.5 | prompt |
| cg-release.prompt.md | Sonnet 4.6 | prompt |
| cg-roadmap.agent.md | Haiku 4.5 | agent |
| cg-code-quality.agent.md | Haiku 4.5 | agent |
| cg-testing.agent.md | Haiku 4.5 | agent |
| cg-documentation.agent.md | Haiku 4.5 | agent |
| cg-version-control.agent.md | Haiku 4.5 | agent |
| cg-reproducibility.agent.md | Haiku 4.5 | agent |
| cg-learnings-researcher.agent.md | Haiku 4.5 | agent |
| cg-performance.agent.md | Sonnet 4.6 | agent |
| cg-data-quality.agent.md | Sonnet 4.6 | agent |
| cg-architecture.agent.md | Sonnet 4.6 | agent |

### Task Complexity Analysis (from research)

**Prompts:**

| Prompt | Reasoning | Precision | Orchestration | Creativity | Tool Use |
|--------|:---------:|:---------:|:-------------:|:----------:|:--------:|
| cg-strategy | 5 | 5 | 5 | 4 | 2 |
| cg-brainstorm | 4 | 4 | 4 | 4 | 3 |
| cg-plan | 4 | 4 | 4 | 3 | 3 |
| cg-work | 3 | 5 | 4 | 2 | 5 |
| cg-review | 4 | 5 | 5 | 3 | 4 |
| cg-fixbug | 4 | 5 | 4 | 3 | 3 |
| cg-release | 4 | 5 | 4 | 4 | 4 |
| cg-compound | 3 | 4 | 3 | 4 | 3 |
| cg-setup | 2 | 5 | 5 | 1 | 4 |
| cg-fix-triage | 2 | 5 | 4 | 2 | 4 |
| cg-devtag | 2 | 4 | 3 | 1 | 3 |
| cg-resume | 3 | 5 | 3 | 2 | 4 |

**Agents:**

| Agent | Reasoning | Precision | Orchestration | Creativity | Tool Use |
|-------|:---------:|:---------:|:-------------:|:----------:|:--------:|
| cg-performance | 5 | 5 | 1 | 4 | 3 |
| cg-data-quality | 5 | 4 | 1 | 4 | 3 |
| cg-architecture | 5 | 5 | 1 | 4 | 3 |
| cg-code-quality | 4 | 5 | 1 | 3 | 3 |
| cg-testing | 4 | 4 | 1 | 3 | 3 |
| cg-reproducibility | 4 | 4 | 1 | 3 | 3 |
| cg-learnings-researcher | 3 | 3 | 2 | 4 | 5 |
| cg-roadmap | 3 | 4 | 2 | 2 | 4 |
| cg-documentation | 3 | 4 | 1 | 2 | 3 |
| cg-version-control | 3 | 4 | 1 | 2 | 3 |

## Implementation Steps

### 1. Heuristic Classification — Identify Change Candidates

- **Files**: None (analysis only — document in session memory for Step 2)
- **Details**:
  Apply the following classification criteria to every file in the inventory:

  **Tier criteria (cheapest adequate model):**

  | Criterion | Haiku 4.5 | Sonnet 4.6 | Opus 4.6 |
  |-----------|-----------|------------|----------|
  | Reasoning depth | 1-3 | 3-4 | 5 |
  | Creative judgment | 1-2 | 3-4 | 4-5 |
  | Instruction precision | any (Haiku follows rules well) | any | any |
  | Multi-step orchestration | 1-2 | 3-4 | 5 |
  | Subagent dispatch | none | light | heavy |

  **Decision logic per file:**
  - If max(reasoning, creativity) <= 3 AND orchestration <= 2 → **Haiku candidate**
  - If max(reasoning, creativity) >= 5 AND orchestration >= 5 → **Opus required**
  - Everything else → **Sonnet**

  **Compare current tier vs. recommended tier:**
  - If current = recommended → **no change** (mark as "confirmed")
  - If current > recommended → **downgrade candidate** (mark confidence: high/medium)
  - If current < recommended → **upgrade candidate** (mark confidence: high/medium)

  **Preliminary analysis (based on research):**

  Confirmed (no change expected):
  - cg-strategy → Opus (reasoning 5, orchestration 5 — justified)
  - cg-work → Sonnet (precision 5, tool use 5, reasoning 3)
  - cg-review → Sonnet (orchestration 5, dispatches 9 subagents)
  - cg-fixbug → Sonnet (reasoning 4, precision 5)
  - cg-release → Sonnet (reasoning 4, creativity 4, multi-step)
  - cg-resume → Haiku (mechanical context scanning, reasoning 3)
  - cg-roadmap → Haiku (JSON manipulation, reasoning 3)
  - cg-documentation → Haiku (checklist review, creativity 2)
  - cg-version-control → Haiku (checklist review, creativity 2)
  - cg-performance → Sonnet (reasoning 5, creativity 4)
  - cg-data-quality → Sonnet (reasoning 5, creativity 4)
  - cg-architecture → Sonnet (reasoning 5, creativity 4)

  Downgrade candidates:
  - **cg-brainstorm**: Opus → Sonnet? (reasoning 4, creativity 4 — borderline)
  - **cg-plan**: Opus → Sonnet? (reasoning 4, creativity 3 — borderline)
  - **cg-setup**: Sonnet → Haiku? (reasoning 2, creativity 1 — strong candidate)
  - **cg-devtag**: Sonnet → Haiku? (reasoning 2, creativity 1 — strong candidate)

  Confirmed to stay (decided during planning):
  - **cg-fix-triage**: Keep Sonnet. User observed that review-fix-review
    cycles produce new findings — fix quality matters. Downgrading the
    fixer would lengthen the loop.
  - **cg-compound**: Keep Sonnet. Creativity 4 for lesson extraction
    is risky on Haiku — generalisation quality matters.

  Upgrade candidates (monitor, don't change yet):
  - **cg-code-quality / cg-testing / cg-reproducibility**: Keep Haiku.
    User observed second reviews finding more issues, but this is likely
    caused by fixes introducing new code rather than Haiku missing
    original issues. Monitor in future sessions — if second reviews
    consistently find issues in *unchanged* lines, revisit.
  - **cg-learnings-researcher**: Keep Haiku. Mostly search, not reasoning.

- **Tests**: N/A (analysis step)
- **Acceptance criteria**: Every file classified as confirmed/downgrade/upgrade
  with a confidence level and rationale.

### 2. Categorize Changes by Confidence

- **Files**: None (analysis checkpoint)
- **Details**:
  Split candidates into two buckets:

  **High-confidence changes** (apply immediately in Step 3):
  - Downgrade cg-setup Sonnet → Haiku (mechanical scaffolding, no reasoning)
  - Downgrade cg-devtag Sonnet → Haiku (simple git tag, template-following)

  **Borderline changes** (require empirical validation in Step 7):
  - cg-brainstorm Opus → Sonnet (creative Q&A — needs pushback quality test)
  - cg-plan Opus → Sonnet (structured research — needs plan quality test)

  All other candidates were resolved during planning (see Step 1).

- **Tests**: N/A
- **Acceptance criteria**: Two buckets clearly defined, user approves
  high-confidence changes and selects borderline candidates for testing.

### 3. Apply High-Confidence Frontmatter Changes

- **Files**:
  - `.github/prompts/cg-setup.prompt.md` — change `model: Claude Sonnet 4.6 (copilot)` to `model: Claude Haiku 4.5 (copilot)`
  - `.github/prompts/cg-devtag.prompt.md` — change `model: Claude Sonnet 4.6 (copilot)` to `model: Claude Haiku 4.5 (copilot)`
- **Details**:
  Edit only the `model:` line in YAML frontmatter. No body changes.
- **Tests**:
  Add/update test in `tests/prompt-tools.Tests.ps1`:
  - Verify cg-setup model is `Claude Haiku 4.5 (copilot)`
  - Verify cg-devtag model is `Claude Haiku 4.5 (copilot)`
  - Add a comprehensive model assignment test that validates ALL 22 files
    against the expected model (prevents drift):
    ```
    Describe "Model assignments" {
        @{File='cg-strategy.prompt.md'; Model='Claude Opus 4.6 (copilot)'},
        @{File='cg-setup.prompt.md'; Model='Claude Haiku 4.5 (copilot)'},
        ...
    }
    ```
- **Acceptance criteria**: Frontmatter updated, Pester tests pass.

### 4. Create Model Selection Guide

- **Files**:
  - `docs/model-guide.md` (new)
- **Details**:
  Create a reference document containing:

  **Section 1: Model Assignment Table**
  For each of the 22 files:
  - File path
  - Assigned model
  - Task description (one line)
  - Tier rationale (one line)
  - Confidence: confirmed / changed / borderline-pending

  **Section 2: Tier Criteria**
  Document the heuristic classification criteria from Step 1 so future
  audits can reuse the same framework.

  **Section 3: Manual Override Guidance**
  - How to switch models in the VS Code model picker (per-session)
  - When to override: if a prompt feels sluggish, if output quality seems
    low, if token consumption is unexpectedly high
  - Recommended overrides per scenario:
    - "If `/cg-brainstorm` isn't pushing back enough" → switch to Opus
    - "If `/cg-setup` is slow" → confirm it's on Haiku
    - "If a review agent misses obvious issues" → re-run `/cg-review` at
      a higher depth tier, or switch specific agents to Sonnet manually

  **Section 4: Token Cost Reference**
  Approximate relative cost ratios (Opus ~5x Sonnet, Sonnet ~5x Haiku)
  so users can reason about trade-offs.

- **Tests**: N/A (documentation file)
- **Acceptance criteria**: Guide covers all 22 files, criteria are reusable,
  override guidance is actionable.

### 5. Add Retry Guidance to `/cg-review`

- **Files**:
  - `.github/prompts/cg-review.prompt.md` — add subagent quality check
    after Step 2
- **Details**:
  After dispatching each subagent in Step 2, add an instruction block:

  ```
  ### Step 2.5: Subagent Output Quality Check

  After each subagent returns, quickly assess:
  - Did it produce findings or explicitly state "no issues found"?
  - Is the output non-empty and relevant to the changed files?

  If a subagent's output is empty, garbled, or clearly incomplete:
  1. Note this in the review report under a new "⚠️ Incomplete Reviews"
     section.
  2. Suggest: "Agent @<name> did not produce usable output. Consider
     re-running `/cg-review` with the model picker set to a higher tier,
     or invoke @<name> directly."
  3. Do NOT retry the agent automatically — the user controls model
     selection.
  ```

- **Tests**:
  Add to `tests/prompt-tools.Tests.ps1`:
  - Verify `cg-review.prompt.md` contains the string "Subagent Output Quality Check"
  - Verify presence of the "Incomplete Reviews" instruction
- **Acceptance criteria**: `/cg-review` prompt includes step 2.5, Pester
  tests pass.

### 6. Create Audit Reference Document

- **Files**:
  - `.cg-docs/solutions/performance-issues/2026-04-07-model-audit-classification.md` (new)
- **Details**:
  Capture the full audit results as a compound-docs solution:
  - Classification criteria (the tier table from Step 1)
  - Per-file analysis results
  - High-confidence changes applied
  - Borderline candidates and their status
  - Token cost reference

  This ensures future audits can reference and extend this work rather than
  starting from scratch.

- **Tests**: N/A (documentation file)
- **Acceptance criteria**: Solution file follows `.cg-docs/solutions/`
  conventions, includes all analysis data.

### 7. Empirical Validation Protocol (Borderline Candidates)

- **Files**: Depends on test results — frontmatter changes to borderline files
- **Details**:
  For each borderline candidate the user selects for testing:

  **Test protocol:**
  1. Run the prompt/agent on a representative task at its **current** tier.
     Save the full output.
  2. Switch the model in VS Code's model picker to the **proposed** tier.
     Run the same task. Save the full output.
  3. Compare on these criteria:
     - Did it follow all prompt instructions? (check conditional rules)
     - Did it produce findings of equivalent depth? (for review agents)
     - Did it miss anything the other tier caught?
     - Was the output well-structured?
  4. Verdict: **equivalent** (apply change), **degraded** (keep current),
     or **inconclusive** (keep current, re-test later)

  **Update protocol after each test:**
  - If equivalent: update frontmatter in the tested file.
  - Update the model assignment test in `tests/prompt-tools.Tests.ps1`.
  - Update `docs/model-guide.md` to change "borderline-pending" to "changed" or "confirmed".

  This step is designed for a follow-up session, not the initial
  implementation session.

- **Tests**: Update model assignment test per file changed.
- **Acceptance criteria**: Each tested file has a documented verdict,
  frontmatter updated for equivalent cases, model guide updated.

## Testing Strategy

- **Model assignment drift test** (new): A single parametrized Pester test
  that validates all 22 files have their expected `model:` frontmatter value.
  This prevents accidental model changes and serves as a living contract.
- **Review prompt structure test**: Verify the retry guidance step exists in
  `cg-review.prompt.md`.
- **No functional tests needed**: Model assignments are frontmatter metadata;
  the actual model behavior is tested empirically in Step 7.

## Documentation Checklist

- [ ] `docs/model-guide.md` — Model assignment table, tier criteria, override
      guidance, cost reference
- [ ] `.cg-docs/solutions/performance-issues/` — Audit methodology and results
      captured for future reference
- [ ] `docs/reference.md` —  Add cross-reference to `docs/model-guide.md` if
      a model-guide section doesn't already exist

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Haiku can't follow complex cg-setup instructions | cg-setup's branching is structural (if/else on project state), not reasoning-heavy. Haiku handles conditional logic well. Test empirically if quality concern arises. |
| cg-devtag on Haiku botches git operations | cg-devtag is 3 git commands with clear rules. If issues arise, user can switch to Sonnet in picker. |
| Model guide becomes stale after future changes | The model assignment drift test catches unannounced changes. Guide update is part of any future model change checklist. |
| Borderline tests are subjective | Use the 4-point checklist (instructions followed, finding depth, nothing missed, well-structured). Two side-by-side runs reduce bias. |

## Out of Scope

- Automated fallback / retry mechanisms (platform limitation)
- GPT model testing or fallback recommendations
- `compound-gpid.local.md` model config overrides
- Duplicated escalation agent files
- Changes to the compound-engineering-plugin (separate session)
- Performance benchmarking (latency/token counting) — this audit is
  qualitative, not quantitative
