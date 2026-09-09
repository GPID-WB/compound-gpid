---
date: 2026-09-04
title: "Implement Minimal Adaptive Grilling"
status: completed
completed-date: 2026-09-08
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-04-minimal-adaptive-grilling.md"
language: "both"
estimated-effort: "medium"
deviation-policy: "ask"
artifact-schema-version: 1
tags: [brainstorming, adaptive-grilling, requirements, decision-frontier, prompts, skills, generated-targets, pester]
phases: 1
execution-report: ".cg-docs/work-reports/2026-09-08-minimal-adaptive-grilling.md"
completed-phases: [1]
---

# Plan: Implement Minimal Adaptive Grilling

## Objective

Improve `/cg-brainstorm` with the smallest complete adaptive-grilling pilot.
The command will discover facts before asking the user, reserve questions for
material decisions, traverse only the ready frontier of a decision-dependency
tree, use bounded adaptive rounds, and stop when remaining uncertainty cannot
change the minimum viable solution. It will then require explicit confirmation
of the minimal design before it offers any more sophisticated exploration.

## Context

The approved brainstorm selected **Minimal Adaptive Grilling** instead of a
cross-workflow decision spine or a persistent Wayfinder-style graph. The pilot
must reuse the existing `cg-skill-brainstorming` bundle and preserve the current
Compound GPID lifecycle.

The current implementation has two related fixed-question contracts:

- `.github/skills/cg-skill-brainstorming/workflows/requirement-elicitation.md`
  directs the agent through six areas in sequence and uses a usual 3-6 question
  count as its stopping heuristic.
- `.github/prompts/cg-brainstorm.prompt.md` repeats a mandatory ordered six-area
  interview, does not explicitly load `cg-skill-brainstorming`, and moves to
  approaches after a usual 3-6 questions rather than after material uncertainty
  is resolved.

The loaded skill bundle also links
`.github/skills/cg-skill-brainstorming/references/decision-template.md`. Its
legacy capture example omits required `scope` and `artifact-schema-version`
fields and lists statuses that the current artifact validator rejects. The
pilot must align this linked template with the authoritative prompt capture
schema so successful skill loading cannot produce an invalid Brainstorm.

The existing prompt already contains branch setup, staged context loading,
Brain consultation, task and scope classification, Devil's Advocate review,
artifact validation, roadmap handling, and final handoff. Those controls are
not redesign targets. Critical adaptive rules must remain in the prompt as a
safe fallback even though the skill workflow is the shared source of detailed
guidance.

`.github/` is the canonical product source. `scripts/cg_generate_targets.py`
generates complete native trees for Claude Code, Codex, OpenCode, and Kilo,
including recursive skill bundles, commands, and ownership manifests. Generated
files must not be edited directly. Existing target packaging tests already
compare the four-file brainstorming skill bundle recursively across all native
targets.

Relevant project knowledge:

- Generated native trees are committed product surfaces and must be regenerated
  and parity-tested after canonical `.github/` changes. Source:
  `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`.
- Behavioral prompt and skill contracts need focused assertions, not only file
  existence checks. Source:
  `.cg-docs/solutions/testing-patterns/2026-04-20-behavioral-pester-tests-for-skill-md-files.md`.
- Prompt gate order needs guarded `IndexOf()` assertions because content-presence
  tests do not detect dead or reordered workflow steps. Source:
  `.cg-docs/solutions/testing-patterns/2026-04-13-prompt-step-ordering-indexof-tests.md`.

