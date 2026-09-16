# Research Handbook: Start Here

<!-- Created 2026-09-03. -->

Compound Research (`cr`) is the research suite of Compound GPID. It helps
researchers move from a question to evidence, methods, checked outputs, and
reusable knowledge while keeping important judgments visible.

This handbook is for World Bank researchers who know applied poverty,
inequality, welfare, or related research and are somewhat new to Compound GPID.
It is an onboarding path, not a replacement for the detailed command, skill,
and methodology references.

## What you will do

A first CR workflow follows this sequence:

```text
/cr-brainstorm -> /cr-plan -> /cr-work -> /cr-review -> /cr-compound
```

You will start with a research question, clarify what it means, plan the work,
execute it with evidence and integrity checks active, review the result, and
capture a verified lesson for future work.

## Before you begin

You need:

- Compound GPID installed and linked to your development environment.
- A project repository in which the work and its evidence can be kept.
- A project `compound-gpid.local.md` configuration file.
- A research question or a small research task whose result can be checked.
- Access to the data, source documents, or other evidence that the task needs.

If the project has not been configured, run `/cg-setup` first. It creates or
checks the project configuration and can activate the research suite. If you
are working in a project that uses both technical and research workflows, keep
both suites active.

## Activate the research suite

In `compound-gpid.local.md`, choose one of these configurations:

```yaml
suites: [cr]
```

for a research-focused project, or:

```yaml
suites: [cg, cr]
```

when the project also needs the technical `/cg-*` workflow. The research suite
composes shared language, testing, reproducibility, and review capabilities as
needed. You do not need to list those dependencies yourself.

After configuration, begin with:

```text
/cr-brainstorm
```

Give it the research question and enough context to understand the decision it
will inform. It will propose a research task type and ask clarifying questions;
you remain responsible for confirming the framing and consequential choices.

## What a successful first run leaves behind

By the end of the loop, you should be able to point to:

- a scoped research brief and an approved approach;
- a plan with evidence requirements, checks, and acceptance criteria;
- working outputs and records of how they were produced;
- review findings that were resolved or explicitly accepted; and
- a concise, verified lesson with limits on when it can be reused.

The result is not automatically a publishable finding. It is a more inspectable
research process that makes the next human review easier.

## If you get stuck

- No project configuration: run `/cg-setup`.
- The research command is unavailable: check that `suites` includes `cr`, then
  refresh the linked installation with the project's normal update path.
- The question is too broad: return to `/cr-brainstorm` and ask it to narrow
  the decision, population, evidence, and desired output.
- Data or a dependency is missing: record the blocker in the plan and resolve
  it before treating the result as complete.
- A review finds a serious issue: do not compound the lesson yet; fix or
  explicitly defer the finding, then rerun the relevant check.

Continue with the [CR philosophy](philosophy.md), or follow the [first CR
workflow](first-workflow.md) for the command-by-command path.
