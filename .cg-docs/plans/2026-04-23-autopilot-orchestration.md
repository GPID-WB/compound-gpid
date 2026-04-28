---
date: 2026-04-23
title: "Autopilot orchestration — prompt-first with hook safety net"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-04-23-autopilot-orchestration.md"
language: "both"
estimated-effort: "large"
tags: [autopilot, hooks, orchestration, automation, state-machine, subagent, architecture-research, powershell]
---

# Plan: Autopilot Orchestration — Prompt-First with Hook Safety Net

## Objective

Build `/cg-autopilot` — a fire-and-forget command that executes the full compound-gpid loop (work → review → fix-triage → verify → compound → commit → PR) autonomously, dispatching each phase as a fresh subagent. A lightweight `Stop` hook prevents premature termination. A persistent state file in `.cg-docs/autopilot-runs/` provides audit trail, resumability, and failure diagnostics.

## Context

The manual loop (`/cg-work` → `/cg-review` → `/cg-fix-triage P0` → `P1` → `P2` → `P3` → `/cg-review light` → `/cg-fix-triage` → `/cg-compound`) is the most painful friction point in daily compound-gpid use. The fix-triage stage depends on review findings, creating variable-length loops that require manual queueing of commands.

The brainstorm chose **Approach 3: Hybrid — Prompt-First with Hook Safety Net**:
- The prompt contains the orchestration logic (phase sequence, branching, retry budgets).
- Hooks act as safety nets: `Stop` hook blocks premature stopping, `PreCompact` saves state.
- Each phase runs via `runSubagent` for context isolation.
- State file is the single source of truth for resumability and debugging.
- Future evolution: Model C (Copilot CLI with worktrees) can replace Model B (in-session subagents) without changing the state file schema.

**Critical constraint** (from `.cg-docs/solutions/testing-patterns/2026-03-30-do-not-delegate-file-write-guardrail.md`): Subagent file writes persist only when done directly — not via sub-subagent delegation. Each phase subagent must write artifacts directly. The orchestrator must verify artifact existence after each phase.

## Requirements

| ID  | Requirement                                                                 | Source           |
|-----|-----------------------------------------------------------------------------|------------------|
| R1  | User invokes `@cg-autopilot` with a plan reference or auto-discovery       | brainstorm       |
| R2  | Full autopilot (default): no human intervention until completion or halt    | brainstorm       |
| R3  | Supervised mode (opt-in): pauses at checkpoints for user approval           | brainstorm       |
| R4  | Each phase dispatched via `runSubagent` for context isolation               | brainstorm       |
| R5  | Persistent audit trail in `.cg-docs/autopilot-runs/<timestamp>.json`        | brainstorm       |
| R6  | `Stop` hook blocks premature stopping when phases remain                    | brainstorm       |
| R7  | `PreCompact` hook saves state before context compaction                     | brainstorm       |
| R8  | P0 findings halt autopilot immediately regardless of mode                   | brainstorm       |
| R9  | Retry budgets: 2 attempts per finding, 3 max review cycles                 | brainstorm       |
| R10 | Plan discovery: same pattern as `/cg-work` Step 1 + user confirmation       | brainstorm       |
| R11 | Scope check at entry: warn if plan is too large for one run                 | brainstorm (CE)  |
| R12 | PR creation as final step                                                   | brainstorm       |
| R13 | Artifact verification after each phase (guard against silent subagent loss) | solution doc     |
| R14 | State file schema supports future Model C (CLI) without changes             | brainstorm       |
| R15 | Agent-scoped hooks: zero side effects on non-autopilot sessions             | brainstorm       |
| R16 | Resume from halted state via `@cg-autopilot --resume`                       | brainstorm       |
| R17 | Stale-run detection: orphaned `running` state files must not block future runs | plan-review P2.4 |
| R18 | `--reset` mode to abandon orphaned runs                                      | plan-review P2.4 |

## Implementation Steps

### Phase 0: Hook PoC Validation (Gate)