The matching roadmap feature is
`minimal-adaptive-grilling-for-the-compound-gpid-workflow`. Roadmap linking is a
separate workflow action; implementation must not write `roadmap.json` directly
or overwrite the current uncommitted roadmap changes.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Reuse the existing `cg-skill-brainstorming` bundle as the shared adaptive-grilling logic layer; do not create a second grilling skill. | brainstorm requirements 2-4 |
| R2 | Separate discoverable facts from material user decisions; research available facts before asking the user; and fail loudly on missing, inaccessible, stale, or conflicting material facts. | brainstorm requirements 5-6 and plan review P2.1 |
| R3 | Model material decisions and their prerequisites as an internal dependency tree; ask only decisions on the ready frontier whose answers can change implementation, behavior, scope, risk, or user experience. | brainstorm requirements 7-9 |
| R4 | Ask one question by default; batch no more than two or three short independent decisions only when this clearly reduces user effort, and never batch dependent decisions. | brainstorm requirements 11-12 |
| R5 | Give each material decision a concise recommended answer and trade-offs while making the recommendation visibly optional and avoiding large recommendation batches that encourage passive agreement. | brainstorm requirements 11, 13 |
| R6 | Prefer the simplest reasonable default for immaterial uncertainty and stop when unresolved items cannot materially change the minimum viable solution. | brainstorm requirements 4, 9-10, 14 |
| R7 | Keep purpose, users, inputs/outputs, constraints, edge cases, and scope as a completeness checklist, not a mandatory sequence or fixed question count anywhere in the prompt. | brainstorm next step 2 and plan review P1.1 |
| R8 | Resolve any material approach choice explicitly, then summarize the selected minimal design and require confirmation before capture or implementation handoff; only after confirmation may the command ask whether to explore a more sophisticated version, and a rejected summary must return through a defined objection-classification transition. | brainstorm requirements 15-16 and plan review P1.2 |
| R9 | Preserve existing branch, context-loading, Brain, task classification, scope, Devil's Advocate, artifact validation, roadmap, side-idea, and handoff behavior. | brainstorm requirement 17 |
| R10 | Explicitly load and apply `cg-skill-brainstorming`, but retain the critical fact/decision, materiality, adaptive-round, stop, and confirmation rules in the prompt so skill-loading failure cannot remove safety or lifecycle gates. | brainstorm requirements 3, 18 and Decision |
| R11 | Add focused prompt and skill assertions for loading, fact discovery, dependency frontier, materiality, round bounds, recommendation transparency, stop conditions, coverage-checklist semantics, minimal-design confirmation, and complexity opt-in ordering. | brainstorm next step 6 |
| R12 | Regenerate Claude Code, Codex, OpenCode, and Kilo targets through the canonical generator and verify canonical-to-native command and recursive skill-bundle parity. | brainstorm next step 7 |
| R13 | Keep stable decision IDs, persistent graphs, specification/ticket splitting, review-axis changes, glossary or ADR writes, and `/cr-brainstorm` integration outside this pilot. | brainstorm Decision deferred list |
| R14 | Align the brainstorming skill's linked decision template with the current Brainstorm artifact schema and prompt capture contract. | plan review P2.2 and artifact validation contract |
| R15 | Compare two or three approaches only when at least two materially different paths remain; when only one viable path remains, present it directly for Devil's Advocate review instead of inventing alternatives. | plan review second pass P2.3 and existing approach-comparison workflow |

## Implementation Steps

## Phase 1: Adaptive Contract And Native Propagation

### 1. Define adaptive elicitation in the existing brainstorming skill

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R10, R13, R14
- **Files**:
  - `.github/skills/cg-skill-brainstorming/SKILL.md`
  - `.github/skills/cg-skill-brainstorming/workflows/requirement-elicitation.md`
  - `.github/skills/cg-skill-brainstorming/references/decision-template.md`
- **Details**:
  - Keep `SKILL.md` as a thin router, but state that the requirement-elicitation
    workflow supplies the shared adaptive decision protocol used by
    `/cg-brainstorm`.
  - Replace the mandatory six-area sequence and 3-6-question heuristic in the
    requirement-elicitation workflow with an explicit fact-discovery pass,
    fact-versus-decision classification, a material-decision dependency tree,
    and a ready-frontier selection rule.
  - Track fact status in memory as established, unavailable, stale, or
    conflicting. Apply existing authority precedence: the charter governs
    scope and constraints; current code, configuration, and tool output beat
    historical artifacts; and unresolved equal-authority conflicts remain
    explicit. Report failed sources. Block confirmation when an unresolved fact
    is material, ask the user only when the user is the authoritative source,
    and disclose the chosen simple default for an immaterial fact gap.
  - Define materiality by outcome: ask only if an answer can change
    implementation, behavior, scope, risk, or user experience. Select the
    simplest reasonable default for other uncertainty and record it in the
    eventual summary rather than asking about it.
  - Define adaptive rounds precisely: one decision by default; two or three
    short independent decisions only when batching clearly lowers user effort;
    no dependent decisions in the same round. Recompute the frontier after each
    answer or round.
  - Require a visible recommendation and concise trade-offs for each material
    decision. State that the recommendation is a default, not a hidden choice,
    and avoid large batches of recommended answers.
  - Retain the six existing subject areas as a final coverage checklist. Missing
    coverage does not create a question unless the missing information is
    material to the minimum viable solution.
  - Define the stop condition as an empty material ready frontier plus no
    unresolved uncertainty that can change the minimum viable solution. Do not
    introduce IDs, persisted graphs, schemas, or a new skill.
  - Align `references/decision-template.md` with the authoritative Step 4
    Brainstorm frontmatter: include `scope` and `artifact-schema-version: 1`,
    use only `decided`, `in-progress`, or `abandoned` status values, and keep
    capture headings consistent with the canonical prompt. Do not let the skill
    template override prompt file permissions, validation, or lifecycle steps.
