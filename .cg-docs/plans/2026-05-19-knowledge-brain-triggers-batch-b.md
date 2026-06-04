---
date: 2026-05-19
title: "Knowledge Brain Triggers — Batch B"
status: completed
completed-date: 2026-05-19
completed-phases: [1, 2]
scope: "Lightweight"
brainstorm: null
language: "PowerShell"
estimated-effort: "small"
tags: [brain, rebuild, compound, prompt, cg-index, triggers]
phases: 2
---

# Plan: Knowledge Brain Triggers — Batch B

## Objective

Wire the brain rebuild into two user-facing entry points: an explicit
`/cg-brain-rebuild` command for on-demand use, and automatic triggering after
`/cg-compound` captures a solution. This ensures `BRAIN.md` stays current
without manual intervention.

## Context

- Batch A (complete): the brain engine (`scripts/brain/`) and its CLI
  entry point (`cg-index --brain`) are fully functional.
- `cg-compound.prompt.md` Step 3b currently runs `cg-index --digest`
  (legacy mode). The `--brain` flag supersedes `--digest` and produces the
  full BRAIN output (BRAIN.md, BRAIN-01…N.md, BRAIN-log.md, brain-index.json).
- Strategy specifies: automatic rebuild on `/cg-compound`, explicit rebuild
  via `/cg-brain-rebuild`. All other commands consume the brain (read path)
  but don't rebuild it.

## Requirements

| ID  | Requirement                                                    | Source   |
|-----|----------------------------------------------------------------|----------|
| R1  | `/cg-brain-rebuild` prompt exists and triggers `cg-index --brain` | strategy |
| R2  | The prompt validates brain output exists after rebuild          | strategy |
| R3  | `/cg-compound` Step 3b runs `cg-index --brain` instead of `--digest` | strategy |
| R4  | Legacy `DIGEST.md` and `search-index.json` are removed on successful brain build | cg_index.py (already implemented) |
| R5  | Prompt tests cover both new features                           | project convention |

## Phase 1: `/cg-brain-rebuild` prompt

### 1. Create `.github/prompts/cg-brain-rebuild.prompt.md`

- **Requirements**: R1, R2
- **Files**: `.github/prompts/cg-brain-rebuild.prompt.md`
- **Details**:
  - Frontmatter: `description: "Rebuild the project knowledge brain (BRAIN.md + indexes)."`, model same as other prompts (`Claude Sonnet 4.6 (copilot)`)
  - Step 0: standard bearings (read charter, local, context — same as all prompts)
  - Step 1: Run `cg-index --brain` in terminal from project root
  - Step 2: Verify success — primary signal is exit code 0. Secondary confirmation: scan stdout for the line matching `[cg-index] Brain index written to` and parse entity/topic/edge counts from it (do NOT rely on "last line" — legacy removal messages may follow). Also confirm `.cg-docs/BRAIN.md` exists as a tertiary check.
  - Step 3: If `cg-index` is not available or fails (exit code ≠ 0), report the error clearly and suggest the two most likely causes: (a) `cg-index` not on PATH — verify with `cg-index --version`; (b) not running from project root — `.cg-docs/` directory must exist in cwd
  - Keep it simple — this is a "run one command and report results" prompt
- **Test Scenarios**:
  - ✅ Prompt file exists and has correct frontmatter
  - ✅ Prompt references `cg-index --brain` command
  - ✅ Prompt uses exit code as primary success signal
  - ✅ Prompt includes error handling for missing `cg-index` / missing `.cg-docs/`
- **Acceptance criteria**: Prompt file passes structural tests; invoking `/cg-brain-rebuild` in a project with `.cg-docs/` produces an updated `BRAIN.md`

### 2. Register `/cg-brain-rebuild` in Workflow Entry Points

- **Requirements**: R1
- **Files**: `.github/copilot-instructions.md`
- **Details**:
  - Add a row to the Workflow Entry Points table:
    `| Rebuild knowledge brain | \`/cg-brain-rebuild\` |`
  - Place it near the existing knowledge-capture commands (`/cg-compound`, `/cg-compound-refresh`)
