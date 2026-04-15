---
date: 2026-04-14
title: "Pushback, plan review, side-idea capture, and schema bypass"
status: completed
completed-date: 2026-04-14
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-14-pushback-side-ideas-schema-bypass.md"
language: "both"
estimated-effort: "medium"
tags: [quality-loop, brainstorm, plan, pushback, roadmap, schema, cg-resume, agent]
---

# Plan: Pushback, Plan Review, Side-Idea Capture, and Schema Bypass

## Objective

Add devil's advocate pushback to `/cg-brainstorm` (inline, always-on), create a
dedicated plan review system (`@cg-plan-critic` agent + `/cg-plan-review` prompt),
wire up organic side-idea capture in both brainstorm and plan flows, and fix the
schema version false-alarm in `/cg-resume` when running inside the compound-gpid
repository itself.

## Context

The Quality Loop milestone tracks these features:
- `honest-pushback-in-brainstorm-strategy` (status: idea)
- `side-idea-capture-in-brainstorm` (status: idea)
- Schema bypass is a bug — not yet in roadmap.
- Plan review (`@cg-plan-critic` + `/cg-plan-review`) is a new feature — not yet
  in roadmap.

The brainstorm (`.cg-docs/brainstorms/2026-04-14-pushback-side-ideas-schema-bypass.md`)
decided:
- Brainstorm pushback is inline prompt logic (NOT `@cg-adversarial` dispatch)
- Plan review is a separate agent + prompt (NOT inline)
- Side-idea capture is organic (mid-conversation) + context-aware closing question
- Schema bypass detects `SCHEMA_VERSION` file at workspace root

Existing conventions:
- Agents use `user-invocable: false` unless they're meant for direct chat use
  (only `@cg-roadmap` is user-invocable today)
- Prompt files are self-contained with "Step 0: Get Bearings" boilerplate
- Tests in `prompt-tools.Tests.ps1` validate prompt structure via regex

## Requirements

| ID  | Requirement                                                    | Source     |
|-----|----------------------------------------------------------------|------------|
| R1  | Inline devil's advocate Step 3.5 in `cg-brainstorm.prompt.md` | brainstorm |
| R2  | Pushback is always-on, conversational, not a gate              | brainstorm |
| R3  | Pushback checklist: problem real? simpler solution? worth it? charter conflict? | brainstorm |
| R4  | Mid-conversation side-idea capture instruction in pushback     | brainstorm |
| R5  | Context-aware closing question in brainstorm Step 5            | brainstorm |
| R6  | New `@cg-plan-critic` agent with structured plan review focus  | brainstorm |
| R7  | New `/cg-plan-review` prompt that dispatches `@cg-plan-critic` | brainstorm |
| R8  | `/cg-plan-review` can review existing plans standalone         | brainstorm |
| R9  | `/cg-plan` Step 6 suggests `/cg-plan-review` and includes closing side-idea question | brainstorm |
| R10 | Schema bypass: skip comparison when `SCHEMA_VERSION` at workspace root | brainstorm |
| R11 | Roadmap updated: link existing features, add new ones          | brainstorm |
| R12 | `docs/reference.md` documents `/cg-plan-review` and `@cg-plan-critic` | brainstorm |
| R13 | `copilot-instructions.md` workflow table includes `/cg-plan-review` | brainstorm |
| R14 | Tests guard new prompt/agent structural requirements            | brainstorm |

## Implementation Steps

### 1. Add Step 3.5 Devil's Advocate to `cg-brainstorm.prompt.md`

- **Requirements**: R1, R2, R3, R4
- **Files**: `.github/prompts/cg-brainstorm.prompt.md`
- **Details**:
  Insert a new `### Step 3.5: Devil's Advocate` section between Step 3 (Propose
  Approaches) and Step 4 (Capture Decision). Contents:

  1. **Problem validation**: "Is this problem real and worth solving? Could the
     team live without this?" Challenge the premise.
  2. **Simplicity check**: "Does a simpler solution exist that we're
     overlooking? Could this be solved with configuration, a convention, or an
     existing tool instead of new code?"
  3. **Effort-value check**: "Is the effort proportional to the value? Could
     we achieve 80% of the value with 20% of the effort?"
  4. **Charter alignment**: "Does the chosen approach conflict with any
     declared constraints in `compound-gpid.md`?" (Cross-reference Step 0
     charter data.)
  5. **Side-idea capture instruction**: "If the user identifies an adjacent
     idea worth tracking separately during this exchange, offer to dispatch
     `@cg-roadmap` to capture it as an idea before continuing."

  Tone: conversational, not interrogative. Frame as "Here's my honest
  pushback..." not "Answer these questions." The user responds, and the
  conversation continues naturally before proceeding to Step 4.

  For Thinking Partner mode: adapt the checklist — replace "effort-value" with
  "decision reversibility" and "charter alignment" with "stakeholder impact."