- **Test Scenarios**: a discoverable repository fact; one material decision;
  two independent short decisions; dependent decisions; immaterial uncertainty;
  a missing or inaccessible material fact; stale evidence; conflicting current
  sources; the user as authoritative source; an initially relevant branch made
  irrelevant by an earlier answer; uncovered checklist area that is immaterial;
  unresolved material decision; decision-template validation.
- **Tests**: focused behavioral assertions added in Step 3 and run through
  `. tests\Run-Tests.ps1 -File prompt-tools` by an execution subagent.
- **Acceptance criteria**: The existing skill bundle defines one coherent,
  bounded adaptive protocol with objective materiality and stop rules, preserves
  the six coverage areas without forcing them into a questionnaire, handles
  unavailable or conflicting facts without a silent fallback, exposes a valid
  capture template, and adds no new persistence or skill infrastructure.

### 2. Integrate the skill and confirmation gate into `/cg-brainstorm`

- **Requirements**: R2, R3, R4, R5, R6, R7, R8, R9, R10, R13, R15
- **Files**:
  - `.github/prompts/cg-brainstorm.prompt.md`
- **Details**:
  - Add an explicit instruction to load and apply
    `cg-skill-brainstorming` before elicitation. Treat a load failure as a
    warning and continue with the prompt's complete critical fallback rules;
    do not silently skip the adaptive or lifecycle gates.
  - Refocus Step 1 research on discovering relevant facts before the first user
    decision. Do not ask the user for information that current code, project
    files, tools, or documentation can supply. Mirror the skill's explicit
    missing, stale, and conflicting fact rules in the prompt fallback: report
    failed sources, follow authority precedence, block on an unresolved material
    fact, and ask only an authoritative user.
  - Replace fixed-count scope guidance in Step 1.5. Scope controls research,
    risk analysis, and option detail, not a target number of questions. Remove
    the current `2-3 focused questions` and `Full 6-question set` instructions.
  - Replace Step 2's ordered six-question interview with the adaptive protocol.
    Keep explicit prompt-level rules for fact/decision separation, materiality,
    dependency prerequisites, one-by-default and three-maximum independent
    rounds, recommendations with trade-offs, frontier recomputation, and the
    minimum-viable stop condition.
  - Keep the six subject areas as a coverage check performed before proposing
    approaches. A gap can reopen Step 2 only when it exposes a material decision.
  - Preserve the purpose of Step 3 approach analysis and Step 3.5 Devil's
    Advocate behavior, but make Step 3 conditional. Compare two or three
    approaches only when at least two materially different paths remain. If one
    viable path remains, present that path and why alternatives are not material,
    then run Devil's Advocate without inventing extra options. If no viable path
    remains, stop with the blocking facts or decisions. Recommendations made
    during elicitation do not replace comparison when multiple paths remain.
  - Replace Step 3's `usually 3-6 questions` entry condition with an adaptive
    condition: proceed only when no unresolved fact or decision can materially
    change the paths being analyzed.
  - Replace Step 3.5's current direct `proceed to Step 4` transition with
    `proceed to Step 3.6`. Preserve the Devil's Advocate exchange itself, but do
    not permit it to bypass approach selection or minimal-design confirmation.
  - Add `### Step 3.6: Resolve Approach Choice`. After Devil's Advocate, treat
    any unresolved choice between materially different approaches as one
    material frontier decision. Obtain an explicit selection before composing
    the confirmation summary; never treat the recommended approach as selected
    by default.
  - Add `### Step 3.7: Minimal Design Confirmation`. Summarize the selected
    smallest complete design, researched facts, explicit decisions, selected
    defaults, and remaining immaterial uncertainty. Use stable user-facing
    anchors `Minimal design for confirmation:`, `Confirm this minimal design
    before I capture it.`, and, only after an affirmative response, `Minimal
    design confirmed. Explore a more sophisticated version? (yes/no, default:
    no)`.
  - If confirmation is declined, ask for one concise objection. Classify it as
    a discoverable fact, a material decision, or a scope change; research or add
    it to the frontier as appropriate, then recompute the frontier. If the user
    provides no actionable reason or a material fact remains unavailable, stop
    with an explicit unresolved state and do not capture or hand off.
  - If the confirmed user opts into added complexity, return to Step 2 and then
    follow Step 3 approach analysis, Step 3.5 Devil's Advocate, Step 3.6 approach
    choice, and Step 3.7 minimal-design confirmation in that order before
    capture. Default the optional complexity answer to no.
  - Leave branch setup, context stages, Brain consultation, task/scope modes,
    artifact validation, roadmap and side-idea handling, and final handoff in
    their current relative order and with their existing failure behavior.