- **Acceptance criteria**: Table contains `/cg-brain-rebuild` entry

### 3. Add test coverage for the new prompt

- **Requirements**: R5
- **Files**: `tests/prompt-tools.Tests.ps1` (add Describe block)
- **Details**:
  - Add a Describe block `"/cg-brain-rebuild prompt"` that:
    - Asserts file exists at `.github/prompts/cg-brain-rebuild.prompt.md`
    - Asserts frontmatter contains `description:`
    - Asserts content references `cg-index --brain`
    - Asserts content references `BRAIN.md` (verification step)
    - Asserts content includes error-handling guidance (exit code or "not available")
- **Acceptance criteria**: New test block passes in `prompt-tools.Tests.ps1`

## Phase 2: Wire brain rebuild into `/cg-compound`

### 4. Update `cg-compound.prompt.md` Step 3b to use `--brain`

- **Requirements**: R3, R4
- **Files**: `.github/prompts/cg-compound.prompt.md`
- **Details**:
  - Replace `cg-index --digest` with `cg-index --brain` in Step 3b
  - Update the step title from "Rebuild Knowledge Digest" to "Rebuild Knowledge Brain"
  - Update the narrative: "Run `cg-index --brain` from the project root to
    rebuild the full knowledge brain (BRAIN.md, topic index, entity catalog,
    edge list). This regenerates the brain from all `.cg-docs/` artifacts —
    guaranteeing the brain reflects the newly captured solution."
  - Keep the fallback note: "If `cg-index` is not available, note it in the
    Step 6 confirmation and skip."
  - Keep the modulo-10 notification (unrelated to brain — it's solution count)
  - Update the File Permissions comment: change `cg-index --digest` reference to `cg-index --brain`
- **Test Scenarios**:
  - ✅ `cg-compound.prompt.md` no longer references `--digest`
  - ✅ `cg-compound.prompt.md` references `cg-index --brain`
  - ✅ `cg-compound.prompt.md` references `BRAIN.md` in Step 3b
- **Acceptance criteria**: `cg-compound.prompt.md` uses `--brain` flag; prompt-tools tests pass

### 5. Add/update test coverage for compound brain integration

- **Requirements**: R5
- **Files**: `tests/prompt-tools.Tests.ps1` (update existing compound tests)
- **Details**:
  - In existing `/cg-compound prompt` Describe block (or add to it):
    - Assert content matches `cg-index --brain` (not `--digest`)
    - Assert Step 3b title references "Brain" (not "Digest")
  - Negative assertion: `$content -match '--digest'` should be `$false`
    (ensure no leftover legacy references in compound prompt)
- **Acceptance criteria**: All prompt-tools tests pass; no `--digest` references remain in `cg-compound.prompt.md`

## Testing Strategy

Structural Pester tests in `tests/prompt-tools.Tests.ps1` — same pattern as
all other prompt tests in this project. Verify file existence, frontmatter
validity, and key content assertions. No runtime/integration tests needed
for prompt files (the prompts are instructions, not executable code).

## Documentation Checklist

- [x] Prompt file has description in frontmatter (serves as docs)
- [x] `copilot-instructions.md` Workflow Entry Points table (Step 2 above)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `cg-index` not on PATH in some installations | Prompt includes fallback guidance; `bin/cg-index` shimmed during install |
| Legacy `--digest` callers confused by removal | `--digest` still works (deprecated alias in cg_index.py) — only the prompt changes |

## Out of Scope

- Brain read path (Batch C) — prompts don't consume BRAIN.md yet
- Cross-project team brain (Batch D)
- Changes to `cg_index.py` itself (engine is complete from Batch A)
- `docs/reference.md` command table update (separate docs PR)
- `docs/workflow.md` knowledge capture flow update (separate docs PR)
