---
date: 2026-04-10
title: "@cg-fix-problems agent and /cg-fix-problems prompt"
status: decided
scope: "Standard"
chosen-approach: "Single agent + prompt wrapper"
tags: [quality-loop, diagnostics, auto-fix, agent, prompt, cg-work]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# @cg-fix-problems Agent and /cg-fix-problems Prompt

## Context

The Quality Loop milestone needs auto-fix diagnostics capability. Currently:
- `/cg-fixbug` handles user-reported bugs (reproduce → diagnose → fix arc)
- `/cg-fix-triage` applies findings from review reports in `.cg-docs/reviews/`
- Neither covers VS Code Problems panel diagnostics (syntax errors, lint
  warnings, type errors, unresolved imports, test failures)

The gap: when `/cg-work` Step 2 runs tests and they fail, or when the VS Code
Problems panel lights up with errors, there's no automated fix pathway. The
developer must manually diagnose and fix before continuing.

## Requirements

### Input Sources
- VS Code Problems panel diagnostics (via `get_errors` tool)
- Test failures (test runner output)
- Runtime errors, compilation failures, lint/type errors

### Two Modes

**Auto mode** (dispatched by `/cg-work` after Step 2.4 failures):
- Scope: only files touched by the current `/cg-work` step
- Severity filter: errors only (no warnings, no info)
- No user confirmation before fixing
- 2-round budget: fix → verify → fix again → verify → stop
- If errors remain after 2 rounds: skip, continue `/cg-work`, notify user
  with list of unfixed problems

**Interactive mode** (standalone `/cg-fix-problems`):
- Scope: all files in workspace (user can narrow)
- Severity: all levels (errors, warnings, info)
- Hybrid discovery: auto-scan Problems panel, show user what was found,
  let them select scope (all, by file, by severity) before fixing
- No round limit — user controls when to stop

### Retry Protocol (Auto Mode)
- Per-round, not per-problem
- Round 1: fix all errors in scoped files → re-check diagnostics
- Round 2: fix remaining + newly introduced errors → re-check
- After round 2: report unfixed problems and continue

### Relationship to Existing Prompts
- Does NOT replace `/cg-fixbug` (user-reported bugs with reproduce/diagnose)
- Does NOT replace `/cg-fix-triage` (review report findings)
- Complements both — handles a different input source (VS Code diagnostics)

## Approaches Considered

### Approach 1: Single Agent + Prompt Wrapper (chosen)

One `@cg-fix-problems` agent supports both auto and interactive modes. Mode
behavior (severity filter, user confirmation, scope) is parameterized by the
caller. `/cg-fix-problems` prompt sets interactive mode and dispatches.
`/cg-work` dispatches in auto mode.

- **Pros**: Single source of fix logic. One file to maintain. Mode branching
  is clean — caller provides context.
- **Cons**: Agent file is slightly more complex (mode branching). Haiku tier
  may struggle with interactive mode's broader scope.
- **Effort**: Medium

### Approach 2: Separate Agent + Separate Prompt (Fully Independent)

`@cg-fix-problems` agent is auto-mode only (Haiku, errors-only, 2 rounds).
`/cg-fix-problems` prompt is interactive-mode only (Sonnet, hybrid discovery,
all severities). No shared logic.

- **Pros**: Each file is simpler. Model tier optimized per mode.
- **Cons**: Fix protocol duplicated — if protocol changes, update both files.
- **Effort**: Medium

### Approach 3: Prompt-Only (Inline Auto-Fix in /cg-work)

No agent file. `/cg-work` gets inline auto-fix instructions. Standalone prompt
for interactive use.

- **Pros**: Fewest new files. Simple.
- **Cons**: `/cg-work` grows more complex. Auto-fix logic not reusable.
- **Effort**: Small

## Decision

Approach 1 — Single Agent + Prompt Wrapper. Best balance of modularity and
maintainability. Single source of fix logic avoids DRY violations while
keeping both modes operational.

## Next Steps

1. Create `@cg-fix-problems` agent (`.github/agents/cg-fix-problems.agent.md`)
   with dual-mode support (auto + interactive)
2. Create `/cg-fix-problems` prompt (`.github/prompts/cg-fix-problems.prompt.md`)
   that sets interactive mode and dispatches the agent
3. Modify `/cg-work` Step 2 to auto-dispatch `@cg-fix-problems` in auto mode
   after test/validate failures
4. Add tests in `tests/prompt-tools.Tests.ps1`
5. Register in `copilot-instructions.md` Workflow Entry Points and
   `docs/reference.md`
6. Update roadmap features to active/done