- **Test Scenarios**: skill load succeeds; skill load fails; fact available from
  repository; missing material fact; conflicting fact sources; one ready
  material decision; batched independent decisions; dependent decision withheld;
  user rejects recommendation; multiple-path comparison; single viable path;
  no viable path; explicit approach selection; no material questions remain;
  user rejects minimal design with a fact objection; user
  rejects without an actionable reason; user confirms and declines complexity;
  user confirms and opts into complexity then repeats Steps 2, 3, 3.5, 3.6, and
  3.7; Thinking Partner mode; existing branch and artifact failure paths.
- **Tests**: focused content and ordering assertions added in Step 3 and run via
  the canonical Pester runner.
- **Acceptance criteria**: `/cg-brainstorm` can execute the complete minimal
  adaptive workflow even if skill loading fails, requires minimal-design
  confirmation of an explicitly selected approach before capture or handoff,
  has a terminating rejection transition, and cannot offer added complexity
  before confirmation while preserving all existing lifecycle gates.

### 3. Add behavioral and ordering regression contracts, then regenerate

- **Requirements**: R7, R8, R9, R10, R11, R12, R14, R15
- **Files**:
  - `tests/prompt-tools.Tests.ps1`
  - `.claude/` (generated)
  - `.agents/` (generated)
  - `.opencode/` (generated)
  - `.kilo/` (generated)
- **Details**:
  - Add a dedicated behavioral `Describe` block that reads the canonical
    brainstorming skill workflow and independently asserts fact discovery,
    failed/conflicting fact handling, materiality dimensions,
    dependency-tree/frontier handling, one-question default, three-question
    maximum, no dependent batching, recommendation transparency,
    coverage-checklist semantics, and the material stop condition.
  - Add a decision-template contract block that verifies required `scope` and
    `artifact-schema-version: 1` fields and only current valid status values.
  - Add canonical prompt assertions for exact skill loading and critical
    fallback behavior. Assert each mandatory concept separately; do not use a
    broad regex alternation where one arm can hide a missing contract.
  - Isolate Step 1.5, Step 2, and Step 3 text between guarded heading positions.
    Reject the current en-dash or ASCII forms with a Unicode-tolerant pattern
    such as `2(?:-|\u2013)3\s+focused questions`. Assert that `Full 6-question
    set`, ordered six-area interviewing, and `usually 3-6 questions` are also
    absent from their relevant blocks while the six areas remain as a coverage
    checklist.
  - Add structural `IndexOf()` assertions for the exact headings Step 3.5,
    Step 3.6, Step 3.7, and Step 4. Prove `Step 3.5 < Step 3.6 < Step 3.7 < Step
    4`, with separate presence checks for every heading.
  - Extract only the Step 3.7 block using guarded Step 3.7 and Step 4 indices.
    Assert the three stable user-facing anchors in that block and their local
    order: summary before confirmation, confirmation before optional complexity.
    Do not let duplicate fallback prose elsewhere satisfy these assertions.
  - Extract the Step 3.5 block with guarded Step 3.5 and Step 3.6 indices. Assert
    that its final transition points to Step 3.6 and does not point directly to
    Step 4.
  - Assert that Step 3 conditionally compares two or three paths, has a distinct
    single-viable-path branch without artificial alternatives, and blocks when
    no viable path remains. Assert that complexity opt-in routes through Steps 2,
    3, 3.5, 3.6, and 3.7 in order.
  - Add rejection-path assertions for one concise objection, fact/decision/scope
    classification, frontier recomputation, and explicit unresolved stop.
  - Keep and run all existing `/cg-brainstorm` contract tests so branch, scope,
    Devil's Advocate, side-idea, artifact, roadmap, and handoff regressions fail
    in the same focused run.
  - After canonical source and tests are complete, run
    `python scripts/cg_generate_targets.py --all` once. Do not edit generated
    commands, skills, adapters, configs, or ownership manifests by hand.