- **Test Scenarios**:
  - ✅ Happy path: Step 3.5 exists and contains all four checklist items
  - 🛑 Edge case: Thinking Partner mode variant is documented
  - ❌ Error path: N/A (prompt logic, not executable code)
- **Tests**: Add Pester tests in `prompt-tools.Tests.ps1` for Step 3.5 structure
- **Acceptance criteria**: Step 3.5 section exists between Steps 3 and 4, contains
  all checklist items, includes side-idea capture instruction

### 2. Update Brainstorm Step 5 with Context-Aware Side-Idea Capture

- **Requirements**: R5
- **Files**: `.github/prompts/cg-brainstorm.prompt.md`
- **Details**:
  In Step 5 (Handoff), add a new section `#### 5b-bis. Side-Idea Capture`
  between the existing 5b (Roadmap Registration) and 5c (Handoff). This section:

  1. Check whether a pushback exchange occurred in Step 3.5.
  2. If **no pushback exchange**: present:
     > "No adjacent ideas surfaced during this session. Want to add anything to the roadmap anyway?"
  3. If **pushback exchange occurred**: present:
     > "During our pushback discussion, we touched on [summarize topics]. These could be added as ideas to [suggest milestone]. Want me to add any of them? Or capture a different idea?"
  4. If the user says yes to any: dispatch `@cg-roadmap` with the idea details.
  5. If no: proceed to 5c.

  Rename existing "5b. Roadmap Registration" numbering is fine — the new
  section logically sits after the automatic brainstorm-to-roadmap registration
  and before the final handoff options.

- **Test Scenarios**:
  - ✅ Happy path: Side-idea capture section exists in Step 5
  - 🛑 Edge case: Both "no pushback" and "had pushback" variants documented
  - ❌ Error path: N/A
- **Tests**: Add Pester test checking for side-idea capture content in Step 5
- **Acceptance criteria**: New section exists with both variants of the closing question

### 3. Create `@cg-plan-critic` Agent

- **Requirements**: R6
- **Files**: `.github/agents/cg-plan-critic.agent.md` (new)
- **Details**:
  Create a new agent definition file:

  ```yaml
  ---
  description: "Reviews implementation plans for risks, over-engineering, missing edge cases, and flawed assumptions. Dispatched by /cg-plan-review."
  model: Claude Sonnet 4.6 (copilot)
  tools: ['read', 'search']
  user-invocable: false
  ---
  ```

  Body should define the agent's review methodology:

  **Focus Areas** (plan-specific, NOT code-level):
  1. **Assumption validation**: Are the plan's assumptions about the codebase,
     dependencies, or user needs correct? Cross-reference actual code.
  2. **Over-engineering detection**: Are there steps that could be merged or
     eliminated? Is the plan building abstractions prematurely?
  3. **Missing edge cases**: What scenarios does the plan not account for?
     What could go wrong during implementation?
  4. **Risk assessment**: Are the listed risks the actual top risks? Are
     mitigations concrete and actionable?
  5. **Scope creep detection**: Does any step go beyond what the requirements
     demand? Are "nice to have" items mixed in with essentials?
  6. **Dependency accuracy**: Are referenced files, packages, and APIs real
     and current? Does the plan assume things that don't exist yet?

  **Output format**: Structured findings with priority levels (P1 for plan-
  blocking issues, P2 for important gaps, P3 for suggestions). Each finding
  includes: the specific plan section, what's wrong, and a concrete fix.

  **Rules**:
  - Read the actual codebase to verify plan assumptions — don't trust the plan's
    claims about what exists.
  - Focus on the plan document only. Do not review existing code quality.
  - If the plan is solid, say so. Do not manufacture findings.

  Also: user will build a parallel version using `/create-agent` for comparison.

- **Test Scenarios**:
  - ✅ Happy path: Agent file exists, has correct frontmatter, substantive body
  - 🛑 Edge case: Agent body > 100 chars (existing test `Agent files - non-trivial body content` covers this automatically)
  - ❌ Error path: Agent is NOT user-invocable
- **Tests**: Existing agent body-length test covers this automatically. Add
  frontmatter-specific test for `cg-plan-critic`.
- **Acceptance criteria**: Agent file exists, tools restricted to read+search,
  not user-invocable, body defines plan-specific review methodology

