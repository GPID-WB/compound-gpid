# Your First CR Workflow

<!-- Created 2026-09-03. -->

Start with the [CR Handbook: Start Here](index.md) if the project is not
configured yet. Once the research suite is active, use the five commands below
in order. Each command leaves a handoff for the next one; none turns a proposal
into accepted research without human review.

## The route

| Stage | Command | What it does | What it leaves behind |
|---|---|---|---|
| Scope | `/cr-brainstorm` | Clarifies the question, surfaces assumptions, and proposes a task type and approaches. | A scoped research brief, alternatives, and explicit decisions. |
| Plan | `/cr-plan` | Converts the approved direction into ordered work and checks. | A plan with evidence requirements, tests, and acceptance criteria. |
| Execute | `/cr-work` | Carries out the plan while research-integrity and reproducibility gates remain active. | Working outputs, evidence records, run details, and blocked/completed steps. |
| Verify | `/cr-review` | Reviews the work through research and engineering lenses matched to the task. | Prioritized findings and a record of what was resolved or accepted. |
| Maintain | `/cr-compound` | Captures a verified research lesson for future work. | A reusable lesson with its limits and supporting evidence. |

The full command contracts are in the [Commands reference](../reference/commands.md).

## 1. Scope the question

Run `/cr-brainstorm` with the research question, the decision it should
inform, the population or unit of analysis, and any evidence already in hand.
It will ask follow-up questions before recommending an approach. Confirm or
correct its provisional task classification and make consequential choices
visible.

A good result is a question that can be planned. It is not a final method or a
claim that can be quoted without checking.

## 2. Plan the work

Pass the approved brainstorm to `/cr-plan`. The plan should say what evidence
is needed, which assumptions matter, what will be tested, and what would count
as a credible answer. Keep the plan proportionate to the question; a small
orientation task does not need a full research program.

## 3. Execute with records attached

Use `/cr-work` to implement the plan or a named phase. Record sources,
parameters, seeds where randomness is used, data restrictions, derivations, and
outputs while the work happens. If a required input or dependency is missing,
keep the step blocked and record what is needed rather than silently changing
the question.

## 4. Review the result

Run `/cr-review` after the planned work has produced something checkable. The
review route depends on the task: identification, econometrics, measurement,
provenance, machine learning, writing, publication output, replication, and
shared engineering checks are not interchangeable.

Resolve serious findings before compounding the lesson. If a limitation remains,
record it and decide whether it is acceptable for the intended audience and
purpose.

## 5. Compound what was learned

Run `/cr-compound` only after the relevant checks pass. Capture why the approach
worked, what was uncertain, which alternatives were rejected, and when the
lesson should not be reused. The useful unit is the reasoning and its boundary,
not just the final answer.

## What the researcher decides

Throughout the loop, the researcher remains responsible for:

- the meaning of the question and the target population;
- the credibility and interpretation of sources and data;
- assumptions, identification, definitions, thresholds, and weighting rules;
- responses to review findings and remaining limitations; and
- whether the result is fit for publication, policy use, or further work.

For the lifecycle, task types, and an example of this route in practice, use
the [research lifecycle and task types](lifecycle.md) and the [short workflow
example](short-example.md).