- **Test Scenarios**: deletion of any one adaptive rule; accidental restoration
  of any fixed-count instruction, including the en-dash form; restoration of
  the ordered interview; direct Step 3.5-to-Step 4 bypass; artificial options in
  a single-path case; approach selection removed; complexity prompt moved before confirmation;
  fallback text accidentally satisfies a Step 3.7 test; missing heading used for
  block extraction; invalid decision template; existing lifecycle text removed;
  canonical change not reflected in one native target.
- **Tests**:
  - execution subagent: `. tests\Run-Tests.ps1 -File prompt-tools`, then read
    `tests/last-run.json` and return only `passed`, `failedCount`, and `failures`
  - `python scripts/cg_generate_targets.py --all`
- **Acceptance criteria**: Focused Pester evidence passes, every new contract has
  a direct failure signal, existing brainstorm contracts remain green, and the
  generator completes without ownership, path, or collision errors.

### 4. Verify canonical-to-native command and skill parity

- **Requirements**: R11, R12
- **Files**:
  - `.github/prompts/cg-brainstorm.prompt.md`
  - `.github/skills/cg-skill-brainstorming/`
  - `.claude/commands/cg-brainstorm.md`
  - `.claude/skills/cg-skill-brainstorming/`
  - `.agents/commands/cg-brainstorm.md`
  - `.agents/skills/cg-skill-brainstorming/`
  - `.opencode/commands/cg-brainstorm.md`
  - `.opencode/skills/cg-skill-brainstorming/`
  - `.kilo/commands/cg-brainstorm.md`
  - `.kilo/skills/cg-skill-brainstorming/`
  - generated ownership manifests under each native tree
- **Details**:
  - Run the existing recursive package tests against the current working tree so
    every canonical brainstorming skill file and generated relative path is
    compared across all four native targets.
  - Run the existing platform-format tests for Claude Code, Codex, OpenCode, and
    Kilo so generated command and skill frontmatter remains valid for each
    platform after canonical prompt changes.
  - Use generator and test outputs as evidence. Do not require the committed-HEAD
    drift gate before `/cg-work` completion because that gate intentionally
    rejects uncommitted generated changes; leave that release/commit check for
    the normal commit workflow.
  - If generation changes unrelated native outputs, inspect the generator result
    and ownership manifest before accepting them. Do not hand-edit or discard
    generated files to force a small diff.
- **Test Scenarios**: exact recursive skill inventory; transformed command path
  and frontmatter; all four targets present; one stale generated command; one
  missing workflow file; malformed target metadata.
- **Tests**: `python -m pytest scripts/tests/test_target_packaging.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_kilo.py -q`
- **Acceptance criteria**: All four generated command and skill surfaces contain
  the current adaptive contract in valid target-native form, recursive skill
  inventories match canonical source, and focused target tests pass without
  direct generated-file edits.

### 5. Audit the pilot boundary and prepare the final phase gate

- **Requirements**: R9, R11, R12, R13
- **Files**:
  - all files changed by Steps 1-4
  - `tests/last-run.json` (test evidence artifact only)
- **Details**:
  - Do not start an additional full Pester run inside this step. After Step 5,
    the mandatory `/cg-work` Step 2.5 final phase-boundary gate runs the complete
    `. tests\Run-Tests.ps1` command once through an execution subagent and reads
    `passed`, `failedCount`, `failures`, and `filteredFiles` from
    `tests/last-run.json`. A partial result with non-null `filteredFiles` does
    not satisfy V4 or phase completion.
  - Run `git diff --check`. Compare final `git status --short` and changed paths
    with the implementation-owned paths in this plan. Preserve the pre-existing
    brainstorm and roadmap changes and do not claim them as implementation work.
  - Confirm no new dependency, skill, persistent artifact schema, roadmap write,
    review redesign, or `/cr-brainstorm` change entered the diff.
  - Record prompt-runtime behavior as pilot uncertainty rather than claiming
    that static prose tests prove model compliance. Empirical evidence can inform
    the deferred Deep-only follow-up after real use.