### 4. Create `/cg-plan-review` Prompt

- **Requirements**: R7, R8
- **Files**: `.github/prompts/cg-plan-review.prompt.md` (new)
- **Details**:
  Create a new prompt file. Structure:

  **Frontmatter**:
  ```yaml
  ---
  description: "Review an implementation plan for risks, over-engineering, and gaps. Use after /cg-plan or on existing plans."
  model: Claude Opus 4.6 (copilot)
  ---
  ```

  **Process**:
  - Step 0: Get Bearings (standard boilerplate — read charter + local config)
  - Step 1: Locate the plan to review
    - If the user specifies a plan file → use it
    - If not → scan `.cg-docs/plans/` for the most recent `status: active` plan
    - If no active plans → ask the user which plan to review
    - Read the full plan content
  - Step 2: Dispatch `@cg-plan-critic` with the plan content and charter context
  - Step 3: Present findings to the user interactively
    - For each P1/P2 finding, ask: "Do you want to address this?"
    - Collect decisions
  - Step 4: Side-idea capture (same context-aware pattern as brainstorm)
    - If the review surfaced adjacent ideas: present them with milestone suggestion
    - If not: "No adjacent ideas surfaced. Want to add anything to the roadmap?"
  - Step 5: Handoff
    - If findings need action: suggest `/cg-plan` to revise the plan
    - If plan is solid: suggest `/cg-work` to start implementation

  **File Permissions**:
  - May read any file
  - May NOT create or modify files (pure review)
  - Dispatches `@cg-plan-critic` and optionally `@cg-roadmap`

- **Test Scenarios**:
  - ✅ Happy path: Prompt exists, has correct frontmatter, dispatches @cg-plan-critic
  - 🛑 Edge case: Can find and review an existing plan without user specifying path
  - ❌ Error path: No plans exist in `.cg-docs/plans/`
- **Tests**: Add Pester tests for file existence, frontmatter structure, content patterns
- **Acceptance criteria**: Prompt file exists, dispatches `@cg-plan-critic`, can
  review existing plans standalone, includes side-idea capture

### 5. Update `/cg-plan` Step 6 Handoff + Side-Idea Capture

- **Requirements**: R9
- **Files**: `.github/prompts/cg-plan.prompt.md`
- **Details**:
  Two changes to the existing `cg-plan.prompt.md`:

  **5a. Add `/cg-plan-review` to Step 6 handoff options**:
  Update the handoff menu to include:
  ```
  > 1. **`/cg-work`** — Start implementing this plan immediately
  > 2. **`/cg-plan-review`** — Challenge this plan before starting *(recommended for Standard/Deep plans)*
  > 3. **`/cg-brainstorm`** — Revisit open questions or explore a related topic first
  ```
  (Replace the previous option 2 which was `/cg-review` — code review isn't
  appropriate for a plan; plan review is.)

  **5b. Add side-idea closing question before handoff (new Step 5.5 or within Step 6)**:
  Before presenting handoff options, add the context-aware side-idea question:
  - If the `/cg-plan` session surfaced any ideas in Q&A or research that aren't
    part of this plan: "During planning, we discussed [topics]. Any of these
    worth adding to the roadmap as separate ideas?"
  - If no side threads: "Want to capture any adjacent ideas to the roadmap
    before proceeding?"

- **Test Scenarios**:
  - ✅ Happy path: `/cg-plan-review` appears in handoff options
  - 🛑 Edge case: Side-idea question exists
  - ❌ Error path: N/A
- **Tests**: Add Pester test checking for `/cg-plan-review` mention in Step 6
- **Acceptance criteria**: Handoff suggests `/cg-plan-review`, side-idea question present

### 6. Fix Schema Bypass in `/cg-resume`

- **Requirements**: R10
- **Files**: `.github/prompts/cg-resume.prompt.md`
- **Details**:
  In Step 1 (Schema Version Check), add a guard at the very beginning:

  > **Before comparing versions**: Check if the workspace root contains a
  > `SCHEMA_VERSION` file (not the global install path —the workspace itself).
  >
  > If the workspace root has `SCHEMA_VERSION`, this IS the compound-gpid
  > source repository. The schema check is not meaningful here — skip it
  > entirely and proceed to Step 2.

  This goes before the existing "Locate the global Compound GPID `SCHEMA_VERSION`
  file at..." instruction.

- **Test Scenarios**:
  - ✅ Happy path: Guard text exists in Step 1 mentioning workspace root check
  - 🛑 Edge case: The skip instruction is clear ("skip" + "proceed to Step 2")
  - ❌ Error path: Guard does NOT remove the existing schema check for normal projects
