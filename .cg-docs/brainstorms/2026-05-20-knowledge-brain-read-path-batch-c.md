---
date: 2026-05-20
title: "Knowledge Brain Read Path — Batch C Design"
status: decided
scope: "Standard"
chosen-approach: "Skill with full protocol + short prompt directives"
tags: [brain, read-path, prompt-integration, skill, brain-query, knowledge-brain]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Knowledge Brain Read Path — Batch C Design

## Context

Batches A and B of the Knowledge Brain strategy are complete: the engine
(`scripts/brain/`) indexes all `.cg-docs/` artifacts into BRAIN.md with topics,
relationships, and a chronological log, and the triggers (`/cg-brain-rebuild` +
auto-rebuild on `/cg-compound`) keep it current. However, no prompt currently
*reads* the brain — the 400-entity knowledge base is produced but never
consumed. Batch C wires the read path: making agents consult the brain before
acting, so accumulated institutional knowledge flows into every session.

Two features per the strategy:
1. `brain-prompt-integration` — add a "Consult Brain" step to 6 major prompts
2. `brain-query-skill` — create `cg-skill-brain-query` teaching agents how to
   search the brain efficiently

## Requirements

### Functional

1. **Brain consultation in 6 prompts**: `/cg-brainstorm`, `/cg-plan`,
   `/cg-work`, `/cg-review`, `/cg-fix-triage`, `/cg-compound` each gain a
   "Consult Brain" step that searches for relevant takeaways and gotchas.

2. **Intelligent filtering**: The agent searches for relevant entries, evaluates
   whether they are logically sound and useful for the current problem, adapts
   useful ones to the specific task, prioritizes by relevance, resolves
   contradictions, and discards outdated entries. Not blind application.

3. **Per-prompt search directives**: Each prompt specifies *what* to search for
   (its unique search scope); the skill teaches *how* to search.

4. **Placement after task context**: The brain consultation step is placed
   *after* the task context is established in each prompt (not a fixed Step 0
   sub-step), because precise searches require knowing the task:
   - `/cg-brainstorm`: after user's request is received (early — user states topic)
   - `/cg-plan`: after user's request/brainstorm reference is known (early)
   - `/cg-work`: after Step 1 loads the plan
   - `/cg-review`: after Step 1 identifies changed files
   - `/cg-fix-triage`: after Step 1 loads the review report
   - `/cg-compound`: after user describes the solution (early)

5. **`--no-brain` bypass flag**: All 6 prompts accept `--no-brain` to skip
   brain consultation entirely. When passed, the step is skipped silently.

6. **Always attempt search**: No auto-skip heuristics. The agent always
   attempts the brain search unless `--no-brain` is passed or BRAIN.md does
   not exist (hard technical constraint).

7. **Graceful absence**: If `.cg-docs/BRAIN.md` does not exist, skip silently
   (project hasn't run `cg-brain-rebuild` yet). No warning, no error.

8. **Skill protocol**: `cg-skill-brain-query` covers:
   - Navigation: scan BRAIN.md topic index → identify relevant topic(s)
   - Drill-down: open the linked BRAIN-NN.md sub-file for matched topics
   - Extraction: pull out takeaways, gotchas, patterns, and edge cases
   - Evaluation: assess relevance and logical soundness for current task
   - Prioritization: rank findings by relevance to the specific problem
   - Contradiction resolution: when entries conflict, resolve based on recency,
     specificity, and logical consistency
   - Staleness detection: identify outdated entries and discard them
   - Citation: reference source artifacts so the user can verify
   - No-match reporting: state "No relevant brain entries found" when empty

### Non-functional

- Each prompt's brain step is 4-6 lines (lean directive + skill reference)
- Skill file is self-contained (~150-200 lines)
- No changes to the brain engine (`scripts/brain/`) or its output format
- No cross-project brain consultation (Batch D territory)
- Read-only: the skill never writes to brain artifacts

### Architecture: Skill owns "how", prompts own "what"

The skill (`cg-skill-brain-query`) encapsulates:
- **Navigation mechanics**: how to traverse BRAIN.md → sub-files
- **Evaluation protocol**: prioritize, resolve contradictions, detect staleness
- **Output format**: how to present findings to the agent's context

Each prompt provides:
- **Search directive**: a one-sentence description of what to look for
- **Placement**: which step the consultation occurs in
- **Flag parsing**: `--no-brain` check before the consultation step

## Approaches Considered

### Approach 1: Skill with full protocol + short prompt directives (CHOSEN)

The skill contains the complete protocol — navigation, extraction, evaluation,
contradiction resolution, staleness detection, and citation format. Each prompt
adds a short step (4-6 lines) with a flag check + search directive + "Load
`cg-skill-brain-query` and follow its protocol."

**Pros**: Prompts stay lean; evaluation logic defined once; easy to evolve;
matches existing skill pattern.
**Cons**: Skill file moderately large (~150-200 lines); agent must load it
every time (context cost); overriding per-prompt evaluation requires exception.

### Approach 2: Thin skill (navigation only) + longer prompt steps

Skill covers only navigation mechanics. Each prompt embeds its own evaluation
logic inline (~12-15 lines per prompt).

**Pros**: Each prompt independently tunable; skill stays small.
**Cons**: Evaluation logic repeated 6 times; drift inevitable; more total
prompt length; updating evaluation requires touching all 6 prompts.

### Approach 3: Brain query agent dispatched by prompts

A `@cg-brain-query` agent is dispatched by each prompt. Agent reads BRAIN.md,
searches, evaluates, and returns structured findings.

**Pros**: Zero boilerplate in prompts; testable independently.
**Cons**: Subagent latency and token cost; parent can't tune evaluation;
overkill for read-and-filter; findings don't flow naturally into parent context.

## Decision

**Approach 1** — Skill with full protocol + short prompt directives. Best
balance of consistency (one source of truth for evaluation logic) and
separation of concerns (prompts declare search scope, skill teaches technique).

## Next Steps

1. Design and write `cg-skill-brain-query` SKILL.md with full protocol
2. Add `--no-brain` flag parsing to Step 0 of each target prompt
3. Add "Consult Brain" step to `/cg-brainstorm` (after user request)
4. Add "Consult Brain" step to `/cg-plan` (after user request/brainstorm ref)
5. Add "Consult Brain" step to `/cg-work` (after Step 1 loads plan)
6. Add "Consult Brain" step to `/cg-review` (after Step 1 identifies files)
7. Add "Consult Brain" step to `/cg-fix-triage` (after Step 1 loads report)
8. Add "Consult Brain" step to `/cg-compound` (after user describes solution)
9. Add skill description to `copilot-instructions.md` skill catalog
10. Write tests verifying each prompt has the brain step and flag