- **Test Scenarios**: complete suite pass; partial Pester artifact; failed test;
  whitespace error; unexpected changed path; deferred feature in the diff;
  pre-existing unrelated worktree change.
- **Tests**:
  - no additional Pester invocation in this step; use the automatic final
    phase-boundary full-suite gate for V4
  - `git diff --check`
  - `git status --short`
- **Acceptance criteria**: Target pytest evidence passes, `git diff --check`
  succeeds, implementation-owned changes stay within the pilot boundary,
  pre-existing worktree changes remain intact, and the automatic final
  phase-boundary gate remains the single required full-suite run.

## Testing Strategy

- Treat prompt and skill prose as behavioral contracts. Give each material rule
  an independent Pester assertion with wording derived from the final canonical
  text.
- Use guarded section extraction for Step 1.5, Step 2, Step 3, and Step 3.7
  assertions. Check heading positions before `Substring()` so a missing heading
  produces a clear failed assertion rather than an exception.
- Test order separately from presence for fact discovery, explicit approach
  selection, minimal-design confirmation, optional complexity, decision capture,
  and final handoff. Scope confirmation anchors to the Step 3.7 block.
- Isolate the Step 3.5 transition and prove it enters Step 3.6 rather than
  bypassing the new gates. Test the explicit Step 2 -> 3 -> 3.5 -> 3.6 -> 3.7
  complexity opt-in loop separately.
- Test missing, inaccessible, stale, and conflicting facts as explicit states;
  require a blocking outcome when any unresolved fact can change the minimal
  design.
- Keep all current `/cg-brainstorm` tests in the focused run. The pilot is an
  addition to the workflow, not a replacement for branch, scope, Brain,
  Devil's Advocate, artifact, roadmap, or side-idea contracts.
- Run focused Pester through `tests/Run-Tests.ps1` and an execution subagent in
  Step 3. Let `/cg-work` Step 2.5 run the complete suite once at the final
  one-phase boundary. Never invoke `Invoke-Pester` directly or pipe Pester
  output. Read the atomic `tests/last-run.json` summary.
- Use existing generator/package/platform pytest suites for native parity. Do
  not add a new evaluation harness or runtime dependency for this pilot.
- Keep empirical model adherence outside the deterministic completion gate.
  Static contract and parity tests prove shipped instructions, not that every
  model run will follow them perfectly.

## Documentation Checklist

