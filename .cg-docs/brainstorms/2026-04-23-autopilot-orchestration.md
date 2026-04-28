---
date: 2026-04-23
title: "Autopilot orchestration for compound-gpid workflow loop"
status: decided
scope: "Deep"
chosen-approach: "Hybrid — Prompt-First with Hook Safety Net"
tags: [autopilot, hooks, orchestration, automation, state-machine, subagent, architecture-research]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Autopilot Orchestration for Compound-GPID Workflow Loop

## Context

The compound-gpid workflow loop (`/cg-work` → `/cg-review` → `/cg-fix-triage` → `/cg-compound`) requires manual user invocation at every step. The fix-triage stage depends on review findings, creating variable-length loops. Users must queue commands manually and manage context window exhaustion across phases. This is the most painful friction point in daily use.

The Architecture Research milestone already identified `evaluate-copilot-hooks`, `adding-hooks-to-streamline-process`, and `autonomous-pipeline-autopilot` as idea-stage features. This brainstorm converges them into a concrete design.

## Requirements

1. **Full autopilot as default**: User invokes `/cg-autopilot`, points it at a plan, and walks away. The system executes work → review → fix-triage loops → compound → commit → PR without human intervention.
2. **Supervised mode as opt-in**: User can choose supervised mode where the orchestrator pauses at key checkpoints (after review findings, before compounding) for approval.
3. **Context isolation**: Each phase runs in a fresh context via `runSubagent`. The orchestrator stays thin — it only tracks phase status and subagent summaries.
4. **Persistent audit trail**: Every run is logged to `.cg-docs/autopilot-runs/<timestamp>.json` with phase-by-phase results, summaries, and halt reasons.
5. **Self-monitoring compaction**: The orchestrator tracks its own context usage. When nearing limits, it saves state to the run file and asks for `/compact`. State file enables clean resume.
6. **P0 findings always halt**: Security vulnerabilities, PII exposure, silent data corruption, and incorrect statistical results stop the autopilot immediately regardless of mode.
7. **Retry budgets**: 2 attempts per finding in fix-triage, 3 max review cycles before halting with a status report.
8. **Plan discovery**: Same mechanism as `/cg-work` — discover available plans and confirm with the user before starting.
9. **Scope check at entry**: If the plan contains more tasks than fit in one session, warn before starting (inspired by CE's reject-plan-re-scoping pattern).
10. **PR creation at exit**: Final step after compound creates a PR (or updates an existing one).
11. **All compound-gpid users**: Designed for the whole user base, not just power users.
12. **Future evolution to Copilot CLI**: Design the state file contract and phase handoff so that Model C (CLI-based multi-session execution with worktrees) can replace Model B (in-session subagents) without changing the state format or audit trail.

## Approaches Considered

### Approach 1: Hook-Driven Orchestrator Agent

A custom agent `@cg-autopilot` with agent-scoped hooks that drive a state machine. Each phase dispatches to `runSubagent`. A `Stop` hook keeps the agent running until all phases complete. A PowerShell script manages the state file.

**Architecture:**
```
.github/agents/cg-autopilot.agent.md     ← orchestrator agent with hooks in frontmatter
.github/hooks/autopilot-orchestrator.ps1  ← state machine logic (reads/writes state file)
.github/prompts/cg-autopilot.prompt.md    ← user-facing prompt that invokes the agent
.cg-docs/autopilot-runs/                  ← persistent audit trail (one file per run)
```

**Hook usage:**
- `Stop` hook: Reads state file → blocks stopping if phases remain → tells agent what to do next. Checks `stop_hook_active` to prevent infinite loops.
- `PreCompact` hook: Saves orchestrator state before context compaction.
- `SubagentStop` hook: Logs each subagent phase result to the run file.
- `SessionStart` hook: On resume, injects last run state as context.
- All hooks are agent-scoped (defined in `cg-autopilot.agent.md` frontmatter) — zero side effects on normal workflows.

**Phase flow:**
1. User runs `/cg-autopilot` → discovers plan, confirms, selects mode (full/supervised)
2. Creates `.cg-docs/autopilot-runs/<timestamp>.json` with phase plan
3. Dispatches `work` phase via `runSubagent` → subagent reads plan, implements, runs tests
4. Dispatches `review` phase via `runSubagent` → subagent reviews code, writes findings file
5. Reads review summary → if findings exist, dispatches `fix-triage` per priority tier
6. After fix-triage, dispatches `review verify` → checks if findings are resolved
7. If unresolved findings remain and retry budget allows, loops back to step 5
8. Dispatches `compound` phase → captures solution
9. Commits changes
10. Creates PR

**Failure modes:**
- Work fails (tests don't pass after retries) → halt, write status report
- P0 findings in review → immediate halt regardless of mode
- Fix-triage can't resolve after 2 attempts → halt, write status report
- Review loop doesn't converge after 3 cycles → halt, write status report
- VS Code closes mid-run → state file on disk, user resumes via `/cg-autopilot --resume`

**Pros:**
- Uses the platform's native mechanism — hooks are designed for this
- Agent-scoped hooks mean zero side effects on normal workflows
- State file is single source of truth — resumable, debuggable, auditable
- Each phase gets fresh context via `runSubagent`
- `PreCompact` hook preserves state if context is compacted
- Incorporates GSD-2 verification commands pattern and CE scope check

**Cons:**
- Hooks API is Preview — format may change (accepted risk)
- PowerShell hook script is complex (~100+ lines of state machine logic)
- Orchestration logic split between hook (determines next phase) and prompt (dispatches it) — debugging requires tracing both layers
- `Stop` hook + `stop_hook_active` needs careful testing
- Subagent context injection needs precise calibration

**Effort:** Large

**Not chosen** — the hook cannot invoke `runSubagent` or execute prompts; it only returns a `reason` string. So the agent still interprets and dispatches. This means the hook doesn't truly drive execution — it drives continuation. Putting full state machine logic in the hook adds complexity without eliminating the agent's role in orchestration.

### Approach 2: Pure Prompt Orchestrator (No Hooks)

A `/cg-autopilot` prompt that instructs the agent to run all phases sequentially using `runSubagent`, with the agent tracking state in the run file. No hooks.

**Pros:**
- Simpler — no hooks, no PowerShell script
- No dependency on Preview API
- Easier to test and iterate on

**Cons:**
- No safety net — agent can stop early
- Context accumulates in orchestrator without compaction awareness
- No `PreCompact` state preservation
- Less reliable for fire-and-forget
- Can't self-monitor context usage

**Effort:** Medium

**Not chosen** because it's too fragile for the fully unsupervised objective.

### Approach 3: Hybrid — Prompt-First with Hook Safety Net (CHOSEN)

The prompt contains the orchestration logic (phase sequence, branching, retry budgets). The agent follows prompt instructions to dispatch each phase via `runSubagent` and track state. Lightweight hooks act as safety nets: `Stop` hook blocks premature stopping, `PreCompact` saves state before compaction.

**Architecture:**
```
.github/agents/cg-autopilot.agent.md     ← orchestrator agent with safety-net hooks in frontmatter
.github/hooks/autopilot-guard.ps1         ← lightweight guard (~20 lines: "is run complete? block or allow")
.github/prompts/cg-autopilot.prompt.md    ← user-facing prompt with full orchestration logic
.cg-docs/autopilot-runs/                  ← persistent audit trail (one file per run)
```

**Division of responsibility:**
- **Prompt**: Owns the workflow — phase sequence, branching (fix-triage per priority tier), retry budgets, mode selection (full/supervised), subagent dispatch, state file updates.
- **`Stop` hook**: Safety net only — reads state file, blocks stopping if `status != completed`, tells agent "read your state file for next steps." ~20 lines of PowerShell.
- **`PreCompact` hook**: Saves current phase and progress to state file before context compaction.
- **`SessionStart` hook**: On resume, injects last run state as `additionalContext`.
- All hooks agent-scoped (in `cg-autopilot.agent.md` frontmatter) — zero side effects on normal workflows.

**Phase flow:** Same as Approach 1 (work → review → fix-triage loop → verify → compound → commit → PR), but driven by prompt instructions rather than hook-determined phase transitions.

**Failure modes:** Same as Approach 1 (P0 halt, retry budgets, non-convergence halt, resume from state file).

**Compaction resilience:** If context is compacted and the agent loses track, the `Stop` hook catches premature stopping and directs the agent to read the state file. Same outcome as Approach 1, triggered reactively rather than proactively.

**Pros:**
- Single source of truth for orchestration logic (the prompt)
- Hook script is trivially simple — less breakage when Preview API evolves
- Incrementally buildable — prompt works alone for supervised mode (Approach 2), hooks add full autopilot reliability
- Easier to debug — orchestration logic is in the prompt (visible in conversation), hook is a simple boolean gate
- Agent can adapt to unexpected situations (e.g., unusual review output) rather than rigidly following hook-determined transitions
- Same state file contract as Approach 1 — future Model C evolution is unchanged

**Cons:**
- Prompt logic is non-deterministic (LLM may misinterpret phase transitions) — mitigated by `Stop` hook catching errors
- Still depends on Preview hooks API for the safety net
- After compaction, agent relies on state file + hook nudge to resume — slightly less proactive than Approach 1

**Effort:** Large (but buildable in phases: prompt-only first, hooks second)

## Decision

**Approach 3: Hybrid — Prompt-First with Hook Safety Net** — chosen after reconsidering the division of responsibility between hooks and prompts.

The key insight: hooks can block stopping and provide a `reason` string, but they cannot invoke `runSubagent` or execute prompts. The agent always drives execution. In Approach 1, orchestration logic was split across two layers (hook determines next phase, agent dispatches it) — adding complexity without eliminating the agent's role. In Approach 3, the prompt owns the orchestration logic (single source of truth), and hooks are lightweight safety nets (~20 lines) that catch premature stopping and preserve state on compaction.

This architecture is:
- **More maintainable**: One place to update when the workflow changes (the prompt), not two.
- **More resilient to API changes**: The hook is trivially simple — less surface area exposed to Preview API evolution.
- **Incrementally buildable**: Prompt-only version works for supervised mode today. Hooks upgrade it to reliable full autopilot.
- **Equally future-proof**: Same state file contract — Model C (Copilot CLI) evolution is unchanged.

Approach 1 would be the better choice if the workflow became significantly more complex (many branch points, conditional phase skipping, parallel tracks), but the current workflow is a mostly linear sequence with one conditional loop — well within what a prompt can handle reliably.

Key design influences from competitive reviews:
- **GSD-2**: Verification commands pattern (configurable post-phase checks with retry budgets), decisions register pattern (append-only audit trail), scope check at entry
- **Superpowers**: Verification-before-completion (verify subagent claims before advancing), inline self-review (quick checks within phases)
- **Compound Engineering**: HITL review-loop (supervised mode), reject plan re-scoping (scope check), per-finding judgment loop (fine-grained triage)

## Next Steps

1. **Research spike**: Build a minimal proof-of-concept with agent-scoped `Stop` hook + `stop_hook_active` interaction, and `PreCompact` state preservation. Verify that the hook can reliably catch premature agent stopping.
2. **Design state file schema**: Define `.cg-docs/autopilot-runs/` JSON schema — phases, statuses, summaries, retry counts, halt reasons.
3. **Implement prompt orchestrator**: `cg-autopilot.prompt.md` with full phase sequence, branching logic, retry budgets, and mode selection. This is the primary deliverable.
4. **Implement orchestrator agent**: `cg-autopilot.agent.md` with agent-scoped safety-net hooks.
5. **Implement guard script**: `autopilot-guard.ps1` — lightweight "is run complete?" check (~20 lines of PowerShell).
6. **Implement phase dispatchers**: Each phase (work, review, fix-triage, compound, commit, PR) as a `runSubagent` call with precise context injection.
7. **Test failure modes**: P0 halt, retry budget exhaustion, review non-convergence, mid-run interruption and resume.
8. **Add to roadmap**: Update `autonomous-pipeline-autopilot` from idea to planned, link plan.