> **Added per plan review P1.1**: The brainstorm chose Approach 3 conditionally — pending PoC validation that hooks work in VS Code Copilot. This phase gates all subsequent work. If the PoC fails, fall back to Approach 2 (pure prompt orchestrator without hooks).

#### 0. Proof-of-Concept — Minimal Agent with Stop Hook

- **Requirements**: R6, R15 (validation only)
- **Files**:
  - Create `.github/agents/cg-hello-hook.agent.md` (temporary — deleted after PoC)
  - Create `.github/hooks/hello-hook-guard.ps1` (temporary)
- **Details**: Build a minimal throwaway agent to validate three critical assumptions:

  **Assumption 1**: Agent-scoped hooks in `.agent.md` frontmatter fire in VS Code Copilot (not just Copilot CLI).
  **Assumption 2**: The Stop hook receives `stop_hook_active` in its stdin JSON payload.
  **Assumption 3**: A response of `{ "hookSpecificOutput": { "decision": "block", ... } }` causes VS Code to block the stop (vs. Claude Code's top-level format).

  **PoC agent** (`cg-hello-hook.agent.md`):
  ```yaml
  ---
  description: "Temporary PoC — validates hook behavior. Delete after validation."
  model: Claude Sonnet 4.6 (copilot)
  user-invocable: true
  hooks:
    Stop:
      - type: command
        windows: "powershell -ExecutionPolicy Bypass -File .github\\hooks\\hello-hook-guard.ps1"
        command: "powershell -ExecutionPolicy Bypass -File .github/hooks/hello-hook-guard.ps1"
  ---
  # Hello Hook PoC
  Say "Hello! I will now try to stop. The hook should block me."
  Then attempt to stop.
  ```

  **PoC guard script** (`hello-hook-guard.ps1`):
  - Read stdin, log the full JSON payload to `.cg-docs/autopilot-runs/poc-hook-input.json` for inspection
  - If `stop_hook_active` is `false` or absent: output block response, log to `.cg-docs/autopilot-runs/poc-hook-output-block.json`
  - If `stop_hook_active` is `true`: output `{}` (allow stop), log to `.cg-docs/autopilot-runs/poc-hook-output-allow.json`

  **Validation criteria** (must ALL pass to proceed to Phase 1):
  1. Invoking `@cg-hello-hook` triggers the hook script (check log files exist)
  2. `poc-hook-input.json` contains `stop_hook_active` field
  3. Block response prevents the agent from stopping (agent continues after hook fires)
  4. On second stop attempt, `stop_hook_active: true` allows the stop

  **If PoC fails**: Document which assumptions failed. Fall back to Approach 2 (pure prompt orchestrator). Remove hook-related steps (2, 3) and hook frontmatter from Step 4. The state file schema (Step 1) and agent orchestration logic survive either approach.

- **Test Scenarios**:
  - ✅ Hook script fires and writes log files
  - ✅ stdin contains expected JSON structure
  - 🛑 Edge case: hook fires but response format differs from docs → document actual format
  - ❌ Error path: hook doesn't fire at all → Approach 2 fallback
- **Tests**: Manual validation (invoke agent, inspect log files). No Pester — this is a throwaway PoC.
- **Acceptance criteria**: All 4 validation criteria pass, or a documented decision to fall back to Approach 2
- **Cleanup**: Delete `cg-hello-hook.agent.md`, `hello-hook-guard.ps1`, and PoC log files after validation

### Phase 1: Foundation

> **Gate**: Phase 0 PoC must pass before starting Phase 1.

#### 1. State File Schema and Directory

- **Requirements**: R5, R14, R16
- **Files**:
  - Create `.cg-docs/autopilot-runs/.gitkeep`
  - Create `.github/skills/cg-skill-autopilot-schema/SKILL.md` — schema reference for the state file (consumed by agent and hook scripts)
- **Details**: Define the JSON schema for autopilot run state files. Schema must support:
  - Run metadata: plan path, mode, start time, status
  - Phase list with statuses, summaries, timestamps
  - Review cycle tracking (current cycle, max cycles)
  - Finding counts per review cycle
  - Retry tracking per fix-triage phase
  - Halt reason (if applicable)
  - Resume checkpoint

  **State file schema** (`.cg-docs/autopilot-runs/YYYY-MM-DDTHH-MM-<plan-slug>.json`):
  ```json
  {
    "schemaVersion": "autopilot-v1",
    "plan": ".cg-docs/plans/2026-04-23-my-feature.md",
    "mode": "full",
    "status": "running",
    "startedAt": "2026-04-23T14:30:00Z",
    "completedAt": null,
    "haltedAt": null,
    "haltReason": null,
    "currentPhase": 2,
    "reviewCycle": 1,
    "maxReviewCycles": 3,
    "phases": [
      {
        "id": 1,
        "type": "work",
        "status": "completed",
        "summary": "3 files created, 2 modified, tests pass",
        "startedAt": "2026-04-23T14:30:05Z",
        "completedAt": "2026-04-23T14:35:00Z",
        "artifacts": [".cg-docs/plans/2026-04-23-my-feature.md"],
        "retryCount": 0
      },
      {
        "id": 2,
        "type": "review",
        "status": "running",
        "summary": null,
        "startedAt": "2026-04-23T14:35:05Z",
        "completedAt": null,
        "artifacts": [],
        "reviewCycle": 1,
        "findings": { "P0": 0, "P1": 0, "P2": 0, "P3": 0 }
      }
    ]
  }
  ```
  The `status` field at top level uses: `running`, `completed`, `halted`, `failed`, `abandoned`.
  Phase `status` uses: `pending`, `running`, `completed`, `failed`, `skipped`.
  Phase `type` uses: `work`, `review`, `fix-triage`, `review-verify`, `compound`, `commit`, `pr`.

- **Test Scenarios**:
  - ✅ Happy path: state file created with valid schema, all fields populated
  - 🛑 Edge case: plan slug with special characters gets sanitized in filename
  - ❌ Error path: state file directory doesn't exist → created on first write
- **Tests**: Pester test validates schema structure, required fields, valid enum values
- **Acceptance criteria**: Schema documented in skill file; `.cg-docs/autopilot-runs/` directory exists with `.gitkeep`

#### 2. Hook Guard Script — `Stop` Hook

- **Requirements**: R6, R15
- **Files**:
  - Create `.github/hooks/autopilot-guard.ps1`
- **Details**: Lightweight PowerShell script (~30 lines) that reads the autopilot state file and decides whether to block the agent from stopping.

  **Logic**:
  1. Read JSON from stdin (hook input with `stop_hook_active`, `hookEventName`)
  2. Check `stop_hook_active` — if `true`, allow stop (prevent infinite loop)
  3. Scan `.cg-docs/autopilot-runs/` for any file with `"status": "running"`
  4. If found: output `{ "hookSpecificOutput": { "hookEventName": "Stop", "decision": "block", "reason": "Autopilot run in progress. Read .cg-docs/autopilot-runs/<filename> for current state and execute the next phase." } }`
  5. If not found (no running run, or all completed/halted): output `{}` (allow stop)

  **Stale-run detection (R17)**: Before blocking, check the `startedAt` timestamp of any `running` state file. If older than 4 hours, treat it as stale: update the state file's `status` to `abandoned` and `haltReason` to `"Stale run — abandoned after 4h timeout"`, then allow the stop. This prevents orphaned state files from permanently blocking all future autopilot runs.

  **Key constraint**: Script must exit in <2 seconds. No network calls. Pure file I/O.

  **Anti-recursion guard**: The `stop_hook_active` flag is critical. When the hook blocks a stop, the agent continues. When it tries to stop again, `stop_hook_active` will be `true` — the hook must allow the stop to prevent infinite loops. The orchestrator prompt must update the state file to `completed` or `halted` BEFORE allowing the final stop. The flow is:
  - Agent tries to stop → hook blocks (phases remain)
  - Agent runs next phase → tries to stop again → hook blocks
  - Agent finishes all phases → updates state to `completed` → tries to stop → hook sees no `running` state → allows stop
  - Safeguard: if `stop_hook_active` is `true` (agent was already nudged once this turn), always allow stop

- **Test Scenarios**:
  - ✅ Happy path: running state file → blocks stop with reason
  - ✅ Happy path: completed state file → allows stop (empty JSON)
  - ✅ Happy path: no state files → allows stop
  - 🛑 Edge case: `stop_hook_active: true` → always allows stop (anti-recursion)
  - 🛑 Edge case: malformed JSON in state file → allows stop (fail-open)
  - 🛑 Edge case: stale `running` state file (`startedAt` > 4 hours ago) → allows stop, marks file as `abandoned`
  - ❌ Error path: state file directory doesn't exist → allows stop
- **Tests**: Pester tests in `tests/autopilot.Tests.ps1` (created alongside — TDD). Pipe mock stdin JSON to the script and verify stdout JSON. Test all seven scenarios above.
- **Acceptance criteria**: Script correctly blocks/allows stop based on state file; never causes infinite loop; completes in <2 seconds; stale runs don't permanently block

#### 3. Hook Guard Script — `PreCompact` Hook

- **Requirements**: R7
- **Files**:
  - Create `.github/hooks/autopilot-precompact.ps1`
- **Details**: Saves current orchestration state before context compaction. When the agent's context is compacted, it may lose track of where it is in the autopilot sequence. This script ensures the state file is up-to-date.

  **Logic**:
  1. Read JSON from stdin (hook input)
  2. Scan `.cg-docs/autopilot-runs/` for any file with `"status": "running"`
  3. If found: add/update a `lastCompactedAt` timestamp field in the state file
  4. Output `{ "systemMessage": "Autopilot state saved before compaction. Read .cg-docs/autopilot-runs/<filename> to resume." }`
  5. If not found: output `{}` (no-op)

- **Test Scenarios**:
  - ✅ Happy path: running state file → timestamp updated, system message returned
  - ✅ Happy path: no running state → no-op
  - 🛑 Edge case: state file is read-only → fail silently, still return message
- **Tests**: Pester tests in `tests/autopilot.Tests.ps1` (same file as Stop hook tests — TDD alongside script). Verify timestamp update and JSON output.
- **Acceptance criteria**: State file gets `lastCompactedAt` timestamp; system message tells agent where to find state

### Phase 2: Agent and Prompt

#### 4. Orchestrator Agent — `cg-autopilot.agent.md`

- **Requirements**: R1, R2, R3, R4, R6, R7, R8, R9, R10, R11, R13, R15, R16
- **Files**:
  - Create `.github/agents/cg-autopilot.agent.md`
- **Details**: The primary artifact. Agent file with:
  - YAML frontmatter: `description`, `model: Claude Sonnet 4.6 (copilot)`, `user-invocable: true`, `tools`, `hooks` (agent-scoped Stop and PreCompact hooks)
  - Full orchestration instructions in the body

  **Frontmatter** (agent-scoped — hooks only fire when `@cg-autopilot` is active):
  ```yaml
  description: "Run the full compound-gpid loop autonomously."
  model: Claude Sonnet 4.6 (copilot)
  user-invocable: true
  tools:
    - read
    - search
    - editFiles
    - runInTerminal
    - get_errors
  hooks:
    Stop:
      - type: command
        windows: "powershell -ExecutionPolicy Bypass -File .github\\hooks\\autopilot-guard.ps1"
        command: "powershell -ExecutionPolicy Bypass -File .github/hooks/autopilot-guard.ps1"
    PreCompact:
      - type: command
        windows: "powershell -ExecutionPolicy Bypass -File .github\\hooks\\autopilot-precompact.ps1"
        command: "powershell -ExecutionPolicy Bypass -File .github/hooks/autopilot-precompact.ps1"
  ```

  > **Note (P2.3)**: The `tools:` key is required — without it, the agent cannot execute git commands in the commit phase or run tests during the work phase. The `runInTerminal` tool enables shell access for `git add`/`git commit`. Verify during Phase 0 PoC that agent-scoped `tools:` restricts to only the listed tools.

  **Agent body — orchestration logic**:

  **Step 0: Get Bearings** — Standard compound-gpid Step 0 (read charter, local config, context).

  **Step 1: Plan Discovery and Argument Parsing** — Same as `/cg-work` Step 1:
  - Find most recent plan in `.cg-docs/plans/` or ask user.
  - Read plan. Confirm with user.
  - Parse arguments: `--resume` (resume last run), `--reset` (abandon orphaned runs), `--supervised` (supervised mode), bare invocation = full autopilot.
  - If `--reset`: scan `.cg-docs/autopilot-runs/` for any state file with `"status": "running"`. Update each to `"status": "abandoned"`, `"haltReason": "Manual reset via --reset"`. Report count and exit. Do not proceed to plan discovery.

  **Step 1.5: Scope Check** — Count implementation steps in the plan.
  - If >10 steps: warn "This plan has N steps — may exceed a single autopilot run. Proceed anyway?"
  - Read the plan's `scope:` — if `Deep`, suggest splitting into sub-plans.

  **Step 2: Initialize Run** — Create state file in `.cg-docs/autopilot-runs/`:
  - Filename: `YYYY-MM-DDTHH-MM-<plan-slug>.json`
  - Populate with plan reference, mode, initial phase list.

  **Step 2a: Resume Mode (R16)** — If `--resume`:
  - Scan `.cg-docs/autopilot-runs/` for most recent `halted` or `failed` state file.
  - If none found: report "No halted or failed runs found. Start a new run instead." and exit.
  - If found: read the state file. Present to user:
    > "Found halted run: `<filename>` — halted at phase <N> (<type>). Reason: <haltReason>. Resume from this point?"
  - On confirmation: set `status` back to `running`. Skip all phases with `status: completed`. Re-enter at the first phase with `status: failed` or `pending`.
  - If the halted phase was `failed`: reset its `status` to `pending` and increment `retryCount`.
  - If `retryCount` exceeds budget (2): warn "This phase has already been retried <N> times. Proceed anyway?".

  **Step 3: Execute Phases** — The core loop. For each phase:

  **3a. Work Phase**:
  - Dispatch `runSubagent` with prompt: "You are implementing a plan. [plan content]. Follow these conventions: [project conventions from charter]. Write code, run tests, commit checkpoints. Write artifacts directly — do NOT delegate file writes to sub-subagents. After completing all steps, report: files created/modified, test results, any failing steps."
  - Update state file: phase status, summary from subagent.
  - **Artifact verification**: Check that code files were actually modified (use `get_changed_files` or `git diff --name-only`).
  - If subagent reports test failures after retries → update state to `halted`, halt reason = "Work phase: tests failing after retries".

  **3b. Review Phase**:
  - **Pre-specify artifact path**: Before dispatching, compute the review file path: `.cg-docs/reviews/<plan-slug>-cycle<N>-review.md` (e.g., `.cg-docs/reviews/autopilot-orchestration-cycle1-review.md`).
  - Dispatch `runSubagent` with prompt: "You are running a code review. Review the files changed in this work session. Use review depth: [light for verify passes, standard for first pass]. Write the review report to `<pre-specified path>` — write the file directly, do NOT delegate. Report back: finding counts by priority (P0, P1, P2, P3)."
  - **Artifact verification**: Check that review file exists at the pre-specified path (not a subagent-reported path).
  - Update state file with finding counts and the review file path in `artifacts`.
  - **P0 gate (R8)**: If P0 findings > 0 → halt immediately. Update state: `halted`, reason = "P0 findings detected — manual review required". Present P0 findings to user.

  **3c. Fix-Triage Phase** (runs once per priority tier with findings):
  - Determine which priority tiers have open findings (P1 first, then P2, then P3).
  - For each tier: dispatch `runSubagent` with prompt: "You are applying fixes from a review report at `<pre-specified review path>`. Fix all P[N] findings. Update the review file's findings: frontmatter. Write changes directly — do NOT delegate. Report: findings fixed, findings remaining, files modified."
  - **Artifact verification**: Re-read review file at pre-specified path, confirm `findings:` map updated.
  - Track retry count per tier. If a tier still has open findings after 2 attempts → mark as unresolvable, continue to next tier.

  **3d. Review-Verify Phase**:
  - **Pre-specify artifact path**: `.cg-docs/reviews/<plan-slug>-cycle<N>-verify.md`.
  - Dispatch `runSubagent` with prompt: "You are running a verification review (mode:verify). The prior review is at `<pre-specified review path>`. Check if fixed findings are truly resolved and look for new issues introduced by fixes. Write verify review to `<pre-specified verify path>` — write directly. Report: new finding counts, whether all prior findings are resolved."
  - **Artifact verification**: Check that verify review file exists at the pre-specified path.
  - If new findings found → loop back to 3c (increment review cycle counter).
  - If review cycle >= `maxReviewCycles` (3) → halt: "Review non-convergence after N cycles."
  - If clean → proceed to 3e.

  **3e. Compound Phase**:
  - **Pre-specify artifact path**: `.cg-docs/solutions/<category>/<date>-<plan-slug>.md` (category inferred from plan tags).
  - Dispatch `runSubagent` with prompt: "You are capturing lessons learned. The plan is at `<path>`. The review reports are at `<pre-specified review paths>`. Capture the key solution to `<pre-specified solution path>`. Write the file directly. Report: category, tags."
  - **Artifact verification**: Check solution file exists at the pre-specified path.

  **3f. Commit Phase**:
  - The orchestrator creates a conventional commit directly using `runInTerminal` (declared in `tools:`).
  - Use `git add -A` then `git commit -m "feat(<scope>): <title from plan>"`.
  - Note: This phase intentionally runs in the orchestrator (not a subagent) because git operations are simpler and more reliable without context isolation overhead.

  **3g. PR Phase (R12)**:
  - Dispatch `github-pull-request_create_pull_request` tool (if available).
  - If tool not available: suggest manual PR creation with a prepared description.

  **Step 4: Finalize** — Update state file to `completed`. Present summary:
  ```
  ## Autopilot Complete
  
  Plan: <plan title>
  Mode: full | supervised
  Phases: N completed, M skipped
  Review cycles: N
  Findings: X found, Y fixed, Z unresolvable
  Commit: <commit hash>
  PR: <PR URL or "manual">
  Run log: .cg-docs/autopilot-runs/<filename>
  ```

  **Supervised mode additions**: If `--supervised`, after each of these phases, present results and ask "Continue? [yes/halt]": review (show finding counts), fix-triage (show remaining findings), compound (show captured solution).

  **Self-monitoring (R5)**: After every 4 phases, check accumulated message count. If the agent has >30 messages in context, write `systemMessage`: "Context getting heavy. State saved to <file>. If compaction occurs, resume by reading the state file."

- **Test Scenarios**:
  - ✅ Happy path: plan with 3 steps → work → review (0 findings) → compound → commit → PR
  - ✅ Happy path: plan → work → review (P1, P2 findings) → fix-triage P1 → fix-triage P2 → review-verify (clean) → compound → commit → PR
  - 🛑 Edge case: P0 finding → immediate halt
  - 🛑 Edge case: review non-convergence (3 cycles) → halt
  - 🛑 Edge case: fix-triage exhausts retry budget → continues with remaining findings noted
  - 🛑 Edge case: `--resume` with halted state file → picks up at correct phase
  - 🛑 Edge case: `--resume` with no halted/failed runs → reports "no runs to resume" and exits
  - 🛑 Edge case: `--resume` on a phase that already exhausted retry budget → warns before proceeding
  - 🛑 Edge case: `--reset` with orphaned running state files → marks all as abandoned and exits
  - 🛑 Edge case: work subagent reports no files changed → halt (empty work)
  - ❌ Error path: subagent returns but artifact not found on disk → retry once, then halt
  - ❌ Error path: `--supervised` + user says "halt" → graceful halt, state saved
- **Tests**: Pester tests for: agent file structure (frontmatter hooks present, model correct, user-invocable true), phase type enums valid, "Do NOT delegate" guardrail present in all subagent prompts
- **Acceptance criteria**: Agent file parses cleanly; hooks reference correct scripts; all subagent dispatch prompts include file-write guardrail; both modes documented

#### 5. Convenience Prompt — `cg-autopilot.prompt.md`

- **Requirements**: R1
- **Files**:
  - Create `.github/prompts/cg-autopilot.prompt.md`
- **Details**: Thin prompt that directs users to invoke `@cg-autopilot`:

  ```markdown
  ---
  description: "Run the full compound-gpid loop autonomously: work → review → fix-triage → compound → commit → PR."
  ---
  
  # Autopilot
  
  > This prompt is a convenience entry point. The autopilot logic lives in
  > `@cg-autopilot` (the agent). Invoke it directly for full functionality
  > including hook-based safety nets.
  >
  > Usage:
  > - `@cg-autopilot` — Full autopilot (default)
  > - `@cg-autopilot --supervised` — Pause at checkpoints
  > - `@cg-autopilot --resume` — Resume a halted run
  > - `@cg-autopilot --reset` — Abandon orphaned runs
  
  Invoke `@cg-autopilot` with the user's request. Pass through any arguments.
  ```

- **Test Scenarios**:
  - ✅ Happy path: prompt file parses with valid frontmatter
- **Tests**: Pester test validates frontmatter structure
- **Acceptance criteria**: Prompt exists and references agent correctly

### Phase 3: Integration and Hardening

#### 6. Update `copilot-instructions.md` — Workflow Entry Points Table

- **Requirements**: R1
- **Files**:
  - Modify `.github/copilot-instructions.md`
- **Details**: Add `/cg-autopilot` (or `@cg-autopilot`) to the Workflow Entry Points table:

  | Situation | Command |
  |---|---|
  | Run full loop autonomously | `@cg-autopilot` |

- **Test Scenarios**:
  - ✅ Existing Pester tests validate workflow entry points table structure
- **Tests**: Existing `prompt-tools.Tests.ps1` should catch if the table is malformed
- **Acceptance criteria**: Entry appears in the table

#### 7. Update `reference.md` — Command Reference

- **Requirements**: R1, R2, R3, R16
- **Files**:
  - Modify `docs/reference.md`
- **Details**: Add `@cg-autopilot` section documenting:
  - Purpose and when to use
  - Arguments: `--supervised`, `--resume`
  - Phase sequence diagram
  - State file location
  - Failure modes and halt conditions
  - Retry budgets

- **Test Scenarios**:
  - ✅ Section exists with correct heading level
- **Tests**: Manual review (documentation)
- **Acceptance criteria**: `@cg-autopilot` documented in reference.md with all arguments and failure modes

#### 8. Pester Tests — Agent Structural Tests

- **Requirements**: R1, R2, R3, R4, R6, R7, R15
- **Files**:
  - Extend `tests/autopilot.Tests.ps1` (created in Phase 1 alongside hook scripts)
- **Details**: Add agent file structural tests to the existing test file:

  **Agent file structural tests** (added to `tests/autopilot.Tests.ps1`):
  - `cg-autopilot.agent.md` has `hooks:` in frontmatter
  - `hooks.Stop` references `autopilot-guard.ps1`
  - `hooks.PreCompact` references `autopilot-precompact.ps1`
  - `model:` is `Claude Sonnet 4.6 (copilot)`
  - `user-invocable:` is `true`
  - `tools:` includes `runInTerminal` (for commit phase)
  - Body contains "Do NOT delegate" in all subagent dispatch instructions
  - Body contains all phase types: work, review, fix-triage, review-verify, compound, commit, pr
  - Body contains `--resume` documentation
  - Body contains `--reset` documentation
  - All artifact paths are orchestrator-specified (no "Report back: ... file path" patterns)

  > **Note (P3.1)**: Hook script Pester tests are written in Phase 1 alongside the scripts (TDD). This step only adds agent structural tests.

- **Test Scenarios**:
  - ✅ All structural assertions pass
- **Tests**: Pester file `tests/autopilot.Tests.ps1` (extended)
- **Acceptance criteria**: All structural tests pass

#### 9. Update Roadmap

- **Requirements**: (roadmap hygiene)
- **Files**:
  - Modify `roadmap.json` via `@cg-roadmap`
- **Details**: Link this plan to `autonomous-pipeline-autopilot` and set status to `planned`. Do **NOT** mark `evaluate-copilot-hooks` as `done` yet — that depends on Phase 0 PoC passing (per plan review P2.1). Mark `evaluate-copilot-hooks` as `in-progress` to reflect the PoC work. It gets closed to `done` only after Phase 0 validation criteria pass.
- **Acceptance criteria**: `autonomous-pipeline-autopilot` linked and set to `planned`; `evaluate-copilot-hooks` set to `in-progress` (not `done`)

## Testing Strategy

- **Phase 0 PoC**: Manual validation — invoke `@cg-hello-hook`, inspect log files. No Pester.
- **Hook scripts (Phase 1, TDD)**: Isolated Pester tests written alongside scripts in `tests/autopilot.Tests.ps1`. Mock stdin/state files. No network, no git. Includes stale-run detection tests.
- **Agent structural tests (Phase 3)**: Pester tests added to `tests/autopilot.Tests.ps1` that parse the agent `.md` file and validate frontmatter YAML, hook references, `tools:` key, and body content (phase types, guardrails, `--resume`/`--reset` docs).
- **State file schema**: Pester tests that validate JSON schema invariants (required fields, valid enums including `abandoned`).
- **Integration testing**: Manual end-to-end test — invoke `@cg-autopilot` on a small plan, verify all phases execute and state file is populated. Document the test procedure in the agent body as a "smoke test" section.
- **Safety**: All Pester tests via `execution_subagent` pattern per project rules.

## Documentation Checklist

- [ ] Agent file has comprehensive body documentation (phases, modes, failure handling)
- [ ] `docs/reference.md` updated with `@cg-autopilot` section
- [ ] `.github/copilot-instructions.md` workflow entry points table updated
- [ ] State file schema documented in skill file
- [ ] Hook scripts have inline comments explaining logic
- [ ] Phase 0 PoC results documented (which assumptions passed/failed)
- [ ] `--resume` and `--reset` documented in agent body and reference.md
- [ ] Stale-run detection threshold (4h) documented in hook script and reference.md
- [ ] Troubleshooting section added to `docs/troubleshooting.md` for common autopilot issues (including orphaned state file recovery)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hooks API changes (Preview) | Medium | Medium | Guard script is ~30 lines — easy to update. Phase 0 PoC validates current API before full implementation. Fallback to Approach 2 if hooks don't work. |
| Subagent loses file writes | Low | High | Every subagent prompt includes "Do NOT delegate" guardrail. Orchestrator verifies artifacts after each phase. |
| `Stop` hook infinite loop | Low | High | `stop_hook_active` flag checked first. State file update to `completed` before final stop. Stale-run detection (4h timeout) prevents permanent blocking. Pester tests cover anti-recursion. |
| Review non-convergence | Medium | Low | Hard cap at 3 review cycles. After cap, halt with detailed report — user reviews manually. |
| Context overflow despite subagent isolation | Low | Medium | Self-monitoring after every 4 phases. `PreCompact` hook saves state. Resume capability (`--resume`). Reset capability (`--reset`) for orphaned runs. |
| Phase subagent misinterprets instructions | Medium | Medium | Subagent prompts are specific and structured (not copies of full prompts). Artifact verification catches failures. |
| PR creation tool unavailable | Low | Low | Graceful fallback: suggest manual PR with prepared description. |

## Out of Scope

- **Copilot CLI execution (Model C)** — future evolution, tracked as separate roadmap feature
- **Multi-plan orchestration** — one plan per autopilot run
- **Automatic branching** — user must be on the correct branch before invoking
- **Hook-based triggering** — autopilot is explicitly invoked, not auto-triggered
- **Parallel phase execution** — phases are sequential (Copilot subagents don't support true parallelism)
- **Automatic plan selection** — user must confirm which plan to execute
- **Token cost tracking** — Copilot doesn't expose token counts to prompts