- [ ] `cg-skill-brainstorming/SKILL.md` identifies the adaptive elicitation workflow as the shared logic layer.
- [ ] The requirement-elicitation workflow defines fact failure states, material decisions, prerequisites, frontier selection, rounds, recommendations, stop conditions, and the six-area coverage check.
- [ ] The linked decision template uses the current required Brainstorm fields and valid statuses.
- [ ] `/cg-brainstorm` documents skill loading plus complete critical fallback rules.
- [ ] `/cg-brainstorm` removes all fixed question-count guidance and documents explicit approach selection, terminating rejection handling, minimal-design confirmation, and post-confirmation complexity opt-in paths.
- [ ] `/cg-brainstorm` compares approaches only when multiple material paths remain and has explicit one-path and no-path branches.
- [ ] Existing branch, context, Brain, scope, Devil's Advocate, artifact, roadmap, side-idea, and handoff instructions remain present.
- [ ] Generated Claude Code, Codex, OpenCode, and Kilo command and skill files are refreshed by the generator.
- [ ] No general user or maintainer documentation claims decision IDs, persistence, runtime evaluation, or cross-suite support from this pilot.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Shared skill guidance and prompt fallback drift into different adaptive rules. | Platform or skill-loading differences produce inconsistent interviews or remove a gate. | Keep one detailed skill workflow, duplicate only critical fail-safe rules in the prompt, and assert the same objective bounds independently in both files. |
| A required fact is missing, stale, inaccessible, or contradicted by an equal-authority source. | The frontier is evaluated from an unsupported premise or the workflow silently converts a fact into a preference. | Track fact state in memory, report failed sources, apply explicit authority precedence, ask only an authoritative user, and block confirmation while a material fact remains unresolved. |
| Materiality, dependency readiness, or the stop condition is too vague. | The command still asks unnecessary questions or stops before a consequential choice is settled. | Define materiality by five explicit outcome dimensions, define ready decisions by settled prerequisites, require frontier recomputation, and require both no material ready decision and no minimum-viable-impact uncertainty before stopping. |
| Recommended answers anchor the user or make batched acceptance passive. | The user accepts hidden design choices without evaluating trade-offs. | Default to one decision, cap rounds at three independent decisions, label recommendations as optional defaults, provide concise trade-offs, and forbid dependent decisions in one round. |
| The optional complexity offer weakens the minimum-design gate or creates an interview loop. | Users are pushed into over-engineering or capture occurs without stable agreement. | Put explicit confirmation before the offer, default the offer to no, return opt-in work to the adaptive frontier, and repeat Devil's Advocate plus confirmation before capture. |
| Step 3.5 retains its old direct transition to Step 4. | The command bypasses explicit approach selection and minimal-design confirmation even though the new steps exist. | Replace the transition with Step 3.6 and test the isolated Step 3.5 block for the required route and forbidden direct jump. |
| Step 3 invents alternatives when research supports only one path. | The workflow adds token cost, weak options, and user confusion contrary to the minimal pilot. | Compare approaches only with two or more material paths; otherwise present the one viable path for pushback or block when none remains. |
| Existing lifecycle steps are reordered or removed while Step 2 is rewritten. | Branch safety, Brain use, artifact validation, roadmap handling, or handoff behavior regresses. | Limit edits to fact discovery, elicitation, and the new confirmation step; retain existing tests and add guarded ordering assertions around new and existing boundaries. |
| The skill's linked capture template remains stale after the elicitation workflow changes. | A loaded skill can guide the agent to write a Brainstorm that fails mandatory artifact validation. | Align the template with the prompt and artifact schema, then test required fields and valid statuses directly. |
| Broad or alternating regex assertions stay green after one contract disappears. | Tests give false confidence while prompt behavior silently regresses. | Assert each contract separately, derive patterns from final prose, use negative checks on an isolated Step 2 block, and guard all indices before section extraction. |
| Canonical changes are not propagated to one native target. | Some users receive the old fixed questionnaire or an incomplete skill bundle. | Run the canonical generator for all targets, use recursive bundle comparison and all four platform tests, and never edit generated outputs directly. |
| The committed-HEAD drift test is used before the implementation is committed. | Correct uncommitted generated changes cause a false completion failure. | Use working-tree packaging and platform parity tests during `/cg-work`; leave the committed drift/release gate to the normal commit workflow. |
| The pilot expands into persistent decision infrastructure or cross-suite redesign. | A medium prompt improvement becomes a large architecture change without evidence. | Enforce the explicit boundary list, audit changed paths, and stop under `deviation-policy: ask` if any deferred capability becomes necessary. |
| Static prompt tests are mistaken for empirical model-behavior proof. | The team overstates pilot success and expands the design without usage evidence. | State this limitation in final evidence and require later real-use evidence of decision drift, false completion, or context loss before the deferred Deep follow-up. |

## Out of Scope

- Stable decision IDs or requirement traceability from brainstorm to plan and review.
- A persisted dependency graph, Wayfinder state, decision tickets, or a new artifact schema.
- A second grilling skill or a general cross-suite grilling capability.
- `/cr-brainstorm` or module-registry changes.
- A new specification-compliance review axis.
- Splitting specification from ticket generation.
- Automatic glossary, ADR, or roadmap writes during elicitation.
- A prompt-runtime evaluation harness, model benchmark, or new dependency.
- Direct edits to generated native target files or `roadmap.json`.
- Treating the deferred `brainstorm-depth-grill-mode` roadmap item as part of this pilot.

## Completion Contract

### Outcome

