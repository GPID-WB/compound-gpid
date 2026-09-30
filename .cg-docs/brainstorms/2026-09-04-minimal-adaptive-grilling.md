---
date: 2026-09-04
title: "Minimal adaptive grilling for the Compound GPID workflow"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Minimal Adaptive Grilling"
tags: [brainstorming, grilling, requirements, decision-tree, simplicity, workflow, external-research]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Minimal Adaptive Grilling for the Compound GPID Workflow

## Context

This brainstorm reviewed the main-flow skills in `mattpocock/skills` and the
related AI Hero articles to determine whether their logic can improve Compound
GPID. The main interest was the `grilling` method and its relationship to the
current `/cg-brainstorm` command.

The external repository was reviewed on 2026-09-04 at commit
`3cca18b368ae95cdbdebbff572ccafa662551015`. Its current main flow is:

```text
grill-with-docs -> to-spec -> to-tickets -> implement -> code-review
```

Supporting skills include `grilling`, `domain-modeling`, and `tdd`. The
`wayfinder` skill adds a persistent decision graph for large, multi-session
work. The external workflow has useful clarification logic, but Compound GPID
already has stronger durable artifacts, execution gates, specialized reviews,
and post-work knowledge capture.

Relevant external sources:

- <https://www.aihero.dev/skills>
- <https://www.aihero.dev/skills-grilling>
- <https://www.aihero.dev/grill-with-docs>
- <https://www.aihero.dev/skills-wayfinder>
- <https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling/SKILL.md>
- <https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/grill-with-docs/SKILL.md>
- <https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/wayfinder/SKILL.md>

Prior project decisions also apply:

- Main-command defaults remain self-contained in their prompts rather than a
  new central defaults layer. Source:
  `.cg-docs/brainstorms/2026-05-18-command-default-behaviors.md`.
- External ideas require controlled adaptation and review. Generic workflows
  that duplicate stronger local controls should not be imported unchanged.
  Source:
  `.cg-docs/strategy/2026-07-30-trusted-external-capability-adoption.md`.

## Research Findings

### Valuable External Logic

1. **Decision dependency tree**: clarification is modeled as decisions and
   prerequisites instead of a fixed questionnaire.
2. **Decision frontier**: only decisions whose prerequisites are settled are
   ready to ask. Each answer can expose or remove later questions.
3. **Fact and decision separation**: the agent discovers facts from the
   environment; the user resolves material trade-offs.
4. **Materiality filter**: a question is useful only when its answer can change
   implementation, behavior, scope, risk, or user experience.
5. **Recommended answers**: each decision includes a default recommendation to
   reduce user effort.
6. **Shared-understanding gate**: implementation does not start until the user
   confirms the resulting design.
7. **Independent review axes**: external `code-review` separates standards
   compliance from specification compliance.
8. **Deep-scope persistence**: `wayfinder` persists unresolved decisions and
   dependency edges across sessions.

### External Weaknesses Not to Copy

1. The inferred decision tree has no explicit schema or deterministic
   completeness check.
2. Large batches of recommended answers can anchor the user or cause passive
   agreement.
3. Most grilling decisions remain transient until the specification step.
4. Thin wrapper skills depend on reliable cross-skill loading without a
   fallback contract.
5. The external implementation contract has weaker failure, evidence, and
   completion gates than `/cg-work`.
6. The external pre-commit review sequence conflicts with a review diff that
   ends at committed `HEAD`.
7. There is no direct equivalent of `/cg-compound` for systematic post-work
   learning.
8. Splitting specification and ticket generation would duplicate parts of the
   current Compound GPID plan and phase system.

## Requirements

1. Optimize the improvement for all Compound GPID users, not only expert
   maintainers.
2. Select targeted improvements rather than copy or redesign the full external
   workflow.
3. Reuse the existing `cg-skill-brainstorming` skill as the shared logic layer.
   Do not create a second grilling skill for the first iteration.
4. Always aim for the smallest implementation that fully satisfies the goal.
5. Distinguish discoverable facts from material user decisions.
6. Research facts from available code, tools, environment, and documentation
   before asking the user.
7. Model material decisions and their prerequisites as a dependency tree.
8. Ask only questions whose answers could materially change implementation,
   behavior, scope, risk, or user experience.
9. Use the simplest reasonable default for immaterial uncertainty and do not
   ask the user about it.
10. Stop when remaining uncertainty cannot materially affect the minimum viable
    solution.
11. Prevent question fatigue, answer anchoring, and false completion.
12. Use adaptive rounds: ask one question by default, but group at most two or
    three short independent decisions when doing so clearly reduces user
    effort. Never place dependent decisions in the same round.
13. For each material decision, provide a recommended answer and concise
    trade-offs. Recommendations must remain transparent defaults, not hidden
    decisions.
14. Favor simplicity over flexibility and speculative extensibility.
15. Summarize the minimal design and obtain explicit confirmation before any
    implementation handoff.
16. Only after minimal-design confirmation, ask whether the user wants to
    explore a more sophisticated version.
17. Preserve existing Compound GPID branch, context-loading, Brain, scope,
    Devil's Advocate, artifact validation, roadmap, and handoff behavior.
18. Preserve critical prompt-level fallback rules so a skill-loading failure
    cannot remove safety or lifecycle gates.

## Agreed Core Instruction

The implementation should preserve the following instruction as the normative
behavior of adaptive grilling:

