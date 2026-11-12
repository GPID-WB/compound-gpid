# The Standard Module

The standard module is Compound GPID's technical suite, selected with
`suites: [cg]`. It gives everyday development a repeatable structure: understand
the task, agree on a plan, implement it, check it, and keep the useful lesson.
It is the default starting point for building tools, maintaining code, and
improving data infrastructure.

You bring the objective and judgment. The plugin supplies reusable prompts,
specialist guidance, review routes, and project records inside your existing
AI coding environment. It does not replace your editor, tests, or version control.

## Start with one real task

After [installation and setup](../getting-started/index.md), follow
[Your First Standard Workflow](first-workflow.md). It walks through a small
file-validation tool, including a copy-ready brief, acceptance criteria, the
review handoff, and what to do when a check fails.

Already familiar with the loop? Browse [standard use cases](examples.md) or
use the [workflow chooser](index.md) to find the right entry point.

## What the loop produces

Run these commands in the agent chat, one stage at a time. Approval of a
direction is separate from approval to implement a saved plan.

| Stage | Entry point | What to inspect before continuing |
|---|---|---|
| Understand | `/cg-brainstorm` | The problem, constraints, alternatives, and an agreed direction |
| Plan | `/cg-plan` | A saved Plan with scope, acceptance criteria, risks, and concrete checks |
| Challenge the plan | `/cg-plan-review` | Unresolved assumptions and required plan revisions; especially useful for consequential work |
| Implement | `/cg-work` | Working changes, executed validation evidence, and a Work Report |
| Review | `/cg-review` | A Review Report with findings prioritized by severity |
| Resolve | `/cg-fix-triage` | Verified fixes or explicit decisions about remaining findings |
| Remember | `/cg-compound` | A verified, reusable lesson in `.cg-docs/solutions/` |

The point is continuity. A teammate should be able to recover why a change was
made, how it was checked, and what remains uncertain without rereading a chat.

## Choose the right amount of process

| Your situation | Start here | Boundary |
|---|---|---|
| A small, low-risk technical change | `/cg-light-work -- <task>` | Approve a saved Plan first; mandatory light Review follows; compounding needs a separate opt-in |
| A reproducible defect | `/cg-fixbug` | Establish expected behavior, demonstrate the failure, and verify the fix |
| A substantial or uncertain change | `/cg-brainstorm`, then `/cg-plan` | Review assumptions and scope before implementation |
| An approved saved Plan exists | `/cg-work` | Executes the saved Plan; an unmatched inline task does not authorize implementation |
| A session was interrupted | `/cg-resume` | Inspect the recovered state and run the returned next command |
| Research, estimation, measurement, or publication | [Research module](../research/index.md) | Use `/cr-*` for scientific reasoning and research integrity |

Small does not automatically mean low risk. Authentication, destructive file
operations, schemas, dependencies, statistical correctness, and sensitive data
can require a deeper route even when the code change is short.

## Configure it once for the project

Run `/cg-setup` after linking the project. The shared configuration lives in
`compound-gpid.local.md`:

```yaml
suites: [cg]
```

Use `suites: [cg, cr]` if the same project also conducts research. The two
suites share capabilities; the research suite can also run independently with
`suites: [cr]`. "Standard" is the default user route, not a requirement to
run technical commands before research commands.

Setup also records language preferences, R dialect where applicable, and
review depth. See [Configuration](../configuration/index.md) before changing
managed files or platform links.

## Keep the evidence with the work

- Commit the Plan, Work Report, review findings, and verified lessons in
  `.cg-docs/`, alongside the source change and relevant tests.
- Use [review depth matched to risk](assure.md). A formatting fix and a
  survey-processing change need different checks.
- Resolve P0 and P1 findings before accepting delivery. A green test run
  alone does not settle a methodological or security concern.
- Capture a lesson after verification. Record its assumptions and limits so
  another project does not reuse it in the wrong context.
- Keep secrets, restricted data, and raw private outputs out of Git and
  reusable knowledge records.

## Continue learning

1. [Walk through your first task](first-workflow.md).
2. [Adapt a standard use case](examples.md).
3. [Design the work](design.md), [deliver and resume](deliver.md), and
   [review the result](assure.md).
4. [Find a command](../reference/commands.md) or [a skill](../skills/index.md).
5. [Understand the research module](../research/index.md) when the task
   moves from software behavior to evidence and inference.