`/cg-brainstorm` uses the existing brainstorming skill to research discoverable
facts, model material decisions as a dependency frontier, ask bounded adaptive
rounds, resolve the approach explicitly, stop at the minimum viable shared
understanding, require explicit minimal-design confirmation, and offer added
complexity only afterward. Missing material facts and non-actionable rejected
summaries stop visibly. Existing lifecycle gates, the linked capture template,
and all generated native targets remain valid.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Canonical skill, linked decision template, and prompt contain valid fact-state, adaptive decision, materiality, round, stop, conditional approach, Step 3.5 transition, selection, rejection, confirmation, opt-in loop, and fallback contracts with no fixed-count conflicts. | Focused assertions in `tests/prompt-tools.Tests.ps1` through `. tests\Run-Tests.ps1 -File prompt-tools`; inspect `tests/last-run.json` | yes |
| V2 | 1 | Existing context, branch, Brain, scope, Devil's Advocate, artifact, roadmap, and handoff contracts still pass. | Same focused Pester run and focused failure summary from `tests/last-run.json` | yes |
| V3 | 1 | Claude Code, Codex, OpenCode, and Kilo command and skill outputs match regenerated canonical behavior before Phase 1 is complete. | `python scripts/cg_generate_targets.py --all`; `python -m pytest scripts/tests/test_target_packaging.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_kilo.py -q` | yes |
| V4 | 1 | The automatic final phase-boundary gate runs the complete safe project regression suite once and returns unfiltered passing evidence. | `/cg-work` Step 2.5: `. tests\Run-Tests.ps1` through an execution subagent; `tests/last-run.json` with `passed: true` and `filteredFiles: null` | yes |
| V5 | final | The implementation-owned changed-file set stays within the approved pilot boundary and has no whitespace errors. | `git diff --check`; `git status --short`; changed-file review against plan boundaries and pre-work baseline | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Keep the existing `/cg-brainstorm` lifecycle and critical prompt-level fallback gates. | Existing and new prompt contract tests. |
| C2 | 1 | Keep the six current question areas as a coverage checklist, not a mandatory sequence or fixed count anywhere in the prompt. | Isolated Step 1.5, Step 2, and Step 3 positive and negative assertions. |
| C3 | 1 | Ask one question by default; batch only two or three short independent decisions and never dependent decisions. | Skill and prompt behavioral assertions. |
| C4 | 1 | Edit `.github/` canonical files only; update native targets only through the generator and verify them before Phase 1 completes. | Changed-path review, generator output, and target parity tests. |
| C5 | final | Do not add decision IDs, persistent graphs, new grilling skills, review-axis redesign, or `/cr-brainstorm` integration. | Requirements, changed-file, and boundary review. |
| C6 | final | Preserve pre-existing brainstorm and roadmap worktree changes without modification or attribution to this implementation. | Compare pre-work and final `git status --short`; inspect diffs only for implementation-owned paths. |
| C7 | 1 | Do not confirm or capture a design while a material fact, approach choice, or rejection reason is unresolved. | Fact-state, Step 3.6, Step 3.7, and rejection-path assertions. |
| C8 | 1 | Do not force multiple approaches when fewer than two materially different viable paths exist. | Conditional Step 3 branch assertions and single-path scenario. |

### Boundaries

- Allowed: `.github/prompts/cg-brainstorm.prompt.md`; the existing
  `.github/skills/cg-skill-brainstorming/` bundle; focused
  `tests/prompt-tools.Tests.ps1` assertions; generator-produced `.claude/`,
  `.agents/`, `.opencode/`, and `.kilo/` mirrors and ownership manifests.
- Out of scope: stable decision IDs; cross-flow traceability; persistent
  decision graphs; specification/ticket splitting; glossary or ADR writes;
  review redesign; cross-suite integration; a runtime evaluation harness;
  direct roadmap or generated-file edits.

### Iteration Policy

1. Define the shared skill contract before changing the prompt.
2. Keep safety and lifecycle rules duplicated at prompt level only where skill-loading failure would remove a gate.
3. Add focused behavioral and ordering tests before regeneration.
4. Regenerate all native targets once canonical changes are complete, then pass native parity tests before Phase 1 can stop.
5. After all implementation fixes and Step 5 checks are complete, let `/cg-work` Step 2.5 run the complete safe Pester suite once at the final one-phase boundary.
6. Under `deviation-policy: ask`, pause before any material scope, phase, file-boundary, lifecycle, or deferred-capability change.
7. Mark the single phase complete only after V1-V4 pass; mark the plan complete only after V5 and all final constraints pass.

### Blocked-Stop Conditions

- The current branch, context, Brain, scope, Devil's Advocate, artifact,
  roadmap, side-idea, or handoff behavior cannot be preserved without redesign.
- Native target generation reports an ownership conflict, unsafe path, collision,
  or canonical-source mutation.
- A required focused or final test remains failed after bounded diagnosis and
  repair.
- Final Pester evidence is missing, partial, stale, or cannot be produced through
  the safe canonical runner.
- A material fact remains unavailable or contradictory, an approach remains
  unselected, or a rejected confirmation has no actionable reason; report the
  unresolved state and do not capture or hand off.
- Completing the pilot requires a decision ID, persisted graph, new skill,
  cross-suite change, review redesign, or other deferred infrastructure.
- A protected or unlisted file boundary must be crossed to continue.
- A required deviation is discovered and user approval is unavailable.