> Interview the user until you reach a shared understanding of what should be
> built, while always aiming for the smallest implementation that fully
> satisfies the goal. Treat the design as a dependency tree: ask only decisions
> that can be made with the information currently available, and let each
> answer determine what becomes relevant next. Ask one question by default.
> Group at most two or three short independent questions into a round only when
> this clearly reduces user effort; never group dependent decisions. Only ask a
> question if its answer could materially change the implementation, behavior,
> scope, risk, or user experience; otherwise choose the simplest reasonable
> default and do not ask. Stop interviewing once the remaining uncertainties
> would not materially affect the minimum viable solution. Discover facts
> yourself whenever they can be obtained from the environment, tools, code, or
> documentation; reserve the user's attention for actual decisions. For each
> material decision, provide a recommended answer and concise trade-offs,
> generally favoring simplicity over flexibility or over-engineering. Once all
> material decisions are settled, summarize the minimal design and obtain
> confirmation before implementation. Only after that confirmation, optionally
> ask whether the user wants to explore a more sophisticated version.

## Approaches Considered

### Approach 1: Minimal Adaptive Grilling

Update the existing brainstorming skill and `/cg-brainstorm` command with the
agreed core instruction. Preserve the current main flow and artifacts.

**Pros**:

- Captures the highest-value external insight with the smallest change.
- Reuses an existing extension point.
- Reduces avoidable questions and premature design choices.
- Keeps current Compound GPID safety, review, and knowledge-capture strengths.
- Provides a low-cost pilot before adding persistent decision infrastructure.

**Cons**:

- Does not add stable decision IDs or explicit cross-flow traceability.
- Does not share the primitive with `/cr-brainstorm` in this iteration.
- The decision tree remains an agent reasoning model rather than a validated
  persisted graph.

**Effort**: Medium.

### Approach 2: Decision Spine Across the Main Flow

Apply adaptive grilling and add stable decision IDs that map from brainstorm
requirements to plan requirements and a separate specification-conformance
axis in review.

**Pros**:

- Adds end-to-end intent traceability.
- Makes requirement drift visible during planning and review.
- Adapts the useful standards-versus-spec distinction to Compound GPID.

**Cons**:

- Changes several artifact and prompt contracts.
- Adds process weight to simple tasks.
- Requires renderer, generated-target, and test updates.
- Has no current evidence that decision loss is frequent enough to justify the
  added machinery.

**Effort**: Large.

### Approach 3: Wayfinder-Style Workflow Redesign

Add a durable decision graph, decision tickets, separate specification and
ticket-generation stages, and a cross-suite grilling capability.

**Pros**:

- Supports highly uncertain work across many sessions.
- Makes unresolved decisions and dependencies explicit.
- Creates clear routes for research and prototype work.

**Cons**:

- Duplicates roadmap, phased-plan, active-state, and research-scoping behavior.
- Adds cross-suite registry and capability work.
- Increases ceremony and token use for ordinary tasks.
- Risks replacing stronger local gates with a less complete external flow.

**Effort**: Large and multi-phase.

## Decision

Choose **Minimal Adaptive Grilling**.

This approach provides the best effort-to-value ratio. It adopts the external
workflow's strongest logic - decision dependencies, materiality filtering,
fact research, and shared-understanding confirmation - without importing its
weaker artifact and execution contracts.

The existing `cg-skill-brainstorming` skill is the correct shared primitive for
the first iteration. The implementation should update that skill instead of
creating a parallel `grilling` skill. `/cg-brainstorm` must explicitly load and
apply it, while retaining enough critical rules in the prompt to fail safely if
skill loading is unavailable.

Adaptive rounds resolve the tension between frontier batching and question
fatigue. The default remains one question. A round can contain at most two or
three short independent decisions when batching clearly lowers user effort.

The following items are deliberately deferred:

- Stable decision IDs and cross-flow requirement traceability.
- A new specification-compliance section in `/cg-review`.
- A persistent Wayfinder-style decision graph.
- A split between specification and ticket generation.
- Immediate glossary or ADR writes during brainstorming.
- Cross-suite use by `/cr-brainstorm` and module-registry changes.

These are not rejected permanently. They require evidence from the minimal
pilot, such as repeated decision drift, false completion, or context loss.

## Next Steps

1. Use `/cg-plan` to define a minimal implementation around the existing
   `.github/skills/cg-skill-brainstorming/` bundle and
   `.github/prompts/cg-brainstorm.prompt.md`.
2. Replace the fixed six-question execution rule with material-decision,
   dependency-frontier, and stop-condition rules while retaining the six areas
   as a coverage checklist rather than a mandatory sequence.
3. Add the bounded adaptive-round rule and anti-anchoring recommendation format.
4. Add the minimal-design confirmation gate and the post-confirmation optional
   complexity question.
5. Preserve all existing context, branch, Brain, Devil's Advocate, artifact,
   roadmap, and handoff steps.
6. Add focused assertions to `tests/prompt-tools.Tests.ps1` for skill loading,
   fact-versus-decision behavior, materiality, adaptive-round bounds, stop
   conditions, minimal-design confirmation, and complexity opt-in ordering.
7. Regenerate native platform targets through the existing canonical generator
   and verify parity rather than editing generated targets directly.
8. Treat the change as a pilot. Do not add decision IDs or a persistent graph
   unless later use provides evidence that the minimal method is insufficient.
