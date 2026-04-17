---
date: 2026-04-17
title: "Structural prevention of agent-caused Pester crashes"
status: decided
scope: "Standard"
chosen-approach: "Full Stack — JSON Artifact + Prompt Hardening"
tags: [pester, crash-prevention, agent-safety, testing, powershell, architecture]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Structural Prevention of Agent-Caused Pester Crashes

## Context

AI agents (including Copilot) have crashed VS Code 18+ confirmed times by using
forbidden Pester patterns — `Invoke-Pester tests/`, `2>&1 | ...` pipelines,
`-PassThru | Select-Object -ExpandProperty TestResult`, etc. The prohibition is
documented in 4+ locations (copilot-instructions.md, compound-gpid.local.md,
cg-skill-pester-safety, memory notes) but enforcement is documentation-only.
After context compaction, agents revert to naive PowerShell idioms and crash VS Code.

**Crash distribution** (18 confirmed):
- **~72% Category A**: Agent composes forbidden `Invoke-Pester` commands from
  scratch, ignoring all documentation. Happens after every context reset.
- **~28% Category B**: Agent uses nominally "safe" patterns but in long sessions
  where even `-Quiet -PassThru` via `run_in_terminal` floods the context window
  with 300+ lines of test output.
- **0% Category C**: No user-caused crashes — users never run Pester directly.

The current system has the right *knowledge* (safety rules are well-documented)
but the wrong *architecture* (nothing prevents an agent from ignoring the rules).

## Requirements

1. **Category A elimination**: Make it architecturally unnecessary for an agent to
   ever compose an `Invoke-Pester` command. The safe wrapper must be the only
   entry point, enforced by literal copy-paste blocks in every prompt that runs tests.

2. **Category B elimination**: Decouple test results from agent context entirely.
   Agents must read a bounded-size artifact file, not terminal output. The artifact
   must be ~500 bytes regardless of test suite size.

3. **Artifact schema**: JSON file at `tests/last-run.json` with:
   - Top-level: `passed` (bool), `totalCount`, `passedCount`, `failedCount`,
     `gitSha` (for staleness detection), `ranAt` (for crash diagnosis)
   - Per-file array: `name`, `total`, `passed`, `failed`
   - Failures array: `file`, `describe`, `context`, `name`, `message`
   - No passing test names — actively harmful noise

4. **Single-file mode**: `Run-Tests.ps1 -File prompt-tools` for fast feedback
   during implementation (~5s vs ~60s full suite). Full suite mandatory before commit.

5. **Staleness detection**: Git SHA in artifact; agent compares with
   `git rev-parse --short HEAD` before trusting results.

6. **Atomic write**: Write-then-rename pattern to prevent partial-artifact reads
   on runner crash.

7. **Prompt hardening**: Every test-running prompt contains a literal
   `execution_subagent` block with the exact query, the `Invoke-Pester` prohibition
   adjacent, and the if-passed/if-failed decision logic inline.

8. **Regression tests**: `prompt-tools.Tests.ps1` verifies the literal
   `execution_subagent` block exists in each hardened prompt (same `Get-Content +
   regex` pattern used elsewhere). This converts copy-paste maintenance from a
   permanent liability into a detected regression.

9. **Self-contained prompts**: Each prompt embeds its own test block — no
   cross-prompt references. Consistent with the project's documented prompt design
   convention (prompts must work standalone without prior context).

10. **Audit trail**: The JSON artifact serves as verification that tests were run
    and passed — not just for agent decision-making, but for crash diagnosis
    (`/cg-diagnose` can read it) and post-hoc verification. The `execution_subagent`
    approach alone provides no persistent audit trail.

## Approaches Considered

### Approach 1: Full Stack — JSON Artifact + Prompt Hardening (CHOSEN)

Modify `Run-Tests.ps1` to emit a bounded `tests/last-run.json` artifact, add
`-File` mode, and replace all test-running instructions across prompts with literal
`execution_subagent` copy-paste blocks that read the artifact instead of parsing
terminal output.

**Components**:
1. `Run-Tests.ps1` upgrades: `-File` param, JSON artifact emission, git SHA,
   atomic write-then-rename, `.gitignore` entries
2. Prompt hardening: literal `execution_subagent` blocks in `/cg-work`,
   `/cg-fix-triage`, `/cg-diagnose`, `cg-fix-problems` agent
3. Safety docs update: `cg-skill-pester-safety/SKILL.md` updated to show
   artifact-based workflow as THE pattern; old `$r = Invoke-Pester` demoted to
   "debugging only, never in agent workflows"