- **Tests**: Add Pester test checking for workspace-root SCHEMA_VERSION guard
- **Acceptance criteria**: Guard text exists, existing schema check preserved for
  non-compound-gpid workspaces

### 7. Update Documentation and Roadmap

- **Requirements**: R11, R12, R13, R14
- **Files**:
  - `docs/reference.md` — add `/cg-plan-review` to prompts table, `@cg-plan-critic` to agents table
  - `.github/copilot-instructions.md` — add `/cg-plan-review` to workflow entry points
  - `roadmap.json` — via `@cg-roadmap` dispatch:
    - Add feature "Plan review agent and prompt (@cg-plan-critic + /cg-plan-review)" to quality-loop
    - Add feature "Schema bypass for compound-gpid repo in /cg-resume" to quality-loop
    - Link this plan to all four relevant features
- **Details**:

  **`docs/reference.md`**:
  - Add row to Copilot Chat Prompts table:
    `| /cg-plan-review | Claude Opus 4.6 | Review an implementation plan for risks, over-engineering, and gaps. Dispatches @cg-plan-critic. |`
  - Add row to agents section (new "Plan Review Agent" table or add to existing):
    `| cg-plan-critic | Plan review: assumptions, over-engineering, missing edges, scope creep | Sonnet 4.6 |`
  - Update `@cg-plan-critic` description to note it's dispatched by `/cg-plan-review`

  **`.github/copilot-instructions.md`**:
  - Add entry: `| Review a plan before implementing | /cg-plan-review |`

- **Test Scenarios**:
  - ✅ Happy path: reference.md mentions `/cg-plan-review` and `@cg-plan-critic`
  - 🛑 Edge case: copilot-instructions.md workflow table entry exists
  - ❌ Error path: N/A
- **Tests**: (covered by existing CI patterns — no new Pester tests needed for docs)
- **Acceptance criteria**: Both docs updated, roadmap has all features linked

## Testing Strategy

All tests are structural Pester tests in `prompt-tools.Tests.ps1` that validate
prompt content via regex. Pattern follows existing tests (e.g., Step 0.5, Step 1.5,
Step 4.5 tests). New test blocks:

1. **`cg-brainstorm.prompt.md - Step 3.5 Devil's Advocate`**: Checks for step
   existence, checklist items (problem validation, simplicity, effort-value,
   charter alignment), side-idea capture instruction.
2. **`cg-brainstorm.prompt.md - Step 5 Side-Idea Capture`**: Checks for both
   closing-question variants.
3. **`cg-plan-critic.agent.md - existence and frontmatter`**: File exists, correct
   tools, not user-invocable. (Existing body-length test auto-covers.)
4. **`cg-plan-review.prompt.md - existence and structure`**: File exists, no tools
   restriction (orchestrating prompt), dispatches `@cg-plan-critic`.
5. **`cg-plan.prompt.md - Step 6 plan-review handoff`**: `/cg-plan-review` in
   handoff options, side-idea question present.
6. **`cg-resume.prompt.md - schema bypass guard`**: SCHEMA_VERSION workspace root
   check in Step 1.

## Documentation Checklist

- [ ] `docs/reference.md` — `/cg-plan-review` prompt entry, `@cg-plan-critic` agent entry
- [ ] `.github/copilot-instructions.md` — workflow table entry for plan review
- [ ] Inline comments in new prompt/agent files explaining the design rationale

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Pushback feels annoying on Lightweight brainstorms | Medium | Medium | Keep it brief for Lightweight scope — 1-2 sentences, not the full checklist. Add scope-adaptive note. |
| `@cg-plan-critic` findings overlap with Step 4.5 Confidence Check | Medium | Low | Different focus: Confidence Check is structural completeness; plan-critic is substantive quality. Document the distinction in the prompt. |
| Side-idea capture adds friction to workflow | Low | Low | Both triggers are conversational, not modal. User can always skip. |
| Schema bypass could mask real schema drift in forks | Low | Medium | Detection is file-based (`SCHEMA_VERSION` in workspace root), which only the source repo has. Forks that rename/restructure wouldn't have this file. |

## Out of Scope

- Extending `@cg-adversarial` for plan-level review (decided against in brainstorm)
- `/cg-plan review` (space variant / argument detection) — opted for hyphenated prompt instead
- Pushback in `/cg-strategy` (same roadmap feature title mentions it, but this plan focuses on brainstorm + plan only)
- Testing skills for Python/Stata (separate roadmap features)
- Per-step test enforcement in `/cg-work` (separate roadmap feature)
