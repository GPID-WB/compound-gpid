# Workflow Overview

Choose the shortest workflow that matches the uncertainty and risk of the task.
Commands are workflow entry points; skills and most agents are loaded by those
commands rather than invoked directly.

## Choose by situation

First choose the suite that owns the task. Use `/cg-*` for technical delivery,
infrastructure, and code-review workflows. Use `/cr-*` for research scoping,
identification, measurement, econometrics, replication, writing, and
publication output. The research suite composes shared implementation
capabilities without depending on the technical command suite.

For a guided first research workflow, use the [Research Handbook](../research/index.md).

| Situation | Start with | Continue with |
|---|---|---|
| Project direction is unclear | `/cg-strategy` | `/cg-ideate`, then `/cg-brainstorm` |
| One requirement is fuzzy | `/cg-brainstorm` | `/cg-plan` |
| The task is known | `/cg-plan` | `/cg-plan-review` when consequential, then `/cg-work` |
| A bug can be reproduced | `/cg-fixbug` | Review and compound after verification |
| A plan already exists | `/cg-work` | `/cg-review`, `/cg-fix-triage` |
| Work was interrupted | `/cg-resume` | Run the returned next command |
| A change needs assurance | `/cg-review` | `/cg-fix-triage`, then verify |
| A solved problem should be reusable | `/cg-compound` | `/cg-brain-rebuild` when the Brain needs refreshing |
| CI is failing on a pull request | `/cg-verify-pr` | Apply confirmed fixes and rerun checks |
| VS Code or Positron crashed | `/cg-diagnose` | Follow the bounded recovery path |
| A research question or method is unclear | `/cr-brainstorm` | `/cr-plan` |
| A research plan is ready | `/cr-work` | `/cr-review`, then `/cr-compound` |

## The standard loop

```text
Understand -> Plan -> Deliver -> Assure -> Resolve -> Remember
```

```text
/cg-brainstorm -> /cg-plan -> /cg-work -> /cg-review -> /cg-fix-triage -> /cg-compound
```

Not every task needs every step. Lightweight work may begin at planning or
implementation. High-risk analytical, schema, credential, publishing, install,
or destructive-file changes should not bypass appropriate review and executed
evidence.

## Focused guides

- [Design the Work](design.md): strategy, ideation, brainstorming, planning, and plan review.
- [Deliver and Resume](deliver.md): implementation, bug fixing, phase boundaries, and restart records.
- [Review and Assure](assure.md): review routes, findings, CI, diagnostics, and verification.
- [Knowledge and Coordination](knowledge.md): solutions, Brain, roadmap, issues, and wiki.
- [Detailed Workflow Manual](../workflow.md): complete step behavior, scenarios, and edge cases.
- [Modular Guide](../modular-guide.md): suite selection, shared capabilities, and extension rules.

## Related pages

- [Commands](../reference/commands.md)
- [Skills Catalog](../skills/index.md)
- [Governance and Security](../governance/index.md)