4. `copilot-instructions.md` update: reference `last-run.json` as canonical output
5. Regression tests: `prompt-tools.Tests.ps1` tests verifying literal blocks exist
   in each hardened prompt; tests for `-File` parameter behavior

**Pros**: Addresses both Category A (72%) and B (28%) structurally. Agent never
composes `Invoke-Pester`. Artifact is ~500 bytes. Git SHA staleness. Atomic write.

**Cons**: Touches 6+ files. Literal blocks in prompts are copy-paste — but
regression tests detect drift.

### Approach 2: JSON Artifact Only (Minimal)

Upgrade `Run-Tests.ps1` only, no prompt changes.

**Pros**: Smaller scope. Solves Category B.

**Cons**: Does not address Category A (72% of crashes). Agent can still compose
forbidden commands after context compaction. Does not meet "near zero" goal.

### Approach 3: Full Stack + Dedicated `/cg-test` Prompt

Everything in Approach 1 plus a `/cg-test` prompt as a callable subroutine.

**Pros**: Single source of truth for test logic.

**Cons**: Copilot prompts can't dispatch to other prompts mid-workflow — they're
user-invoked entry points, not subroutines. More importantly, cross-prompt
references violate the project's documented design convention that prompts must be
self-contained. Indirection is *less* robust to context compaction than literal
inline blocks.

## Decision

**Approach 1 — Full Stack — JSON Artifact + Prompt Hardening**, with all user
additions:

- Regression tests verifying literal blocks exist (closes the maintenance con)
- Two-phase implementation (Phase 1: script, Phase 2: prompts)
- Artifact's audit-trail purpose explicitly stated (subagent-only doesn't persist)
- Complete affected-files list including safety skill and Run-Tests.ps1 test coverage

### Why not Approach 2
Leaves 72% of crashes unaddressed. A half-measure.

### Why not Approach 3
Violates the self-contained prompt design convention. Indirection is less robust
to context loss than inline literal blocks.

## Next Steps

### Phase 1 (one session) — Run-Tests.ps1 upgrades
1. Add `-File` parameter with junction-ordering enforcement
2. Build JSON artifact from Pester 3.4 `-PassThru` results
   (`.Describe`, `.Context`, `.Name`, `.FailureMessage`)
3. Add `gitSha` via `git rev-parse --short HEAD`
4. Add `ranAt` timestamp
5. Implement atomic write-then-rename (`.last-run.tmp` → `last-run.json`)
6. Add `tests/last-run.json` and `tests/.last-run.tmp` to `.gitignore`
7. Add tests for `-File` parameter behavior
8. Commit and push before Phase 2

### Phase 2 (second session) — Prompt hardening
1. Add literal `execution_subagent` test blocks to `/cg-work` (Step 2.4)
2. Add literal `execution_subagent` test blocks to `/cg-fix-triage` (Step 3)
3. Add literal `execution_subagent` test blocks to `/cg-diagnose` (recovery)
4. Update `cg-fix-problems` agent with test execution block
5. Update `cg-skill-pester-safety/SKILL.md`: artifact workflow as THE pattern,
   old `$r = Invoke-Pester` demoted to debugging-only
6. Update `copilot-instructions.md` Pester Safety Rules section
7. Add `prompt-tools.Tests.ps1` tests verifying literal blocks in each prompt
8. Run full test suite, commit, push

### Artifact schema (agreed)

```json
{
  "gitSha": "d5d763e",
  "ranAt": "2026-04-17T10:00:00Z",
  "passed": true,
  "totalCount": 623,
  "passedCount": 621,
  "failedCount": 2,
  "files": [
    { "name": "prompt-tools", "total": 465, "passed": 464, "failed": 1 },
    { "name": "ps51-compat",  "total": 12,  "passed": 11,  "failed": 1 }
  ],
  "failures": [
    {
      "file": "prompt-tools",
      "describe": "cg-compound.prompt.md - context enrichment step ordering",
      "context": "",
      "name": "offers to create context.md if it does not exist",
      "message": "Expected: {True}"
    }
  ]
}
```

### Literal block template (for Phase 2)

````markdown
Run tests (do NOT use `Invoke-Pester` directly — always use `execution_subagent`):

> **Query**: "In the repo root, run `. tests\Run-Tests.ps1`
> (no flags, no pipeline). Then run `Get-Content tests\last-run.json |
> ConvertFrom-Json | Select-Object passed, failedCount, failures`.
> Return only those three fields."

If `passed` is `true`: continue to the next step.
If `passed` is `false`: read `failures` array and fix before continuing.
````
