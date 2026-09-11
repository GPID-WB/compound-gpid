# Design the Work

Use these workflows to turn institutional objectives and uncertain requests
into an explicit, reviewable implementation path.

## Set project direction

Run `/cg-strategy` when the project vision, priorities, or roadmap need
structure. Use `/cg-ideate` when the objective is understood but the next piece
of work has not been selected. Strategy and roadmap changes are distinct from
implementation approval.

## Clarify one task

Run `/cg-brainstorm` when requirements are fuzzy, alternatives have meaningful
tradeoffs, or assumptions need challenge. It checks prior brainstorms and can
record a decision without pretending implementation has begun.

Skip brainstorming when expected behavior and scope are already explicit.

## Choose the delivery route

Use `/cg-light-work` only when one small, low-risk technical task qualifies. Use
`/cg-fixbug` for a reproducible bug and `/cr-*` for research, statistical, or
publication work. Larger, ambiguous, security-sensitive, schema, dependency, or
destructive work uses `/cg-brainstorm` -> `/cg-plan` -> `/cg-work`.

## Create the plan

Run `/cg-plan` for a known task. The plan records requirements, repository
evidence, validation, deviations, completion criteria, and phases when useful.
`/cg-work` executes an approved saved Plan. If no saved Plan matches supplied
task text, it stops and returns a copy-ready `/cg-light-work` route without
dispatching it.

Use `/cg-plan-review` when assumptions, dependencies, phase boundaries, or
failure modes deserve independent criticism before execution.

```text
/cg-brainstorm
/cg-plan
/cg-plan-review
```

## Handoff standard

Before delivery, confirm that the plan identifies:

- The behavior or artifact that should exist when complete.
- Sources of truth in the repository or external specification.
- Data, statistical, security, schema, and compatibility risks.
- Tests or other executed evidence required for acceptance.
- Work that is explicitly out of scope.

## Related pages

- [Deliver and Resume](deliver.md)
- [Governance and Security](../governance/index.md)
- [Detailed Workflow Manual](../workflow.md)
